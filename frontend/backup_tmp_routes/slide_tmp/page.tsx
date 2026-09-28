'use client';

import { useEffect, useState } from 'react';
import { getDocuments, generateSlides } from '@/lib/api';
import type { DocumentInfo, SlideData } from '@/lib/api';
import { NeuralCard } from '@/components/ui/NeuralCard';
import { NeuralBadge } from '@/components/ui/NeuralBadge';
import { NeuralButton } from '@/components/ui/NeuralButton';
import { Presentation, FileText, Loader2, Sparkles, ChevronDown, ChevronRight, Download, Settings2, Wand2, BarChart3, BookOpen, Users, GraduationCap, Microscope } from 'lucide-react';

const STYLES = [
 { value: 'academic', label: 'Học thuật', icon: BookOpen, color: '#0D9488' },
 { value: 'conference', label: 'Hội nghị', icon: Users, color: '#7C3AED' },
 { value: 'thesis', label: 'Luận văn', icon: GraduationCap, color: '#F59E0B' },
 { value: 'seminar', label: 'Seminar', icon: Microscope, color: '#EC4899' },
];

const SLIDE_TYPE_COLORS: Record<string, { bg: string; border: string; icon: string }> = {
 title: { bg: 'from-indigo-500/10 to-blue-500/10', border: 'border-indigo-200 dark:border-indigo-800', icon: '#4F46E5' },
 background: { bg: 'from-sky-500/10 to-cyan-500/10', border: 'border-sky-200 dark:border-sky-800', icon: '#0EA5E9' },
 methodology: { bg: 'from-amber-500/10 to-orange-500/10', border: 'border-amber-200 dark:border-amber-800', icon: '#F59E0B' },
 results: { bg: 'from-emerald-500/10 to-green-500/10', border: 'border-emerald-200 dark:border-emerald-800', icon: '#10B981' },
 discussion: { bg: 'from-violet-500/10 to-purple-500/10', border: 'border-violet-200 dark:border-violet-800', icon: '#8B5CF6' },
 conclusion: { bg: 'from-teal-500/10 to-cyan-500/10', border: 'border-teal-200 dark:border-teal-800', icon: '#14B8A6' },
 default: { bg: 'from-gray-500/10 to-slate-500/10', border: 'border-gray-200 dark:border-gray-700', icon: '#6B7280' },
};

