'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/store/useAppStore';
import {
 adminGetPlanLimits, adminGetSystemInfo,
 adminUpdateSettings, adminGetSettings,
 SystemInfo,
} from '@/lib/api';
import { Crown, TrendingUp, ArrowLeft, RefreshCw, Edit2, Check, X, AlertCircle } from 'lucide-react';
import Link from 'next/link';

interface PlanLimit {
 label: string;
 max_docs: number | null;
 max_monthly_docs: number | null;
 max_monthly_chat: number | null;
 price_vnd: number;
 features: string[];
}

const PLAN_COLORS: Record<string, { bg: string; text: string; border: string; ring: string }> = {
 free: { bg: 'bg-slate-50 dark:bg-slate-800/40/50', text: 'text-slate-700 dark:text-slate-200', border: 'border-slate-200 dark:border-slate-700', ring: 'ring-gray-200' },
 pro: { bg: 'bg-indigo-50 dark:bg-indigo-900/20', text: 'text-indigo-700 dark:text-indigo-300', border: 'border-indigo-200 dark:border-indigo-800', ring: 'ring-indigo-300' },
 researcher: { bg: 'bg-violet-50 dark:bg-violet-900/20', text: 'text-violet-700 dark:text-violet-300', border: 'border-violet-200 dark:border-violet-800', ring: 'ring-violet-300' },
 enterprise: { bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-700 dark:text-amber-300', border: 'border-amber-200 dark:border-amber-800', ring: 'ring-amber-300' },
};

function fmt(n: number) {
 return n.toLocaleString('en-US') + ' VND';
}

function fmtRevenue(price: number, users: number) {
 const est = price * users;
 if (est === 0) return '—';
 return (est / 1_000_000).toFixed(1) + 'M VND/month';
}

export default function AdminPlansPage() {
 const { user } = useAppStore();
 const router = useRouter();

 // eslint-disable-next-line @typescript-eslint/no-explicit-any
 const [plans, setPlans] = useState<Record<string, any>>({});
 const [info, setInfo] = useState<SystemInfo | null>(null);
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState('');

 const [editKey, setEditKey] = useState<string | null>(null);
 const [editNote, setEditNote] = useState('');
 const [planNotes, setPlanNotes] = useState<Record<string, string>>({});
 const [saving, setSaving] = useState(false);

 useEffect(() => {
 if (!user) { router.push('/login'); return; }
 if (user.role !== 'admin') { router.push('/'); return; }
 load();
 }, [user]);

 async function load() {
 setLoading(true); setError('');
 try {
 const [plansRes, infoRes, settingsRes] = await Promise.all([
 adminGetPlanLimits(),
 adminGetSystemInfo(),
 adminGetSettings(),
 ]);
 setPlans(plansRes);
 setInfo(infoRes);
 const notes: Record<string, string> = {};
 for (const key of ['plan_note_free', 'plan_note_pro', 'plan_note_researcher', 'plan_note_enterprise']) {
 const planKey = key.replace('plan_note_', '');
 notes[planKey] = (settingsRes as Record<string, { value: string }>)[key]?.value ?? '';
 }
 setPlanNotes(notes);
 } catch (e: unknown) {
 const err = e as { response?: { data?: { detail?: string } } };
 setError(err?.response?.data?.detail ?? 'Failed to load data');
 } finally {
 setLoading(false);
 }
 }

 async function saveNote(planKey: string) {
 setSaving(true);
 try {
 await adminUpdateSettings({ [`plan_note_${planKey}`]: editNote });
 setPlanNotes(prev => ({ ...prev, [planKey]: editNote }));
 setEditKey(null);
 } finally {
 setSaving(false);
 }
 }

 if (loading) return (
 <div className="flex items-center justify-center h-64">
 <RefreshCw className="w-6 h-6 animate-spin text-indigo-500" />
 </div>
 );

 const planOrder = ['free', 'pro', 'researcher', 'enterprise'];
 const breakdown: Record<string, number> = info?.plan_breakdown ?? {};

 return (
 <div className="p-6 max-w-7xl mx-auto space-y-8">
 {/* Header */}
 <div className="flex items-center justify-between">
 <div className="flex items-center gap-3">
 <Link href="/admin" className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 dark:hover:bg-gray-800 transition-colors">
 <ArrowLeft className="w-4 h-4 text-slate-500 dark:text-slate-400" />
 </Link>
 <div>
 <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 dark:text-white flex items-center gap-2">
 <Crown className="w-6 h-6 text-amber-500" /> Service Plans
 </h1>
 <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">Configure and analyze service plans</p>
 </div>
 </div>
 <button onClick={load} className="flex items-center gap-2 text-sm px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800/60 dark:hover:bg-gray-800 transition-colors">
 <RefreshCw className="w-3.5 h-3.5" /> Refresh
 </button>
 </div>

 {error && (
 <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex gap-3 text-sm text-red-700 dark:text-red-300">
 <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" /> {error}
 </div>
 )}

 {/* Plan overview cards */}
 <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
 {planOrder.map(key => {
 const plan = plans[key];
 if (!plan) return null;
 const c = PLAN_COLORS[key];
 const count = breakdown[key] ?? 0;
 const revenue = fmtRevenue(plan.price_vnd, count);
 return (
 <div key={key} className={`rounded-xl border ${c.border} ${c.bg} p-5 space-y-4`}>
 <div className="flex items-start justify-between">
 <div>
 <p className="text-xs uppercase tracking-widest font-semibold text-slate-400 dark:text-slate-500">{key.toUpperCase()}</p>
 <p className={`text-xl font-bold mt-1 ${c.text}`}>{plan.label}</p>
 </div>
 <div className={`text-xs px-2.5 py-1 rounded-full font-semibold ${c.bg} ${c.text} border ${c.border}`}>
 {key === 'enterprise' ? 'Custom' : plan.price_vnd === 0 ? 'Free' : fmt(plan.price_vnd) + '/month'}
 </div>
 </div>

 <div className="grid grid-cols-2 gap-3">
 <div className="bg-white dark:bg-slate-800/60/40 rounded-lg p-3 text-center">
 <p className={`text-2xl font-bold ${c.text}`}>{count}</p>
 <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Users</p>
 </div>
 <div className="bg-white dark:bg-slate-800/60/40 rounded-lg p-3 text-center">
 <p className={`text-base font-bold ${c.text} truncate`}>{revenue}</p>
 <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Est. Revenue</p>
 </div>
 </div>

 {/* Note field */}
 <div>
 {editKey === key ? (
 <div className="flex gap-1.5">
 <input
 autoFocus
 value={editNote}
 onChange={e => setEditNote(e.target.value)}
 placeholder="Notes..."
 className="flex-1 text-xs px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
 />
 <button
 disabled={saving}
 onClick={() => saveNote(key)}
 className="p-1 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white transition-colors"
 >
 <Check className="w-3 h-3" />
 </button>
 <button onClick={() => setEditKey(null)} className="p-1 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 dark:hover:bg-gray-800 transition-colors">
 <X className="w-3 h-3 text-slate-500 dark:text-slate-400" />
 </button>
 </div>
 ) : (
 <button
 onClick={() => { setEditKey(key); setEditNote(planNotes[key] ?? ''); }}
 className="w-full text-left text-xs text-slate-400 dark:text-slate-500 dark:hover:text-gray-200 flex items-center gap-1.5 transition-colors"
 >
 <Edit2 className="w-3 h-3 flex-shrink-0" />
 <span className="truncate">{planNotes[key] || 'Add note...'}</span>
 </button>
 )}
 </div>
 </div>
 );
 })}
 </div>

 {/* Total revenue estimate */}
 <div className="bg-gradient-to-r from-indigo-50 to-violet-50 dark:from-indigo-900/20 dark:to-violet-900/20 rounded-xl border border-indigo-100 dark:border-indigo-800 p-6">
 <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
 <div>
 <p className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">{info?.total_users ?? 0}</p>
 <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Total Users</p>
 </div>
 <div>
 <p className="text-3xl font-bold text-violet-600 dark:text-violet-400">
 {((breakdown.pro ?? 0) + (breakdown.researcher ?? 0) + (breakdown.enterprise ?? 0))}
 </p>
 <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Paid Accounts</p>
 </div>
 <div>
 <p className="text-3xl font-bold text-amber-600 dark:text-amber-400">
 {info?.total_users ? Math.round(((breakdown.pro ?? 0) + (breakdown.researcher ?? 0) + (breakdown.enterprise ?? 0)) / info.total_users * 100) : 0}%
 </p>
 <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Conversion Rate</p>
 </div>
 <div>
 <p className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">
 {((breakdown.pro ?? 0) * 149 + (breakdown.researcher ?? 0) * 499 + (breakdown.enterprise ?? 0) * 3000) > 0
 ? (((breakdown.pro ?? 0) * 149 + (breakdown.researcher ?? 0) * 499 + (breakdown.enterprise ?? 0) * 3000) / 1000).toFixed(0) + 'K VND'
 : '0 VND'}
 </p>
 <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Estimated Monthly Revenue</p>
 </div>
 </div>
 </div>

 {/* Plan limits table */}
 <div className="bg-white dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
 <div className="p-5 border-b border-slate-100 dark:border-slate-800">
 <h2 className="font-semibold text-slate-900 dark:text-slate-100 dark:text-white flex items-center gap-2">
 <TrendingUp className="w-4 h-4 text-indigo-500" /> Plan Limits Details
 </h2>
 </div>
 <div className="overflow-x-auto">
 <table className="w-full text-sm">
 <thead>
 <tr className="bg-slate-50 dark:bg-slate-800/40/50">
 <th className="text-left px-5 py-3 font-medium text-slate-500 dark:text-slate-400 w-48">Feature</th>
 {planOrder.map(key => (
 <th key={key} className="text-center px-4 py-3 font-medium text-slate-700 dark:text-slate-200">
 {plans[key]?.label ?? key}
 </th>
 ))}
 </tr>
 </thead>
 <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
 {[
 // eslint-disable-next-line @typescript-eslint/no-explicit-any
 { label: 'Price/month', fn: (p: any, k: string) => k === 'enterprise' ? 'From 3,000,000 VND' : p.price_vnd === 0 ? 'Free' : fmt(p.price_vnd) },
 // eslint-disable-next-line @typescript-eslint/no-explicit-any
 { label: 'Docs/month', fn: (p: any) => p.max_monthly_docs == null ? 'Unlimited' : `${p.max_monthly_docs}` },
 // eslint-disable-next-line @typescript-eslint/no-explicit-any
 { label: 'Questions/month', fn: (p: any) => p.max_monthly_chat == null ? 'Unlimited' : `${Number(p.max_monthly_chat).toLocaleString('en-US')}` },
 // eslint-disable-next-line @typescript-eslint/no-explicit-any
 { label: 'Current Users', fn: (_: any, k: string) => `${breakdown[k] ?? 0} users` },
 ].map(row => (
 <tr key={row.label} className="hover:bg-slate-100 dark:hover:bg-slate-800/60 dark:hover:bg-gray-800/30 transition-colors">
 <td className="px-5 py-3.5 font-medium text-slate-700 dark:text-slate-200">{row.label}</td>
 {planOrder.map(key => (
 <td key={key} className="px-4 py-3.5 text-center text-slate-600 dark:text-slate-300">
 {plans[key] ? row.fn(plans[key], key) : '—'}
 </td>
 ))}
 </tr>
 ))}
 {/* Feature rows */}
 {(() => {
 const maxFeatures = Math.max(...planOrder.map(k => plans[k]?.features?.length ?? 0));
 return Array.from({ length: maxFeatures }).map((_, i) => (
 <tr key={`f${i}`} className="hover:bg-slate-100 dark:hover:bg-slate-800/60 dark:hover:bg-gray-800/30 transition-colors">
 <td className="px-5 py-3 text-slate-400 dark:text-slate-500 text-xs">{i === 0 ? 'Features included' : ''}</td>
 {planOrder.map(key => (
 <td key={key} className="px-4 py-3 text-center text-xs text-slate-500 dark:text-slate-400">
 {plans[key]?.features?.[i] ?? ''}
 </td>
 ))}
 </tr>
 ));
 })()}
 </tbody>
 </table>
 </div>
 </div>

 {/* Storage info */}
 {info && (
 <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
 {[
 { label: 'User PDFs', value: `${info.storage.user_pdf_count} files`, sub: `${info.storage.user_pdf_size_mb} MB` },
 { label: 'Total Documents', value: `${info.storage.user_pdf_count} files`, sub: `${info.storage.user_pdf_size_mb} MB · uploaded by users` },
 { label: 'System Version', value: info.version, sub: `DB: ${info.db_status === 'ok' ? '✅ OK' : '❌ Error'}` },
 ].map(card => (
 <div key={card.label} className="bg-white dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
 <p className="text-xs text-slate-400 dark:text-slate-500 uppercase tracking-wide font-medium">{card.label}</p>
 <p className="text-xl font-bold text-slate-800 dark:text-slate-100 dark:text-white mt-1">{card.value}</p>
 <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{card.sub}</p>
 </div>
 ))}
 </div>
 )}

 {/* Link to public pricing */}
 <div className="flex justify-end">
 <Link
 href="/pricing"
 className="text-sm text-indigo-500 hover:text-indigo-700 dark:hover:text-indigo-300 underline underline-offset-2 transition-colors"
 >
 View public pricing page →
 </Link>
 </div>
 </div>
 );
}
