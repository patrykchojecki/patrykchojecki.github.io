"""Check published discovery metadata, optionally against the exact build. No dependencies."""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser
from xml.etree import ElementTree

spec = importlib.util.spec_from_file_location("site_checker", Path(__file__).with_name("check-site.py"))
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)
TARGETS = Path(__file__).with_name("geo") / "targets.json"
LIMIT = 5 * 1024 * 1024
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(url):
    request = Request(quote(url, safe=":/%?=&"), headers={"User-Agent": "ChojeckiSiteCheck/1.0", "Cache-Control": "no-cache"})
    try:
        with build_opener(NoRedirect).open(request, timeout=15) as response:
            body = response.read(LIMIT + 1)
            if len(body) > LIMIT:
                raise ValueError("response exceeds 5 MiB limit")
            return response.status, dict(response.headers.items()), body
    except HTTPError as error:
        return error.code, dict(error.headers.items()), b""


def sitemap_entries(body, origin):
    root = ElementTree.fromstring(body)
    if root.tag != f"{{{NS['s']}}}urlset":
        raise ValueError("expected a sitemap urlset")
    entries = {}
    for node in root.findall("s:url", NS):
        url = node.findtext("s:loc", namespaces=NS)
        parsed = urlsplit(url or "")
        if not url or f"{parsed.scheme}://{parsed.netloc}" != origin or parsed.query or parsed.fragment:
            raise ValueError(f"noncanonical sitemap URL: {url}")
        if url in entries:
            raise ValueError(f"duplicate sitemap URL: {url}")
        entries[url] = node.findtext("s:lastmod", namespaces=NS)
    if not 1 <= len(entries) <= 200:
        raise ValueError("expected 1–200 sitemap URLs for this site")
    return entries


def metadata_fingerprint(page):
    data = {"canonical": page.canonical_urls, "robots": page.robots, "schema": page.structured_data}
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build_manifest(directory, targets):
    root = Path(directory).resolve()
    entries = sitemap_entries((root / "sitemap.xml").read_bytes(), targets["origin"])
    metadata, assets = {}, {}
    for url in entries:
        path = (root / unquote(urlsplit(url).path).lstrip("/")).resolve()
        if not path.is_relative_to(root):
            raise ValueError("sitemap path leaves build directory")
        if path.is_dir():
            path /= "index.html"
        if path.suffix == ".html":
            metadata[url] = metadata_fingerprint(site.Page(path.read_text()))
        elif not path.is_file():
            raise ValueError(f"missing sitemap target: {url}")
        else:
            assets[url] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"sitemap": entries, "metadata": metadata, "assets": assets}


def indexing_blocked(value):
    # Includes an optional crawler prefix in X-Robots-Tag (e.g. googlebot: noindex).
    return bool(re.search(r"\b(?:noindex|none|nosnippet)\b|\bmax-snippet\s*:\s*0\b", value, re.I))


