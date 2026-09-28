'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAppStore } from '@/store/useAppStore';
import { applyResearcher, getApplicationStatus, ResearcherApplication } from '@/lib/api';
import { GraduationCap, CheckCircle, Clock, XCircle, ArrowLeft, Send } from 'lucide-react';

type PageState = 'loading' | 'already_upgraded' | 'pending' | 'rejected' | 'apply' | 'success';

export default function ResearcherApplyPage() {
 const { user } = useAppStore();
 const router = useRouter();
 const [state, setState] = useState<PageState>('loading');
 const [application, setApplication] = useState<ResearcherApplication | null>(null);
 const [reason, setReason] = useState('');
 const [submitting, setSubmitting] = useState(false);
 const [error, setError] = useState('');

 useEffect(() => {
 if (user === null) return;
 if (!user) { router.replace('/login'); return; }
 if (user.role === 'admin' || user.role === 'researcher') {
 setState('already_upgraded'); return;
 }
 loadStatus();
 }, [user]);

 const loadStatus = async () => {
 try {
 const data = await getApplicationStatus();
 setApplication(data.application);
 if (data.status === 'pending') { setState('pending'); return; }
 if (data.status === 'rejected') { setState('rejected'); return; }
 setState('apply');
 } catch {
 setState('apply');
 }
 };

 const handleSubmit = async (e: React.FormEvent) => {
 e.preventDefault();
 if (!reason.trim()) { setError('Please enter a reason for applying.'); return; }
 setSubmitting(true); setError('');
 try {
 await applyResearcher(reason.trim());
 setState('success');
 } catch (err: unknown) {
 const errWithResponse = err as { response?: { data?: { detail?: string } } };
 const msg = errWithResponse?.response?.data?.detail;
 setError(msg ?? 'An error occurred. Please try again.');
 } finally { setSubmitting(false); }
 };

 // ── Loading ──────────────────────────────────────────────────────────────
 if (state === 'loading' || !user) {
 return (
 <div className="flex items-center justify-center min-h-[60vh]">
 <div className="w-6 h-6 border-2 border-indigo-300 border-t-indigo-500 rounded-full animate-spin" />
 </div>
 );
 }

 return (
 <div className="max-w-xl mx-auto px-4 py-10">
 <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-xs text-slate-400 dark:text-slate-500 dark:hover:text-gray-300 mb-6 transition-colors">
 <ArrowLeft className="w-3.5 h-3.5" /> Back
 </Link>

 {/* ── Already researcher / admin ── */}
 {state === 'already_upgraded' && (
 <div className="bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-slate-800 p-8 text-center shadow-sm">
 <div className="w-14 h-14 bg-blue-50 dark:bg-blue-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
 <CheckCircle className="w-7 h-7 text-blue-500" />
 </div>
 <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-2">
 You are already a {user.role === 'admin' ? 'Admin' : 'Researcher'}
 </h2>
 <p className="text-sm text-slate-400 dark:text-slate-500 mb-6">
 Your account already has full {user.role === 'admin' ? 'system administration' : 'research expert'}.
 </p>
 <Link href="/library" className="text-sm bg-indigo-500 hover:bg-indigo-600 text-white px-5 py-2 rounded-xl font-medium transition-colors">
 Go to document library →
 </Link>
 </div>
 )}

 {/* ── Pending ── */}
 {state === 'pending' && (
 <div className="bg-white dark:bg-slate-800/60 rounded-2xl border border-amber-200 dark:border-amber-800/40 p-8 text-center shadow-sm">
 <div className="w-14 h-14 bg-amber-50 dark:bg-amber-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
 <Clock className="w-7 h-7 text-amber-500" />
 </div>
 <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-2">Application Pending Review</h2>
 <p className="text-sm text-slate-400 dark:text-slate-500 mb-4">
 Admin will review your application soon. You will be notified of the result.
 </p>
 {application?.reason && (
 <div className="bg-slate-50 dark:bg-slate-800/40 rounded-xl px-4 py-3 text-left mb-4">
 <p className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide mb-1">Submitted Reason</p>
 <p className="text-sm text-slate-600 dark:text-slate-300">{application.reason}</p>
 </div>
 )}
 {application?.created_at && (
 <p className="text-xs text-slate-400 dark:text-slate-500">
 Submitted at {new Date(application.created_at).toLocaleString('en-US')}
 </p>
 )}
 </div>
 )}

 {/* ── Rejected — allow re-apply ── */}
 {state === 'rejected' && (
 <div className="space-y-5">
 <div className="bg-white dark:bg-slate-800/60 rounded-2xl border border-red-200 dark:border-red-800/40 p-6 shadow-sm">
 <div className="flex items-start gap-3">
 <div className="w-10 h-10 bg-red-50 dark:bg-red-500/10 rounded-xl flex items-center justify-center shrink-0">
 <XCircle className="w-5 h-5 text-red-500" />
 </div>
 <div>
 <p className="font-semibold text-slate-800 dark:text-slate-100 text-sm mb-1">Previous Application Rejected</p>
 {application?.admin_note
 ? <p className="text-xs text-slate-500 dark:text-slate-400">Note: {application.admin_note}</p>
 : <p className="text-xs text-slate-400 dark:text-slate-500">No admin notes.</p>
 }
 </div>
 </div>
 </div>
 <ApplyForm
 reason={reason} setReason={setReason}
 onSubmit={handleSubmit} submitting={submitting} error={error}
 reapply
 />
 </div>
 )}

 {/* ── Apply form ── */}
 {state === 'apply' && (
 <ApplyForm
 reason={reason} setReason={setReason}
 onSubmit={handleSubmit} submitting={submitting} error={error}
 />
 )}

 {/* ── Success ── */}
 {state === 'success' && (
 <div className="bg-white dark:bg-slate-800/60 rounded-2xl border border-emerald-200 dark:border-emerald-800/40 p-8 text-center shadow-sm">
 <div className="w-14 h-14 bg-emerald-50 dark:bg-emerald-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
 <CheckCircle className="w-7 h-7 text-emerald-500" />
 </div>
 <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-2">Application Submitted Successfully!</h2>
 <p className="text-sm text-slate-400 dark:text-slate-500 mb-6">
 Admin will review your application. After approval, your account will be upgraded to <strong>Researcher</strong>.
 </p>
 <Link href="/dashboard" className="text-sm text-indigo-500 hover:text-indigo-600 font-medium">
 ← Back to Dashboard
 </Link>
 </div>
 )}
 </div>
 );
}

