'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import {
 getEnterpriseOffer, claimEnterpriseOffer, pollOfferStatus,
 EnterpriseOffer, OfferClaimResult,
} from '@/lib/api';
import { Building2, CheckCircle2, Clock, Copy, AlertTriangle } from 'lucide-react';

type Step = 'loading' | 'enter_email' | 'qr' | 'paid' | 'expired' | 'not_found';

function fmtVnd(n: number) {
 return n.toLocaleString('en-US') + ' VND';
}

export default function EnterpriseOfferPage() {
 const params = useParams();
 const token = params?.token as string;

 const [step, setStep] = useState<Step>('loading');
 const [offer, setOffer] = useState<EnterpriseOffer | null>(null);
 const [claim, setClaim] = useState<OfferClaimResult | null>(null);
 const [email, setEmail] = useState('');
 const [err, setErr] = useState('');
 const [busy, setBusy] = useState(false);
 const [copied, setCopied] = useState(false);

 useEffect(() => {
 if (!token) return;
 getEnterpriseOffer(token)
 .then(o => {
 setOffer(o);
 if (o.status === 'paid') setStep('paid');
 else if (o.status === 'expired') setStep('expired');
 else setStep('enter_email');
 })
 .catch(e => {
 const status = e?.response?.status;
 if (status === 410) setStep('expired');
 else setStep('not_found');
 });
 }, [token]);

 // Poll for payment confirmation
 useEffect(() => {
 if (step !== 'qr') return;
 const id = setInterval(async () => {
 try {
 const s = await pollOfferStatus(token);
 if (s.status === 'paid') {
 clearInterval(id);
 setStep('paid');
 }
 } catch {}
 }, 4000);
 return () => clearInterval(id);
 }, [step, token]);

 const handleClaim = async (e: React.FormEvent) => {
 e.preventDefault();
 if (!email.trim()) { setErr('Please enter your email'); return; }
 setBusy(true); setErr('');
 try {
 const result = await claimEnterpriseOffer(token, email.trim());
 setClaim(result);
 setStep('qr');
 } catch (ex: unknown) {
 const msg = (ex as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
 setErr(msg || 'An error occurred. Please try again.');
 } finally {
 setBusy(false);
 }
 };

 const copy = useCallback((text: string) => {
 navigator.clipboard.writeText(text).then(() => {
 setCopied(true);
 setTimeout(() => setCopied(false), 1500);
 });
 }, []);

 if (step === 'loading') {
 return (
 <div className="min-h-screen flex items-center justify-center">
 <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
 </div>
 );
 }

 if (step === 'not_found') {
 return (
 <div className="min-h-screen flex flex-col items-center justify-center gap-4 p-6 text-center">
 <AlertTriangle className="w-12 h-12 text-slate-400 dark:text-slate-500" />
 <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100 dark:text-white">Form not found</h1>
 <p className="text-sm text-slate-500 dark:text-slate-400">This link does not exist or has been deleted.</p>
 <Link href="/" className="text-sm text-indigo-600 hover:underline">Go to Homepage</Link>
 </div>
 );
 }

 if (step === 'expired') {
 return (
 <div className="min-h-screen flex flex-col items-center justify-center gap-4 p-6 text-center">
 <Clock className="w-12 h-12 text-amber-400" />
 <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100 dark:text-white">Form Expired</h1>
 <p className="text-sm text-slate-500 dark:text-slate-400">This payment form has expired. Please contact admin for assistance.</p>
 <Link href="/pricing" className="text-sm text-indigo-600 hover:underline">View Pricing Plans</Link>
 </div>
 );
 }

 if (step === 'paid') {
 return (
 <div className="min-h-screen flex flex-col items-center justify-center gap-4 p-6 text-center">
 <div className="w-20 h-20 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
 <CheckCircle2 className="w-10 h-10 text-emerald-500" />
 </div>
 <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 dark:text-white">Payment Successful!</h1>
 <p className="text-sm text-slate-500 dark:text-slate-400 max-w-sm">
 Enterprise account has been activated. Log in to start using.
 </p>
 <Link href="/login"
 className="mt-2 px-6 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-semibold rounded-xl transition-colors">
 Log in
 </Link>
 </div>
 );
 }

 // Enter email step
 if (step === 'enter_email' && offer) {
 return (
 <div className="min-h-screen bg-amber-50 dark:bg-gray-950 flex items-center justify-center p-4">
 <div className="bg-white dark:bg-slate-800/60 rounded-2xl shadow-xl w-full max-w-md p-8">
 {/* Header */}
 <div className="flex items-center gap-3 mb-6">
 <div className="w-12 h-12 rounded-2xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
 <Building2 className="w-6 h-6 text-amber-600 dark:text-amber-400" />
 </div>
 <div>
 <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100 dark:text-white">Enterprise Payment Form</h1>
 <p className="text-xs text-slate-500 dark:text-slate-400">Acamind</p>
 </div>
 </div>

 {/* Info */}
 <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl p-4 mb-6 space-y-2">
 <div className="flex justify-between text-sm">
 <span className="text-slate-500 dark:text-slate-400">Organization</span>
 <span className="font-semibold text-slate-800 dark:text-slate-100 dark:text-white">{offer.school_name}</span>
 </div>
 <div className="flex justify-between text-sm">
 <span className="text-slate-500 dark:text-slate-400">Duration</span>
 <span className="font-semibold text-slate-800 dark:text-slate-100 dark:text-white">{offer.duration_months} months</span>
 </div>
 <div className="flex justify-between text-sm">
 <span className="text-slate-500 dark:text-slate-400">Package</span>
 <span className="font-semibold text-slate-800 dark:text-slate-100 dark:text-white capitalize">{offer.package_type}</span>
 </div>
 {offer.max_slots && (
 <div className="flex justify-between text-sm">
 <span className="text-slate-500 dark:text-slate-400">Number of Members</span>
 <span className="font-semibold text-slate-800 dark:text-slate-100 dark:text-white">{offer.max_slots}</span>
 </div>
 )}
 <div className="pt-2 border-t border-amber-200 dark:border-amber-700">
 <div className="flex justify-between items-baseline">
 <span className="text-sm text-slate-500 dark:text-slate-400">Total Payment</span>
 <span className="text-2xl font-black text-amber-600 dark:text-amber-400">{fmtVnd(offer.amount)}</span>
 </div>
 </div>
 </div>

 {/* Email form */}
 <form onSubmit={handleClaim} className="flex flex-col gap-3">
 <div>
 <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1.5 block">
 Your Acamind account email
 </label>
 <input
 type="email"
 value={email}
 onChange={e => setEmail(e.target.value)}
 placeholder="email@truong.edu.vn"
 className="w-full text-sm px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-400"
 />
 <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">This account will be upgraded to Enterprise after payment</p>
 </div>
 {err && <p className="text-xs text-red-500">{err}</p>}
 <button type="submit" disabled={busy}
 className="w-full py-3 bg-amber-500 hover:bg-amber-600 disabled:opacity-60 text-white text-sm font-bold rounded-xl transition-colors">
 {busy ? 'Processing...' : 'Continue → Get QR Code'}
 </button>
 </form>
 </div>
 </div>
 );
 }

 // QR step
 if (step === 'qr' && claim) {
 return (
 <div className="min-h-screen bg-amber-50 dark:bg-gray-950 flex items-center justify-center p-4">
 <div className="bg-white dark:bg-slate-800/60 rounded-2xl shadow-xl w-full max-w-md p-8">
 <div className="text-center mb-6">
 <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100 dark:text-white mb-1">Scan QR to Pay</h1>
 <p className="text-xs text-slate-500 dark:text-slate-400">
 Account will be automatically upgraded in a few seconds
 </p>
 </div>

 {/* QR image */}
 <div className="flex justify-center mb-5">
 <div className="relative w-56 h-56 rounded-xl overflow-hidden border-2 border-amber-300 dark:border-amber-700">
 <Image
 src={claim.qr_url}
 alt="VietQR"
 fill
 className="object-contain"
 unoptimized
 />
 </div>
 </div>

 {/* Amount */}
 <div className="text-center mb-5">
 <p className="text-3xl font-black text-amber-600 dark:text-amber-400">{fmtVnd(claim.amount)}</p>
 </div>

 {/* Bank info */}
 <div className="bg-slate-50 dark:bg-slate-800/40 rounded-xl p-4 space-y-2 mb-5">
 <div className="flex justify-between items-center text-sm">
 <span className="text-slate-500 dark:text-slate-400">Bank</span>
 <span className="font-semibold text-slate-800 dark:text-slate-100 dark:text-white">{claim.bank_code}</span>
 </div>
 <div className="flex justify-between items-center text-sm">
 <span className="text-slate-500 dark:text-slate-400">Account No.</span>
 <span className="font-mono font-semibold text-slate-800 dark:text-slate-100 dark:text-white">{claim.bank_account_no}</span>
 </div>
 <div className="flex justify-between items-center text-sm">
 <span className="text-slate-500 dark:text-slate-400">Account Holder</span>
 <span className="font-semibold text-slate-800 dark:text-slate-100 dark:text-white">{claim.bank_account_name}</span>
 </div>
 <div className="flex justify-between items-center text-sm">
 <span className="text-slate-500 dark:text-slate-400">Transfer Note</span>
 <div className="flex items-center gap-2">
 <span className="font-mono font-bold text-amber-600 dark:text-amber-400">{claim.ref_code}</span>
 <button onClick={() => copy(claim.ref_code)} className="text-slate-400 dark:text-slate-500 hover:text-amber-500 transition-colors">
 <Copy className="w-3.5 h-3.5" />
 </button>
 </div>
 </div>
 </div>

 {copied && (
 <p className="text-center text-xs text-emerald-600 dark:text-emerald-400 -mt-3 mb-3">Copied!</p>
 )}

 {/* Waiting indicator */}
 <div className="flex items-center justify-center gap-2 text-xs text-slate-500 dark:text-slate-400">
 <div className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
 Waiting for payment confirmation...
 </div>

 <p className="text-center text-[11px] text-slate-400 dark:text-slate-500 mt-3">
 Remember to enter the correct transfer note <strong>{claim.ref_code}</strong>
 </p>
 </div>
 </div>
 );
 }

 return null;
}