export default function SlidesPage() {
 const [docs, setDocs] = useState<DocumentInfo[]>([]);
 const [docId, setDocId] = useState('');
 const [numSlides, setNumSlides] = useState(8);
 const [style, setStyle] = useState('academic');
 const [result, setResult] = useState<SlideData | null>(null);
 const [loading, setLoading] = useState(false);
 const [error, setError] = useState('');
 const [expanded, setExpanded] = useState<number | null>(0);

 useEffect(() => {
 getDocuments().then(d => {
 const ready = d.filter(doc => doc.status === 'ready');
 setDocs(ready);
 if (ready.length > 0 && !docId) setDocId(ready[0].id);
 });
 }, []);

 const handleGenerate = async () => {
 if (!docId) return;
 setLoading(true); setError(''); setResult(null); setExpanded(0);
 try {
 const res = await generateSlides(docId, numSlides, style);
 setResult(res);
 } catch (e: unknown) {
 const err = e as { response?: { data?: { detail?: string } } };
 setError(err?.response?.data?.detail ?? 'Không thể tạo slide. Thử lại sau.');
 } finally {
 setLoading(false);
 }
 };

 const exportText = () => {
 if (!result) return;
 const lines: string[] = [`# ${result.title}`, `## ${result.subtitle}`, ''];
 result.slides.forEach(s => {
 lines.push(`### Slide ${s.number}: ${s.title} [${s.type}]`);
 s.bullets.forEach(b => lines.push(`- ${b}`));
 if (s.speaker_note) lines.push(`\n> ${s.speaker_note}`);
 lines.push('');
 });
 const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
 const url = URL.createObjectURL(blob);
 const a = document.createElement('a');
 a.href = url; a.download = `${result.title}.txt`; a.click();
 URL.revokeObjectURL(url);
 };

 const selectedDoc = docs.find(d => d.id === docId);
 const selectedStyle = STYLES.find(s => s.value === style) ?? STYLES[0];

 return (
 <div className="min-h-screen bg-gray-50 dark:bg-surface-base transition-colors duration-300">

 {/* Hero Header */}
 <div className="relative overflow-hidden bg-gradient-to-br from-orange-500/5 via-amber-500/5 to-dopamine-500/5 dark:from-orange-900/20 dark:via-amber-900/20 dark:to-dopamine-900/20 border-b border-gray-200/50 dark:border-gray-800/50">
 <div className="absolute top-0 right-0 w-64 h-64 rounded-full bg-orange-500/10 blur-3xl" />
 <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full bg-amber-500/10 blur-3xl" />
 <div className="relative container mx-auto px-6 py-10 max-w-5xl">
 <div className="flex items-center gap-3 mb-4">
 <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-orange-500 to-amber-500 flex items-center justify-center shadow-lg shadow-orange-500/20">
 <Presentation className="w-6 h-6 text-white" />
 </div>
 <NeuralBadge variant="cortex" dot pulse>
 Tạo Slide
 </NeuralBadge>
 </div>
 <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 dark:text-white mb-2">
 Tạo Slide Thuyết trình
 </h1>
 <p className="text-gray-600 dark:text-gray-400 max-w-2xl">
 AI tự động tạo slide từ tài liệu nghiên cứu. Chọn phong cách và số lượng slide phù hợp.
 </p>
 </div>
 </div>

 <div className="container mx-auto px-6 py-8 max-w-5xl space-y-8">

 {/* Controls */}
 <NeuralCard variant="elevated" padding="lg">
 <div className="flex items-center gap-3 mb-6">
 <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-amber-500 flex items-center justify-center">
 <Settings2 className="w-5 h-5 text-white" />
 </div>
 <div>
 <h2 className="font-bold text-gray-900 dark:text-white">Cấu hình slide</h2>
 <p className="text-xs text-gray-500">Thiết lập tài liệu nguồn và phong cách</p>
 </div>
 </div>

 {/* Document select */}
 <div className="space-y-3 mb-6">
 <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-200">
 <FileText className="w-4 h-4 text-gray-400" />
 Tài liệu nguồn
 </label>
 {docs.length === 0 ? (
 <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800">
 <p className="text-sm text-amber-700 dark:text-amber-400">Chưa có tài liệu nào sẵn sàng. Hãy upload PDF trước.</p>
 </div>
 ) : (
 <select
 value={docId}
 onChange={e => setDocId(e.target.value)}
 className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-orange-500/50 transition-all cursor-pointer"
 >
 {docs.map(d => (
 <option key={d.id} value={d.id}>{d.title || d.filename}</option>
 ))}
 </select>
 )}
 </div>

 <div className="grid md:grid-cols-2 gap-6 mb-6">
 {/* Num slides */}
 <div className="space-y-3">
 <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-200">
 <BarChart3 className="w-4 h-4 text-gray-400" />
 Số lượng slide: <span className="text-orange-500 font-bold">{numSlides}</span>
 </label>
 <div className="relative">
 <input
 type="range"
 min={5} max={15} value={numSlides}
 onChange={e => setNumSlides(Number(e.target.value))}
 className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-orange-500"
 />
 <div className="flex justify-between text-xs text-gray-400 mt-2">
 <span>5 (tóm tắt)</span>
 <span>15 (chi tiết)</span>
 </div>
 </div>
 </div>

 {/* Style */}
 <div className="space-y-3">
 <label className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-200">
 <Wand2 className="w-4 h-4 text-gray-400" />
 Phong cách
 </label>
 <div className="grid grid-cols-2 gap-2">
 {STYLES.map(s => (
 <button
 key={s.value}
 onClick={() => setStyle(s.value)}
 className={`flex items-center gap-2 text-xs px-3 py-2.5 rounded-xl font-medium transition-all border ${
 style === s.value
 ? 'border-2 shadow-lg'
 : 'border border-gray-200 dark:border-gray-700 hover:border-gray-300'
 }`}
 style={style === s.value ? {
 background: `${s.color}15`,
 borderColor: s.color,
 color: s.color,
 boxShadow: `0 4px 12px ${s.color}20`
 } : {
 color: '#6B7280'
 }}
 >
 <span className="w-5 h-5 rounded-lg flex items-center justify-center text-[10px]" style={style === s.value ? { background: s.color, color: 'white' } : {}}>
 {s.label[0]}
 </span>
 {s.label}
 </button>
 ))}
 </div>
 </div>
 </div>

 {error && (
 <div className="mb-4 p-3 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800">
 <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
 </div>
 )}

 <button
 onClick={handleGenerate}
 disabled={!docId || loading}
 className="w-full flex items-center justify-center gap-3 py-3.5 rounded-xl font-semibold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 hover:shadow-xl hover:shadow-orange-500/25 text-white"
 >
 {loading ? (
 <>
 <Loader2 className="w-5 h-5 animate-spin" /> Đang tạo slide...
 </>
 ) : (
 <>
 <Sparkles className="w-5 h-5" /> Tạo {numSlides} slides ({selectedStyle.label})
 </>
 )}
 </button>
 </NeuralCard>

 {/* Result */}
 {result && (
 <div className="space-y-6">
 {/* Header */}
 <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-orange-500 via-amber-500 to-orange-400 p-8 text-white shadow-xl shadow-orange-500/20">
 <div className="absolute top-0 right-0 w-64 h-64 rounded-full bg-white/10 blur-3xl" />
 <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full bg-white/10 blur-3xl" />
 <div className="relative flex items-start justify-between gap-4">
 <div>
 <div className="flex items-center gap-2 mb-3">
 <FileText className="w-4 h-4 opacity-75" />
 <span className="text-xs opacity-75 truncate max-w-[300px]">{selectedDoc?.title || selectedDoc?.filename}</span>
 </div>
 <h2 className="text-2xl md:text-3xl font-bold mb-2">{result.title}</h2>
 <p className="text-sm opacity-90 mb-4">{result.subtitle}</p>
 <div className="flex items-center gap-3 text-xs opacity-75">
 <span className="px-2 py-1 rounded-lg bg-white/20">{result.slides.length} slides</span>
 <span className="px-2 py-1 rounded-lg bg-white/20 capitalize">{style}</span>
 </div>
 </div>
 <button
 onClick={exportText}
 className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/20 hover:bg-white/30 text-sm font-medium transition-colors flex-shrink-0 backdrop-blur-sm border border-white/20"
 >
 <Download className="w-4 h-4" /> Xuất TXT
 </button>
 </div>
 </div>

 {/* Slides */}
 <div className="space-y-3">
 {result.slides.map((slide, i) => {
 const colorConfig = SLIDE_TYPE_COLORS[slide.type] ?? SLIDE_TYPE_COLORS.default;
 const isOpen = expanded === i;
 return (
 <NeuralCard
 key={slide.number}
 variant="elevated"
 padding="none"
 className="overflow-hidden border-l-4"
 style={{ borderLeftColor: colorConfig.icon }}
 >
 <button
 className="w-full flex items-center gap-4 px-5 py-4 text-left hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
 onClick={() => setExpanded(isOpen ? null : i)}
 >
 <div className="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold text-white flex-shrink-0"
 style={{ background: `linear-gradient(135deg, ${colorConfig.icon}, ${colorConfig.icon}80)` }}>
 {slide.number}
 </div>
 <div className="flex-1 min-w-0">
 <p className="font-semibold text-gray-900 dark:text-white">{slide.title}</p>
 <div className="flex items-center gap-3 mt-1">
 <span className="text-xs px-2 py-0.5 rounded-md capitalize" style={{ background: `${colorConfig.icon}15`, color: colorConfig.icon }}>
 {slide.type}
 </span>
 <span className="text-xs text-gray-400">{slide.bullets.length} điểm</span>
 </div>
 </div>
 {isOpen ? (
 <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
 ) : (
 <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
 )}
 </button>

 {isOpen && (
 <div className="px-5 pb-5 border-t border-gray-100 dark:border-gray-800 pt-4">
 <ul className="space-y-2.5 mb-4">
 {slide.bullets.map((b, j) => (
 <li key={j} className="flex items-start gap-3 text-sm text-gray-700 dark:text-gray-200">
 <div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0" style={{ background: colorConfig.icon }} />
 {b}
 </li>
 ))}
 </ul>
 {slide.speaker_note && (
 <div className="p-3 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800">
 <p className="text-xs text-gray-500 dark:text-gray-400">
 <span className="font-semibold not-italic">📝 Ghi chú: </span>
 {slide.speaker_note}
 </p>
 </div>
 )}
 </div>
 )}
 </NeuralCard>
 );
 })}
 </div>
 </div>
 )}
 </div>
 </div>
 );
}