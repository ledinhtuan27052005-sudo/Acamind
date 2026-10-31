import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services import reranker


class FastCommitPolicyTests(unittest.TestCase):
    def setUp(self):
        reranker._rerank_cache.clear()
        reranker._PAIR_SCORE_CACHE.clear()

    def chunks(self):
        return [{"id": str(i), "content": f"Passage {i}", "rrf_score": .02} for i in range(2)]

    def run_case(self, flag, force=False):
        model = MagicMock()
        # The heuristic winner is actually less relevant according to the model.
        model.score.return_value = [.1, .9]
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("RERANK_EXPERIMENTAL_FAST_COMMIT", None)
            if flag is not None:
                os.environ["RERANK_EXPERIMENTAL_FAST_COMMIT"] = flag
            with patch.object(reranker, "get_reranker", return_value=model), \
                 patch.object(reranker, "_env_use_llm_rerank", return_value=False), \
                 patch.object(reranker, "_compute_fast_cascade_prior", side_effect=[.95, .3]):
                result = reranker.rerank("query", self.chunks(), force_score=force)
        return model, result

    def test_default_scores_despite_dominant_heuristic(self):
        model, result = self.run_case(None)
        model.score.assert_called_once()
        self.assertEqual(result[0]["id"], "1")
        self.assertTrue(all(not c["cascade_fast_commit"] for c in result))

    def test_disabled_and_invalid_flags_do_not_enable_skip(self):
        for flag in ("0", "true", "yes", "invalid", ""):
            with self.subTest(flag=flag):
                reranker._rerank_cache.clear()
                model, result = self.run_case(flag)
                model.score.assert_called_once()
                self.assertEqual(result[0]["score_source"], "cross_encoder")

    def test_explicit_experiment_remains_unscored(self):
        model, result = self.run_case("1")
        model.score.assert_not_called()
        self.assertEqual(result[0]["id"], "0")
        self.assertTrue(result[0]["cascade_fast_commit"])
        self.assertIsNone(result[0]["cross_encoder_score"])
        self.assertFalse(result[0]["rerank_score_available"])

    def test_force_score_overrides_experiment(self):
        model, result = self.run_case("1", force=True)
        model.score.assert_called_once()
        self.assertEqual(result[0]["id"], "1")

    def test_disabling_experiment_cannot_reuse_heuristic_result(self):
        self.run_case("1")
        model, result = self.run_case("0")
        model.score.assert_called_once()
        self.assertEqual(result[0]["score_source"], "cross_encoder")


if __name__ == "__main__":
    unittest.main()
