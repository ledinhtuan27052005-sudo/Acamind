import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.services import reranker


class InvalidRerankOutputTests(unittest.TestCase):
    def setUp(self):
        reranker._rerank_cache.clear()
        reranker._PAIR_SCORE_CACHE.clear()
        self.chunks = [{'id': str(i), 'content': f'evidence {i}'} for i in range(3)]

    def test_single_invalid_scores_fall_back_without_caching(self):
        for scores in ([0.5], [0.5, float('nan'), 0.1], [1.2, 0.5, 0.1]):
            model = MagicMock()
            model.score.return_value = scores
            with patch.object(reranker, 'get_reranker', return_value=model), \
                 patch.object(reranker, '_env_use_llm_rerank', return_value=False), \
                 patch.object(reranker, '_llm_rerank', return_value=[]) as fallback:
                self.assertEqual(reranker.rerank('q', self.chunks), [])
                fallback.assert_called_once()
            self.assertEqual(reranker._rerank_cache, {})

    def test_group_invalid_scores_do_not_drop_candidates(self):
        model = MagicMock()
        model.score_pairs.return_value = [0.2, float('inf'), 0.1]
        with patch.object(reranker, 'get_reranker', return_value=model), \
             patch.object(reranker, '_env_use_llm_rerank', return_value=False):
            result = reranker.rerank_groups([('q', self.chunks)], 3)[0]
        self.assertEqual(len(result), 3)
        self.assertTrue(all(not c['rerank_score_available'] for c in result))
        self.assertFalse(reranker._PAIR_SCORE_CACHE)

    def test_llm_duplicate_indexes_are_unique_and_tail_preserved(self):
        client = MagicMock()
        client.complete.return_value = '[1, 1, 99]'
        with patch('app.services.llm_client.get_default_client', return_value=client):
            result = reranker._llm_rerank('q', self.chunks, 3)
        self.assertEqual([c['id'] for c in result], ['1', '0', '2'])
        self.assertTrue(all(not c['rerank_score_available'] for c in result))


if __name__ == '__main__':
    unittest.main()
