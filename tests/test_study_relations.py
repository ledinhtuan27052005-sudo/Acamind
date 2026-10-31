import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from uuid import uuid4
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.services import study_relations as relations
from app.services.study_comparability import profile_passages


class StudyRelationsTests(unittest.TestCase):
    def setUp(self):
        self.a = [{'source': '0', 'document_id': 'a', 'page': 3, 'text': 'We found no improvement after twelve weeks.'}]
        self.b = [{'source': '0', 'document_id': 'b', 'page': 7, 'text': 'Our results showed no improvement after twelve weeks.'}]

    def item(self, **changes):
        return {'aspect': 'Outcome at twelve weeks', 'relation': 'agreement', 'reason': 'Both report no improvement.',
                'same_outcome': True, 'same_timepoint': True, 'same_comparison': True, 'same_direction_coding': True,
                'evidence_a': {'source': '0', 'quote': self.a[0]['text']},
                'evidence_b': {'source': '0', 'quote': self.b[0]['text']}, **changes}

    def test_valid_pair_preserves_two_sources_and_pages(self):
        result = relations.validate_relations({'relations': [self.item()]}, self.a, self.b)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['evidence_a']['page'], 3)
        self.assertEqual(result[0]['evidence_b']['page'], 7)
        self.assertEqual(result[0]['assessment'], 'model_assessed')

    def test_missing_compatibility_flags_reject_classification(self):
        for key in ('same_outcome', 'same_timepoint', 'same_comparison', 'same_direction_coding'):
            for value in (False, None, 'true', 1):
                self.assertEqual(relations.validate_relations({'relations': [self.item(**{key: value})]}, self.a, self.b), [])

    def test_fabrication_partial_quote_and_wrong_source_are_rejected(self):
        for evidence in ({'source': '0', 'quote': 'We found improved outcomes after twelve weeks.'},
                         {'source': '0', 'quote': 'no improvement after twelve weeks.'},
                         {'source': '9', 'quote': self.a[0]['text']}, {}):
            self.assertEqual(relations.validate_relations({'relations': [self.item(evidence_a=evidence)]}, self.a, self.b), [])

    def test_duplicate_pair_is_unique_and_conflicting_labels_are_discarded(self):
        raw = {'relations': [self.item(), self.item()]}
        self.assertEqual(len(relations.validate_relations(raw, self.a, self.b)), 1)
        raw['relations'].append(self.item(relation='contradiction'))
        self.assertEqual(relations.validate_relations(raw, self.a, self.b), [])

    def test_malformed_unknown_and_same_document_do_not_establish_relation(self):
        for raw in (None, [], {'relations': {}}, {'relations': [False]}, {'relations': [self.item(relation='insufficient')]}):
            self.assertEqual(relations.validate_relations(raw, self.a, self.b), [])
        self.assertEqual(relations.validate_relations({'relations': [self.item()]}, self.a, self.a), [])

    def test_incompatible_or_missing_conditions_skip_relation_model(self):
        for status in ('conditions_differ', 'insufficient_data'):
            with patch.object(relations, 'assess_profiles', return_value={'status': status}), patch.object(relations, 'local_assess') as model:
                result = relations.assess_study_relations({}, {}, 'outcome')
                self.assertEqual(result['status'], status)
                self.assertEqual(result['relations'], [])
                model.assert_not_called()

    def test_compatible_pair_runs_assessment_and_rejects_empty_output(self):
        with patch.object(relations, 'assess_profiles', return_value={'status': 'comparable'}), \
             patch.object(relations, 'profile_passages', side_effect=[self.a, self.b]), \
             patch.object(relations, 'local_assess', return_value={'relations': []}):
            result = relations.assess_study_relations({'title': 'A'}, {'title': 'B'}, 'outcome')
        self.assertEqual(result['status'], 'insufficient_data')

    def test_long_source_keeps_trailing_qualifier(self):
        quote = 'Our results ' + 'were measured ' * 60 + 'but the difference was not significant.'
        profile = {'document_id': 'a', 'fields': {'finding': {'candidates': [{'quote': quote, 'page': 1, 'origin': 'current_study_candidate'}]}}}
        self.assertEqual(profile_passages(profile)[0]['text'], quote)

    def test_endpoint_requires_focus_and_keeps_model_failure_separate(self):
        from app.api.v1.features import study_relations, ComparabilityRequest
        req = ComparabilityRequest(document_a=uuid4(), document_b=uuid4())
        with patch('app.api.v1.features.study_profile') as profile:
            with self.assertRaises(HTTPException) as error:
                study_relations(req, MagicMock(), object())
            self.assertEqual(error.exception.status_code, 400)
            profile.assert_not_called()
        req.focus = 'outcome'
        with patch('app.api.v1.features.study_profile', return_value={}), patch.object(relations, 'assess_study_relations', side_effect=ConnectionError):
            with self.assertRaises(HTTPException) as error:
                study_relations(req, MagicMock(), object())
            self.assertEqual(error.exception.status_code, 503)


if __name__ == '__main__':
    unittest.main()
