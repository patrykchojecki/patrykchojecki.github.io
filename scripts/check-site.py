"""Check the generated website using only the Python standard library."""

import json
import sys
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
from xml.etree import ElementTree


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids = []
        self.references = []
        self.headings = 0
        self.main = False
        self.redirect = False
        self.structured_data = []
        self.structured_data_errors = []
        self.schema_contexts = []
        self.canonical_urls = []
        self.robots = []
        self.json_ld = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical_urls.append(attrs.get("href", ""))
        if tag == "meta" and attrs.get("name", "").lower() in ("robots", "googlebot"):
            self.robots.append(attrs.get("content", "").lower())
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.json_ld = []
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "a" and attrs.get("name"):
            self.ids.append(attrs["name"])
        self.headings += tag == "h1"
        self.main |= tag == "main" or attrs.get("role") == "main"
        self.redirect |= tag == "meta" and attrs.get("http-equiv", "").lower() == "refresh"
        for attribute in ("href", "src", "poster"):
            if attrs.get(attribute):
                self.references.append(attrs[attribute])
        if attrs.get("srcset") and not attrs["srcset"].startswith("data:"):
            self.references.extend(part.strip().split()[0] for part in attrs["srcset"].split(",") if part.strip())

    def handle_data(self, data):
        if self.json_ld is not None:
            self.json_ld.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.json_ld is not None:
            try:
                data = json.loads("".join(self.json_ld), parse_constant=reject_constant)
                nodes = data if isinstance(data, list) else [data]
                for node in nodes:
                    if not isinstance(node, dict):
                        raise ValueError("JSON-LD nodes must be objects")
                    self.schema_contexts.append(node.get("@context"))
                    graph = node.get("@graph", [node])
                    if not isinstance(graph, list) or any(not isinstance(item, dict) for item in graph):
                        raise ValueError("JSON-LD @graph must be an array of objects")
                    self.structured_data.extend(graph)
            except ValueError as error:
                self.structured_data_errors.append(str(error))
            self.json_ld = None


def reject_constant(value):
    raise ValueError(f"Invalid JSON constant: {value}")


def schema_types(node):
    value = node.get("@type", [])
    return [value] if isinstance(value, str) else value if isinstance(value, list) else []


def is_web_url(value):
    if not isinstance(value, str):
        return False
    try:
        url = urlsplit(value)
        return url.scheme in ("https", "http") and bool(url.hostname) and not url.username
    except ValueError:
        return False


def metadata_errors(page, canonical_url, require_indexable=False):
    """Validate the site's emitted schema contract, not all of schema.org."""
    errors = [f"invalid JSON-LD: {error}" for error in page.structured_data_errors]
    if page.canonical_urls != [canonical_url]:
        errors.append(f"expected exactly one canonical URL: {canonical_url}")
    if not page.structured_data:
        errors.append("missing JSON-LD")
    if any(context not in ("https://schema.org", "http://schema.org") for context in page.schema_contexts):
        errors.append("expected a schema.org @context on each JSON-LD document")
    if require_indexable and any(
        token.strip() in ("noindex", "none", "nosnippet", "max-snippet:0", "max-snippet: 0")
        for value in page.robots for token in value.split(",")
    ):
        errors.append("sitemap page blocks indexing or snippets")

    nodes = page.structured_data
    identifiers = {}
    for node in nodes:
        node_id = node.get("@id")
        if node_id is not None:
            if not is_web_url(node_id):
                errors.append("JSON-LD @id must be an absolute web URL")
            elif node_id in identifiers:
                errors.append(f"duplicate top-level JSON-LD @id: {node_id}")
            else:
                identifiers[node_id] = node
        if not schema_types(node):
            errors.append("JSON-LD node needs @type")

    origin = urlsplit(canonical_url)
    home_url = f"{origin.scheme}://{origin.netloc}/"

    def resolves(value, expected_type):
        target = value if isinstance(value, dict) else {}
        if isinstance(target.get("@id"), str):
            target = identifiers.get(target["@id"], target)
        return expected_type in schema_types(target) and bool(target.get("name"))

    for required_type in ("WebSite", "WebPage", "Person"):
        if not any(required_type in schema_types(node) for node in nodes):
            errors.append(f"missing {required_type} JSON-LD")
    if canonical_url == home_url and not any("ProfilePage" in schema_types(node) for node in nodes):
        errors.append("homepage needs ProfilePage JSON-LD")

    for node in nodes:
        types = schema_types(node)
        for node_type in ("WebSite", "WebPage", "Person", "ProfilePage", "CreativeWork", "Organization"):
            if node_type in types and not (isinstance(node.get("name"), str) and node["name"].strip()):
                errors.append(f"{node_type} needs a nonempty name")
        if any(kind in types for kind in ("WebPage", "ProfilePage", "CreativeWork")) and node.get("url") != canonical_url:
            errors.append(f"{types}: url must match the page canonical")
        if "WebSite" in types and node.get("url") != home_url:
            errors.append("WebSite URL must identify the site root")
        if "Person" in types:
            links = node.get("sameAs")
            if not isinstance(links, list) or not links or not all(is_web_url(link) for link in links):
                errors.append("Person sameAs must contain absolute identity URLs")
            if node.get("url") != home_url:
                errors.append("Person URL must identify the profile homepage")
        if "ProfilePage" in types and not resolves(node.get("mainEntity"), "Person"):
            errors.append("ProfilePage mainEntity must resolve to a named Person")
        if any(kind in types for kind in ("CreativeWork", "Article")):
            if not resolves(node.get("author"), "Person"):
                errors.append(f"{types}: author must resolve to a named Person")
            if not resolves(node.get("mainEntityOfPage"), "WebPage"):
                errors.append(f"{types}: mainEntityOfPage must resolve to a WebPage")
    return errors


