'use client';

import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { getDocuments, getDocStats, getSystemReadiness, DocumentInfo, DocStats, SystemReadiness } from '@/lib/api';
import { useAppStore } from '@/store/useAppStore';
import Link from 'next/link';
import {
  FileText, CheckCircle, Layers, MessageCircle,
  ArrowRight, Upload, Brain, BarChart3, Network,
  Zap, TrendingUp, Clock, BookOpen,
} from 'lucide-react';

/* ─── Particle Background (client-only to avoid SSR mismatch) ───────────── */

// Fixed positions — no Math.random(), safe for SSR
const PARTICLE_DATA = [
  { id: 0, x: 5, size: 3, delay: 0, dur: 10, c: '#3B82F6' },
  { id: 1, x: 15, size: 5, delay: 2, dur: 14, c: '#A855F7' },
  { id: 2, x: 25, size: 2, delay: 0.5, dur: 12, c: '#06B6D4' },
  { id: 3, x: 35, size: 4, delay: 3, dur: 11, c: '#3B82F6' },
  { id: 4, x: 45, size: 3, delay: 1, dur: 15, c: '#A855F7' },
  { id: 5, x: 55, size: 5, delay: 4, dur: 10, c: '#06B6D4' },
  { id: 6, x: 65, size: 2, delay: 1.5, dur: 13, c: '#3B82F6' },
  { id: 7, x: 75, size: 4, delay: 2.5, dur: 12, c: '#A855F7' },
  { id: 8, x: 85, size: 3, delay: 0.8, dur: 14, c: '#06B6D4' },
  { id: 9, x: 92, size: 5, delay: 3.5, dur: 11, c: '#3B82F6' },
  { id: 10, x: 10, size: 2, delay: 5, dur: 16, c: '#A855F7' },
  { id: 11, x: 30, size: 4, delay: 6, dur: 10, c: '#06B6D4' },
  { id: 12, x: 50, size: 3, delay: 7, dur: 15, c: '#3B82F6' },
  { id: 13, x: 70, size: 5, delay: 1.2, dur: 12, c: '#A855F7' },
  { id: 14, x: 88, size: 2, delay: 4.5, dur: 13, c: '#06B6D4' },
];

function ParticleField() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);
  if (!mounted) return null;

  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden" style={{ zIndex: 0 }}>
      {PARTICLE_DATA.map(p => (
        <div
          key={p.id}
          className="particle"
          style={{
            left: `${p.x}%`,
            width: p.size,
            height: p.size,
            background: p.c,
            boxShadow: `0 0 ${p.size * 3}px ${p.c}`,
            animationDuration: `${p.dur}s`,
            animationDelay: `${p.delay}s`,
            bottom: '-20px',
          }}
        />
      ))}
    </div>
  );
}

/* ─── Stat Card ─────────────────────────────────────────────────────────── */

const statGradients = [
  { from: '#3B82F6', to: '#06B6D4', glow: 'rgba(59,130,246,0.3)' },
  { from: '#10B981', to: '#06B6D4', glow: 'rgba(16,185,129,0.3)' },
  { from: '#A855F7', to: '#EC4899', glow: 'rgba(168,85,247,0.3)' },
  { from: '#F59E0B', to: '#EF4444', glow: 'rgba(245,158,11,0.3)' },
];

interface StatCardProps {
  icon: React.ElementType;
  label: string;
  value: string | number;
  sub?: string;
  href?: string;
  index: number;
  badge?: string;
}

