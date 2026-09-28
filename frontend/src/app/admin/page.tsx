'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/store/useAppStore';
import {
    adminListUsers, adminUpdateRole, adminDeleteUser, adminGetStats,
    adminListApplications, adminReviewApplication,
    adminListCategories, adminCreateCategory, adminUpdateCategory, adminDeleteCategory,
    upgradeUserPlan, adminConfirmPayment, adminListPayments,
    adminListTickets, adminUpdateTicket, adminListOffers, adminCreateOffer, adminConfirmOffer,
    adminSendNotification,
    AdminUser, AdminStats, ResearcherApplication, DocumentCategory, AdminPaymentRecord,
    EnterpriseTicket, EnterpriseOffer,
} from '@/lib/api';
import Link from 'next/link';
import { Users, FileCheck, Tag, RefreshCw, Check, X, ChevronDown, Plus, Pencil, Trash2, ArrowLeft, Receipt, CheckCircle2, Clock, XCircle, Building2, ExternalLink, Send, Bell } from 'lucide-react';

// ── Role badge ────────────────────────────────────────────────────────────────

function RoleBadge({ role }: { role: string }) {
    const map: Record<string, string> = {
        admin: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
        researcher: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
        student: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
        user: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
    };
    const label: Record<string, string> = {
        admin: 'Admin', researcher: 'Researcher', student: 'Student', user: 'Student',
    };
    return (
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${map[role] ?? 'bg-slate-100 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300'}`}>
            {label[role] ?? role}
        </span>
    );
}

function StatusBadge({ status }: { status: string }) {
    const map: Record<string, string> = {
        pending: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
        approved: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
        rejected: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
    };
    const label: Record<string, string> = { pending: 'Pending', approved: 'Approved', rejected: 'Rejected' };
    return (
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${map[status] ?? ''}`}>
            {label[status] ?? status}
        </span>
    );
}

// ── Role select dropdown ──────────────────────────────────────────────────────

function RoleSelect({
    currentRole, userId, selfId, busy,
    onChange,
}: {
    currentRole: string; userId: string; selfId: string; busy: boolean;
    onChange: (userId: string, role: string) => void;
}) {
    if (userId === selfId) return <span className="text-xs text-slate-300 dark:text-slate-600">You</span>;
    return (
        <div className="relative inline-block">
            <select
                value={currentRole === 'user' ? 'student' : currentRole}
                disabled={busy}
                onChange={e => onChange(userId, e.target.value)}
                className="text-xs pr-6 pl-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-700 dark:text-slate-200 appearance-none cursor-pointer disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
            >
                <option value="student">Student</option>
                <option value="researcher">Researcher</option>
                <option value="admin">Admin</option>
            </select>
            <ChevronDown className="absolute right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-400 dark:text-slate-500 pointer-events-none" />
        </div>
    );
}

// ── Main page ─────────────────────────────────────────────────────────────────

type Tab = 'users' | 'applications' | 'categories' | 'payments' | 'enterprise' | 'notifications';

