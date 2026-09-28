'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAppStore } from '@/store/useAppStore';
import {
  adminGetSettings, adminUpdateSettings, adminGetSystemInfo,
  adminSendTestEmail, SystemSetting, SystemInfo,
} from '@/lib/api';
import {
  Settings, Database, Mail, Cpu, ArrowLeft, Save,
  RefreshCw, CheckCircle2, XCircle, AlertCircle,
  ToggleLeft, ToggleRight, Server, HardDrive, Users,
  FileText, Layers, Send, Eye, EyeOff,
} from 'lucide-react';

// ── Helpers ───────────────────────────────────────────────────────────────────

const inputCls = "w-full text-sm px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/60 text-slate-900 dark:text-slate-100 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#1E88E5]";
const labelCls = "text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1.5 block";

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${checked ? 'bg-[#1E88E5]' : 'bg-gray-300 dark:bg-gray-600'}`}
    >
      <span className={`inline-block h-4 w-4 transform rounded-full bg-white dark:bg-slate-800/60 shadow transition-transform ${checked ? 'translate-x-6' : 'translate-x-1'}`} />
    </button>
  );
}

function StatCard({ icon, label, value, sub }: { icon: React.ReactNode; label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-700 p-4 flex items-start gap-3">
      <div className="w-9 h-9 rounded-xl bg-[#002D72]/10 dark:bg-[#1E88E5]/10 flex items-center justify-center text-[#002D72] dark:text-[#1E88E5] shrink-0">
        {icon}
      </div>
      <div>
        <p className="text-xl font-bold text-slate-900 dark:text-slate-100 dark:text-white">{value}</p>
        <p className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</p>
        {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

// ── Tab: System Info ──────────────────────────────────────────────────────────

function SystemInfoTab() {
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    adminGetSystemInfo().then(setInfo).catch(() => setInfo(null)).finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
      {Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-20 rounded-2xl bg-slate-100 dark:bg-slate-800/60 animate-pulse" />)}
    </div>
  );

  if (!info) return <p className="text-sm text-red-500">Failed to load system information.</p>;

  const dbOk = info.db_status === 'ok';

  return (
    <div className="space-y-6">
      {/* DB status */}
      <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${dbOk ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-700' : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-700'}`}>
        {dbOk
          ? <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
          : <XCircle className="w-5 h-5 text-red-500 shrink-0" />}
        <div>
          <p className={`text-sm font-semibold ${dbOk ? 'text-emerald-700 dark:text-emerald-300' : 'text-red-700 dark:text-red-300'}`}>
            PostgreSQL: {dbOk ? 'Connected' : 'Disconnected'}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">pgvector + pgvecto.rs</p>
        </div>
        <span className="ml-auto text-xs text-slate-400 dark:text-slate-500">v{info.version}</span>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        <StatCard icon={<Users className="w-5 h-5" />} label="Total Users" value={info.total_users} />
        <StatCard icon={<FileText className="w-5 h-5" />} label="Documents PDF" value={info.total_documents} />
        <StatCard icon={<Layers className="w-5 h-5" />} label="Chunks (embedding)" value={info.total_chunks.toLocaleString()} />
        <StatCard icon={<HardDrive className="w-5 h-5" />} label="PDF user" value={info.storage.user_pdf_count} sub={`${info.storage.user_pdf_size_mb} MB`} />
        <StatCard icon={<Database className="w-5 h-5" />} label="Library Documents" value={info.storage.library_pdf_count} sub="original PDF files" />
        <StatCard icon={<Server className="w-5 h-5" />} label="Version" value={`v${info.version}`} sub="Acamind RAG System" />
      </div>

      {/* Plan breakdown */}
      <div className="bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-700 p-5">
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100 dark:text-white mb-4">User Plan Distribution</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Free', val: info.plan_breakdown.free, color: 'bg-slate-100 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300' },
            { label: 'Pro', val: info.plan_breakdown.pro, color: 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300' },
            { label: 'Researcher', val: info.plan_breakdown.researcher, color: 'bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300' },
            { label: 'Enterprise', val: info.plan_breakdown.enterprise, color: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300' },
          ].map(p => (
            <div key={p.label} className={`rounded-xl px-4 py-3 text-center ${p.color}`}>
              <p className="text-2xl font-bold">{p.val}</p>
              <p className="text-xs font-medium mt-0.5">{p.label}</p>
            </div>
          ))}
        </div>
      </div>

      <button onClick={load} disabled={loading}
        className="flex items-center gap-2 text-xs text-slate-400 dark:text-slate-500 dark:hover:text-gray-300 transition-colors">
        <RefreshCw className="w-3.5 h-3.5" /> Refresh
      </button>
    </div>
  );
}

