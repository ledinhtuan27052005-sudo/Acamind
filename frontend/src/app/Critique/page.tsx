'use client';

import { useState } from 'react';
import { debateStream, scrapeUrl, ScrapeResult } from '@/lib/api';
import { NeuralCard } from '@/components/ui/NeuralCard';
import { NeuralBadge } from '@/components/ui/NeuralBadge';
import { NeuralButton } from '@/components/ui/NeuralButton';
import { Scale, Globe, Brain, Sparkles, ChevronRight, Loader2, ArrowLeftRight, Link2 } from 'lucide-react';

type Phase = 'input' | 'loading' | 'result';

export default function DebatePage() {
 const [url1, setUrl1] = useState('');
 const [url2, setUrl2] = useState('');
 const [topic, setTopic] = useState('');
 const [phase, setPhase] = useState<Phase>('input');
 const [preview1, setPreview1] = useState<ScrapeResult | null>(null);
 const [preview2, setPreview2] = useState<ScrapeResult | null>(null);
 const [previewLoading, setPreviewLoading] = useState(false);
 const [analysis, setAnalysis] = useState('');
 const [error, setError] = useState('');

 const handlePreview = async () => {
 if (!url1.trim() || !url2.trim()) return;
 setPreviewLoading(true);
 setError('');
 try {
 const [r1, r2] = await Promise.all([
 scrapeUrl(url1.trim()),
 scrapeUrl(url2.trim()),
 ]);
 setPreview1(r1);
 setPreview2(r2);
 } catch (e) {
 setError('Cannot read content. Check URL and try again.');
 } finally {
 setPreviewLoading(false);
 }
 };

 const handleAnalyze = async () => {
 if (!url1.trim() || !url2.trim()) return;
 setPhase('loading');
 setAnalysis('');
 setError('');
 try {
 await debateStream(url1.trim(), url2.trim(), topic.trim(), (chunk) => {
 setAnalysis((prev) => prev + chunk);
 setPhase('result');
 });
 } catch (e) {
 setError('Analysis error: ' + (e as Error).message);
 setPhase('input');
 }
 };

 const reset = () => {
 setUrl1(''); setUrl2(''); setTopic('');
 setPhase('input'); setAnalysis('');
 setPreview1(null); setPreview2(null);
 setError('');
 };

 return (
 <div className="min-h-screen bg-gray-50 dark:bg-surface-base transition-colors duration-300">
 {/* Hero Header */}
 <div className="relative overflow-hidden bg-gradient-to-br from-neural-500/5 via-cortex-500/5 to-dopamine-500/5 dark:from-neural-900/20 dark:via-cortex-900/20 dark:to-dopamine-900/20 border-b border-gray-200/50 dark:border-gray-800/50">
 <div className="absolute top-0 right-0 w-64 h-64 rounded-full bg-neural-500/10 blur-3xl" />
 <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full bg-cortex-500/10 blur-3xl" />
 <div className="relative container mx-auto px-6 py-10 max-w-5xl">
 <div className="flex items-center gap-3 mb-4">
 <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
 <Scale className="w-6 h-6 text-white" />
 </div>
 <NeuralBadge variant="cortex" dot pulse>
 AI Critique
 </NeuralBadge>
 </div>
 <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 dark:text-white mb-2">
 Analyze & Critique Articles
 </h1>
 <p className="text-gray-600 dark:text-gray-400 max-w-2xl">
 Enter 2 articles/URLs — AI will compare viewpoints, analyze contradictions, and evaluate the rigor of scientific arguments.
 </p>
 </div>
 </div>

 <div className="container mx-auto px-6 py-8 max-w-5xl space-y-8">
 {/* How it works */}
 {phase === 'input' && (
 <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
 {[
 { icon: Globe, title: 'Content Collection', desc: 'AI automatically reads and extracts text from the 2 URLs you provide.', color: '#0D9488' },
 { icon: Brain, title: 'Viewpoint Analysis', desc: 'LLM compares arguments, finds agreements and contradictions.', color: '#7C3AED' },
 { icon: Scale, title: 'Objective Evaluation', desc: 'Comprehensive assessment of reliability and argument quality.', color: '#F59E0B' },
 ].map(({ icon: Icon, title, desc, color }) => (
 <NeuralCard key={title} variant="elevated" padding="lg" className="text-center">
 <div className="w-12 h-12 rounded-xl mx-auto mb-3 flex items-center justify-center" style={{ background: `${color}15` }}>
 <Icon className="w-6 h-6" style={{ color }} />
 </div>
 <h3 className="font-bold text-gray-900 dark:text-white mb-1">{title}</h3>
 <p className="text-sm text-gray-600 dark:text-gray-400">{desc}</p>
 </NeuralCard>
 ))}
 </div>
 )}

 {/* Input form */}
 <NeuralCard variant="elevated" padding="lg">
 <div className="grid md:grid-cols-2 gap-6 mb-6">
 {/* Article 1 */}
 <div className="space-y-3">
 <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-200">
 <div className="w-2 h-2 rounded-full bg-blue-500" />
 Article 1
 </label>
 <div className="relative">
 <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
 <input
 type="url"
 value={url1}
 onChange={(e) => setUrl1(e.target.value)}
 placeholder="https://..."
 className="w-full pl-9 pr-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-neural-500/50 focus:border-neural-500 transition-all placeholder-gray-400"
 />
 </div>
 {preview1 && (
 <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-100 dark:border-blue-800">
 <p className="text-xs font-semibold text-blue-700 dark:text-blue-300 truncate">{preview1.title}</p>
 <p className="text-xs text-gray-500 mt-0.5">{preview1.char_count.toLocaleString()} characters</p>
 </div>
 )}
 </div>

 {/* Article 2 */}
 <div className="space-y-3">
 <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-200">
 <div className="w-2 h-2 rounded-full bg-purple-500" />
 Article 2
 </label>
 <div className="relative">
 <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
 <input
 type="url"
 value={url2}
 onChange={(e) => setUrl2(e.target.value)}
 placeholder="https://..."
 className="w-full pl-9 pr-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-neural-500/50 focus:border-neural-500 transition-all placeholder-gray-400"
 />
 </div>
 {preview2 && (
 <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-xl border border-purple-100 dark:border-purple-800">
 <p className="text-xs font-semibold text-purple-700 dark:text-purple-300 truncate">{preview2.title}</p>
 <p className="text-xs text-gray-500 mt-0.5">{preview2.char_count.toLocaleString()} characters</p>
 </div>
 )}
 </div>
 </div>

 {/* Topic */}
 <div className="mb-6">
 <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">
 <Sparkles className="w-4 h-4 text-dopamine-500" />
 Debate Topic <span className="text-gray-400 font-normal">(optional)</span>
 </label>
 <input
 type="text"
 value={topic}
 onChange={(e) => setTopic(e.target.value)}
 placeholder="Example: COVID-19 vaccine efficacy, Effects of sugar in diet..."
 className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-neural-500/50 focus:border-neural-500 transition-all placeholder-gray-400"
 />
 </div>

 {error && (
 <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-xl border border-red-100 dark:border-red-800">
 <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
 </div>
 )}

 <div className="flex flex-wrap gap-3">
 <button
 onClick={handlePreview}
 disabled={!url1.trim() || !url2.trim() || previewLoading}
 className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 text-sm font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-40 transition-colors"
 >
 {previewLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Globe className="w-4 h-4" />}
 Preview Content
 </button>
 <button
 onClick={handleAnalyze}
 disabled={!url1.trim() || !url2.trim() || phase === 'loading'}
 className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-gradient-to-r from-neural-500 to-cyan-500 text-white text-sm font-semibold hover:shadow-lg hover:shadow-neural-500/25 disabled:opacity-40 transition-all"
 >
 {phase === 'loading' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Scale className="w-4 h-4" />}
 {phase === 'loading' ? 'AI is analyzing...' : 'Start Analysis & Critique'}
 </button>
 </div>
 </NeuralCard>

 {/* Analysis result */}
 {(phase === 'result' || phase === 'loading') && (
 <NeuralCard variant="elevated" padding="lg">
 <div className="flex items-center justify-between mb-6">
 <div className="flex items-center gap-3">
 <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cortex-500 to-violet-500 flex items-center justify-center">
 <Brain className="w-5 h-5 text-white" />
 </div>
 <div>
 <h2 className="font-bold text-gray-900 dark:text-white">Analysis Results</h2>
 <p className="text-xs text-gray-500">Compare & evaluate two articles</p>
 </div>
 </div>
 {phase === 'result' && (
 <button
 onClick={reset}
 className="text-xs text-gray-400 hover:text-neural-500 transition-colors"
 >
 New Analysis
 </button>
 )}
 </div>

 {phase === 'loading' && !analysis && (
 <div className="flex items-center gap-3 py-6">
 <div className="flex gap-1">
 <span className="w-2 h-2 rounded-full bg-neural-500 animate-bounce" style={{ animationDelay: '0ms' }} />
 <span className="w-2 h-2 rounded-full bg-neural-500 animate-bounce" style={{ animationDelay: '150ms' }} />
 <span className="w-2 h-2 rounded-full bg-neural-500 animate-bounce" style={{ animationDelay: '300ms' }} />
 </div>
 <span className="text-sm text-gray-500">AI is reading and comparing content...</span>
 </div>
 )}

 {analysis && (
 <div className="prose prose-sm dark:prose-invert max-w-none">
 <div className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed whitespace-pre-wrap">
 {analysis}
 </div>
 </div>
 )}
 </NeuralCard>
 )}
 </div>
 </div>
 );
}
