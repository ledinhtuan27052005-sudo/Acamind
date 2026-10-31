import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.scientific_appraiser import (
    _extract_sample_size_candidates,
    compute_meta_analysis_forest_plot,
    extract_structured_study_cells,
)
from app.services.study_profile import build_study_profile
from app.services.study_comparability import validate_comparability


class LiteratureExtractionRegressionTests(unittest.TestCase):
    def test_sample_is_not_misclassified_as_scale(self):
        source = "Synthetic CBT Anxiety Study A\nRandomized trial with 40 adult students. CBT group n=20; waitlist n=20."
        cells = extract_structured_study_cells(
            "browser_study_a", "browser_study_a.pdf",
            [{"content": source, "page_number": 1}],
            {("browser_study_a.pdf", 1): source},
        )
        self.assertIn("Randomized trial with 40 adult students", cells["methodology"])
        self.assertEqual(cells["scale_or_metric"], "Chưa tìm thấy câu mô tả chỉ số")
        candidates = _extract_sample_size_candidates([{"content": source, "page_number": 1}])["sample_size_candidates"]
        self.assertIn(40, [candidate["value"] for candidate in candidates])

    def test_study_profile_exposes_sample_candidate_without_verifying_it(self):
        document = {"document_id": "study-a", "filename": "a.pdf", "title": "Study A"}
        chunks = [{"document_id": "study-a", "page_number": 1,
                   "content": "Randomized trial with 40 adult students. CBT group n=20; waitlist n=20."}]
        profile = build_study_profile(document, chunks)
        self.assertEqual(profile["fields"]["sample"]["status"], "unverified")
        self.assertIn("40 adult students", profile["fields"]["sample"]["candidates"][0]["quote"])

    def test_sample_candidate_does_not_authorize_meta_analysis(self):
        result = compute_meta_analysis_forest_plot([{
            "document_id": "study-a", "filename": "a.pdf",
            "methodology": "Randomized trial with 40 adult students.",
            "sample_size_candidates": [{"value": 40, "page": 1, "quote": "40 adult students"}],
        }])
        self.assertEqual(result["status"], "insufficient_data")
        self.assertTrue(result["missing_sample_studies"][0]["has_unverified_candidate"])

    def test_unreported_comparator_is_not_a_proven_difference(self):
        a = [{"source": "0", "document_id": "a", "page": 1,
              "text": "Weekly CBT was reported for 6 weeks."}]
        b = [{"source": "0", "document_id": "b", "page": 1,
              "text": "CBT group n=20; waitlist n=20."}]
        raw = {"criteria": [{"key": "comparator", "status": "different",
                             "reason": "Study A does not report any comparator; Study B reports a waitlist.",
                             "evidence_a": {"source": "0", "quote": a[0]["text"]},
                             "evidence_b": {"source": "0", "quote": b[0]["text"]}}]}
        result = validate_comparability(raw, a, b)
        self.assertEqual(result["criteria"][4]["status"], "unknown")
        self.assertEqual(result["status"], "insufficient_data")


if __name__ == "__main__":
    unittest.main()
