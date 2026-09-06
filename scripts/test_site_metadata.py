"""Regression cases for the structured data and indexing contract."""

import importlib.util
import json
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("site_checker", Path(__file__).with_name("check-site.py"))
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

ORIGIN = "https://chojecki.net/"


def document(nodes, canonical=ORIGIN, robots="index, follow"):
    return f'<link rel="canonical" href="{canonical}"><meta name="robots" content="{robots}"><script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": nodes})}</script>'


def nodes():
    return [
        {"@type": "WebSite", "@id": ORIGIN + "#website", "name": "Site", "url": ORIGIN},
        {"@type": "WebPage", "@id": ORIGIN + "#webpage", "name": "Home", "url": ORIGIN},
        {"@type": "Person", "@id": ORIGIN + "#person", "name": "Patryk Chojecki", "url": ORIGIN, "sameAs": ["https://github.com/patrykchojecki"]},
        {"@type": "ProfilePage", "name": "Profile", "url": ORIGIN, "mainEntity": {"@id": ORIGIN + "#person"}},
    ]


class MetadataTests(unittest.TestCase):
    def check(self, source):
        return checker.metadata_errors(checker.Page(source), ORIGIN, require_indexable=True)

    def test_valid_linked_profile(self):
        self.assertEqual(self.check(document(nodes())), [])

    def test_broken_person_reference(self):
        data = nodes(); data[-1]["mainEntity"] = {"@id": ORIGIN + "#missing"}
        self.assertTrue(any("mainEntity" in error for error in self.check(document(data))))

    def test_duplicate_canonical(self):
        source = document(nodes()) + f'<link rel="canonical" href="{ORIGIN}">'
        self.assertTrue(any("one canonical" in error for error in self.check(source)))

    def test_wrong_page_url(self):
        data = nodes(); data[1]["url"] = "https://wrong.example/"
        self.assertTrue(any("canonical" in error for error in self.check(document(data))))

    def test_noindex_and_snippet_restrictions(self):
        for directive in ("noindex, follow", "none", "index, max-snippet: 0", "nosnippet"):
            with self.subTest(directive=directive):
                self.assertTrue(any("blocks indexing" in error for error in self.check(document(nodes(), robots=directive))))

    def test_empty_identity_links(self):
        data = nodes(); data[2]["sameAs"] = []
        self.assertTrue(any("sameAs" in error for error in self.check(document(data))))

    def test_invalid_graph_is_reported(self):
        for graph in (None, 42, {}, "bad", [1]):
            source = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@graph": graph}) + '</script>'
            with self.subTest(graph=graph):
                self.assertTrue(checker.Page(source).structured_data_errors)

    def test_non_json_constant_is_rejected(self):
        page = checker.Page('<script type="application/ld+json">{"@type":"Person","name":NaN}</script>')
        self.assertTrue(page.structured_data_errors)

    def test_dates_with_equivalent_offsets_agree(self):
        page = checker.Page(document([{"@type": "WebPage", "dateModified": "2026-09-03T10:24:15+08:00"}, {"@type": "CreativeWork", "dateModified": "2026-09-03T02:24:15Z"}]))
        errors = []
        self.assertEqual(len(checker.modification_dates(page, "example", errors)), 1)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
