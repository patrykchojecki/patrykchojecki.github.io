"""Local build readers must reject paths escaping their selected directory."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_live_site import live
from test_site_metadata import ORIGIN, checker, document, nodes


class ContainmentTests(unittest.TestCase):
    @contextlib.contextmanager
    def build(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory).resolve()
            root = parent / "build"
            root.mkdir()
            (root / "index.html").write_text("<h1>Home</h1><main></main>" + document(nodes()))
            self.sitemap(root, "/")
            outside = parent / "outside.txt"
            outside.write_text("outside fixture must not be read")
            yield root, outside

    def sitemap(self, root, *paths):
        entries = "".join(f"<url><loc>{ORIGIN.rstrip('/')}{path}</loc></url>" for path in paths)
        (root / "sitemap.xml").write_text(
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + entries + "</urlset>"
        )

    @contextlib.contextmanager
    def contained_reads(self, root):
        original_open = Path.open

        def guarded_open(path, *args, **kwargs):
            self.assertTrue(path.resolve().is_relative_to(root), "attempted to open an outside file")
            return original_open(path, *args, **kwargs)

        with patch.object(Path, "open", guarded_open):
            yield

    def assert_rejected(self, root):
        with self.contained_reads(root):
            with self.assertRaisesRegex(ValueError, "path leaves build directory"):
                live.build_manifest(root, {"origin": ORIGIN.rstrip("/")})
            with self.assertRaisesRegex(SystemExit, "path leaves build directory"):
                checker.check_site(root)

    def test_sitemap_rejects_plain_and_encoded_traversal(self):
        for path in ("/../outside.txt", "/%2e%2e/outside.txt", "/%2e%2e%2foutside.txt"):
            with self.subTest(path=path), self.build() as (root, outside):
                self.sitemap(root, "/", path)
                self.assert_rejected(root)

    def test_sitemap_rejects_symlink_files_directories_and_index_leaves(self):
        for kind in ("file", "directory", "index"):
            with self.subTest(kind=kind), self.build() as (root, outside):
                if kind == "file":
                    (root / "alias.txt").symlink_to(outside)
                    path = "/alias.txt"
                elif kind == "directory":
                    (root / "alias").symlink_to(outside.parent, target_is_directory=True)
                    path = "/alias/"
                else:
                    (root / "alias").mkdir()
                    (root / "alias" / "index.html").symlink_to(outside)
                    path = "/alias/"
                self.sitemap(root, "/", path)
                self.assert_rejected(root)

    def test_sitemap_source_and_homepage_cannot_escape(self):
        for name in ("sitemap.xml", "index.html"):
            with self.subTest(name=name), self.build() as (root, outside):
                (root / name).unlink()
                (root / name).symlink_to(outside)
                self.assert_rejected(root)

    def test_html_discovery_rejects_unreferenced_outside_symlinks(self):
        with self.build() as (root, outside):
            (root / "unlisted.html").symlink_to(outside)
            with self.contained_reads(root):
                with self.assertRaisesRegex(SystemExit, "unlisted.html: path leaves build directory"):
                    checker.check_site(root)

    def test_internal_links_recheck_index_and_html_fallbacks(self):
        for kind in ("index", "extension"):
            with self.subTest(kind=kind), self.build() as (root, outside):
                if kind == "index":
                    (root / "alias").mkdir()
                    (root / "alias" / "index.html").symlink_to(outside)
                    reference = "/alias/"
                else:
                    (root / "alias.html").symlink_to(outside)
                    reference = "/alias"
                with (root / "index.html").open("a") as page:
                    page.write(f'<a href="{reference}">Link</a>')
                with self.contained_reads(root):
                    with self.assertRaises(SystemExit) as result:
                        checker.check_site(root)
                self.assertIn(f"index.html: path leaves build directory: {reference}", str(result.exception))

    def test_valid_indexes_encoded_assets_and_contained_symlinks_still_work(self):
        with self.build() as (root, outside):
            (root / "directory").mkdir()
            data = nodes()
            for node in (data[1], data[3]):
                node["url"] = ORIGIN + "directory/"
            (root / "directory" / "index.html").write_text(
                "<h1>Directory</h1><main></main>" + document(data, canonical=ORIGIN + "directory/")
            )
            (root / "asset name.pdf").write_bytes(b"%PDF-1.7 fixture")
            (root / "alias.pdf").symlink_to(root / "asset name.pdf")
            (root / "pretty.html").write_text('<meta http-equiv="refresh" content="0;url=/">')
            with (root / "index.html").open("a") as page:
                page.write('<a href="/pretty">Pretty URL</a><a href="/directory/">Directory</a>')
            self.sitemap(root, "/", "/directory/", "/asset%20name.pdf", "/alias.pdf")
            with self.contained_reads(root), contextlib.redirect_stdout(io.StringIO()):
                checker.check_site(root)
                manifest = live.build_manifest(root, {"origin": ORIGIN.rstrip("/")})
            self.assertEqual(set(manifest["metadata"]), {ORIGIN, ORIGIN + "directory/"})
            self.assertEqual(manifest["assets"][ORIGIN + "alias.pdf"], manifest["assets"][ORIGIN + "asset%20name.pdf"])


if __name__ == "__main__":
    unittest.main()
