"""Regression checks for Jekyll aliases and static-only hosting constraints."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("cloudflare", Path(__file__).with_name("prepare-cloudflare.py"))
cloudflare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cloudflare)


class CloudflareTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        (self.root / "404.html").write_text("Not found")
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


if __name__ == "__main__":
    unittest.main()
