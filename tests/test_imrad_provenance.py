import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.scientific_appraiser import classify_imrad_section


class ImradProvenanceTests(unittest.TestCase):
    def test_participants_in_outcome_sentence_does_not_imply_methods(self):
        result = classify_imrad_section(
            "Results showed a significant reduction in depression among participants."
        )
        self.assertEqual(result["section_code"], "RESULTS")
        self.assertEqual(result["section_basis"], "keyword_heuristic")
        self.assertEqual(result["claim_origin"], "unverified")

    def test_keywords_and_numbers_do_not_certify_original_results(self):
        result = classify_imrad_section("Results were significant (p < 0.01), as Smith (2020) reported.", 2)
        self.assertEqual(result["section_code"], "RESULTS")
        self.assertEqual(result["section_basis"], "keyword_heuristic")
        self.assertEqual(result["claim_origin"], "unverified")
        self.assertTrue(result["has_secondary_citations"])
        self.assertNotIn("thực nghiệm gốc", result["section_label"])

    def test_explicit_heading_precedes_body_keywords(self):
        result = classify_imrad_section("## 1. Introduction\nPrior results were significant (p < 0.05).", 12)
        self.assertEqual(result["section_code"], "INTRODUCTION")
        self.assertEqual(result["section_basis"], "explicit_heading")
        self.assertEqual(result["claim_origin"], "unverified")

    def test_single_citation_warns_even_in_methods_and_results(self):
        for heading in ("Methods", "Results"):
            for citation in ("[1]", "[2, 3]", "Smith (2020)", "Smith et al. (2020)", "(Smith, 2020)"):
                with self.subTest(heading=heading, citation=citation):
                    result = classify_imrad_section(f"{heading}\nA finding was reported {citation}.")
                    self.assertTrue(result["has_secondary_citations"])
                    self.assertIn("Có dấu hiệu trích dẫn", result["guard_note"])

    def test_page_number_does_not_invent_structure(self):
        for page in (1, 2, 10, None, "unknown"):
            result = classify_imrad_section("Some text without structural cues.", page)
            self.assertEqual(result["section_code"], "UNKNOWN")

    def test_no_citation_does_not_prove_ownership(self):
        result = classify_imrad_section("Results\nThe effect was d = 0.5.", 1)
        self.assertFalse(result["has_secondary_citations"])
        self.assertEqual(result["claim_origin"], "unverified")
        self.assertIn("không xác nhận", result["guard_note"])

    def test_multiple_sections_are_not_assigned_one_role(self):
        result = classify_imrad_section("Methods\nParticipants were recruited.\nResults\nWe found an effect.")
        self.assertEqual(result["section_code"], "MIXED")
        self.assertEqual(result["section_basis"], "multiple_headings")

    def test_vietnamese_heading(self):
        result = classify_imrad_section("3. Kết quả nghiên cứu\nGiá trị d = 0.4.")
        self.assertEqual(result["section_code"], "RESULTS")
        self.assertEqual(result["section_basis"], "explicit_heading")

    def test_prompt_exposes_origin_warning(self):
        from app.services.generator import build_psychology_prompt
        messages = build_psychology_prompt("Compare findings", [{
            "doc_filename": "a.pdf", "page_number": 6,
            "content": "Results\nA significant effect was reported by Smith (2020)."
        }], lang="vi")
        prompt = "\n".join(m["content"] for m in messages)
        self.assertIn("Nhãn mục không xác nhận", prompt)
        self.assertNotIn("Results / Kết quả thực nghiệm gốc", prompt)


if __name__ == "__main__":
    unittest.main()
