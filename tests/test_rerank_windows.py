import os
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.services import reranker


class Tokenizer:
    def __call__(self, text, pair=None, add_special_tokens=False, **kwargs):
        spans = [(m.start(), m.end()) for m in re.finditer(r'\S+', text)]
        n = len(spans) + (len(pair.split()) if pair is not None else 0)
        return {'input_ids': list(range(n + (3 if add_special_tokens else 0))), 'offset_mapping': spans}

    def num_special_tokens_to_add(self, pair=True):
        return 3


class Model:
    tokenizer = Tokenizer()

    def __init__(self):
        self.calls = []

    def compute_score(self, pairs, **kwargs):
        self.calls.append(pairs[:])
        return [.95 if 'FINAL_RESULT' in text else .1 for _, text in pairs]


class RerankWindowTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {'RERANK_MAX_LENGTH': '128', 'RERANK_WINDOW_OVERLAP': '32', 'RERANK_MAX_WINDOWS': '32'})
        env.start()
        self.addCleanup(env.stop)

    def test_exact_slices_cover_start_middle_end_with_overlap(self):
        text = '  ' + ' '.join(f'từ{i}' for i in range(500)) + ' FINAL_RESULT  '
        windows = reranker._passage_windows('query', text, Tokenizer())
        self.assertEqual(windows[0][0], 0)
        self.assertEqual(windows[-1][1], len(text))
        for lo, hi, snippet in windows:
            self.assertEqual(snippet, text[lo:hi])
            self.assertLessEqual(len(Tokenizer()('query', snippet, add_special_tokens=True)['input_ids']), 128)
        for first, second in zip(windows, windows[1:]):
            self.assertLess(second[0], first[1])
            self.assertGreater(second[1], first[1])

    def test_tail_changes_score_and_batch_preserves_pair_order(self):
        model = Model()
        wrapper = reranker.FlagRerankerWrapper()
        wrapper._model = model
        long_text = 'background ' * 400 + 'FINAL_RESULT'
        self.assertEqual(wrapper.score_pairs([('q', 'short'), ('q', long_text), ('q', 'other')]), [.1, .95, .1])
        self.assertEqual(len(model.calls), 1)
        self.assertTrue(any('FINAL_RESULT' in text for call in model.calls for _, text in call))

    def test_batch_size_stays_bounded(self):
        model = Model()
        wrapper = reranker.FlagRerankerWrapper()
        wrapper._model = model
        self.assertEqual(len(wrapper.score_pairs([('q', 'word ' * 900)] * 4)), 4)
        self.assertTrue(all(len(call) <= 16 for call in model.calls))

    def test_short_and_empty_passages_stay_intact(self):
        for text in ('', 'short passage', ' tiếng Việt '):
            self.assertEqual(reranker._passage_windows('q', text, Tokenizer()), [(0, len(text), text)])

    def test_window_limit_fails_instead_of_dropping_tail(self):
        with patch.dict(os.environ, {'RERANK_MAX_WINDOWS': '1'}):
            with self.assertRaisesRegex(ValueError, 'window budget'):
                reranker._passage_windows('q', 'word ' * 300, Tokenizer())

    def test_long_query_fails_instead_of_silent_truncation(self):
        with self.assertRaisesRegex(ValueError, 'query'):
            reranker._passage_windows('query ' * 120, 'word ' * 300, Tokenizer())

    def test_chunk_content_and_page_are_unchanged(self):
        wrapper = reranker.FlagRerankerWrapper()
        wrapper._model = Model()
        chunk = {'content': 'word ' * 300 + 'FINAL_RESULT', 'page_number': 9, 'document_id': 'a'}
        original = dict(chunk)
        self.assertEqual(wrapper.score('q', [chunk]), [.95])
        self.assertEqual(chunk, original)

    def test_cache_namespace_changes_with_window_settings(self):
        wrapper = reranker.FlagRerankerWrapper()
        wrapper._model = Model()
        first = reranker._score_cache_namespace(wrapper)
        with patch.dict(os.environ, {'RERANK_WINDOW_OVERLAP': '0'}):
            self.assertNotEqual(first, reranker._score_cache_namespace(wrapper))


if __name__ == '__main__':
    unittest.main()
