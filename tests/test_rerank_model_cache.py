import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services import reranker


class RerankModelCacheTests(unittest.TestCase):
    def setUp(self):
        reranker._rerank_cache.clear()
        reranker._PAIR_SCORE_CACHE.clear()
        mode = patch.object(reranker, "_env_use_llm_rerank", return_value=False)
        mode.start()
        self.addCleanup(mode.stop)
        self.chunk = {"id": "a", "content": "Same passage"}

    def model(self, name, value):
        return SimpleNamespace(model_name=name,
            _model=SimpleNamespace(config=SimpleNamespace(_commit_hash="revision-a")),
            score=MagicMock(return_value=[value]), score_pairs=MagicMock(return_value=[value]))

    def score(self, model, grouped):
        with patch.object(reranker, "get_reranker", return_value=model):
            if grouped:
                return reranker.rerank_groups([("query", [self.chunk])], 1)[0][0]["cross_encoder_score"]
            return reranker.rerank("query", [self.chunk], force_score=True)[0]["cross_encoder_score"]

    def test_model_switch_does_not_reuse_either_cache(self):
        for grouped in (False, True):
            with self.subTest(grouped=grouped):
                a, b = self.model("model-a", .2), self.model("model-b", .9)
                self.assertEqual(self.score(a, grouped), .2)
                self.assertEqual(self.score(b, grouped), .9)
                self.assertEqual(self.score(b, grouped), .9)
                self.assertEqual((b.score_pairs if grouped else b.score).call_count, 1)

    def test_same_name_new_instance_requires_rescoring(self):
        for grouped in (False, True):
            a, b = self.model("same-name", .2), self.model("same-name", .8)
            self.assertEqual(self.score(a, grouped), .2)
            self.assertEqual(self.score(b, grouped), .8)

    def test_revision_and_backend_replacement_invalidate_scores(self):
        for grouped in (False, True):
            model = self.model("same-name", .2)
            self.score(model, grouped)
            method = model.score_pairs if grouped else model.score
            model._model.config._commit_hash = "revision-b"
            method.return_value = [.7]
            self.assertEqual(self.score(model, grouped), .7)
            model._model = SimpleNamespace(config=SimpleNamespace(_commit_hash="revision-b"))
            method.return_value = [.8]
            self.assertEqual(self.score(model, grouped), .8)
            self.assertEqual(method.call_count, 3)

    def test_scoring_schema_change_invalidates_both_caches(self):
        for grouped in (False, True):
            model = self.model("a", .2)
            self.score(model, grouped)
            method = model.score_pairs if grouped else model.score
            method.return_value = [.6]
            with patch.object(reranker, "_SCORING_SCHEMA", "new-scoring-policy"):
                self.assertEqual(self.score(model, grouped), .6)

    def test_transient_model_failure_does_not_cache_fallback(self):
        model = self.model("a", .8)
        model.score.side_effect = [RuntimeError("temporary failure"), [.8]]
        fallback = [reranker._unscored(self.chunk, "llm_order")]
        with patch.object(reranker, "get_reranker", return_value=model), \
             patch.object(reranker, "_llm_rerank", return_value=fallback):
            first = reranker.rerank("query", [self.chunk], force_score=True)
            second = reranker.rerank("query", [self.chunk], force_score=True)
        self.assertFalse(first[0]["rerank_score_available"])
        self.assertEqual(second[0]["cross_encoder_score"], .8)
        self.assertEqual(model.score.call_count, 2)

    def test_empty_groups_do_not_load_a_model_for_cache_identity(self):
        with patch.object(reranker, "get_reranker") as get_model:
            self.assertEqual(reranker.rerank_groups([], 3), [])
            self.assertEqual(reranker.rerank_groups([("q", [])], 3), [[]])
            get_model.assert_not_called()


if __name__ == "__main__":
    unittest.main()
