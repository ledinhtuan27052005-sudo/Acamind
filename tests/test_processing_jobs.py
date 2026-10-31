import unittest
from uuid import uuid4
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.document import User, Document
from app.models.processing_job import ProcessingJob
from app.services.processing_jobs import checkpoint, ProcessingCancelled
from app.api.v1.processing import cancel_processing, retry_processing, processing_status


class ProcessingTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        for model in (User, Document, ProcessingJob):
            model.__table__.create(self.engine)
        self.db = Session(self.engine)
        self.user = User(id=uuid4(), email='user@test.local', hashed_password='test', role='student')
        self.doc = Document(id=uuid4(), user_id=self.user.id, filename='same.pdf', file_path='test.pdf', status='processing')
        self.db.add_all([self.user, self.doc]); self.db.commit()

    def tearDown(self):
        self.db.close(); self.engine.dispose()

    def test_stages_persist_without_fabricated_percent(self):
        checkpoint(self.db, self.doc.id, 'embedding')
        result = processing_status(self.doc.id, self.db, self.user)
        self.assertEqual(result['stage'], 'embedding')
        self.assertIsNotNone(result['updated_at'])
        self.assertNotIn('percent', result)

    def test_cancel_waits_for_checkpoint_and_never_marks_ready(self):
        cancel_processing(self.doc.id, self.db, self.user)
        self.assertEqual(self.doc.status, 'cancel_requested')
        with self.assertRaises(ProcessingCancelled):
            checkpoint(self.db, self.doc.id, 'ready')
        self.assertEqual(self.doc.status, 'cancelled')
        with self.assertRaises(ProcessingCancelled):
            checkpoint(self.db, self.doc.id, 'ready')

    def test_cancellation_wins_over_error(self):
        cancel_processing(self.doc.id, self.db, self.user)
        with self.assertRaises(ProcessingCancelled):
            checkpoint(self.db, self.doc.id, 'error')
        self.assertEqual(self.doc.status, 'cancelled')

    def test_completed_job_cannot_cancel_or_retry(self):
        checkpoint(self.db, self.doc.id, 'ready')
        for action in (cancel_processing, retry_processing):
            with self.assertRaises(HTTPException) as error:
                action(self.doc.id, self.db, self.user)
            self.assertEqual(error.exception.status_code, 409)

    def test_other_user_cannot_control_or_inspect(self):
        other = User(id=uuid4(), role='student')
        for action in (cancel_processing, retry_processing, processing_status):
            with self.assertRaises(HTTPException) as error:
                action(self.doc.id, self.db, other)
            self.assertEqual(error.exception.status_code, 403)

    def test_retry_reuses_saved_pdf_and_id(self):
        self.doc.status = 'error'; self.db.commit()
        with patch('app.api.v1.processing.os.path.isfile', return_value=True), patch('app.api.v1.document._enqueue_pipeline') as enqueue:
            retry_processing(self.doc.id, self.db, self.user)
            self.assertEqual(enqueue.call_args.args[:2], ('test.pdf', str(self.doc.id)))
            self.assertEqual(self.doc.status, 'processing')
            with self.assertRaises(HTTPException):
                retry_processing(self.doc.id, self.db, self.user)
            self.assertEqual(enqueue.call_count, 1)

    def test_missing_pdf_and_queue_failure_reported(self):
        self.doc.status = 'error'; self.db.commit()
        with patch('app.api.v1.processing.os.path.isfile', return_value=False):
            with self.assertRaises(HTTPException) as error:
                retry_processing(self.doc.id, self.db, self.user)
            self.assertEqual(error.exception.status_code, 409)
        with patch('app.api.v1.processing.os.path.isfile', return_value=True), patch('app.api.v1.document._enqueue_pipeline', side_effect=RuntimeError):
            with self.assertRaises(HTTPException) as error:
                retry_processing(self.doc.id, self.db, self.user)
            self.assertEqual(error.exception.status_code, 503)
            self.assertEqual(self.doc.status, 'error')

    def test_pending_cancel_skips_pdf_parsing(self):
        from app.api.v1.document import _run_pipeline
        cancel_processing(self.doc.id, self.db, self.user)
        did = str(self.doc.id)
        with patch('app.db.postgres.SessionLocal', return_value=self.db), \
             patch('app.db.postgres._resolve_postgres_url', return_value='unused'), \
             patch('app.api.v1.document.parse_pdf') as parse:
            _run_pipeline('test.pdf', did, 'unused')
            parse.assert_not_called()

    def test_routes_registered(self):
        from fastapi import FastAPI
        from app.api.v1 import api_router
        app = FastAPI(); app.include_router(api_router)
        self.assertIn('/document/{document_id}/retry-processing', app.openapi()['paths'])


if __name__ == '__main__':
    unittest.main()
