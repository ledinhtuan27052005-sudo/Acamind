import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services import retriever


class RetrievalPageNeutralityTests(unittest.TestCase):
    def vector_search(self, original, translated):
        session = MagicMock()
        result = MagicMock()
        result.fetchall.side_effect = [original, translated]
        session.execute.return_value = result
        with patch.object(retriever, "SessionLocal") as factory, \
             patch.object(retriever, "embed_query_cached", return_value=[.1, .2]), \
             patch.object(retriever, "_is_valid_prose_chunk", return_value=True), \
             patch.object(retriever, "is_reference_content", return_value=False):
            factory.return_value.__enter__.return_value = session
            return retriever._vector_search_task("hạn chế", "limitations")

    def row(self, key, page, score):
        return SimpleNamespace(id=key, document_id="doc", content="Study limitations", page_number=page, score=score)

    def test_late_original_evidence_keeps_better_score(self):
        rows = [self.row("late", 15, .800), self.row("early", 1, .799)]
        self.assertEqual([r.id for r in self.vector_search(rows, [])], ["late", "early"])

    def test_late_translated_evidence_keeps_better_score(self):
        rows = [self.row("late", 15, .800), self.row("early", 1, .799)]
        self.assertEqual([r.id for r in self.vector_search([], rows)], ["late", "early"])

    def test_changing_page_numbers_does_not_change_order(self):
        first = self.vector_search([self.row("a", 1, .8), self.row("b", 20, .799)], [])
        second = self.vector_search([self.row("a", 20, .8), self.row("b", 1, .799)], [])
        self.assertEqual([r.id for r in first], [r.id for r in second])

    def test_all_fts_query_paths_use_unweighted_relevance(self):
        session = MagicMock()
        session.execute.return_value.fetchall.return_value = []
        scope = "'00000000-0000-0000-0000-000000000001'"
        retriever._bm25_via_fts(["limitations"], "clinical psychology limitations", ["caveats"], scope, session)
        queries = [str(c.args[0]) for c in session.execute.call_args_list if "FROM page_texts" in str(c.args[0])]
        # 4 đường truy vấn: cụm từ liền kề (phrase), truy vấn chính, cặp từ cốt lõi, mở rộng.
        self.assertEqual(len(queries), 4)
        for sql in queries:
            self.assertIn("ts_rank_cd(tsv, to_tsquery('simple', :q)) AS rank", sql)
            self.assertNotIn("CASE WHEN page_number", sql)
            self.assertNotIn("* ts_rank_cd", sql)
            self.assertIn(f"document_id IN ({scope})", sql)
            self.assertIn("ORDER BY rank DESC", sql)


if __name__ == "__main__":
    unittest.main()
