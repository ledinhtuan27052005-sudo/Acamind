import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.services.facet_reranker import rerank_by_facets, requested_facets
from app.services import retriever


class FacetRerankerTests(unittest.TestCase):
    def chunks(self, doc='a'):
        return [{'id': str(i), 'document_id': doc, 'page_number': i + 1,
                 'content': f'{doc} passage {i}'} for i in range(4)]

    def scorer(self, groups, top_n):
        out = []
        for q, chunks in groups:
            leader = '2' if 'sample size' in q else '3' if 'limitations and' in q else '0'
            out.append(sorted([{**c, 'rerank_score': .9 if c['id'] == leader else .1,
                                'ranking_score': .9 if c['id'] == leader else .1,
                                'cross_encoder_score': .9 if c['id'] == leader else .1,
                                'rerank_score_available': True} for c in chunks],
                              key=lambda c: c['rerank_score'], reverse=True)[:top_n])
        return out

    def test_detects_explicit_vietnamese_and_english_criteria(self):
        self.assertEqual(requested_facets('cỡ mẫu và hạn chế', False), ['sample', 'limitation'])
        self.assertEqual(requested_facets('methods and findings', False), ['method', 'finding'])
        self.assertEqual(requested_facets('What is CBT?', False), ['answer'])

    def test_specific_winners_survive_without_overwriting_global_scores(self):
        chunks = self.chunks()
        original = deepcopy(chunks)
        with patch('app.services.reranker.rerank_groups', side_effect=self.scorer) as score:
            result = rerank_by_facets([('study A', chunks)], ['sample', 'limitation'], 2)[0]
        self.assertEqual([c['id'] for c in result], ['2', '3'])
        self.assertEqual(result[0]['rerank_score'], .1)
        self.assertEqual(result[0]['facet_scores']['sample'], .9)
        self.assertEqual(result[0]['facet_selection'], ['sample'])
        self.assertEqual(chunks, original)
        score.assert_called_once()
        self.assertEqual(len(score.call_args.args[0]), 3)

    def test_studies_remain_separate_even_with_shared_chunk_ids(self):
        with patch('app.services.reranker.rerank_groups', side_effect=self.scorer):
            groups = rerank_by_facets([('A', self.chunks('a')), ('B', self.chunks('b'))], ['sample', 'limitation'], 2)
        self.assertEqual({c['document_id'] for c in groups[0]}, {'a'})
        self.assertEqual({c['document_id'] for c in groups[1]}, {'b'})

    def test_failed_scoring_preserves_order_without_inventing_facet_scores(self):
        def unavailable(groups, top_n):
            return [[{**c, 'rerank_score_available': False, 'rerank_score': None} for c in chunks][:top_n]
                    for _, chunks in groups]
        with patch('app.services.reranker.rerank_groups', side_effect=unavailable):
            result = rerank_by_facets([('A', self.chunks())], ['sample', 'limitation'], 3)[0]
        self.assertEqual([c['id'] for c in result], ['0', '1', '2'])
        self.assertTrue(all(c['facet_rerank_status'] == 'unavailable' for c in result))
        self.assertTrue(all(v is None for c in result for v in c['facet_scores'].values()))

    def test_duplicate_winners_and_small_pools_never_duplicate_chunks(self):
        with patch('app.services.reranker.rerank_groups', side_effect=self.scorer):
            result = rerank_by_facets([('A', self.chunks()[:1])], ['sample', 'limitation'], 5)[0]
        self.assertEqual(len(result), 1)

    def test_empty_group_and_zero_budget(self):
        with patch('app.services.reranker.rerank_groups', side_effect=lambda groups, top_n: [[] for _ in groups]):
            self.assertEqual(rerank_by_facets([('A', [])], ['sample'], 3), [[]])
            self.assertEqual(rerank_by_facets([('A', self.chunks())], ['sample'], 0), [[]])

    def test_single_query_routes_multi_criteria_before_shortcuts(self):
        with patch.object(retriever, '_retrieve_single_pass', return_value=self.chunks()) as search, \
             patch.object(retriever, '_enrich_parent_context', side_effect=lambda chunks, db: chunks), \
             patch('app.services.reranker.rerank_groups', side_effect=self.scorer):
            result = retriever.retrieve('Cỡ mẫu và hạn chế của nghiên cứu', ['scope'], MagicMock(), top_k=2)
        self.assertTrue(search.call_args.kwargs['defer_rerank'])
        self.assertEqual(search.call_args.args[1], ['scope'])
        self.assertEqual([c['id'] for c in result], ['2', '3'])
        self.assertTrue(result[0]['_telemetry']['facet_rerank'])

    def test_single_criterion_keeps_existing_path(self):
        with patch.object(retriever, '_retrieve_single_pass', return_value=[]) as search:
            retriever.retrieve('Cỡ mẫu là bao nhiêu?', None, MagicMock())
        self.assertNotIn('defer_rerank', search.call_args.kwargs)


if __name__ == '__main__':
    unittest.main()
