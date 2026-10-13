"""Ensure the deployment gate rejects sensitive artifacts at any depth."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from test_site_metadata import ORIGIN, checker, document, nodes


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "index.html").write_text("<h1>Home</h1><main></main>" + document(nodes()))
        (self.root / "sitemap.xml").write_text(
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f'<url><loc>{ORIGIN}</loc></url></urlset>'
        )

    def test_normal_public_assets_pass(self):
        for name in ("assets/main.js", "images/profile.png", "data/public.json", ".well-known/security.txt"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("public content")
        with contextlib.redirect_stdout(io.StringIO()):
            checker.check_site(self.root)

    def test_sensitive_files_fail_the_deployment_gate(self):
        for name in (
            ".env", "nested/.env.production", "nested/private.pem", "nested/private.KEY",
            "nested/account.p12", "nested/account.pfx", "nested/id_rsa", "nested/deploy_rsa",
            "nested/id_ed25519", "nested/id_ecdsa", "nested/id_dsa",
            "nested/credentials-prod.json", "nested/secrets.json",
            "nested/.aws/credentials", "nested/.ssh/config", "nested/.git/config",
            "nested/.svn/entries", "nested/.bundle/config",
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory(dir=self.root) as folder:
                path = Path(folder) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("synthetic secret fixture")
                with self.assertRaises(SystemExit) as result:
                    checker.check_site(self.root)
                self.assertIn("Sensitive file or directory was published", str(result.exception))
                self.assertIn(name, str(result.exception))
                self.assertNotIn("synthetic secret fixture", str(result.exception))


if __name__ == "__main__":
    unittest.main()
