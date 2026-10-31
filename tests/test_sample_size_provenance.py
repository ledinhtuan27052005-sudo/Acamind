import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.scientific_appraiser import harmonize_cross_study_metrics


class SampleSizeProvenanceTests(unittest.TestCase):
    def result(self, text, **extra):
        return harmonize_cross_study_metrics([
            {"document_id": "a", "doc_filename": "a.pdf", "content": text, "page_number": 4, **extra}
        ])

    def test_largest_value_is_not_selected(self):
        result = self.result("Our study recruited 120 participants. Smith (2020) reported N = 900.")
        study = result["studies"][0]
        self.assertIsNone(study["sample_n"])
        self.assertEqual(study["sample_size_status"], "ambiguous")
        self.assertEqual([c["value"] for c in study["sample_size_candidates"]], [120, 900])
        self.assertIn("không chọn số lớn nhất", result["prompt_summary"])

    def test_single_number_is_not_assumed_to_be_study_total(self):
        for text in ("Smith (2020) recruited 900 participants.", "Control group: n = 40.",
                     "Planned N = 200", "At follow-up N = 80", "Participants (N = 180) completed BDI-II."):
            with self.subTest(text=text):
                study = self.result(text)["studies"][0]
                self.assertIsNone(study["sample_n"])
                self.assertEqual(study["sample_size_status"], "unverified")

    def test_original_page_quote_and_offsets_are_preserved(self):
        text = "Methods: N = 1,200 participants were enrolled."
        study = self.result(text)["studies"][0]
        candidate = study["sample_size_candidates"][0]
        self.assertEqual(candidate["value"], 1200)
        self.assertEqual(candidate["page"], 4)
        self.assertEqual(candidate["document_id"], "a")
        self.assertEqual(text[candidate["start"]:candidate["end"]], candidate["quote"])
        self.assertEqual(candidate["source_text"], text)

    def test_parent_context_cannot_supply_wrong_page_evidence(self):
        study = self.result("Methods section", parent_context="Previous page N = 800")["studies"][0]
        self.assertEqual(study["sample_size_status"], "missing")
        self.assertEqual(study["sample_size_candidates"], [])

    def test_duplicate_chunks_do_not_duplicate_mentions(self):
        chunk = {"document_id": "a", "page_number": 2, "content": "N = 100"}
        study = harmonize_cross_study_metrics([chunk, dict(chunk)])["studies"][0]
        self.assertEqual(len(study["sample_size_candidates"]), 1)
        self.assertIsNone(study["sample_n"])

    def test_invalid_numeric_mentions_are_not_truncated(self):
        for text in ("N = -10", "N = 0", "N = 12.5", "N = 1,20"):
            self.assertEqual(self.result(text)["studies"][0]["sample_size_candidates"], [])

    def test_small_vietnamese_sample_and_missing_page(self):
        study = self.result("Có 8 người tham gia", page_number=None)["studies"][0]
        self.assertEqual(study["sample_size_candidates"][0]["value"], 8)
        self.assertIsNone(study["sample_size_candidates"][0]["page"])


if __name__ == "__main__":
    unittest.main()
