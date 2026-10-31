import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.scientific_appraiser import compute_meta_analysis_forest_plot


class MetaAnalysisSampleSizeTests(unittest.TestCase):
    def test_missing_sample_blocks_statistics_for_every_evidence_level(self):
        for level in ("1a", "1b", "2b", "5"):
            with self.subTest(level=level):
                result = compute_meta_analysis_forest_plot([
                    {"filename": "missing.pdf", "cebm_level": level, "finding": "d = 0.50"}
                ])
                self.assertEqual(result["status"], "insufficient_data")
                self.assertEqual(result["studies"], [])
                self.assertIsNone(result["missing_sample_studies"][0]["sample_n"])
                for key in ("pooled_effect", "pooled_se", "pooled_ci_lower", "p_value_str", "total_sample_n"):
                    self.assertNotIn(key, result)

    def test_mixed_input_does_not_silently_pool_only_complete_studies(self):
        result = compute_meta_analysis_forest_plot([
            {"filename": "complete.pdf", "methodology": "N = 120", "finding": "d = 0.50"},
            {"filename": "missing.pdf", "finding": "d = 0.60"},
        ])
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["k_studies"], 0)
        self.assertEqual([s["filename"] for s in result["missing_sample_studies"]], ["missing.pdf"])

    def test_unsupported_sample_is_not_replaced(self):
        for sample in (0, 10, 9000):
            with self.subTest(sample=sample):
                result = compute_meta_analysis_forest_plot([
                    {"methodology": f"N = {sample}", "finding": "d = 0.50"}
                ])
                self.assertEqual(result["status"], "insufficient_data")

    def test_sample_sizes_alone_do_not_establish_poolability(self):
        result = compute_meta_analysis_forest_plot([
            {"methodology": "N = 120", "finding": "d = 0.50"},
            {"methodology": "200 participants", "finding": "d = 0.60"},
        ])
        self.assertEqual(result["status"], "insufficient_data")
        self.assertNotIn("total_sample_n", result)

    def test_empty_input_has_no_studies(self):
        self.assertEqual(compute_meta_analysis_forest_plot([])["studies"], [])


if __name__ == "__main__":
    unittest.main()
