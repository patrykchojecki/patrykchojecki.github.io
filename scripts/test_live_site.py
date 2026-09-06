"""Published-response regression cases; no external network required."""

import copy
import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path

from test_site_metadata import document, nodes, ORIGIN

spec = importlib.util.spec_from_file_location("live_checker", Path(__file__).with_name("check-live-site.py"))
live = importlib.util.module_from_spec(spec)
spec.loader.exec_module(live)


class LiveTests(unittest.TestCase):
    def setUp(self):
        self.targets = {"origin": ORIGIN.rstrip("/"), "sitemap": ORIGIN + "sitemap.xml",
                        "pages": ["/"], "search_crawlers": ["Googlebot", "OAI-SearchBot", "Claude-SearchBot", "PerplexityBot"]}
        self.sitemap = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>' + ORIGIN + '</loc></url></urlset>'
        self.html = '<h1>Profile</h1><main></main>' + document(nodes())
        self.responses = {
            ORIGIN: (200, {"Content-Type": "text/html"}, self.html.encode()),
            ORIGIN + "sitemap.xml": (200, {"Content-Type": "application/xml"}, self.sitemap.encode()),
            ORIGIN + "robots.txt": (200, {"Content-Type": "text/plain"}, ('User-agent: *\nAllow: /\nSitemap: ' + ORIGIN + 'sitemap.xml').encode()),
        }

    def audit(self, expected=None):
        return live.audit(self.targets, expected, fetcher=lambda url: self.responses[url])["errors"]

    def test_healthy_responses(self):
        self.assertEqual(self.audit(), [])

    def test_ci_requires_a_manifest_before_fetching(self):
        result = subprocess.run([sys.executable, str(Path(live.__file__)), "--require-manifest"],
                                env={**os.environ, "EXPECTED_SITE_MANIFEST": ""}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("nonempty build manifest is required", result.stderr)

    def test_redirect_or_http_failure(self):
        for status in (301, 403, 404, 503):
            with self.subTest(status=status):
                self.responses[ORIGIN] = (status, {}, b"")
                self.assertTrue(any(f"HTTP {status}" in e for e in self.audit()))

    def test_robots_blocks_search_crawler(self):
        self.responses[ORIGIN + "robots.txt"] = (200, {"Content-Type": "text/plain"}, b'User-agent: OAI-SearchBot\nDisallow: /')
        self.assertTrue(any("blocks OAI-SearchBot" in e for e in self.audit()))

    def test_noindex_http_header(self):
        self.responses[ORIGIN] = (200, {"Content-Type": "text/html", "X-Robots-Tag": "googlebot: noindex"}, self.html.encode())
        self.assertTrue(any("X-Robots-Tag" in e for e in self.audit()))

    def test_noindex_meta_and_wrong_canonical(self):
        source = '<h1>Profile</h1><main></main>' + document(nodes(), canonical="https://wrong.example/", robots="noindex")
        self.responses[ORIGIN] = (200, {"Content-Type": "text/html"}, source.encode())
        errors = self.audit()
        self.assertTrue(any("canonical" in e for e in errors))
        self.assertTrue(any("blocks indexing" in e for e in errors))

    def test_missing_critical_page(self):
        self.targets["pages"].append("/projects/")
        self.assertTrue(any("critical page absent" in e for e in self.audit()))

    def test_stale_deployed_metadata(self):
        expected = {"sitemap": {ORIGIN: None}, "metadata": {ORIGIN: live.metadata_fingerprint(live.site.Page(self.html))}}
        self.assertEqual(self.audit(expected), [])
        stale = copy.deepcopy(expected); stale["metadata"][ORIGIN] = "stale"
        self.assertTrue(any("differs from the build" in e for e in self.audit(stale)))

    def test_mismatched_revision_date(self):
        data = nodes(); data[1]["dateModified"] = "2026-09-03T02:24:15Z"
        self.responses[ORIGIN] = (200, {"Content-Type": "text/html"}, ('<h1>Profile</h1><main></main>' + document(data)).encode())
        self.responses[ORIGIN + "sitemap.xml"] = (200, {"Content-Type": "application/xml"}, self.sitemap.replace('</url>', '<lastmod>2026-08-01T00:00:00Z</lastmod></url>').encode())
        self.assertTrue(any("lastmod differs" in e for e in self.audit()))

    def test_sitemap_cannot_fetch_external_or_duplicate_urls(self):
        for body in (self.sitemap.replace(ORIGIN, 'https://other.example/'), self.sitemap.replace('</urlset>', '<url><loc>' + ORIGIN + '</loc></url></urlset>')):
            with self.subTest(body=body):
                with self.assertRaises(ValueError):
                    live.sitemap_entries(body, ORIGIN.rstrip('/'))

    def test_html_challenge_instead_of_robots(self):
        self.responses[ORIGIN + "robots.txt"] = (200, {"Content-Type": "text/html"}, b'<html>Verify you are human</html>')
        self.assertTrue(any("plain text" in e for e in self.audit()))

    def test_pdf_checkout_date_is_ignored_but_changed_bytes_fail(self):
        url = ORIGIN + "cv.pdf"
        pdf = b"%PDF-1.7 example"
        xml = self.sitemap.replace('</urlset>', f'<url><loc>{url}</loc><lastmod>2026-09-06</lastmod></url></urlset>')
        self.responses[ORIGIN + "sitemap.xml"] = (200, {"Content-Type": "application/xml"}, xml.encode())
        self.responses[url] = (200, {"Content-Type": "application/pdf"}, pdf)
        expected = {"sitemap": {ORIGIN: None, url: "2026-04-25"},
                    "metadata": {ORIGIN: live.metadata_fingerprint(live.site.Page(self.html))},
                    "assets": {url: live.hashlib.sha256(pdf).hexdigest()}}
        self.assertEqual(self.audit(expected), [])
        self.responses[url] = (200, {"Content-Type": "application/pdf"}, pdf + b" changed")
        self.assertTrue(any("asset differs" in e for e in self.audit(expected)))


if __name__ == "__main__":
    unittest.main()
