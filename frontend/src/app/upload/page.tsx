'use client';

import React, { useState, useRef, useEffect, useCallback, DragEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
 Upload, FileText, CheckCircle, XCircle, Clock,
 ArrowLeft, X, BookOpen, Tag, Loader2,
} from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { uploadDocument, getDocuments, getCategories, getMyPlanUsage, DocumentInfo, DbCategory, PlanUsage } from '@/lib/api';
import { useI18n } from '@/lib/i18n/context';
import { GuestBlockScreen } from '@/components/auth/AuthRequiredModal';

// ── Types ─────────────────────────────────────────────────────────────────────

interface QueueItem {
 id: string;
 file: File;
 status: 'pending' | 'uploading' | 'processing' | 'ready' | 'error';
 documentId?: string;
 error?: string;
 category?: string;
 progress?: number; // 0-100
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function catStyle(color: string): React.CSSProperties {
 return { backgroundColor: color + '22', color };
}

function formatSize(bytes: number): string {
 if (bytes < 1024) return `${bytes} B`;
 if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
 return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const STATUS_CONFIG = {
  pending: { label: 'Pending', icon: Clock, color: 'text-slate-400 dark:text-slate-500' },
  uploading: { label: 'Uploading...', icon: Loader2, color: 'text-blue-500', spin: true },
  processing: { label: 'Processing...', icon: Loader2, color: 'text-amber-500', spin: true },
  ready: { label: 'Completed', icon: CheckCircle, color: 'text-emerald-500' },
};

// ── Component ─────────────────────────────────────────────────────────────────

export default function UploadPage() {
 const { user } = useAppStore();
 const router = useRouter();
 const { t } = useI18n();

 const [categories, setCategories] = useState<DbCategory[]>([]);
 const [selectedCat, setSelectedCat] = useState<string>('');
 const [queue, setQueue] = useState<QueueItem[]>([]);
 const [dragging, setDragging] = useState(false);
 const [recentDocs, setRecentDocs] = useState<DocumentInfo[]>([]);
 const [planUsage, setPlanUsage] = useState<PlanUsage | null>(null);

 const fileInputRef = useRef<HTMLInputElement>(null);
 const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
 const mountedRef = useRef(true);

 // ── Auth guard ─────────────────────────────────────────────────────────────
 useEffect(() => {
 // Wait for user to load before checking permissions
 if (user === undefined) return; // Still loading, wait
 if (user === null) return; // Not logged in, may show login prompt
 if (user.role !== 'admin' && user.role !== 'researcher') {
 router.replace('/library');
 }
 }, [user]);

 // ── Load categories & recent docs ──────────────────────────────────────────
 useEffect(() => {
 mountedRef.current = true;
 getCategories().then(setCategories).catch(() => {});
 getMyPlanUsage().then(setPlanUsage).catch(() => {});
 loadRecentDocs();
 return () => {
 mountedRef.current = false;
 if (pollRef.current) clearInterval(pollRef.current);
 };
 }, []);

 const loadRecentDocs = async () => {
 try {
 const docs = await getDocuments();
 if (mountedRef.current) setRecentDocs(docs.filter(d => d.is_owner).slice(0, 5));
 } catch { /* silent */ }
 };

 // ── Poll processing items ──────────────────────────────────────────────────
 const startPolling = useCallback(() => {
 if (pollRef.current) return;
 pollRef.current = setInterval(async () => {
 const processing = queue.filter(q => q.status === 'processing');
 if (processing.length === 0) {
 clearInterval(pollRef.current!);
 pollRef.current = null;
 return;
 }
 try {
 const docs = await getDocuments();
 if (!mountedRef.current) return;
 setQueue(prev => prev.map(item => {
 if (item.status !== 'processing' || !item.documentId) return item;
 const doc = docs.find(d => d.id === item.documentId);
 if (!doc) return item;
 if (doc.status === 'ready') return { ...item, status: 'ready' };
 if (doc.status === 'error') return { ...item, status: 'error', error: 'Pipeline error' };
 return item;
 }));
 setRecentDocs(docs.filter(d => d.is_owner).slice(0, 5));
 } catch { /* silent */ }
 }, 3000);
 }, [queue]);

 useEffect(() => {
 const hasProcessing = queue.some(q => q.status === 'processing');
 if (hasProcessing) startPolling();
 }, [queue]);

 // ── File handling ──────────────────────────────────────────────────────────

 const addFiles = (files: FileList | File[]) => {
 const pdfs = Array.from(files).filter(f => f.name.toLowerCase().endsWith('.pdf'));
 if (pdfs.length === 0) return;
 const newItems: QueueItem[] = pdfs.map(f => ({
 id: Math.random().toString(36).slice(2),
 file: f,
 status: 'pending',
 category: selectedCat || undefined,
 progress: 0,
 }));
 setQueue(prev => [...prev, ...newItems]);
 // Upload up to 3 files in parallel for speed
 const CONCURRENCY = 3;
 let idx = 0;
 const next = () => {
 if (idx >= newItems.length) return;
 const item = newItems[idx++];
 processItem(item).finally(() => next());
 };
 for (let i = 0; i < Math.min(CONCURRENCY, newItems.length); i++) next();
 };

 const processItem = async (item: QueueItem) => {
 setQueue(prev => prev.map(q => q.id === item.id ? { ...q, status: 'uploading', progress: 0 } : q));
 try {
 const result = await uploadDocument(
 item.file,
 item.category || null,
 (loaded, total) => {
 const pct = total > 0 ? Math.round((loaded / total) * 100) : 0;
 setQueue(prev => prev.map(q => q.id === item.id ? { ...q, progress: pct } : q));
 },
 );
 setQueue(prev => prev.map(q =>
 q.id === item.id
 ? { ...q, status: 'processing', documentId: result.document_id, progress: 100 }
 : q,
 ));
 } catch (err: unknown) {
 const errWithResponse = err as { response?: { data?: { detail?: string } } };
 const msg = errWithResponse?.response?.data?.detail ?? 'Upload failed';
 setQueue(prev => prev.map(q => q.id === item.id ? { ...q, status: 'error', error: msg } : q));
 }
 };

 const removeItem = (id: string) =>
 setQueue(prev => prev.filter(q => q.id !== id));

 const retryItem = (item: QueueItem) => {
 setQueue(prev => prev.map(q =>
 q.id === item.id ? { ...q, status: 'pending', error: undefined, documentId: undefined } : q,
 ));
 processItem({ ...item, status: 'pending', error: undefined, documentId: undefined });
 };

 // ── Drag & drop ────────────────────────────────────────────────────────────

 const onDragOver = (e: DragEvent) => { e.preventDefault(); setDragging(true); };
 const onDragLeave = (e: DragEvent) => { e.preventDefault(); setDragging(false); };
 const onDrop = (e: DragEvent) => {
 e.preventDefault(); setDragging(false);
 addFiles(e.dataTransfer.files);
 };

 // ── Render ─────────────────────────────────────────────────────────────────

 // Show loading while checking auth
 if (user === undefined) {
 return (
 <div className="flex items-center justify-center min-h-[50vh]">
 <div className="flex flex-col items-center gap-3">
 <div className="w-8 h-8 border-2 border-teal-500/30 border-t-teal-500 rounded-full animate-spin" />
 <p className="text-sm text-slate-500">Loading...</p>
 </div>
 </div>
 );
 }

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-4">
        <GuestBlockScreen
          title="Yêu cầu đăng nhập để tải lên tài liệu"
          description="Bạn cần đăng nhập tài khoản Nhà nghiên cứu hoặc Quản trị viên để đóng góp tài liệu vào thư viện Acamind."
        />
      </div>
    );
  }

