'use client';

import { useEffect, useState, useCallback } from 'react';
import { useAppStore } from '@/store/useAppStore';
import { getLibraryArticles, analyzeArticles, LibraryArticle, AnalysisResult } from '@/lib/api';
import { useI18n } from '@/lib/i18n/context';
import {
  BarChart2, Search, BookOpen, Check, X, Loader2,
  ChevronDown, ChevronUp, AlertCircle, Sparkles, Globe, Target
} from 'lucide-react';
import Link from 'next/link';

// ── Small helpers ──────────────────────────────────────────────────────────────

function LangBadge({ lang }: { lang: string }) {
  return lang === 'en'
    ? <span className="text-xs px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300">🇬🇧 EN</span>
    : <span className="text-xs px-1.5 py-0.5 rounded bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-300">🇻🇳 VI</span>;
}

// ── Article selector card ──────────────────────────────────────────────────────

function ArticleSelectCard({
  article,
  selected,
  onToggle,
}: {
  article: LibraryArticle;
  selected: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      className={`w-full text-left p-4 rounded-xl border transition-all flex items-start gap-3 ${
        selected
          ? 'bg-teal-500/10 border-teal-500/30 shadow-md shadow-teal-500/5'
          : 'bg-white dark:bg-slate-800/60 border-slate-200 dark:border-slate-700/60 hover:bg-slate-50 dark:hover:bg-slate-700/40'
      }`}
    >
      <div className={`mt-0.5 w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 transition-all ${
        selected ? 'bg-teal-500 border-teal-500 text-white' : 'border-slate-300 dark:border-slate-600 bg-transparent'
      }`}>
        {selected && <Check className="w-3 h-3 stroke-[3]" />}
      </div>

      <div className="flex-1 min-w-0 space-y-1">
        <h4 className="font-semibold text-slate-800 dark:text-slate-100 text-sm line-clamp-1 leading-snug">
          {article.title_vi || article.title_original}
        </h4>
        {article.title_vi && article.title_original && (
          <p className="text-xs text-slate-400 dark:text-slate-500 italic line-clamp-1">
            {article.title_original}
          </p>
        )}
        <div className="flex items-center gap-2 mt-2">
          <LangBadge lang={article.language} />
          <span className="text-[10px] text-slate-400 dark:text-slate-500 truncate max-w-[150px]">
            {article.authors || 'Unknown Authors'}
          </span>
        </div>
      </div>
    </button>
  );
}

// ── Section Component for Comparison Table ──────────────────────────────────────

