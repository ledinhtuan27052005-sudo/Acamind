import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from fastapi import HTTPException
from pydantic import ValidationError
from app.api.v1.evaluate import _compute_chunk_metrics, EvalRequest, AblationSuiteRequest, run_statistical_ablation_suite


class EvaluationIntegrityTests(unittest.TestCase):
    def test_identical_retrieval_gets_identical_metrics_for_all_architectures(self):
        results = [_compute_chunk_metrics('alpha beta', [], [{'content': 'alpha'}], mode)
                   for mode in ('naive_dense', 'hybrid_rrf', 'acamind_full')]
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1], results[2])
        self.assertEqual(results[0]['keyword_coverage_pct'], 50)
        for key in ('citation_precision_pct', 'semantic_alignment_pct', 'overall_composite_pct'):
            self.assertIsNone(results[0][key])

    def test_empty_or_unrelated_retrieval_has_no_artificial_floor(self):
        for chunks in ([], [{'content': 'wholesale capacity'}]):
            self.assertEqual(_compute_chunk_metrics('who apa', [], chunks, 'acamind_full')['keyword_coverage_pct'], 0)

    def test_statistical_suite_cannot_export_synthetic_significance(self):
        db = MagicMock()
        with self.assertRaises(HTTPException) as error:
            run_statistical_ablation_suite(AblationSuiteRequest(), db)
        self.assertEqual(error.exception.status_code, 422)
        db.execute.assert_not_called()

    def test_invalid_document_scopes_are_rejected_before_sql(self):
        for model, extra in ((EvalRequest, {'question': 'q'}), (AblationSuiteRequest, {})):
            with self.assertRaises(ValidationError):
                model(document_ids=["x' OR TRUE --"], **extra)


if __name__ == '__main__':
    unittest.main()
