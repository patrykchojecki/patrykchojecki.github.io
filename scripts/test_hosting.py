"""Hosting verification must tolerate propagation without accepting stale assets."""

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("hosting", Path(__file__).with_name("check-hosting.py"))
hosting = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hosting)


class HostingTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        (self.root / "index.html").write_text('<h1>Projects</h1><main></main>')
        (self.root / "redirects.json").write_text('{}')
        (self.root / "_redirects").write_text('')
        self.link = '</assets/css/main.0123456789abcdef.css>; rel=preload; as=style'
        (self.root / "_headers").write_text('/\n  Link: ' + self.link + '\n')
        self.requests = 0

    def responses(self, stale_attempts):
        def fetch(url):
            if url.endswith('/__hosting-check-missing-7d9c2a__'):
                return 404, {}, b''
            if url.endswith('/redirects.json'):
                return 200, {}, b'{}'
            self.requests += 1
            link = 'stale stylesheet' if self.requests <= stale_attempts else self.link
            return 200, {'Link': link, 'Cache-Control': 'public, max-age=0'}, (self.root / 'index.html').read_bytes()
        return fetch

    def test_stale_header_is_rechecked_until_it_matches(self):
        with patch.object(hosting.live, 'fetch', self.responses(1)), patch.object(hosting.time, 'sleep') as sleep:
            hosting.check_with_retries(self.root, 'https://preview.example', attempts=3, retry_delay=20)
        self.assertEqual(self.requests, 2)
        sleep.assert_called_once_with(20)

    def test_persistent_mismatch_still_blocks_deployment(self):
        with patch.object(hosting.live, 'fetch', self.responses(3)), patch.object(hosting.time, 'sleep') as sleep:
            with self.assertRaisesRegex(SystemExit, '/: unexpected link header'):
                hosting.check_with_retries(self.root, 'https://preview.example', attempts=3, retry_delay=20)
        self.assertEqual(self.requests, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_success_does_not_wait_or_retry(self):
        with patch.object(hosting.live, 'fetch', self.responses(0)), patch.object(hosting.time, 'sleep') as sleep:
            hosting.check_with_retries(self.root, 'https://preview.example', attempts=3)
        self.assertEqual(self.requests, 1)
        sleep.assert_not_called()

    def test_default_still_fails_on_first_mismatch(self):
        with patch.object(hosting.live, 'fetch', self.responses(1)), patch.object(hosting.time, 'sleep') as sleep:
            with self.assertRaises(SystemExit):
                hosting.check_with_retries(self.root, 'https://preview.example')
        self.assertEqual(self.requests, 1)
        sleep.assert_not_called()


if __name__ == '__main__':
    unittest.main()
