'use client';

import React, { useEffect, useState } from 'react';
import {
  FileText, Loader2, Microscope, Search, Sparkles, Table,
  Download, Copy, Check, Code, Award, BookOpen, ShieldCheck, Activity, Scale, Eye,
} from 'lucide-react';
import {
  generateLiteratureReview, getDocuments, decodeBase64Utf8Json,
  analyzeContradictionRadar, verifyAtomicClaims,
  type DocumentInfo, type LiteratureMatrixRow,
  type CebmContradictionRadar, type ClaimVerificationResult,
} from '@/lib/api';
import { useAppStore } from '@/store/useAppStore';
import { NeuralBadge } from '@/components/ui/NeuralBadge';
import { NeuralCard } from '@/components/ui/NeuralCard';
import { SideBySidePdfViewer } from '@/components/ui/SideBySidePdfViewer';
import { AcademicDocumentRenderer, cleanMarkdownText } from '@/components/ui/AcademicDocumentRenderer';

export default function LiteraturePage() {
  const { token } = useAppStore();
  const [topic, setTopic] = useState('');
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [loadingDocuments, setLoadingDocuments] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  const [matrixRows, setMatrixRows] = useState<LiteratureMatrixRow[]>([]);
  const [radarResult, setRadarResult] = useState<CebmContradictionRadar | null>(null);
  const [radarLoading, setRadarLoading] = useState(false);
  const [claimResult, setClaimResult] = useState<ClaimVerificationResult | null>(null);
  const [claimLoading, setClaimLoading] = useState(false);
  const [error, setError] = useState('');

  const [copiedMode, setCopiedMode] = useState<'md' | 'latex' | 'apa_all' | string | null>(null);
  const [activePdfViewer, setActivePdfViewer] = useState<{
    documentId: string;
    filename: string;
    title?: string;
    page: number;
    totalPages?: number | null;
    snippet?: string;
  } | null>(null);

  useEffect(() => {
    getDocuments()
      .then((items) => setDocuments(items.filter((item) => item.status === 'ready')))
      .catch(() => setError('Không thể tải thư viện tài liệu. Kiểm tra backend rồi thử lại.'))
      .finally(() => setLoadingDocuments(false));
  }, []);

  const toggleDocument = (id: string) =>
    setSelectedIds((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id].slice(0, 10)
    );

  const handleOpenPdfVerify = (docId: string, filename: string, page: number, snippet?: string, title?: string) => {
    const matched = documents.find(
      (d) =>
        d.id === docId ||
        d.filename.toLowerCase() === filename.toLowerCase() ||
        (d.title && d.title.toLowerCase() === filename.toLowerCase())
    );
    setActivePdfViewer({
      documentId: matched?.id || docId,
      filename: matched?.filename || filename,
      title: matched?.title || title || filename,
      page: Math.max(1, page || 1),
      totalPages: matched?.total_pages,
      snippet: snippet,
    });
  };

  const handleGenerate = async () => {
    if (!topic.trim() || selectedIds.length === 0 || loading) return;
    setLoading(true);
    setError('');
    setResult('');
    setMatrixRows([]);
    setRadarResult(null);
    setClaimResult(null);
    try {
      const response = await generateLiteratureReview(selectedIds, topic.trim());
      if (!response.ok) {
        let message = 'Không thể tạo Literature Review. Vui lòng thử lại.';
        try {
          message = (await response.json()).detail || message;
        } catch {
          /* non-JSON error */
        }
        throw new Error(message);
      }

      // Đọc Ma trận Bằng chứng 4 Thuộc tính từ HTTP Header X-Literature-Matrix
      const matrixB64 = response.headers.get('X-Literature-Matrix');
      const decodedMatrix = decodeBase64Utf8Json<LiteratureMatrixRow[]>(matrixB64);
      if (decodedMatrix && Array.isArray(decodedMatrix)) {
        setMatrixRows(decodedMatrix);
      }

      // Đọc Radar Đồng thuận & Mâu thuẫn Học thuật Trọng số CEBM từ HTTP Header X-Literature-Radar
      const radarB64 = response.headers.get('X-Literature-Radar');
      const decodedRadar = decodeBase64Utf8Json<CebmContradictionRadar>(radarB64);
      if (decodedRadar && typeof decodedRadar.cebm_weighted_consensus_pct === 'number') {
        setRadarResult(decodedRadar);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('Backend không trả về nội dung để hiển thị.');
      const decoder = new TextDecoder();
      let fullText = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        fullText += decoder.decode(value, { stream: true });
        setResult(fullText);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không thể tạo Literature Review.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunRadarManual = async () => {
    if (selectedIds.length === 0 || radarLoading) return;
    setRadarLoading(true);
    try {
      const res = await analyzeContradictionRadar(
        selectedIds,
        topic.trim() || 'Tổng hợp bằng chứng lâm sàng'
      );
      setRadarResult(res.radar);
      if (res.matrix_rows && res.matrix_rows.length > 0 && matrixRows.length === 0) {
        setMatrixRows(res.matrix_rows);
      }
    } catch (e) {
      console.error('Radar analysis error:', e);
    } finally {
      setRadarLoading(false);
    }
  };

  const handleVerifyReviewClaims = async () => {
    if (!result || claimLoading) return;
    setClaimLoading(true);
    try {
      const res = await verifyAtomicClaims(
        topic.trim(),
        result,
        selectedIds
      );
      setClaimResult(res);
    } catch (e) {
      console.error('Claim verification error:', e);
    } finally {
      setClaimLoading(false);
    }
  };

  // ── Export Helpers (CSV / Excel, Markdown, LaTeX, APA 7th) ──

  const triggerCopyFeedback = (key: string) => {
    setCopiedMode(key);
    setTimeout(() => setCopiedMode(null), 2000);
  };

  const handleExportCsv = () => {
    if (!matrixRows.length) return;
    const esc = (v: string | number) => `"${String(v ?? '').replace(/"/g, '""')}"`;
    const headers = [
      'Document Title',
      'Authors',
      'Year',
      'CEBM Evidence Level',
      'Study Design',
      'Methodology / Intervention',
      'Psychometric Scale / Metric',
      'Key Finding / Effect Size',
      'Page Citation',
      'APA 7th Citation',
    ];
    const rows = matrixRows.map((r) => [
      esc(r.title),
      esc(r.authors),
      esc(r.year),
      esc(r.cebm_label),
      esc(r.study_design),
      esc(r.methodology),
      esc(r.scale_or_metric),
      esc(r.finding),
      esc(r.page_citation),
      esc(r.apa7),
    ]);
    const csvContent = '\uFEFF' + [headers.map(esc).join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Acamind_Evidence_Matrix_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleCopyMarkdownMatrix = () => {
    if (!matrixRows.length) return;
    const cleanCell = (s: string) => (s || '').replace(/\|/g, '\\|').replace(/\n+/g, ' ').trim();
    const lines = [
      '| Nghiên cứu & Cấp độ CEBM | Phương pháp & Can thiệp (Methodology) | Thang đo / Chỉ số (Scale & Metric) | Phát hiện Chính & Cỡ Hiệu ứng (Key Finding) | Trích dẫn Trang |',
      '|---|---|---|---|---|',
      ...matrixRows.map(
        (r) =>
          `| **${cleanCell(r.title)}** (${cleanCell(r.authors)}, ${r.year}) — *${cleanCell(r.cebm_label)}* | ${cleanCell(
            r.methodology
          )} | ${cleanCell(r.scale_or_metric)} | ${cleanCell(r.finding)} | \`${cleanCell(r.page_citation)}\` |`
      ),
    ];
    navigator.clipboard.writeText(lines.join('\n'));
    triggerCopyFeedback('md');
  };

  const handleCopyLatexMatrix = () => {
    if (!matrixRows.length) return;
    const escTex = (s: string) =>
      (s || '')
        .replace(/\\/g, '\\textbackslash{}')
        .replace(/([&%$#_{}])/g, '\\$1')
        .replace(/~/g, '\\textasciitilde{}')
        .replace(/\^/g, '\\textasciicircum{}')
        .replace(/\n+/g, ' ')
        .trim();

    const bodyLines = matrixRows.map(
      (r) =>
        `${escTex(r.title)} (${escTex(r.authors)}, ${r.year}) [${escTex(r.cebm_level)}] & ${escTex(
          r.methodology
        )} & ${escTex(r.scale_or_metric)} & ${escTex(r.finding)} & \\texttt{${escTex(r.page_citation)}} \\\\ \\hline`
    );

    const latex = [
      '\\begin{table*}[htbp]',
      '\\centering',
      '\\caption{Structured 4-Attribute Clinical Evidence Matrix Generated by Acamind}',
      '\\label{tab:acamind_evidence_matrix}',
      '\\renewcommand{\\arraystretch}{1.25}',
      '\\begin{tabular}{|p{3.2cm}|p{3.8cm}|p{3.2cm}|p{4.0cm}|p{2.2cm}|}',
      '\\hline',
      '\\textbf{Study \\& CEBM Level} & \\textbf{Methodology / Intervention} & \\textbf{Scale / Metric} & \\textbf{Key Finding / Effect Size} & \\textbf{Page Citation} \\\\ \\hline',
      ...bodyLines,
      '\\end{tabular}',
      '\\end{table*}',
    ].join('\n');

    navigator.clipboard.writeText(latex);
    triggerCopyFeedback('latex');
  };

  const handleCopyAllApa = () => {
    if (!matrixRows.length) return;
    const allApa = matrixRows.map((r, idx) => `${idx + 1}. ${r.apa7}`).join('\n\n');
    navigator.clipboard.writeText(allApa);
    triggerCopyFeedback('apa_all');
  };

  // Render narrative review with interactive Click-to-Verify citation buttons
  const renderReviewWithInteractiveCitations = (rawText: string) => {
    const parts: React.ReactNode[] = [];
    const regex = /\[([^\]]+?)\s*[-–—,:]\s*(?:Page|Trang|tr\.?|p\.?|pp\.?)\s*(\d+)\]/gi;
    let lastIdx = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(rawText)) !== null) {
      if (match.index > lastIdx) {
        parts.push(<span key={`txt-${lastIdx}`}>{rawText.slice(lastIdx, match.index)}</span>);
      }
      const fname = match[1].trim();
      const pageNum = parseInt(match[2], 10);
      const beforeText = rawText.slice(Math.max(0, match.index - 220), match.index);
      const sents = beforeText.replace(/\[[^\]]+\]/g, '').split(/(?<=[.!?\n])\s+/);
      const snippet = (sents[sents.length - 1] || fname).trim();
      const matchedRow = matrixRows.find(
        (r) =>
          r.filename.toLowerCase() === fname.toLowerCase() ||
          r.title.toLowerCase().includes(fname.toLowerCase())
      );

      parts.push(
        <button
          key={`cite-${match.index}`}
          type="button"
          onClick={() =>
            handleOpenPdfVerify(
              matchedRow?.document_id || '',
              matchedRow?.filename || fname,
              pageNum,
              snippet,
              matchedRow?.title || fname
            )
          }
          className="inline-flex items-center gap-1 px-2 py-0.5 mx-1 my-0.5 rounded-md text-xs font-semibold bg-teal-50 hover:bg-teal-100 dark:bg-teal-950/70 dark:hover:bg-teal-900 text-teal-700 dark:text-teal-300 border border-teal-300 dark:border-teal-700 transition-all hover:scale-105 cursor-pointer"
          title={`Nhấn để mở đối chiếu PDF "${fname}" tại Trang ${pageNum} (Tự động bôi vàng bằng chứng)`}
        >
          <FileText className="h-3 w-3 shrink-0" />
          <span className="truncate max-w-[160px]">{fname}</span>
          <span className="rounded bg-teal-200/80 dark:bg-teal-800 px-1 text-[10px] font-mono font-bold">
            Tr. {pageNum}
          </span>
        </button>
      );
      lastIdx = regex.lastIndex;
    }

    if (lastIdx < rawText.length) {
      parts.push(<span key={`txt-end`}>{rawText.slice(lastIdx)}</span>);
    }
    return parts;
  };

  return (
    <div className="flex min-h-screen bg-gray-50 dark:bg-surface-base transition-colors duration-300">
      <div className={`flex-1 min-w-0 transition-all duration-300 ${activePdfViewer ? 'hidden lg:block lg:w-1/2' : 'w-full'}`}>
        <div className="border-b border-gray-200/50 bg-gradient-to-br from-violet-500/5 via-purple-500/5 to-pink-500/5 dark:border-gray-800/50 dark:from-violet-900/20 dark:via-purple-900/20 dark:to-pink-900/20">
          <div className="container mx-auto max-w-6xl px-6 py-8">
            <div className="mb-3 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-purple-500 shadow-lg shadow-violet-500/20">
                <Microscope className="h-6 w-6 text-white" />
              </div>
              <NeuralBadge variant="cortex" dot pulse>
                Structured Evidence Synthesis
              </NeuralBadge>
            </div>
            <h1 className="mb-2 text-3xl font-extrabold text-gray-900 dark:text-white md:text-4xl">
              Literature Review & 4-Attribute Clinical Matrix
            </h1>
            <p className="max-w-3xl text-sm md:text-base text-gray-600 dark:text-gray-400">
              Bóc tách Ma trận Bằng chứng 4 Thuộc tính (Methodology, Psychometric Scale/Metric, Key Finding/Effect Size, Page Citation), phân tầng Oxford CEBM và tổng hợp học thuật có kiểm chứng từ các tài liệu PDF.
            </p>
          </div>
        </div>

        <div className="container mx-auto max-w-6xl space-y-6 px-6 py-8">
          <NeuralCard variant="elevated" padding="lg">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Search className="h-5 w-5 text-violet-500" />
                <h2 className="font-bold text-gray-900 dark:text-white">Chủ đề / Câu hỏi nghiên cứu</h2>
              </div>
              <input
                value={topic}
                onChange={(event) => setTopic(event.target.value)}
                placeholder="Ví dụ: Hiệu quả của CBT và thang đo BDI-II / PHQ-9 trong can thiệp trầm cảm"
                className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-violet-500/50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
              />
              <div>
                <p className="mb-2 text-sm font-semibold text-gray-800 dark:text-gray-100">
                  Chọn tài liệu đối sánh ({selectedIds.length}/10)
                </p>
                {loadingDocuments ? (
                  <p className="text-sm text-gray-500">Đang tải thư viện…</p>
                ) : documents.length === 0 ? (
                  <p className="text-sm text-amber-600">Chưa có tài liệu sẵn sàng để phân tích.</p>
                ) : (
                  <div className="max-h-60 space-y-1.5 overflow-y-auto rounded-xl border border-gray-200 p-3 dark:border-gray-700">
                    {documents.map((document) => (
                      <label
                        key={document.id}
                        className="flex cursor-pointer items-start gap-3 rounded-lg p-2 hover:bg-violet-50 dark:hover:bg-violet-950/30 transition-colors"
                      >
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(document.id)}
                          onChange={() => toggleDocument(document.id)}
                          className="mt-1"
                        />
                        <div className="min-w-0 flex-1">
                          <span className="text-sm font-medium text-gray-800 dark:text-gray-200 block truncate">
                            {document.title || document.filename}
                          </span>
                          <span className="text-xs text-gray-400">
                            {document.authors ? `${document.authors} • ` : ''}
                            {document.year ? `${document.year} • ` : ''}
                            {document.filename}
                          </span>
                        </div>
                      </label>
                    ))}
                  </div>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <button
                  onClick={handleGenerate}
                  disabled={!topic.trim() || selectedIds.length === 0 || loading}
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-violet-500 to-purple-500 py-3 px-4 font-semibold text-white shadow-md shadow-violet-500/20 hover:opacity-95 disabled:opacity-50 cursor-pointer text-sm"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      Đang bóc tách Ma trận 4 Thuộc tính & Tổng hợp…
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-5 w-5" />
                      Tạo Ma trận Bằng chứng & Literature Review
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={handleRunRadarManual}
                  disabled={selectedIds.length === 0 || radarLoading}
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 py-3 px-4 font-semibold text-white shadow-md shadow-amber-500/20 hover:opacity-95 disabled:opacity-50 cursor-pointer text-sm"
                >
                  {radarLoading ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      Đang tính toán Radar Trọng số CEBM…
                    </>
                  ) : (
                    <>
                      <Scale className="h-5 w-5" />
                      Chạy Radar Phát hiện Mâu thuẫn & Đồng thuận CEBM
                    </>
                  )}
                </button>
              </div>
              {error && (
                <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300">
                  {error}
                </p>
              )}
            </div>
          </NeuralCard>

          {/* ── Feature 2: CEBM-Weighted Contradiction & Consensus Radar ── */}
          {radarResult && (
            <NeuralCard variant="elevated" padding="lg">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 dark:border-gray-800 pb-4">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/15 text-amber-600 dark:text-amber-400">
                    <Scale className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-gray-900 dark:text-white flex items-center gap-2">
                      Radar Phát hiện Mâu thuẫn & Đồng thuận Học thuật Trọng số Oxford CEBM
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {radarResult.formula}
                    </p>
                  </div>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-bold border ${
                    radarResult.cebm_weighted_consensus_pct >= 70
                      ? 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border-emerald-500/30'
                      : radarResult.cebm_weighted_consensus_pct >= 45
                      ? 'bg-amber-500/15 text-amber-800 dark:text-amber-300 border-amber-500/30'
                      : 'bg-rose-500/15 text-rose-800 dark:text-rose-300 border-rose-500/30'
                  }`}
                >
                  {radarResult.cebm_weighted_consensus_pct >= 70
                    ? 'Đồng thuận Cao (High CEBM Consensus)'
                    : radarResult.cebm_weighted_consensus_pct >= 45
                    ? 'Phân kỳ Có Điều kiện (Moderate Divergence)'
                    : 'Mâu thuẫn Học thuật Đáng kể (High Divergence)'}
                </span>
              </div>

              {/* KPI Metrics & Stacked CEBM Bar */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/70 border border-slate-200 dark:border-slate-800">
                  <div className="text-xs text-gray-500 dark:text-gray-400">Chỉ số Đồng thuận Trọng số (Consensus Index)</div>
                  <div className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400 font-mono mt-1">
                    {radarResult.cebm_weighted_consensus_pct}%
                  </div>
                  {radarResult.dominant_study && (
                    <div className="text-[11px] text-gray-500 mt-0.5 truncate" title={radarResult.dominant_study.title}>
                      Trụ cột: {cleanMarkdownText(radarResult.dominant_study.title)} ({radarResult.dominant_study.cebm_label}, w={radarResult.dominant_study.cebm_weight})
                    </div>
                  )}
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/70 border border-slate-200 dark:border-slate-800">
                  <div className="text-xs text-gray-500 dark:text-gray-400">Chỉ số Phân kỳ / Đối nghịch (Divergence Index)</div>
                  <div className="text-2xl font-extrabold text-amber-600 dark:text-amber-400 font-mono mt-1">
                    {radarResult.divergence_index_pct}%
                  </div>
                  <div className="text-[11px] text-gray-500 mt-0.5">
                    Phát hiện {radarResult.contradictions.length} cặp đối sánh phương pháp luận
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/70 border border-slate-200 dark:border-slate-800 flex flex-col justify-center">
                  <div className="flex justify-between text-[11px] font-semibold mb-1.5">
                    <span className="text-emerald-600 dark:text-emerald-400">Đồng thuận: {radarResult.cebm_weighted_consensus_pct}%</span>
                    <span className="text-amber-600 dark:text-amber-400">Phân kỳ: {radarResult.divergence_index_pct}%</span>
                  </div>
                  <div className="w-full h-3 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-800 flex">
                    <div
                      style={{ width: `${radarResult.cebm_weighted_consensus_pct}%` }}
                      className="bg-emerald-500 h-full transition-all"
                    />
                    <div
                      style={{ width: `${radarResult.divergence_index_pct}%` }}
                      className="bg-amber-500 h-full transition-all"
                    />
                  </div>
                  <div className="text-[10.5px] text-gray-400 mt-1">
                    Thanh phân bổ tỷ trọng bằng chứng theo cấp độ Oxford CEBM
                  </div>
                </div>
              </div>

              {/* Consensus Points */}
              {radarResult.consensus_points && radarResult.consensus_points.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 mb-4">
                  {radarResult.consensus_points.map((cp, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl border border-emerald-200/80 dark:border-emerald-800/60 bg-emerald-50/40 dark:bg-emerald-950/20 text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-bold text-emerald-900 dark:text-emerald-300">
                          ✓ {cleanMarkdownText(cp.aspect)}
                        </span>
                        <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 font-mono font-bold text-[10.5px]">
                          Ủng hộ: {cp.weighted_support}%
                        </span>
                      </div>
                      <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                        {cleanMarkdownText(cp.statement)}
                      </p>
                      <div className="text-[10.5px] text-gray-500 dark:text-gray-400">
                        Nguồn: {cp.citations.join(' • ')}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Pairwise Contradictions / Methodological Divergence Cards */}
              {radarResult.contradictions && radarResult.contradictions.length > 0 && (
                <div className="space-y-2.5 mb-4">
                  <div className="text-xs font-bold uppercase tracking-wider text-amber-800 dark:text-amber-300">
                    ⚡ Ma trận Đối kháng &amp; Phân kỳ Phương pháp luận Giữa các Nghiên cứu
                  </div>
                  {radarResult.contradictions.map((c) => (
                    <div
                      key={c.id}
                      className="p-3.5 rounded-xl border border-amber-200 dark:border-amber-800/70 bg-white dark:bg-slate-900/70 text-xs space-y-2"
                    >
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <span className="font-bold text-slate-900 dark:text-white">
                          Chiều đối sánh: {cleanMarkdownText(c.dimension)}
                        </span>
                        <span className="px-2 py-0.5 rounded bg-amber-500/15 text-amber-800 dark:text-amber-300 font-mono font-bold text-[10.5px]">
                          Δw_CEBM = {c.weight_delta}
                        </span>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700 space-y-1">
                          <div className="flex items-center justify-between gap-1 font-bold text-teal-700 dark:text-teal-300">
                            <span className="truncate">{cleanMarkdownText(c.study_a.title)} ({c.study_a.year})</span>
                            <span className="font-mono text-[10px] shrink-0">{c.study_a.cebm_level} (w={c.study_a.cebm_weight})</span>
                          </div>
                          <p className="text-[11px] text-gray-700 dark:text-gray-300">{cleanMarkdownText(c.study_a.position)}</p>
                        </div>
                        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700 space-y-1">
                          <div className="flex items-center justify-between gap-1 font-bold text-purple-700 dark:text-purple-300">
                            <span className="truncate">{cleanMarkdownText(c.study_b.title)} ({c.study_b.year})</span>
                            <span className="font-mono text-[10px] shrink-0">{c.study_b.cebm_level} (w={c.study_b.cebm_weight})</span>
                          </div>
                          <p className="text-[11px] text-gray-700 dark:text-gray-300">{cleanMarkdownText(c.study_b.position)}</p>
                        </div>
                      </div>
                      <div className="text-[11px] text-amber-800 dark:text-amber-200 bg-amber-50/70 dark:bg-amber-950/30 px-2.5 py-1.5 rounded-lg">
                        <strong>Nguyên nhân gốc rễ:</strong> {cleanMarkdownText(c.root_cause)} • <strong>Phán quyết CEBM:</strong> {cleanMarkdownText(c.cebm_verdict)}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Methodological Summary */}
              <div className="p-3.5 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-200/80 dark:border-emerald-800/60 space-y-1 text-xs">
                <div className="font-bold text-emerald-900 dark:text-emerald-300 uppercase tracking-wider text-[11px]">
                  ⚖️ Tổng kết Phương pháp luận &amp; Khuyến nghị Trọng số Bằng chứng (CEBM Synthesis)
                </div>
                <p className="text-gray-800 dark:text-gray-200 leading-relaxed">
                  {cleanMarkdownText(radarResult.methodological_summary)}
                </p>
              </div>
            </NeuralCard>
          )}

          {/* ── 4-Attribute Clinical Evidence Matrix (Proposal 2, 3, 5) ── */}
          {matrixRows.length > 0 && (
            <NeuralCard variant="elevated" padding="lg">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 dark:border-gray-800 pb-4">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-500/15 text-teal-600 dark:text-teal-400">
                    <Table className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-gray-900 dark:text-white flex items-center gap-2">
                      Ma trận Bằng chứng Thực nghiệm 4 Thuộc tính ({matrixRows.length} nghiên cứu)
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Structure-Aware Disjoint Slot Extraction • Bấm vào nhãn trang để mở PDF đối chiếu & tự động tô sáng bằng chứng
                    </p>
                  </div>
                </div>

                {/* 1-Click Export Toolbar */}
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={handleExportCsv}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-950/60 dark:hover:bg-emerald-900/80 px-3 py-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 transition-colors cursor-pointer"
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span>Xuất Excel (.csv)</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleCopyMarkdownMatrix}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 transition-colors cursor-pointer"
                  >
                    {copiedMode === 'md' ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                    <span>{copiedMode === 'md' ? 'Đã copy Markdown' : 'Copy Bảng Markdown'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleCopyLatexMatrix}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-purple-50 hover:bg-purple-100 dark:bg-purple-950/60 dark:hover:bg-purple-900/80 px-3 py-1.5 text-xs font-semibold text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800 transition-colors cursor-pointer"
                  >
                    {copiedMode === 'latex' ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Code className="h-3.5 w-3.5" />}
                    <span>{copiedMode === 'latex' ? 'Đã copy LaTeX' : 'Copy LaTeX (Overleaf)'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleCopyAllApa}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/60 dark:hover:bg-blue-900/80 px-3 py-1.5 text-xs font-semibold text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 transition-colors cursor-pointer"
                  >
                    {copiedMode === 'apa_all' ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <BookOpen className="h-3.5 w-3.5" />}
                    <span>{copiedMode === 'apa_all' ? 'Đã copy APA 7th' : 'Copy Tất cả APA 7th'}</span>
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-100 dark:bg-slate-800/90 text-slate-800 dark:text-slate-100 border-b border-gray-200 dark:border-gray-700">
                      <th className="p-3 font-bold uppercase tracking-wider w-[22%]">
                        Nghiên cứu & Cấp độ Bằng chứng
                      </th>
                      <th className="p-3 font-bold uppercase tracking-wider w-[23%]">
                        1. Phương pháp & Can thiệp (Methodology)
                      </th>
                      <th className="p-3 font-bold uppercase tracking-wider w-[20%]">
                        2. Thang đo / Chỉ số (Scale & Metric)
                      </th>
                      <th className="p-3 font-bold uppercase tracking-wider w-[23%]">
                        3. Phát hiện Chính & Cỡ Hiệu ứng (Key Finding)
                      </th>
                      <th className="p-3 font-bold uppercase tracking-wider w-[12%]">
                        4. Trích dẫn Trang
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                    {matrixRows.map((row, idx) => {
                      const isTier1 = row.authority_tier === 'tier_1' || row.cebm_level.startsWith('1');
                      const isTier2 = row.authority_tier === 'tier_2' || row.cebm_level.startsWith('2');
                      const badgeCls = isTier1
                        ? 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border-emerald-500/30'
                        : isTier2
                        ? 'bg-blue-500/15 text-blue-800 dark:text-blue-300 border-blue-500/30'
                        : 'bg-violet-500/15 text-violet-800 dark:text-violet-300 border-violet-500/30';

                      return (
                        <tr
                          key={`${row.document_id}-${idx}`}
                          className="hover:bg-violet-50/40 dark:hover:bg-violet-950/20 transition-colors align-top"
                        >
                          <td className="p-3 space-y-1.5">
                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold border ${badgeCls}`}>
                              <Award className="h-3 w-3 shrink-0" />
                              {row.cebm_label}
                            </span>
                            <div className="font-bold text-gray-900 dark:text-white leading-snug">
                              {row.title}
                            </div>
                            <div className="text-[11px] text-gray-500 dark:text-gray-400">
                              {row.authors} ({row.year})
                            </div>
                            <div className="flex flex-wrap gap-1 pt-1">
                              <button
                                type="button"
                                onClick={() => {
                                  navigator.clipboard.writeText(row.apa7);
                                  triggerCopyFeedback(`apa-${row.document_id}`);
                                }}
                                className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 cursor-pointer"
                              >
                                {copiedMode === `apa-${row.document_id}` ? (
                                  <Check className="h-2.5 w-2.5 text-emerald-500" />
                                ) : (
                                  <Copy className="h-2.5 w-2.5" />
                                )}
                                <span>APA 7th</span>
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  navigator.clipboard.writeText(row.bibtex);
                                  triggerCopyFeedback(`bib-${row.document_id}`);
                                }}
                                className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 cursor-pointer"
                              >
                                {copiedMode === `bib-${row.document_id}` ? (
                                  <Check className="h-2.5 w-2.5 text-emerald-500" />
                                ) : (
                                  <Code className="h-2.5 w-2.5" />
                                )}
                                <span>.bib</span>
                              </button>
                            </div>
                          </td>

                          <td className="p-3 text-gray-700 dark:text-gray-200 leading-relaxed">
                            {cleanMarkdownText(row.methodology)}
                          </td>

                          <td className="p-3 text-gray-700 dark:text-gray-200 leading-relaxed">
                            {cleanMarkdownText(row.scale_or_metric)}
                          </td>

                          <td className="p-3 text-gray-800 dark:text-gray-100 font-medium leading-relaxed">
                            {cleanMarkdownText(row.finding)}
                          </td>

                          <td className="p-3">
                            <button
                              type="button"
                              onClick={() =>
                                handleOpenPdfVerify(
                                  row.document_id,
                                  row.filename,
                                  row.primary_page,
                                  row.finding || row.methodology,
                                  row.title
                                )
                              }
                              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-bold bg-teal-50 hover:bg-teal-100 dark:bg-teal-950/70 dark:hover:bg-teal-900 text-teal-700 dark:text-teal-300 border border-teal-300 dark:border-teal-700 transition-all hover:scale-105 cursor-pointer shadow-2xs"
                              title={`Mở PDF "${row.filename}" tại Trang ${row.primary_page} và tự động bôi vàng bằng chứng`}
                            >
                              <FileText className="h-3.5 w-3.5 shrink-0" />
                              <span>Trang {row.primary_page}</span>
                            </button>
                            {row.supporting_pages && row.supporting_pages.length > 1 && (
                              <div className="mt-1.5 flex flex-wrap gap-1">
                                {row.supporting_pages
                                  .filter((p) => p !== row.primary_page)
                                  .map((p) => (
                                    <button
                                      key={p}
                                      type="button"
                                      onClick={() =>
                                        handleOpenPdfVerify(
                                          row.document_id,
                                          row.filename,
                                          p,
                                          row.scale_or_metric || row.methodology,
                                          row.title
                                        )
                                      }
                                      className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-gray-100 hover:bg-teal-50 dark:bg-gray-800 dark:hover:bg-teal-950 text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 cursor-pointer"
                                    >
                                      Tr. {p}
                                    </button>
                                  ))}
                              </div>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </NeuralCard>
          )}

          {/* ── Narrative Synthesis Result + Feature 1 Claim-Level Entailment Shield ── */}
          {result && (
            <NeuralCard variant="elevated" padding="lg">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-gray-200 dark:border-gray-800 pb-3">
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-violet-500" />
                  <h3 className="font-bold text-gray-900 dark:text-white">
                    Tổng hợp Học thuật Chuyên sâu (Có gắn nhãn kiểm chứng PDF)
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={handleVerifyReviewClaims}
                  disabled={claimLoading}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-950/60 dark:hover:bg-emerald-900 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 transition-colors cursor-pointer"
                >
                  <ShieldCheck className="h-4 w-4" />
                  <span>{claimLoading ? 'Đang kiểm chứng mệnh đề...' : 'Kiểm chứng Chống Ảo giác X-Ray (CLHV)'}</span>
                </button>
              </div>

              {claimResult && (
                <div className="mb-5 p-4 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/70 space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-bold text-slate-900 dark:text-white">
                        🛡️ Điểm Trung thực Học thuật (Faithfulness):{' '}
                        <span className="text-emerald-600 dark:text-emerald-400 font-mono text-sm">
                          {claimResult.faithfulness_score}%
                        </span>
                      </span>
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 font-semibold">
                        🟢 Bảo chứng ({claimResult.entailed_count})
                      </span>
                      <span className="px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-800 dark:text-amber-300 font-semibold">
                        🟡 Suy luận ({claimResult.extrapolated_count})
                      </span>
                      <span className="px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-800 dark:text-rose-300 font-semibold">
                        🔴 Chưa đủ bằng chứng ({claimResult.unverified_count})
                      </span>
                    </div>
                    <span className="font-mono text-[10.5px] text-gray-500">{claimResult.formula}</span>
                  </div>

                  <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                    {claimResult.claims.map((c) => (
                      <div
                        key={c.index}
                        className="p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-gray-200 dark:border-gray-800 text-xs space-y-1"
                      >
                        <div className="flex items-center justify-between flex-wrap gap-1.5">
                          <span className="font-bold text-slate-800 dark:text-slate-200">
                            #{c.index} • {c.status_label} (S={c.entailment_score} • {c.entailment_pct}%)
                          </span>
                          {c.matched_filename && c.matched_page > 0 && (
                            <button
                              type="button"
                              onClick={() =>
                                handleOpenPdfVerify(
                                  c.matched_doc_id || '',
                                  c.matched_filename,
                                  c.matched_page,
                                  c.evidence_snippet,
                                  c.matched_title
                                )
                              }
                              className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800 text-[10.5px] font-semibold cursor-pointer"
                            >
                              <Eye className="h-3 w-3" />
                              <span>Đối chiếu PDF Trang {c.matched_page}</span>
                            </button>
                          )}
                        </div>
                        <p className="text-gray-700 dark:text-gray-300">{cleanMarkdownText(c.clean_text || c.claim_text)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <AcademicDocumentRenderer
                content={result}
                onCitationClick={(fname, pageNum, snippet) => {
                  const matchedRow = matrixRows.find(
                    (r) =>
                      r.filename.toLowerCase() === fname.toLowerCase() ||
                      r.title.toLowerCase().includes(fname.toLowerCase()) ||
                      fname.toLowerCase().includes(r.filename.toLowerCase().replace(/\.pdf$/i, ''))
                  );
                  handleOpenPdfVerify(
                    matchedRow?.document_id || '',
                    matchedRow?.filename || fname,
                    pageNum,
                    snippet,
                    matchedRow?.title || fname
                  );
                }}
              />
            </NeuralCard>
          )}
        </div>
      </div>

      {/* ── Side-by-Side PDF Viewer Panel (Click-to-Verify with Yellow Highlight) ── */}
      {activePdfViewer && (
        <aside className="w-full lg:w-1/2 h-screen sticky top-0 shrink-0 border-l border-gray-200 dark:border-gray-800 z-20 bg-white dark:bg-[#0A0F1A]">
          <SideBySidePdfViewer
            documentId={activePdfViewer.documentId}
            filename={activePdfViewer.filename}
            title={activePdfViewer.title}
            initialPage={activePdfViewer.page}
            totalPages={activePdfViewer.totalPages}
            token={token}
            snippet={activePdfViewer.snippet}
            onClose={() => setActivePdfViewer(null)}
          />
        </aside>
      )}
    </div>
  );
}
