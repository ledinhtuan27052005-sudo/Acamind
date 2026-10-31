import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.scientific_appraiser import compute_cross_study_concordance


class CrossStudyConcordanceTests(unittest.TestCase):
    def test_rhetorical_keywords_never_produce_a_verdict(self):
        for text in ("Neutral methods text.", "support confirm similarly " * 30,
                     "however contrary to conflicting " * 30,
                     "đồng thuận phù hợp với mâu thuẫn ngược lại " * 30):
            with self.subTest(text=text[:30]):
                result = compute_cross_study_concordance([
                    {"document_id": "a", "content": text},
                    {"document_id": "b", "content": text},
                ])
                self.assertEqual(result["concordance_level"], "INSUFFICIENT_EVIDENCE")
                self.assertIsNone(result["concordance_score"])
                self.assertEqual(result["unique_documents_retrieved"], 2)
                self.assertEqual(result["unique_documents_compared"], 0)
                self.assertEqual(result["assessed_pairs"], 0)

    def test_no_sources_is_insufficient_not_high_confidence(self):
        for chunks in ([], [{"content": "consistent with prior work"}]):
            result = compute_cross_study_concordance(chunks)
            self.assertEqual(result["reason"], "no_identified_sources")
            self.assertIsNone(result["concordance_score"])

    def test_multiple_pages_of_one_document_are_not_multiple_studies(self):
        result = compute_cross_study_concordance([
            {"document_id": "a", "page_number": page} for page in range(1, 6)
        ])
        self.assertEqual(result["concordance_level"], "NOT_APPLICABLE")
        self.assertEqual(result["unique_documents_retrieved"], 1)
        self.assertIsNone(result["concordance_score"])

    def test_filename_fallback_and_json_null(self):
        result = compute_cross_study_concordance([
            {"doc_filename": "a.pdf"}, {"doc_filename": "b.pdf"}
        ])
        self.assertEqual(result["unique_documents_retrieved"], 2)
        self.assertIsNone(json.loads(json.dumps(result))["concordance_score"])

    def test_prompt_has_no_unverified_numeric_concordance(self):
        from app.services.generator import build_psychology_prompt
        chunks = [
            {"document_id": key, "doc_filename": key + ".pdf", "page_number": 1,
             "content": "Participants completed a questionnaire about anxiety and depression. " * 3}
            for key in ("a", "b")
        ]
        for lang in ("vi", "en"):
            prompt = "\n".join(m["content"] for m in build_psychology_prompt("Compare A and B", chunks, lang=lang))
            self.assertIn("Chưa có chỉ số đồng thuận được kiểm chứng", prompt)
            self.assertNotIn("Concordance Index):", prompt)
            self.assertNotIn("CONVERGENT", prompt)


if __name__ == "__main__":
    unittest.main()
