import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.services import study_comparability as comp
from app.services.study_profile import build_study_profile


class StudyComparabilityTests(unittest.TestCase):
    def setUp(self):
        self.a = [{'source': '0', 'document_id': 'a', 'page': 1, 'text': 'Adults were assessed at twelve weeks.'}]
        self.b = [{'source': '0', 'document_id': 'b', 'page': 2, 'text': 'Adults were assessed at twelve weeks.'}]

    def cells(self):
        return {'criteria': [{'key': key, 'status': 'matched', 'reason': 'Explicit matching conditions',
            'evidence_a': {'source': '0', 'quote': self.a[0]['text']},
            'evidence_b': {'source': '0', 'quote': self.b[0]['text']}} for key in comp.CRITERIA]}

    def test_comparable_requires_all_six_criteria(self):
        result = comp.validate_comparability(self.cells(), self.a, self.b)
        self.assertEqual(result['status'], 'comparable')
        raw = self.cells(); raw['criteria'].pop()
        self.assertEqual(comp.validate_comparability(raw, self.a, self.b)['status'], 'insufficient_data')

    def test_difference_does_not_claim_contradiction(self):
        raw = self.cells(); raw['criteria'][0]['status'] = 'different'
        self.assertEqual(comp.validate_comparability(raw, self.a, self.b)['status'], 'conditions_differ')

    def test_fabricated_missing_or_cross_source_quotes_are_rejected(self):
        for evidence in ({}, {'source': 'wrong', 'quote': self.a[0]['text']}, {'source': '0', 'quote': 'Invented description of the study'}):
            raw = self.cells(); raw['criteria'][0]['evidence_a'] = evidence
            result = comp.validate_comparability(raw, self.a, self.b)
            self.assertEqual(result['criteria'][0]['status'], 'unknown')
            self.assertEqual(result['status'], 'insufficient_data')

    def test_duplicate_and_malformed_criteria_are_unknown(self):
        raw = self.cells(); raw['criteria'].append(raw['criteria'][0])
        self.assertEqual(comp.validate_comparability(raw, self.a, self.b)['criteria'][0]['status'], 'unknown')
        for raw in ([], {'criteria': None}, {'criteria': [False]}):
            self.assertEqual(comp.validate_comparability(raw, self.a, self.b)['status'], 'insufficient_data')

    def test_same_document_cannot_supply_both_sides(self):
        self.assertEqual(comp.validate_comparability(self.cells(), self.a, self.a)['status'], 'insufficient_data')

    def test_profile_excludes_secondary_attribution_and_missing_evidence_skips_model(self):
        a = build_study_profile({'document_id': 'a', 'title': 'A'}, [{'document_id': 'a', 'page_number': 1,
             'content': 'Previous studies reported improved outcomes after twelve weeks.'}])
        b = build_study_profile({'document_id': 'b', 'title': 'B'}, [])
        self.assertEqual(comp.profile_passages(a), [])
        with patch.object(comp, 'local_assess') as model:
            self.assertEqual(comp.assess_profiles(a, b)['status'], 'insufficient_data')
        model.assert_not_called()

    def test_remote_model_address_is_rejected(self):
        from app.core.config import settings
        with patch.object(settings, 'OLLAMA_BASE_URL', 'https://remote.invalid'), patch.object(comp.httpx, 'Client') as client:
            with self.assertRaises(ValueError): comp.local_assess({})
            client.assert_not_called()

    def test_model_failure_is_503_not_false_incompatibility(self):
        from app.api.v1.features import study_comparability, ComparabilityRequest
        from fastapi import HTTPException
        with patch('app.api.v1.features.study_profile', return_value={}), patch.object(comp, 'assess_profiles', side_effect=ConnectionError):
            with self.assertRaises(HTTPException) as error:
                study_comparability(ComparabilityRequest(document_a=uuid4(), document_b=uuid4()), MagicMock(), object())
        self.assertEqual(error.exception.status_code, 503)


if __name__ == '__main__':
    unittest.main()