def modification_dates(page, relative, errors):
    dates = set()
    for node in page.structured_data:
        if not isinstance(node, dict):
            errors.append(f"{relative}: JSON-LD nodes must be objects")
            continue
        value = node.get("dateModified")
        if value is not None:
            try:
                dates.add(datetime.fromisoformat(value.replace("Z", "+00:00")))
            except (AttributeError, TypeError, ValueError):
                errors.append(f"{relative}: invalid JSON-LD dateModified {value!r}")
    if len(dates) > 1:
        errors.append(f"{relative}: inconsistent JSON-LD dateModified values")
    return dates


def check_site(directory):
    root = Path(directory).resolve()
    if not (root / "index.html").is_file():
        raise SystemExit(f"Build the site before checking it: {root}/index.html is missing")
    pages = {file: Page(file.read_text()) for file in root.rglob("*.html")}
    errors = []
    internal_hosts = {"chojecki.net", "www.chojecki.net", "patrykchojecki.github.io", "localhost", "127.0.0.1"}

    for file, page in pages.items():
        relative = file.relative_to(root).as_posix()
        canonical_path = "/" + relative.removesuffix("index.html")
        if not page.redirect:
            errors.extend(f"{relative}: {error}" for error in metadata_errors(page, f"https://chojecki.net{canonical_path}"))
        modification_dates(page, relative, errors)
        if relative.startswith("projects/") and not page.redirect:
            for schema_type in ("WebPage", "CreativeWork"):
                nodes = [node for node in page.structured_data if isinstance(node, dict) and node.get("@type") == schema_type]
                if schema_type == "WebPage" or relative != "projects/index.html":
                    if not nodes or any(not node.get("dateModified") for node in nodes):
                        errors.append(f"{relative}: expected {schema_type} with an explicit dateModified")
        if not page.redirect:
            if page.headings != 1 or not page.main:
                errors.append(f"{relative}: expected one h1 and a main landmark")
            for value, count in Counter(page.ids).items():
                if count > 1:
                    errors.append(f"{relative}: duplicate id {value!r}")

        for reference in page.references:
            url = urlsplit(urljoin(f"https://chojecki.net/{relative}", reference))
            if url.scheme not in ("http", "https") or url.hostname not in internal_hosts:
                continue
            target = (root / unquote(url.path).lstrip("/")).resolve()
            if not target.is_relative_to(root):
                errors.append(f"{relative}: path leaves the site: {reference}")
                continue
            if target.is_dir():
                target /= "index.html"
            elif not target.suffix and target.with_suffix(".html").is_file():
                target = target.with_suffix(".html")
            if not target.is_file():
                errors.append(f"{relative}: missing destination {reference}")
            elif url.fragment and target in pages and not pages[target].redirect:
                fragment = unquote(url.fragment).split(":~:text=", 1)[0]
                if fragment and fragment not in pages[target].ids:
                    errors.append(f"{relative}: missing fragment {reference}")

    for unwanted in (".geo", "scripts", "PRODUCT.md", "DESIGN", "design-qa.md", "AGENTS.md", "markdown", "non-menu-page", "archive-layout-with-content"):
        if (root / unwanted).exists():
            errors.append(f"Internal source or template demo was published: {unwanted}")

    sitemap = ElementTree.parse(root / "sitemap.xml")
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    entries = sitemap.findall("s:url", namespace)
    for entry in entries:
        location = entry.find("s:loc", namespace)
        target = root / unquote(urlsplit(location.text).path).lstrip("/")
        if target.is_dir():
            target /= "index.html"
        if not target.is_file():
            errors.append(f"Sitemap points to missing file: {location.text}")
        elif target in pages:
            errors.extend(f"{location.text}: {error}" for error in metadata_errors(pages[target], location.text, require_indexable=True))
            dates = modification_dates(pages[target], target.relative_to(root).as_posix(), errors)
            lastmod = entry.findtext("s:lastmod", namespaces=namespace)
            # lastmod is optional outside the explicitly dated project pages.
            if dates and (lastmod is not None or target.is_relative_to(root / "projects")):
                try:
                    if datetime.fromisoformat(lastmod.replace("Z", "+00:00")) not in dates:
                        errors.append(f"Sitemap lastmod differs from JSON-LD dateModified: {location.text}")
                except (AttributeError, ValueError):
                    errors.append(f"Sitemap needs a valid lastmod matching JSON-LD: {location.text}")

    if errors:
        raise SystemExit("Site checks failed:\n" + "\n".join(sorted(set(errors))))
    print(f"Site checks passed: {len(pages)} HTML files, internal links, fragments, assets, landmarks, JSON-LD, and {len(entries)} sitemap entries with consistent revision dates.")


if __name__ == "__main__":
    check_site(sys.argv[1] if len(sys.argv) > 1 else "_site")
