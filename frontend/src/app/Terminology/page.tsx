'use client';

import React, { useEffect, useState } from 'react';
import {
  explainTerm,
  getDocuments,
  DocumentInfo,
  ExplainSourceItem,
  PipelineTelemetry,
} from '@/lib/api';
import { useAppStore } from '@/store/useAppStore';
import { NeuralCard } from '@/components/ui/NeuralCard';
import { NeuralBadge } from '@/components/ui/NeuralBadge';
import { SideBySidePdfViewer } from '@/components/ui/SideBySidePdfViewer';
import { AcademicDocumentRenderer, cleanMarkdownText } from '@/components/ui/AcademicDocumentRenderer';
import {
  Lightbulb,
  Search,
  Loader2,
  BookOpen,
  ChevronRight,
  Sparkles,
  Globe,
  FileText,
  Activity,
  Zap,
  Cpu,
  ShieldCheck,
  Copy,
  Check,
  ExternalLink,
  FileCode2,
} from 'lucide-react';

const SAMPLE_TERMS = [
  'Meta-analysis',
  'Systematic review',
  'p-value',
  'Effect size',
  'Cognitive behavioral therapy',
  'Randomized controlled trial',
  'Biomarker',
  'Comorbidity',
  'Pathophysiology',
  'Longitudinal study',
  'Cross-sectional study',
  'Confounding variable',
  'DSM-5',
  'ICD-11',
  'Serotonin',
];

