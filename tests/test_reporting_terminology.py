import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))


class ReportingTerminologyTests(unittest.TestCase):
    def test_deep_mode_uses_generic_evidence_table_in_both_languages(self):
        from app.api.v1.chat import _normalize_mode_instruction
        for lang in ("vi", "en"):
            with self.subTest(lang=lang):
                text = _normalize_mode_instruction("[System: MODE=DEEP] Compare the studies", lang)
                self.assertIn("Evidence Synthesis Matrix", text)
                self.assertNotIn("PRISMA Evidence", text)
                self.assertIn("PICO", text)

    def test_generated_system_prompt_separates_reporting_from_quality(self):
        from app.services.generator import build_psychology_prompt
        chunk = {"document_id": "a", "doc_filename": "a.pdf", "page_number": 1,
                 "content": "This study investigates cognition and behavior in adults."}
        for lang in ("vi", "en"):
            with self.subTest(lang=lang):
                messages = build_psychology_prompt("Compare the studies", [chunk], lang=lang)
                system = messages[0]["content"]
                self.assertNotIn("PRISMA Evidence", system)
                if lang == "en":
                    self.assertIn("not a methodological quality", system)
                    self.assertIn("Do not claim PRISMA compliance", system)
                    self.assertIn("missing excerpts do not prove missing reporting", system)
                else:
                    self.assertIn("không phải điểm chất lượng phương pháp", system)
                    self.assertIn("Không tuyên bố đạt PRISMA", system)
                    self.assertIn("không chứng minh báo cáo thiếu", system)


if __name__ == "__main__":
    unittest.main()
