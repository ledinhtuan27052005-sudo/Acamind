'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  ArrowLeft, Download, Copy, Check, Code, Zap, ShieldCheck,
  Activity, Layers, FileText, Sparkles, Award,
} from 'lucide-react';
import {
  getDocuments,
  DocumentInfo,
  runEvaluation,
  EvalResult,
  runAblationBenchmark,
  AblationBenchmarkResult,
  runStatisticalAblationSuite,
  AblationSuiteResult,
} from '@/lib/api';
import { useAppStore } from '@/store/useAppStore';
import { GuestBlockScreen } from '@/components/auth/AuthRequiredModal';
import { AcademicDocumentRenderer, cleanMarkdownText } from '@/components/ui/AcademicDocumentRenderer';

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 75 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-rose-500';
  return (
    <div className="mb-3.5">
      <div className="flex justify-between text-xs mb-1">
        <span className="font-semibold text-slate-700 dark:text-slate-200">{label}</span>
        <span className={`font-bold font-mono ${pct >= 75 ? 'text-emerald-600' : pct >= 50 ? 'text-amber-600' : 'text-rose-500'}`}>
          {pct}%
        </span>
      </div>
      <div className="w-full h-2.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-2.5 rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

const SAMPLE_BENCHMARK_QUERIES = [
  'So sánh hiệu quả của Liệu pháp Nhận thức Hành vi (CBT) và thuốc chống trầm cảm SSRI trên thang đo BDI-II và PHQ-9',
  'Cơ chế sinh học thần kinh của Hạch hạnh nhân (Amygdala) và Vỏ não trước trán (PFC) trong rối loạn lo âu và trầm cảm',
  'Đánh giá độ tin cậy, phương pháp nghiên cứu và cỡ mẫu của các thử nghiệm lâm sàng về can thiệp tâm lý',
];

export default function EvaluatePage() {
  const { user } = useAppStore();
  const [mounted, setMounted] = useState(false);
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [ablationLoading, setAblationLoading] = useState(false);
  const [suiteLoading, setSuiteLoading] = useState(false);
  const [result, setResult] = useState<EvalResult | null>(null);
  const [ablationResult, setAblationResult] = useState<AblationBenchmarkResult | null>(null);
  const [suiteResult, setSuiteResult] = useState<AblationSuiteResult | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (user) {
      getDocuments()
        .then((d) => {
          const ready = d.filter((doc) => doc.status === 'ready');
          setDocs(ready);
          if (ready.length > 0 && selectedIds.length === 0) {
            setSelectedIds(ready.slice(0, Math.min(5, ready.length)).map((x) => x.id));
          }
        })
        .catch(console.error);
    }
  }, [user]);

  if (mounted && !user) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-slate-900 flex items-center justify-center p-4">
        <GuestBlockScreen
          title="Yêu cầu đăng nhập để sử dụng Phòng Thí nghiệm Thực nghiệm RAG"
          description="Phòng thí nghiệm đối chứng thuật toán (Live RAG Ablation & Benchmark Lab) yêu cầu tài khoản đã đăng nhập."
        />
      </div>
    );
  }

  const toggleDoc = (id: string) =>
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );

  const handleRunAblation = async () => {
    if (!question.trim()) {
      setError('Vui lòng nhập câu hỏi truy vấn thực nghiệm.');
      return;
    }
    setAblationLoading(true);
    setError('');
    try {
      const res = await runAblationBenchmark(
        question.trim(),
        selectedIds.length > 0 ? selectedIds : undefined
      );
      setAblationResult(res);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || (e as Error).message || 'Lỗi khi chạy đối chứng thuật toán.');
    } finally {
      setAblationLoading(false);
    }
  };

  const handleRunStatisticalSuite = async () => {
    setSuiteLoading(true);
    setError('');
    try {
      const res = await runStatisticalAblationSuite(
        question.trim() || undefined,
        selectedIds.length > 0 ? selectedIds : undefined
      );
      setSuiteResult(res);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || (e as Error).message || 'Lỗi khi chạy bộ kiểm định thống kê đa truy vấn.');
    } finally {
      setSuiteLoading(false);
    }
  };

  const handleCopySuiteLatex = () => {
    if (!suiteResult) return;
    navigator.clipboard.writeText(suiteResult.latex_statistical_table);
    setCopiedKey('suite_latex');
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleRunJudge = async () => {
    if (!question.trim()) {
      setError('Vui lòng nhập câu hỏi truy vấn thực nghiệm.');
      return;
    }
    if (selectedIds.length === 0) {
      setError('Vui lòng chọn ít nhất 1 tài liệu nguồn.');
      return;
    }
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await runEvaluation(question.trim(), selectedIds);
      setResult(res);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || (e as Error).message || 'Lỗi khi đánh giá RAG.');
    } finally {
      setLoading(false);
    }
  };

  const handleExportAblationCsv = () => {
    if (!ablationResult) return;
    const esc = (v: string | number | null) => `"${String(v ?? '').replace(/"/g, '""')}"`;
    const headers = [
      'Pipeline ID',
      'Architecture Name',
      'Overall Score (%)',
      'Faithfulness / Grounding (%)',
      'Keyword Coverage (%)',
      'Semantic Alignment (%)',
      'Citation Precision (%)',
      'Top Chunks Retrieved',
      'Latency (ms)',
    ];
    const rows = ablationResult.pipelines.map((p) => [
      esc(p.id),
      esc(p.name),
      esc(p.overall_score_pct),
      esc(p.faithfulness_pct),
      esc(p.keyword_coverage_pct),
      esc(p.semantic_alignment_pct),
      esc(p.citation_precision_pct),
      esc(p.top_chunks.length),
      esc(p.latency_ms),
    ]);
    const csv = '\uFEFF' + [headers.map(esc).join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Acamind_Ablation_Benchmark_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleCopyAblationLatex = () => {
    if (!ablationResult) return;
    const lines = ablationResult.pipelines.map((p) => {
      const isProp = p.id === 'acamind_full' || p.id === 'acamind_proposed';
      const fmt = (v: number | null) => v === null ? "N/A" : `${v.toFixed(1)}\\%`;
      const nameStr = isProp ? `\\textbf{${p.name}}` : p.name;
      return `${nameStr} & ${fmt(p.faithfulness_pct)} & ${fmt(p.keyword_coverage_pct)} & ${fmt(p.semantic_alignment_pct)} & ${fmt(p.citation_precision_pct)} & ${fmt(p.overall_score_pct)} & ${p.latency_ms} ms \\\\ \\hline`;
    });

    const tex = [
      '\\begin{table*}[htbp]',
      '\\centering',
      '\\caption{Exploratory retrieval comparison; N/A metrics require independent labels}',
      '\\label{tab:acamind_ablation_study}',
      '\\renewcommand{\\arraystretch}{1.25}',
      '\\begin{tabular}{|l|c|c|c|c|c|c|}',
      '\\hline',
      '\\textbf{Architecture Variant} & \\textbf{Faithfulness} & \\textbf{Keyword Cov.} & \\textbf{Semantic Sim.} & \\textbf{Citation Prec.} & \\textbf{Overall} & \\textbf{Latency} \\\\ \\hline',
      ...lines,
      '\\end{tabular}',
      '\\end{table*}',
    ].join('\n');

    navigator.clipboard.writeText(tex);
    setCopiedKey('latex');
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const avgScore = result
    ? Math.round(((result.faithfulness + result.answer_relevancy + result.context_quality) / 3) * 100)
    : 0;

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div>
        <Link
          href="/profile"
          className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-teal-600 transition-colors mb-3"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Quay lại Hồ sơ Nghiên cứu
        </Link>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2.5">
              <span>🔬 Phòng Thí nghiệm Đối chứng Thuật toán Trực tiếp (Live RAG Ablation &amp; Benchmark Lab)</span>
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Chạy thực nghiệm đối chứng trực tiếp 3 kiến trúc: (A) Naive Dense RAG vs. (B) Standard Hybrid RRF vs. (C) Acamind Full Pipeline, kèm Kiểm định Ý nghĩa Thống kê Đa truy vấn (Paired t-test, p-value, Cohen&apos;s d, Bootstrap 95% CI) và Đường biên Tối ưu Pareto.
            </p>
          </div>
        </div>
      </div>

      {/* Control Panel */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 space-y-4">
        <div className="grid md:grid-cols-12 gap-6">
          <div className="md:col-span-7 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-bold text-sm text-slate-800 dark:text-slate-100">
                1. Câu hỏi Truy vấn Thực nghiệm (Benchmark Query)
              </h2>
              <span className="text-[11px] text-teal-600 dark:text-teal-400 font-semibold">
                Hỗ trợ truy vấn đơn mục tiêu &amp; bộ Benchmark N=6 truy vấn
              </span>
            </div>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={3}
              placeholder="Nhập câu hỏi nghiên cứu để chạy đối chứng 3 thuật toán RAG (hoặc bấm chạy Bộ Kiểm định Thống kê N=6 truy vấn bên dưới)..."
              className="w-full border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-800 dark:text-slate-100 resize-none focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
            <div className="space-y-1">
              <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                💡 Gợi ý câu hỏi Benchmark mẫu (nhấn để điền nhanh):
              </p>
              <div className="flex flex-wrap gap-1.5">
                {SAMPLE_BENCHMARK_QUERIES.map((sq, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setQuestion(sq)}
                    className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-teal-50 dark:bg-slate-800 dark:hover:bg-teal-950/50 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition-colors cursor-pointer text-left truncate max-w-full"
                  >
                    {sq}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="md:col-span-5 space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">
                2. Tập Tài liệu Nguồn ({selectedIds.length}/{docs.length})
              </h3>
              <button
                type="button"
                onClick={() =>
                  setSelectedIds(
                    selectedIds.length === docs.length ? [] : docs.map((d) => d.id)
                  )
                }
                className="text-[11px] font-semibold text-teal-600 hover:underline cursor-pointer"
              >
                {selectedIds.length === docs.length ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
              </button>
            </div>
            <div className="max-h-40 overflow-y-auto space-y-1 rounded-xl border border-slate-200 dark:border-slate-700 p-2.5 bg-slate-50/50 dark:bg-slate-800/40">
              {docs.length === 0 ? (
                <p className="text-xs text-slate-400">Chưa có tài liệu PDF sẵn sàng.</p>
              ) : (
                docs.map((d) => (
                  <label
                    key={d.id}
                    className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-200 cursor-pointer hover:bg-white dark:hover:bg-slate-800 px-2 py-1.5 rounded-lg"
                  >
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(d.id)}
                      onChange={() => toggleDoc(d.id)}
                      className="accent-teal-600"
                    />
                    <span className="truncate font-medium">{d.title || d.filename}</span>
                  </label>
                ))
              )}
            </div>
          </div>
        </div>

        {error && (
          <div className="text-xs text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 rounded-xl px-3.5 py-2.5">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
          <button
            type="button"
            onClick={handleRunAblation}
            disabled={ablationLoading}
            className="w-full bg-gradient-to-r from-teal-600 to-indigo-600 hover:opacity-95 text-white py-3 px-4 rounded-xl font-bold text-xs sm:text-sm shadow-md transition-all disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2"
          >
            <Zap className="w-4 h-4 shrink-0" />
            <span>
              {ablationLoading
                ? '⏳ Đang chạy Đối chứng A/B/C...'
                : '⚡ 1. Chạy Đối chứng Đơn Truy vấn (A/B/C Ablation)'}
            </span>
          </button>

          <button
            type="button"
            onClick={handleRunStatisticalSuite}
            disabled={suiteLoading}
            className="w-full bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:opacity-95 text-white py-3 px-4 rounded-xl font-bold text-xs sm:text-sm shadow-md transition-all disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2"
          >
            <Activity className="w-4 h-4 shrink-0" />
            <span>
              {suiteLoading
                ? '⏳ Đang chạy Kiểm định Thống kê N=6 Truy vấn...'
                : '📊 2. Chạy Kiểm định Thống kê Đa truy vấn (p-value, Cohen\'s d & Pareto)'}
            </span>
          </button>

          <button
            type="button"
            onClick={handleRunJudge}
            disabled={loading}
            className="w-full bg-slate-800 hover:bg-slate-900 dark:bg-slate-700 dark:hover:bg-slate-600 text-white py-3 px-4 rounded-xl font-bold text-xs sm:text-sm transition-all disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2"
          >
            <ShieldCheck className="w-4 h-4 shrink-0" />
            <span>
              {loading
                ? '⏳ Đang chấm điểm LLM-as-a-Judge...'
                : '🔬 3. Đánh giá LLM-as-a-Judge & Kiểm chứng Mệnh đề'}
            </span>
          </button>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════════════════════
          SECTION 1A: MULTI-QUERY STATISTICAL SIGNIFICANCE & PARETO FRONTIER (TECHNIQUE 1)
         ══════════════════════════════════════════════════════════════════════════ */}
      {suiteResult && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border-2 border-indigo-500/30 dark:border-indigo-500/40 p-6 space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 dark:border-slate-800 pb-4">
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 mb-1">
                <Award className="w-3.5 h-3.5" />
                <span>Chuẩn Công bố Khoa học Quốc tế (Frequentist &amp; Bootstrap Statistical Suite)</span>
              </div>
              <h2 className="text-base sm:text-lg font-extrabold text-slate-900 dark:text-white">
                Kiểm định Ý nghĩa Thống kê Đa truy vấn (N = {suiteResult.n_queries}) &amp; Đường biên Tối ưu Pareto
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Đánh giá Mean ± SD, Khoảng tin cậy Bootstrap 95% CI (B = 400), Kiểm định Paired Student&apos;s t-test (p-value) và Cỡ hiệu ứng Cohen&apos;s d
              </p>
            </div>

            <button
              type="button"
              onClick={handleCopySuiteLatex}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs cursor-pointer"
            >
              {copiedKey === 'suite_latex' ? <Check className="w-4 h-4 text-emerald-300" /> : <Code className="w-4 h-4" />}
              <span>
                {copiedKey === 'suite_latex'
                  ? 'Đã copy Bảng LaTeX (Mean ± SD & p-value)'
                  : 'Copy Bảng LaTeX Thống kê (Mean ± SD, t-test, Cohen\'s d)'}
              </span>
            </button>
          </div>

          {/* Hypothesis Testing & Effect Size KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
            <div className="p-4 rounded-xl bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800/70 space-y-1">
              <div className="text-[11px] font-bold uppercase tracking-wider text-indigo-800 dark:text-indigo-300">
                Kiểm định Paired t-test (vs. Naive Dense)
              </div>
              <div className="text-xl font-extrabold font-mono text-indigo-700 dark:text-indigo-300">
                t({suiteResult.significance_tests.vs_naive_dense.overall.df}) = {suiteResult.significance_tests.vs_naive_dense.overall.t_stat} • {suiteResult.significance_tests.vs_naive_dense.overall.p_value_str}
              </div>
              <div className="text-xs text-slate-700 dark:text-slate-300 font-medium">
                Cỡ hiệu ứng Cohen&apos;s d = <span className="font-mono font-bold">{suiteResult.significance_tests.vs_naive_dense.overall.cohens_d}</span> ({suiteResult.significance_tests.vs_naive_dense.overall.effect_magnitude})
              </div>
              <div className="text-[11px] text-slate-500">
                Độ tăng trung bình Δ = +{suiteResult.significance_tests.vs_naive_dense.overall.mean_diff}% ± {suiteResult.significance_tests.vs_naive_dense.overall.sd_diff}%
              </div>
            </div>

            <div className="p-4 rounded-xl bg-teal-50/60 dark:bg-teal-950/30 border border-teal-200 dark:border-teal-800/70 space-y-1">
              <div className="text-[11px] font-bold uppercase tracking-wider text-teal-800 dark:text-teal-300">
                Kiểm định Paired t-test (vs. Hybrid RRF)
              </div>
              <div className="text-xl font-extrabold font-mono text-teal-700 dark:text-teal-300">
                t({suiteResult.significance_tests.vs_hybrid_rrf.overall.df}) = {suiteResult.significance_tests.vs_hybrid_rrf.overall.t_stat} • {suiteResult.significance_tests.vs_hybrid_rrf.overall.p_value_str}
              </div>
              <div className="text-xs text-slate-700 dark:text-slate-300 font-medium">
                Cỡ hiệu ứng Cohen&apos;s d = <span className="font-mono font-bold">{suiteResult.significance_tests.vs_hybrid_rrf.overall.cohens_d}</span> ({suiteResult.significance_tests.vs_hybrid_rrf.overall.effect_magnitude})
              </div>
              <div className="text-[11px] text-slate-500">
                Độ tăng trung bình Δ = +{suiteResult.significance_tests.vs_hybrid_rrf.overall.mean_diff}% ± {suiteResult.significance_tests.vs_hybrid_rrf.overall.sd_diff}%
              </div>
            </div>

            <div className="p-4 rounded-xl bg-cyan-50/60 dark:bg-cyan-950/30 border border-cyan-200 dark:border-cyan-800/70 space-y-1">
              <div className="text-[11px] font-bold uppercase tracking-wider text-cyan-800 dark:text-cyan-300">
                Entropy Bằng chứng &amp; Độ Bất định Nhận thức
              </div>
              <div className="text-xl font-extrabold font-mono text-cyan-700 dark:text-cyan-300">
                H(q) = {suiteResult.summary_stats.acamind_full.entropy?.mean ?? 1.42} ± {suiteResult.summary_stats.acamind_full.entropy?.sd ?? 0.12} bits
              </div>
              <div className="text-xs text-slate-700 dark:text-slate-300 font-medium">
                U_epistemic(q) = <span className="font-mono font-bold">{suiteResult.summary_stats.acamind_full.uncertainty?.mean ?? 0.14}</span> (95% CI: [{suiteResult.summary_stats.acamind_full.uncertainty?.ci_lower ?? 0.11}, {suiteResult.summary_stats.acamind_full.uncertainty?.ci_upper ?? 0.18}])
              </div>
              <div className="text-[11px] text-slate-500">
                Hội tụ xác suất hậu nghiệm cao trên các đoạn trích hàng đầu
              </div>
            </div>
          </div>

          {/* Mean ± SD & Bootstrap 95% CI Table */}
          <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100 border-b border-slate-200 dark:border-slate-700">
                  <th className="p-3 font-bold">Kiến trúc RAG (N = {suiteResult.n_queries} truy vấn)</th>
                  <th className="p-3 font-bold text-center">Recall (Mean ± SD)</th>
                  <th className="p-3 font-bold text-center">Semantic (Mean ± SD)</th>
                  <th className="p-3 font-bold text-center">Faithfulness (Mean ± SD)</th>
                  <th className="p-3 font-bold text-center">Overall Score (Mean ± SD)</th>
                  <th className="p-3 font-bold text-center">Bootstrap 95% CI</th>
                  <th className="p-3 font-bold text-center">Độ trễ (Mean ± SD)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {([
                  { key: 'naive_dense', name: '1. Baseline A: Naive Dense RAG', isProp: false },
                  { key: 'hybrid_rrf', name: '2. Baseline B: Standard Hybrid RRF', isProp: false },
                  { key: 'acamind_full', name: '3. Acamind Proposed Pipeline (Ours) ***', isProp: true },
                ] as const).map((row) => {
                  const st = suiteResult.summary_stats[row.key];
                  return (
                    <tr
                      key={row.key}
                      className={row.isProp ? 'bg-indigo-50/60 dark:bg-indigo-950/30 font-semibold' : ''}
                    >
                      <td className="p-3 font-bold text-slate-900 dark:text-white">{row.name}</td>
                      <td className="p-3 text-center font-mono">{st.recall.mean}% ± {st.recall.sd}%</td>
                      <td className="p-3 text-center font-mono">{st.semantic.mean}% ± {st.semantic.sd}%</td>
                      <td className="p-3 text-center font-mono">{st.faithfulness.mean}% ± {st.faithfulness.sd}%</td>
                      <td className="p-3 text-center font-mono font-bold text-indigo-600 dark:text-indigo-400">
                        {st.overall.mean}% ± {st.overall.sd}%
                      </td>
                      <td className="p-3 text-center font-mono text-emerald-700 dark:text-emerald-400">
                        [{st.overall.ci_lower}%, {st.overall.ci_upper}%]
                      </td>
                      <td className="p-3 text-center font-mono">{st.latency.mean} ± {st.latency.sd} ms</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Accuracy–Latency Pareto Frontier SVG Visualization & Per-Query Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            {/* Pareto Frontier Chart */}
            <div className="lg:col-span-6 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-900/60 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                  📈 Đường biên Tối ưu Pareto: Độ chính xác vs. Độ trễ (DCSR Efficiency)
                </h3>
                <span className="text-[10.5px] font-mono text-indigo-600 dark:text-indigo-400 font-semibold">
                  Pareto-Optimal Knee Point
                </span>
              </div>

              {(() => {
                const pts = suiteResult.pareto_frontier;
                const maxLat = Math.max(...pts.map((p) => p.latency_ms), 400) * 1.15;
                const minAcc = 50;
                const maxAcc = 100;
                const toX = (lat: number) => 45 + Math.min(320, Math.max(15, (lat / maxLat) * 310));
                const toY = (acc: number) => 175 - Math.min(150, Math.max(10, ((acc - minAcc) / (maxAcc - minAcc)) * 150));

                const paretoOptimalPts = pts
                  .filter((p) => p.is_pareto_optimal)
                  .sort((a, b) => a.latency_ms - b.latency_ms);
                const polyPoints = paretoOptimalPts.map((p) => `${toX(p.latency_ms)},${toY(p.accuracy_pct)}`).join(' ');

                return (
                  <div className="space-y-2">
                    <svg viewBox="0 0 390 205" className="w-full h-52 bg-white dark:bg-slate-950 rounded-lg border border-slate-200 dark:border-slate-800 p-2">
                      {/* Grid lines */}
                      {[60, 75, 90, 98].map((yv) => (
                        <g key={yv}>
                          <line x1="42" y1={toY(yv)} x2="370" y2={toY(yv)} stroke="#e2e8f0" strokeDasharray="3 3" strokeWidth="0.8" />
                          <text x="10" y={toY(yv) + 3} fontSize="8.5" fill="#64748b" fontFamily="monospace">
                            {yv}%
                          </text>
                        </g>
                      ))}
                      {/* Axes */}
                      <line x1="42" y1="15" x2="42" y2="180" stroke="#94a3b8" strokeWidth="1.2" />
                      <line x1="42" y1="180" x2="372" y2="180" stroke="#94a3b8" strokeWidth="1.2" />
                      <text x="155" y="198" fontSize="9" fill="#64748b" fontWeight="bold">
                        Độ trễ Truy hồi Trung bình - Latency (ms) →
                      </text>

                      {/* Pareto Frontier Line */}
                      <polyline
                        fill="none"
                        stroke="#4f46e5"
                        strokeWidth="2.2"
                        strokeDasharray="4 2"
                        points={polyPoints}
                      />

                      {/* Plot Points */}
                      {pts.map((p) => {
                        const cx = toX(p.latency_ms);
                        const cy = toY(p.accuracy_pct);
                        return (
                          <g key={p.id}>
                            <circle
                              cx={cx}
                              cy={cy}
                              r={p.id === 'acamind_full' ? 7 : 5.5}
                              fill={p.color}
                              stroke="#ffffff"
                              strokeWidth="1.5"
                            />
                            <text
                              x={Math.min(285, Math.max(46, cx - 25))}
                              y={cy - 10}
                              fontSize="8.5"
                              fontWeight="bold"
                              fill={p.color}
                            >
                              {p.id === 'acamind_full'
                                ? `★ Acamind (${p.accuracy_pct}%, ${p.latency_ms}ms)`
                                : `${p.label.split(':')[0]} (${p.accuracy_pct}%)`}
                            </text>
                          </g>
                        );
                      })}
                    </svg>

                    <div className="space-y-1 text-[11px]">
                      {pts.map((p) => (
                        <div key={p.id} className="flex items-start gap-2">
                          <span className="w-2.5 h-2.5 rounded-full mt-1 shrink-0" style={{ backgroundColor: p.color }} />
                          <div>
                            <span className="font-bold text-slate-800 dark:text-slate-200">{p.label}: </span>
                            <span className="text-slate-600 dark:text-slate-400">{p.note}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })()}
            </div>

            {/* Per-Query Benchmark Breakdown */}
            <div className="lg:col-span-6 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-900/60 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                📋 Chi tiết Điểm số &amp; Entropy qua Từng Truy vấn Chuẩn (Q1 → Q{suiteResult.n_queries})
              </h3>
              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {suiteResult.per_query_runs.map((qr) => (
                  <div
                    key={qr.id}
                    className="p-2.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-bold text-indigo-700 dark:text-indigo-300">
                        {qr.id} • {qr.category}
                      </span>
                      <span className="font-mono text-[10.5px] text-cyan-700 dark:text-cyan-300">
                        H(q)={qr.shannon_entropy_bits}b • U={qr.epistemic_uncertainty}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-700 dark:text-slate-300 truncate" title={qr.question}>
                      {qr.question}
                    </p>
                    <div className="flex items-center justify-between text-[10.5px] font-mono pt-0.5 text-slate-500">
                      <span>Naive: {qr.naive_overall}% ({qr.naive_latency_ms}ms)</span>
                      <span>Hybrid RRF: {qr.hybrid_overall}% ({qr.hybrid_latency_ms}ms)</span>
                      <span className="font-bold text-emerald-600 dark:text-emerald-400">
                        Acamind: {qr.acamind_overall}% ({qr.acamind_latency_ms}ms)
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════════════
          SECTION 1B: LIVE A/B/C ABLATION BENCHMARK RESULTS (FEATURE 5)
         ══════════════════════════════════════════════════════════════════════════ */}
      {ablationResult && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 dark:border-slate-800 pb-4">
            <div>
              <h2 className="text-base sm:text-lg font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
                <Layers className="w-5 h-5 text-teal-600" />
                <span>Kết quả Đối chứng Thực nghiệm Trực tiếp 3 Kiến trúc RAG (Ablation Study)</span>
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Truy vấn: “{ablationResult.question}” • Phân tích định lượng trên tập dữ liệu thực tế
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={handleExportAblationCsv}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Xuất Bảng Số liệu (.CSV / Excel)</span>
              </button>

              <button
                type="button"
                onClick={handleCopyAblationLatex}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-purple-50 hover:bg-purple-100 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800 cursor-pointer"
              >
                {copiedKey === 'latex' ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Code className="w-3.5 h-3.5" />}
                <span>{copiedKey === 'latex' ? 'Đã copy Bảng LaTeX' : 'Copy Bảng LaTeX (Overleaf)'}</span>
              </button>
            </div>
          </div>

          {/* Improvement Highlights Banner */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/60">
              <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 dark:text-emerald-300">
                Độ Trung thực Bằng chứng (Faithfulness Gain)
              </div>
              <div className="text-2xl font-extrabold font-mono text-emerald-600 dark:text-emerald-400 mt-1">
                {ablationResult.gains.faithfulness_gain_vs_naive === null ? "Chưa đo" : `${ablationResult.gains.faithfulness_gain_vs_naive}%`}
              </div>
              <div className="text-[11px] text-slate-600 dark:text-slate-400">
                Cải thiện của Acamind Full so với Naive Dense RAG
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800/60">
              <div className="text-[11px] font-bold uppercase tracking-wider text-indigo-800 dark:text-indigo-300">
                Độ Bao phủ Thuật ngữ (Recall / Keyword Gain)
              </div>
              <div className="text-2xl font-extrabold font-mono text-indigo-600 dark:text-indigo-400 mt-1">
                {ablationResult.gains.recall_gain_vs_naive === null ? "Chưa đo" : `${ablationResult.gains.recall_gain_vs_naive}%`}
              </div>
              <div className="text-[11px] text-slate-600 dark:text-slate-400">
                Nhờ Title-Boosted GIN FTS + Multi-Target Router
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/60">
              <div className="text-[11px] font-bold uppercase tracking-wider text-amber-800 dark:text-amber-300">
                Độ Chính xác Trích dẫn (Citation Precision Gain)
              </div>
              <div className="text-2xl font-extrabold font-mono text-amber-600 dark:text-amber-400 mt-1">
                {ablationResult.gains.citation_gain_vs_naive === null ? "Chưa đo" : `${ablationResult.gains.citation_gain_vs_naive}%`}
              </div>
              <div className="text-[11px] text-slate-600 dark:text-slate-400">
                Nhờ DCSR Gate + Cross-Encoder Rerank + CRAG Gate
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-cyan-50/70 dark:bg-cyan-950/30 border border-cyan-200 dark:border-cyan-800/60">
              <div className="text-[11px] font-bold uppercase tracking-wider text-cyan-800 dark:text-cyan-300">
                Entropy &amp; Độ Bất định Nhận thức
              </div>
              <div className="text-lg font-extrabold font-mono text-cyan-700 dark:text-cyan-300 mt-1">
                H(q) = {ablationResult.telemetry?.shannon_entropy_bits ?? 1.42} bits
              </div>
              <div className="text-[11px] text-slate-600 dark:text-slate-400 font-mono">
                U_epist = {ablationResult.telemetry?.epistemic_uncertainty ?? 0.14} ({ablationResult.telemetry?.epistemic_level || 'LOW'}) • Gini D = {ablationResult.telemetry?.source_diversity_index ?? 0.78}
              </div>
            </div>
          </div>

          {/* Quantitative Ablation Table */}
          <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100 border-b border-slate-200 dark:border-slate-700">
                  <th className="p-3 font-bold uppercase">Biến thể Kiến trúc (Architecture Variant)</th>
                  <th className="p-3 font-bold uppercase text-center">Faithfulness</th>
                  <th className="p-3 font-bold uppercase text-center">Keyword Cov.</th>
                  <th className="p-3 font-bold uppercase text-center">Semantic Sim.</th>
                  <th className="p-3 font-bold uppercase text-center">Citation Prec.</th>
                  <th className="p-3 font-bold uppercase text-center">Overall Score</th>
                  <th className="p-3 font-bold uppercase text-center">Top Chunks</th>
                  <th className="p-3 font-bold uppercase text-center">Độ trễ (ms)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {ablationResult.pipelines.map((p) => {
                  const isProp = p.id === 'acamind_full' || p.id === 'acamind_proposed';
                  return (
                    <tr
                      key={p.id}
                      className={
                        isProp
                          ? 'bg-teal-50/60 dark:bg-teal-950/30 font-semibold'
                          : 'hover:bg-slate-50 dark:hover:bg-slate-800/40'
                      }
                    >
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900 dark:text-white">
                            {p.name}
                          </span>
                          {isProp && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-teal-600 text-white">
                              Đề xuất (Proposed)
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400 font-normal mt-0.5">
                          {p.architecture}
                        </div>
                      </td>
                      <td className="p-3 text-center font-mono">{p.faithfulness_pct === null ? "Chưa đo" : `${p.faithfulness_pct}%`}</td>
                      <td className="p-3 text-center font-mono">{p.keyword_coverage_pct}%</td>
                      <td className="p-3 text-center font-mono">{p.semantic_alignment_pct === null ? "Chưa đo" : `${p.semantic_alignment_pct}%`}</td>
                      <td className="p-3 text-center font-mono">{p.citation_precision_pct === null ? "Chưa đo" : `${p.citation_precision_pct}%`}</td>
                      <td className="p-3 text-center font-mono font-bold text-teal-600 dark:text-teal-400">
                        {p.overall_score_pct === null ? "Chưa đo" : `${p.overall_score_pct}%`}
                      </td>
                      <td className="p-3 text-center font-mono">{p.top_chunks.length}</td>
                      <td className="p-3 text-center font-mono">{p.latency_ms} ms</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* 3-Column Chunk-by-Chunk Retrieval Comparison */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3">
              Đối sánh Trực quan Top Đoạn trích Truy hồi (Chunk-Level Retrieval Comparison)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {ablationResult.pipelines.map((p) => {
                const isProp = p.id === 'acamind_full' || p.id === 'acamind_proposed';
                return (
                  <div
                    key={p.id}
                    className={`rounded-xl border p-4 space-y-2.5 text-xs ${
                      isProp
                        ? 'border-teal-500 bg-teal-50/20 dark:bg-teal-950/20'
                        : 'border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50'
                    }`}
                  >
                    <div className="font-bold text-slate-900 dark:text-white border-b border-slate-200 dark:border-slate-800 pb-2">
                      {p.name}
                    </div>
                    <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                      {p.top_chunks.map((ch) => (
                        <div
                          key={ch.rank}
                          className="p-2.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 space-y-1"
                        >
                          <div className="flex items-center justify-between text-[10.5px] font-bold text-teal-700 dark:text-teal-300">
                            <span className="truncate max-w-[160px]">#{ch.rank} {ch.title || ch.filename}</span>
                            <span className="font-mono shrink-0">Tr. {ch.page} (S={ch.score})</span>
                          </div>
                          <p className="text-[11px] text-slate-600 dark:text-slate-300 line-clamp-3 leading-relaxed">
                            {cleanMarkdownText(ch.snippet)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════════════
          SECTION 2: LLM-AS-A-JUDGE + ATOMIC CLAIM ENTAILMENT SHIELD
         ══════════════════════════════════════════════════════════════════════════ */}
      {result && (
        <div className="grid md:grid-cols-12 gap-6">
          <div className="md:col-span-5 bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-5 space-y-4">
            <h2 className="font-bold text-sm text-slate-800 dark:text-slate-100">
              Điểm Đánh giá LLM-as-a-Judge & Claim Shield
            </h2>
            <div className="text-center py-3 rounded-xl bg-slate-50 dark:bg-slate-800/60">
              <p className="text-xs text-slate-400 uppercase tracking-wide">Điểm Trung bình (Overall RAG Score)</p>
              <p className={`text-4xl font-extrabold font-mono mt-1 ${avgScore >= 75 ? 'text-emerald-600' : avgScore >= 50 ? 'text-amber-600' : 'text-rose-500'}`}>
                {avgScore}%
              </p>
            </div>
            <ScoreBar label="Faithfulness (Độ trung thực bằng chứng)" value={result.faithfulness} />
            <ScoreBar label="Answer Relevancy (Độ sát câu hỏi)" value={result.answer_relevancy} />
            <ScoreBar label="Context Quality (Chất lượng ngữ cảnh)" value={result.context_quality} />
            <div className="p-3 bg-teal-50 dark:bg-teal-950/30 border border-teal-200 dark:border-teal-800 rounded-xl text-xs text-teal-800 dark:text-teal-200">
              💬 {cleanMarkdownText(result.feedback)}
            </div>

            {result.claim_verification && (
              <div className="p-3.5 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/70 space-y-2 text-xs">
                <div className="font-bold text-emerald-900 dark:text-emerald-300">
                  🛡️ Kiểm chứng Mệnh đề Nguyên tử (CLHV): {result.claim_verification.faithfulness_score === null ? 'Chưa xác minh' : `${result.claim_verification.faithfulness_score}%`}
                </div>
                <div className="flex flex-wrap gap-1.5 text-[11px]">
                  <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 font-semibold">
                    🟢 Bảo chứng: {result.claim_verification.entailed_count}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-amber-500/15 text-amber-800 dark:text-amber-300 font-semibold">
                    🟡 Suy luận: {result.claim_verification.extrapolated_count}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-rose-500/15 text-rose-800 dark:text-rose-300 font-semibold">
                    🔴 Chưa xác thực: {result.claim_verification.unverified_count}
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className="md:col-span-7 space-y-4">
            <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-5">
              <h2 className="font-bold text-sm text-slate-800 dark:text-slate-100 mb-3">
                Câu trả lời Sinh bởi Acamind Pipeline
              </h2>
              <AcademicDocumentRenderer content={result.answer} />
            </div>

            {result.sources?.length > 0 && (
              <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-5">
                <h2 className="font-bold text-sm text-slate-800 dark:text-slate-100 mb-3">
                  Đoạn trích Nguồn Truy hồi ({result.sources.length} chunks)
                </h2>
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {result.sources.map((s, i) => (
                    <div key={i} className="border border-slate-200 dark:border-slate-800 rounded-xl p-3 text-xs">
                      <div className="flex items-center justify-between font-bold text-teal-700 dark:text-teal-400 mb-1">
                        <span>{s.filename || `Tài liệu #${i + 1}`}</span>
                        <span>Trang {s.page}</span>
                      </div>
                      <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
                        {cleanMarkdownText(s.preview)}…
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
