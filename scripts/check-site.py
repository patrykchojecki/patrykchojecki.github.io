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
        self.json_ld = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
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
                data = json.loads("".join(self.json_ld))
                nodes = data if isinstance(data, list) else [data]
                for node in nodes:
                    if not isinstance(node, dict):
                        raise ValueError("JSON-LD nodes must be objects")
                    self.structured_data.extend(node.get("@graph", [node]))
            except ValueError as error:
                self.structured_data_errors.append(str(error))
            self.json_ld = None


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
        for error in page.structured_data_errors:
            errors.append(f"{relative}: invalid JSON-LD: {error}")
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

    for unwanted in ("scripts", "PRODUCT.md", "DESIGN", "design-qa.md", "AGENTS.md", "markdown", "non-menu-page", "archive-layout-with-content"):
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
