'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Image from 'next/image';
import { useAppStore } from '@/store/useAppStore';
import {
 createPayment, getPaymentStatus, getMyPlanUsage,
 PaymentInfo, PlanTier,
} from '@/lib/api';
import {
 X, Copy, Check, Clock, CheckCircle2, AlertCircle,
 Loader2, ExternalLink, Zap, Star,
} from 'lucide-react';

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatVnd(n: number) {
 return n.toLocaleString('en-US') + ' VND';
}

function useCountdown(expiresAt: string | null) {
 const [seconds, setSeconds] = useState(0);
 useEffect(() => {
 if (!expiresAt) return;
 const tick = () => {
 const diff = Math.max(0, Math.floor((new Date(expiresAt).getTime() - Date.now()) / 1000));
 setSeconds(diff);
 };
 tick();
 const id = setInterval(tick, 1000);
 return () => clearInterval(id);
 }, [expiresAt]);
 const m = Math.floor(seconds / 60);
 const s = seconds % 60;
 return { seconds, label: `${m}:${s.toString().padStart(2, '0')}` };
}

function CopyButton({ text }: { text: string }) {
 const [copied, setCopied] = useState(false);
 const copy = () => {
 navigator.clipboard.writeText(text).then(() => {
 setCopied(true);
 setTimeout(() => setCopied(false), 2000);
 });
 };
 return (
 <button
 onClick={copy}
 className="ml-2 p-1 rounded text-slate-400 dark:text-slate-500 hover:text-indigo-600 transition-colors"
 title="Copy"
 >
 {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
 </button>
 );
}

// ── Main component ────────────────────────────────────────────────────────────

interface Props {
 tier: PlanTier;
 onClose: () => void;
 onSuccess: (plan: string) => void;
}

type Step = 'confirm' | 'paying' | 'success' | 'expired' | 'error';

export default function UpgradeModal({ tier, onClose, onSuccess }: Props) {
 const { updateUser } = useAppStore();

 const [step, setStep] = useState<Step>('confirm');
 const [payment, setPayment] = useState<PaymentInfo | null>(null);
 const [errorMsg, setErrorMsg] = useState('');
 const [qrLoaded, setQrLoaded] = useState(false);
 const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

 const { seconds, label: countdownLabel } = useCountdown(
 step === 'paying' ? payment?.expires_at ?? null : null
 );

 // Stop polling & expire when countdown hits 0
 useEffect(() => {
 if (step === 'paying' && seconds === 0 && payment) {
 clearInterval(pollRef.current!);
 setStep('expired');
 }
 }, [seconds, step, payment]);

 // Cleanup on unmount
 useEffect(() => () => { clearInterval(pollRef.current!); }, []);

 // ── Start payment ──────────────────────────────────────────────────────────
 const handleStartPayment = async () => {
 setStep('paying');
 setErrorMsg('');
 try {
 const info = await createPayment(tier.key);
 setPayment(info);
 startPolling(info.ref_code);
 } catch (err: unknown) {
 const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Could not create transaction';
 setErrorMsg(msg);
 setStep('error');
 }
 };

 // ── Poll status ────────────────────────────────────────────────────────────
 const startPolling = useCallback((refCode: string) => {
 if (pollRef.current) clearInterval(pollRef.current);
 pollRef.current = setInterval(async () => {
 try {
 const status = await getPaymentStatus(refCode);
 if (status.status === 'completed') {
 clearInterval(pollRef.current!);
 // Sync plan in store
 const usage = await getMyPlanUsage().catch(() => null);
 if (usage) updateUser({ plan: usage.plan });
 setStep('success');
 onSuccess(tier.key);
 } else if (status.status === 'expired') {
 clearInterval(pollRef.current!);
 setStep('expired');
 }
 } catch { /* silent */ }
 }, 3000);
 }, [tier.key, updateUser, onSuccess]);

 // ── Render ─────────────────────────────────────────────────────────────────

 const PLAN_ICON = tier.key === 'pro' ? <Zap className="w-5 h-5" /> : <Star className="w-5 h-5" />;
 const PLAN_COLOR = tier.key === 'pro'
 ? { accent: 'text-indigo-600', bg: 'bg-indigo-50 dark:bg-indigo-900/20', border: 'border-indigo-200 dark:border-indigo-700' }
 : { accent: 'text-violet-600', bg: 'bg-violet-50 dark:bg-violet-900/20', border: 'border-violet-200 dark:border-violet-700' };

 return (
 <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
 <div className="relative w-full max-w-md bg-white dark:bg-slate-800/60 rounded-2xl shadow-2xl border border-slate-100 dark:border-slate-800 overflow-hidden">

 {/* Close */}
 <button
 onClick={onClose}
 className="absolute top-4 right-4 text-slate-400 dark:text-slate-500 dark:hover:text-gray-300 transition-colors z-10"
 >
 <X className="w-5 h-5" />
 </button>

 {/* ── Step: CONFIRM ── */}
 {step === 'confirm' && (
 <div className="p-6 space-y-5">
 <div className="flex items-center gap-3">
 <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${PLAN_COLOR.bg} ${PLAN_COLOR.accent}`}>
 {PLAN_ICON}
 </div>
 <div>
 <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 dark:text-white">
 Upgrade to {tier.label}
 </h2>
 <p className="text-sm text-slate-500 dark:text-slate-400">
 {formatVnd(tier.price_vnd ?? 0)}/month
 </p>
 </div>
 </div>

 <ul className="space-y-2">
 {tier.features.map(f => (
 <li key={f} className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
 <Check className="w-4 h-4 text-emerald-500 shrink-0" />
 {f}
 </li>
 ))}
 </ul>

 <div className={`rounded-xl border p-4 ${PLAN_COLOR.bg} ${PLAN_COLOR.border}`}>
 <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
 Pay via <strong>bank transfer</strong>. Account will be auto-upgraded after transaction is confirmed.
 </p>
 </div>

 <button
 onClick={handleStartPayment}
 className={`w-full py-3 rounded-xl font-semibold text-white text-sm transition-colors
 ${tier.key === 'pro' ? 'bg-indigo-600 hover:bg-indigo-700' : 'bg-violet-600 hover:bg-violet-700'}`}
 >
 Generate Payment QR
 </button>
 </div>
 )}

 {/* ── Step: PAYING ── */}
 {step === 'paying' && (
 <div className="p-6 space-y-4">
 <div className="text-center">
 <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 dark:text-white mb-1">
 Scan QR to Pay
 </h2>
 <p className="text-xs text-slate-500 dark:text-slate-400">
 Auto-upgrade after successful transfer
 </p>
 </div>

 {/* QR Code */}
 {payment ? (
 <div className="flex justify-center">
 <div className="relative w-52 h-52 bg-slate-50 dark:bg-slate-800/40 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700">
 {!qrLoaded && (
 <div className="absolute inset-0 flex items-center justify-center">
 <Loader2 className="w-8 h-8 text-slate-300 dark:text-slate-600 animate-spin" />
 </div>
 )}
 <img
 src={payment.qr_url}
 alt="VietQR"
 className={`w-full h-full object-contain transition-opacity ${qrLoaded ? 'opacity-100' : 'opacity-0'}`}
 onLoad={() => setQrLoaded(true)}
 onError={() => setQrLoaded(true)}
 />
 </div>
 </div>
 ) : (
 <div className="flex justify-center py-8">
 <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
 </div>
 )}

 {/* Bank details */}
 {payment && (
 <div className="bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-700 divide-y divide-slate-200 dark:divide-slate-700 text-sm">
 {[
 { label: 'Bank', value: payment.bank_code },
 { label: 'Account Number', value: payment.bank_account_no, copy: true },
 { label: 'Account Holder', value: payment.bank_account_name },
 { label: 'Amount', value: formatVnd(payment.amount) },
 { label: 'Transfer Note', value: payment.ref_code, copy: true, highlight: true },
 ].map(row => (
 <div key={row.label} className="flex items-center justify-between px-4 py-2.5">
 <span className="text-slate-500 dark:text-slate-400 text-xs shrink-0">{row.label}</span>
 <div className="flex items-center min-w-0 ml-2">
 <span className={`text-xs font-medium truncate
 ${row.highlight ? 'font-mono text-indigo-600 dark:text-indigo-400 font-bold' : 'text-slate-800 dark:text-slate-100'}`}>
 {row.value}
 </span>
 {row.copy && <CopyButton text={row.value} />}
 </div>
 </div>
 ))}
 </div>
 )}

 {/* Countdown + status */}
 <div className="flex items-center justify-between text-xs">
 <div className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400">
 <Clock className="w-3.5 h-3.5" />
 <span>Expires in <strong>{countdownLabel}</strong></span>
 </div>
 <div className="flex items-center gap-1.5 text-slate-400 dark:text-slate-500">
 <Loader2 className="w-3 h-3 animate-spin" />
 <span>Pending Confirmation…</span>
 </div>
 </div>

 <p className="text-[10px] text-center text-slate-400 dark:text-slate-500 leading-relaxed">
 ⚠ Enter the correct transfer note <strong className="text-slate-600 dark:text-slate-300">{payment?.ref_code}</strong> for automatic system recognition
 </p>
 </div>
 )}

 {/* ── Step: SUCCESS ── */}
 {step === 'success' && (
 <div className="p-8 text-center space-y-4">
 <div className="w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center mx-auto">
 <CheckCircle2 className="w-9 h-9 text-emerald-500" />
 </div>
 <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 dark:text-white">
 Upgrade successful! 🎉
 </h2>
 <p className="text-sm text-slate-500 dark:text-slate-400">
 Your account has been upgraded to{' '}
 <span className="font-semibold text-emerald-600">{tier.label}</span>.
 All features are now unlocked.
 </p>
 <button
 onClick={onClose}
 className="w-full py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-semibold text-sm transition-colors"
 >
 Start Using
 </button>
 </div>
 )}

 {/* ── Step: EXPIRED ── */}
 {step === 'expired' && (
 <div className="p-8 text-center space-y-4">
 <div className="w-16 h-16 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center mx-auto">
 <Clock className="w-9 h-9 text-amber-500" />
 </div>
 <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 dark:text-white">Transaction Expired</h2>
 <p className="text-sm text-slate-500 dark:text-slate-400">
 QR code has expired. You can create a new transaction.
 </p>
 <div className="flex gap-3">
 <button onClick={onClose} className="flex-1 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/60 dark:hover:bg-gray-800 transition-colors">
 Close
 </button>
 <button
 onClick={() => { setStep('confirm'); setPayment(null); setQrLoaded(false); }}
 className="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition-colors"
 >
 Try again
 </button>
 </div>
 </div>
 )}

 {/* ── Step: ERROR ── */}
 {step === 'error' && (
 <div className="p-8 text-center space-y-4">
 <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto">
 <AlertCircle className="w-9 h-9 text-red-500" />
 </div>
 <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 dark:text-white">Error</h2>
 <p className="text-sm text-slate-500 dark:text-slate-400">{errorMsg}</p>
 <div className="flex gap-3">
 <button onClick={onClose} className="flex-1 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/60 dark:hover:bg-gray-800 transition-colors">
 Close
 </button>
 <button
 onClick={() => { setStep('confirm'); setErrorMsg(''); }}
 className="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition-colors"
 >
 Try again
 </button>
 </div>
 </div>
 )}

 </div>
 </div>
 );
}
