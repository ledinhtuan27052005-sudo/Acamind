import unittest
from app.services.ranking_explanation import explain_ranking


class RankingExplanationTests(unittest.TestCase):
    def test_zero_is_real_score_not_missing(self):
        result = explain_ranking({'score_source': 'cross_encoder', 'rerank_score_available': True,
                                  'cross_encoder_score': 0, 'ranking_score': .08}, 2)
        self.assertEqual(result['model_score'], 0)
        self.assertEqual(result['ranking_score'], .08)
        self.assertEqual(result['retrieval_position'], 2)

    def test_fallback_never_presents_stale_model_score(self):
        for source in ('heuristic', 'llm_order', 'unscored', 'unavailable', 'unknown'):
            result = explain_ranking({'score_source': source, 'rerank_score_available': True,
                                      'cross_encoder_score': .99}, 1)
            self.assertIsNone(result['model_score'])

    def test_nonfinite_invalid_and_unavailable_scores(self):
        for value in (float('nan'), float('inf'), True, '0.8', -1, 1.5):
            result = explain_ranking({'score_source': 'cross_encoder', 'rerank_score_available': True,
                                      'cross_encoder_score': value}, 1)
            self.assertIsNone(result['model_score'])
        result = explain_ranking({'score_source': 'cross_encoder', 'cross_encoder_score': .8}, 1)
        self.assertIsNone(result['model_score'])

    def test_facets_remain_distinct_from_base_score(self):
        result = explain_ranking({'facet_scores': {'sample': .7, 'method': None, 'fake': 1},
                                  'facet_selection': ['sample'], 'rrf_score': .03}, 1)
        self.assertIsNone(result['model_score'])
        self.assertEqual(result['rrf_score'], .03)
        self.assertEqual(len(result['facets']), 2)
        self.assertTrue(result['facets'][0]['selected'])
        self.assertEqual(result['facets'][0]['score'], .7)
        self.assertIsNone(result['facets'][1]['score'])

    def test_absent_scores_not_invented(self):
        result = explain_ranking({}, 1)
        for key in ('model_score', 'ranking_score', 'heuristic_score', 'rrf_score', 'composite_score'):
            self.assertIsNone(result[key])
        self.assertEqual(result['facets'], [])


if __name__ == '__main__':
    unittest.main()
