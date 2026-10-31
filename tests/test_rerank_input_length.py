import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services import reranker


class RerankInputLengthTests(unittest.TestCase):
    def setUp(self):
        reranker._rerank_cache.clear()
        reranker._PAIR_SCORE_CACHE.clear()
        env = patch.dict(os.environ, {"RERANK_MAX_LENGTH": "512"})
        env.start()
        self.addCleanup(env.stop)

    def test_original_passage_end_reaches_flag_backend(self):
        wrapper = reranker.FlagRerankerWrapper()
        model = MagicMock(spec=["compute_score"])
        model.compute_score.return_value = [.8]
        wrapper._model = model
        text = "Background information. " * 30 + "The intervention had no significant effect."
        for title in ("Study A", ""):
            wrapper.score("What was the outcome?", [{"content": text, "doc_title": title}])
            pairs = model.compute_score.call_args.args[0]
            self.assertTrue(pairs[0][1].endswith("The intervention had no significant effect."))
            self.assertIn(text, pairs[0][1])
            self.assertEqual(model.compute_score.call_args.kwargs["max_length"], 512)

    def test_sentence_transformers_backend_uses_same_limit(self):
        wrapper = reranker.FlagRerankerWrapper()
        model = MagicMock(spec=["predict", "max_length"])
        model.predict.return_value = [.6]
        wrapper._model = model
        for limit in (256, 512):
            with patch.dict(os.environ, {"RERANK_MAX_LENGTH": str(limit)}):
                self.assertEqual(wrapper.score_pairs([("query", "passage")]), [.6])
                self.assertEqual(model.max_length, limit)

    def test_length_is_bounded_and_bad_configuration_has_default(self):
        for raw, expected in (("bad", 512), ("0", 128), ("9999", 512), ("384", 384)):
            with patch.dict(os.environ, {"RERANK_MAX_LENGTH": raw}):
                self.assertEqual(reranker._rerank_max_length(), expected)

    def test_pair_cache_changes_with_length_and_late_text(self):
        model = MagicMock()
        model.score_pairs.return_value = [.5]
        chunk = {"id": "a", "content": "Background " * 70 + "Outcome one"}
        with patch.object(reranker, "get_reranker", return_value=model), \
             patch.object(reranker, "_env_use_llm_rerank", return_value=False):
            for limit in (256, 512, 512):
                with patch.dict(os.environ, {"RERANK_MAX_LENGTH": str(limit)}):
                    reranker.rerank_groups([("q", [chunk])], 1)
            self.assertEqual(model.score_pairs.call_count, 2)
            chunk["content"] += " Outcome changed"
            reranker.rerank_groups([("q", [chunk])], 1)
            self.assertEqual(model.score_pairs.call_count, 3)

    def test_result_cache_changes_with_length_and_title(self):
        model = MagicMock()
        model.score.return_value = [.5]
        chunk = {"id": "a", "content": "Passage", "doc_title": "Title A"}
        with patch.object(reranker, "get_reranker", return_value=model), \
             patch.object(reranker, "_env_use_llm_rerank", return_value=False):
            for limit in (256, 512, 512):
                with patch.dict(os.environ, {"RERANK_MAX_LENGTH": str(limit)}):
                    reranker.rerank("q", [chunk], force_score=True)
            self.assertEqual(model.score.call_count, 2)
            chunk["doc_title"] = "Title B"
            reranker.rerank("q", [chunk], force_score=True)
            self.assertEqual(model.score.call_count, 3)


if __name__ == "__main__":
    unittest.main()
