import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.services.study_profile import build_study_profile


class StudyProfileTests(unittest.TestCase):
    def build(self, text, **extra):
        return build_study_profile({'document_id': 'a', 'title': 'A'}, [
            {'document_id': 'a', 'id': 'c', 'page_number': 7, 'content': text, **extra}])

    def test_seven_fields_and_exact_source_offsets(self):
        text = 'Our objective was to assess response.\nWe recruited participants from the adult population.\nOur results showed no difference between groups.'
        result = self.build(text)
        self.assertTrue({'objective', 'method', 'sample', 'data', 'measure', 'finding', 'limitation'} <= set(result['fields']))
        for field in result['fields'].values():
            for candidate in field['candidates']:
                self.assertEqual(candidate['quote'], text[candidate['start']:candidate['end']])
                self.assertEqual(candidate['document_id'], 'a')
                self.assertEqual(candidate['page'], 7)
        self.assertEqual(result['fields']['limitation']['status'], 'not_found')

    def test_other_documents_and_parent_context_are_excluded(self):
        self.assertEqual(self.build('Plain background.', document_id='b')['coverage']['chunks_scanned'], 0)
        result = self.build('Plain background.', parent_context='Our results showed improved outcomes.')
        self.assertFalse(result['fields']['finding']['candidates'])

    def test_external_findings_are_not_promoted_to_current_study(self):
        result = self.build('Previous studies reported positive results in all participants.')
        self.assertEqual(result['fields']['finding']['candidates'][0]['origin'], 'cited_study_candidate')

    def test_current_study_precedes_external_candidates(self):
        result = self.build('Previous studies reported positive results.\nOur results showed no improvement in participants.')
        self.assertEqual(result['fields']['finding']['candidates'][0]['origin'], 'current_study_candidate')

    def test_overlapping_chunks_do_not_repeat_same_quote(self):
        chunk = {'document_id': 'a', 'page_number': 1, 'content': 'Our results showed no difference between groups.'}
        result = build_study_profile({'document_id': 'a'}, [chunk, chunk])
        self.assertEqual(result['fields']['finding']['candidate_count'], 1)

    def test_invalid_pages_cannot_invent_a_source_page(self):
        for page in (None, 0, -1, 'bad', True):
            self.assertEqual(self.build('Our results showed no difference between groups.', page_number=page)['coverage']['chunks_scanned'], 0)

    def test_processing_limit_is_explicit(self):
        self.assertTrue(self.build('x' * 2_000_001)['coverage']['truncated'])

    def test_endpoint_requires_document_read_access_before_chunks(self):
        from app.api.v1.features import study_profile
        did = uuid4()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(id=did)
        with patch('app.api.v1.document._enforce_doc_read_access', side_effect=HTTPException(403, 'Forbidden')):
            with self.assertRaises(HTTPException) as error:
                study_profile(did, db, object())
        self.assertEqual(error.exception.status_code, 403)
        self.assertEqual(db.query.call_count, 1)


if __name__ == '__main__':
    unittest.main()