// ── Tab: General settings ─────────────────────────────────────────────────────

const SETTING_GROUPS: { title: string; keys: string[] }[] = [
  { title: 'Chung', keys: ['site_name', 'registration_open', 'allow_google_auth', 'default_plan'] },
  { title: 'Upload', keys: ['max_upload_mb'] },
  { title: 'AI / Model', keys: ['ai_model', 'ai_temperature', 'max_context_chunks'] },
  { title: 'Maintenance', keys: ['maintenance_mode', 'maintenance_message'] },
];

const BOOLEAN_KEYS = new Set(['registration_open', 'allow_google_auth', 'maintenance_mode']);
const SELECT_OPTIONS: Record<string, string[]> = {
  default_plan: ['free', 'pro', 'researcher', 'enterprise'],
};

function GeneralSettingsTab() {
  const [raw, setRaw] = useState<Record<string, SystemSetting> | null>(null);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

  useEffect(() => {
    adminGetSettings()
      .then(data => { setRaw(data); setDraft(Object.fromEntries(Object.entries(data).map(([k, v]) => [k, v.value]))); })
      .catch(() => setRaw(null))
      .finally(() => setLoading(false));
  }, []);

  const save = async () => {
    setSaving(true); setMsg(null);
    try {
      await adminUpdateSettings(draft);
      setMsg({ type: 'ok', text: 'Settings saved successfully.' });
    } catch {
      setMsg({ type: 'err', text: 'Save error. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="animate-pulse space-y-3">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-12 rounded-xl bg-slate-100 dark:bg-slate-800/60" />)}</div>;
  if (!raw) return <p className="text-sm text-red-500">Failed to load settings.</p>;

  const allKeys = Object.keys(raw);

  return (
    <div className="space-y-6">
      {msg && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-xl text-sm ${msg.type === 'ok' ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-700' : 'bg-red-50 dark:bg-red-900/20 text-red-600 border border-red-200 dark:border-red-700'}`}>
          {msg.type === 'ok' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          {msg.text}
        </div>
      )}

      {SETTING_GROUPS.map(group => {
        const groupKeys = group.keys.filter(k => allKeys.includes(k));
        if (groupKeys.length === 0) return null;
        return (
          <div key={group.title} className="bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-700 p-5">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 dark:text-white mb-4 pb-3 border-b border-slate-100 dark:border-slate-800">
              {group.title}
            </h3>
            <div className="space-y-4">
              {groupKeys.map(key => {
                const setting = raw[key];
                const value = draft[key] ?? setting.value;

                if (BOOLEAN_KEYS.has(key)) {
                  return (
                    <div key={key} className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-sm font-medium text-slate-700 dark:text-slate-200">{setting.description}</p>
                        <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5 font-mono">{key}</p>
                      </div>
                      <Toggle
                        checked={value === 'true'}
                        onChange={v => setDraft(p => ({ ...p, [key]: v ? 'true' : 'false' }))}
                      />
                    </div>
                  );
                }

                if (SELECT_OPTIONS[key]) {
                  return (
                    <div key={key}>
                      <label className={labelCls}>{setting.description} <span className="font-mono text-slate-400 dark:text-slate-500">({key})</span></label>
                      <select
                        value={value}
                        onChange={e => setDraft(p => ({ ...p, [key]: e.target.value }))}
                        className={inputCls}
                      >
                        {SELECT_OPTIONS[key].map(opt => <option key={opt} value={opt}>{opt}</option>)}
                      </select>
                    </div>
                  );
                }

                if (key === 'maintenance_message') {
                  return (
                    <div key={key}>
                      <label className={labelCls}>{setting.description} <span className="font-mono text-slate-400 dark:text-slate-500">({key})</span></label>
                      <textarea
                        value={value}
                        onChange={e => setDraft(p => ({ ...p, [key]: e.target.value }))}
                        rows={2}
                        className={inputCls + ' resize-none'}
                        placeholder="System under maintenance, please come back later..."
                      />
                    </div>
                  );
                }

                return (
                  <div key={key}>
                    <label className={labelCls}>{setting.description} <span className="font-mono text-slate-400 dark:text-slate-500">({key})</span></label>
                    <input
                      value={value}
                      onChange={e => setDraft(p => ({ ...p, [key]: e.target.value }))}
                      className={inputCls}
                    />
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}

      <button
        onClick={save}
        disabled={saving}
        className="flex items-center gap-2 bg-[#002D72] hover:bg-[#1E88E5] disabled:opacity-60 text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition-colors"
      >
        {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
        {saving ? 'Saving...' : 'Save Settings'}
      </button>
    </div>
  );
}

// ── Tab: Email test ───────────────────────────────────────────────────────────

function EmailTab() {
  const { user } = useAppStore();
  const [to, setTo] = useState(user?.email ?? '');
  const [sending, setSending] = useState(false);
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

  const send = async () => {
    if (!to.trim()) return;
    setSending(true); setMsg(null);
    try {
      await adminSendTestEmail(to.trim());
      setMsg({ type: 'ok', text: `Test email sent to ${to}. Check your inbox.` });
    } catch (e: any) {
      const detail = e?.response?.data?.detail || 'Send failed. Check SMTP configuration in .env';
      setMsg({ type: 'err', text: detail });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-5 max-w-lg">
      <div className="bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-700 p-5">
        <div className="flex items-center gap-2 mb-4">
          <Mail className="w-5 h-5 text-[#002D72]" />
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 dark:text-white">Test SMTP</h3>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
          Send a test email to verify SMTP configuration. Settings are from environment variables{' '}
          <code className="bg-slate-100 dark:bg-slate-800/60 px-1 py-0.5 rounded text-[11px]">SMTP_USER</code> and{' '}
          <code className="bg-slate-100 dark:bg-slate-800/60 px-1 py-0.5 rounded text-[11px]">SMTP_PASS</code> trong <code className="bg-slate-100 dark:bg-slate-800/60 px-1 py-0.5 rounded text-[11px]">.env</code>.
        </p>

        <div className="space-y-3">
          <div>
            <label className={labelCls}>Send to email</label>
            <input
              type="email"
              value={to}
              onChange={e => setTo(e.target.value)}
              placeholder="example@email.com"
              className={inputCls}
            />
          </div>
          <button
            onClick={send}
            disabled={sending || !to.trim()}
            className="flex items-center gap-2 bg-[#002D72] hover:bg-[#1E88E5] disabled:opacity-60 text-white text-sm font-semibold px-4 py-2.5 rounded-xl transition-colors"
          >
            {sending ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            {sending ? 'Sending...' : 'Send test email'}
          </button>
        </div>

        {msg && (
          <div className={`mt-4 flex items-start gap-2 px-3 py-2.5 rounded-xl text-sm ${msg.type === 'ok' ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-700' : 'bg-red-50 dark:bg-red-900/20 text-red-600 border border-red-200 dark:border-red-700'}`}>
            {msg.type === 'ok' ? <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" /> : <XCircle className="w-4 h-4 shrink-0 mt-0.5" />}
            {msg.text}
          </div>
        )}
      </div>

      {/* SMTP config reference */}
      <div className="bg-slate-50 dark:bg-slate-800/40 rounded-2xl border border-slate-200 dark:border-slate-700 p-5">
        <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">SMTP Environment Variables</h3>
        <div className="space-y-2 font-mono text-xs text-slate-600 dark:text-slate-300">
          {[
            ['SMTP_HOST', 'smtp.gmail.com'],
            ['SMTP_PORT', '587'],
            ['SMTP_USER', 'your@gmail.com'],
            ['SMTP_PASS', 'app-password-here'],
          ].map(([k, v]) => (
            <div key={k} className="flex gap-2">
              <span className="text-[#1E88E5] w-24 shrink-0">{k}</span>
              <span className="text-slate-400 dark:text-slate-500">=</span>
              <span className="text-amber-600 dark:text-amber-400">{v}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

type Tab = 'info' | 'general' | 'email';

const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
  { key: 'info', label: 'System Information', icon: <Server className="w-4 h-4" /> },
  { key: 'general', label: 'Settings chung', icon: <Settings className="w-4 h-4" /> },
  { key: 'email', label: 'Email / SMTP', icon: <Mail className="w-4 h-4" /> },
];

export default function SettingsPage() {
  const { user } = useAppStore();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>('info');

  if (user && user.role !== 'admin') {
    router.replace('/');
    return null;
  }

  return (
    <div className="min-h-screen bg-[#FAF9F6] dark:bg-[#070A13] transition-colors duration-500">
      {/* Header */}
      <div className="bg-white dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-700 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center gap-4">
          <Link href="/admin" className="text-slate-400 dark:text-slate-500 dark:hover:text-gray-200 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100 dark:text-white flex items-center gap-2">
              <Settings className="w-5 h-5 text-[#002D72]" /> System Settings
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">System operations and monitoring</p>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-6">
        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-slate-200 dark:border-slate-700">
          {TABS.map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex items-center gap-2 text-sm font-medium px-4 py-2.5 border-b-2 transition-colors ${tab === t.key
                  ? 'border-[#1E88E5] text-[#1E88E5]'
                  : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 dark:hover:text-gray-300'
                }`}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        {tab === 'info' && <SystemInfoTab />}
        {tab === 'general' && <GeneralSettingsTab />}
        {tab === 'email' && <EmailTab />}
      </div>
    </div>
  );
}
