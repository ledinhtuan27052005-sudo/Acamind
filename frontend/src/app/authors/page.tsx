'use client';

import { useEffect, useState, useCallback } from 'react';
import { useAppStore } from '@/store/useAppStore';
import { getAuthors, getAuthorDetail, Author, AuthorDetail, LibraryArticle } from '@/lib/api';
import { Users, Search, BookOpen, Globe, Calendar, X, ExternalLink, ChevronRight, RefreshCw } from 'lucide-react';
import Link from 'next/link';

// ── Helpers ────────────────────────────────────────────────────────────────────

function LangBadge({ lang }: { lang: string }) {
 return lang === 'en'
 ? <span className="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300">🇬🇧 EN</span>
 : <span className="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-300">🇻🇳 VI</span>;
}

function getInitials(name: string) {
 const parts = name.trim().split(/\s+/);
 if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
 return name.slice(0, 2).toUpperCase();
}

const AVATAR_COLORS = [
 'from-indigo-400 to-violet-500',
 'from-blue-400 to-cyan-500',
 'from-emerald-400 to-teal-500',
 'from-amber-400 to-orange-500',
 'from-sky-400 to-rose-500',
 'from-violet-400 to-purple-500',
];
function avatarColor(name: string) {
 const code = name.charCodeAt(0) + (name.charCodeAt(1) || 0);
 return AVATAR_COLORS[code % AVATAR_COLORS.length];
}

// ── Author card ────────────────────────────────────────────────────────────────

