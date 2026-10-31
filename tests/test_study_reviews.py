import unittest
from uuid import uuid4
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.document import User, Document, Chunk
from app.models.study_review import StudyFieldReview
from app.api.v1.study_reviews import save_review, review_history, ReviewInput


class StudyReviewTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        for model in (User, Document, Chunk, StudyFieldReview):
            model.__table__.create(self.engine)
        self.db = Session(self.engine)
        self.user = User(id=uuid4(), email='one@example.test', hashed_password='test', full_name='Reviewer')
        self.other = User(id=uuid4(), email='two@example.test', hashed_password='test')
        self.doc = Document(id=uuid4(), filename='source.pdf', file_path='test')
        self.chunk = Chunk(id=uuid4(), document_id=self.doc.id, content='Our sample included 100 adults recruited locally.', page_number=4)
        self.db.add_all([self.user, self.other, self.doc, self.chunk]); self.db.commit()
        self.access = patch('app.api.v1.document._enforce_doc_read_access')
        self.access.start()

    def tearDown(self):
        self.access.stop(); self.db.close(); self.engine.dispose()

    def body(self, revision=0, **kwargs):
        values = dict(expected_revision=revision, status='confirmed', value='100 adults', note='Checked PDF', chunk_id=self.chunk.id, quote=self.chunk.content)
        values.update(kwargs)
        return ReviewInput(**values)

    def history(self, user=None, before=None):
        return review_history(self.doc.id, 'sample', before, self.db, user or self.user)

    def test_save_and_reload_preserves_source_and_actor(self):
        result = save_review(self.doc.id, 'sample', self.body(), self.db, self.user)
        self.assertEqual(result['revision'], 1)
        self.assertEqual(result['page'], 4)
        self.assertEqual(result['reviewer_name'], 'Reviewer')
        self.db.expire_all()
        self.assertEqual(self.history()['items'][0]['quote'], self.chunk.content)

    def test_changes_append_and_can_withdraw_confirmation(self):
        save_review(self.doc.id, 'sample', self.body(), self.db, self.user)
        save_review(self.doc.id, 'sample', self.body(1, status='draft', value='Rechecking sample'), self.db, self.user)
        rows = self.history()['items']
        self.assertEqual([r['revision'] for r in rows], [2, 1])
        self.assertEqual(rows[1]['value'], '100 adults')
        self.assertEqual(rows[0]['status'], 'draft')

    def test_stale_revision_rejected_without_overwrite(self):
        save_review(self.doc.id, 'sample', self.body(), self.db, self.user)
        with self.assertRaises(HTTPException) as error:
            save_review(self.doc.id, 'sample', self.body(value='Stale value'), self.db, self.user)
        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(len(self.history()['items']), 1)

    def test_personal_reviews_isolated(self):
        save_review(self.doc.id, 'sample', self.body(), self.db, self.user)
        self.assertEqual(self.history(self.other)['items'], [])
        result = save_review(self.doc.id, 'sample', self.body(value='Other account review'), self.db, self.other)
        self.assertEqual(result['revision'], 1)
        self.assertEqual(self.history()['items'][0]['value'], '100 adults')

    def test_foreign_source_and_fabricated_quote_rejected(self):
        for body in (self.body(chunk_id=uuid4()), self.body(quote='A fabricated quote about the sample.')):
            with self.assertRaises(HTTPException) as error:
                save_review(self.doc.id, 'sample', body, self.db, self.user)
            self.assertEqual(error.exception.status_code, 422)
        self.assertEqual(self.history()['items'], [])

    def test_missing_document_invalid_criterion_and_blank_value(self):
        for did, criterion, body, code in [(uuid4(), 'sample', self.body(), 404),
                (self.doc.id, 'bad', self.body(), 422), (self.doc.id, 'sample', self.body(value='  '), 422)]:
            with self.assertRaises(HTTPException) as error:
                save_review(did, criterion, body, self.db, self.user)
            self.assertEqual(error.exception.status_code, code)

    def test_history_pagination_keeps_all_revisions(self):
        for index in range(22):
            save_review(self.doc.id, 'sample', self.body(index), self.db, self.user)
        first = self.history()
        second = self.history(before=first['next_before'])
        self.assertEqual(len(first['items']), 20)
        self.assertEqual([r['revision'] for r in second['items']], [2, 1])
        self.assertIsNone(second['next_before'])

    def test_denied_access_cannot_read_or_write(self):
        with patch('app.api.v1.document._enforce_doc_read_access', side_effect=HTTPException(403)):
            with self.assertRaises(HTTPException):
                self.history()
            with self.assertRaises(HTTPException):
                save_review(self.doc.id, 'sample', self.body(), self.db, self.user)
        self.assertEqual(self.history()['items'], [])

    def test_routes_and_table_registered_before_startup(self):
        from app.api.v1 import api_router
        from app.db.postgres import Base
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(api_router)
        paths = app.openapi()['paths']
        self.assertIn('/features/study-profile/{document_id}/reviews/{criterion}', paths)
        self.assertIn('/features/study-profile/{document_id}', paths)
        self.assertIn('study_field_reviews', Base.metadata.tables)


if __name__ == '__main__':
    unittest.main()
