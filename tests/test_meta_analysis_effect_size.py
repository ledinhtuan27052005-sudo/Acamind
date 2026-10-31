import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.scientific_appraiser import compute_meta_analysis_forest_plot


class MetaAnalysisEffectSizeTests(unittest.TestCase):
    def row(self, finding, **extra):
        return {"filename": "study.pdf", "methodology": "N = 120", "finding": finding, **extra}

    def test_missing_effect_never_inferred_from_metadata(self):
        for level in ("1a", "1b", "2b", "5"):
            result = compute_meta_analysis_forest_plot([
                self.row("Improvement reported", cebm_level=level, title="Different study", cebm_weight=0.9)
            ])
            self.assertEqual(result["status"], "insufficient_data")
            self.assertIsNone(result["missing_effect_studies"][0]["effect_size"])
            self.assertNotIn("pooled_effect", result)

    def test_no_unsupported_conversions(self):
        for finding in ("Response 85%", "r = 0.70", "F1 = 0.80", "AUC = 0.90", "accuracy = 0.95", "OR = 2.5"):
            with self.subTest(finding=finding):
                result = compute_meta_analysis_forest_plot([self.row(finding)])
                self.assertEqual(result["status"], "insufficient_data")
                self.assertEqual(result["studies"], [])

    def test_mixed_studies_do_not_silently_drop_missing_effect(self):
        result = compute_meta_analysis_forest_plot([self.row("d = 0.5"), self.row("Response 80%", filename="missing.pdf")])
        self.assertEqual(result["status"], "insufficient_data")
        self.assertEqual(result["missing_effect_studies"][0]["filename"], "missing.pdf")
        self.assertNotIn("pooled_ci_lower", result)

    def test_reported_g_alone_does_not_establish_variance(self):
        for value in (-0.5, 0, 0.1, 2.0):
            with self.subTest(value=value):
                result = compute_meta_analysis_forest_plot([self.row(f"Hedges' g = {value}.")])
                self.assertEqual(result["status"], "insufficient_data")
                self.assertNotIn("pooled_effect", result)

    def test_cohens_d_without_design_is_not_converted(self):
        for value in (-0.5, 0, 0.1, 2.0):
            result = compute_meta_analysis_forest_plot([self.row(f"Cohen's d = {value}")])
            self.assertEqual(result["status"], "insufficient_data")

    def test_unicode_minus(self):
        result = compute_meta_analysis_forest_plot([self.row("g = −0.40")])
        self.assertEqual(result["status"], "insufficient_data")


if __name__ == "__main__":
    unittest.main()
