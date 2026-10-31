import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.services.claim_origin import classify_claim_origins
from app.services.evidence_policy import evidence_packet
from app.services.generator import build_psychology_prompt


class ClaimOriginTests(unittest.TestCase):
    def test_current_study_requires_explicit_subject(self):
        for text in ('We found no improvement in symptoms.', 'Chúng tôi ghi nhận sự khác biệt.',
                     'In this study, participants received no intervention.'):
            result = classify_claim_origins(text)[0]
            self.assertEqual(result['origin'], 'current_study_candidate')
            self.assertEqual(result['status'], 'unverified')

    def test_external_attribution(self):
        for text in ('Smith et al. (2020) reported improved outcomes.',
                     'Previous studies found improvement.', 'Các nghiên cứu trước cho thấy hiệu quả.'):
            self.assertEqual(classify_claim_origins(text)[0]['origin'], 'cited_study_candidate')

    def test_heading_numbers_and_citation_alone_cannot_certify_ownership(self):
        for text in ('Results', 'N = 100; p < 0.05.', 'Improvement was observed [12].',
                     'The sample was large (Smith, 2020).'):
            self.assertEqual(classify_claim_origins(text)[0]['origin'], 'unclear')

    def test_mixed_quoted_and_qualified_subjects_remain_unclear(self):
        for text in ('Our results agree with previous studies.', 'Our results replicate Smith (2020).',
                     '“We found an effect,” the article stated.', 'These are not our results.',
                     'Are our results significant?'):
            self.assertEqual(classify_claim_origins(text)[0]['origin'], 'unclear')

    def test_sentence_spans_preserve_exact_unicode_offsets(self):
        text = '  We found no effect.\nCác nghiên cứu trước cho thấy hiệu quả.  '
        spans = classify_claim_origins(text)
        self.assertEqual(len(spans), 2)
        self.assertEqual([s['origin'] for s in spans], ['current_study_candidate', 'cited_study_candidate'])
        for s in spans:
            self.assertEqual(s['quote'], text[s['start']:s['end']])

    def test_empty_text(self):
        self.assertEqual(classify_claim_origins(''), [])

    def test_evidence_uses_original_chunk_not_parent(self):
        packet = evidence_packet(['A'], [{'content': 'Previous studies found an effect.',
            'parent_context': 'We found an effect.', 'document_id': 'a', 'page_number': 2}])
        self.assertEqual(packet[0]['origin_candidates'][0]['origin'], 'cited_study_candidate')
        self.assertEqual(packet[0]['page'], 2)

    def test_generator_receives_caution_and_per_sentence_hint(self):
        prompt = build_psychology_prompt('What were the findings?', [{
            'content': 'Previous studies found an effect.', 'doc_filename': 'a.pdf', 'page_number': 2}])
        text = '\n'.join(m['content'] for m in prompt)
        self.assertIn('Có dấu hiệu thuật lại nghiên cứu khác', text)
        self.assertIn('Nguồn gốc nhận định chưa xác minh', text)


if __name__ == '__main__':
    unittest.main()
