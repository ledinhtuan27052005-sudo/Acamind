import contextvars
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import astuple, fields
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "eval"))

from app.services.ablation_config import CONFIGS, FULL, flags, use_flags  # noqa: E402
import metrics  # noqa: E402
import stats  # noqa: E402


class AblationFlagTests(unittest.TestCase):
    def test_default_is_full_system(self):
        self.assertEqual(flags(), FULL)

    def test_each_config_adds_exactly_one_component(self):
        # use_parent_context chỉ mở rộng nội dung (không đổi thứ hạng) nên được bật
        # cùng use_density_priority ở bước cuối "evidence prioritisation".
        comp = [f.name for f in fields(FULL) if f.name not in ("fixed_depth", "use_parent_context")]
        names = list(CONFIGS)
        for prev, cur in zip(names, names[1:]):
            a = [getattr(CONFIGS[prev], n) for n in comp]
            b = [getattr(CONFIGS[cur], n) for n in comp]
            self.assertEqual(sum(1 for x, y in zip(a, b) if x != y), 1, f"{prev} -> {cur}")
            self.assertTrue(all(y or not x for x, y in zip(a, b)), "components must only be added")
        self.assertEqual(CONFIGS[names[-1]], FULL)

    def test_use_flags_restores_previous_value(self):
        with use_flags(CONFIGS["M1_Dense"]):
            self.assertFalse(flags().use_fts)
        self.assertEqual(flags(), FULL)

    def test_flags_propagate_to_worker_threads_with_copied_context(self):
        with ThreadPoolExecutor(1) as ex, use_flags(CONFIGS["M2_Hybrid_RRF"]):
            got = ex.submit(contextvars.copy_context().run, flags).result()
        self.assertEqual(got, CONFIGS["M2_Hybrid_RRF"])


class MetricTests(unittest.TestCase):
    def test_unlabelled_question_is_excluded_not_counted_as_hit(self):
        m = metrics.retrieval_metrics([("a.pdf", 1)], {})
        self.assertIsNone(m["doc_hit@5"])
        self.assertIsNone(m["doc_mrr@10"])

    def test_page_hit_at_5_uses_five_pages(self):
        ranked = [(f"d{i}.pdf", 1) for i in range(6)]
        self.assertEqual(metrics.retrieval_metrics(ranked, {("d5.pdf", 1): 2})["page_hit@5"], 0.0)
        self.assertEqual(metrics.retrieval_metrics(ranked, {("d4.pdf", 1): 2})["page_hit@5"], 1.0)

    def test_recall_and_mrr(self):
        ranked = [("x.pdf", 1), ("a.pdf", 2), ("b.pdf", 3)]
        q = {("a.pdf", 2): 2, ("c.pdf", 1): 1}
        m = metrics.retrieval_metrics(ranked, q)
        self.assertAlmostEqual(m["doc_recall@5"], 0.5)
        self.assertAlmostEqual(m["doc_mrr@10"], 0.5)
        self.assertTrue(0 < m["doc_ndcg@10"] < 1)

    def test_answer_facet_not_counted(self):
        self.assertIsNone(metrics.facet_coverage(["anything here"], ["answer"]))

    def test_target_coverage_uses_entity_labels(self):
        labels = {("a.pdf", 1): {"CBT"}}
        self.assertEqual(metrics.target_coverage([("a.pdf", 1)], labels, ["CBT", "SSRI"]), 0.5)


class StatsTests(unittest.TestCase):
    def test_no_artificial_p_floor(self):
        a, b = [1.0] * 40, [0.0] * 40
        p = stats.mcnemar_exact_p(a, b)
        self.assertLess(p, 1e-11)
        self.assertNotEqual(p, 1e-12)

    def test_holm_is_monotone_and_bounded(self):
        adj = stats.holm([0.01, 0.04, None, 0.03])
        self.assertIsNone(adj[2])
        self.assertTrue(all(x <= 1 for x in adj if x is not None))
        self.assertAlmostEqual(adj[0], 0.03)

    def test_bootstrap_ci_contains_mean(self):
        d, lo, hi = stats.bootstrap_ci([1, 0, 1, 1], [0, 0, 1, 0])
        self.assertTrue(lo <= d <= hi)


if __name__ == "__main__":
    unittest.main()