export default function ExplainPage() {
  const token = useAppStore((s) => s.token);
  const [term, setTerm] = useState('');
  const [context, setContext] = useState('');
  const [lang, setLang] = useState<'vi' | 'en'>('vi');
  const [result, setResult] = useState('');
  const [sourceType, setSourceType] = useState<'uploaded_docs' | 'web_fallback' | ''>('');
  const [sources, setSources] = useState<ExplainSourceItem[]>([]);
  const [telemetry, setTelemetry] = useState<PipelineTelemetry | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<{
    term: string;
    result: string;
    sourceType?: 'uploaded_docs' | 'web_fallback' | '';
    sources?: ExplainSourceItem[];
    telemetry?: PipelineTelemetry | null;
  }[]>([]);
  const [docsList, setDocsList] = useState<DocumentInfo[]>([]);
  const [docIds, setDocIds] = useState<string[]>([]);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [activePdfViewer, setActivePdfViewer] = useState<{
    documentId: string;
    filename: string;
    title: string;
    page: number;
    snippet?: string;
  } | null>(null);

  useEffect(() => {
    getDocuments()
      .then((docs) => {
        const ready = docs.filter((d) => d.status === 'ready');
        setDocsList(ready);
        setDocIds(ready.map((d) => d.id));
      })
      .catch(() => {});
  }, []);

  const copyText = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const openCitationViewer = (
    docId?: string,
    docName?: string,
    pageRaw?: number | string,
    snippetText?: string
  ) => {
    const pageNum = typeof pageRaw === 'number' ? pageRaw : parseInt(String(pageRaw || '1'), 10) || 1;
    if (docId) {
      const found = docsList.find((d) => d.id === docId);
      setActivePdfViewer({
        documentId: docId,
        filename: found?.filename || docName || 'Document.pdf',
        title: found?.title || docName || 'Document.pdf',
        page: pageNum,
        snippet: snippetText,
      });
      return;
    }
    const cleanTarget = (docName || '').toLowerCase().replace(/\.pdf$/i, '').trim();
    const matchedDoc = docsList.find((d) => {
      const f = (d.filename || '').toLowerCase().replace(/\.pdf$/i, '').trim();
      const t = (d.title || '').toLowerCase().replace(/\.pdf$/i, '').trim();
      return (
        f === cleanTarget ||
        t === cleanTarget ||
        f.includes(cleanTarget) ||
        cleanTarget.includes(f) ||
        (t && (t.includes(cleanTarget) || cleanTarget.includes(t)))
      );
    });
    if (matchedDoc) {
      setActivePdfViewer({
        documentId: matchedDoc.id,
        filename: matchedDoc.filename,
        title: matchedDoc.title || matchedDoc.filename,
        page: pageNum,
        snippet: snippetText,
      });
    }
  };

  const renderExplanationWithCitations = (rawText: string) => {
    const regex = /(\*\*[\s\S]*?\*\*|\*[^*\n]+\*|\[[^\[\]]+?\s*(?:[-–—,:]|\s+)\s*(?:Page|Trang|tr\.|p\.|pp\.)\s*\d+(?:\s*[-–]\s*\d+)?\])/gi;
    const parts = rawText.split(regex);
    return parts.map((part, idx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={idx} className="font-bold text-gray-900 dark:text-white">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith('*') && part.endsWith('*')) {
        return (
          <em key={idx} className="italic text-gray-800 dark:text-gray-200">
            {part.slice(1, -1)}
          </em>
        );
      }
      const citMatch = part.match(
        /^\[([^\[\]]+?)\s*(?:[-–—,:]|\s+)\s*(?:Page|Trang|tr\.|p\.|pp\.)\s*(\d+)(?:\s*[-–]\s*\d+)?\]$/i
      );
      if (citMatch) {
        const docName = citMatch[1].trim();
        const pageNum = parseInt(citMatch[2], 10) || 1;
        const matchedSource = sources.find(
          (s) =>
            s.doc_filename?.toLowerCase().includes(docName.toLowerCase().replace(/\.pdf$/i, '')) ||
            s.doc_title?.toLowerCase().includes(docName.toLowerCase().replace(/\.pdf$/i, ''))
        );
        return (
          <button
            key={idx}
            type="button"
            onClick={() =>
              openCitationViewer(
                matchedSource?.document_id,
                matchedSource?.doc_filename || docName,
                pageNum,
                matchedSource?.text
              )
            }
            title={`Click-to-Verify: Mở ${docName} tại trang ${pageNum} và tô sáng đoạn trích`}
            className="inline-flex items-center gap-1 mx-1 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-amber-50 hover:bg-amber-100 dark:bg-amber-900/30 dark:hover:bg-amber-800/50 text-amber-800 dark:text-amber-300 border border-amber-300/80 dark:border-amber-700/70 transition-all cursor-pointer shadow-xs"
          >
            <FileText className="w-3 h-3 text-amber-600 dark:text-amber-400 shrink-0" />
            <span className="truncate max-w-[200px]">{docName}</span>
            <span className="px-1 rounded bg-amber-200/70 dark:bg-amber-800 text-amber-900 dark:text-amber-200 font-bold">
              Tr.{pageNum}
            </span>
          </button>
        );
      }
      return <React.Fragment key={idx}>{part}</React.Fragment>;
    });
  };

  async function handleExplain(overrideTerm?: string) {
    const t = (overrideTerm ?? term).trim();
    if (!t) return;
    setLoading(true);
    setError('');
    setResult('');
    setSourceType('');
    setSources([]);
    setTelemetry(null);
    try {
      const res = await explainTerm(
        t,
        context.trim() || undefined,
        lang,
        docIds.length > 0 ? docIds : undefined
      );
      setResult(res.explanation);
      const st = (res.source_type as 'uploaded_docs' | 'web_fallback') || '';
      setSourceType(st);
      setSources(res.sources || []);
      setTelemetry(res.telemetry || null);
      setHistory((prev) => [
        {
          term: t,
          result: res.explanation,
          sourceType: st,
          sources: res.sources || [],
          telemetry: res.telemetry || null,
        },
        ...prev.slice(0, 9),
      ]);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err?.response?.data?.detail ?? 'Could not explain. Try again later.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-surface-base transition-colors duration-300 flex">
      <div className={`flex-1 min-w-0 transition-all duration-300 ${activePdfViewer ? 'lg:pr-2' : ''}`}>
        {/* Hero Header */}
        <div className="relative overflow-hidden bg-gradient-to-br from-cortex-500/5 via-neural-500/5 to-dopamine-500/5 dark:from-cortex-900/20 dark:via-neural-900/20 dark:to-dopamine-900/20 border-b border-gray-200/50 dark:border-gray-800/50">
          <div className="absolute top-0 right-0 w-64 h-64 rounded-full bg-cortex-500/10 blur-3xl" />
          <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full bg-neural-500/10 blur-3xl" />
          <div className="relative container mx-auto px-6 py-10 max-w-5xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
                <Lightbulb className="w-6 h-6 text-white" />
              </div>
              <NeuralBadge variant="cortex" dot pulse>
                Explain Terms • Dual-Memory L1/L2 RAG
              </NeuralBadge>
            </div>
            <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 dark:text-white mb-2">
              Psychology Terminology
            </h1>
            <p className="text-gray-600 dark:text-gray-400 max-w-2xl">
              AI explains specialized academic terms grounded in your uploaded clinical documents (L1 Concept Memory & L2 Hybrid RRF + DCSR), with CEBM evidence grading and Click-to-Verify PDF highlighting.
            </p>
          </div>
        </div>

        <div className="container mx-auto px-6 py-8 max-w-5xl space-y-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: input + result */}
            <div className="lg:col-span-2 space-y-6">
              {/* Term input */}
              <NeuralCard variant="elevated" padding="lg">
                <div className="space-y-5">
                  <div className="space-y-3">
                    <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-200">
                      <Sparkles className="w-4 h-4 text-cortex-500" />
                      Term to explain
                    </label>
                    <div className="relative">
                      <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        value={term}
                        onChange={(e) => setTerm(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleExplain()}
                        placeholder="Enter a term... (e.g., meta-analysis, CBT, DSM-5, PHQ-9)"
                        className="w-full pl-11 pr-4 py-3.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-cortex-500/50 focus:border-cortex-500 transition-all placeholder-gray-400"
                      />
                    </div>
                  </div>

                  <div className="space-y-3">
                    <label className="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-300">
                      <BookOpen className="w-4 h-4 text-gray-400" />
                      Context <span className="text-gray-400 font-normal">(optional)</span>
                    </label>
                    <textarea
                      value={context}
                      onChange={(e) => setContext(e.target.value)}
                      placeholder="Paste text containing the term for more accurate explanation..."
                      rows={3}
                      className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-cortex-500/50 placeholder-gray-400 transition-all"
                    />
                  </div>

                  <div className="flex items-center justify-between flex-wrap gap-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => setLang('vi')}
                        className={`text-sm px-4 py-2 rounded-xl font-medium transition-all ${
                          lang === 'vi'
                            ? 'bg-neural-500 text-white shadow-md shadow-neural-500/25'
                            : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                        }`}
                      >
                        🇻🇳 Vietnamese
                      </button>
                      <button
                        onClick={() => setLang('en')}
                        className={`text-sm px-4 py-2 rounded-xl font-medium transition-all ${
                          lang === 'en'
                            ? 'bg-neural-500 text-white shadow-md shadow-neural-500/25'
                            : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                        }`}
                      >
                        🇬🇧 English
                      </button>
                    </div>
                    <button
                      onClick={() => handleExplain()}
                      disabled={!term.trim() || loading}
                      className="flex items-center gap-2 px-6 py-2.5 rounded-xl font-semibold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed bg-gradient-to-r from-cortex-500 to-violet-500 hover:shadow-lg hover:shadow-cortex-500/25 text-white"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" /> Explaining...
                        </>
                      ) : (
                        <>
                          <Lightbulb className="w-4 h-4" /> Explain
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </NeuralCard>

              {/* Result */}
              {(loading || result || error) && (
                <NeuralCard variant="elevated" padding="lg">
                  {loading ? (
                    <div className="space-y-3 py-4">
                      {[90, 75, 85, 60, 80].map((w, i) => (
                        <div
                          key={i}
                          className="h-4 bg-gradient-to-r from-gray-200 to-gray-100 dark:from-gray-700 dark:to-gray-800 rounded animate-pulse"
                          style={{ width: `${w}%` }}
                        />
                      ))}
                    </div>
                  ) : error ? (
                    <div className="text-center py-6">
                      <p className="text-sm text-red-500 mb-2">{error}</p>
                      <button
                        onClick={() => setError('')}
                        className="text-xs text-gray-400 hover:text-gray-600"
                      >
                        Try again
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center gap-3 mb-4 pb-4 border-b border-gray-100 dark:border-gray-800 flex-wrap">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center shrink-0">
                          <Lightbulb className="w-5 h-5 text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <span className="font-bold text-lg text-gray-900 dark:text-white block truncate">
                            {term}
                          </span>
                        </div>
                        {sourceType === 'uploaded_docs' && (
                          <span className="text-[11px] font-bold px-3 py-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 border border-emerald-100 dark:border-emerald-800">
                            <FileText className="w-3.5 h-3.5" /> Từ tài liệu lâm sàng đã tải lên
                          </span>
                        )}
                        {sourceType === 'web_fallback' && (
                          <span className="text-[11px] font-bold px-3 py-1.5 rounded-lg bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center gap-1.5 border border-blue-100 dark:border-blue-800">
                            <Globe className="w-3.5 h-3.5" /> Từ cơ sở tri thức / giáo trình chuẩn
                          </span>
                        )}
                      </div>

                      {/* Live RAG Pipeline Telemetry Pill */}
                      {telemetry && (
                        <div className="mb-5 p-2.5 rounded-xl bg-slate-50/90 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800 flex flex-wrap items-center gap-2 text-[11px]">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-semibold bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 border border-indigo-200/60 dark:border-indigo-800">
                            <Activity className="w-3 h-3" />
                            {telemetry.memory_tier || 'L2_HYBRID'}
                          </span>
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-medium bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200/70 dark:border-gray-700">
                            Dense {telemetry.vector_hits} + FTS {telemetry.fts_hits} (RRF k={telemetry.rrf_k})
                          </span>
                          <span
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-semibold border ${
                              telemetry.dcsr_fast_skip
                                ? 'bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border-amber-200/60 dark:border-amber-800'
                                : 'bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border-purple-200/60 dark:border-purple-800'
                            }`}
                          >
                            {telemetry.dcsr_fast_skip ? (
                              <>
                                <Zap className="w-3 h-3" /> DCSR Fast-Skip (Conf {telemetry.dcsr_confidence.toFixed(2)})
                              </>
                            ) : (
                              <>
                                <Cpu className="w-3 h-3" /> Cross-Encoder Reranked (Conf {telemetry.dcsr_confidence.toFixed(2)})
                              </>
                            )}
                          </span>
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-semibold bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border border-emerald-200/60 dark:border-emerald-800">
                            <ShieldCheck className="w-3 h-3" /> CRAG S₂={telemetry.crag_score.toFixed(3)}
                          </span>
                          <span className="ml-auto text-gray-500 dark:text-gray-400 font-mono">
                            {telemetry.latency_ms} ms
                          </span>
                        </div>
                      )}

                      <div className="mb-6">
                        <AcademicDocumentRenderer
                          content={result}
                          onCitationClick={(docName, pageNum, snippet) => {
                            const matchedSource = sources.find(
                              (s) =>
                                s.doc_filename?.toLowerCase().includes(docName.toLowerCase().replace(/\.pdf$/i, '')) ||
                                s.doc_title?.toLowerCase().includes(docName.toLowerCase().replace(/\.pdf$/i, ''))
                            );
                            openCitationViewer(
                              matchedSource?.document_id,
                              matchedSource?.doc_filename || docName,
                              pageNum,
                              matchedSource?.text || snippet
                            );
                          }}
                        />
                      </div>

                      {sources.length > 0 && (
                        <div className="pt-5 border-t border-gray-100 dark:border-gray-800">
                          <div className="flex items-center justify-between mb-3">
                            <p className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 flex items-center gap-2">
                              <BookOpen className="w-4 h-4 text-cortex-500" /> Tài liệu tham chiếu & Phân tầng bằng chứng CEBM ({sources.length})
                            </p>
                          </div>
                          <div className="space-y-3">
                            {sources.map((s, i) => {
                              const tierColor =
                                s.authority_tier === 'tier1'
                                  ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800'
                                  : s.authority_tier === 'tier2'
                                  ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800'
                                  : 'bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800';
                              return (
                                <div
                                  key={i}
                                  className="p-3.5 bg-gray-50/90 dark:bg-gray-800/50 rounded-xl border border-gray-200/70 dark:border-gray-800 space-y-2"
                                >
                                  <div className="flex items-start justify-between gap-2 flex-wrap">
                                    <div className="flex items-center gap-2.5 min-w-0">
                                      <div className="w-6 h-6 rounded-lg bg-cortex-100 dark:bg-cortex-900/40 flex items-center justify-center text-[11px] font-bold text-cortex-600 dark:text-cortex-400 shrink-0">
                                        {i + 1}
                                      </div>
                                      <div className="min-w-0">
                                        <span className="font-semibold text-sm text-gray-800 dark:text-gray-100 truncate block">
                                          {s.doc_title}
                                        </span>
                                        {s.doc_authors && (
                                          <span className="text-[11px] text-gray-500 dark:text-gray-400 block truncate">
                                            {s.doc_authors}
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                    <div className="flex items-center gap-1.5 flex-wrap">
                                      {s.cebm_label && (
                                        <span
                                          className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${tierColor}`}
                                        >
                                          {s.authority_tier === 'tier1' ? '🥇 ' : s.authority_tier === 'tier2' ? '🥈 ' : '🥉 '}
                                          {s.cebm_label}
                                        </span>
                                      )}
                                      {s.page_number !== '?' && (
                                        <button
                                          type="button"
                                          onClick={() =>
                                            openCitationViewer(
                                              s.document_id,
                                              s.doc_filename || s.doc_title,
                                              s.page_number,
                                              s.text
                                            )
                                          }
                                          className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-amber-50 hover:bg-amber-100 dark:bg-amber-900/30 dark:hover:bg-amber-800/50 text-amber-800 dark:text-amber-300 border border-amber-300/80 dark:border-amber-700/70 transition-all cursor-pointer"
                                          title="Click-to-Verify: Mở PDF đúng trang và tô sáng đoạn trích"
                                        >
                                          <ExternalLink className="w-3 h-3" />
                                          Mở PDF Tr.{s.page_number}
                                        </button>
                                      )}
                                    </div>
                                  </div>

                                  {s.text && (
                                    <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 italic pl-8 border-l-2 border-cortex-300 dark:border-cortex-700">
                                      “{cleanMarkdownText(s.text)}”
                                    </p>
                                  )}

                                  {(s.apa7 || s.bibtex) && (
                                    <div className="flex items-center gap-2 pl-8 pt-1 flex-wrap">
                                      {s.apa7 && (
                                        <button
                                          type="button"
                                          onClick={() => copyText(s.apa7!, `apa-${i}`)}
                                          className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-1 rounded-md bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 transition-colors"
                                        >
                                          {copiedKey === `apa-${i}` ? (
                                            <>
                                              <Check className="w-3 h-3 text-emerald-500" /> Đã chép APA 7th
                                            </>
                                          ) : (
                                            <>
                                              <Copy className="w-3 h-3" /> Copy APA 7th
                                            </>
                                          )}
                                        </button>
                                      )}
                                      {s.bibtex && (
                                        <button
                                          type="button"
                                          onClick={() => copyText(s.bibtex!, `bib-${i}`)}
                                          className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-1 rounded-md bg-white dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 transition-colors"
                                        >
                                          {copiedKey === `bib-${i}` ? (
                                            <>
                                              <Check className="w-3 h-3 text-emerald-500" /> Đã chép BibTeX
                                            </>
                                          ) : (
                                            <>
                                              <FileCode2 className="w-3 h-3" /> Copy BibTeX
                                            </>
                                          )}
                                        </button>
                                      )}
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </NeuralCard>
              )}
            </div>

            {/* Right: suggestions + history */}
            <div className="space-y-4">
              {/* Sample terms */}
              <NeuralCard variant="elevated" padding="lg">
                <div className="flex items-center gap-2 mb-4">
                  <Sparkles className="w-5 h-5 text-dopamine-500" />
                  <span className="text-sm font-bold text-gray-700 dark:text-gray-200">Popular Terms</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {SAMPLE_TERMS.map((t) => (
                    <button
                      key={t}
                      onClick={() => {
                        setTerm(t);
                        handleExplain(t);
                      }}
                      className="text-xs px-3 py-2 rounded-xl font-medium transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md border border-transparent hover:border-cortex-300 dark:hover:border-cortex-700 bg-cortex-50 dark:bg-cortex-900/30 text-cortex-700 dark:text-cortex-300 hover:bg-cortex-100 dark:hover:bg-cortex-900/50"
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </NeuralCard>

              {/* History */}
              {history.length > 0 && (
                <NeuralCard variant="elevated" padding="lg">
                  <div className="flex items-center gap-2 mb-4">
                    <BookOpen className="w-5 h-5 text-gray-400" />
                    <span className="text-sm font-bold text-gray-700 dark:text-gray-200">Recently Searched</span>
                  </div>
                  <div className="space-y-2">
                    {history.map((h, i) => (
                      <button
                        key={i}
                        onClick={() => {
                          setTerm(h.term);
                          setResult(h.result);
                          setSourceType(h.sourceType || '');
                          setSources(h.sources || []);
                          setTelemetry(h.telemetry || null);
                        }}
                        className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800/60 transition-colors group border border-transparent hover:border-gray-100 dark:hover:border-gray-800"
                      >
                        <div className="w-7 h-7 rounded-lg bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-[10px] font-bold text-gray-400 group-hover:bg-cortex-100 group-hover:text-cortex-600 dark:group-hover:bg-cortex-900/30 dark:group-hover:text-cortex-400 transition-colors">
                          {i + 1}
                        </div>
                        <span className="flex-1 text-sm text-left text-gray-700 dark:text-gray-200 group-hover:text-cortex-600 dark:group-hover:text-cortex-400 transition-colors truncate">
                          {h.term}
                        </span>
                        <ChevronRight className="w-4 h-4 text-gray-300 dark:text-gray-600 group-hover:text-cortex-500 transition-colors" />
                      </button>
                    ))}
                  </div>
                </NeuralCard>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Split-Screen PDF Click-to-Verify Viewer */}
      {activePdfViewer && (
        <div className="w-full lg:w-[46%] xl:w-[48%] h-screen sticky top-0 border-l border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 z-30 shadow-2xl">
          <SideBySidePdfViewer
            documentId={activePdfViewer.documentId}
            filename={activePdfViewer.filename}
            title={activePdfViewer.title}
            initialPage={activePdfViewer.page}
            token={token}
            snippet={activePdfViewer.snippet}
            onClose={() => setActivePdfViewer(null)}
          />
        </div>
      )}
    </div>
  );
}

