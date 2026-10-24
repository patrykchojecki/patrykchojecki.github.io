"""Regression checks for Jekyll aliases and static-only hosting constraints."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from cloudflare_assets import IMMUTABLE, header_rules, optimize

spec = importlib.util.spec_from_file_location("cloudflare", Path(__file__).with_name("prepare-cloudflare.py"))
cloudflare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cloudflare)


class CloudflareTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        (self.root / "404.html").write_text("Not found")
        (self.root / "assets/css").mkdir(parents=True)
        (self.root / "assets/js").mkdir(parents=True)
        (self.root / "assets/webfonts").mkdir(parents=True)
        (self.root / "assets/webfonts/icons.woff2").write_bytes(b"font-one")
        (self.root / "assets/css/main.css").write_text('body{color:black}@font-face{src:url("../webfonts/icons.woff2")}')
        for name in ("main.min.js", "theme-toggle.js", "site-delight.js"):
            (self.root / "assets/js" / name).write_text('console.log("ok")')
        self.html = '<link rel="stylesheet" href="/assets/css/main.css?v=100"><script src="/assets/js/main.min.js?v=100" defer></script><a href="/cv/">CV</a>'
        (self.root / "index.html").write_text(self.html)
        (self.root / "redirects.json").write_text(json.dumps({
            "/about.html": "https://chojecki.net/",
            "/about/": "https://chojecki.net/",
            "/now.html": "https://chojecki.net/now/",
            "/resume": "https://chojecki.net/cv/",
        }))

    def test_extensionless_aliases_do_not_loop(self):
        cloudflare.prepare(self.root)
        rules = (self.root / "_redirects").read_text()
        for line in ["/about / 301", "/about.html / 301", "/about/ / 301",
                     "/now /now/ 301", "/now.html /now/ 301", "/resume /cv/ 301"]:
            self.assertIn(line + "\n", rules)
        self.assertNotIn("/now/ /now/", rules)

    def test_missing_404_cannot_enable_spa_fallback(self):
        (self.root / "404.html").unlink()
        with self.assertRaisesRegex(ValueError, "404.html"):
            cloudflare.prepare(self.root)

    def test_worker_cannot_silently_change_static_hosting(self):
        (self.root / "_worker.js").write_text("export default {}")
        with self.assertRaisesRegex(ValueError, "only static"):
            cloudflare.prepare(self.root)

    def test_external_redirect_is_rejected(self):
        (self.root / "redirects.json").write_text('{"/old":"https://unrelated.example/"}')
        with self.assertRaisesRegex(ValueError, "destination"):
            cloudflare.prepare(self.root)

    def test_identical_assets_keep_urls_across_activity_only_builds(self):
        first = optimize(self.root)
        (self.root / "index.html").write_text(self.html.replace("v=100", "v=200") + "Updated activity")
        second = optimize(self.root)
        self.assertEqual(first, second)
        self.assertNotIn("?v=", (self.root / "index.html").read_text())
        self.assertEqual((self.root / "assets/js/main.min.js").read_text(), 'console.log("ok")')
        self.assertIn('<a href="/cv/">CV</a>', (self.root / "index.html").read_text())

    def test_font_changes_invalidate_css_but_not_unrelated_scripts(self):
        first = optimize(self.root)
        (self.root / "assets/webfonts/icons.woff2").write_bytes(b"font-two")
        second = optimize(self.root)
        self.assertNotEqual(first["/assets/webfonts/icons.woff2"], second["/assets/webfonts/icons.woff2"])
        self.assertNotEqual(first["/assets/css/main.css"], second["/assets/css/main.css"])
        self.assertEqual(first["/assets/js/main.min.js"], second["/assets/js/main.min.js"])
        self.assertIn(second["/assets/webfonts/icons.woff2"], (self.root / second["/assets/css/main.css"].lstrip("/")).read_text())
        self.assertIn(second["/assets/css/main.css"], (self.root / "index.html").read_text())

    def test_only_hashed_assets_get_long_caching_and_hint_matches_html(self):
        mapping = optimize(self.root)
        rules = header_rules(self.root)
        immutable_paths = {route for route, headers in rules.items() if headers.get("cache-control") == IMMUTABLE}
        self.assertEqual(immutable_paths, set(mapping.values()))
        self.assertEqual(rules["/"], {"link": f'<{mapping["/assets/css/main.css"]}>; rel=preload; as=style'})
        self.assertNotIn("/assets/css/main.css", rules)
        self.assertNotIn("/robots.txt", rules)
        self.assertNotIn("/sitemap.xml", rules)

    def test_preparation_is_repeatable_and_preserves_external_urls(self):
        external = '<script src="https://example.com/assets/js/main.min.js?v=9"></script>'
        (self.root / "index.html").write_text(self.html + external)
        cloudflare.prepare(self.root)
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        cloudflare.prepare(self.root)
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertIn(external, (self.root / "index.html").read_text())

    def test_missing_css_resource_blocks_upload(self):
        (self.root / "assets/webfonts/icons.woff2").unlink()
        with self.assertRaisesRegex(ValueError, "CSS resource"):
            optimize(self.root)

    def test_symlinked_asset_directory_cannot_write_outside_upload(self):
        with tempfile.TemporaryDirectory() as external:
            (self.root / "outside").symlink_to(external, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "Symlinks"):
                cloudflare.prepare(self.root)


if __name__ == "__main__":
    unittest.main()
