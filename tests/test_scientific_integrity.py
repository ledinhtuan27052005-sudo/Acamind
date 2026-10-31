import math
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.services import scientific_appraiser as science
from app.services.authority_scorer import score_document_authority, score_topical_information_density, prioritize_candidates_by_authority_and_density


def reviewed_row(key, effect=0.5, variance=0.04, **changes):
    data = dict(hedges_g=effect, variance=variance, sample_n=100, reviewed=True,
                reviewer='reviewer-1', analysis_group='adult-depression-12weeks-CBT-vs-control-lower-better',
                independent_study_id=key, source={'document_id': key, 'page': 2, 'quote': 'Reported effect and variance'})
    data.update(changes)
    return {'document_id': key, 'filename': key + '.pdf', 'meta_analysis_input': data}


class ScientificIntegrityTests(unittest.TestCase):
    def test_pico_does_not_use_generated_answer_or_invent_missing_fields(self):
        result = science.extract_pico_framework('q', 'N = 120 patients received CBT with 90% improvement', [])
        self.assertFalse(result['has_pico'])
        self.assertTrue(all(not values for values in result['candidates'].values()))

    def test_pico_keeps_each_source_separate(self):
        result = science.extract_pico_framework('q', '', [
            {'document_id': 'a', 'page_number': 1, 'content': 'Participants included 100 adults.'},
            {'document_id': 'b', 'page_number': 3, 'content': 'The intervention was CBT.'}])
        self.assertEqual(result['candidates']['population'][0]['document_id'], 'a')
        self.assertEqual(result['candidates']['intervention'][0]['document_id'], 'b')
        self.assertEqual(result['status'], 'unverified')

    def test_study_cells_never_attribute_parent_text_to_chunk_page(self):
        result = science.extract_structured_study_cells('Study', 'a.pdf', [{
            'page_number': 2, 'content': 'Background information about general concepts without any experimental conclusion.',
            'parent_context': 'Results show that our treatment improves depression by 90 percent in all participants.'}])
        self.assertNotIn('90 percent', result['finding'])
        self.assertEqual(result['extraction_status'], 'unverified')

    def test_citation_export_never_invents_bibliography(self):
        doc = {'filename': 'unknown.pdf'}
        for export in (science.generate_bibtex_entry, science.generate_ris_entry, science.generate_apa7_citation):
            result = export(doc)
            self.assertNotIn('2023', result)
            self.assertNotIn('Acamind Research Team', result)
            self.assertNotIn('Journal of Clinical', result)
        self.assertIn('n.d.', science.generate_apa7_citation(doc))
        self.assertNotIn('AU  -', science.generate_ris_entry(doc))

    def test_keyword_mentions_never_certify_authority(self):
        for text in ('people who participated', 'capacity', 'WHO APA RCT', 'systematic review', 'PhD Nature journal'):
            score, tier, label = score_document_authority({'title': text}, text)
            self.assertEqual(score, 0)
            self.assertEqual(tier, 'unverified')
            self.assertNotIn('Cấp 1', label)

    def test_cebm_does_not_assign_grade_from_mentions(self):
        for text in ('meta-analysis', 'RCT', 'DSM-5', 'cohort', ''):
            result = science.evaluate_cebm_evidence_level([{'title': text}], [{'content': text}])
            self.assertEqual(result['level'], 'unverified')
            self.assertEqual(result['grade'], 'unverified')
            self.assertEqual(result['stars'], 0)

    def test_overlap_uses_tokens_not_substrings(self):
        self.assertEqual(score_topical_information_density('Capacity and wholesale discussion. ' * 5, 'apa who')[2], 0)

    def test_selection_preserves_missing_ids_and_document_limit(self):
        chunks = [{'document_id': str(i), 'content': 'Evidence', 'ranking_score': 0.8} for i in range(3)]
        self.assertEqual(len(prioritize_candidates_by_authority_and_density(chunks, 'compare studies', top_k=3)), 3)
        self.assertEqual(prioritize_candidates_by_authority_and_density(chunks, 'q', top_k=0), [])
        for chunk in chunks:
            chunk['document_id'] = 'one'
        self.assertEqual(len(prioritize_candidates_by_authority_and_density(chunks, 'q', max_per_doc=1)), 1)

    def test_no_synthetic_consensus_conflicts_or_research_gaps(self):
        rows = [{'document_id': 'a', 'finding': 'No difference'}, {'document_id': 'b', 'finding': 'Same result'}]
        result = science.analyze_cebm_contradiction_radar(rows)
        self.assertIsNone(result['cebm_weighted_consensus_pct'])
        self.assertIsNone(result['dominant_study'])
        self.assertEqual(result['contradictions'], [])
        self.assertEqual(result['consensus_points'], [])
        self.assertEqual(result['research_gaps']['novel_hypotheses'], [])
        for answer in ('hiệu quả cải thiện', 'tác dụng phụ', ''):
            self.assertIsNone(science.calculate_consensus_matrix('q', answer, [])['consensus_percentage'])

    def test_meta_identical_effects_matches_closed_form(self):
        result = science.compute_meta_analysis_forest_plot([reviewed_row('a'), reviewed_row('b')])
        self.assertEqual(result['status'], 'available')
        self.assertAlmostEqual(result['pooled_effect'], 0.5)
        self.assertAlmostEqual(result['pooled_se'], math.sqrt(0.02))
        self.assertEqual(result['tau_squared'], 0)
        self.assertEqual(result['i_squared_pct'], 0)
        self.assertAlmostEqual(result['p_value'], math.erfc((0.5 / math.sqrt(0.02)) / math.sqrt(2)))

    def test_zero_effect_has_p_one_and_signed_effect_is_preserved(self):
        for effect in (0.0, -0.5, 2.0):
            result = science.compute_meta_analysis_forest_plot([reviewed_row('a', effect), reviewed_row('b', effect)])
            self.assertAlmostEqual(result['pooled_effect'], effect)
            if effect == 0:
                self.assertEqual(result['p_value'], 1)

    def test_meta_does_not_cap_heterogeneity_at_96(self):
        result = science.compute_meta_analysis_forest_plot([reviewed_row('a', -10), reviewed_row('b', 10)])
        self.assertGreater(result['i_squared_pct'], 96)

    def test_meta_rejects_unreviewed_invalid_incomparable_or_dependent_rows(self):
        invalid = [reviewed_row('b', reviewed=False), reviewed_row('b', variance=0),
                   reviewed_row('b', variance=float('nan')), reviewed_row('b', effect=float('inf')),
                   reviewed_row('b', analysis_group='other-outcome'), reviewed_row('a'),
                   reviewed_row('b', source={}), reviewed_row('b', sample_n=True)]
        for row in invalid:
            with self.subTest(row=row):
                result = science.compute_meta_analysis_forest_plot([reviewed_row('a'), row])
                self.assertEqual(result['status'], 'insufficient_data')
                self.assertNotIn('pooled_effect', result)

    def test_citation_without_evidence_never_verifies_claim(self):
        result = science.verify_atomic_claims_entailment('q', 'The intervention significantly improved every outcome [fake.pdf - Page 9].', [])
        self.assertIsNone(result['faithfulness_score'])
        self.assertEqual(result['entailed_count'], 0)
        self.assertEqual(result['claims'][0]['evidence_snippet'], '')

    def test_similarity_and_parent_context_do_not_prove_support(self):
        with patch('app.services.embedder.embed_query_cached', return_value=[1.0, 0.0]):
            result = science.verify_atomic_claims_entailment('q', 'The treatment improved depression in participants [a.pdf - Page 2].', [{
                'document_id': 'a', 'doc_filename': 'a.pdf', 'page_number': 2,
                'content': 'The treatment did not improve depression in participants.',
                'parent_context': 'The treatment improved depression in participants.'}])
        self.assertEqual(result['entailed_count'], 0)
        self.assertIsNone(result['claims'][0]['entailment_score'])
        self.assertIn('did not', result['claims'][0]['evidence_snippet'])


if __name__ == '__main__':
    unittest.main()
