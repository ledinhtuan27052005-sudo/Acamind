import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.scientific_appraiser import harmonize_cross_study_metrics


class HarmonizationDirectionTests(unittest.TestCase):
    def profile(self, text):
        return harmonize_cross_study_metrics([
            {"document_id": "a", "content": text, "page_number": 2}
        ])["studies"][0]

    def test_d_preserves_sign_zero_and_precision(self):
        for value in (-0.54321, 0, 0.54321, 2):
            with self.subTest(value=value):
                profile = self.profile(f"Cohen's d = {value}.")["effect_candidates"][0]
                self.assertEqual(profile["effect_value"], value)
                self.assertIsNone(profile["harmonized_cohen_d"])
                self.assertTrue(profile["effect_valid"])
                self.assertEqual(profile["direction_status"], "reported_direction_only")

    def test_g_keeps_its_type_and_sign(self):
        profile = self.profile("Hedges’ g = −.45")["effect_candidates"][0]
        self.assertEqual(profile["effect_type"], "g")
        self.assertEqual(profile["effect_value"], -0.45)
        self.assertIsNone(profile["harmonized_cohen_d"])
        self.assertIn("g = -0.45", profile["raw_effect"])

    def test_r_and_or_are_not_clipped_or_unconditionally_converted(self):
        for metric, value in (("r", -1), ("r", -0.5), ("r", 1), ("OR", 0.005), ("OR", 1), ("OR", 2)):
            with self.subTest(metric=metric, value=value):
                profile = self.profile(f"{metric} = {value}")["effect_candidates"][0]
                self.assertEqual(profile["effect_value"], value)
                self.assertTrue(profile["effect_valid"])
                self.assertIsNone(profile["harmonized_cohen_d"])

    def test_invalid_metrics_are_flagged_not_repaired(self):
        for text in ("r = 1.2", "r = -1.2", "OR = 0", "OR = -2"):
            profile = self.profile(text)["effect_candidates"][0]
            self.assertFalse(profile["effect_valid"])
            self.assertIsNone(profile["harmonized_cohen_d"])

    def test_opposite_effects_remain_opposite_in_profiles_and_prompt(self):
        result = harmonize_cross_study_metrics([
            {"document_id": "a", "content": "d = -0.5"},
            {"document_id": "b", "content": "d = 0.5"},
        ])
        self.assertEqual([s["effect_candidates"][0]["effect_value"] for s in result["studies"]], [-0.5, 0.5])
        self.assertTrue(all(s["harmonized_cohen_d"] is None for s in result["studies"]))
        self.assertIn("d = -0.5", result["prompt_summary"])
        self.assertIn("d = 0.5", result["prompt_summary"])
        self.assertIn("chưa xác minh chiều thang đo", result["prompt_summary"])

    def test_missing_effect_is_unknown(self):
        profile = self.profile("No effect estimate was reported.")
        self.assertIsNone(profile["effect_value"])
        self.assertIsNone(profile["harmonized_cohen_d"])
        self.assertIsNone(profile["effect_valid"])


if __name__ == "__main__":
    unittest.main()
