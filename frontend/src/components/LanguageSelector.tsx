'use client';

import { useState, useRef, useEffect } from 'react';
import { useI18n } from '@/lib/i18n/context';
import type { Locale } from '@/lib/i18n';

export default function LanguageSelector() {
 const { locale, setLocale, locales } = useI18n();
 const [open, setOpen] = useState(false);
 const ref = useRef<HTMLDivElement>(null);

 const current = locales.find(l => l.code === locale) ?? locales[0];

 useEffect(() => {
 const handler = (e: MouseEvent) => {
 if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
 };
 document.addEventListener('mousedown', handler);
 return () => document.removeEventListener('mousedown', handler);
 }, []);

 return (
 <div ref={ref} className="relative">
 <button
 onClick={() => setOpen(p => !p)}
 className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-800/60 dark:hover:bg-gray-700 transition-colors text-slate-600 dark:text-slate-300 font-medium"
 title="Select Language"
 >
 <span className="text-base leading-none">{current.flag}</span>
 <span className="hidden sm:inline">{current.label}</span>
 </button>

 {open && (
 <div className="absolute right-0 mt-1.5 w-44 bg-white dark:bg-slate-800/60 rounded-xl shadow-xl border border-slate-200 dark:border-slate-700 overflow-hidden z-50 py-1">
 {locales.map(l => (
 <button
 key={l.code}
 onClick={() => { setLocale(l.code as Locale); setOpen(false); }}
 className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left transition-colors ${
 locale === l.code
 ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 font-medium'
 : 'text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/60 dark:hover:bg-gray-800'
 }`}
 >
 <span className="text-base">{l.flag}</span>
 <span>{l.label}</span>
 {locale === l.code && <span className="ml-auto text-indigo-500">✓</span>}
 </button>
 ))}
 </div>
 )}
 </div>
 );
}
