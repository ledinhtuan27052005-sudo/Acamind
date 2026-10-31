import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services import reranker


class RerankCandidateBudgetTests(unittest.TestCase):
    def setUp(self):
        reranker._rerank_cache.clear()
        reranker._PAIR_SCORE_CACHE.clear()
        env = patch.dict(os.environ, {"RERANK_CANDIDATES": "30", "RERANK_GROUP_CANDIDATES": "30"})
        env.start()
        self.addCleanup(env.stop)
        mode = patch.object(reranker, "_env_use_llm_rerank", return_value=False)
        mode.start()
        self.addCleanup(mode.stop)

    def chunks(self, n, prefix="a"):
        return [{"id": f"{prefix}-{i}", "content": f"Evidence {prefix} {i}", "rrf_score": .02,
                 "sub_query_target": prefix} for i in range(n)]

    def test_single_late_candidate_can_win_with_small_output(self):
        model = MagicMock()
        model.score.side_effect = lambda q, cs: [.99 if c["id"] == "a-24" else .1 for c in cs]
        with patch.object(reranker, "get_reranker", return_value=model), \
             patch.object(reranker, "_compute_fast_cascade_prior", return_value=.4):
            result = reranker.rerank("question", self.chunks(30), top_n=2, force_score=True)
        self.assertEqual(len(model.score.call_args.args[1]), 30)
        self.assertEqual(result[0]["id"], "a-24")
        self.assertEqual(len(result), 2)

    def test_each_group_scores_late_candidates_in_one_batch(self):
        model = MagicMock()
        model.score_pairs.return_value = [.1] * 24 + [.99] + [.1] * 4 + [.98]
        with patch.object(reranker, "get_reranker", return_value=model), \
             patch.object(reranker, "_compute_fast_cascade_prior", return_value=.4):
            result = reranker.rerank_groups([("A", self.chunks(25)), ("B", self.chunks(5, "b"))], 2)
        self.assertEqual(model.score_pairs.call_count, 1)
        self.assertEqual(len(model.score_pairs.call_args.args[0]), 30)
        self.assertEqual(result[0][0]["id"], "a-24")
        self.assertEqual(result[1][0]["id"], "b-4")
        self.assertTrue(all(c["sub_query_target"] == "a" for c in result[0]))

    def test_presorting_does_not_discard_positions_after_ten(self):
        model = MagicMock()
        model.score_pairs.return_value = [.9, .1]
        with patch.dict(os.environ, {"RERANK_GROUP_CANDIDATES": "2"}), \
             patch.object(reranker, "get_reranker", return_value=model), \
             patch.object(reranker, "_compute_fast_cascade_prior", side_effect=lambda q, c: .99 if c["id"] == "a-19" else .1):
            result = reranker.rerank_groups([("A", self.chunks(20))], 1)
        self.assertEqual(result[0][0]["id"], "a-19")

    def test_budget_change_invalidates_single_query_result_cache(self):
        model = MagicMock()
        model.score.side_effect = lambda q, cs: [.5] * len(cs)
        with patch.object(reranker, "get_reranker", return_value=model):
            for budget in (8, 30):
                with patch.dict(os.environ, {"RERANK_CANDIDATES": str(budget)}):
                    reranker.rerank("question", self.chunks(30), top_n=2, force_score=True)
        self.assertEqual([len(c.args[1]) for c in model.score.call_args_list], [8, 30])

    def test_failure_preserves_output_candidates_beyond_scoring_budget(self):
        model = MagicMock()
        model.score_pairs.side_effect = RuntimeError("unavailable")
        with patch.dict(os.environ, {"RERANK_GROUP_CANDIDATES": "2"}), \
             patch.object(reranker, "get_reranker", return_value=model):
            result = reranker.rerank_groups([("A", self.chunks(8))], 6)[0]
        self.assertEqual(len(result), 6)
        self.assertTrue(all(not c["rerank_score_available"] for c in result))

    def test_budget_configuration_is_bounded(self):
        for raw, expected in (("bad", 30), ("0", 1), ("-10", 1), ("999999", 128)):
            with patch.dict(os.environ, {"RERANK_CANDIDATES": raw, "RERANK_GROUP_CANDIDATES": raw}):
                self.assertEqual(reranker._candidate_budget(), expected)
                self.assertEqual(reranker._candidate_budget(True), expected)

    def test_empty_and_zero_output(self):
        self.assertEqual(reranker.rerank_groups([], 3), [])
        self.assertEqual(reranker.rerank_groups([("A", [])], 3), [[]])
        with patch.object(reranker, "get_reranker") as model:
            self.assertEqual(reranker.rerank("q", self.chunks(5), top_n=0), [])
            self.assertEqual(reranker.rerank_groups([("A", self.chunks(5))], 0), [[]])
            model.assert_not_called()


if __name__ == "__main__":
    unittest.main()
