'use client';

import { useEffect, useState, useRef } from 'react';
import { getDocuments } from '@/lib/api';
import type { DocumentInfo } from '@/lib/api';
import { motion, useInView } from 'framer-motion';
import { Timer, FileText, ChevronRight, Search, Clock, TrendingUp, BookOpen } from 'lucide-react';
import Link from 'next/link';

function FadeIn({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
 const ref = useRef<HTMLDivElement>(null);
 const inView = useInView(ref, { once: true, margin: '-60px' });
 return (
 <motion.div
 ref={ref}
 initial={{ opacity: 0, y: 28 }}
 animate={inView ? { opacity: 1, y: 0 } : {}}
 transition={{ duration: 0.55, delay, ease: [0.25, 0.46, 0.45, 0.94] }}
 >
 {children}
 </motion.div>
 );
}

function YearNode({ year, count }: { year: string; count: number }) {
 const ref = useRef<HTMLDivElement>(null);
 const inView = useInView(ref, { once: true, margin: '-40px' });
 const isUnknown = year === 'Unknown year';

 return (
 <motion.div
 ref={ref}
 initial={{ opacity: 0, scale: 0.7 }}
 animate={inView ? { opacity: 1, scale: 1 } : {}}
 transition={{ duration: 0.4, type: 'spring', stiffness: 200, damping: 18 }}
 className="flex flex-col items-center gap-1.5 w-[88px] flex-shrink-0"
 >
 <div className={`
 w-[72px] h-[72px] rounded-2xl flex items-center justify-center
 border-2 shadow-lg
 ${isUnknown
 ? 'border-slate-200 bg-slate-50 shadow-slate-100'
 : 'border-transparent bg-gradient-to-br from-blue-500 to-violet-600 shadow-blue-200'}
 `}>
 <span className={`font-bold text-sm leading-tight text-center ${isUnknown ? 'text-slate-400' : 'text-white'}`}>
 {isUnknown ? '?' : year}
 </span>
 </div>
 <span className="text-[11px] text-slate-400 font-medium">{count} articles</span>
 </motion.div>
 );
}

function DocCard({ doc, index }: { doc: DocumentInfo; index: number }) {
 const ref = useRef<HTMLAnchorElement>(null);
 const inView = useInView(ref, { once: true, margin: '-30px' });

 const statusStyle =
 doc.status === 'ready'
 ? 'bg-emerald-50 text-emerald-600'
 : doc.status === 'error'
 ? 'bg-red-50 text-red-500'
 : 'bg-amber-50 text-amber-600';

 return (
 <motion.a
 ref={ref as React.Ref<HTMLAnchorElement>}
 href={`/chat?doc=${doc.id}`}
 initial={{ opacity: 0, x: 20 }}
 animate={inView ? { opacity: 1, x: 0 } : {}}
 transition={{ duration: 0.45, delay: index * 0.06, ease: [0.25, 0.46, 0.45, 0.94] }}
 whileHover={{ y: -2 }}
 className="flex items-start gap-3 p-4 bg-white dark:bg-slate-800/60 rounded-xl border border-slate-100 hover:border-blue-200 hover:shadow-md hover:shadow-blue-50 transition-all group cursor-pointer"
 >
 <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0 mt-0.5 group-hover:bg-blue-100 transition-colors">
 <FileText className="w-4 h-4 text-blue-500" />
 </div>

 <div className="flex-1 min-w-0">
 <p className="text-sm font-semibold text-slate-800 group-hover:text-blue-600 transition-colors line-clamp-2 leading-snug">
 {doc.title || doc.filename}
 </p>
 <div className="flex items-center gap-2 mt-1.5 flex-wrap">
 {doc.authors && (
 <span className="text-xs text-slate-400 truncate max-w-[180px]">{doc.authors}</span>
 )}
 {doc.category && (
 <span className="text-[11px] px-2 py-0.5 rounded-full bg-violet-50 text-violet-600 font-medium">
 {doc.category}
 </span>
 )}
 <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${statusStyle}`}>
 {doc.status}
 </span>
 </div>
 </div>

 <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-blue-400 group-hover:translate-x-0.5 transition-all flex-shrink-0 mt-1" />
 </motion.a>
 );
}

export default function TimelinePage() {
 const [docs, setDocs] = useState<DocumentInfo[]>([]);
 const [loading, setLoading] = useState(true);
 const [search, setSearch] = useState('');

 useEffect(() => {
 getDocuments().then(setDocs).finally(() => setLoading(false));
 }, []);

 const q = search.toLowerCase();
 const filtered = docs.filter(d =>
 !q ||
 (d.title ?? '').toLowerCase().includes(q) ||
 (d.authors ?? '').toLowerCase().includes(q)
 );

 const grouped: Record<string, DocumentInfo[]> = {};
 filtered.forEach(d => {
 const yr = d.year ? String(d.year) : 'Unknown year';
 grouped[yr] = [...(grouped[yr] ?? []), d];
 });
 const years = Object.keys(grouped).sort((a, b) => {
 if (a === 'Unknown year') return 1;
 if (b === 'Unknown year') return -1;
 return Number(b) - Number(a);
 });

 const yearRange = years.filter(y => y !== 'Unknown year');
 const spanLabel = yearRange.length >= 2
 ? `${yearRange[yearRange.length - 1]} – ${yearRange[0]}`
 : yearRange[0] ?? '';

 return (
 <div className="min-h-full bg-[#FAF9F6] dark:bg-[#070A13] transition-colors duration-500">
 <div className="max-w-3xl mx-auto px-6 py-8 space-y-8">

 {/* ── Header ──────────────────────────────────────────────────────────── */}
 <FadeIn>
 <div className="flex items-start justify-between flex-wrap gap-4">
 <div>
 <div className="flex items-center gap-2 mb-2">
 <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-blue-50 text-blue-600 border border-blue-100 uppercase tracking-wide">
 Chronological
 </span>
 <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-violet-50 text-violet-600 border border-violet-100 uppercase tracking-wide">
 AI Indexed
 </span>
 </div>
 <h1 className="text-2xl font-bold text-slate-800 tracking-tight">
 Research Evolution Timeline
 </h1>
 <p className="text-sm text-slate-500 mt-1">
 {loading ? '...' : `${filtered.length} documents`}
 {spanLabel && !loading && (
 <span className="ml-2 text-slate-400">· {spanLabel}</span>
 )}
 </p>
 </div>

 {/* Stats */}
 {!loading && docs.length > 0 && (
 <div className="flex gap-3">
 {[
 { icon: BookOpen, label: 'Documents', value: docs.length },
 { icon: TrendingUp, label: 'Years', value: yearRange.length },
 ].map(({ icon: Icon, label, value }) => (
 <div key={label} className="bg-white dark:bg-slate-800/60 rounded-xl border border-slate-100 px-4 py-3 text-center min-w-[72px] shadow-sm">
 <div className="text-xl font-bold text-slate-800">{value}</div>
 <div className="text-[11px] text-slate-400 font-medium mt-0.5">{label}</div>
 </div>
 ))}
 </div>
 )}
 </div>
 </FadeIn>

 {/* ── Search ──────────────────────────────────────────────────────────── */}
 <FadeIn delay={0.05}>
 <div className="relative">
 <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
 <input
 value={search}
 onChange={e => setSearch(e.target.value)}
 placeholder="Search documents, authors..."
 className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 bg-white dark:bg-slate-800/60 text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-300 shadow-sm transition-all"
 />
 </div>
 </FadeIn>

 {/* ── Content ─────────────────────────────────────────────────────────── */}
 {loading ? (
 <div className="space-y-8">
 {Array.from({ length: 3 }).map((_, i) => (
 <div key={i} className="flex gap-6">
 <div className="w-[72px] h-[72px] rounded-2xl bg-slate-100 animate-pulse flex-shrink-0" />
 <div className="flex-1 space-y-3 pt-2">
 {Array.from({ length: 2 }).map((_, j) => (
 <div key={j} className="h-20 bg-slate-100 rounded-xl animate-pulse" />
 ))}
 </div>
 </div>
 ))}
 </div>
 ) : years.length === 0 ? (
 <FadeIn delay={0.1}>
 <div className="text-center py-20 bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-100 shadow-sm">
 <div className="w-14 h-14 rounded-2xl bg-blue-50 flex items-center justify-center mx-auto mb-4">
 <Clock className="w-7 h-7 text-blue-400" />
 </div>
 <h3 className="font-semibold text-slate-700 mb-1">No documents yet</h3>
 <p className="text-sm text-slate-400 mb-4">Upload PDFs to build your research timeline.</p>
 <Link
 href="/library/upload"
 className="inline-flex items-center gap-2 text-sm font-medium text-blue-500 hover:text-blue-600 transition-colors"
 >
 Upload PDF →
 </Link>
 </div>
 </FadeIn>
 ) : (
 <div className="relative">
 {/* Vertical connecting line */}
 <div className="absolute left-[35px] top-8 bottom-8 w-0.5 bg-gradient-to-b from-blue-300 via-violet-200 to-transparent" />

 <div className="space-y-10">
 {years.map((yr, yIdx) => (
 <FadeIn key={yr} delay={yIdx * 0.04}>
 <div className="flex gap-6">
 <YearNode year={yr} count={grouped[yr].length} />
 <div className="flex-1 space-y-2.5 pt-2">
 {grouped[yr].map((doc, dIdx) => (
 <DocCard key={doc.id} doc={doc} index={dIdx} />
 ))}
 </div>
 </div>
 </FadeIn>
 ))}
 </div>
 </div>
 )}

 {/* ── Bottom insight ───────────────────────────────────────────────────── */}
 {!loading && filtered.length > 0 && (
 <FadeIn delay={0.1}>
 <div className="bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-100 shadow-sm p-5">
 <div className="flex items-center gap-2 mb-3">
 <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
 <Timer className="w-3.5 h-3.5 text-white" />
 </div>
 <span className="text-sm font-semibold text-slate-700">Timeline Summary</span>
 </div>
 <p className="text-sm text-slate-500 leading-relaxed">
 {yearRange.length > 1
 ? `Your knowledge base spans ${yearRange.length} years of research (${yearRange[yearRange.length - 1]}–${yearRange[0]}), with ${docs.length} documents across ${Object.keys(grouped).length} time periods.`
 : `${docs.length} documents indexed in your knowledge base.`}
 </p>
 </div>
 </FadeIn>
 )}

 </div>
 </div>
 );
}
