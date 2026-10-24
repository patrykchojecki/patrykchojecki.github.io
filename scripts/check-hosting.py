"""Check deployed routes, legacy redirects, static asset bytes, and real 404s."""

import argparse
import hashlib
import importlib.util
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit

spec = importlib.util.spec_from_file_location("live", Path(__file__).with_name("check-live-site.py"))
live = importlib.util.module_from_spec(spec)
spec.loader.exec_module(live)


def check(root, base, check_hosts=False):
    root = Path(root).resolve()
    base = base.rstrip("/")
    errors = []
    aliases = json.loads((root / "redirects.json").read_text())
    redirect_files = set()
    for path in aliases:
        target = live.site.local_target(root, path, html_fallback=True)
        redirect_files.add(target)
    files = [p for p in root.rglob("*") if p.is_file() and p not in redirect_files
             and p.name not in {"_redirects", "_headers", "404.html"}]

    def verify_file(path):
        relative = path.relative_to(root).as_posix()
        route = "/" + relative.removesuffix("index.html") if path.suffix == ".html" else "/" + relative
        status, headers, body = live.fetch(base + quote(route, safe="/"))
        if status != 200:
            return f"{route}: expected HTTP 200, got {status}"
        if path.suffix == ".html":
            expected = live.site.Page(path.read_text())
            actual = live.site.Page(body.decode("utf-8"))
            if live.metadata_fingerprint(expected) != live.metadata_fingerprint(actual):
                return f"{route}: HTML metadata differs from this build"
            if actual.headings != expected.headings or actual.main != expected.main or actual.redirect:
                return f"{route}: page structure differs from this build"
        # Cloudflare can append managed crawler rules to robots.txt. The live
        # metadata check validates its effective access and canonical sitemap.
        elif relative != "robots.txt" and hashlib.sha256(body).digest() != hashlib.sha256(path.read_bytes()).digest():
            return f"{route}: asset bytes differ from this build"
        return None

    with ThreadPoolExecutor(max_workers=4) as pool:
        errors.extend(error for error in pool.map(verify_file, files) if error)

    rules = []
    for line in (root / "_redirects").read_text().splitlines():
        if line and not line.startswith("#") and line.startswith("/"):
            source, destination, code = line.split()
            rules.append((base + source, base + destination, int(code)))
    rules.append((base + "/__hosting-check-missing-7d9c2a__", None, 404))
    if check_hosts:
        rules.extend([
            ("https://www.chojecki.net/cv/?hosting-check=1", "https://chojecki.net/cv/?hosting-check=1", 301),
            ("http://chojecki.net/cv/?hosting-check=1", "https://chojecki.net/cv/?hosting-check=1", 301),
        ])
    for source, destination, expected_status in rules:
        status, headers, _ = live.fetch(source)
        if status != expected_status:
            errors.append(f"{source}: expected HTTP {expected_status}, got {status}")
        if destination:
            location = next((v for k, v in headers.items() if k.lower() == "location"), "")
            if urljoin(source, location) != destination:
                errors.append(f"{source}: incorrect redirect destination")
    if errors:
        raise SystemExit("Hosting checks failed:\n" + "\n".join(errors))
    print(f"Hosting checks passed: {len(files)} pages/assets and {len(rules)} redirect/404 checks at {base}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", type=Path, default=Path("_site"))
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--check-host-redirects", action="store_true")
    args = parser.parse_args()
    origin = urlsplit(args.base_url)
    if origin.scheme != "https" or not origin.netloc or origin.path not in ("", "/") or origin.query or origin.fragment:
        parser.error("--base-url must be an HTTPS origin")
    check(args.site_dir, args.base_url, args.check_host_redirects)
