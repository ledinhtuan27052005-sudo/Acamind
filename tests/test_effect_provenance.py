import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.scientific_appraiser import harmonize_cross_study_metrics


class EffectProvenanceTests(unittest.TestCase):
    def chunk(self, text, **extra):
        return {"document_id": "a", "doc_filename": "a.pdf", "page_number": 4, "content": text, **extra}

    def profile(self, *chunks):
        return harmonize_cross_study_metrics(list(chunks))["studies"][0]

    def test_all_effects_retained_without_first_selection(self):
        text = "Smith (2020): d = 0.9. Our outcome A: g = -0.3; outcome B: OR = 0.8."
        profile = self.profile(self.chunk(text))
        self.assertEqual(profile["effect_status"], "ambiguous")
        self.assertIsNone(profile["effect_value"])
        self.assertEqual([(c["effect_type"], c["effect_value"]) for c in profile["effect_candidates"]],
                         [("d", 0.9), ("g", -0.3), ("OR", 0.8)])
        for c in profile["effect_candidates"]:
            self.assertEqual(c["quote"], text[c["start"]:c["end"]])
            self.assertEqual(c["source_text"], text)
            self.assertEqual(c["page"], 4)
            self.assertEqual(c["document_id"], "a")

    def test_single_cited_or_subgroup_effect_is_not_promoted(self):
        for text in ("Smith (2020) reported d = 0.8", "Control subgroup g = -0.2", "At follow-up r = .3"):
            profile = self.profile(self.chunk(text))
            self.assertEqual(profile["effect_status"], "unverified")
            self.assertIsNone(profile["effect_value"])
            self.assertIsNone(profile["raw_effect"])

    def test_parent_context_does_not_supply_wrong_page(self):
        profile = self.profile(self.chunk("No effect mentioned here", parent_context="Earlier page d = 0.7"))
        self.assertEqual(profile["effect_status"], "missing")

    def test_duplicate_chunks_removed_but_distinct_pages_kept(self):
        chunk = self.chunk("d = 0.4")
        profile = self.profile(chunk, dict(chunk), self.chunk("d = 0.4", page_number=7))
        self.assertEqual([c["page"] for c in profile["effect_candidates"]], [4, 7])
        self.assertEqual(profile["effect_status"], "ambiguous")

    def test_missing_page_is_not_invented(self):
        profile = self.profile(self.chunk("d = -0.4", page_number=None))
        self.assertIsNone(profile["effect_candidates"][0]["page"])

    def test_malformed_numbers_not_partially_parsed(self):
        for text in ("d = 0,35", "d = 1.2e-3", "d = 1.2.3"):
            self.assertEqual(self.profile(self.chunk(text))["effect_candidates"], [])

    def test_nonfinite_value_is_not_serialized_as_infinity(self):
        profile = self.profile(self.chunk("d = " + "9" * 400))
        candidate = profile["effect_candidates"][0]
        self.assertFalse(candidate["effect_valid"])
        self.assertIsNone(candidate["effect_value"])
        json.dumps(profile, allow_nan=False)

    def test_prompt_reports_candidates_not_representative_result(self):
        result = harmonize_cross_study_metrics([self.chunk("d = 0.8; d = -0.4")])
        self.assertIn("không chọn giá trị đầu tiên", result["prompt_summary"])
        self.assertIn("d = 0.8", result["prompt_summary"])
        self.assertIn("d = -0.4", result["prompt_summary"])


if __name__ == "__main__":
    unittest.main()
