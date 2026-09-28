'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAppStore } from '@/store/useAppStore';
import {
 getPricing, getMyPlanUsage, getPaymentHistory,
 PlanTier, PlanUsage, PaymentRecord,
 submitEnterpriseContact,
} from '@/lib/api';
import UpgradeModal from '@/components/UpgradeModal';
import {
 Check, Zap, Star, Building2, Crown, ArrowLeft, BookOpen,
 Receipt, CheckCircle2, Clock, XCircle, X,
} from 'lucide-react';

// ── Helpers ───────────────────────────────────────────────────────────────────

const PLAN_ICONS: Record<string, React.ReactNode> = {
 free: <BookOpen className="w-6 h-6" />,
 pro: <Zap className="w-6 h-6" />,
 researcher: <Star className="w-6 h-6" />,
 enterprise: <Building2 className="w-6 h-6" />,
};

const PLAN_COLORS: Record<string, { bg: string; border: string; badge: string; btn: string }> = {
 free: { bg: 'bg-slate-50 dark:bg-slate-800/40/50', border: 'border-slate-200 dark:border-slate-700', badge: 'bg-slate-100 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 dark:bg-gray-700', btn: 'bg-gray-600 hover:bg-gray-700 text-white' },
 pro: { bg: 'bg-indigo-50 dark:bg-indigo-900/20', border: 'border-indigo-400 dark:border-indigo-500', badge: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300', btn: 'bg-indigo-600 hover:bg-indigo-700 text-white' },
 researcher: { bg: 'bg-violet-50 dark:bg-violet-900/20', border: 'border-violet-400 dark:border-violet-500', badge: 'bg-violet-100 text-violet-700 dark:bg-violet-900/50 dark:text-violet-300', btn: 'bg-violet-600 hover:bg-violet-700 text-white' },
 enterprise: { bg: 'bg-amber-50 dark:bg-amber-900/20', border: 'border-amber-400 dark:border-amber-500', badge: 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300', btn: 'bg-amber-600 hover:bg-amber-700 text-white' },
};

function formatPrice(vnd: number | null, key?: string): string {
 if (vnd === null) return 'Custom';
 if (vnd === 0) return 'Free';
 const formatted = vnd.toLocaleString('en-US') + ' VND/month';
 return key === 'enterprise' ? 'From ' + formatted : formatted;
}

function formatVnd(n: number) {
 return n.toLocaleString('en-US') + ' VND';
}

const STATUS_CONFIG = {
 pending: { icon: <Clock className="w-3.5 h-3.5 text-amber-500" />, label: 'Pending', color: 'text-amber-600 bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-700' },
 completed: { icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />, label: 'Success', color: 'text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-700' },
 expired: { icon: <XCircle className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />, label: 'Expired', color: 'text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-700' },
};

// ── Page ──────────────────────────────────────────────────────────────────────

// ── Enterprise Contact Modal ──────────────────────────────────────────────────

function EnterpriseContactModal({ onClose }: { onClose: () => void }) {
 const { user } = useAppStore();
 const [form, setForm] = useState({
 name: user?.full_name ?? '',
 email: user?.email ?? '',
 school_name: '',
 phone: '',
 message: '',
 });
 const [submitting, setSubmitting] = useState(false);
 const [done, setDone] = useState(false);
 const [err, setErr] = useState('');

 const handleSubmit = async (e: React.FormEvent) => {
 e.preventDefault();
 if (!form.name || !form.email || !form.school_name) { setErr('Please fill in all required fields'); return; }
 setSubmitting(true); setErr('');
 try {
 await submitEnterpriseContact(form);
 setDone(true);
 } catch {
 setErr('An error occurred. Please try again.');
 } finally {
 setSubmitting(false);
 }
 };

 return (
 <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
 <div className="bg-white dark:bg-slate-800/60 rounded-2xl shadow-2xl w-full max-w-md p-6 relative">
 <button onClick={onClose} className="absolute top-4 right-4 text-slate-400 dark:text-slate-500 dark:hover:text-gray-200">
 <X className="w-5 h-5" />
 </button>
 {done ? (
 <div className="text-center py-6">
 <div className="w-14 h-14 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center mx-auto mb-4">
 <CheckCircle2 className="w-7 h-7 text-emerald-500" />
 </div>
 <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 dark:text-white mb-2">Request Submitted!</h3>
 <p className="text-sm text-slate-500 dark:text-slate-400 mb-5">
 Admin will contact you as soon as possible.
 </p>
 <button onClick={onClose} className="px-5 py-2 bg-amber-500 hover:bg-amber-600 text-white text-sm font-semibold rounded-lg">
 Close
 </button>
 </div>
 ) : (
 <>
 <div className="flex items-center gap-3 mb-5">
 <div className="w-10 h-10 rounded-xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
 <Building2 className="w-5 h-5 text-amber-600" />
 </div>
 <div>
 <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 dark:text-white">Contact us Enterprise</h3>
 <p className="text-xs text-slate-500 dark:text-slate-400">Fill in details, admin will consult and create a custom payment form</p>
 </div>
 </div>
 <form onSubmit={handleSubmit} className="flex flex-col gap-3">
 <div className="grid grid-cols-2 gap-3">
 <div>
 <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">Name <span className="text-red-500">*</span></label>
 <input value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
 className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-400"
 placeholder="John Doe" />
 </div>
 <div>
 <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">Phone</label>
 <input value={form.phone} onChange={e => setForm(p => ({ ...p, phone: e.target.value }))}
 className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-400"
 placeholder="0909..." />
 </div>
 </div>
 <div>
 <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">Email <span className="text-red-500">*</span></label>
 <input type="email" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))}
 className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-400"
 placeholder="email@truong.edu.vn" />
 </div>
 <div>
 <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">School / Organization <span className="text-red-500">*</span></label>
 <input value={form.school_name} onChange={e => setForm(p => ({ ...p, school_name: e.target.value }))}
 className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-400"
 placeholder="University ABC" />
 </div>
 <div>
 <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">Requirements / Notes</label>
 <textarea value={form.message} onChange={e => setForm(p => ({ ...p, message: e.target.value }))} rows={3}
 className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-400 resize-none"
 placeholder="Number of users, special requirements..." />
 </div>
 {err && <p className="text-xs text-red-500">{err}</p>}
 <button type="submit" disabled={submitting}
 className="w-full py-2.5 bg-amber-500 hover:bg-amber-600 disabled:opacity-60 text-white text-sm font-semibold rounded-lg transition-colors">
 {submitting ? 'Sending...' : 'Submit request'}
 </button>
 </form>
 </>
 )}
 </div>
 </div>
 );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function PricingPage() {
 const { user, updateUser } = useAppStore();

 const [tiers, setTiers] = useState<PlanTier[]>([]);
 const [usage, setUsage] = useState<PlanUsage | null>(null);
 const [history, setHistory] = useState<PaymentRecord[]>([]);
 const [loading, setLoading] = useState(true);
 const [modalTier, setModalTier] = useState<PlanTier | null>(null);
 const [showHistory, setShowHistory] = useState(false);
 const [showEnterpriseContact, setShowEnterpriseContact] = useState(false);

 useEffect(() => {
 getPricing().then(setTiers).catch(() => {}).finally(() => setLoading(false));
 }, []);

 useEffect(() => {
 if (user) {
 getMyPlanUsage().then(setUsage).catch(() => {});
 getPaymentHistory().then(setHistory).catch(() => {});
 }
 }, [user]);

 const currentPlan = usage?.plan ?? (user ? 'free' : null);

 const handleSuccess = (plan: string) => {
 updateUser({ plan });
 setUsage(prev => prev ? { ...prev, plan } : prev);
 getPaymentHistory().then(setHistory).catch(() => {});
 };

 if (loading) {
 return (
 <div className="min-h-screen flex items-center justify-center">
 <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
 </div>
 );
 }

 return (
 <div className="min-h-screen bg-[#FAF9F6] dark:bg-[#070A13] transition-colors duration-500 px-4 py-10">

 {/* Back */}
 <div className="max-w-5xl mx-auto mb-6 flex items-center justify-between">
 <Link
 href="/profile"
 className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
 >
 <ArrowLeft className="w-3.5 h-3.5" /> Profile
 </Link>
 {user && history.length > 0 && (
 <button
 onClick={() => setShowHistory(v => !v)}
 className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
 >
 <Receipt className="w-3.5 h-3.5" />
 Payment History
 </button>
 )}
 </div>

 {/* Header */}
 <div className="max-w-5xl mx-auto text-center mb-12">
 <div className="inline-flex items-center gap-2 bg-[#F9A825]/15 text-[#002D72] dark:bg-[#F9A825]/10 dark:text-[#F9A825] text-xs font-medium px-3 py-1 rounded-full mb-4 border border-[#F9A825]/30">
 <Crown className="w-3.5 h-3.5" /> Service Plans
 </div>
 <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100 dark:text-white mb-3">
 Choose the right plan for you
 </h1>
 <p className="text-slate-500 dark:text-slate-400 max-w-xl mx-auto text-sm">
 Pay via bank transfer — auto-upgrade after confirmation
 </p>
 </div>

 {/* Usage banner */}
 {usage && (
 <div className="max-w-5xl mx-auto mb-8 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-700 rounded-xl p-4 flex flex-wrap gap-4 items-center justify-between">
 <div className="flex items-center gap-3">
 <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-800 flex items-center justify-center text-indigo-600 dark:text-indigo-300">
 {PLAN_ICONS[usage.plan] ?? <Zap className="w-4 h-4" />}
 </div>
 <div>
 <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 dark:text-white">
 Current Plan: <span className="text-indigo-600 dark:text-indigo-400">{usage.plan_label}</span>
 </p>
 <p className="text-xs text-slate-500 dark:text-slate-400">
 Documents: {usage.used_docs}{usage.max_docs ? `/${usage.max_docs}` : ''} &nbsp;·&nbsp;
 Questions today: {usage.used_today_chat}{usage.max_daily_chat ? `/${usage.max_daily_chat}` : ''}
 </p>
 </div>
 </div>
 {usage.plan === 'free' && (
 <p className="text-xs text-indigo-600 dark:text-indigo-400 font-medium">
 Upgrade to unlock all features ↓
 </p>
 )}
 </div>
 )}

 {/* Pricing cards */}
 <div className="max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
 {tiers.map((tier) => {
 const colors = PLAN_COLORS[tier.key] ?? PLAN_COLORS.free;
 const isCurrent = tier.key === currentPlan;
 const isPopular = tier.key === 'pro';
 const canUpgrade = user && !isCurrent && tier.key !== 'free' && tier.key !== 'enterprise' && tier.price_vnd !== null;

 return (
 <div
 key={tier.key}
 className={`relative rounded-2xl border-2 p-5 flex flex-col gap-4 transition-shadow hover:shadow-lg
 ${colors.bg} ${isCurrent ? colors.border : 'border-slate-200 dark:border-slate-700'}`}
 >
 {isPopular && (
 <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#F9A825] text-[#002D72] text-[10px] font-bold px-3 py-0.5 rounded-full uppercase tracking-wider shadow-sm">
 Popular
 </span>
 )}
 {isCurrent && (
 <span className={`absolute -top-3 right-4 text-[10px] font-bold px-3 py-0.5 rounded-full uppercase tracking-wider ${colors.badge}`}>
 Your Plan
 </span>
 )}

 {/* Icon + title */}
 <div className="flex items-center gap-3">
 <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${colors.badge}`}>
 {PLAN_ICONS[tier.key]}
 </div>
 <div>
 <h3 className="font-bold text-slate-900 dark:text-slate-100 dark:text-white text-sm">{tier.label}</h3>
 <p className="text-xs text-slate-500 dark:text-slate-400">
 {tier.max_docs !== null ? `${tier.max_docs} documents` : 'Unlimited'}
 </p>
 </div>
 </div>

 {/* Price */}
 <div>
 <p className="text-lg font-bold text-slate-900 dark:text-slate-100 dark:text-white leading-snug">
 {formatPrice(tier.price_vnd, tier.key)}
 </p>
 </div>

 {/* Features */}
 <ul className="flex flex-col gap-2 flex-1">
 {tier.features.map((f) => (
 <li key={f} className="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-300">
 <Check className="w-3.5 h-3.5 text-emerald-500 mt-0.5 shrink-0" />
 {f}
 </li>
 ))}
 </ul>

 {/* CTA */}
 <div className="mt-auto pt-2">
 {isCurrent ? (
 <div className={`w-full text-center text-xs font-medium py-2 rounded-lg ${colors.badge}`}>
 Currently using
 </div>
 ) : tier.key === 'enterprise' ? (
 <button
 onClick={() => setShowEnterpriseContact(true)}
 className={`w-full text-xs font-semibold py-2.5 rounded-lg transition-colors ${colors.btn}`}
 >
 Contact us
 </button>
 ) : tier.key === 'free' ? (
 !user ? (
 <Link
 href="/register"
 className={`block w-full text-center text-xs font-semibold py-2.5 rounded-lg transition-colors ${colors.btn}`}
 >
 Sign up free
 </Link>
 ) : (
 <div className={`w-full text-center text-xs font-medium py-2 rounded-lg ${colors.badge}`}>
 Basic Plan
 </div>
 )
 ) : canUpgrade ? (
 <button
 onClick={() => setModalTier(tier)}
 className={`w-full text-xs font-semibold py-2.5 rounded-lg transition-colors ${colors.btn}`}
 >
 Upgrade now
 </button>
 ) : (
 <Link
 href="/register"
 className={`block w-full text-center text-xs font-semibold py-2.5 rounded-lg transition-colors ${colors.btn}`}
 >
 Sign up
 </Link>
 )}
 </div>
 </div>
 );
 })}
 </div>

 {/* Payment method note */}
 <div className="max-w-5xl mx-auto mt-8 bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 rounded-xl p-5 flex flex-col sm:flex-row gap-4 items-start">
 <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center shrink-0">
 <Receipt className="w-5 h-5 text-blue-500" />
 </div>
 <div>
 <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 mb-1">Payment Instructions</p>
 <ol className="text-xs text-slate-500 dark:text-slate-400 space-y-1 list-decimal list-inside">
 <li>Click <strong>Upgrade now</strong> → system generates a unique QR code for you</li>
 <li>Open banking app, scan QR or manually transfer with correct <strong>transfer note</strong></li>
 <li>Account auto-upgrades within <strong>seconds</strong> after successful transfer</li>
 <li>Each QR code is valid for <strong>15 minutes</strong> — can regenerate when expired</li>
 </ol>
 </div>
 </div>

 {/* Payment history */}
 {showHistory && history.length > 0 && (
 <div className="max-w-5xl mx-auto mt-6">
 <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3 flex items-center gap-2">
 <Receipt className="w-4 h-4" /> Payment History
 </h2>
 <div className="rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
 <table className="w-full text-xs">
 <thead>
 <tr className="bg-slate-50 dark:bg-slate-800/40 border-b border-slate-200 dark:border-slate-700">
 {['Plan', 'Amount', 'Reference Code', 'Created', 'Status'].map(h => (
 <th key={h} className="text-left px-4 py-2.5 text-[10px] uppercase tracking-wide font-semibold text-slate-400 dark:text-slate-500">{h}</th>
 ))}
 </tr>
 </thead>
 <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
 {history.map(p => {
 const sc = STATUS_CONFIG[p.status];
 return (
 <tr key={p.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/30">
 <td className="px-4 py-3 font-medium text-slate-800 dark:text-slate-100">{p.plan_label}</td>
 <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{formatVnd(p.amount)}</td>
 <td className="px-4 py-3 font-mono text-slate-500 dark:text-slate-400">{p.ref_code}</td>
 <td className="px-4 py-3 text-slate-400 dark:text-slate-500">
 {p.created_at ? new Date(p.created_at).toLocaleString('en-US') : '—'}
 </td>
 <td className="px-4 py-3">
 <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-medium ${sc.color}`}>
 {sc.icon} {sc.label}
 </span>
 </td>
 </tr>
 );
 })}
 </tbody>
 </table>
 </div>
 </div>
 )}

 {/* Footer note */}
 <div className="max-w-5xl mx-auto mt-10 text-center text-xs text-slate-400 dark:text-slate-500">
 <p>All prices exclude VAT. Monthly billing.</p>
 <p className="mt-1">
 Questions?{' '}
 <a href="mailto:dinhhchi2110@gmail.com" className="text-indigo-500 hover:underline">
 Contact us
 </a>
 </p>
 </div>

 {/* Upgrade modal */}
 {modalTier && (
 <UpgradeModal
 tier={modalTier}
 onClose={() => setModalTier(null)}
 onSuccess={(plan) => {
 handleSuccess(plan);
 setModalTier(null);
 }}
 />
 )}

 {/* Enterprise contact modal */}
 {showEnterpriseContact && (
 <EnterpriseContactModal onClose={() => setShowEnterpriseContact(false)} />
 )}
 </div>
 );
}
