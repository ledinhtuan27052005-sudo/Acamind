'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAppStore } from '@/store/useAppStore';
import {
 adminListUsers, adminUpdateRole, upgradeUserPlan,
 adminGetPlanLimits, AdminUser,
} from '@/lib/api';
import {
 Check, X, Minus, Shield, Search, ArrowLeft,
 Users, Crown, Zap, Star, BookOpen, Building2,
 ChevronDown, Save, RefreshCw,
} from 'lucide-react';

// ── Permission matrix data ────────────────────────────────────────────────────

type ColKey = 'free' | 'pro' | 'researcher' | 'enterprise' | 'admin';

interface PermRow {
 feature: string;
 category: string;
 values: Record<ColKey, string | boolean>;
}

const COLS: { key: ColKey; label: string; icon: React.ReactNode; color: string }[] = [
 { key: 'free', label: 'Free', icon: <BookOpen className="w-4 h-4" />, color: 'text-slate-600 dark:text-slate-300' },
 { key: 'pro', label: 'Pro', icon: <Zap className="w-4 h-4" />, color: 'text-indigo-600' },
 { key: 'researcher', label: 'Researcher', icon: <Star className="w-4 h-4" />, color: 'text-violet-600' },
 { key: 'enterprise', label: 'Enterprise', icon: <Building2 className="w-4 h-4" />, color: 'text-amber-600' },
 { key: 'admin', label: 'Admin', icon: <Shield className="w-4 h-4" />, color: 'text-[#002D72]' },
];

const PERMISSION_ROWS: PermRow[] = [
 // Documents
 { category: 'Documents', feature: 'View document library', values: { free: true, pro: true, researcher: true, enterprise: true, admin: true } },
 { category: 'Documents', feature: 'Upload PDF', values: { free: false, pro: '20/month', researcher: '80/month', enterprise: 'Unlimited', admin: 'Unlimited' } },
 { category: 'Documents', feature: 'AI automatic categorization', values: { free: false, pro: true, researcher: true, enterprise: true, admin: true } },
 // Hỏi VNDáp AI
 { category: 'AI Chat', feature: 'Basic AI Q&A', values: { free: '600/month', pro: '1,000/month', researcher: '5,000/month', enterprise: 'Unlimited', admin: 'Unlimited' } },
 { category: 'AI Chat', feature: 'Memory Chat (history recall)', values: { free: false, pro: true, researcher: true, enterprise: true, admin: true } },
 { category: 'AI Chat', feature: 'Learning Mode (choose level)', values: { free: false, pro: true, researcher: true, enterprise: true, admin: true } },
 { category: 'AI Chat', feature: 'Translation & terminology', values: { free: false, pro: true, researcher: true, enterprise: true, admin: true } },
 // Học tập
 { category: 'Learning', feature: 'Quiz from documents', values: { free: true, pro: true, researcher: true, enterprise: true, admin: true } },
 { category: 'Learning', feature: 'Literature Review AI', values: { free: false, pro: false, researcher: true, enterprise: true, admin: true } },
 { category: 'Learning', feature: 'AI slides generation', values: { free: false, pro: false, researcher: true, enterprise: true, admin: true } },
 { category: 'Learning', feature: 'Export Word report (.docx)', values: { free: false, pro: true, researcher: true, enterprise: true, admin: true } },
 // Thư viện tổng hợp
 { category: 'Library', feature: 'View bilingual abstract', values: { free: 'Yes (short)', pro: true, researcher: true, enterprise: true, admin: true } },
 { category: 'Library', feature: 'Full translation (paywall)', values: { free: false, pro: true, researcher: true, enterprise: true, admin: true } },
 { category: 'Library', feature: 'Download original PDF (paywall)', values: { free: false, pro: true, researcher: true, enterprise: true, admin: true } },
 // Phân tích
 { category: 'Analysis', feature: 'Knowledge Graph', values: { free: true, pro: true, researcher: true, enterprise: true, admin: true } },
 { category: 'Analysis', feature: 'Research Timeline', values: { free: true, pro: true, researcher: true, enterprise: true, admin: true } },
 { category: 'Analysis', feature: 'Trending Topics', values: { free: false, pro: false, researcher: true, enterprise: true, admin: true } },
 { category: 'Analysis', feature: 'Cross-article analysis (comparison)', values: { free: false, pro: false, researcher: true, enterprise: true, admin: true } },
 // Organization
 { category: 'Organization', feature: 'Group/class Workspace', values: { free: false, pro: false, researcher: false, enterprise: true, admin: true } },
 { category: 'Organization', feature: 'Manage organization members', values: { free: false, pro: false, researcher: false, enterprise: true, admin: true } },
 { category: 'Organization', feature: 'Private API', values: { free: false, pro: false, researcher: false, enterprise: true, admin: true } },
 { category: 'Organization', feature: '24/7 Support', values: { free: false, pro: false, researcher: false, enterprise: true, admin: true } },
 // Admin
 { category: 'Admin', feature: 'Admin Panel', values: { free: false, pro: false, researcher: false, enterprise: false, admin: true } },
 { category: 'Admin', feature: 'Manage all users', values: { free: false, pro: false, researcher: false, enterprise: false, admin: true } },
 { category: 'Admin', feature: 'System Settings', values: { free: false, pro: false, researcher: false, enterprise: false, admin: true } },
];

