'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useAppStore } from '@/store/useAppStore';
import {
 getProfileSummary, getProfileSymptoms, getLatestInsight, generateInsights,
 getChatHistory, getDocuments,
 getMyProfile, updateMyName, changePassword, uploadAvatar,
 joinOrg, getMyOrg,
 ProfileSummary, ProfileSymptoms, ChatHistoryRecord,
} from '@/lib/api';
import {
 Shield, Upload, Microscope, BarChart2, Network, Users, FileCheck,
 Settings, BookOpen, MessageSquare, Brain, Activity, ClipboardList,
 ChevronRight, Edit3, Calendar, Mail, User, Zap, Crown,
 Camera, Lock, Check, X, Eye, EyeOff, Key,
 GraduationCap, Stethoscope, HeartPulse, Building2, RefreshCw,
} from 'lucide-react';

// ── Helpers ───────────────────────────────────────────────────────────────────

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function resolveAvatar(url: string | null | undefined): string | null {
 if (!url) return null;
 if (url.startsWith('http')) return url;
 return `${API_URL}${url}`;
}

const PAIN_COLOR = (level: number) => {
 if (level <= 3) return '#16a34a';
 if (level <= 5) return '#ca8a04';
 if (level <= 7) return '#ea580c';
 return '#dc2626';
};

const AVATAR_COLORS = [
 '#6366F1', '#0EA5E9', '#10B981', '#F59E0B',
 '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6',
];
function avatarColor(name: string) {
 const code = (name.charCodeAt(0) || 0) + (name.charCodeAt(1) || 0);
 return AVATAR_COLORS[code % AVATAR_COLORS.length];
}
function initials(name: string, email: string) {
 if (name) {
 const p = name.trim().split(/\s+/);
 return p.length >= 2 ? (p[0][0] + p[p.length - 1][0]).toUpperCase() : p[0].slice(0, 2).toUpperCase();
 }
 return email.slice(0, 2).toUpperCase();
}

const ROLE_META: Record<string, { label: string; color: string; bg: string }> = {
 admin: { label: 'Admin', color: 'text-purple-700 dark:text-purple-300', bg: 'bg-purple-100 dark:bg-purple-900/30' },
 researcher: { label: 'Researcher', color: 'text-blue-700 dark:text-blue-300', bg: 'bg-blue-100 dark:bg-blue-900/30' },
 student: { label: 'Student', color: 'text-emerald-700 dark:text-emerald-300', bg: 'bg-emerald-100 dark:bg-emerald-900/30' },
 user: { label: 'Student', color: 'text-emerald-700 dark:text-emerald-300', bg: 'bg-emerald-100 dark:bg-emerald-900/30' },
};

const USER_TYPES: { value: string; label: string; icon: React.ElementType; desc: string }[] = [
 { value: 'user', label: 'User', icon: User, desc: 'General user, explore and discover information.' },
 { value: 'patient', label: 'Patient', icon: HeartPulse, desc: 'Track personal health and lookup medical information.' },
 { value: 'student', label: 'Medical Student', icon: GraduationCap, desc: 'Medical student, academic research.' },
 { value: 'expert', label: 'Expert / Doctor', icon: Stethoscope, desc: 'Healthcare professional, in-depth analysis.' },
];

// ── Shortcut config ───────────────────────────────────────────────────────────

