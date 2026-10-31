import sys
import unittest
from pathlib import Path
from uuid import UUID
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services import retriever


class RetrievalScopeTests(unittest.TestCase):
    def ids(self, count):
        return [str(UUID(int=i + 1)) for i in range(count)]

    def run_pass(self, ids, resolved=None):
        executor = MagicMock()
        executor.submit.return_value.result.return_value = []
        bundle = {"orig_query": "psychology", "translated_query": None, "fts_expanded_terms": []}
        with patch.object(retriever, "_RETRIEVE_EXECUTOR", executor), \
             patch.object(retriever, "_resolve_explicit_title_scope", return_value=resolved), \
             patch.object(retriever, "_set_hnsw_ef_search"), \
             patch.object(retriever, "embed_queries_batch_cached"), \
             patch.object(retriever, "get_cross_lingual_query_bundle", return_value=bundle):
            result = retriever._retrieve_single_pass("psychology", ids, MagicMock(), defer_rerank=True)
        self.assertEqual(result, [])
        return executor

    def test_scope_kept_for_both_workers_at_all_sizes(self):
        for size in (1, 199, 200, 201, 1528):
            with self.subTest(size=size):
                ids = self.ids(size)
                executor = self.run_pass(ids)
                vector_args, lexical_args = [call.args for call in executor.submit.call_args_list]
                expected = ", ".join(f"'{value}'" for value in ids)
                self.assertEqual(vector_args[3], expected)
                self.assertEqual(lexical_args[4], ids)
                self.assertEqual(lexical_args[5], expected)

    def test_invalid_explicit_selection_fails_closed(self):
        executor = self.run_pass(["invalid", "'); DROP TABLE documents; --"])
        executor.submit.assert_not_called()

    def test_mixed_ids_keep_only_valid_scope(self):
        ids = self.ids(1)
        executor = self.run_pass(ids + ["invalid"])
        self.assertEqual(executor.submit.call_args_list[0].args[3], f"'{ids[0]}'")

    def test_unscoped_search_and_title_resolution_remain_supported(self):
        executor = self.run_pass(None)
        self.assertIsNone(executor.submit.call_args_list[0].args[3])
        ids = self.ids(200)
        executor = self.run_pass(None, resolved=ids)
        self.assertEqual(executor.submit.call_args_list[0].args[3], ", ".join(f"'{value}'" for value in ids))

    def test_vector_queries_keep_large_scope_in_both_languages(self):
        scope = ", ".join(f"'{value}'" for value in self.ids(201))
        session = MagicMock()
        session.execute.return_value.fetchall.return_value = []
        with patch.object(retriever, "SessionLocal") as factory, \
             patch.object(retriever, "embed_query_cached", return_value=[0.1, 0.2]):
            factory.return_value.__enter__.return_value = session
            retriever._vector_search_task("tâm lý", "psychology", scope)
        selects = [str(call.args[0]) for call in session.execute.call_args_list if "SELECT" in str(call.args[0])]
        self.assertEqual(len(selects), 2)
        for sql in selects:
            self.assertIn(f"WHERE document_id IN ({scope})", sql)

    def test_fts_relaxation_queries_keep_large_scope(self):
        scope = ", ".join(f"'{value}'" for value in self.ids(201))
        session = MagicMock()
        session.execute.return_value.fetchall.return_value = []
        retriever._bm25_via_fts(["tâm", "lý"], "clinical psychology therapy", [], scope, session)
        selects = [str(call.args[0]) for call in session.execute.call_args_list if "FROM page_texts" in str(call.args[0])]
        self.assertGreaterEqual(len(selects), 2)
        for sql in selects:
            self.assertIn(f"AND document_id IN ({scope})", sql)


if __name__ == "__main__":
    unittest.main()