interface SectionProps {
  title: string;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

function Section({ title, isOpen, onToggle, children }: SectionProps) {
  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-5 py-3.5 bg-slate-50 dark:bg-slate-800/40 text-left"
      >
        <span className="font-medium text-sm text-slate-800 dark:text-slate-100">{title}</span>
        {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400 dark:text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-400 dark:text-slate-500" />}
      </button>
      {isOpen && <div className="p-5">{children}</div>}
    </div>
  );
}

// ── Comparison table ───────────────────────────────────────────────────────────

function ComparisonTable({
  result,
}: {
  result: AnalysisResult;
}) {
  const { t } = useI18n();
  const { articles, analysis } = result;
  const [open, setOpen] = useState({ themes: true, diffs: true, table: true, gaps: true });

  const toggle = (k: keyof typeof open) => setOpen(prev => ({ ...prev, [k]: !prev[k] }));

  return (
    <div className="space-y-4">
      {/* Summary banner */}
      <div className="bg-gradient-to-r from-teal-50 to-purple-50 dark:from-teal-900/20 dark:to-purple-900/20 rounded-xl border border-teal-100 dark:border-teal-800/50 p-5 shadow-inner">
        <div className="flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-teal-500 flex-shrink-0 mt-0.5 drop-shadow-[0_0_8px_rgba(20,184,166,0.4)]" />
          <div>
            <p className="text-sm font-semibold text-teal-800 dark:text-teal-300 mb-1">{t.analysis.summary}</p>
            <p className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed">{analysis.summary}</p>
          </div>
        </div>
      </div>

      {/* Article headers */}
      <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${articles.length}, 1fr)` }}>
        {articles.map((art, i) => (
          <div key={art.id} className="bg-glass-card rounded-lg p-3 text-center">
            <p className="text-xs font-bold bg-clip-text text-transparent bg-gradient-to-r from-teal-500 to-purple-500 mb-1">{t.analysis.article_label} {i + 1}</p>
            <p className="text-xs text-slate-700 dark:text-slate-200 line-clamp-2">{art.title_vi || art.title_original}</p>
            <LangBadge lang={art.language} />
          </div>
        ))}
      </div>

      {/* Comparison table */}
      {analysis.comparison_table.length > 0 && (
        <Section title={`📊 ${t.analysis.comparison_table}`} isOpen={open.table} onToggle={() => toggle('table')}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50/50 dark:bg-slate-800/30">
                  <th className="text-left px-4 py-2.5 font-medium text-slate-600 dark:text-slate-300 w-40">{t.analysis.factor}</th>
                  {articles.map((_, i) => (
                    <th key={i} className="text-center px-4 py-2.5 font-medium text-teal-600 dark:text-teal-400">
                      {t.analysis.article_label} {i + 1}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {analysis.comparison_table.map((row, ri) => (
                  <tr key={ri} className="hover:bg-slate-100 dark:hover:bg-slate-800/60 dark:hover:bg-gray-800/30 transition-colors">
                    <td className="px-4 py-3 font-medium text-slate-700 dark:text-slate-200">{row.factor}</td>
                    {row.values.map((val, vi) => (
                      <td key={vi} className="px-4 py-3 text-center text-slate-600 dark:text-slate-300 text-xs">
                        {val || '—'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}

      <Section title={`💡 ${t.analysis.common_themes}`} isOpen={open.themes} onToggle={() => toggle('themes')}>
        <div className="grid gap-4 md:grid-cols-2">
          {analysis.common_themes.map((theme: any, i: number) => (
            <div key={i} className="bg-glass-card p-4 rounded-xl space-y-1.5 hover:shadow-md transition-shadow">
              <h4 className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-teal-400" /> {theme.theme}
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">{theme.explanation}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section title={`⚖️ ${t.analysis.differences}`} isOpen={open.diffs} onToggle={() => toggle('diffs')}>
        <div className="space-y-3">
          {analysis.differences.map((diff: any, i: number) => (
            <div key={i} className="bg-glass-card p-4 rounded-xl border-l-4 border-purple-400 space-y-1.5">
              <h4 className="font-semibold text-slate-800 dark:text-slate-200">{diff.aspect}</h4>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">{diff.difference}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section title={`🔍 ${t.analysis.research_gaps}`} isOpen={open.gaps} onToggle={() => toggle('gaps')}>
        <div className="space-y-3">
          {analysis.research_gaps.map((gap: any, i: number) => (
            <div key={i} className="bg-glass-card p-4 rounded-xl border-l-4 border-amber-400 space-y-1.5">
              <h4 className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                <Target className="w-4 h-4 text-amber-500" /> {gap.gap}
              </h4>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">{gap.implication}</p>
            </div>
          ))}
        </div>
      </Section>

      {analysis.recommendation && (
        <div className="bg-gradient-to-r from-purple-50 to-teal-50 dark:from-purple-900/10 dark:to-teal-900/10 rounded-xl border border-purple-100/50 dark:border-purple-800/40 p-5 space-y-2">
          <h4 className="font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-purple-500 drop-shadow-[0_0_8px_rgba(168,85,247,0.4)]" /> {t.analysis.recommendation}
          </h4>
          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">{analysis.recommendation}</p>
        </div>
      )}
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function AnalysisPage() {
  const { user } = useAppStore();
  const { t } = useI18n();

  const [articles, setArticles] = useState<LibraryArticle[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState('');
  const [langFilter, setLangFilter] = useState<'all' | 'en' | 'vi'>('all');
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState('');

  const loadArticles = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getLibraryArticles();
      setArticles(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadArticles(); }, [loadArticles]);

  const filtered = articles.filter(a => {
    const q = search.toLowerCase();
    const matchesSearch = !q ||
      (a.title_original?.toLowerCase().includes(q)) ||
      (a.title_vi?.toLowerCase().includes(q)) ||
      (a.authors?.toLowerCase().includes(q));
    const matchesLang = langFilter === 'all' || a.language === langFilter;
    return matchesSearch && matchesLang;
  });

  const toggleSelect = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else if (next.size < 8) next.add(id);
      return next;
    });
    setResult(null);
  };

  async function runAnalysis() {
    if (selected.size < 2) return;
    setAnalyzing(true); setError(''); setResult(null);
    try {
      const res = await analyzeArticles(Array.from(selected));
      setResult(res);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err?.response?.data?.detail ?? t.common.error);
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 dark:text-white flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500 to-purple-500 flex items-center justify-center shadow-lg shadow-teal-500/20">
              <BarChart2 className="w-5 h-5 text-white" />
            </div>
            {t.analysis.title}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
            {t.analysis.subtitle}
          </p>
        </div>
        <Link href="/library" className="flex items-center gap-2 text-sm font-medium text-teal-600 hover:text-teal-700 dark:text-teal-400 dark:hover:text-teal-300 transition-colors bg-teal-50 dark:bg-teal-500/10 px-4 py-2 rounded-xl">
          <BookOpen className="w-4 h-4" /> {t.analysis.library}
        </Link>
      </div>

      <div className={`grid gap-6 ${result ? 'xl:grid-cols-2' : 'xl:grid-cols-1'}`}>
        {/* Left: selector */}
        <div className="space-y-4">
          {/* Toolbar */}
          <div className="flex flex-wrap gap-3">
            <div className="relative flex-1 min-w-52">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500 pointer-events-none" />
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder={t.analysis.search_placeholder}
                className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300/50 placeholder-slate-400 dark:placeholder-slate-500"
              />
            </div>
            <div className="flex gap-2">
              {(['all', 'en', 'vi'] as const).map(l => (
                <button
                  key={l}
                  onClick={() => setLangFilter(l)}
                  className={`text-xs px-3 py-2 rounded-lg border font-medium transition-all ${
                    langFilter === l
                      ? 'bg-teal-50 dark:bg-teal-900/30 border-teal-300 dark:border-teal-700 text-teal-600 dark:text-teal-400'
                      : 'bg-white dark:bg-slate-800/60 border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:border-gray-300'
                  }`}
                >
                  {l === 'all' ? <Globe className="w-3.5 h-3.5 inline" /> : l === 'en' ? '🇬🇧 EN' : '🇻🇳 VI'}
                </button>
              ))}
            </div>
          </div>

          {/* Selection status */}
          <div className="flex items-center justify-between bg-white dark:bg-slate-800/60 rounded-lg border border-slate-200 dark:border-slate-700 px-4 py-3">
            <span className="text-sm text-slate-600 dark:text-slate-300">
              {t.analysis.selected}: <strong className="text-teal-600 dark:text-teal-400">{selected.size}</strong> / 8 {t.analysis.article_label.toLowerCase()}s
              {selected.size >= 2 && <span className="ml-2 text-teal-500 font-medium">✓ {t.analysis.ready}</span>}
              {selected.size === 1 && <span className="ml-2 text-amber-500">{t.analysis.need_more}</span>}
            </span>
            <div className="flex gap-2">
              {selected.size > 0 && (
                <button
                  onClick={() => { setSelected(new Set()); setResult(null); }}
                  className="text-xs text-slate-400 dark:text-slate-500 hover:text-red-500 transition-colors flex items-center gap-1"
                >
                  <X className="w-3 h-3" /> {t.analysis.clear}
                </button>
              )}
              <button
                onClick={runAnalysis}
                disabled={selected.size < 2 || analyzing}
                className="flex items-center gap-2 text-sm px-4 py-1.5 rounded-lg bg-gradient-to-r from-teal-500 to-purple-500 hover:from-teal-600 hover:to-purple-600 disabled:from-gray-300 disabled:to-gray-300 dark:disabled:from-gray-700 dark:disabled:to-gray-700 text-white font-medium transition-all disabled:cursor-not-allowed shadow-md shadow-teal-500/20"
              >
                {analyzing ? (
                  <><Loader2 className="w-3.5 h-3.5 animate-spin" /> {t.analysis.analyzing}</>
                ) : (
                  <><Sparkles className="w-3.5 h-3.5" /> {t.analysis.run_analysis}</>
                )}
              </button>
            </div>
          </div>

          {error && (
            <div className="flex items-start gap-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-lg p-3 border border-red-200 dark:border-red-800">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" /> {error}
            </div>
          )}

          {/* Article list */}
          <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-1">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-20 bg-slate-100 dark:bg-slate-800/60 rounded-xl animate-pulse" />
              ))
            ) : filtered.length === 0 ? (
              <div className="text-center py-12 text-slate-400 dark:text-slate-500">
                <BookOpen className="w-8 h-8 mx-auto mb-2" />
                <p className="text-sm">{search ? t.analysis.no_results : t.analysis.no_articles}</p>
              </div>
            ) : (
              filtered.map(art => (
                <ArticleSelectCard
                  key={art.id}
                  article={art}
                  selected={selected.has(art.id)}
                  onToggle={() => toggleSelect(art.id)}
                />
              ))
            )}
          </div>
        </div>

        {/* Right: results */}
        {result && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-200 dark:border-slate-700">
              <Sparkles className="w-4 h-4 text-teal-500 drop-shadow-[0_0_8px_rgba(20,184,166,0.4)]" />
              <h2 className="font-semibold text-slate-900 dark:text-slate-100 dark:text-white text-sm">{t.analysis.results}</h2>
              <span className="text-xs text-slate-400 dark:text-slate-500">({result.articles.length} {t.analysis.article_label.toLowerCase()}s)</span>
            </div>
            <ComparisonTable result={result} />
          </div>
        )}
      </div>
    </div>
  );
}