const ADMIN_SHORTCUTS = [
 { href: '/admin', icon: Shield, label: 'Admin Panel', desc: 'System administration', color: 'text-purple-600 dark:text-purple-400', bg: 'bg-purple-50 dark:bg-purple-900/20' },
 { href: '/admin', icon: Users, label: 'User', desc: 'Users & permissions', color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-900/20' },
 { href: '/admin', icon: FileCheck, label: 'Researcher Applications', desc: 'Review applications', color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-900/20' },
 { href: '/library/upload', icon: Upload, label: 'Upload Documents', desc: 'Upload public documents', color: 'text-indigo-600 dark:text-indigo-400', bg: 'bg-indigo-50 dark:bg-indigo-900/20' },
 { href: '/evaluate', icon: BarChart2, label: 'RAGAS Evaluation', desc: 'RAG quality evaluation', color: 'text-indigo-600 dark:text-indigo-400', bg: 'bg-indigo-50 dark:bg-indigo-900/20' },
 { href: '/settings', icon: Settings, label: 'System Settings', desc: 'AI & system configuration', color: 'text-slate-600 dark:text-slate-300', bg: 'bg-slate-100 dark:bg-slate-800/60' },
];

const RESEARCHER_SHORTCUTS = [
 { href: '/library/upload', icon: Upload, label: 'Upload Documents', desc: 'Upload public documents', color: 'text-indigo-600 dark:text-indigo-400', bg: 'bg-indigo-50 dark:bg-indigo-900/20' },
 { href: '/literature', icon: Microscope,label: 'Literature Review',desc: 'AI-generated Related Work', color: 'text-violet-600 dark:text-violet-400', bg: 'bg-violet-50 dark:bg-violet-900/20' },
 { href: '/evaluate', icon: BarChart2, label: 'RAGAS Evaluation', desc: 'RAG quality evaluation', color: 'text-indigo-600 dark:text-indigo-400', bg: 'bg-indigo-50 dark:bg-indigo-900/20' },
 { href: '/graph', icon: Network, label: 'Knowledge Graph', desc: 'Author & article network', color: 'text-sky-600 dark:text-sky-400', bg: 'bg-sky-50 dark:bg-sky-900/20' },
 { href: '/library', icon: BookOpen, label: 'Library', desc: 'Manage your documents', color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-900/20' },
 { href: '/trends', icon: Zap, label: 'Trending Topics', desc: 'Trending research topics', color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-900/20' },
];

// ── Sub-components ─────────────────────────────────────────────────────────────

function UserTypeModal({ current, onSave, onClose }: {
 current: string | null; onSave: (v: string) => void; onClose: () => void;
}) {
 const [selected, setSelected] = useState(current ?? '');
 const overlayRef = useRef<HTMLDivElement>(null);
 return (
 <div ref={overlayRef} className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
 onClick={e => { if (e.target === overlayRef.current) onClose(); }}>
 <div className="bg-white dark:bg-slate-800/60 rounded-2xl shadow-2xl w-full max-w-md border border-slate-100 dark:border-slate-800 overflow-hidden">
 <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-800">
 <div>
 <h2 className="font-bold text-sm text-slate-800 dark:text-slate-100">User Category</h2>
 <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">Personalize your experience</p>
 </div>
 <button onClick={onClose} className="w-7 h-7 flex items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800/60 text-slate-400 dark:text-slate-500 dark:hover:text-gray-300 text-sm">✕</button>
 </div>
 <div className="p-4 space-y-2.5">
 {USER_TYPES.map(t => {
 const Icon = t.icon;
 return (
 <button key={t.value} onClick={() => setSelected(t.value)}
 className={`w-full text-left flex items-center gap-3.5 p-3.5 rounded-xl border-2 transition-all ${
 selected === t.value ? 'border-indigo-400 bg-indigo-50 dark:bg-indigo-900/20' : 'border-slate-100 dark:border-slate-800 hover:border-gray-200 dark:hover:border-gray-700'
 }`}>
 <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
 selected === t.value ? 'bg-indigo-100 dark:bg-indigo-900/40' : 'bg-slate-100 dark:bg-slate-800/60'
 }`}>
 <Icon className={`w-5 h-5 ${selected === t.value ? 'text-indigo-500' : 'text-slate-400 dark:text-slate-500'}`} />
 </div>
 <div className="flex-1 min-w-0">
 <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{t.label}</p>
 <p className="text-xs text-slate-400 dark:text-slate-500 leading-relaxed">{t.desc}</p>
 </div>
 {selected === t.value && <Check className="w-4 h-4 text-indigo-500 shrink-0" />}
 </button>
 );
 })}
 </div>
 <div className="flex gap-2.5 px-4 pb-4">
 <button onClick={onClose} className="flex-1 py-2.5 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 rounded-xl text-sm font-medium hover:bg-slate-100 dark:hover:bg-slate-800/60 dark:hover:bg-gray-800 transition-colors">Cancel</button>
 <button onClick={() => { if (selected) onSave(selected); }} disabled={!selected}
 className="flex-1 py-2.5 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl text-sm font-semibold transition-colors disabled:opacity-40">Save</button>
 </div>
 </div>
 </div>
 );
}

function ShortcutCard({ href, icon: Icon, label, desc, color, bg }: {
 href: string; icon: React.ElementType; label: string; desc: string; color: string; bg: string;
}) {
 return (
 <Link href={href} className="group flex items-center gap-3 p-3.5 bg-white dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 hover:border-indigo-200 dark:hover:border-indigo-800 hover:shadow-md transition-all">
 <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${bg}`}>
 <Icon className={`w-4.5 h-4.5 ${color}`} size={18} />
 </div>
 <div className="min-w-0 flex-1">
 <p className="text-xs font-semibold text-slate-800 dark:text-slate-100 leading-tight">{label}</p>
 <p className="text-[10px] text-slate-400 dark:text-slate-500 truncate mt-0.5">{desc}</p>
 </div>
 <ChevronRight className="w-3.5 h-3.5 text-slate-300 dark:text-slate-600 group-hover:text-indigo-400 transition-colors shrink-0" />
 </Link>
 );
}

// ── Main page ─────────────────────────────────────────────────────────────────

type ActiveTab = 'account' | 'symptoms' | 'history' | 'insights';

export default function ProfilePage() {
 const { user, updateUser } = useAppStore();

 const [userId, setUserId] = useState<string | null>(null);
 const [summary, setSummary] = useState<ProfileSummary | null>(null);
 const [symptoms, setSymptoms] = useState<ProfileSymptoms | null>(null);
 const [insight, setInsight] = useState<string | null>(null);
 const [history, setHistory] = useState<ChatHistoryRecord[]>([]);
 const [docCount, setDocCount] = useState(0);
 const [loading, setLoading] = useState(true);
 const [generating, setGenerating] = useState(false);
 const [activeTab, setActiveTab] = useState<ActiveTab>('account');
 const [userType, setUserType] = useState<string | null>(null);
 const [typeModal, setTypeModal] = useState(false);

 // Edit states
 const [editName, setEditName] = useState(false);
 const [nameInput, setNameInput] = useState('');
 const [nameSaving, setNameSaving] = useState(false);
 const [nameMsg, setNameMsg] = useState('');

 const [showPwForm, setShowPwForm] = useState(false);
 const [pwForm, setPwForm] = useState({ current: '', next: '', confirm: '' });
 const [showPw, setShowPw] = useState({ current: false, next: false, confirm: false });
 const [pwSaving, setPwSaving] = useState(false);
 const [pwMsg, setPwMsg] = useState('');
 const [pwError, setPwError] = useState('');

 const [avatarUploading, setAvatarUploading] = useState(false);
 const fileInputRef = useRef<HTMLInputElement>(null);

 // Join org state
 const [joinCode, setJoinCode] = useState('');
 const [joinBusy, setJoinBusy] = useState(false);
 const [joinMsg, setJoinMsg] = useState('');
 const [joinErr, setJoinErr] = useState('');
 const [orgMembership, setOrgMembership] = useState<{ org_name: string; expires_at: string; duration_label: string; status: string } | null>(null);

 useEffect(() => {
 if (typeof window === 'undefined') return;
 const savedType = localStorage.getItem('user_type');
 if (savedType) setUserType(savedType);

 let uid: string | null = null;
 try { uid = JSON.parse(localStorage.getItem('user') ?? '{}')?.id ?? null; } catch {}
 if (!uid) uid = localStorage.getItem('user_id');
 setUserId(uid);
 if (!uid) { setLoading(false); return; }

 const fallbackSummary = { symptom_count: 0, chat_count: 0, user_type: '', onboarding_done: false };
 const fallbackSymptoms = { total: 0, avg_pain: 0, region_counts: {}, symptoms: [] };

 Promise.all([
 getProfileSummary(uid).catch(() => fallbackSummary),
 getProfileSymptoms(uid).catch(() => fallbackSymptoms),
 getLatestInsight(uid).catch(() => ({ insight: null })),
 getChatHistory(uid, 20).catch(() => ({ total: 0, history: [] })),
 getDocuments().catch(() => []),
 getMyProfile().catch(() => null),
 ]).then(([s, sym, ins, hist, docs, me]) => {
 setSummary(s);
 setSymptoms(sym);
 setInsight(ins.insight);
 setHistory(hist.history);
 setDocCount(Array.isArray(docs) ? docs.length : 0);
 if (!savedType && s.user_type) setUserType(s.user_type);
 if (me) updateUser({ avatar_url: me.avatar_url, is_oauth: me.is_oauth, full_name: me.full_name, plan: me.plan });
 // Load org membership info
 getMyOrg().then(org => {
 if (org.role === 'member') setOrgMembership({ org_name: org.org_name!, expires_at: org.expires_at!, duration_label: org.duration_label!, status: org.status! });
 }).catch(() => {});
 }).finally(() => setLoading(false));
 }, []);

 const handleJoinOrg = async () => {
 if (!joinCode.trim()) return;
 setJoinBusy(true); setJoinErr(''); setJoinMsg('');
 try {
 const res = await joinOrg(joinCode.trim());
 setJoinMsg(`Joined ${res.org_name}! Duration: ${res.duration_label}`);
 setOrgMembership({ org_name: res.org_name, expires_at: res.expires_at, duration_label: res.duration_label, status: 'active' });
 updateUser({ plan: 'enterprise' });
 setJoinCode('');
 } catch (e: unknown) {
 setJoinErr((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Invalid invite code');
 } finally { setJoinBusy(false); }
 };

 const handleSaveType = (v: string) => {
 setUserType(v);
 localStorage.setItem('user_type', v);
 setTypeModal(false);
 };

 const handleGenerateInsights = async () => {
 if (!userId) return;
 setGenerating(true);
 try {
 const res = await generateInsights(userId);
 setInsight(res.health_insight);
 setActiveTab('insights');
 } catch { alert('Error generating analysis. Try again later.'); }
 finally { setGenerating(false); }
 };

 const handleSaveName = async (e: React.FormEvent) => {
 e.preventDefault();
 if (!nameInput.trim()) return;
 setNameSaving(true); setNameMsg('');
 try {
 const res = await updateMyName(nameInput.trim());
 updateUser({ full_name: res.full_name });
 setEditName(false);
 setNameMsg('Name updated!');
 setTimeout(() => setNameMsg(''), 3000);
 } catch {
 setNameMsg('Update failed. Try again.');
 } finally {
 setNameSaving(false);
 }
 };

 const handleChangePw = async (e: React.FormEvent) => {
 e.preventDefault();
 if (pwForm.next !== pwForm.confirm) { setPwError('Password confirmation does not match'); return; }
 if (pwForm.next.length < 6) { setPwError('New password must be at least 6 characters'); return; }
 setPwSaving(true); setPwError(''); setPwMsg('');
 try {
 await changePassword(pwForm.current, pwForm.next);
 setPwMsg('Password changed successfully!');
 setPwForm({ current: '', next: '', confirm: '' });
 setShowPwForm(false);
 updateUser({ is_oauth: false });
 setTimeout(() => setPwMsg(''), 3000);
 } catch (err: unknown) {
 const errWithResponse = err as { response?: { data?: { detail?: string } } };
 const msg = errWithResponse?.response?.data?.detail;
 setPwError(msg || 'Current password is incorrect');
 } finally {
 setPwSaving(false);
 }
 };

 const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
 const file = e.target.files?.[0];
 if (!file) return;
 setAvatarUploading(true);
 try {
 const res = await uploadAvatar(file);
 updateUser({ avatar_url: res.avatar_url });
 } catch { alert('Error uploading photo. Try again.'); }
 finally {
 setAvatarUploading(false);
 if (fileInputRef.current) fileInputRef.current.value = '';
 }
 };

 // ── Loading & unauthenticated ──────────────────────────────────────────────

 if (!userId && !loading) {
 return (
 <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-6">
 <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800/60 rounded-2xl flex items-center justify-center mb-4">
 <User className="w-8 h-8 text-slate-400 dark:text-slate-500" />
 </div>
 <h2 className="text-lg font-bold text-slate-700 dark:text-slate-200 mb-2">Not Logged In</h2>
 <p className="text-sm text-slate-400 dark:text-slate-500 mb-5">Log in to view your profile.</p>
 <Link href="/login" className="text-sm bg-indigo-500 hover:bg-indigo-600 text-white px-5 py-2.5 rounded-xl font-medium transition-colors">
 Log in
 </Link>
 </div>
 );
 }

 if (loading) {
 return (
 <div className="flex items-center justify-center min-h-[60vh]">
 <div className="w-6 h-6 border-2 border-indigo-300 border-t-indigo-500 rounded-full animate-spin" />
 </div>
 );
 }

 const role = user?.role ?? 'student';
 const roleMeta = ROLE_META[role] ?? ROLE_META.student;
 const name = user?.full_name ?? '';
 const email = user?.email ?? '';
 const isOAuth = user?.is_oauth ?? false;
 const avatarUrl = resolveAvatar(user?.avatar_url);
 const avi = initials(name, email);
 const aviColor = avatarColor(name || email);
 const shortcuts = role === 'admin' ? ADMIN_SHORTCUTS : role === 'researcher' ? RESEARCHER_SHORTCUTS : null;

 const TABS: { key: ActiveTab; label: string; icon: React.ElementType }[] = [
 { key: 'account', label: 'Account', icon: User },
 { key: 'symptoms', label: 'Health', icon: Activity },
 { key: 'history', label: 'Chat History', icon: MessageSquare },
 { key: 'insights', label: 'AI Insights', icon: Brain },
 ];

 return (
 <div className="max-w-4xl mx-auto p-5 pb-10 space-y-5">

 {/* ── Hero card ── */}
 <div className="bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-slate-800 overflow-hidden shadow-sm">
 <div className="h-24 bg-gradient-to-br from-indigo-500/15 via-purple-500/10 to-sky-500/15 dark:from-indigo-900/40 dark:via-purple-900/30 dark:to-sky-900/30" />

 <div className="px-6 pb-5">
 <div className="flex items-end justify-between -mt-10 mb-3">

 {/* Avatar with upload */}
 <div className="relative">
 {avatarUrl ? (
 <img
 src={avatarUrl}
 alt={name}
 className="w-20 h-20 rounded-2xl object-cover shadow-lg ring-4 ring-white dark:ring-gray-900"
 />
 ) : (
 <div
 className="w-20 h-20 rounded-2xl flex items-center justify-center text-white text-2xl font-bold shadow-lg ring-4 ring-white dark:ring-gray-900"
 style={{ backgroundColor: aviColor }}
 >
 {avi}
 </div>
 )}
 <button
 onClick={() => fileInputRef.current?.click()}
 disabled={avatarUploading}
 className="absolute -bottom-1.5 -right-1.5 w-7 h-7 bg-indigo-500 hover:bg-indigo-600 rounded-full flex items-center justify-center shadow-md transition-colors disabled:opacity-50"
 title="Change avatar"
 >
 {avatarUploading
 ? <span className="w-3 h-3 border border-white/40 border-t-white rounded-full animate-spin" />
 : <Camera className="w-3.5 h-3.5 text-white" />
 }
 </button>
 <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleAvatarUpload} />
 </div>

 <button
 onClick={() => setTypeModal(true)}
 className="flex items-center gap-1.5 text-xs text-slate-400 dark:text-slate-500 hover:text-indigo-500 dark:hover:text-indigo-400 transition-colors mb-1 px-3 py-1.5 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/20 dark:hover:bg-indigo-900/20"
 >
 <Edit3 className="w-3.5 h-3.5" /> Change user type
 </button>
 </div>

 <div className="flex flex-wrap items-center gap-2 mb-0.5">
 <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100">{name || 'User'}</h1>
 <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${roleMeta.bg} ${roleMeta.color}`}>
 {roleMeta.label}
 </span>
 {isOAuth && (
 <span className="text-xs text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-800/60 px-2 py-0.5 rounded-full flex items-center gap-1">
 <svg className="w-3 h-3" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
 Google
 </span>
 )}
 {userType && (() => {
 const ut = USER_TYPES.find(t => t.value === userType);
 if (!ut) return null;
 const UtIcon = ut.icon;
 return (
 <span className="inline-flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800/60 px-2.5 py-0.5 rounded-full">
 <UtIcon className="w-3 h-3" />{ut.label}
 </span>
 );
 })()}
 </div>
 <p className="text-sm text-slate-400 dark:text-slate-500">{email}</p>
 </div>

 {/* Stats strip */}
 <div className="grid grid-cols-2 sm:grid-cols-4 border-t border-slate-100 dark:border-slate-800 divide-x divide-slate-100 dark:divide-slate-800">
 {[
 { label: 'Documents', value: docCount, icon: BookOpen },
 { label: 'Q&A', value: summary?.chat_count ?? 0, icon: MessageSquare },
 { label: 'Symptoms', value: symptoms?.total ?? 0, icon: Activity },
 { label: 'Avg Pain', value: symptoms?.avg_pain ? `${symptoms.avg_pain.toFixed(1)}/10` : '—', icon: ClipboardList },
 ].map(({ label, value, icon: Icon }) => (
 <div key={label} className="flex flex-col items-center py-3.5 gap-0.5">
 <Icon className="w-4 h-4 text-slate-300 dark:text-slate-600 mb-0.5" />
 <p className="text-lg font-bold text-slate-800 dark:text-slate-100">{value}</p>
 <p className="text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-wide">{label}</p>
 </div>
 ))}
 </div>
 </div>

 {/* ── Plan banner ── */}
 {(() => {
 const plan = user?.plan ?? 'free';
 const planLabels: Record<string, string> = { free: 'Freemium', pro: 'Pro', researcher: 'Researcher', enterprise: 'Enterprise' };
 const label = planLabels[plan] ?? 'Freemium';
 const isFree = plan === 'free' && role !== 'admin';
 return (
 <div className={`flex items-center justify-between gap-3 px-4 py-3 rounded-xl border ${
 isFree
 ? 'bg-amber-50 dark:bg-amber-900/10 border-amber-200 dark:border-amber-800'
 : 'bg-indigo-50 dark:bg-indigo-900/10 border-indigo-200 dark:border-indigo-800'
 }`}>
 <div className="flex items-center gap-2.5">
 <Crown className={`w-4 h-4 ${isFree ? 'text-amber-500' : 'text-indigo-500'}`} />
 <div>
 <p className="text-xs font-semibold text-slate-800 dark:text-slate-100">
 Current Plan: <span className={isFree ? 'text-amber-600 dark:text-amber-400' : 'text-indigo-600 dark:text-indigo-400'}>{label}</span>
 </p>
 {isFree && (
 <p className="text-[10px] text-slate-500 dark:text-slate-400">
 Limited to 5 documents & 50 questions/day
 </p>
 )}
 </div>
 </div>
 <Link
 href="/pricing"
 className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors ${
 isFree
 ? 'bg-amber-500 hover:bg-amber-600 text-white'
 : 'bg-indigo-100 dark:bg-indigo-800 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-200 dark:hover:bg-indigo-700'
 }`}
 >
 {isFree ? 'Upgrade' : 'View plans'}
 </Link>
 </div>
 );
 })()}

 {/* ── Org membership / join ── */}
 {user?.plan !== 'admin' && (
 <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 p-4 space-y-3">
 <div className="flex items-center gap-2">
 <Building2 className="w-4 h-4 text-indigo-500" />
 <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">Organization</p>
 </div>
 {orgMembership ? (
 <div className="flex items-center justify-between gap-3 text-sm">
 <div>
 <p className="font-medium text-slate-800 dark:text-slate-100">{orgMembership.org_name}</p>
 <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">
 {orgMembership.duration_label} · Expires {new Date(orgMembership.expires_at).toLocaleDateString('en-US')}
 </p>
 </div>
 <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
 orgMembership.status === 'active'
 ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
 : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
 }`}>
 {orgMembership.status === 'active' ? 'Active' : 'Revoked'}
 </span>
 </div>
 ) : (
 <div className="space-y-2">
 <p className="text-xs text-slate-400 dark:text-slate-500">Enter invite code from your school/organization for free Enterprise upgrade.</p>
 <div className="flex gap-2">
 <input
 type="text"
 value={joinCode}
 onChange={e => setJoinCode(e.target.value.toUpperCase())}
 onKeyDown={e => e.key === 'Enter' && handleJoinOrg()}
 placeholder="ORGXXXXXXXX"
 className="flex-1 text-sm font-mono px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
 />
 <button
 onClick={handleJoinOrg}
 disabled={joinBusy || !joinCode.trim()}
 className="text-sm px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium transition-colors disabled:opacity-40"
 >
 {joinBusy ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Join'}
 </button>
 </div>
 {joinMsg && <p className="text-xs text-emerald-500">{joinMsg}</p>}
 {joinErr && <p className="text-xs text-red-500">{joinErr}</p>}
 </div>
 )}
 {user?.plan === 'enterprise' && !orgMembership && (
 <Link href="/org" className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:underline">
 Your Organization →
 </Link>
 )}
 </div>
 )}

 {/* ── Role shortcuts ── */}
 {shortcuts && (
 <div>
 <div className="flex items-center gap-2 mb-3">
 <div className={`w-5 h-5 rounded-md flex items-center justify-center ${role === 'admin' ? 'bg-purple-100 dark:bg-purple-900/30' : 'bg-blue-100 dark:bg-blue-900/30'}`}>
 {role === 'admin' ? <Shield size={12} className="text-purple-600 dark:text-purple-400" /> : <Zap size={12} className="text-blue-600 dark:text-blue-400" />}
 </div>
 <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
 Shortcuts {role === 'admin' ? 'Admin' : 'Researcher'}
 </h2>
 </div>
 <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
 {shortcuts.map(s => <ShortcutCard key={s.href + s.label} {...s} />)}
 </div>
 </div>
 )}

 {/* ── Tabs ── */}
 <div className="bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-slate-800 overflow-hidden shadow-sm">

 <div className="flex border-b border-slate-100 dark:border-slate-800 overflow-x-auto">
 {TABS.map(({ key, label, icon: Icon }) => (
 <button key={key} onClick={() => setActiveTab(key)}
 className={`flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
 activeTab === key ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400' : 'border-transparent text-slate-400 dark:text-slate-500 dark:hover:text-gray-300'
 }`}>
 <Icon className="w-3.5 h-3.5" />
 {label}
 </button>
 ))}
 </div>

 {/* ── Tab: Account ── */}
 {activeTab === 'account' && (
 <div className="p-5 space-y-6">

 {/* Personal Information */}
 <div>
 <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-3">Personal Information</h3>
 <div className="space-y-1">

 {/* Full name — editable */}
 <div className="flex items-center gap-3 py-3 border-b border-gray-50">
 <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800/60 flex items-center justify-center shrink-0">
 <User className="w-4 h-4 text-slate-400 dark:text-slate-500" />
 </div>
 <div className="flex-1 min-w-0">
 <p className="text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-wide mb-0.5">Full name</p>
 {editName ? (
 <form onSubmit={handleSaveName} className="flex items-center gap-2 mt-1">
 <input
 value={nameInput}
 onChange={e => setNameInput(e.target.value)}
 autoFocus
 className="flex-1 text-sm px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/40 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
 />
 <button type="submit" disabled={nameSaving || !nameInput.trim()}
 className="w-7 h-7 flex items-center justify-center bg-indigo-500 hover:bg-indigo-600 rounded-lg text-white disabled:opacity-40">
 {nameSaving ? <span className="w-3 h-3 border border-white/40 border-t-white rounded-full animate-spin" /> : <Check className="w-3.5 h-3.5" />}
 </button>
 <button type="button" onClick={() => setEditName(false)}
 className="w-7 h-7 flex items-center justify-center bg-slate-100 dark:bg-slate-800/60 hover:bg-slate-200 dark:hover:bg-slate-700 dark:hover:bg-gray-700 rounded-lg text-slate-500 dark:text-slate-400">
 <X className="w-3.5 h-3.5" />
 </button>
 </form>
 ) : (
 <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{name || '—'}</p>
 )}
 </div>
 {!editName && (
 <button onClick={() => { setNameInput(name); setEditName(true); }}
 className="shrink-0 w-7 h-7 flex items-center justify-center rounded-lg text-slate-300 dark:text-slate-600 hover:text-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 dark:hover:bg-indigo-900/20 transition-colors">
 <Edit3 className="w-3.5 h-3.5" />
 </button>
 )}
 </div>
 {nameMsg && (
 <p className={`text-xs px-2 py-1 ${nameMsg.includes('Error') ? 'text-red-500' : 'text-emerald-600'}`}>{nameMsg}</p>
 )}

 {/* Email — read only */}
 <div className="flex items-center gap-3 py-3 border-b border-gray-50">
 <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800/60 flex items-center justify-center shrink-0">
 <Mail className="w-4 h-4 text-slate-400 dark:text-slate-500" />
 </div>
 <div className="flex-1 min-w-0">
 <p className="text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-wide">Email</p>
 <p className="text-sm font-medium text-slate-800 dark:text-slate-100 truncate">{email || '—'}</p>
 </div>
 </div>

 {/* Role */}
 <div className="flex items-center gap-3 py-3 border-b border-gray-50">
 <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800/60 flex items-center justify-center shrink-0">
 <Shield className="w-4 h-4 text-slate-400 dark:text-slate-500" />
 </div>
 <div className="flex-1">
 <p className="text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-wide">System Role</p>
 <span className={`inline-block mt-0.5 text-xs font-semibold px-2.5 py-0.5 rounded-full ${roleMeta.bg} ${roleMeta.color}`}>
 {roleMeta.label}
 </span>
 </div>
 </div>

 {/* User type */}
 <div className="flex items-center gap-3 py-3">
 <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800/60 flex items-center justify-center shrink-0">
 <Calendar className="w-4 h-4 text-slate-400 dark:text-slate-500" />
 </div>
 <div className="flex-1">
 <p className="text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-wide">User Type</p>
 {(() => {
 const ut = USER_TYPES.find(t => t.value === userType);
 if (!ut) return <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Not categorized</p>;
 const UtIcon = ut.icon;
 return (
 <p className="text-sm font-medium text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
 <UtIcon className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />{ut.label}
 </p>
 );
 })()}
 </div>
 <button onClick={() => setTypeModal(true)} className="text-xs text-indigo-500 hover:text-indigo-600 shrink-0">Change</button>
 </div>
 </div>
 </div>

 {/* Security */}
 <div>
 <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-3">Security</h3>

 {isOAuth && !showPwForm && (
 <div className="mb-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-100 dark:border-blue-800/40 text-xs text-blue-600 dark:text-blue-400">
 Google account — you can set a password for email login.
 </div>
 )}
 {pwMsg && (
 <p className="text-xs text-emerald-600 dark:text-emerald-400 mb-3 px-1">{pwMsg}</p>
 )}

 {!showPwForm ? (
 <button
 onClick={() => { setShowPwForm(true); setPwError(''); setPwMsg(''); }}
 className="flex items-center gap-2.5 px-4 py-2.5 bg-slate-100 dark:bg-slate-800/60 hover:bg-slate-200 dark:hover:bg-slate-700 dark:hover:bg-gray-700 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 transition-colors"
 >
 <Key className="w-4 h-4 text-slate-400 dark:text-slate-500" />
 {isOAuth ? 'Set Password' : 'Change Password'}
 </button>
 ) : (
 <form onSubmit={handleChangePw} className="space-y-3 bg-slate-50 dark:bg-slate-800/40 rounded-xl p-4 border border-slate-100 dark:border-slate-800">
 {!isOAuth && (
 <div className="relative">
 <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
 <input
 type={showPw.current ? 'text' : 'password'}
 value={pwForm.current}
 onChange={e => setPwForm(f => ({ ...f, current: e.target.value }))}
 placeholder="Current Password"
 className="w-full pl-9 pr-9 py-2 text-sm border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 rounded-lg text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
 />
 <button type="button" onClick={() => setShowPw(s => ({ ...s, current: !s.current }))}
 className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500">
 {showPw.current ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
 </button>
 </div>
 )}
 <div className="relative">
 <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
 <input
 type={showPw.next ? 'text' : 'password'}
 value={pwForm.next}
 onChange={e => setPwForm(f => ({ ...f, next: e.target.value }))}
 placeholder="New Password (min 6 characters)"
 className="w-full pl-9 pr-9 py-2 text-sm border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 rounded-lg text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
 />
 <button type="button" onClick={() => setShowPw(s => ({ ...s, next: !s.next }))}
 className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500">
 {showPw.next ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
 </button>
 </div>
 <div className="relative">
 <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
 <input
 type={showPw.confirm ? 'text' : 'password'}
 value={pwForm.confirm}
 onChange={e => setPwForm(f => ({ ...f, confirm: e.target.value }))}
 placeholder="Confirm New Password"
 className={`w-full pl-9 pr-9 py-2 text-sm border rounded-lg bg-white dark:bg-slate-800/60 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-300/50 ${
 pwForm.confirm && pwForm.confirm !== pwForm.next ? 'border-red-400' : 'border-slate-200 dark:border-slate-700'
 }`}
 />
 <button type="button" onClick={() => setShowPw(s => ({ ...s, confirm: !s.confirm }))}
 className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500">
 {showPw.confirm ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
 </button>
 </div>
 {pwError && <p className="text-xs text-red-500">{pwError}</p>}
 <div className="flex gap-2 pt-1">
 <button type="submit" disabled={pwSaving}
 className="flex-1 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-40 flex items-center justify-center gap-2">
 {pwSaving ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : null}
 {isOAuth ? 'Set Password' : 'Change Password'}
 </button>
 <button type="button" onClick={() => { setShowPwForm(false); setPwError(''); setPwForm({ current: '', next: '', confirm: '' }); }}
 className="px-4 py-2 bg-slate-200 dark:bg-slate-700 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-lg text-sm text-slate-600 dark:text-slate-300 transition-colors">
 Cancel
 </button>
 </div>
 </form>
 )}
 </div>

 {/* Role info box */}
 {role === 'admin' && (
 <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-xl border border-purple-200 dark:border-purple-800/40">
 <p className="text-xs font-semibold text-purple-700 dark:text-purple-300 mb-1">Admin Access</p>
 <p className="text-xs text-purple-600/80 dark:text-purple-400/80 leading-relaxed">
 You have full system administration access, user management, Researcher application review, and access to all features.
 </p>
 </div>
 )}
 {role === 'researcher' && (
 <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800/40">
 <p className="text-xs font-semibold text-blue-700 dark:text-blue-300 mb-1">Researcher Access</p>
 <p className="text-xs text-blue-600/80 dark:text-blue-400/80 leading-relaxed">
 You can publish public documents, use Literature Review, RAGAS Evaluation and advanced research tools.
 </p>
 </div>
 )}
 {(role === 'student' || role === 'user') && (
 <div className="p-4 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-700">
 <p className="text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Account Student</p>
 <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-2">
 Your uploaded documents are private. Apply as Researcher to publish public documents and unlock research tools.
 </p>
 <Link href="/researcher-apply" className="inline-flex items-center gap-1.5 text-xs text-indigo-600 dark:text-indigo-400 font-medium hover:underline">
 Sign up Researcher <ChevronRight className="w-3 h-3" />
 </Link>
 </div>
 )}
 </div>
 )}

 {/* ── Tab: Health ── */}
 {activeTab === 'symptoms' && (
 <div className="p-5">
 <div className="flex items-center justify-between mb-5">
 <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest">Recorded Symptoms</h3>
 <button onClick={handleGenerateInsights} disabled={generating || (symptoms?.total ?? 0) === 0}
 className="flex items-center gap-1.5 text-xs bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white px-3 py-1.5 rounded-lg font-medium disabled:opacity-40 transition-all">
 <Brain className="w-3.5 h-3.5" />
 {generating ? 'Analyzing...' : 'AI Analysis'}
 </button>
 </div>
 {symptoms && Object.keys(symptoms.region_counts).length > 0 && (
 <div className="bg-slate-50 dark:bg-slate-800/40 rounded-xl p-4 mb-4">
 <p className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-3">Affected Areas</p>
 <div className="space-y-2">
 {Object.entries(symptoms.region_counts).sort(([, a], [, b]) => b - a).map(([region, count]) => {
 const max = Math.max(...Object.values(symptoms.region_counts));
 return (
 <div key={region} className="flex items-center gap-3">
 <span className="text-xs text-slate-600 dark:text-slate-300 w-28 shrink-0 truncate">{region}</span>
 <div className="flex-1 bg-slate-200 dark:bg-slate-700 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
 <div className="h-2 rounded-full bg-indigo-400 transition-all" style={{ width: `${(count / max) * 100}%` }} />
 </div>
 <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 w-5 text-right">{count}</span>
 </div>
 );
 })}
 </div>
 </div>
 )}
 {(symptoms?.symptoms ?? []).length === 0 ? (
 <div className="text-center py-12">
 <Activity className="w-10 h-10 text-gray-200 dark:text-gray-700 mx-auto mb-3" />
 <p className="text-sm text-slate-400 dark:text-slate-500">No symptoms recorded yet.</p>
 <Link href="/3d" className="text-xs text-indigo-500 hover:underline mt-1 block">Use 3D Atlas to report →</Link>
 </div>
 ) : (
 <div className="space-y-2.5">
 {symptoms!.symptoms.map(s => (
 <div key={s.id} className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
 <div className="flex-1 min-w-0">
 <div className="flex items-center gap-2 mb-1 flex-wrap">
 <span className="text-[10px] font-semibold px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-300 rounded-full">{s.region_name}</span>
 {s.duration && <span className="text-[10px] text-slate-400 dark:text-slate-500">{s.duration}</span>}
 </div>
 <p className="text-xs text-slate-700 dark:text-slate-200 leading-relaxed">{s.description}</p>
 </div>
 <div className="text-right shrink-0">
 <p className="text-base font-bold" style={{ color: PAIN_COLOR(s.pain_level) }}>{s.pain_level}/10</p>
 <p className="text-[10px] text-slate-400 dark:text-slate-500">{s.reported_at ? s.reported_at.slice(0, 10) : ''}</p>
 </div>
 </div>
 ))}
 </div>
 )}
 </div>
 )}

 {/* ── Tab: Chat History ── */}
 {activeTab === 'history' && (
 <div className="p-5">
 <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-4">Recent History</h3>
 {history.length === 0 ? (
 <div className="text-center py-12">
 <MessageSquare className="w-10 h-10 text-gray-200 dark:text-gray-700 mx-auto mb-3" />
 <p className="text-sm text-slate-400 dark:text-slate-500">No chat history yet.</p>
 <Link href="/chat" className="text-xs text-indigo-500 hover:underline mt-1 block">Start AI Q&A →</Link>
 </div>
 ) : (
 <div className="space-y-3">
 {history.map(h => (
 <div key={h.id} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
 <div className="flex items-start gap-2 mb-2">
 <span className="text-[10px] font-semibold text-indigo-500 bg-indigo-50 dark:bg-indigo-900/20 px-2 py-0.5 rounded-full shrink-0 mt-0.5">Q</span>
 <p className="text-sm font-medium text-slate-800 dark:text-slate-100 leading-snug">{h.query}</p>
 </div>
 <div className="flex items-start gap-2">
 <span className="text-[10px] font-semibold text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 px-2 py-0.5 rounded-full shrink-0 mt-0.5">A</span>
 <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed line-clamp-2">{h.answer}</p>
 </div>
 <p className="text-[10px] text-slate-300 dark:text-slate-600 mt-2 text-right">{h.created_at?.slice(0, 16) ?? ''}</p>
 </div>
 ))}
 </div>
 )}
 </div>
 )}

 {/* ── Tab: AI Insights ── */}
 {activeTab === 'insights' && (
 <div className="p-5">
 <div className="flex items-center justify-between mb-4">
 <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest">AI Health Insights</h3>
 <button onClick={handleGenerateInsights} disabled={generating || (symptoms?.total ?? 0) === 0}
 className="flex items-center gap-1.5 text-xs bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white px-3 py-1.5 rounded-lg font-medium disabled:opacity-40 transition-all">
 <Brain className="w-3.5 h-3.5" />
 {generating ? 'Analyzing...' : 'Generate'}
 </button>
 </div>
 {!insight ? (
 <div className="text-center py-12">
 <Brain className="w-10 h-10 text-gray-200 dark:text-gray-700 mx-auto mb-3" />
 <p className="text-sm text-slate-400 dark:text-slate-500 mb-1">Click "Generate" for AI analysis.</p>
 <p className="text-xs text-slate-400 dark:text-slate-500">Requires at least 1 symptom.</p>
 </div>
 ) : (
 <div>
 <div className="text-sm text-slate-700 dark:text-slate-200 leading-relaxed whitespace-pre-wrap bg-slate-50 dark:bg-slate-800/40 rounded-xl p-4 border border-slate-100 dark:border-slate-800 mb-3">
 {insight}
 </div>
 <div className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-100 dark:border-amber-800/40">
 <p className="text-xs text-amber-600 dark:text-amber-400">
 Preliminary AI assessment, not a substitute for professional medical diagnosis. Consult a doctor when needed.
 </p>
 </div>
 </div>
 )}
 </div>
 )}
 </div>

 {typeModal && <UserTypeModal current={userType} onSave={handleSaveType} onClose={() => setTypeModal(false)} />}
 </div>
 );
}