// ── Cell renderer ─────────────────────────────────────────────────────────────

function Cell({ value }: { value: string | boolean }) {
 if (value === true) return <Check className="w-4 h-4 text-emerald-500 mx-auto" />;
 if (value === false) return <X className="w-4 h-4 text-slate-300 dark:text-slate-600 mx-auto" />;
 return <span className="text-xs text-gray-600 font-medium">{value}</span>;
}

// ── User quick action panel ───────────────────────────────────────────────────

const ROLES = ['student', 'researcher', 'admin'];
const PLANS = ['free', 'pro', 'researcher', 'enterprise'];

function UserQuickActions() {
 const [search, setSearch] = useState('');
 const [users, setUsers] = useState<AdminUser[]>([]);
 const [loading, setLoading] = useState(false);
 const [saving, setSaving] = useState<string | null>(null);
 const [msg, setMsg] = useState('');

 const doSearch = async () => {
 if (!search.trim()) return;
 setLoading(true);
 try {
 const data = await adminListUsers({ search: search.trim() });
 setUsers(data);
 } catch { setUsers([]); }
 finally { setLoading(false); }
 };

 const changeRole = async (u: AdminUser, role: string) => {
 setSaving(u.id + '_role'); setMsg('');
 try {
 await adminUpdateRole(u.id, role);
 setUsers(prev => prev.map(x => x.id === u.id ? { ...x, role } : x));
 setMsg(`✅ Changed role ${u.email} → ${role}`);
 } catch { setMsg('❌ Error changing role'); }
 finally { setSaving(null); }
 };

 const changePlan = async (u: AdminUser, plan: string) => {
 setSaving(u.id + '_plan'); setMsg('');
 try {
 await upgradeUserPlan(u.id, plan);
 setUsers(prev => prev.map(x => x.id === u.id ? { ...x, plan } : x));
 setMsg(`✅ Changed plan ${u.email} → ${plan}`);
 } catch { setMsg('❌ Error changing plan'); }
 finally { setSaving(null); }
 };

 return (
 <div className="space-y-4">
 <p className="text-sm text-slate-500 dark:text-slate-400">
 Search users to update role or plan directly.
 </p>
 <div className="flex gap-2">
 <div className="relative flex-1">
 <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500" />
 <input
 value={search}
 onChange={e => setSearch(e.target.value)}
 onKeyDown={e => e.key === 'Enter' && doSearch()}
 placeholder="Search by email or name..."
 className="w-full pl-9 pr-4 py-2 text-sm rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#1E88E5]"
 />
 </div>
 <button onClick={doSearch} disabled={loading}
 className="px-4 py-2 bg-[#002D72] hover:bg-[#1E88E5] text-white text-sm font-medium rounded-xl transition-colors disabled:opacity-60">
 {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Search'}
 </button>
 </div>

 {msg && (
 <div className={`text-sm px-3 py-2 rounded-lg ${msg.startsWith('✅') ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300' : 'bg-red-50 dark:bg-red-900/20 text-red-600'}`}>
 {msg}
 </div>
 )}

 {users.length > 0 && (
 <div className="rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
 <table className="w-full text-sm">
 <thead>
 <tr className="bg-slate-50 dark:bg-slate-800/40 border-b border-slate-200 dark:border-slate-700">
 {['Email', 'Name', 'Role', 'Plan', 'Documents'].map(h => (
 <th key={h} className="text-left px-4 py-2.5 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide">{h}</th>
 ))}
 </tr>
 </thead>
 <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
 {users.map(u => (
 <tr key={u.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/30">
 <td className="px-4 py-3 font-medium text-slate-800 dark:text-slate-100 text-xs">{u.email}</td>
 <td className="px-4 py-3 text-slate-600 dark:text-slate-300 text-xs">{u.full_name || '—'}</td>
 <td className="px-4 py-3">
 <select
 value={u.role}
 onChange={e => changeRole(u, e.target.value)}
 disabled={saving === u.id + '_role'}
 className="text-xs px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-800 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-1 focus:ring-[#1E88E5] disabled:opacity-60"
 >
 {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
 </select>
 </td>
 <td className="px-4 py-3">
 <select
 value={u.plan || 'free'}
 onChange={e => changePlan(u, e.target.value)}
 disabled={saving === u.id + '_plan'}
 className="text-xs px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-800 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-1 focus:ring-[#1E88E5] disabled:opacity-60"
 >
 {PLANS.map(p => <option key={p} value={p}>{p}</option>)}
 </select>
 </td>
 <td className="px-4 py-3 text-slate-500 dark:text-slate-400 text-xs">{u.document_count ?? 0}</td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>
 )}

 {users.length === 0 && !loading && search && (
 <p className="text-sm text-slate-400 dark:text-slate-500 text-center py-4">No users found.</p>
 )}
 </div>
 );
}

// ── Plan limits table ─────────────────────────────────────────────────────────

function PlanLimitsTable() {
 const [limits, setLimits] = useState<Record<string, any> | null>(null);
 const [loading, setLoading] = useState(true);

 useEffect(() => {
 adminGetPlanLimits().then(setLimits).catch(() => setLimits(null)).finally(() => setLoading(false));
 }, []);

 if (loading) return <div className="animate-pulse h-40 rounded-xl bg-slate-100 dark:bg-slate-800/60" />;
 if (!limits) return <p className="text-sm text-red-500">Failed to load data.</p>;

 const planKeys = Object.keys(limits);
 const fieldLabels: Record<string, string> = {
 label: 'Plan Name',
 price_vnd: 'Price (VND/month)',
 max_monthly_docs: 'Documents / month',
 max_monthly_chat: 'Questions / month',
 max_daily_chat: 'Questions / day',
 };

 return (
 <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700">
 <table className="w-full text-sm">
 <thead>
 <tr className="bg-slate-50 dark:bg-slate-800/40">
 <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide">Metric</th>
 {planKeys.map(pk => (
 <th key={pk} className="px-4 py-3 text-center text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wide">
 {limits[pk].label}
 </th>
 ))}
 </tr>
 </thead>
 <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
 {Object.entries(fieldLabels).map(([field, label]) => (
 <tr key={field} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/30">
 <td className="px-4 py-3 font-medium text-slate-700 dark:text-slate-200 text-xs">{label}</td>
 {planKeys.map(pk => {
 const val = limits[pk][field];
 return (
 <td key={pk} className="px-4 py-3 text-center text-xs text-slate-600 dark:text-slate-300">
 {val === null
 ? <span className="text-emerald-500 font-semibold">∞</span>
 : field === 'price_vnd'
 ? val === 0 ? 'Free' : val.toLocaleString('en-US') + ' VND'
 : String(val)}
 </td>
 );
 })}
 </tr>
 ))}
 {/* Features */}
 <tr className="bg-gray-50/50/30">
 <td className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-200 text-xs">Feature</td>
 {planKeys.map(pk => (
 <td key={pk} className="px-4 py-3 align-top">
 <ul className="space-y-1">
 {(limits[pk].features || []).map((f: string) => (
 <li key={f} className="flex items-start gap-1 text-[11px] text-slate-600 dark:text-slate-300">
 <Check className="w-3 h-3 text-emerald-500 mt-0.5 shrink-0" />{f}
 </li>
 ))}
 </ul>
 </td>
 ))}
 </tr>
 </tbody>
 </table>
 </div>
 );
}

// ── Page ──────────────────────────────────────────────────────────────────────

type Tab = 'matrix' | 'limits' | 'users';
const TABS: { key: Tab; label: string }[] = [
 { key: 'matrix', label: '🛡️ Permission Matrix' },
 { key: 'limits', label: '📊 Plan Limits' },
 { key: 'users', label: '👤 Manage Users' },
];

export default function PermissionsPage() {
 const { user } = useAppStore();
 const router = useRouter();
 const [tab, setTab] = useState<Tab>('matrix');

 // Group rows by category
 const categories = Array.from(new Set(PERMISSION_ROWS.map(r => r.category)));

 if (user && user.role !== 'admin') {
 router.replace('/');
 return null;
 }

 return (
 <div className="min-h-screen bg-[#FAF9F6] dark:bg-[#070A13] transition-colors duration-500">
 {/* Header */}
 <div className="bg-white dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-700 px-6 py-4">
 <div className="max-w-6xl mx-auto flex items-center gap-4">
 <Link href="/admin" className="text-slate-400 dark:text-slate-500 dark:hover:text-gray-200 transition-colors">
 <ArrowLeft className="w-5 h-5" />
 </Link>
 <div>
 <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100 dark:text-white flex items-center gap-2">
 <Shield className="w-5 h-5 text-[#002D72]" /> System Permissions
 </h1>
 <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
 Manage permissions by role & service plan
 </p>
 </div>
 </div>
 </div>

 <div className="max-w-6xl mx-auto px-4 py-6">
 {/* Tabs */}
 <div className="flex gap-1 bg-white dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl p-1 mb-6 w-fit">
 {TABS.map(t => (
 <button key={t.key} onClick={() => setTab(t.key)}
 className={`text-sm font-medium px-4 py-2 rounded-lg transition-colors ${
 tab === t.key
 ? 'bg-[#002D72] text-white shadow-sm'
 : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 dark:hover:text-gray-300'
 }`}>
 {t.label}
 </button>
 ))}
 </div>

 {/* ── Permission matrix ── */}
 {tab === 'matrix' && (
 <div className="bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden">
 <div className="overflow-x-auto">
 <table className="w-full">
 <thead>
 <tr className="bg-slate-50 dark:bg-slate-800/40 border-b border-slate-200 dark:border-slate-700">
 <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide w-56">
 Feature
 </th>
 {COLS.map(col => (
 <th key={col.key} className="px-4 py-3 text-center">
 <div className={`flex flex-col items-center gap-1 ${col.color}`}>
 {col.icon}
 <span className="text-xs font-bold">{col.label}</span>
 </div>
 </th>
 ))}
 </tr>
 </thead>
 <tbody>
 {categories.map(cat => {
 const rows = PERMISSION_ROWS.filter(r => r.category === cat);
 return (
 <>
 <tr key={`cat-${cat}`} className="bg-gray-50/80/50">
 <td colSpan={COLS.length + 1} className="px-5 py-2 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest">
 {cat}
 </td>
 </tr>
 {rows.map(row => (
 <tr key={row.feature} className="border-t border-slate-100 dark:border-slate-800 hover:bg-gray-50/50 dark:hover:bg-gray-800/20">
 <td className="px-5 py-3 text-sm text-slate-700 dark:text-slate-200">{row.feature}</td>
 {COLS.map(col => (
 <td key={col.key} className="px-4 py-3 text-center">
 <Cell value={row.values[col.key]} />
 </td>
 ))}
 </tr>
 ))}
 </>
 );
 })}
 </tbody>
 </table>
 </div>
 <div className="px-5 py-3 border-t border-slate-100 dark:border-slate-800 bg-gray-50/50/30 flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
 <span className="flex items-center gap-1.5"><Check className="w-3.5 h-3.5 text-emerald-500" /> Has permission</span>
 <span className="flex items-center gap-1.5"><X className="w-3.5 h-3.5 text-slate-300 dark:text-slate-600" /> No permission</span>
 <span className="text-slate-400 dark:text-slate-500">Text = specific limit</span>
 </div>
 </div>
 )}

 {/* ── Plan limits ── */}
 {tab === 'limits' && (
 <div className="space-y-4">
 <div className="flex items-center justify-between">
 <div>
 <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 dark:text-white">Plan Limits</h2>
 <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Data from backend — updated in plan_utils.py</p>
 </div>
 </div>
 <PlanLimitsTable />
 </div>
 )}

 {/* ── User quick actions ── */}
 {tab === 'users' && (
 <div className="bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-700 p-6">
 <div className="flex items-center gap-2 mb-5">
 <Users className="w-5 h-5 text-[#002D72]" />
 <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 dark:text-white">Manage User Permissions</h2>
 </div>
 <UserQuickActions />
 <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800">
 <Link href="/admin" className="text-xs text-[#1E88E5] hover:underline">
 → Full user management in Admin Panel
 </Link>
 </div>
 </div>
 )}
 </div>
 </div>
 );
}