export default function AdminPage() {
    const { user } = useAppStore();
    const router = useRouter();

    const [tab, setTab] = useState<Tab>('users');
    const [users, setUsers] = useState<AdminUser[]>([]);
    const [stats, setStats] = useState<AdminStats | null>(null);
    const [apps, setApps] = useState<ResearcherApplication[]>([]);
    const [appFilter, setAppFilter] = useState<'pending' | 'approved' | 'rejected'>('pending');
    const [loading, setLoading] = useState(true);
    const [appsLoading, setAppsLoading] = useState(false);
    const [actionId, setActionId] = useState<string | null>(null);
    const [error, setError] = useState('');

    // ── Payment state ──────────────────────────────────────────────────────────
    const [payments, setPayments] = useState<AdminPaymentRecord[]>([]);
    const [paymentsLoading, setPaymentsLoading] = useState(false);
    const [paymentFilter, setPaymentFilter] = useState<'pending' | 'completed' | 'expired' | ''>('pending');

    // ── Enterprise state ───────────────────────────────────────────────────────
    const [tickets, setTickets] = useState<EnterpriseTicket[]>([]);
    const [offers, setOffers] = useState<EnterpriseOffer[]>([]);
    const [entLoading, setEntLoading] = useState(false);
    const [ticketFilter, setTicketFilter] = useState<'open' | 'in_progress' | 'closed' | ''>('open');
    const [entSubTab, setEntSubTab] = useState<'tickets' | 'offers'>('tickets');
    const [showOfferForm, setShowOfferForm] = useState<string | null>(null); // ticket_id or 'new'
    const [offerForm, setOfferForm] = useState({
        school_name: '', contact_email: '', amount: '', duration_months: '12',
        package_type: 'monthly', max_slots: '', max_monthly_docs_member: '',
        expires_in_days: '30',
    });
    const [offerBusy, setOfferBusy] = useState(false);
    const [offerErr, setOfferErr] = useState('');

    // ── Notification state ─────────────────────────────────────────────────────
    const [notifForm, setNotifForm] = useState({
        title: '', body: '', type: 'info', link: '', target_email: '',
    });
    const [notifBusy, setNotifBusy] = useState(false);
    const [notifResult, setNotifResult] = useState<string | null>(null);
    const [notifErr, setNotifErr] = useState('');

    // ── Category state ─────────────────────────────────────────────────────────
    const [cats, setCats] = useState<DocumentCategory[]>([]);
    const [catsLoading, setCatsLoading] = useState(false);
    const [editingCat, setEditingCat] = useState<string | null>(null);
    const [editName, setEditName] = useState('');
    const [editColor, setEditColor] = useState('#6366f1');
    const [newName, setNewName] = useState('');
    const [newColor, setNewColor] = useState('#6366f1');
    const [catError, setCatError] = useState('');
    const [catBusy, setCatBusy] = useState(false);

    // ── Auth guard ─────────────────────────────────────────────────────────────
    useEffect(() => {
        if (user === null) return;
        if (user && user.role !== 'admin') { router.replace('/'); return; }
        if (!user) { router.replace('/login'); return; }
        loadAll();
    }, [user]);

    // ── Data loaders ───────────────────────────────────────────────────────────
    const loadAll = async () => {
        setLoading(true); setError('');
        try {
            const [u, s] = await Promise.all([adminListUsers(), adminGetStats()]);
            setUsers(u); setStats(s);
        } catch (e: unknown) {
            setError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Failed to load data');
        } finally { setLoading(false); }
    };

    const loadApps = async (status: typeof appFilter = appFilter) => {
        setAppsLoading(true);
        try { setApps(await adminListApplications(status)); }
        catch { setApps([]); }
        finally { setAppsLoading(false); }
    };

    const loadCats = async () => {
        setCatsLoading(true); setCatError('');
        try { setCats(await adminListCategories()); }
        catch { setCatError('Failed to load categories'); }
        finally { setCatsLoading(false); }
    };

    const loadPayments = async (status: typeof paymentFilter = paymentFilter) => {
        setPaymentsLoading(true);
        try { setPayments(await adminListPayments(status || undefined)); }
        catch { setPayments([]); }
        finally { setPaymentsLoading(false); }
    };

    const loadEnterprise = async (tFilter: typeof ticketFilter = ticketFilter) => {
        setEntLoading(true);
        try {
            const [t, o] = await Promise.all([
                adminListTickets(tFilter || undefined),
                adminListOffers(),
            ]);
            setTickets(t); setOffers(o);
        } catch { setTickets([]); setOffers([]); }
        finally { setEntLoading(false); }
    };

    const updateTicketStatus = async (ticketId: string, status: string) => {
        try {
            const updated = await adminUpdateTicket(ticketId, { status });
            setTickets(prev => prev.map(t => t.id === ticketId ? updated : t));
        } catch (e: unknown) {
            alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Update failed');
        }
    };

    const submitOffer = async (ticketId?: string) => {
        const amount = parseInt(offerForm.amount.replace(/\D/g, ''));
        if (!offerForm.school_name || !offerForm.contact_email || !amount) {
            setOfferErr('Please fill in all required fields'); return;
        }
        setOfferBusy(true); setOfferErr('');
        try {
            const result = await adminCreateOffer({
                ticket_id: ticketId || undefined,
                school_name: offerForm.school_name,
                contact_email: offerForm.contact_email,
                amount,
                duration_months: parseInt(offerForm.duration_months),
                package_type: offerForm.package_type,
                max_slots: offerForm.max_slots ? parseInt(offerForm.max_slots) : undefined,
                max_monthly_docs_member: offerForm.max_monthly_docs_member ? parseInt(offerForm.max_monthly_docs_member) : undefined,
                expires_in_days: parseInt(offerForm.expires_in_days),
            });
            alert(`Offer created!\nURL: ${result.offer_url}\nEmail sent to ${offerForm.contact_email}`);
            setShowOfferForm(null);
            setOfferForm({ school_name: '', contact_email: '', amount: '', duration_months: '12', package_type: 'monthly', max_slots: '', max_monthly_docs_member: '', expires_in_days: '30' });
            await loadEnterprise();
        } catch (e: unknown) {
            setOfferErr((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Offer creation failed');
        } finally { setOfferBusy(false); }
    };

    const confirmOffer = async (offerId: string) => {
        if (!confirm('Confirm manual Enterprise activation?')) return;
        setActionId(offerId);
        try {
            const res = await adminConfirmOffer(offerId);
            alert(res.message);
            await loadEnterprise();
        } catch (e: unknown) {
            alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Confirmation failed');
        } finally { setActionId(null); }
    };

    useEffect(() => {
        if (tab === 'applications') loadApps();
        if (tab === 'categories') loadCats();
        if (tab === 'payments') loadPayments();
        if (tab === 'enterprise') loadEnterprise();
    }, [tab]);

    // ── Actions ────────────────────────────────────────────────────────────────
    const changeRole = async (userId: string, newRole: string) => {
        const u = users.find(x => x.id === userId);
        if (!u || u.role === newRole || u.role === 'user' && newRole === 'student') return;
        if (!confirm(`Change role of ${u.email} to "${newRole}"?`)) return;
        setActionId(userId);
        try {
            await adminUpdateRole(userId, newRole);
            setUsers(prev => prev.map(x => x.id === userId ? { ...x, role: newRole } : x));
            if (stats) setStats({ ...stats });
            await loadAll();
        } catch (e: unknown) {
            alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Role change failed');
        } finally { setActionId(null); }
    };

    const changePlan = async (userId: string, newPlan: string) => {
        const u = users.find(x => x.id === userId);
        if (!u || u.plan === newPlan) return;
        setActionId(userId);
        try {
            await upgradeUserPlan(userId, newPlan);
            setUsers(prev => prev.map(x => x.id === userId ? { ...x, plan: newPlan } : x));
        } catch (e: unknown) {
            alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Plan change failed');
        } finally { setActionId(null); }
    };

    const deleteUser = async (u: AdminUser) => {
        if (!confirm(`Delete account ${u.email}? This action cannot be undone.`)) return;
        setActionId(u.id);
        try {
            await adminDeleteUser(u.id);
            setUsers(prev => prev.filter(x => x.id !== u.id));
        } catch (e: unknown) {
            alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Delete user failed');
        } finally { setActionId(null); }
    };

    const addCategory = async () => {
        const name = newName.trim();
        if (!name) return;
        setCatBusy(true); setCatError('');
        try {
            const cat = await adminCreateCategory(name, newColor);
            setCats(prev => [...prev, cat].sort((a, b) => a.name.localeCompare(b.name)));
            setNewName(''); setNewColor('#6366f1');
        } catch (e: unknown) {
            setCatError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Add category failed');
        } finally { setCatBusy(false); }
    };

    const startEditCat = (cat: DocumentCategory) => {
        setEditingCat(cat.id);
        setEditName(cat.name);
        setEditColor(cat.color);
        setCatError('');
    };

    const saveEditCat = async (catId: string) => {
        const name = editName.trim();
        if (!name) return;
        setCatBusy(true); setCatError('');
        try {
            const updated = await adminUpdateCategory(catId, { name, color: editColor });
            setCats(prev => prev.map(c => c.id === catId ? { ...c, ...updated } : c));
            setEditingCat(null);
        } catch (e: unknown) {
            setCatError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Update failed');
        } finally { setCatBusy(false); }
    };

    const deleteCat = async (cat: DocumentCategory) => {
        const msg = cat.doc_count > 0
            ? `Delete category "${cat.name}"? ${cat.doc_count} documents will be uncategorized.`
            : `Delete category "${cat.name}"?`;
        if (!confirm(msg)) return;
        setCatBusy(true); setCatError('');
        try {
            await adminDeleteCategory(cat.id);
            setCats(prev => prev.filter(c => c.id !== cat.id));
        } catch (e: unknown) {
            setCatError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Delete failed');
        } finally { setCatBusy(false); }
    };

    const confirmPayment = async (refCode: string) => {
        if (!confirm(`Confirm payment ${refCode}? Account will be upgraded immediately.`)) return;
        setActionId(refCode);
        try {
            const res = await adminConfirmPayment(refCode);
            alert(res.message);
            await loadPayments();
            await loadAll();
        } catch (e: unknown) {
            alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Confirmation failed');
        } finally { setActionId(null); }
    };

    const reviewApp = async (appId: string, action: 'approve' | 'reject') => {
        const a = apps.find(x => x.id === appId);
        const label = action === 'approve' ? 'approve' : 'reject';
        if (!confirm(`Confirm ${label} application of ${a?.user_email}?`)) return;
        setActionId(appId);
        try {
            await adminReviewApplication(appId, action);
            setApps(prev => prev.filter(x => x.id !== appId));
            await loadAll(); // refresh stats
        } catch (e: unknown) {
            alert((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Application processing failed');
        } finally { setActionId(null); }
    };

    // ── Guard render ───────────────────────────────────────────────────────────
    if (!user || user.role !== 'admin') {
        return <div className="flex items-center justify-center min-h-[60vh] text-slate-400 dark:text-slate-500">Checking permissions...</div>;
    }

    return (
        <div className="max-w-5xl mx-auto p-6 space-y-6">

            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Link
                        href="/profile"
                        className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-[#1E88E5] dark:hover:text-[#1E88E5] transition-colors"
                    >
                        <ArrowLeft className="w-3.5 h-3.5" />
                        Profile
                    </Link>
                    <div className="w-px h-4 bg-slate-200 dark:bg-slate-700 dark:bg-gray-700" />
                    <div>
                        <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100">System Administration</h1>
                        <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">Manage users and review Researcher applications</p>
                    </div>
                </div>
                <span className="text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 px-3 py-1 rounded-full font-semibold">
                    Admin Panel
                </span>
            </div>

            {/* Stats */}
            {stats && (
                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                    {[
                        { label: 'Total Users', value: stats.total_users, color: 'text-slate-700 dark:text-slate-200' },
                        { label: 'Admin', value: stats.admin_count, color: 'text-purple-600 dark:text-purple-300' },
                        { label: 'Researcher', value: stats.researcher_count, color: 'text-blue-600 dark:text-blue-300' },
                        { label: 'Student', value: stats.student_count, color: 'text-emerald-600 dark:text-emerald-300' },
                        { label: 'Pending', value: stats.pending_applications, color: 'text-amber-600 dark:text-amber-300' },
                        { label: 'Documents', value: stats.total_documents, color: 'text-slate-700 dark:text-slate-200' },
                        { label: 'Chunks', value: stats.total_chunks.toLocaleString('en-US'), color: 'text-slate-700 dark:text-slate-200' },
                    ].map(({ label, value, color }) => (
                        <div key={label} className="bg-white dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 p-3 text-center">
                            <p className="text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-wide mb-1">{label}</p>
                            <p className={`text-xl font-bold ${color}`}>{value}</p>
                        </div>
                    ))}
                </div>
            )}

            {error && (
                <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-300 text-sm rounded-lg">
                    {error}
                </div>
            )}

            {/* Tabs */}
            <div className="bg-white dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 overflow-hidden">

                {/* Tab bar */}
                <div className="flex border-b border-slate-100 dark:border-slate-800">
                    {([
                        { key: 'users', label: 'Users', icon: Users },
                        { key: 'applications', label: `Researcher Applications${stats?.pending_applications ? ` (${stats.pending_applications})` : ''}`, icon: FileCheck },
                        { key: 'categories', label: 'Categories', icon: Tag },
                        { key: 'payments', label: 'Payments', icon: Receipt },
                        { key: 'enterprise', label: 'Enterprise', icon: Building2 },
                        { key: 'notifications', label: 'Notifications', icon: Bell },
                    ] as const).map(({ key, label, icon: Icon }) => (
                        <button
                            key={key}
                            onClick={() => setTab(key)}
                            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${tab === key
                                    ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                                    : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 dark:hover:text-gray-300'
                                }`}
                        >
                            <Icon className="w-4 h-4" />{label}
                        </button>
                    ))}
                    <div className="flex-1" />
                    <button
                        onClick={() => tab === 'users' ? loadAll() : tab === 'applications' ? loadApps() : tab === 'payments' ? loadPayments() : tab === 'enterprise' ? loadEnterprise() : loadCats()}
                        disabled={loading || appsLoading || catsLoading || paymentsLoading || entLoading}
                        className="flex items-center gap-1.5 px-4 text-xs text-slate-400 dark:text-slate-500 dark:hover:text-gray-300 disabled:opacity-40"
                    >
                        <RefreshCw className={`w-3.5 h-3.5 ${loading || appsLoading || paymentsLoading || entLoading ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                </div>

                {/* ── Tab: Users ── */}
                {tab === 'users' && (
                    loading ? (
                        <div className="py-16 text-center text-slate-400 dark:text-slate-500 text-sm">Loading...</div>
                    ) : users.length === 0 ? (
                        <div className="py-16 text-center text-slate-400 dark:text-slate-500 text-sm">No users found</div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-slate-100 dark:border-slate-800">
                                        {['Users', 'Role', 'Plan', 'Documents', 'Created', ''].map(h => (
                                            <th key={h} className="text-left px-4 py-3 text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide">
                                                {h}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-50/50">
                                    {users.map(u => {
                                        const isSelf = u.id === user.id;
                                        const busy = actionId === u.id;
                                        return (
                                            <tr key={u.id} className="hover:bg-gray-50/60 dark:hover:bg-gray-700/30">
                                                <td className="px-4 py-3">
                                                    <p className="font-medium text-slate-800 dark:text-slate-100 text-xs">{u.full_name || '—'}</p>
                                                    <p className="text-[11px] text-slate-400 dark:text-slate-500">{u.email}</p>
                                                </td>
                                                <td className="px-4 py-3">
                                                    <RoleBadge role={u.role} />
                                                </td>
                                                <td className="px-4 py-3">
                                                    {isSelf ? (
                                                        <span className="text-xs text-slate-300 dark:text-slate-600">—</span>
                                                    ) : (
                                                        <div className="relative inline-block">
                                                            <select
                                                                value={u.plan ?? 'free'}
                                                                disabled={busy}
                                                                onChange={e => changePlan(u.id, e.target.value)}
                                                                className="text-xs pr-6 pl-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-700 dark:text-slate-200 appearance-none cursor-pointer disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
                                                            >
                                                                <option value="free">Freemium</option>
                                                                <option value="pro">Pro</option>
                                                                <option value="researcher">Researcher</option>
                                                                <option value="enterprise">Enterprise</option>
                                                            </select>
                                                            <ChevronDown className="absolute right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-400 dark:text-slate-500 pointer-events-none" />
                                                        </div>
                                                    )}
                                                </td>
                                                <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">{u.document_count}</td>
                                                <td className="px-4 py-3 text-[11px] text-slate-400 dark:text-slate-500">
                                                    {u.created_at ? new Date(u.created_at).toLocaleDateString('en-US') : '—'}
                                                </td>
                                                <td className="px-4 py-3">
                                                    <div className="flex items-center gap-2 justify-end">
                                                        <RoleSelect
                                                            currentRole={u.role}
                                                            userId={u.id}
                                                            selfId={user.id}
                                                            busy={busy}
                                                            onChange={changeRole}
                                                        />
                                                        {!isSelf && (
                                                            <button
                                                                onClick={() => deleteUser(u)}
                                                                disabled={busy}
                                                                className="text-[11px] px-2 py-1 rounded-lg border border-red-200 dark:border-red-800 text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-40"
                                                            >
                                                                {busy ? <RefreshCw className="w-3 h-3 animate-spin" /> : 'Delete'}
                                                            </button>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )
                )}

                {/* ── Tab: Applications ── */}
                {tab === 'applications' && (
                    <div>
                        {/* Filter bar */}
                        <div className="flex gap-1 px-4 pt-3 pb-2 border-b border-slate-100 dark:border-slate-800">
                            {(['pending', 'approved', 'rejected'] as const).map(s => (
                                <button
                                    key={s}
                                    onClick={() => { setAppFilter(s); loadApps(s); }}
                                    className={`text-xs px-3 py-1 rounded-full font-medium transition-colors ${appFilter === s
                                            ? s === 'pending' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
                                                : s === 'approved' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
                                                    : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                                            : 'bg-slate-100 dark:bg-slate-800/60 dark:bg-gray-700 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 dark:hover:bg-gray-600'
                                        }`}
                                >
                                    {{ pending: 'Pending', approved: 'Approved', rejected: 'Rejected' }[s]}
                                </button>
                            ))}
                        </div>

                        {appsLoading ? (
                            <div className="py-16 text-center text-slate-400 dark:text-slate-500 text-sm">Loading...</div>
                        ) : apps.length === 0 ? (
                            <div className="py-16 text-center">
                                <p className="text-slate-400 dark:text-slate-500 text-sm">No applications found</p>
                            </div>
                        ) : (
                            <div className="divide-y divide-gray-50/50">
                                {apps.map(a => {
                                    const busy = actionId === a.id;
                                    return (
                                        <div key={a.id} className="px-5 py-4 hover:bg-gray-50/60 dark:hover:bg-gray-700/30">
                                            <div className="flex items-start justify-between gap-4">
                                                <div className="min-w-0">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                                                            {a.user_name || '—'}
                                                        </p>
                                                        <StatusBadge status={a.status} />
                                                    </div>
                                                    <p className="text-xs text-slate-400 dark:text-slate-500 mb-2">{a.user_email}</p>
                                                    {a.reason && (
                                                        <div className="bg-slate-50 dark:bg-slate-800/40 rounded-lg px-3 py-2 text-xs text-slate-600 dark:text-slate-300 leading-relaxed max-w-xl">
                                                            <span className="font-medium text-slate-400 dark:text-slate-500 block mb-0.5 text-[10px] uppercase tracking-wide">Reason</span>
                                                            {a.reason}
                                                        </div>
                                                    )}
                                                    {a.admin_note && (
                                                        <p className="mt-1.5 text-xs text-red-500 dark:text-red-400">Admin note: {a.admin_note}</p>
                                                    )}
                                                    <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-2">
                                                        Submitted at {a.created_at ? new Date(a.created_at).toLocaleString('en-US') : '—'}
                                                    </p>
                                                </div>

                                                {a.status === 'pending' && (
                                                    <div className="flex gap-2 shrink-0">
                                                        <button
                                                            onClick={() => reviewApp(a.id, 'approve')}
                                                            disabled={busy}
                                                            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white font-medium transition-colors disabled:opacity-40"
                                                        >
                                                            {busy ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                                                            Approve
                                                        </button>
                                                        <button
                                                            onClick={() => reviewApp(a.id, 'reject')}
                                                            disabled={busy}
                                                            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border border-red-200 dark:border-red-800 text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 font-medium transition-colors disabled:opacity-40"
                                                        >
                                                            <X className="w-3 h-3" /> Rejected
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                )}

                {/* ── Tab: Payments ── */}
                {tab === 'payments' && (
                    <div>
                        {/* Filter bar */}
                        <div className="flex gap-1 px-4 pt-3 pb-2 border-b border-slate-100 dark:border-slate-800">
                            {([
                                { val: 'pending', label: 'Pending Confirmation' },
                                { val: 'completed', label: 'Confirmed' },
                                { val: 'expired', label: 'Expired' },
                                { val: '', label: 'All' },
                            ] as const).map(({ val, label }) => (
                                <button
                                    key={val}
                                    onClick={() => { setPaymentFilter(val); loadPayments(val); }}
                                    className={`text-xs px-3 py-1 rounded-full font-medium transition-colors ${paymentFilter === val
                                            ? val === 'pending' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
                                                : val === 'completed' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
                                                    : val === 'expired' ? 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 dark:bg-gray-700'
                                                        : 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300'
                                            : 'bg-slate-100 dark:bg-slate-800/60 dark:bg-gray-700 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 dark:hover:bg-gray-600'
                                        }`}
                                >
                                    {label}
                                </button>
                            ))}
                        </div>

                        {paymentsLoading ? (
                            <div className="py-16 text-center text-slate-400 dark:text-slate-500 text-sm">Loading...</div>
                        ) : payments.length === 0 ? (
                            <div className="py-16 text-center text-slate-400 dark:text-slate-500 text-sm">No transactions</div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b border-slate-100 dark:border-slate-800">
                                            {['Users', 'Plan', 'Amount', 'Ref Code', 'Status', 'Time', ''].map(h => (
                                                <th key={h} className="text-left px-4 py-3 text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide">
                                                    {h}
                                                </th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-50/50">
                                        {payments.map(p => {
                                            const busy = actionId === p.ref_code;
                                            return (
                                                <tr key={p.id} className="hover:bg-gray-50/60 dark:hover:bg-gray-700/30">
                                                    <td className="px-4 py-3">
                                                        <p className="font-medium text-slate-800 dark:text-slate-100 text-xs">{p.user_name || '—'}</p>
                                                        <p className="text-[11px] text-slate-400 dark:text-slate-500">{p.user_email}</p>
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${p.plan === 'pro' ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300'
                                                                : p.plan === 'researcher' ? 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300'
                                                                    : 'bg-slate-100 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300'
                                                            }`}>
                                                            {p.plan_label}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-3 text-xs font-medium text-slate-700 dark:text-slate-200">
                                                        {p.amount.toLocaleString('en-US')} VND
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <span className="text-xs font-mono text-indigo-600 dark:text-indigo-400">{p.ref_code}</span>
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium flex items-center gap-1 w-fit ${p.status === 'completed' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
                                                                : p.status === 'pending' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
                                                                    : 'bg-slate-100 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 dark:bg-gray-700'
                                                            }`}>
                                                            {p.status === 'completed' ? <CheckCircle2 className="w-3 h-3" />
                                                                : p.status === 'pending' ? <Clock className="w-3 h-3" />
                                                                    : <XCircle className="w-3 h-3" />}
                                                            {{ completed: 'Confirmed', pending: 'Pending Confirmation', expired: 'Expired' }[p.status] ?? p.status}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-3 text-[11px] text-slate-400 dark:text-slate-500">
                                                        {p.created_at ? new Date(p.created_at).toLocaleString('en-US') : '—'}
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        {p.status === 'pending' && (
                                                            <button
                                                                onClick={() => confirmPayment(p.ref_code)}
                                                                disabled={busy}
                                                                className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white font-medium transition-colors disabled:opacity-40 whitespace-nowrap"
                                                            >
                                                                {busy
                                                                    ? <RefreshCw className="w-3 h-3 animate-spin" />
                                                                    : <CheckCircle2 className="w-3 h-3" />}
                                                                Confirm
                                                            </button>
                                                        )}
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                )}

                {/* ── Tab: Enterprise ── */}
                {tab === 'enterprise' && (
                    <div>
                        {/* Sub-tab bar */}
                        <div className="flex items-center gap-2 px-4 pt-3 pb-2 border-b border-slate-100 dark:border-slate-800">
                            {(['tickets', 'offers'] as const).map(st => (
                                <button key={st} onClick={() => setEntSubTab(st)}
                                    className={`text-xs px-3 py-1 rounded-full font-medium transition-colors ${entSubTab === st
                                            ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
                                            : 'bg-slate-100 dark:bg-slate-800/60 dark:bg-gray-700 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 dark:hover:bg-gray-600'
                                        }`}>
                                    {{ tickets: 'Support Tickets', offers: 'Payment Offers' }[st]}
                                </button>
                            ))}
                            <div className="flex-1" />
                            <button onClick={() => { setShowOfferForm('new'); setOfferErr(''); }}
                                className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white font-medium transition-colors">
                                <Plus className="w-3.5 h-3.5" /> Create New Offer
                            </button>
                        </div>

                        {entLoading ? (
                            <div className="py-16 text-center text-slate-400 dark:text-slate-500 text-sm">Loading...</div>
                        ) : entSubTab === 'tickets' ? (
                            <div>
                                {/* Ticket filter */}
                                <div className="flex gap-1 px-4 pt-2 pb-2 border-b border-slate-100 dark:border-slate-800">
                                    {([
                                        { val: 'open', label: 'New' },
                                        { val: 'in_progress', label: 'Processing' },
                                        { val: 'closed', label: 'Closed' },
                                        { val: '', label: 'All' },
                                    ] as const).map(({ val, label }) => (
                                        <button key={val} onClick={() => { setTicketFilter(val); loadEnterprise(val); }}
                                            className={`text-xs px-3 py-1 rounded-full font-medium transition-colors ${ticketFilter === val
                                                    ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
                                                    : 'bg-slate-100 dark:bg-slate-800/60 dark:bg-gray-700 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 dark:hover:bg-gray-600'
                                                }`}>{label}</button>
                                    ))}
                                </div>
                                {tickets.length === 0 ? (
                                    <div className="py-16 text-center text-slate-400 dark:text-slate-500 text-sm">No tickets</div>
                                ) : (
                                    <div className="divide-y divide-gray-50/50">
                                        {tickets.map(t => (
                                            <div key={t.id} className="px-5 py-4 hover:bg-gray-50/60 dark:hover:bg-gray-700/30">
                                                <div className="flex items-start justify-between gap-4 flex-wrap">
                                                    <div className="min-w-0 flex-1">
                                                        <div className="flex items-center gap-2 flex-wrap mb-1">
                                                            <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{t.name}</p>
                                                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${t.status === 'open' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
                                                                    : t.status === 'in_progress' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                                                                        : 'bg-slate-100 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 dark:bg-gray-700'
                                                                }`}>{t.status === 'open' ? 'New' : t.status === 'in_progress' ? 'Processing' : 'Closed'}</span>
                                                        </div>
                                                        <p className="text-xs text-slate-400 dark:text-slate-500 mb-1">
                                                            <a href={`mailto:${t.email}`} className="text-indigo-500 hover:underline">{t.email}</a>
                                                            {t.phone ? ` · ${t.phone}` : ''} · {t.school_name}
                                                        </p>
                                                        {t.message && (
                                                            <div className="bg-slate-50 dark:bg-slate-800/40 rounded-lg px-3 py-2 text-xs text-slate-600 dark:text-slate-300 max-w-xl mt-1">
                                                                {t.message}
                                                            </div>
                                                        )}
                                                        <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">
                                                            {t.created_at ? new Date(t.created_at).toLocaleString('en-US') : '—'}
                                                        </p>
                                                    </div>
                                                    <div className="flex items-center gap-2 shrink-0">
                                                        {t.status !== 'in_progress' && (
                                                            <button onClick={() => updateTicketStatus(t.id, 'in_progress')}
                                                                className="text-xs px-2.5 py-1 rounded-lg bg-blue-500 hover:bg-blue-600 text-white font-medium transition-colors">
                                                                Process
                                                            </button>
                                                        )}
                                                        {t.status !== 'closed' && (
                                                            <button onClick={() => updateTicketStatus(t.id, 'closed')}
                                                                className="text-xs px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 dark:border-gray-600 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 dark:hover:bg-gray-700 font-medium transition-colors">
                                                                Close
                                                            </button>
                                                        )}
                                                        <button
                                                            onClick={() => {
                                                                setOfferForm(p => ({ ...p, school_name: t.school_name, contact_email: t.email }));
                                                                setShowOfferForm(t.id);
                                                                setOfferErr('');
                                                            }}
                                                            className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-amber-500 hover:bg-amber-600 text-white font-medium transition-colors">
                                                            <Send className="w-3 h-3" /> Create Offer
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ) : (
                            /* Offers sub-tab */
                            <div>
                                {offers.length === 0 ? (
                                    <div className="py-16 text-center text-slate-400 dark:text-slate-500 text-sm">No offers yet</div>
                                ) : (
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="border-b border-slate-100 dark:border-slate-800">
                                                    {['Organization', 'Email', 'Amount', 'Plan', 'Status', 'Ref Code', ''].map(h => (
                                                        <th key={h} className="text-left px-4 py-3 text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide">{h}</th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-50/50">
                                                {offers.map(o => {
                                                    const busy = actionId === o.id;
                                                    return (
                                                        <tr key={o.id} className="hover:bg-gray-50/60 dark:hover:bg-gray-700/30">
                                                            <td className="px-4 py-3">
                                                                <p className="font-medium text-slate-800 dark:text-slate-100 text-xs">{o.school_name}</p>
                                                                <p className="text-[11px] text-slate-400 dark:text-slate-500">{o.duration_months}th · {o.package_type}</p>
                                                            </td>
                                                            <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">{o.contact_email}</td>
                                                            <td className="px-4 py-3 text-xs font-medium text-amber-600 dark:text-amber-400">
                                                                {o.amount.toLocaleString('en-US')} VND
                                                            </td>
                                                            <td className="px-4 py-3 text-xs text-slate-500 dark:text-slate-400">
                                                                {o.package_type === 'annual'
                                                                    ? `${o.max_annual_docs_owner ?? '?'} docs/year`
                                                                    : `${o.max_monthly_docs_owner ?? '?'} docs/month`}
                                                                {o.max_slots ? ` · ${o.max_slots} slots` : ''}
                                                            </td>
                                                            <td className="px-4 py-3">
                                                                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${o.status === 'paid' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
                                                                        : o.status === 'active' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                                                                            : o.status === 'expired' ? 'bg-slate-100 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 dark:bg-gray-700'
                                                                                : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
                                                                    }`}>
                                                                    {{ draft: 'Pending', active: 'Claimed', paid: 'Paid', expired: 'Expired' }[o.status] ?? o.status}
                                                                </span>
                                                            </td>
                                                            <td className="px-4 py-3">
                                                                <span className="font-mono text-xs text-indigo-600 dark:text-indigo-400">{o.ref_code}</span>
                                                            </td>
                                                            <td className="px-4 py-3">
                                                                <div className="flex items-center gap-1.5">
                                                                    <a href={`/enterprise/offer/${o.token}`} target="_blank" rel="noopener noreferrer"
                                                                        className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 dark:border-gray-600 text-slate-400 dark:text-slate-500 hover:text-indigo-500 dark:hover:text-indigo-400 transition-colors"
                                                                        title="Open offer URL">
                                                                        <ExternalLink className="w-3.5 h-3.5" />
                                                                    </a>
                                                                    {o.status !== 'paid' && o.status !== 'expired' && (
                                                                        <button onClick={() => confirmOffer(o.id)} disabled={busy}
                                                                            className="flex items-center gap-1 text-xs px-2 py-1 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white font-medium transition-colors disabled:opacity-40">
                                                                            {busy ? <RefreshCw className="w-3 h-3 animate-spin" /> : <CheckCircle2 className="w-3 h-3" />}
                                                                            Activate
                                                                        </button>
                                                                    )}
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {/* ── Tab: Notifications ── */}
                {tab === 'notifications' && (
                    <div className="p-5 max-w-lg">
                        <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-4">
                            Send Notification
                        </p>

                        <div className="flex flex-col gap-3">
                            {/* Title */}
                            <div>
                                <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">Title *</label>
                                <input
                                    value={notifForm.title}
                                    onChange={e => setNotifForm(p => ({ ...p, title: e.target.value }))}
                                    placeholder="Example: System maintenance at 2 AM"
                                    className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
                                />
                            </div>

                            {/* Body */}
                            <div>
                                <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">Content</label>
                                <textarea
                                    value={notifForm.body}
                                    onChange={e => setNotifForm(p => ({ ...p, body: e.target.value }))}
                                    rows={3}
                                    placeholder="Notification details..."
                                    className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300/50 resize-none"
                                />
                            </div>

                            {/* Type + Link */}
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">Type</label>
                                    <select
                                        value={notifForm.type}
                                        onChange={e => setNotifForm(p => ({ ...p, type: e.target.value }))}
                                        className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
                                    >
                                        <option value="info">ℹ️ Info</option>
                                        <option value="success">✅ Success</option>
                                        <option value="warning">⚠️ Warning</option>
                                        <option value="system">⚙️ System</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">Link (optional)</label>
                                    <input
                                        value={notifForm.link}
                                        onChange={e => setNotifForm(p => ({ ...p, link: e.target.value }))}
                                        placeholder="/pricing"
                                        className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
                                    />
                                </div>
                            </div>

                            {/* Target */}
                            <div>
                                <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">
                                    Send to (account email)
                                </label>
                                <input
                                    value={notifForm.target_email}
                                    onChange={e => setNotifForm(p => ({ ...p, target_email: e.target.value }))}
                                    placeholder="Leave empty = send to ALL users"
                                    className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
                                />
                                <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
                                    {notifForm.target_email
                                        ? `Send to: ${notifForm.target_email}`
                                        : '⚠️ No email → notification will be sent to ALL accounts'}
                                </p>
                            </div>

                            {notifErr && <p className="text-xs text-red-500">{notifErr}</p>}
                            {notifResult && (
                                <div className="flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-700 rounded-lg px-3 py-2">
                                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                                    {notifResult}
                                </div>
                            )}

                            <button
                                disabled={notifBusy || !notifForm.title.trim()}
                                onClick={async () => {
                                    setNotifBusy(true); setNotifErr(''); setNotifResult(null);
                                    try {
                                        const res = await adminSendNotification({
                                            title: notifForm.title,
                                            body: notifForm.body || undefined,
                                            type: notifForm.type,
                                            link: notifForm.link || undefined,
                                            target_email: notifForm.target_email || undefined,
                                        });
                                        setNotifResult(
                                            notifForm.target_email
                                                ? `Notification sent to ${notifForm.target_email}`
                                                : `Notification sent to ${res.sent_to} accounts`
                                        );
                                        setNotifForm(p => ({ ...p, title: '', body: '', link: '' }));
                                    } catch (e: unknown) {
                                        setNotifErr(
                                            (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Failed to send notification'
                                        );
                                    } finally { setNotifBusy(false); }
                                }}
                                className="flex items-center justify-center gap-2 py-2.5 bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 text-white text-sm font-semibold rounded-lg transition-colors"
                            >
                                {notifBusy
                                    ? <><RefreshCw className="w-4 h-4 animate-spin" /> Sending...</>
                                    : <><Send className="w-4 h-4" /> {notifForm.target_email ? 'Send to this account' : 'Send to all'}</>
                                }
                            </button>
                        </div>
                    </div>
                )}

                {/* ── Tab: Categories ── */}
                {tab === 'categories' && (
                    <div className="p-5 space-y-5">

                        {/* Add new category */}
                        <div>
                            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">Add New Category</p>
                            <div className="flex items-center gap-2">
                                <input
                                    type="text"
                                    value={newName}
                                    onChange={e => setNewName(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && addCategory()}
                                    placeholder="Category name..."
                                    className="flex-1 text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
                                />
                                <div className="relative">
                                    <input
                                        type="color"
                                        value={newColor}
                                        onChange={e => setNewColor(e.target.value)}
                                        className="w-10 h-9 rounded-lg border border-slate-200 dark:border-slate-700 cursor-pointer p-0.5 bg-white dark:bg-slate-800/60"
                                        title="Select color"
                                    />
                                </div>
                                <button
                                    onClick={addCategory}
                                    disabled={catBusy || !newName.trim()}
                                    className="flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white font-medium transition-colors disabled:opacity-40"
                                >
                                    {catBusy ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
                                    Add
                                </button>
                            </div>
                            {catError && (
                                <p className="mt-2 text-xs text-red-500 dark:text-red-400">{catError}</p>
                            )}
                        </div>

                        {/* List */}
                        {catsLoading ? (
                            <div className="py-10 text-center text-slate-400 dark:text-slate-500 text-sm">Loading...</div>
                        ) : cats.length === 0 ? (
                            <div className="py-10 text-center text-slate-400 dark:text-slate-500 text-sm">No categories yet</div>
                        ) : (
                            <div className="divide-y divide-slate-100 dark:divide-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-800 overflow-hidden">
                                {cats.map(cat => {
                                    const isEditing = editingCat === cat.id;
                                    return (
                                        <div key={cat.id} className="px-4 py-3 flex items-center gap-3 hover:bg-gray-50/60 dark:hover:bg-gray-700/30">

                                            {/* Color swatch */}
                                            {isEditing ? (
                                                <input
                                                    type="color"
                                                    value={editColor}
                                                    onChange={e => setEditColor(e.target.value)}
                                                    className="w-7 h-7 rounded-full border border-slate-200 dark:border-slate-700 dark:border-gray-600 cursor-pointer p-0.5 shrink-0"
                                                />
                                            ) : (
                                                <span
                                                    className="w-3.5 h-3.5 rounded-full shrink-0 ring-2 ring-offset-1 ring-offset-white dark:ring-offset-gray-800"
                                                    style={{ backgroundColor: cat.color, '--tw-ring-color': cat.color } as React.CSSProperties}
                                                />
                                            )}

                                            {/* Name / edit input */}
                                            {isEditing ? (
                                                <input
                                                    autoFocus
                                                    type="text"
                                                    value={editName}
                                                    onChange={e => setEditName(e.target.value)}
                                                    onKeyDown={e => { if (e.key === 'Enter') saveEditCat(cat.id); if (e.key === 'Escape') setEditingCat(null); }}
                                                    className="flex-1 text-sm px-2 py-1 rounded-lg border border-indigo-300 dark:border-indigo-600 bg-white dark:bg-slate-800/60 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-300/50"
                                                />
                                            ) : (
                                                <div className="flex-1 min-w-0">
                                                    <span className="text-sm font-medium text-slate-800 dark:text-slate-100">{cat.name}</span>
                                                    <span className="ml-2 text-[11px] text-slate-400 dark:text-slate-500">{cat.doc_count} documents</span>
                                                </div>
                                            )}

                                            {/* Actions */}
                                            <div className="flex items-center gap-1.5 shrink-0">
                                                {isEditing ? (
                                                    <>
                                                        <button
                                                            onClick={() => saveEditCat(cat.id)}
                                                            disabled={catBusy}
                                                            className="p-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white transition-colors disabled:opacity-40"
                                                        >
                                                            <Check className="w-3.5 h-3.5" />
                                                        </button>
                                                        <button
                                                            onClick={() => setEditingCat(null)}
                                                            className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 dark:border-gray-600 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 dark:hover:bg-gray-700 transition-colors"
                                                        >
                                                            <X className="w-3.5 h-3.5" />
                                                        </button>
                                                    </>
                                                ) : (
                                                    <>
                                                        <button
                                                            onClick={() => startEditCat(cat)}
                                                            disabled={catBusy}
                                                            className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 dark:border-gray-600 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 dark:hover:bg-gray-700 transition-colors disabled:opacity-40"
                                                            title="Edit"
                                                        >
                                                            <Pencil className="w-3.5 h-3.5" />
                                                        </button>
                                                        <button
                                                            onClick={() => deleteCat(cat)}
                                                            disabled={catBusy}
                                                            className="p-1.5 rounded-lg border border-red-200 dark:border-red-800 text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-40"
                                                            title="Delete"
                                                        >
                                                            <Trash2 className="w-3.5 h-3.5" />
                                                        </button>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Create offer modal */}
            {showOfferForm !== null && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                    <div className="bg-white dark:bg-slate-800/60 rounded-2xl shadow-2xl w-full max-w-lg p-6 relative">
                        <button onClick={() => setShowOfferForm(null)} className="absolute top-4 right-4 text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300">
                            <X className="w-5 h-5" />
                        </button>
                        <div className="flex items-center gap-3 mb-5">
                            <div className="w-10 h-10 rounded-xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                                <Building2 className="w-5 h-5 text-amber-600" />
                            </div>
                            <div>
                                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 dark:text-white">Create Offer Enterprise</h3>
                                <p className="text-xs text-slate-500 dark:text-slate-400">Email will be sent automatically to the customer</p>
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            <div className="col-span-2">
                                <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">Organization *</label>
                                <input value={offerForm.school_name} onChange={e => setOfferForm(p => ({ ...p, school_name: e.target.value }))}
                                    className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-400"
                                    placeholder="University ABC" />
                            </div>
                            <div className="col-span-2">
                                <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">Recipient Email *</label>
                                <input type="email" value={offerForm.contact_email} onChange={e => setOfferForm(p => ({ ...p, contact_email: e.target.value }))}
                                    className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-400"
                                    placeholder="contact@truong.edu.vn" />
                            </div>
                            <div>
                                <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">Amount (VND) *</label>
                                <input value={offerForm.amount} onChange={e => setOfferForm(p => ({ ...p, amount: e.target.value }))}
                                    className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-400"
                                    placeholder="5000000" />
                            </div>
                            <div>
                                <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">Duration (months)</label>
                                <select value={offerForm.duration_months} onChange={e => setOfferForm(p => ({ ...p, duration_months: e.target.value }))}
                                    className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-400">
                                    <option value="1">1 months</option>
                                    <option value="3">3 months</option>
                                    <option value="12">12 months</option>
                                    <option value="24">24 months</option>
                                    <option value="48">48 months</option>
                                </select>
                            </div>
                            <div>
                                <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">Package</label>
                                <select value={offerForm.package_type} onChange={e => setOfferForm(p => ({ ...p, package_type: e.target.value }))}
                                    className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-400">
                                    <option value="monthly">Monthly (550 docs/mo)</option>
                                    <option value="annual">Annual (7000 docs/year)</option>
                                </select>
                            </div>
                            <div>
                                <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">Number of slots (members)</label>
                                <input value={offerForm.max_slots} onChange={e => setOfferForm(p => ({ ...p, max_slots: e.target.value }))}
                                    className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-400"
                                    placeholder="Unlimited" />
                            </div>
                            <div>
                                <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">Docs/month (members)</label>
                                <input value={offerForm.max_monthly_docs_member} onChange={e => setOfferForm(p => ({ ...p, max_monthly_docs_member: e.target.value }))}
                                    className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-400"
                                    placeholder="20" />
                            </div>
                            <div>
                                <label className="text-xs font-medium text-slate-600 dark:text-slate-300 mb-1 block">Form validity (days)</label>
                                <input value={offerForm.expires_in_days} onChange={e => setOfferForm(p => ({ ...p, expires_in_days: e.target.value }))}
                                    className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-400"
                                    placeholder="30" />
                            </div>
                        </div>
                        {offerErr && <p className="text-xs text-red-500 mt-2">{offerErr}</p>}
                        <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-3">
                            Owner default: {offerForm.package_type === 'annual' ? '7000 docs/year' : '550 docs/month'}
                        </p>
                        <div className="flex gap-3 mt-4">
                            <button onClick={() => setShowOfferForm(null)}
                                className="flex-1 py-2.5 border border-slate-200 dark:border-slate-700 text-sm font-medium rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/60 dark:hover:bg-gray-800 transition-colors">
                                Cancel
                            </button>
                            <button onClick={() => submitOffer(showOfferForm !== 'new' ? showOfferForm : undefined)} disabled={offerBusy}
                                className="flex-1 py-2.5 bg-amber-500 hover:bg-amber-600 disabled:opacity-60 text-white text-sm font-bold rounded-xl transition-colors">
                                {offerBusy ? 'Creating...' : 'Create & send email'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
