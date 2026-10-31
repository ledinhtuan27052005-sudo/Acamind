import unittest
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.document import User, Document
from app.services.study_duplicates import detect_duplicate_pairs, find_upload_duplicate
from app.api.v1.features import study_duplicates, DuplicateCheckRequest


class StudyDuplicateTests(unittest.TestCase):
    def doc(self, **kw):
        return SimpleNamespace(**(dict(id=uuid4(), content_hash=None, title=None, filename='same.pdf', authors=None, year=None) | kw))

    def test_exact_hash_without_title(self):
        pairs = detect_duplicate_pairs([self.doc(content_hash='a' * 64), self.doc(content_hash='a' * 64)])
        self.assertEqual(pairs[0]['kind'], 'identical_file')

    def test_same_filename_missing_hash_not_duplicate(self):
        self.assertEqual(detect_duplicate_pairs([self.doc(), self.doc()]), [])

    def test_similar_long_title_only_candidate(self):
        title = 'Longitudinal analysis of mental health outcomes in university students'
        pair = detect_duplicate_pairs([self.doc(title=title, year=2020), self.doc(title=title.upper(), year=2023)])[0]
        self.assertEqual(pair['kind'], 'possible_version')

    def test_generic_short_title_and_unrelated_titles_ignored(self):
        self.assertEqual(detect_duplicate_pairs([self.doc(title='Introduction'), self.doc(title='Introduction')]), [])
        self.assertEqual(detect_duplicate_pairs([self.doc(title='A longitudinal analysis of student health and anxiety'),
            self.doc(title='Experimental evaluation of neural networks for image classification')]), [])

    def test_scope_checks_before_metadata_return(self):
        db = MagicMock()
        a, b = self.doc(), self.doc()
        db.query.return_value.filter.return_value.all.return_value = [a, b]
        with patch('app.api.v1.document._enforce_doc_read_access', side_effect=HTTPException(403)), \
             patch('app.services.study_duplicates.detect_duplicate_pairs') as detect:
            with self.assertRaises(HTTPException):
                study_duplicates(DuplicateCheckRequest(document_ids=[a.id, b.id]), db, object())
            detect.assert_not_called()

    def test_repeated_ids_rejected(self):
        did = uuid4()
        with self.assertRaises(HTTPException) as error:
            study_duplicates(DuplicateCheckRequest(document_ids=[did, did]), MagicMock(), object())
        self.assertEqual(error.exception.status_code, 422)

    def test_upload_uses_hash_and_account_not_filename(self):
        engine = create_engine('sqlite:///:memory:')
        User.__table__.create(engine); Document.__table__.create(engine)
        with Session(engine) as db:
            uid = uuid4()
            doc = Document(id=uuid4(), user_id=uid, filename='same.pdf', file_path='test', status='ready', content_hash='old')
            db.add(doc); db.commit()
            self.assertIsNone(find_upload_duplicate(db, 'new', uid))
            self.assertIsNone(find_upload_duplicate(db, 'old', uuid4()))
            self.assertEqual(find_upload_duplicate(db, 'old', uid).id, doc.id)
            self.assertEqual(doc.content_hash, 'old')
            doc.status = 'failed'; db.commit()
            self.assertIsNone(find_upload_duplicate(db, 'old', uid))
        engine.dispose()


if __name__ == '__main__':
    unittest.main()
