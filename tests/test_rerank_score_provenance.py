import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services import reranker
from app.services.retriever import adaptive_context_budget
from app.services.comparison_coverage import assess_target_coverage


class RerankScoreProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.budgets = patch.dict("os.environ", {"RERANK_CANDIDATES": "8", "RERANK_GROUP_CANDIDATES": "3"})
        self.budgets.start()
        self.addCleanup(self.budgets.stop)
        reranker._rerank_cache.clear()
        reranker._PAIR_SCORE_CACHE.clear()

    def chunks(self, count):
        return [{"id": str(i), "content": f"Evidence passage {i}", "rrf_score": .02,
                 "document_id": f"doc-{i}", "sub_query_target": "A"} for i in range(count)]

    def assert_unscored(self, chunk):
        self.assertFalse(chunk["rerank_score_available"])
        self.assertIsNone(chunk["rerank_score"])
        self.assertIsNone(chunk["cross_encoder_score"])

    def test_fast_commit_is_not_cross_encoder_evidence(self):
        with patch.dict("os.environ", {"RERANK_EXPERIMENTAL_FAST_COMMIT": "1"}), \
             patch.object(reranker, "_compute_fast_cascade_prior", side_effect=[.95, .3]), \
             patch.object(reranker, "get_reranker") as model:
            ranked = reranker.rerank("query", self.chunks(2))
        model.assert_not_called()
        for chunk in ranked:
            self.assert_unscored(chunk)
            self.assertEqual(chunk["score_source"], "heuristic")
            self.assertTrue(chunk["cascade_fast_commit"])
        self.assertEqual(adaptive_context_budget("query", ranked, 12), 12)
        coverage = assess_target_coverage(["A"], ranked)
        self.assertIn('unscored', str(coverage))

    def test_model_score_is_raw_and_tail_remains_unscored(self):
        model = MagicMock()
        model.score.return_value = [.5] * 8
        with patch.object(reranker, "get_reranker", return_value=model), \
             patch.object(reranker, "_env_use_llm_rerank", return_value=False), \
             patch.object(reranker, "_compute_fast_cascade_prior", return_value=.4):
            ranked = reranker.rerank("query", self.chunks(10), top_n=10, force_score=True)
        for chunk in ranked[:8]:
            self.assertEqual(chunk["cross_encoder_score"], .5)
            self.assertEqual(chunk["rerank_score"], .5)
            self.assertEqual(chunk["ranking_score"], .5 * .92 + .04)
            self.assertEqual(chunk["score_source"], "cross_encoder")
        for chunk in ranked[8:]:
            self.assert_unscored(chunk)
            self.assertEqual(chunk["score_source"], "heuristic")

    def test_single_candidate_clears_old_scores_without_mutating_input(self):
        chunks = self.chunks(1)
        chunks[0].update(rerank_score=.99, cross_encoder_score=.99, rerank_score_available=True)
        model = MagicMock()
        model.score.return_value = [.2]
        with patch.object(reranker, "get_reranker", return_value=model), \
             patch.object(reranker, "_env_use_llm_rerank", return_value=False):
            ranked = reranker.rerank("new query", chunks)
        self.assertEqual(ranked[0]["cross_encoder_score"], .2)
        self.assertTrue(ranked[0]["rerank_score_available"])
        self.assertEqual(chunks[0]["rerank_score"], .99)

    def test_group_tail_and_cache_preserve_score_sources(self):
        model = MagicMock()
        model.score_pairs.return_value = [.8, .4, .1]
        with patch.object(reranker, "get_reranker", return_value=model), \
             patch.object(reranker, "_env_use_llm_rerank", return_value=False), \
             patch.object(reranker, "_compute_fast_cascade_prior", return_value=.4):
            first = reranker.rerank_groups([("query", self.chunks(6))], 6)[0]
            second = reranker.rerank_groups([("query", self.chunks(6))], 6)[0]
        self.assertEqual(model.score_pairs.call_count, 1)
        self.assertEqual(first, second)
        self.assertEqual(sum(c["rerank_score_available"] for c in first), 3)
        for chunk in first:
            if chunk["score_source"] == "heuristic":
                self.assert_unscored(chunk)

    def test_group_failure_clears_stale_model_score(self):
        chunks = self.chunks(2)
        for chunk in chunks:
            chunk.update(rerank_score=.99, rerank_score_available=True)
        model = MagicMock()
        model.score_pairs.side_effect = RuntimeError("unavailable")
        with patch.object(reranker, "get_reranker", return_value=model), \
             patch.object(reranker, "_env_use_llm_rerank", return_value=False):
            ranked = reranker.rerank_groups([("query", chunks)], 2)[0]
        for chunk in ranked:
            self.assert_unscored(chunk)
            self.assertEqual(chunk["score_source"], "unavailable")

    def test_llm_order_never_inherits_model_scores(self):
        chunks = self.chunks(2)
        chunks[0].update(rerank_score=.99, rerank_score_available=True)
        client = MagicMock()
        client.complete.return_value = "[0, 1]"
        with patch("app.services.llm_client.get_default_client", return_value=client):
            ranked = reranker._llm_rerank("query", chunks, 2)
            for chunk in ranked:
                self.assert_unscored(chunk)
                self.assertEqual(chunk["score_source"], "llm_order")
            client.complete.side_effect = RuntimeError("unavailable")
            for chunk in reranker._llm_rerank("query", chunks, 2):
                self.assert_unscored(chunk)


if __name__ == "__main__":
    unittest.main()
