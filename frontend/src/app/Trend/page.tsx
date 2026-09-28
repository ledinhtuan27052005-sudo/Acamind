'use client';

import { useEffect, useState, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { getTrends } from '@/lib/api';
import type { TrendsData } from '@/lib/api';
import { NeuralCard } from '@/components/ui/NeuralCard';
import { NeuralBadge } from '@/components/ui/NeuralBadge';
import { TrendingUp, Hash, BarChart3, Calendar, Zap, Sparkles, TrendingDown, ArrowUp } from 'lucide-react';

/* ── Color palette for word cloud ─────────────────────────────────────────── */

const WORD_PALETTE = [
 { text: '#0D9488', bg: 'rgba(13,148,136,0.08)' },  // neural
 { text: '#7C3AED', bg: 'rgba(124,58,237,0.08)' },  // cortex
 { text: '#F59E0B', bg: 'rgba(245,158,11,0.08)' },   // dopamine
 { text: '#EC4899', bg: 'rgba(236,72,153,0.08)' },   // pink
 { text: '#06B6D4', bg: 'rgba(6,182,212,0.08)' },    // cyan
 { text: '#10B981', bg: 'rgba(16,185,129,0.08)' },   // emerald
 { text: '#8B5CF6', bg: 'rgba(139,92,246,0.08)' },   // violet
 { text: '#EF4444', bg: 'rgba(239,68,68,0.08)' },     // red
];

/* ── Scroll-triggered wrapper ─────────────────────────────────────────────── */

function FadeIn({ children, delay = 0, className = '' }: { children: React.ReactNode; delay?: number; className?: string }) {
 const ref = useRef<HTMLDivElement>(null);
 const seen = useInView(ref, { once: true, margin: '-60px' });
 return (
 <motion.div
 ref={ref}
 initial={{ opacity: 0, y: 18 }}
 animate={seen ? { opacity: 1, y: 0 } : {}}
 transition={{ duration: 0.45, delay, ease: [0.25, 0.1, 0.25, 1] }}
 className={className}
 >
 {children}
 </motion.div>
 );
}

/* ── Word Cloud item ──────────────────────────────────────────────────────── */

function WordTag({ word, count, maxCount, index }: { word: string; count: number; maxCount: number; index: number }) {
 const ratio = count / maxCount;
 const palette = WORD_PALETTE[index % WORD_PALETTE.length];
 const fontSize = ratio > 0.8 ? 28 : ratio > 0.6 ? 22 : ratio > 0.4 ? 17 : ratio > 0.2 ? 14 : 12;
 const weight = ratio > 0.6 ? 800 : ratio > 0.3 ? 600 : 500;

 return (
 <motion.span
 initial={{ opacity: 0, scale: 0.8 }}
 animate={{ opacity: 1, scale: 1 }}
 transition={{ delay: index * 0.03, type: 'spring', stiffness: 200 }}
 whileHover={{ scale: 1.08, y: -2 }}
 title={`${count} times`}
 className="inline-flex items-center cursor-default rounded-full px-3 py-1.5 transition-all"
 style={{
 fontSize,
 fontWeight: weight,
 color: palette.text,
 background: palette.bg,
 border: `1px solid ${palette.text}18`,
 lineHeight: 1.4,
 }}
 >
 {word}
 </motion.span>
 );
}

/* ── Animated bar ─────────────────────────────────────────────────────────── */

function AnimBar({ pct, color, delay }: { pct: number; color: string; delay: number }) {
 const ref = useRef<HTMLDivElement>(null);
 const seen = useInView(ref, { once: true });
 return (
 <div ref={ref} className="h-2 rounded-full overflow-hidden bg-gray-100 dark:bg-gray-800">
 <motion.div
 className="h-full rounded-full"
 style={{ background: `linear-gradient(90deg, ${color}, ${color}80)` }}
 initial={{ width: 0 }}
 animate={seen ? { width: `${pct}%` } : {}}
 transition={{ duration: 0.8, delay, ease: 'easeOut' }}
 />
 </div>
 );
}

/* ── Main Page ────────────────────────────────────────────────────────────── */

export default function TrendsPage() {
 const [data, setData] = useState<TrendsData | null>(null);
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState('');

 useEffect(() => {
 getTrends()
 .then(setData)
 .catch(() => setError('Failed to load trending data.'))
 .finally(() => setLoading(false));
 }, []);

 if (loading) return (
 <div className="min-h-screen bg-gray-50 dark:bg-surface-base flex items-center justify-center">
 <div className="text-center space-y-4">
 <div className="w-12 h-12 rounded-full border-3 border-neural-200 border-t-neural-500 animate-spin mx-auto" />
 <p className="text-sm text-gray-500 dark:text-gray-400">Analyzing trends...</p>
 </div>
 </div>
 );

 if (error || !data) return (
 <div className="min-h-screen bg-gray-50 dark:bg-surface-base flex flex-col items-center justify-center gap-4">
 <TrendingUp size={48} className="text-gray-300 dark:text-gray-600" />
 <p className="text-gray-500 dark:text-gray-400">{error || 'No data available'}</p>
 </div>
 );

 const maxCount = Math.max(...data.keywords.map(k => k.count), 1);
 const maxCat = Math.max(...data.categories.map(c => c.count), 1);
 const maxYear = Math.max(...data.years.map(y => y.count), 1);
 const top3 = data.keywords.slice(0, 3);

 return (
 <div className="min-h-screen bg-gray-50 dark:bg-surface-base transition-colors duration-300">

 {/* Hero Header */}
 <div className="relative overflow-hidden bg-gradient-to-br from-neural-500/5 via-cortex-500/5 to-dopamine-500/5 dark:from-neural-900/20 dark:via-cortex-900/20 dark:to-dopamine-900/20 border-b border-gray-200/50 dark:border-gray-800/50">
 <div className="absolute top-0 right-0 w-64 h-64 rounded-full bg-neural-500/10 blur-3xl" />
 <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full bg-cortex-500/10 blur-3xl" />
 <div className="relative container mx-auto px-6 py-10 max-w-6xl">
 <div className="flex items-start justify-between flex-wrap gap-4">
 <div>
 <div className="flex items-center gap-3 mb-4">
 <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
 <TrendingUp className="w-6 h-6 text-white" />
 </div>
 <NeuralBadge variant="neural" dot pulse>
 Trending
 </NeuralBadge>
 </div>
 <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 dark:text-white mb-2">
 Research Trends
 </h1>
 <p className="text-gray-600 dark:text-gray-400 max-w-2xl">
 Analyzed from <span className="font-semibold text-neural-600 dark:text-neural-400">{data.total_documents}</span> documents in library
 </p>
 </div>
 <div className="flex items-center gap-2">
 <span className="text-[11px] font-semibold px-3 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-800 flex items-center gap-1.5">
 <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
 Real-time
 </span>
 <span className="text-[11px] font-semibold px-3 py-1.5 rounded-full bg-cortex-50 dark:bg-cortex-900/30 text-cortex-600 dark:text-cortex-400 border border-cortex-100 dark:border-cortex-800 flex items-center gap-1.5">
 <Sparkles size={10} />
 AI Contextualized
 </span>
 </div>
 </div>
 </div>
 </div>

 {/* Main Content */}
 <div className="container mx-auto px-6 py-8 max-w-6xl space-y-8">

 {/* Two-column grid: Word cloud + Sidebar */}
 <div className="grid lg:grid-cols-3 gap-6">

 {/* Word cloud — 2/3 */}
 <FadeIn delay={0.1} className="lg:col-span-2">
 <NeuralCard variant="elevated" padding="lg">
 <div className="flex items-center justify-between mb-6">
 <div className="flex items-center gap-2">
 <Hash className="w-5 h-5 text-neural-500" />
 <span className="text-sm font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">Top Keywords</span>
 </div>
 <span className="text-xs text-gray-400">{data.keywords.length} keywords</span>
 </div>

 {data.keywords.length === 0 ? (
 <div className="py-16 text-center text-gray-400 dark:text-gray-500">
 <TrendingUp size={48} className="mx-auto mb-3 opacity-30" />
 <p className="text-sm">No data yet. Upload more documents to see trends.</p>
 </div>
 ) : (
 <div className="flex flex-wrap gap-3 items-center justify-center py-6 min-h-[240px]">
 {data.keywords.map((kw, i) => (
 <WordTag key={kw.word} word={kw.word} count={kw.count} maxCount={maxCount} index={i} />
 ))}
 </div>
 )}
 </NeuralCard>
 </FadeIn>

 {/* Right column — 1/3 */}
 <div className="space-y-4">

 {/* Emerging Pattern */}
 <FadeIn delay={0.15}>
 <NeuralCard variant="elevated" padding="md">
 <div className="flex items-center gap-2 mb-3">
 <Zap size={14} className="text-dopamine-500" />
 <span className="text-[11px] font-bold uppercase tracking-widest text-gray-500 dark:text-gray-400">Emerging Pattern</span>
 </div>
 <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
 {top3.length > 0
 ? `Research focus is increasing around the topic "${top3[0].word}"${top3[1] ? ` and "${top3[1].word}"` : ''}.`
 : 'Upload more documents to discover new trends.'}
 </p>
 </NeuralCard>
 </FadeIn>

 {/* AI Quick Analysis */}
 <FadeIn delay={0.2}>
 <NeuralCard variant="elevated" padding="md">
 <div className="flex items-center gap-2 mb-3">
 <Sparkles size={14} className="text-cortex-500" />
 <span className="text-[11px] font-bold uppercase tracking-widest text-gray-500 dark:text-gray-400">AI Quick Analysis</span>
 </div>
 <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
 {data.categories.length > 0
 ? `Category "${data.categories[0]?.name}" accounts for ${Math.round((data.categories[0]?.count / data.total_documents) * 100)}% of the document repository — the dominant research area.`
 : 'Analysis will appear when enough data is available.'}
 </p>
 </NeuralCard>
 </FadeIn>

 {/* Top 5 keywords list */}
 {data.keywords.length > 0 && (
 <FadeIn delay={0.25}>
 <NeuralCard variant="elevated" padding="md">
 <div className="flex items-center gap-2 mb-4">
 <Hash size={14} className="text-gray-400" />
 <span className="text-[11px] font-bold uppercase tracking-widest text-gray-500 dark:text-gray-400">Top Keywords</span>
 </div>
 <div className="space-y-3">
 {data.keywords.slice(0, 5).map((kw, i) => {
 const palette = WORD_PALETTE[i % WORD_PALETTE.length];
 return (
 <div key={kw.word} className="flex items-center gap-3">
 <span className="text-[11px] font-black w-5 text-center" style={{ color: palette.text }}>#{i + 1}</span>
 <span className="flex-1 text-sm font-semibold text-gray-700 dark:text-gray-200 truncate">{kw.word}</span>
 <span className="text-[11px] font-bold px-2 py-0.5 rounded-md" style={{ color: palette.text, background: palette.bg }}>
 {kw.count}
 </span>
 </div>
 );
 })}
 </div>
 </NeuralCard>
 </FadeIn>
 )}
 </div>
 </div>

 {/* Category + Year Distribution */}
 <div className="grid md:grid-cols-2 gap-6">

 {/* Category breakdown */}
 <FadeIn delay={0.2}>
 <NeuralCard variant="elevated" padding="lg">
 <div className="flex items-center gap-2 mb-6">
 <BarChart3 size={16} className="text-cortex-500" />
 <span className="text-sm font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">Category Distribution</span>
 </div>
 {data.categories.length === 0 ? (
 <p className="text-sm text-gray-400 text-center py-8">No categories yet</p>
 ) : (
 <div className="space-y-4">
 {data.categories.slice(0, 8).map((cat, i) => {
 const pct = (cat.count / maxCat) * 100;
 const color = WORD_PALETTE[i % WORD_PALETTE.length].text;
 return (
 <div key={cat.name}>
 <div className="flex justify-between text-sm mb-2">
 <span className="font-medium text-gray-700 dark:text-gray-200 truncate max-w-[180px]">{cat.name}</span>
 <span className="text-gray-400 font-semibold ml-2">{cat.count}</span>
 </div>
 <AnimBar pct={pct} color={color} delay={0.25 + i * 0.05} />
 </div>
 );
 })}
 </div>
 )}
 </NeuralCard>
 </FadeIn>

 {/* Year distribution */}
 <FadeIn delay={0.25}>
 <NeuralCard variant="elevated" padding="lg">
 <div className="flex items-center gap-2 mb-6">
 <Calendar size={16} className="text-neural-500" />
 <span className="text-sm font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">Distribution by Year</span>
 </div>
 {data.years.length === 0 ? (
 <p className="text-sm text-gray-400 text-center py-8">No year data available</p>
 ) : (
 <div className="flex items-end gap-2 h-48 pt-4">
 {data.years.slice(-14).map((yr, i) => {
 const pct = Math.max((yr.count / maxYear) * 100, 3);
 const ref = useRef<HTMLDivElement>(null);
 const seen = useInView(ref, { once: true });
 return (
 <div key={yr.year} ref={ref} className="flex-1 flex flex-col items-center gap-1.5 group">
 <motion.span
 initial={{ opacity: 0 }}
 animate={seen ? { opacity: 1 } : {}}
 transition={{ delay: i * 0.04 }}
 className="text-[10px] text-gray-400 font-semibold"
 >
 {yr.count}
 </motion.span>
 <div className="w-full h-36 flex items-end">
 <motion.div
 className="w-full rounded-t-lg group-hover:opacity-80 transition-opacity"
 style={{ background: 'linear-gradient(180deg, #0D9488, #14B8A6, #2DD4BF)' }}
 initial={{ height: 0 }}
 animate={seen ? { height: `${pct}%` } : {}}
 transition={{ duration: 0.6, delay: 0.3 + i * 0.04, ease: 'easeOut' }}
 />
 </div>
 <span className="text-[9px] text-gray-400 font-medium">{String(yr.year).slice(-2)}</span>
 </div>
 );
 })}
 </div>
 )}
 </NeuralCard>
 </FadeIn>
 </div>

 {/* Full keyword grid */}
 {data.keywords.length > 5 && (
 <FadeIn delay={0.3}>
 <NeuralCard variant="elevated" padding="lg">
 <div className="flex items-center gap-2 mb-6">
 <ArrowUp className="w-5 h-5 text-dopamine-500" />
 <span className="text-sm font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">Top 20 keywords</span>
 </div>
 <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-5 gap-3">
 {data.keywords.slice(0, 20).map((kw, i) => {
 const palette = WORD_PALETTE[i % WORD_PALETTE.length];
 return (
 <motion.div
 key={kw.word}
 initial={{ opacity: 0, y: 6 }}
 animate={{ opacity: 1, y: 0 }}
 transition={{ delay: 0.35 + i * 0.025 }}
 className="flex items-center gap-2.5 p-3 rounded-xl border border-gray-100 dark:border-gray-800 hover:border-gray-200 dark:hover:border-gray-700 transition-colors"
 style={{ background: palette.bg }}
 >
 <span className="text-[11px] font-black w-6 text-center" style={{ color: palette.text }}>
 #{i + 1}
 </span>
 <div className="flex-1 min-w-0">
 <p className="text-xs font-semibold text-gray-800 dark:text-gray-100 truncate">{kw.word}</p>
 <p className="text-[10px]" style={{ color: palette.text }}>{kw.count} times</p>
 </div>
 </motion.div>
 );
 })}
 </div>
 </NeuralCard>
 </FadeIn>
 )}
 </div>
 </div>
 );
}