def audit(targets, expected=None, base_url=None, fetcher=fetch):
    origin = targets["origin"]
    base_url = (base_url or origin).rstrip("/")
    errors, resources, pages = [], {}, {}

    def get(url):
        try:
            status, headers, body = fetcher(base_url + url[len(origin):])
            headers = {key.lower(): value for key, value in headers.items()}
            result = {"status": status, "content_type": headers.get("content-type", "")}
            if status != 200:
                result["error"] = f"HTTP {status}; expected 200 without redirects"
            elif indexing_blocked(headers.get("x-robots-tag", "")):
                result["error"] = "X-Robots-Tag blocks indexing or snippets"
            return url, result, headers, body
        except (OSError, URLError, ValueError) as error:
            return url, {"error": str(error)}, {}, b""

    robots_url = origin + "/robots.txt"
    sitemap_url = targets["sitemap"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        initial = list(pool.map(get, [robots_url, sitemap_url]))
    bodies = {}
    for url, result, headers, body in initial:
        resources[url] = result
        bodies[url] = body
        if result.get("error"):
            errors.append(f"{url}: {result['error']}")
    try:
        entries = sitemap_entries(bodies[sitemap_url], origin)
    except (ElementTree.ParseError, ValueError) as error:
        errors.append(f"sitemap: {error}")
        entries = {}
    for path in targets["pages"]:
        if origin + path not in entries:
            errors.append(f"critical page absent from sitemap: {path}")
    if expected:
        # Jekyll dates static files using checkout mtime; compare their bytes instead.
        if set(entries) != set(expected["sitemap"]) or any(
            entries.get(url) != expected["sitemap"].get(url) for url in expected["metadata"]
        ):
            errors.append("deployed sitemap differs from the build manifest")

    robots_text = bodies[robots_url].decode("utf-8", errors="replace")
    if not resources[robots_url].get("content_type", "").lower().startswith("text/plain") or "<html" in robots_text.lower():
        errors.append("robots.txt did not return plain text")
    parser = RobotFileParser(robots_url)
    parser.parse(robots_text.splitlines())
    if sitemap_url not in (parser.site_maps() or []):
        errors.append("robots.txt does not advertise the canonical sitemap")
    for crawler in targets["search_crawlers"]:
        for url in entries:
            if not parser.can_fetch(crawler, url):
                errors.append(f"robots.txt blocks {crawler}: {url}")

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(get, sorted(entries)))
    for url, result, headers, body in results:
        resources[url] = result
        if result.get("error"):
            errors.append(f"{url}: {result['error']}")
            continue
        if urlsplit(url).path.lower().endswith(".pdf"):
            if not body.startswith(b"%PDF-") or "application/pdf" not in result["content_type"].lower():
                errors.append(f"{url}: expected a PDF response")
            if expected and hashlib.sha256(body).hexdigest() != expected.get("assets", {}).get(url):
                errors.append(f"{url}: deployed asset differs from the build manifest")
            continue
        if "text/html" not in result["content_type"].lower():
            errors.append(f"{url}: expected HTML")
            continue
        page = site.Page(body.decode("utf-8", errors="replace"))
        pages[url] = metadata_fingerprint(page)
        errors.extend(f"{url}: {error}" for error in site.metadata_errors(page, url, require_indexable=True))
        if page.redirect or not page.main or page.headings != 1:
            errors.append(f"{url}: missing page landmarks or unexpected HTML redirect/challenge")
        dates = site.modification_dates(page, url, errors)
        project = urlsplit(url).path.startswith("/projects/")
        if project and not dates:
            errors.append(f"{url}: project revision date missing")
        if dates and (entries[url] is not None or project):
            try:
                if datetime.fromisoformat(entries[url].replace("Z", "+00:00")) not in dates:
                    errors.append(f"{url}: sitemap lastmod differs from JSON-LD dateModified")
            except (ValueError, AttributeError):
                errors.append(f"{url}: invalid or missing sitemap lastmod")
        if expected and pages[url] != expected["metadata"].get(url):
            errors.append(f"{url}: deployed metadata differs from the build manifest")
    return {"checked_at": datetime.now(timezone.utc).isoformat(), "origin": origin,
            "errors": sorted(set(errors)), "resources": resources,
            "limitations": "HTTP and robots checks do not prove verified AI crawler access or indexing."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", type=Path, default=TARGETS)
    parser.add_argument("--manifest-dir", type=Path, help="Print a compact build manifest and exit")
    parser.add_argument("--expected-dir", type=Path, help="Compare published metadata with this build")
    parser.add_argument("--require-manifest", action="store_true", help="Fail if no build manifest was supplied (CI)")
    parser.add_argument("--base-url", help="Fetch from another origin; canonical expectations stay unchanged")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--attempts", type=int, choices=range(1, 6), default=1)
    parser.add_argument("--retry-delay", type=int, choices=range(0, 61), default=20)
    args = parser.parse_args()
    targets = json.loads(args.targets.read_text())
    if args.manifest_dir:
        print(json.dumps(build_manifest(args.manifest_dir, targets), separators=(",", ":")))
        return
    expected = build_manifest(args.expected_dir, targets) if args.expected_dir else None
    if os.environ.get("EXPECTED_SITE_MANIFEST"):
        expected = json.loads(os.environ["EXPECTED_SITE_MANIFEST"])
    if args.require_manifest and not expected:
        parser.error("a nonempty build manifest is required")
    for attempt in range(args.attempts):
        result = audit(targets, expected, args.base_url)
        result["attempt"] = attempt + 1
        if not result["errors"] or attempt + 1 == args.attempts:
            break
        print(f"Live check attempt {attempt + 1} failed; retrying after {args.retry_delay}s.", file=sys.stderr)
        time.sleep(args.retry_delay)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n")
    if result["errors"]:
        raise SystemExit("Live site checks failed:\n" + "\n".join(result["errors"]))
    print(f"Live site checks passed: {len(result['resources'])} resources; HTTP, robots, canonicals, schema and dates.")


if __name__ == "__main__":
    main()
