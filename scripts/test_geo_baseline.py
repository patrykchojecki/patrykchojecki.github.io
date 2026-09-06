"""Protect baseline denominators and citation attribution."""

import importlib.util
import unittest
from datetime import date
from pathlib import Path

spec = importlib.util.spec_from_file_location("baseline", Path(__file__).parent / "geo" / "baseline.py")
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.data = baseline.new_baseline(date(2026, 9, 6))

    def test_pending_is_not_zero_visibility(self):
        summary = baseline.summarize(self.data)
        self.assertIsNone(summary["engines"]["chatgpt"]["citation_rate"])
        self.assertEqual(summary["next_review"], "2026-09-20")

    def test_mentions_and_citations_are_separate(self):
        row = self.data["observations"][0]
        row.update(status="observed", mentioned=True, evidence="Reviewed answer; no site links")
        result = baseline.summarize(self.data)["engines"]["chatgpt"]
        self.assertEqual((result["observed"], result["mentions"], result["answers_citing_site"]), (1, 1, 0))

    def test_citation_requires_exact_site_host(self):
        for url in ("https://chojecki.net.example/", "https://example.org/?q=chojecki.net", "https://chojecki.net@example.org/"):
            self.assertFalse(baseline.own_citation(url))
        self.assertTrue(baseline.own_citation("https://chojecki.net/cv/?utm_source=chatgpt.com"))

    def test_duplicate_or_missing_observations_rejected(self):
        self.data["observations"].pop()
        with self.assertRaises(ValueError):
            baseline.summarize(self.data)

    def test_unavailable_cannot_claim_a_score(self):
        self.data["observations"][0].update(status="unavailable", mentioned=False)
        with self.assertRaises(ValueError):
            baseline.summarize(self.data)


if __name__ == "__main__":
    unittest.main()