function AuthorCard({ author, onClick }: { author: Author; onClick: () => void }) {
 const initials = getInitials(author.name);
 const gradient = avatarColor(author.name);
 return (
 <button
 onClick={onClick}
 className="group text-left bg-white dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700 p-5 hover:border-indigo-300 dark:hover:border-indigo-700 hover:shadow-md transition-all"
 >
 <div className="flex items-start gap-4">
 {/* Avatar */}
 <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${gradient} flex items-center justify-center text-white font-bold text-base flex-shrink-0`}>
 {initials}
 </div>
 {/* Info */}
 <div className="flex-1 min-w-0">
 <p className="font-semibold text-slate-900 dark:text-slate-100 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors truncate">
 {author.name}
 </p>
 <div className="flex items-center gap-2 mt-1 flex-wrap">
 <span className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
 <BookOpen className="w-3 h-3" /> {author.article_count} articles
 </span>
 {author.year_range && (
 <span className="flex items-center gap-1 text-xs text-slate-400 dark:text-slate-500">
 <Calendar className="w-3 h-3" /> {author.year_range[0]}–{author.year_range[1]}
 </span>
 )}
 </div>
 <div className="flex gap-1 mt-2">
 {author.languages.map(l => <LangBadge key={l} lang={l} />)}
 </div>
 </div>
 <ChevronRight className="w-4 h-4 text-slate-300 dark:text-slate-600 group-hover:text-indigo-400 transition-colors flex-shrink-0 mt-1" />
 </div>
 {/* Article previews */}
 {author.articles.slice(0, 2).map(art => (
 <p key={art.id} className="mt-2 text-xs text-slate-400 dark:text-slate-500 truncate">
 {art.cover_emoji && <span className="mr-1">{art.cover_emoji}</span>}
 {art.title_vi || art.title_original}
 </p>
 ))}
 </button>
 );
}

// ── Detail modal ───────────────────────────────────────────────────────────────

function DetailModal({ slug, onClose }: { slug: string; onClose: () => void }) {
 const [detail, setDetail] = useState<AuthorDetail | null>(null);
 const [loading, setLoading] = useState(true);

 useEffect(() => {
 getAuthorDetail(slug).then(setDetail).finally(() => setLoading(false));
 }, [slug]);

 return (
 <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
 <div className="bg-white dark:bg-slate-800/60 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden">
 {/* Header */}
 <div className="flex items-center justify-between p-6 border-b border-slate-100 dark:border-slate-800">
 {detail ? (
 <div className="flex items-center gap-3">
 <div className={`w-11 h-11 rounded-full bg-gradient-to-br ${avatarColor(detail.name)} flex items-center justify-center text-white font-bold`}>
 {getInitials(detail.name)}
 </div>
 <div>
 <h2 className="font-bold text-slate-900 dark:text-slate-100 dark:text-white">{detail.name}</h2>
 <p className="text-xs text-slate-500 dark:text-slate-400">{detail.articles.length} articles in the system</p>
 </div>
 </div>
 ) : (
 <div className="h-11 w-48 bg-slate-100 dark:bg-slate-800/60 rounded-lg animate-pulse" />
 )}
 <button onClick={onClose} className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 dark:hover:bg-gray-800 transition-colors">
 <X className="w-4 h-4 text-slate-500 dark:text-slate-400" />
 </button>
 </div>

 {/* Body */}
 <div className="overflow-y-auto p-6 space-y-3 flex-1">
 {loading ? (
 Array.from({ length: 4 }).map((_, i) => (
 <div key={i} className="h-16 bg-slate-100 dark:bg-slate-800/60 rounded-lg animate-pulse" />
 ))
 ) : detail?.articles.length === 0 ? (
 <p className="text-center text-slate-400 dark:text-slate-500 py-8">No articles in the system</p>
 ) : (
 detail?.articles.map((art: LibraryArticle) => (
 <div key={art.id} className="flex items-start gap-3 p-3 rounded-lg border border-slate-100 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800/60 dark:hover:bg-gray-800/50 transition-colors">
 <span className="text-xl flex-shrink-0">{art.cover_emoji || '📄'}</span>
 <div className="flex-1 min-w-0">
 <p className="text-sm font-medium text-slate-900 dark:text-slate-100 dark:text-white line-clamp-2">
 {art.title_vi || art.title_original}
 </p>
 <div className="flex items-center gap-2 mt-1">
 <LangBadge lang={art.language} />
 {art.year && <span className="text-xs text-slate-400 dark:text-slate-500">{art.year}</span>}
 {art.journal && <span className="text-xs text-slate-400 dark:text-slate-500 truncate">· {art.journal}</span>}
 {art.is_paywall && (
 <span className="text-xs px-1.5 py-0.5 rounded bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-300">Paywall</span>
 )}
 </div>
 </div>
 <Link
 href="/thu-vien"
 className="p-1.5 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/20 dark:hover:bg-indigo-900/20 text-indigo-400 hover:text-indigo-600 transition-colors flex-shrink-0"
 >
 <ExternalLink className="w-3.5 h-3.5" />
 </Link>
 </div>
 ))
 )}
 </div>

 <div className="p-4 border-t border-slate-100 dark:border-slate-800">
 <Link
 href="/thu-vien"
 className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 text-sm font-medium hover:bg-indigo-100 dark:hover:bg-indigo-900/40 transition-colors"
 >
 <BookOpen className="w-4 h-4" /> View Synthesized Library
 </Link>
 </div>
 </div>
 </div>
 );
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function AuthorsPage() {
 const { user } = useAppStore();

 const [authors, setAuthors] = useState<Author[]>([]);
 const [total, setTotal] = useState(0);
 const [loading, setLoading] = useState(true);
 const [search, setSearch] = useState('');
 const [langFilter, setLangFilter] = useState<'all' | 'en' | 'vi'>('all');
 const [selected, setSelected] = useState<string | null>(null);

 const load = useCallback(async (q = '') => {
 setLoading(true);
 try {
 const res = await getAuthors(q || undefined);
 setAuthors(res.authors);
 setTotal(res.total);
 } finally {
 setLoading(false);
 }
 }, []);

 useEffect(() => { load(); }, [load]);

 // Debounce search
 useEffect(() => {
 const t = setTimeout(() => load(search), 400);
 return () => clearTimeout(t);
 }, [search, load]);

 const filtered = langFilter === 'all'
 ? authors
 : authors.filter(a => a.languages.includes(langFilter));

 return (
 <div className="p-6 max-w-7xl mx-auto space-y-6">
 {/* Header */}
 <div className="flex items-start justify-between flex-wrap gap-4">
 <div>
 <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 dark:text-white flex items-center gap-2">
 <Users className="w-6 h-6 text-indigo-500" /> Author Lookup
 </h1>
 <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
 {total} authors from the Synthesized Library
 </p>
 </div>
 <Link
 href="/thu-vien"
 className="flex items-center gap-2 text-sm text-indigo-500 hover:text-indigo-700 dark:hover:text-indigo-300 transition-colors"
 >
 <BookOpen className="w-4 h-4" /> Synthesized Library
 </Link>
 </div>

 {/* Filters */}
 <div className="flex flex-wrap gap-3">
 <div className="relative flex-1 min-w-60">
 <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500 pointer-events-none" />
 <input
 value={search}
 onChange={e => setSearch(e.target.value)}
 placeholder="Search by author name..."
 className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300/50 placeholder-slate-400 dark:placeholder-slate-500"
 />
 </div>
 <div className="flex gap-2">
 {(['all', 'en', 'vi'] as const).map(l => (
 <button
 key={l}
 onClick={() => setLangFilter(l)}
 className={`flex items-center gap-1.5 text-xs px-3 py-2 rounded-lg border font-medium transition-all ${
 langFilter === l
 ? 'bg-indigo-50 dark:bg-indigo-900/30 border-indigo-300 dark:border-indigo-700 text-indigo-600 dark:text-indigo-400'
 : 'bg-white dark:bg-slate-800/60 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:border-gray-300'
 }`}
 >
 {l === 'all' ? <><Globe className="w-3.5 h-3.5" /> All</> : l === 'en' ? '🇬🇧 EN' : '🇻🇳 VI'}
 </button>
 ))}
 </div>
 </div>

 {/* Stats bar */}
 {!loading && (
 <div className="grid grid-cols-3 gap-4">
 {[
 { label: 'Total Authors', value: total },
 { label: 'English Authors', value: authors.filter(a => a.languages.includes('en')).length },
 { label: 'Vietnamese Authors', value: authors.filter(a => a.languages.includes('vi')).length },
 ].map(s => (
 <div key={s.label} className="bg-white dark:bg-slate-800/60 rounded-lg border border-slate-200 dark:border-slate-700 p-4 text-center">
 <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{s.value}</p>
 <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{s.label}</p>
 </div>
 ))}
 </div>
 )}

 {/* Grid */}
 {loading ? (
 <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
 {Array.from({ length: 6 }).map((_, i) => (
 <div key={i} className="h-32 bg-slate-100 dark:bg-slate-800/60 rounded-xl animate-pulse" />
 ))}
 </div>
 ) : filtered.length === 0 ? (
 <div className="text-center py-16">
 <Users className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
 <p className="text-slate-500 dark:text-slate-400">
 {search ? `No matching authors for "${search}"` : 'No authors yet. Please seed the library first.'}
 </p>
 {!search && user?.role === 'admin' && (
 <Link href="/thu-vien" className="mt-3 inline-flex items-center gap-2 text-sm text-indigo-500 hover:underline">
 Go to Library to seed documents →
 </Link>
 )}
 </div>
 ) : (
 <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
 {filtered.map(author => (
 <AuthorCard
 key={author.slug}
 author={author}
 onClick={() => setSelected(author.slug)}
 />
 ))}
 </div>
 )}

 {/* Detail modal */}
 {selected && (
 <DetailModal slug={selected} onClose={() => setSelected(null)} />
 )}
 </div>
 );
}
