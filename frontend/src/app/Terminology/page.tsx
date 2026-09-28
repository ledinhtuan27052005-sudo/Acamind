'use client';

import { useEffect, useState } from 'react';
import { explainTerm, getDocuments } from '@/lib/api';
import { NeuralCard } from '@/components/ui/NeuralCard';
import { NeuralBadge } from '@/components/ui/NeuralBadge';
import { NeuralButton } from '@/components/ui/NeuralButton';
import { Lightbulb, Search, Loader2, BookOpen, ChevronRight, Sparkles, Globe, FileText } from 'lucide-react';

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
 const [term, setTerm] = useState('');
 const [context, setContext] = useState('');
 const [lang, setLang] = useState<'vi' | 'en'>('vi');
 const [result, setResult] = useState('');
 const [sourceType, setSourceType] = useState<'uploaded_docs' | 'web_fallback' | ''>('');
 const [sources, setSources] = useState<{ doc_title: string; page_number: number | string; text: string }[]>([]);
 const [loading, setLoading] = useState(false);
 const [error, setError] = useState('');
 const [history, setHistory] = useState<{ term: string; result: string }[]>([]);
 const [docIds, setDocIds] = useState<string[]>([]);

 useEffect(() => {
 getDocuments()
 .then((docs) => setDocIds(docs.filter((d) => d.status === 'ready').map((d) => d.id)))
 .catch(() => {});
 }, []);

 async function handleExplain(overrideTerm?: string) {
 const t = (overrideTerm ?? term).trim();
 if (!t) return;
 setLoading(true); setError(''); setResult(''); setSourceType(''); setSources([]);
 try {
 const res = await explainTerm(t, context.trim() || undefined, lang, docIds.length > 0 ? docIds : undefined);
 setResult(res.explanation);
 setSourceType((res.source_type as 'uploaded_docs' | 'web_fallback') || '');
 setSources(res.sources || []);
 setHistory(prev => [{ term: t, result: res.explanation }, ...prev.slice(0, 9)]);
 } catch (e: unknown) {
 const err = e as { response?: { data?: { detail?: string } } };
 setError(err?.response?.data?.detail ?? 'Could not explain. Try again later.');
 } finally {
 setLoading(false);
 }
 }

 return (
 <div className="min-h-screen bg-gray-50 dark:bg-surface-base transition-colors duration-300">

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
 Explain Terms
 </NeuralBadge>
 </div>
 <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 dark:text-white mb-2">
 Psychology Terminology
 </h1>
 <p className="text-gray-600 dark:text-gray-400 max-w-2xl">
 AI explains specialized academic terms instantly. Choose a suggestion or enter your own term.
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
 onChange={e => setTerm(e.target.value)}
 onKeyDown={e => e.key === 'Enter' && handleExplain()}
 placeholder="Enter a term... (e.g., meta-analysis, CBT, DSM-5)"
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
 onChange={e => setContext(e.target.value)}
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
 <div className="flex items-center gap-3 mb-5 pb-5 border-b border-gray-100 dark:border-gray-800">
 <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center">
 <Lightbulb className="w-5 h-5 text-white" />
 </div>
 <div className="flex-1">
 <span className="font-bold text-lg text-gray-900 dark:text-white">{term}</span>
 </div>
 {sourceType === 'uploaded_docs' && (
 <span className="text-[11px] font-bold px-3 py-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 border border-emerald-100 dark:border-emerald-800">
 <FileText className="w-3.5 h-3.5" /> From uploaded documents
 </span>
 )}
 {sourceType === 'web_fallback' && (
 <span className="text-[11px] font-bold px-3 py-1.5 rounded-lg bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center gap-1.5 border border-blue-100 dark:border-blue-800">
 <Globe className="w-3.5 h-3.5" /> From web/textbooks
 </span>
 )}
 </div>

 <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed whitespace-pre-wrap mb-6">
 {result}
 </p>

 {sources.length > 0 && (
 <div className="pt-5 border-t border-gray-100 dark:border-gray-800">
 <p className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3 flex items-center gap-2">
 <BookOpen className="w-4 h-4" /> References ({sources.length})
 </p>
 <div className="space-y-2">
 {sources.map((s, i) => (
 <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-800">
 <div className="w-6 h-6 rounded-lg bg-cortex-100 dark:bg-cortex-900/30 flex items-center justify-center text-[10px] font-bold text-cortex-600 dark:text-cortex-400">
 {i + 1}
 </div>
 <div className="flex-1 min-w-0">
 <span className="font-medium text-sm text-gray-800 dark:text-gray-200 truncate block">{s.doc_title}</span>
 {s.page_number !== '?' && (
 <span className="text-xs text-gray-400">page {s.page_number}</span>
 )}
 </div>
 </div>
 ))}
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
 {SAMPLE_TERMS.map(t => (
 <button
 key={t}
 onClick={() => { setTerm(t); handleExplain(t); }}
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
 onClick={() => { setTerm(h.term); setResult(h.result); }}
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
 );
}
