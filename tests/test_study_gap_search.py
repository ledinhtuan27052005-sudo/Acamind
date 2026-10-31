import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException
from app.services.study_gap_search import search_gap
from app.api.v1.features import study_gap_search, GapSearchRequest


class GapSearchTests(unittest.TestCase):
    def test_retrieval_is_scoped_and_duplicates_and_foreign_hits_removed(self):
        did = uuid4()
        hits = [{'document_id': str(did), 'id': 'a'}] * 2 + [{'document_id': str(uuid4()), 'id': 'b'}]
        with patch('app.services.retriever.retrieve', return_value=hits) as retrieve:
            query, ids, explanations = search_gap(did, 'sample', 'adults', object())
        self.assertEqual(ids, ['a'])
        self.assertEqual(explanations['a']['retrieval_position'], 1)
        self.assertEqual(list(explanations), ['a'])
        self.assertEqual(retrieve.call_args.args[1], [str(did)])
        self.assertIn('adults', query)

    def test_unknown_criterion_rejected_before_search(self):
        with patch('app.services.retriever.retrieve') as retrieve:
            with self.assertRaises(ValueError):
                search_gap(uuid4(), 'bad', '', object())
            retrieve.assert_not_called()

    def test_denied_access_never_retrieves(self):
        with patch('app.api.v1.document._enforce_doc_read_access', side_effect=HTTPException(403)), \
             patch('app.services.study_gap_search.search_gap') as search:
            with self.assertRaises(HTTPException):
                study_gap_search(uuid4(), GapSearchRequest(criterion='sample'), MagicMock(), object())
            search.assert_not_called()

    def test_original_content_reloaded_and_no_fabricated_quote(self):
        did, cid = uuid4(), uuid4()
        db = MagicMock()
        chunk = MagicMock(id=cid, content='Original full source text.', page_number=3)
        db.query.return_value.filter.return_value.all.return_value = [chunk]
        with patch('app.api.v1.document._enforce_doc_read_access'), \
             patch('app.services.study_gap_search.search_gap', return_value=('query', [str(cid), 'synthetic-id'], {str(cid): {'model_score': 0.4}})):
            result = study_gap_search(did, GapSearchRequest(criterion='sample'), db, object())
        self.assertEqual(result['candidates'], [{'chunk_id': str(cid), 'page': 3, 'quote': chunk.content, 'ranking': {'model_score': 0.4}}])
        self.assertEqual(result['status'], 'unverified')

    def test_search_failure_is_not_missing_evidence(self):
        with patch('app.api.v1.document._enforce_doc_read_access'), \
             patch('app.services.study_gap_search.search_gap', side_effect=RuntimeError):
            with self.assertRaises(HTTPException) as error:
                study_gap_search(uuid4(), GapSearchRequest(criterion='sample'), MagicMock(), object())
        self.assertEqual(error.exception.status_code, 503)

    def test_empty_search_has_no_candidates(self):
        with patch('app.api.v1.document._enforce_doc_read_access'), \
             patch('app.services.study_gap_search.search_gap', return_value=('query', [], {})):
            result = study_gap_search(uuid4(), GapSearchRequest(criterion='sample'), MagicMock(), object())
        self.assertEqual(result['status'], 'not_found')
        self.assertEqual(result['candidates'], [])


if __name__ == '__main__':
    unittest.main()