function StatCard({ icon: Icon, label, value, sub, href, index, badge }: StatCardProps) {
  const g = statGradients[index % statGradients.length];

  const inner = (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.4 }}
      whileHover={{ y: -4, scale: 1.02 }}
      className="glow-card glass rounded-2xl p-5 h-full cursor-pointer group relative overflow-hidden"
      style={{ '--glow-color': g.glow } as React.CSSProperties}
    >
      {/* Background gradient blob */}
      <div
        className="absolute -top-6 -right-6 w-24 h-24 rounded-full opacity-10 group-hover:opacity-20 transition-opacity duration-500"
        style={{ background: `radial-gradient(circle, ${g.from}, ${g.to})` }}
      />
      {/* Icon */}
      <div
        className="w-11 h-11 rounded-xl flex items-center justify-center mb-3 shadow-lg"
        style={{ background: `linear-gradient(135deg, ${g.from}, ${g.to})` }}
      >
        <Icon size={20} color="white" strokeWidth={2.5} />
      </div>
      <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">{label}</p>
      <p
        className="text-3xl font-bold mb-1"
        style={{ background: `linear-gradient(135deg, ${g.from}, ${g.to})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}
      >
        {value}
      </p>
      {sub && <p className="text-xs text-slate-400 dark:text-slate-500">{sub}</p>}
      {badge && (
        <span className="absolute top-3 right-3 text-[10px] font-bold px-2 py-0.5 rounded-full"
          style={{ background: `linear-gradient(135deg, ${g.from}20, ${g.to}20)`, color: g.from, border: `1px solid ${g.from}30` }}>
          {badge}
        </span>
      )}
      {/* Bottom glow line */}
      <div
        className="absolute bottom-0 left-4 right-4 h-px opacity-40 group-hover:opacity-80 transition-opacity"
        style={{ background: `linear-gradient(90deg, transparent, ${g.from}, ${g.to}, transparent)` }}
      />
    </motion.div>
  );

  if (href) return <Link href={href} className="block h-full">{inner}</Link>;
  return inner;
}

/* ─── Quick Action Card ─────────────────────────────────────────────────── */

const quickActions = [
  { href: '/chat', icon: MessageCircle, label: 'AI Q&A', desc: 'RAG Chat', color: '#3B82F6' },
  { href: '/Quiz', icon: Brain, label: 'Quiz', desc: 'Knowledge Test', color: '#A855F7' },
  { href: '/graph', icon: Network, label: 'Knowledge Graph', desc: 'Knowledge Graph', color: '#06B6D4' },
  { href: '/upload', icon: Upload, label: 'Upload PDF', desc: 'Add Documents', color: '#10B981' },
  { href: '/Trend', icon: TrendingUp, label: 'Trending', desc: 'Trending Topics', color: '#F59E0B' },
  { href: '/RAG', icon: BarChart3, label: 'RAG Evaluation', desc: 'Benchmark', color: '#EF4444' },
];

function QuickAction({ href, icon: Icon, label, desc, color, index }: typeof quickActions[0] & { index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.4 + index * 0.06 }}
      whileHover={{ y: -3, scale: 1.03 }}
    >
      <Link
        href={href}
        className="glow-card glass rounded-2xl p-4 flex flex-col items-center gap-2.5 group text-center h-full"
      >
        <div
          className="w-12 h-12 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300"
          style={{ background: `linear-gradient(135deg, ${color}22, ${color}44)`, border: `1px solid ${color}40` }}
        >
          <Icon size={22} style={{ color }} />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">{label}</p>
          <p className="text-[11px] text-slate-400 mt-0.5">{desc}</p>
        </div>
      </Link>
    </motion.div>
  );
}

/* ─── Recent Docs Table ─────────────────────────────────────────────────── */

function StatusBadge({ status }: { status: string }) {
  if (status === 'ready')
    return (
      <span className="badge-ready inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-semibold bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
        <span className="pulse-dot w-1.5 h-1.5 rounded-full bg-emerald-500" />
        Ready
      </span>
    );
  if (status === 'error')
    return (
      <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-semibold bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800">
        <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
        Error
      </span>
    );
  return (
    <span className="badge-processing inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-semibold bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
      Processing
    </span>
  );
}

/* ─── System Info ────────────────────────────────────────────────────────── */

const systemInfo = [
  { label: 'Embedding Model', value: 'nomic-embed-text (Ollama)', icon: Zap, color: '#3B82F6' },
  { label: 'LLM Model', value: 'Checking configuration…', icon: Brain, color: '#A855F7' },
  { label: 'Vector DB', value: 'PostgreSQL + pgvector (HNSW)', icon: Layers, color: '#06B6D4' },
  { label: 'Search', value: 'Hybrid: Vector + BM25 → RRF', icon: Network, color: '#10B981' },
  { label: 'Graph DB', value: 'Neo4j Community Edition', icon: Share2 as typeof Network, color: '#F59E0B' },
  { label: 'Chunk size', value: '500 chars / overlap 50', icon: BookOpen as typeof Network, color: '#EF4444' },
];

/* ─── Main Page ──────────────────────────────────────────────────────────── */

export default function DashboardPage() {
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [stats, setStats] = useState<DocStats | null>(null);
  const [readiness, setReadiness] = useState<SystemReadiness | null>(null);
  const { chatMessages } = useAppStore();

  useEffect(() => {
    getDocuments().then(setDocs).catch(console.error);
    getDocStats().then(setStats).catch(console.error);
    getSystemReadiness().then(setReadiness).catch(console.error);
  }, []);

  const userMessages = chatMessages.filter(m => m.role === 'user').length;
  const recentDocs = [...docs]
    .sort((a, b) => new Date(b.created_at ?? 0).getTime() - new Date(a.created_at ?? 0).getTime())
    .slice(0, 6);

  const processingCount = stats?.processing_documents ?? docs.filter(d => d.status === 'processing').length;
  const readyCount = stats?.ready_documents ?? docs.filter(d => d.status === 'ready').length;
  const totalDocs = stats?.total_documents ?? docs.length;
  const displayedSystemInfo = systemInfo.map((item) =>
    item.label === 'LLM Model' && readiness
      ? { ...item, value: readiness.llm_configured ? readiness.llm_model : `${readiness.llm_model} (not configured)` }
      : item
  );

  return (
    <div className="relative min-h-screen">
      <ParticleField />

      <div className="relative z-10 max-w-6xl mx-auto p-6 space-y-8">

        {/* ── Header ─────────────────────────────────────────────────────── */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold gradient-text mb-1">Dashboard</h1>
              <p className="text-slate-500 dark:text-slate-400 text-sm">
                System Overview · {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
              </p>
            </div>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link
                href="/upload"
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all"
                style={{ background: 'linear-gradient(135deg, #3B82F6, #A855F7)' }}
              >
                <Upload size={15} />
                Upload PDF
              </Link>
            </motion.div>
          </div>
        </motion.div>

        {/* ── Stats Grid ─────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard icon={FileText} label="Total Documents" value={totalDocs} sub="uploaded PDF files" href="/library" index={0} />
          <StatCard icon={CheckCircle} label="Ready" value={readyCount} sub={processingCount > 0 ? `${processingCount} processing` : 'all ready'} index={1} badge={processingCount > 0 ? `${processingCount} running` : undefined} />
          <StatCard icon={Layers} label="Total Chunks" value={stats ? stats.total_chunks.toLocaleString('en-US') : '—'} sub="chunks embedded" index={2} />
          <StatCard icon={MessageCircle} label="Questions" value={userMessages} sub="current session" href="/chat" index={3} />
        </div>

        {/* ── Main Grid ──────────────────────────────────────────────────── */}
        <div className="grid lg:grid-cols-3 gap-6">

          {/* Recent Documents */}
          <motion.div
            className="lg:col-span-2"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
          >
            <div className="glass rounded-2xl overflow-hidden h-full">
              <div className="px-5 py-4 flex items-center justify-between border-b border-white/20 dark:border-white/5">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                    <Clock size={15} color="white" />
                  </div>
                  <h2 className="font-semibold text-slate-700 dark:text-slate-200">Recent Documents</h2>
                </div>
                <Link href="/library" className="text-xs text-blue-500 hover:text-blue-600 flex items-center gap-1 font-medium">
                  View all <ArrowRight size={12} />
                </Link>
              </div>

              <div className="divide-y divide-white/10 dark:divide-white/5">
                {recentDocs.length === 0 ? (
                  <div className="py-12 text-center">
                    <FileText size={32} className="mx-auto text-slate-300 dark:text-slate-600 mb-3" />
                    <p className="text-slate-400 text-sm">No documents yet</p>
                    <Link href="/upload" className="text-xs text-blue-500 mt-2 inline-block hover:text-blue-600">
                      Upload your first document →
                    </Link>
                  </div>
                ) : (
                  recentDocs.map((doc, i) => (
                    <motion.div
                      key={doc.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.35 + i * 0.05 }}
                      className="flex items-center gap-3 px-5 py-3 group hover:bg-blue-50/50 dark:hover:bg-blue-900/10 transition-colors"
                    >
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900/30 dark:to-purple-900/30 flex items-center justify-center flex-shrink-0">
                        <FileText size={14} className="text-blue-600 dark:text-blue-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-slate-700 dark:text-slate-200 font-medium truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                          {doc.title || doc.filename}
                        </p>
                        <p className="text-xs text-slate-400 mt-0.5">
                          {doc.total_pages ? `${doc.total_pages} pages · ` : ''}
                          {doc.created_at ? new Date(doc.created_at).toLocaleDateString('en-US') : ''}
                        </p>
                      </div>
                      <StatusBadge status={doc.status} />
                    </motion.div>
                  ))
                )}
              </div>
            </div>
          </motion.div>

          {/* System Info */}
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.35 }}>
            <div className="glass rounded-2xl overflow-hidden h-full">
              <div className="px-5 py-4 border-b border-white/20 dark:border-white/5 flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                  <Zap size={15} color="white" />
                </div>
                <h2 className="font-semibold text-slate-700 dark:text-slate-200">AI System</h2>
              </div>
              <div className="p-4 space-y-3">
                {displayedSystemInfo.map(({ label, value, icon: Icon, color }, i) => (
                  <motion.div
                    key={label}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 + i * 0.05 }}
                    className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-white/50 dark:hover:bg-white/5 transition-colors"
                  >
                    <div
                      className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
                      style={{ background: `${color}15`, border: `1px solid ${color}30` }}
                    >
                      <Icon size={14} style={{ color }} />
                    </div>
                    <div>
                      <p className="text-[11px] text-slate-400 uppercase tracking-wider font-medium">{label}</p>
                      <p className="text-xs text-slate-600 dark:text-slate-300 font-semibold mt-0.5 leading-tight">{value}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>

        {/* ── Quick Actions ───────────────────────────────────────────────── */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}>
          <div className="flex items-center gap-2 mb-4">
            <Zap size={16} className="text-blue-500" />
            <h2 className="font-semibold text-slate-700 dark:text-slate-200">Quick Access</h2>
          </div>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
            {quickActions.map((action, i) => (
              <QuickAction key={action.href} {...action} index={i} />
            ))}
          </div>
        </motion.div>

        {/* ── AI Activity Strip ───────────────────────────────────────────── */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.55 }}>
          <div
            className="glass rounded-2xl p-5 relative overflow-hidden"
            style={{ background: 'linear-gradient(135deg, rgba(59,130,246,0.06), rgba(168,85,247,0.06))' }}
          >
            {/* Decorative orbs */}
            <div className="orb w-48 h-48 -top-12 -right-12" style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.15), transparent)' }} />
            <div className="orb w-32 h-32 -bottom-8 left-20" style={{ background: 'radial-gradient(circle, rgba(168,85,247,0.12), transparent)' }} />

            <div className="relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`pulse-dot w-2.5 h-2.5 rounded-full ${readiness?.ready_for_rag ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                  <span className={`text-xs font-semibold uppercase tracking-wider ${readiness?.ready_for_rag ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}`}>
                    {readiness?.ready_for_rag ? 'RAG is ready' : 'RAG setup required'}
                  </span>
                </div>
                <h3 className="text-lg font-bold gradient-text">Acamind AI Platform</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                  {readiness?.ready_for_rag
                    ? 'RAG · Psychology Knowledge Base · Medical 3D'
                    : readiness?.issues?.[0] || 'Checking RAG prerequisites...'}
                </p>
              </div>
              <div className="flex gap-3 flex-shrink-0">
                <Link
                  href={readiness?.ready_for_rag ? '/chat' : '/upload'}
                  className="px-4 py-2 rounded-xl text-sm font-semibold text-white shadow-lg transition-all hover:scale-105"
                  style={{ background: 'linear-gradient(135deg, #3B82F6, #A855F7)' }}
                >
                  {readiness?.ready_for_rag ? 'Start Chat' : 'Set up RAG'}
                </Link>
                <Link
                  href="/3d"
                  className="px-4 py-2 rounded-xl text-sm font-semibold border transition-all hover:scale-105 text-slate-700 dark:text-slate-200"
                  style={{ borderColor: 'rgba(59,130,246,0.3)', background: 'rgba(59,130,246,0.06)' }}
                >
                  3D Body
                </Link>
              </div>
            </div>
          </div>
        </motion.div>

      </div>
    </div>
  );
}

/* ── Tiny re-export for missing icon ────────────────────────────────────── */
function Share2({ size, style }: { size: number; style?: React.CSSProperties }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={style}>
      <circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" />
      <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" /><line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
    </svg>
  );
}
