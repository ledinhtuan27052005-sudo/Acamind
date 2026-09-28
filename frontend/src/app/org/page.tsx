'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useAppStore } from '@/store/useAppStore';
import {
 getMyOrg, createOrg, listInviteCodes, createInviteCode, deactivateInviteCode,
 listOrgMembers, kickOrgMember, updateOrgSettings,
 OrgInfo, OrgInviteCode, OrgMember,
} from '@/lib/api';
import {
 Building2, Users, Copy, Check, Trash2, Plus, ArrowLeft,
 RefreshCw, Clock, CheckCircle2, XCircle, ChevronDown, Settings, FileText,
} from 'lucide-react';

// ── Helpers ───────────────────────────────────────────────────────────────────

function CopyBtn({ text }: { text: string }) {
 const [copied, setCopied] = useState(false);
 return (
 <button
 onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
 className="ml-1.5 p-1 rounded text-slate-400 dark:text-slate-500 hover:text-indigo-600 transition-colors"
 >
 {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
 </button>
 );
}

function StatusBadge({ status }: { status: string }) {
 const map: Record<string, { cls: string; label: string; icon: React.ReactNode }> = {
 active: { cls: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300', label: 'Active', icon: <CheckCircle2 className="w-3 h-3" /> },
 revoked: { cls: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300', label: 'Revoked', icon: <XCircle className="w-3 h-3" /> },
 expired: { cls: 'bg-slate-100 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 dark:bg-gray-700', label: 'Expired', icon: <Clock className="w-3 h-3" /> },
 };
 const m = map[status] ?? map.expired;
 return (
 <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${m.cls}`}>
 {m.icon}{m.label}
 </span>
 );
}

const DURATIONS = [
 { value: 1, label: '1 month' },
 { value: 3, label: '3 months' },
 { value: 12, label: '1 year' },
 { value: 48, label: '4 years' },
];

// ── Create org form ───────────────────────────────────────────────────────────

function CreateOrgForm({ onCreated }: { onCreated: (org: OrgInfo) => void }) {
 const [name, setName] = useState('');
 const [busy, setBusy] = useState(false);
 const [err, setErr] = useState('');

 const submit = async () => {
 if (!name.trim()) return;
 setBusy(true); setErr('');
 try {
 const org = await createOrg(name.trim());
 onCreated(org);
 } catch (e: unknown) {
 setErr((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Error creating organization');
 } finally { setBusy(false); }
 };

 return (
 <div className="max-w-md mx-auto mt-16 p-8 bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm text-center space-y-5">
 <div className="w-14 h-14 mx-auto rounded-2xl bg-indigo-50 dark:bg-indigo-900/30 flex items-center justify-center">
 <Building2 className="w-7 h-7 text-indigo-600 dark:text-indigo-400" />
 </div>
 <div>
 <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">Create Organization</h2>
 <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">Enter your school/company name</p>
 </div>
 <input
 type="text"
 value={name}
 onChange={e => setName(e.target.value)}
 onKeyDown={e => e.key === 'Enter' && submit()}
 placeholder="e.g., MIT, Stanford University"
 className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-sm text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
 />
 {err && <p className="text-xs text-red-500">{err}</p>}
 <button
 onClick={submit}
 disabled={busy || !name.trim()}
 className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition-colors disabled:opacity-40"
 >
 {busy ? <RefreshCw className="w-4 h-4 animate-spin mx-auto" /> : 'Create Organization'}
 </button>
 </div>
 );
}

// ── Main page ─────────────────────────────────────────────────────────────────

type Tab = 'codes' | 'members' | 'settings';

export default function OrgPage() {
 const { user } = useAppStore();

 const [org, setOrg] = useState<OrgInfo | null>(null);
 const [noOrg, setNoOrg] = useState(false);
 const [loading, setLoading] = useState(true);
 const [tab, setTab] = useState<Tab>('codes');

 // invite codes state
 const [codes, setCodes] = useState<OrgInviteCode[]>([]);
 const [codesLoading, setCodesLoading] = useState(false);
 const [showCreateCode, setShowCreateCode] = useState(false);
 const [newDuration, setNewDuration] = useState(12);
 const [newMaxUses, setNewMaxUses] = useState('');
 const [newValidDays, setNewValidDays] = useState('');
 const [codeBusy, setCodeBusy] = useState(false);
 const [codeErr, setCodeErr] = useState('');

 // settings state
 const [settingsMonthlyDocs, setSettingsMonthlyDocs] = useState('');
 const [settingsBusy, setSettingsBusy] = useState(false);
 const [settingsMsg, setSettingsMsg] = useState('');

 // members state
 const [members, setMembers] = useState<OrgMember[]>([]);
 const [membersLoading, setMembersLoading] = useState(false);
 const [actionId, setActionId] = useState<string | null>(null);

 const loadOrg = useCallback(async () => {
 setLoading(true);
 try {
 const info = await getMyOrg();
 if (info.role === 'owner') {
 const o: OrgInfo = { id: info.id!, name: info.name!, max_slots: info.max_slots ?? null, max_monthly_docs: info.max_monthly_docs ?? null, member_count: info.member_count ?? 0, created_at: null };
 setOrg(o);
 setSettingsMonthlyDocs(o.max_monthly_docs != null ? String(o.max_monthly_docs) : '');
 setNoOrg(false);
 } else {
 setNoOrg(true);
 }
 } catch { setNoOrg(true); }
 finally { setLoading(false); }
 }, []);

 const loadCodes = useCallback(async () => {
 setCodesLoading(true);
 try { setCodes(await listInviteCodes()); } catch { setCodes([]); }
 finally { setCodesLoading(false); }
 }, []);

 const loadMembers = useCallback(async () => {
 setMembersLoading(true);
 try { setMembers(await listOrgMembers()); } catch { setMembers([]); }
 finally { setMembersLoading(false); }
 }, []);

 useEffect(() => { loadOrg(); }, [loadOrg]);

 useEffect(() => {
 if (!org) return;
 if (tab === 'codes') loadCodes();
 if (tab === 'members') loadMembers();
 }, [tab, org]);

 const handleCreateCode = async () => {
 setCodeBusy(true); setCodeErr('');
 try {
 const code = await createInviteCode(
 newDuration,
 newMaxUses ? parseInt(newMaxUses) : undefined,
 newValidDays ? parseInt(newValidDays) : undefined,
 );
 setCodes(prev => [code, ...prev]);
 setShowCreateCode(false);
 setNewMaxUses(''); setNewValidDays('');
 } catch (e: unknown) {
 setCodeErr((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Error creating code');
 } finally { setCodeBusy(false); }
 };

 const handleDeactivate = async (code: string) => {
 if (!confirm(`Revoke code ${code}? Unused codes will no longer work.`)) return;
 setActionId(code);
 try {
 await deactivateInviteCode(code);
 setCodes(prev => prev.map(c => c.code === code ? { ...c, is_active: false } : c));
 } catch (e: unknown) {
 alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Error');
 } finally { setActionId(null); }
 };

 const handleSaveSettings = async () => {
 setSettingsBusy(true); setSettingsMsg('');
 try {
 const val = settingsMonthlyDocs.trim();
 const updated = await updateOrgSettings({
 max_monthly_docs: val ? parseInt(val) : null,
 });
 setOrg(prev => prev ? { ...prev, max_monthly_docs: updated.max_monthly_docs } : prev);
 setSettingsMsg(updated.max_monthly_docs ? `Set limit to ${updated.max_monthly_docs} documents/month` : 'Removed document limit');
 } catch (e: unknown) {
 setSettingsMsg((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Save error');
 } finally { setSettingsBusy(false); }
 };

 const handleKick = async (userId: string, email: string) => {
 if (!confirm(`Revoke access for ${email}? They will keep access until expiry.`)) return;
 setActionId(userId);
 try {
 await kickOrgMember(userId);
 setMembers(prev => prev.map(m => m.user_id === userId ? { ...m, status: 'revoked' } : m));
 } catch (e: unknown) {
 alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Error');
 } finally { setActionId(null); }
 };

 if (loading) return <div className="flex items-center justify-center min-h-[60vh] text-slate-400 dark:text-slate-500 text-sm">Loading...</div>;

 if (!user || user.plan !== 'enterprise') {
 return (
 <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 text-center p-6">
 <Building2 className="w-12 h-12 text-slate-300 dark:text-slate-600" />
 <p className="text-slate-500 dark:text-slate-400 text-sm">This feature is only for Enterprise accounts.</p>
 <Link href="/pricing" className="text-sm text-indigo-600 hover:underline">View pricing plans →</Link>
 </div>
 );
 }

 if (noOrg) {
 return (
 <div className="max-w-5xl mx-auto p-6">
 <div className="flex items-center gap-3 mb-6">
 <Link href="/profile" className="inline-flex items-center gap-1.5 text-xs text-slate-400 dark:text-slate-500 hover:text-indigo-600 transition-colors">
 <ArrowLeft className="w-3.5 h-3.5" /> Profile
 </Link>
 </div>
 <CreateOrgForm onCreated={o => { setOrg(o); setNoOrg(false); loadCodes(); }} />
 </div>
 );
 }

 return (
 <div className="max-w-5xl mx-auto p-6 space-y-6">

 {/* Header */}
 <div className="flex items-center justify-between">
 <div className="flex items-center gap-3">
 <Link href="/profile" className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-indigo-600 transition-colors">
 <ArrowLeft className="w-3.5 h-3.5" /> Profile
 </Link>
 <div className="w-px h-4 bg-slate-200 dark:bg-slate-700 dark:bg-gray-700" />
 <div>
 <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
 <Building2 className="w-5 h-5 text-indigo-500" />
 {org?.name}
 </h1>
 <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">Organization & member management</p>
 </div>
 </div>
 <span className="text-xs bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 px-3 py-1 rounded-full font-semibold">
 Enterprise
 </span>
 </div>

 {/* Stats */}
 <div className="grid grid-cols-3 gap-3">
 <div className="bg-white dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 p-4 text-center">
 <p className="text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-wide mb-1">Members</p>
 <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">{org?.member_count ?? 0}</p>
 {org?.max_slots && <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">/ {org.max_slots} slots</p>}
 </div>
 <div className="bg-white dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 p-4 text-center">
 <p className="text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-wide mb-1">Active invite codes</p>
 <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{codes.filter(c => c.is_active).length}</p>
 </div>
 <div className="bg-white dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 p-4 text-center">
 <p className="text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-wide mb-1">Documents/month</p>
 <p className="text-2xl font-bold text-violet-600 dark:text-violet-400">
 {org?.max_monthly_docs != null ? org.max_monthly_docs : '∞'}
 </p>
 </div>
 </div>

 {/* Tabs */}
 <div className="bg-white dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 overflow-hidden">
 <div className="flex border-b border-slate-100 dark:border-slate-800">
 {([
 { key: 'codes', label: 'Invite code', icon: Copy },
 { key: 'members', label: 'Members', icon: Users },
 { key: 'settings', label: 'Settings', icon: Settings },
 ] as const).map(({ key, label, icon: Icon }) => (
 <button key={key} onClick={() => setTab(key)}
 className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
 tab === key
 ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
 : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 dark:hover:text-gray-300'
 }`}>
 <Icon className="w-4 h-4" />{label}
 </button>
 ))}
 <div className="flex-1" />
 <button onClick={() => tab === 'codes' ? loadCodes() : loadMembers()}
 disabled={codesLoading || membersLoading}
 className="flex items-center gap-1.5 px-4 text-xs text-slate-400 dark:text-slate-500 disabled:opacity-40">
 <RefreshCw className={`w-3.5 h-3.5 ${codesLoading || membersLoading ? 'animate-spin' : ''}`} />
 Refresh
 </button>
 </div>

 {/* ── Tab: Invite Codes ── */}
 {tab === 'codes' && (
 <div className="p-5 space-y-4">

 {/* Create code button / form */}
 {!showCreateCode ? (
 <button
 onClick={() => setShowCreateCode(true)}
 className="flex items-center gap-2 text-sm px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium transition-colors"
 >
 <Plus className="w-4 h-4" /> Create new invite code
 </button>
 ) : (
 <div className="border border-indigo-200 dark:border-indigo-700 rounded-xl p-4 space-y-3 bg-indigo-50/50 dark:bg-indigo-900/10">
 <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">Create new invite code</p>

 {/* Duration */}
 <div>
 <label className="text-xs text-slate-500 dark:text-slate-400 block mb-1">Membership duration</label>
 <div className="relative inline-block w-48">
 <select
 value={newDuration}
 onChange={e => setNewDuration(Number(e.target.value))}
 className="w-full text-sm pl-3 pr-8 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-700 dark:text-slate-200 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
 >
 {DURATIONS.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
 </select>
 <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 dark:text-slate-500 pointer-events-none" />
 </div>
 </div>

 <div className="flex gap-3">
 {/* Max uses */}
 <div>
 <label className="text-xs text-slate-500 dark:text-slate-400 block mb-1">Usage limit <span className="text-gray-400">(leave empty = unlimited)</span></label>
 <input type="number" min={1} value={newMaxUses} onChange={e => setNewMaxUses(e.target.value)}
 placeholder="Unlimited"
 className="w-40 text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
 />
 </div>
 {/* Valid days */}
 <div>
 <label className="text-xs text-slate-500 dark:text-slate-400 block mb-1">Code validity (days) <span className="text-gray-400">(leave empty = forever)</span></label>
 <input type="number" min={1} value={newValidDays} onChange={e => setNewValidDays(e.target.value)}
 placeholder="Forever"
 className="w-40 text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
 />
 </div>
 </div>

 {codeErr && <p className="text-xs text-red-500">{codeErr}</p>}

 <div className="flex gap-2">
 <button onClick={handleCreateCode} disabled={codeBusy}
 className="flex items-center gap-1.5 text-sm px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium transition-colors disabled:opacity-40">
 {codeBusy ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
 Create Code
 </button>
 <button onClick={() => { setShowCreateCode(false); setCodeErr(''); }}
 className="text-sm px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 dark:hover:bg-gray-700 transition-colors">
 Cancel
 </button>
 </div>
 </div>
 )}

 {/* Codes list */}
 {codesLoading ? (
 <div className="py-8 text-center text-slate-400 dark:text-slate-500 text-sm">Loading...</div>
 ) : codes.length === 0 ? (
 <div className="py-8 text-center text-slate-400 dark:text-slate-500 text-sm">No invite codes yet</div>
 ) : (
 <div className="divide-y divide-slate-100 dark:divide-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-800 overflow-hidden">
 {codes.map(c => (
 <div key={c.id} className="px-4 py-3 flex items-center gap-3 hover:bg-gray-50/50 dark:hover:bg-gray-700/30">
 <div className="flex-1 min-w-0">
 <div className="flex items-center gap-2">
 <span className="font-mono text-sm font-bold text-indigo-600 dark:text-indigo-400">{c.code}</span>
 <CopyBtn text={c.code} />
 {!c.is_active && <span className="text-xs text-slate-400 dark:text-slate-500 line-through">Revoked</span>}
 </div>
 <div className="flex items-center gap-3 mt-0.5 text-[11px] text-slate-400 dark:text-slate-500">
 <span>{c.duration_label}</span>
 <span>Used: {c.used_count}{c.max_uses ? `/${c.max_uses}` : ''}</span>
 {c.valid_until && <span>Code expires: {new Date(c.valid_until).toLocaleDateString('en-US')}</span>}
 </div>
 </div>
 {c.is_active && (
 <button
 onClick={() => handleDeactivate(c.code)}
 disabled={actionId === c.code}
 className="p-1.5 rounded-lg border border-red-200 dark:border-red-800 text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-40"
 title="Revoke code"
 >
 {actionId === c.code ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
 </button>
 )}
 </div>
 ))}
 </div>
 )}
 </div>
 )}

 {/* ── Tab: Members ── */}
 {tab === 'members' && (
 membersLoading ? (
 <div className="py-16 text-center text-slate-400 dark:text-slate-500 text-sm">Loading...</div>
 ) : members.length === 0 ? (
 <div className="py-16 text-center text-slate-400 dark:text-slate-500 text-sm">No members yet</div>
 ) : (
 <div className="overflow-x-auto">
 <table className="w-full text-sm">
 <thead>
 <tr className="border-b border-slate-100 dark:border-slate-800">
 {['Members', 'Duration', 'Expired', 'Status', ''].map(h => (
 <th key={h} className="text-left px-4 py-3 text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide">{h}</th>
 ))}
 </tr>
 </thead>
 <tbody className="divide-y divide-gray-50/50">
 {members.map(m => (
 <tr key={m.id} className="hover:bg-gray-50/60 dark:hover:bg-gray-700/30">
 <td className="px-4 py-3">
 <p className="font-medium text-slate-800 dark:text-slate-100 text-xs">{m.user_name || '—'}</p>
 <p className="text-[11px] text-slate-400 dark:text-slate-500">{m.user_email}</p>
 </td>
 <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">{m.duration_label}</td>
 <td className="px-4 py-3 text-[11px] text-slate-400 dark:text-slate-500">
 {new Date(m.expires_at).toLocaleDateString('en-US')}
 </td>
 <td className="px-4 py-3"><StatusBadge status={m.status} /></td>
 <td className="px-4 py-3">
 {m.status === 'active' && (
 <button
 onClick={() => handleKick(m.user_id, m.user_email)}
 disabled={actionId === m.user_id}
 className="text-xs px-2.5 py-1 rounded-lg border border-amber-200 dark:border-amber-800 text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 transition-colors disabled:opacity-40"
 >
 {actionId === m.user_id ? <RefreshCw className="w-3 h-3 animate-spin" /> : 'Revoke'}
 </button>
 )}
 </td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>
 )
 )}

 {/* ── Tab: Settings ── */}
 {tab === 'settings' && (
 <div className="p-5 space-y-6">

 {/* Doc limit */}
 <div className="space-y-2">
 <div className="flex items-center gap-2">
 <FileText className="w-4 h-4 text-indigo-500" />
 <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">Document limit per month for members</p>
 </div>
 <p className="text-xs text-slate-400 dark:text-slate-500">Maximum documents each member can upload per month. Leave empty = unlimited.</p>
 <div className="flex items-center gap-3">
 <input
 type="number"
 min={1}
 value={settingsMonthlyDocs}
 onChange={e => setSettingsMonthlyDocs(e.target.value)}
 placeholder="Unlimited"
 className="w-48 text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
 />
 <span className="text-sm text-slate-400 dark:text-slate-500">documents/month</span>
 </div>
 <div className="flex items-center gap-3">
 <button
 onClick={handleSaveSettings}
 disabled={settingsBusy}
 className="flex items-center gap-1.5 text-sm px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium transition-colors disabled:opacity-40"
 >
 {settingsBusy ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
 Save
 </button>
 {org?.max_monthly_docs != null && (
 <p className="text-xs text-slate-400 dark:text-slate-500">Currently: <span className="font-semibold text-indigo-600 dark:text-indigo-400">{org.max_monthly_docs} documents/month</span></p>
 )}
 </div>
 {settingsMsg && (
 <p className={`text-xs ${settingsMsg.startsWith('Error') ? 'text-red-500' : 'text-emerald-500'}`}>{settingsMsg}</p>
 )}
 </div>

 {/* Stats summary */}
 <div className="border-t border-slate-100 dark:border-slate-800 pt-4">
 <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">Summary</p>
 <div className="grid grid-cols-2 gap-3 text-sm">
 <div className="bg-slate-50 dark:bg-slate-800/40 dark:bg-gray-700/50 rounded-lg p-3">
 <p className="text-xs text-slate-400 dark:text-slate-500 mb-0.5">Active members</p>
 <p className="font-bold text-slate-800 dark:text-slate-100">{org?.member_count ?? 0}{org?.max_slots ? ` / ${org.max_slots}` : ''}</p>
 </div>
 <div className="bg-slate-50 dark:bg-slate-800/40 dark:bg-gray-700/50 rounded-lg p-3">
 <p className="text-xs text-slate-400 dark:text-slate-500 mb-0.5">Document limit/month</p>
 <p className="font-bold text-slate-800 dark:text-slate-100">
 {org?.max_monthly_docs != null ? `${org.max_monthly_docs} documents` : 'Unlimited'}
 </p>
 </div>
 </div>
 </div>
 </div>
 )}
 </div>
 </div>
 );
}