// ── Apply form component ───────────────────────────────────────────────────────

function ApplyForm({
 reason, setReason, onSubmit, submitting, error, reapply = false,
}: {
 reason: string;
 setReason: (v: string) => void;
 onSubmit: (e: React.FormEvent) => void;
 submitting: boolean;
 error: string;
 reapply?: boolean;
}) {
 return (
 <div className="bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm overflow-hidden">
 {/* Header */}
 <div className="px-6 pt-7 pb-5 border-b border-slate-100 dark:border-slate-800">
 <div className="flex items-center gap-3 mb-3">
 <div className="w-10 h-10 bg-indigo-50 dark:bg-indigo-500/10 rounded-xl flex items-center justify-center shrink-0">
 <GraduationCap className="w-5 h-5 text-indigo-500" />
 </div>
 <div>
 <h1 className="text-base font-bold text-slate-800 dark:text-slate-100">
 {reapply ? 'Resubmit Researcher Application' : 'Apply for Researcher Account'}
 </h1>
 <p className="text-xs text-slate-400 dark:text-slate-500">Requires Admin approval</p>
 </div>
 </div>

 {/* What researcher can do */}
 <div className="grid grid-cols-1 gap-2 mt-4">
 {[
 'Upload public PDF documents for everyone',
 'Access Literature Review and RAGAS Evaluation',
 'Your documents appear in the public library',
 ].map((item, i) => (
 <div key={i} className="flex items-start gap-2 text-xs text-slate-500 dark:text-slate-400">
 <span className="text-emerald-500 shrink-0 mt-0.5">✓</span>
 {item}
 </div>
 ))}
 </div>
 </div>

 {/* Form */}
 <form onSubmit={onSubmit} className="px-6 py-5 space-y-4">
 <div>
 <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1.5">
 Reason for becoming a Researcher <span className="text-red-400">*</span>
 </label>
 <textarea
 value={reason}
 onChange={e => setReason(e.target.value)}
 rows={4}
 placeholder="Describe your role, research field, or reason for needing public document upload access..."
 className="w-full text-sm px-3 py-2.5 bg-slate-50 dark:bg-slate-800/40 text-slate-800 dark:text-slate-100 rounded-xl border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-300/50 focus:border-transparent resize-none placeholder:text-gray-400 leading-relaxed"
 />
 <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">{reason.length}/500 characters</p>
 </div>

 {error && (
 <p className="text-xs text-red-500 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded-lg">
 {error}
 </p>
 )}

 <button
 type="submit"
 disabled={submitting || !reason.trim()}
 className="w-full flex items-center justify-center gap-2 py-2.5 bg-indigo-500 hover:bg-indigo-600 disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white rounded-xl text-sm font-semibold transition-colors"
 >
 {submitting
 ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Submitting...</>
 : <><Send className="w-4 h-4" /> Submit Application</>
 }
 </button>
 </form>
 </div>
 );
}