 const stats = {
 total: queue.length,
 done: queue.filter(q => q.status === 'ready').length,
 processing: queue.filter(q => q.status === 'uploading' || q.status === 'processing').length,
 error: queue.filter(q => q.status === 'error').length,
 };

 return (
 <div className="max-w-4xl mx-auto p-6 space-y-6">

  {/* Header */}
  <div className="flex items-center gap-3">
    <Link
      href="/library"
      className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-[#1E88E5] dark:hover:text-[#1E88E5] transition-colors"
    >
      <ArrowLeft className="w-3.5 h-3.5" />
      {t.upload.library}
    </Link>
    <div className="w-px h-4 bg-slate-200 dark:bg-slate-700" />
    <div>
      <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100">{t.upload.title}</h1>
      <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">{t.upload.subtitle}</p>
    </div>
  </div>

 {/* Plan usage banner */}
 {planUsage && planUsage.max_docs !== null && (
 <div className={`flex items-center justify-between gap-3 px-4 py-3 rounded-xl border text-sm ${
 planUsage.used_docs >= planUsage.max_docs
 ? 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-800'
 : planUsage.used_docs >= planUsage.max_docs * 0.8
 ? 'bg-amber-50 dark:bg-amber-900/10 border-amber-200 dark:border-amber-800'
 : 'bg-indigo-50 dark:bg-indigo-900/10 border-indigo-200 dark:border-indigo-800'
 }`}>
 <div>
        <p className="font-medium text-slate-800 dark:text-slate-100 text-xs">
          Plan {planUsage.plan_label}: {planUsage.used_docs}/{planUsage.max_docs} {t.upload.pages.replace('trang', 'documents')}
        </p>
        {planUsage.used_docs >= planUsage.max_docs && (
          <p className="text-[10px] text-red-600 dark:text-red-400 mt-0.5">
            {t.upload.limit_reached}
          </p>
        )}
 </div>
 {planUsage.used_docs >= planUsage.max_docs && (
 <Link
 href="/pricing"
 className="shrink-0 text-xs font-semibold px-3 py-1.5 rounded-lg bg-red-500 hover:bg-red-600 text-white transition-colors"
 >
 Upgrade
 </Link>
 )}
 </div>
 )}

 <div className="grid lg:grid-cols-3 gap-6">

 {/* Left: Upload zone + queue */}
 <div className="lg:col-span-2 space-y-4">

 {/* Category selector */}
 <div className="flex items-center gap-2 flex-wrap">
  <Tag className="w-4 h-4 text-slate-400 dark:text-slate-500 shrink-0" />
  <span className="text-sm text-slate-500 dark:text-slate-400 shrink-0">{t.upload.category}:</span>
  <select
    value={selectedCat}
    onChange={e => setSelectedCat(e.target.value)}
    className="flex-1 min-w-[160px] text-sm border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-1.5 bg-white dark:bg-slate-800/60 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-[#1E88E5]/30"
  >
    <option value="">{t.upload.uncategorized}</option>
 {categories.map(c => (
 <option key={c.id} value={c.name}>{c.name}</option>
 ))}
 </select>
 {selectedCat && (
 <button onClick={() => setSelectedCat('')} className="text-slate-400 dark:text-slate-500 transition-colors">
 <X className="w-4 h-4" />
 </button>
 )}
 </div>

 {/* Drop zone */}
 <div
 onDragOver={onDragOver}
 onDragLeave={onDragLeave}
 onDrop={onDrop}
 onClick={() => fileInputRef.current?.click()}
 className={`relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200 ${
 dragging
 ? 'border-[#1E88E5] bg-[#1E88E5]/5 scale-[1.01]'
 : 'border-slate-300 dark:border-slate-600 hover:border-[#1E88E5] hover:bg-[#1E88E5]/5 dark:hover:bg-[#1E88E5]/10'
 }`}
 >
 <input
 ref={fileInputRef}
 type="file"
 accept=".pdf"
 multiple
 className="hidden"
 onChange={e => e.target.files && addFiles(e.target.files)}
 />
 <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4 transition-colors ${
 dragging ? 'bg-[#1E88E5] text-white' : 'bg-slate-100 dark:bg-slate-800/60 text-slate-400 dark:text-slate-500'
 }`}>
 <Upload className="w-7 h-7" />
 </div>
  <p className="text-base font-semibold text-slate-700 dark:text-slate-200">
    {dragging ? t.upload.drop_here : t.upload.drag_drop}
  </p>
  <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">{t.upload.support_hint}</p>
 {selectedCat && (
 <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium" style={catStyle(categories.find(c => c.name === selectedCat)?.color ?? '#6366f1')}>
 <Tag className="w-3 h-3" />
 {selectedCat}
 </div>
 )}
 </div>

 {/* Upload queue */}
 {queue.length > 0 && (
 <div className="bg-white dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 overflow-hidden">
 {/* Queue header */}
 <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 dark:border-slate-800">
      <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">
        {t.upload.queue} ({queue.length})
      </span>
      <div className="flex items-center gap-3 text-xs text-slate-400 dark:text-slate-500">
        {stats.done > 0 && <span className="text-emerald-500">{stats.done} {t.upload.completed}</span>}
        {stats.processing > 0 && <span className="text-amber-500">{stats.processing} {t.upload.processing}</span>}
        {stats.error > 0 && <span className="text-red-500">{stats.error} {t.upload.errors}</span>}
      </div>
 </div>

 {/* Queue items */}
 <ul className="divide-y divide-gray-50">
 {queue.map(item => {
 const cfg = {
   pending: { label: t.upload.pending_lbl, icon: Clock, color: 'text-slate-400 dark:text-slate-500' },
   uploading: { label: t.upload.uploading_lbl, icon: Loader2, color: 'text-blue-500', spin: true },
   processing: { label: t.upload.processing_lbl, icon: Loader2, color: 'text-amber-500', spin: true },
   ready: { label: t.upload.completed_lbl, icon: CheckCircle, color: 'text-emerald-500' },
   error: { label: t.upload.error_lbl, icon: XCircle, color: 'text-red-500' },
 }[item.status];
 const Icon = cfg.icon;
 return (
 <li key={item.id} className="flex items-center gap-3 px-4 py-3">
 {/* File icon */}
 <div className="w-9 h-9 rounded-lg bg-red-50 dark:bg-red-900/20 flex items-center justify-center shrink-0">
 <FileText className="w-5 h-5 text-red-400" />
 </div>

 {/* Info */}
 <div className="flex-1 min-w-0">
 <p className="text-sm font-medium text-slate-700 dark:text-slate-200 truncate">
 {item.file.name}
 </p>
 <div className="flex items-center gap-2 mt-0.5">
 <span className="text-xs text-slate-400 dark:text-slate-500">{formatSize(item.file.size)}</span>
 {item.category && (
 <>
 <span className="text-gray-200 dark:text-gray-700">·</span>
 <span className="text-xs" style={{ color: categories.find(c => c.name === item.category)?.color ?? '#6b7280' }}>
 {item.category}
 </span>
 </>
 )}
 {item.error && (
 <span className="text-xs text-red-500 truncate">{item.error}</span>
 )}
 </div>
 {item.status === 'uploading' && (
 <div className="mt-1.5 h-1.5 w-full bg-slate-100 dark:bg-slate-800/60 rounded-full overflow-hidden">
 <div
 className="h-full bg-blue-500 transition-all duration-200"
 style={{ width: `${item.progress ?? 0}%` }}
 />
 </div>
 )}
 </div>

  {/* Status */}
  <div className={`flex items-center gap-1.5 text-xs font-medium shrink-0 ${cfg.color}`}>
    <Icon className={`w-4 h-4 ${'spin' in cfg && cfg.spin ? 'animate-spin' : ''}`} />
    <span className="hidden sm:block">
      {item.status === 'pending' ? t.upload.pending_lbl :
       item.status === 'uploading' ? t.upload.uploading_lbl :
       item.status === 'processing' ? t.upload.processing_lbl :
       item.status === 'ready' ? t.upload.completed_lbl :
       t.upload.error_lbl}
    </span>
  </div>

 {/* Actions */}
 <div className="flex items-center gap-1 shrink-0">
 {item.status === 'error' && (
 <button
 onClick={() => retryItem(item)}
 className="text-xs text-blue-500 hover:text-blue-700 px-2 py-1 rounded hover:bg-indigo-50 dark:hover:bg-indigo-900/20 dark:hover:bg-indigo-900/20 dark:hover:bg-indigo-900/20 dark:hover:bg-blue-900/20 transition-colors"
 >
 Retry
 </button>
 )}
 {(item.status === 'ready' || item.status === 'error' || item.status === 'pending') && (
 <button
 onClick={() => removeItem(item.id)}
 className="w-6 h-6 flex items-center justify-center text-slate-400 dark:text-slate-500 dark:hover:text-gray-300 hover:bg-slate-200 dark:hover:bg-slate-700 dark:hover:bg-gray-800 rounded transition-colors"
 >
 <X className="w-3.5 h-3.5" />
 </button>
 )}
 </div>
 </li>
 );
 })}
 </ul>
 </div>
 )}
 </div>

 {/* Right: stats + recent uploads */}
 <div className="space-y-4">

 {/* Stats card */}
 <div className="bg-white dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 p-4 space-y-3">
  <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">{t.upload.session}</h3>
  {[
    { label: t.upload.added, value: stats.total, color: 'text-slate-600 dark:text-slate-300' },
    { label: t.upload.completed_lbl, value: stats.done, color: 'text-emerald-600' },
    { label: t.upload.processing_lbl, value: stats.processing, color: 'text-amber-500' },
    { label: t.upload.error_lbl, value: stats.error, color: 'text-red-500' },
  ].map(s => (
 <div key={s.label} className="flex items-center justify-between">
 <span className="text-xs text-slate-400 dark:text-slate-500">{s.label}</span>
 <span className={`text-sm font-semibold ${s.color}`}>{s.value}</span>
 </div>
 ))}
 </div>

 {/* Recent uploads */}
  <div className="bg-white dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 overflow-hidden">
    <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 dark:border-slate-800">
      <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">{t.upload.recent}</h3>
      <Link href="/library" className="text-xs text-[#1E88E5] hover:underline">{t.upload.view_all}</Link>
    </div>
    {recentDocs.length === 0 ? (
      <div className="flex flex-col items-center justify-center py-8 text-slate-300 dark:text-slate-600">
        <BookOpen className="w-8 h-8 mb-2" />
        <p className="text-xs">{t.upload.no_docs}</p>
      </div>
 ) : (
 <ul className="divide-y divide-gray-50">
 {recentDocs.map(doc => (
 <li key={doc.id} className="flex items-start gap-2.5 px-4 py-3">
 <FileText className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
 <div className="min-w-0 flex-1">
 <p className="text-xs font-medium text-slate-700 dark:text-slate-200 truncate">
 {doc.title || doc.filename}
 </p>
 <div className="flex items-center gap-1.5 mt-0.5">
            <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${
              doc.status === 'ready'
                ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/20 dark:text-emerald-400'
                : doc.status === 'processing'
                ? 'bg-amber-50 text-amber-600 dark:bg-amber-900/20 dark:text-amber-400'
                : 'bg-red-50 text-red-500 dark:bg-red-900/20'
            }`}>
              {doc.status === 'ready' ? t.upload.completed_lbl : doc.status === 'processing' ? t.upload.processing_lbl : t.upload.error_lbl}
            </span>
            {doc.total_pages && (
              <span className="text-[10px] text-slate-400 dark:text-slate-500">{doc.total_pages} {t.upload.pages}</span>
            )}
 </div>
 </div>
 </li>
 ))}
 </ul>
 )}
 </div>

  {/* Tips */}
  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4 border border-blue-100 dark:border-blue-800">
    <p className="text-xs font-semibold text-blue-700 dark:text-blue-300 mb-2">{t.upload.notes}</p>
    <ul className="space-y-1 text-xs text-blue-600 dark:text-blue-400">
      <li>• {t.upload.note_pdf}</li>
      <li>• {t.upload.note_scanned}</li>
      <li>• {t.upload.note_time}</li>
      <li>• {t.upload.note_public}</li>
    </ul>
  </div>
 </div>
 </div>
 </div>
 );
}
