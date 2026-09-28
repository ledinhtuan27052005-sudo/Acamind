'use client';

import React, { useEffect, useState, useRef, useCallback } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { useI18n } from '@/lib/i18n/context';
import {
  Eye,
  Download,
  Trash2,
  Upload,
  BookOpen,
  FileText,
  Sparkles,
  X,
  Check,
  Loader2,
} from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import {
  DocumentInfo,
  DbCategory,
  getDocuments,
  getCategories,
  uploadDocument,
  deleteDocument,
  summarizeDocument,
  updateDocumentCategory,
  updateDocumentMetadata,
  fetchDocumentBlob,
} from '@/lib/api';
import { NeuralCard } from '@/components/ui/NeuralCard';
import { NeuralBadge } from '@/components/ui/NeuralBadge';
import { NeuralButton } from '@/components/ui/NeuralButton';

// ── Category color helpers ─────────────────────────────────────────────────

function catBadgeStyle(color: string): React.CSSProperties {
  return {
    backgroundColor: color + '18',
    color,
    borderColor: color + '30',
  };
}

function getCategoryMeta(value: string | null, cats: DbCategory[]) {
  if (!value) return null;
  return cats.find(c => c.name === value) ?? { id: '', name: value, color: '#6b7280' };
}

// ── Status Configuration ───────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, { label: string; variant: 'success' | 'warning' | 'error'; icon: React.ReactNode }> = {
  ready: {
    label: 'Ready',
    variant: 'success',
    icon: <Check className="w-3 h-3" />,
  },
  processing: {
    label: 'Processing',
    variant: 'warning',
    icon: <Loader2 className="w-3 h-3 animate-spin" />,
  },
  error: {
    label: 'Error',
    variant: 'error',
    icon: <X className="w-3 h-3" />,
  },
};

// ── Document Card ─────────────────────────────────────────────────────────

function DocumentCard({
  doc,
  categories,
  onView,
  onDownload,
  onDelete,
  onSummarize,
  onCategoryChange,
  onAuthorsSave,
  editingCategory,
  editingAuthors,
  setEditingCategory,
  setEditingAuthors,
  loadingPdf,
  isAdmin,
}: {
  doc: DocumentInfo;
  categories: DbCategory[];
  onView: () => void;
  onDownload: () => void;
  onDelete: () => void;
  onSummarize: () => void;
  onCategoryChange: (value: string) => void;
  onAuthorsSave: (value: string) => void;
  editingCategory: string | null;
  editingAuthors: string | null;
  setEditingCategory: (id: string | null) => void;
  setEditingAuthors: (id: string | null) => void;
  loadingPdf: boolean;
  isAdmin: boolean;
}) {
  const { t } = useI18n();
  const statusConfig = STATUS_CONFIG[doc.status] || STATUS_CONFIG.error;
  const catMeta = getCategoryMeta(doc.category, categories);

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'ready': return t.library.ready;
      case 'processing': return t.library.processing;
      case 'error': return t.library.error;
      default: return status;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="neural-card p-5 group"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-4">
        {/* Icon */}
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-neural-500/10 to-cortex-500/10 flex items-center justify-center flex-shrink-0">
          <FileText className="w-6 h-6 text-neural-600 dark:text-neural-400" />
        </div>

        {/* Status */}
        <NeuralBadge variant={statusConfig.variant} className="flex items-center gap-1">
          {statusConfig.icon}
          {getStatusLabel(doc.status)}
        </NeuralBadge>
      </div>

      {/* Title */}
      <h3
        className="font-semibold text-gray-900 dark:text-white line-clamp-2 mb-1 group-hover:text-neural-600 dark:group-hover:text-neural-400 transition-colors"
        title={doc.title || doc.filename}
      >
        {doc.title || doc.filename}
      </h3>

      {/* Filename (if different from title) */}
      {doc.title && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 truncate">
          {doc.filename}
        </p>
      )}

      {/* Authors */}
      <div className="mb-3">
        {doc.is_owner && editingAuthors === doc.id ? (
          <input
            autoFocus
            defaultValue={doc.authors ?? ''}
            onBlur={(e) => onAuthorsSave(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') (e.target as HTMLInputElement).blur();
              if (e.key === 'Escape') setEditingAuthors(null);
            }}
            placeholder="Author name..."
            className="w-full text-sm border border-neural-300 dark:border-neural-700 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-neural-500/30 bg-white dark:bg-gray-900"
          />
        ) : (
          <button
            onClick={() => setEditingAuthors(doc.id)}
            className="w-full text-left group/edit"
          >
            <p className="text-sm text-gray-600 dark:text-gray-400 truncate group-hover/edit:text-gray-900 dark:group-hover/edit:text-gray-200 transition-colors">
              {doc.authors || 'No authors specified'}
            </p>
          </button>
        )}
      </div>

      {/* Category */}
      <div className="mb-4">
        {doc.is_owner && editingCategory === doc.id ? (
          <select
            autoFocus
            defaultValue={doc.category ?? ''}
            onChange={(e) => onCategoryChange(e.target.value)}
            onKeyDown={(e) => e.key === 'Escape' && setEditingCategory(null)}
            className="w-full text-xs border border-neural-300 dark:border-neural-700 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-neural-500/30 bg-white dark:bg-gray-900"
          >
            <option value="">— Uncategorized —</option>
            {categories.map((c) => (
              <option key={c.id} value={c.name}>
                {c.name}
              </option>
            ))}
          </select>
        ) : (
          <button
            onClick={() => setEditingCategory(doc.id)}
            className="w-full text-left"
          >
            {catMeta ? (
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-all hover:scale-105"
                style={catBadgeStyle(catMeta.color)}
              >
                <span
                  className="w-1.5 h-1.5 rounded-full"
                  style={{ backgroundColor: catMeta.color }}
                />
                {catMeta.name}
              </span>
            ) : (
              <span className="text-xs text-gray-400 dark:text-gray-500 italic hover:text-neural-500 transition-colors">
                {t.library.add_category}
              </span>
            )}
          </button>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-800">
        <span className="text-xs text-gray-400">
          {doc.total_pages ? `${doc.total_pages} ${t.library.pages}` : '—'}
        </span>

        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          {doc.status === 'ready' && (
            <button
              onClick={onSummarize}
              title={t.library.summarize}
              className="p-1.5 rounded-lg text-gray-400 hover:text-neural-600 hover:bg-neural-50 dark:hover:bg-neural-900/30 transition-colors"
            >
              <Sparkles className="w-4 h-4" />
            </button>
          )}
          {isAdmin && (
            <>
              <button
                onClick={onView}
                disabled={loadingPdf}
                title={t.library.view_pdf_admin}
                className="p-1.5 rounded-lg text-gray-400 hover:text-neural-600 hover:bg-neural-50 dark:hover:bg-neural-900/30 transition-colors disabled:opacity-50"
              >
                <Eye className="w-4 h-4" />
              </button>
              <button
                onClick={onDownload}
                disabled={loadingPdf}
                title={t.library.download_pdf_admin}
                className="p-1.5 rounded-lg text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-900/30 transition-colors disabled:opacity-50"
              >
                <Download className="w-4 h-4" />
              </button>
            </>
          )}
          {doc.is_owner && (
            <button
              onClick={onDelete}
              title={t.library.delete}
              className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────

export default function LibraryPage() {
  const { user } = useAppStore();
  const { t } = useI18n();
  const canUpload = user?.role === 'admin' || user?.role === 'researcher';
  const isAdmin = user?.role === 'admin';

  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'info' | 'success' | 'error' } | null>(null);
  const [summaryModal, setSummaryModal] = useState<{ docId: string; text: string } | null>(null);
  const [loadingSummary, setLoadingSummary] = useState<string | null>(null);
  const [categories, setCategories] = useState<DbCategory[]>([]);
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [editingCategory, setEditingCategory] = useState<string | null>(null);
  const [editingAuthors, setEditingAuthors] = useState<string | null>(null);
  const [loadingPdf, setLoadingPdf] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchDocs = useCallback(async () => {
    try {
      setDocuments(await getDocuments());
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    fetchDocs();
    getCategories().then(setCategories).catch(() => {});
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [fetchDocs]);

  // ── Upload Handlers ──────────────────────────────────────────────────

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 50 * 1024 * 1024) {
      setMessage({ text: t.library.file_too_large, type: 'error' });
      return;
    }
    await performUpload(file);
  };

  const performUpload = async (file: File) => {
    setUploading(true);
    setMessage({ text: t.library.uploading, type: 'info' });

    try {
      const result = await uploadDocument(file);
      setMessage({ text: `${t.library.processing_id}${result.document_id.slice(0, 8)}...`, type: 'info' });
      await fetchDocs();

      pollRef.current = setInterval(async () => {
        const updated = await getDocuments();
        setDocuments(updated);
        const doc = updated.find((d) => d.id === result.document_id);
        if (doc?.status === 'ready') {
          setMessage({ text: t.library.upload_success, type: 'success' });
          setUploading(false);
          clearInterval(pollRef.current!);
        } else if (doc?.status === 'error') {
          setMessage({ text: t.library.processing_error, type: 'error' });
          setUploading(false);
          clearInterval(pollRef.current!);
        }
      }, 3000);
    } catch (err: unknown) {
      const errWithResponse = err as { response?: { data?: { detail?: string } } };
      const detail = errWithResponse?.response?.data?.detail;
      setMessage({ text: detail || t.library.upload_error, type: 'error' });
      setUploading(false);
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Drag and drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
      await performUpload(file);
    } else {
      setMessage({ text: t.library.pdf_only, type: 'error' });
    }
  };

  // ── Other Handlers ─────────────────────────────────────────────────

  const handleDelete = async (id: string, filename: string) => {
    if (!confirm(t.library.delete_confirm.replace('{filename}', filename))) return;
    try {
      await deleteDocument(id);
      await fetchDocs();
    } catch {
      setMessage({ text: t.library.delete_error, type: 'error' });
    }
  };

  const handleSummarize = async (id: string) => {
    setLoadingSummary(id);
    try {
      const summary = await summarizeDocument(id);
      setSummaryModal({ docId: id, text: summary });
    } catch {
      setMessage({ text: t.library.summary_error, type: 'error' });
    }
    setLoadingSummary(null);
  };

  const handleCategoryChange = async (docId: string, value: string) => {
    const newCat = value === '' ? null : value;
    setDocuments((prev) => prev.map((d) => (d.id === docId ? { ...d, category: newCat } : d)));
    setEditingCategory(null);
    try {
      await updateDocumentCategory(docId, newCat);
    } catch {
      setMessage({ text: t.library.category_error, type: 'error' });
      await fetchDocs();
    }
  };

  const handleAuthorsSave = async (docId: string, value: string) => {
    const newAuthors = value.trim() || null;
    const oldDoc = documents.find((d) => d.id === docId);
    setDocuments((prev) => prev.map((d) => (d.id === docId ? { ...d, authors: newAuthors } : d)));
    setEditingAuthors(null);
    try {
      await updateDocumentMetadata(docId, { authors: newAuthors });
    } catch {
      setMessage({ text: t.library.authors_error, type: 'error' });
      if (oldDoc) setDocuments((prev) => prev.map((d) => (d.id === docId ? oldDoc : d)));
    }
  };

  const handleViewPdf = async (id: string) => {
    setLoadingPdf(id);
    try {
      const blob = await fetchDocumentBlob(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch {
      setMessage({ text: t.library.pdf_load_error, type: 'error' });
    } finally {
      setLoadingPdf(null);
    }
  };

  const handleDownloadPdf = async (id: string, filename: string) => {
    setLoadingPdf(id);
    try {
      const blob = await fetchDocumentBlob(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setMessage({ text: t.library.pdf_download_error, type: 'error' });
    } finally {
      setLoadingPdf(null);
    }
  };

  // ── Filter Logic ─────────────────────────────────────────────────

  const filtered =
    activeCategory === 'all'
      ? documents
      : activeCategory === 'uncategorized'
      ? documents.filter((d) => !d.category)
      : documents.filter((d) => d.category === activeCategory);

  const countByCategory = (val: string) =>
    val === 'all'
      ? documents.length
      : val === 'uncategorized'
      ? documents.filter((d) => !d.category).length
      : documents.filter((d) => d.category === val).length;

  // ── Render ────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-surface-base">
      {/* Header */}
      <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-6xl mx-auto px-4 md:px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-neural-500 to-cortex-500 flex items-center justify-center shadow-lg shadow-neural-500/25">
                <BookOpen className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {t.library.page_title}
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {documents.length} {t.library.page_subtitle}
                </p>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="hidden md:flex items-center gap-6">
              <div className="text-center">
                <p className="text-2xl font-bold text-neural-600 dark:text-neural-400">
                  {documents.filter((d) => d.status === 'ready').length}
                </p>
                <p className="text-xs text-gray-500">{t.library.ready}</p>
              </div>
              <div className="w-px h-10 bg-gray-200 dark:bg-gray-700" />
              <div className="text-center">
                <p className="text-2xl font-bold text-dopamine-500">
                  {documents.filter((d) => d.status === 'processing').length}
                </p>
                <p className="text-xs text-gray-500">{t.library.processing}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-4 md:px-6 py-6 space-y-6">
        {/* Upload Zone */}
        {canUpload ? (
          <motion.div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => !uploading && fileInputRef.current?.click()}
            className={`
              relative rounded-2xl border-2 border-dashed p-10 text-center cursor-pointer
              transition-all duration-300 ease-out
              ${isDragOver
                ? 'border-neural-500 bg-neural-50 dark:bg-neural-900/20 scale-[1.02]'
                : uploading
                ? 'border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 cursor-not-allowed'
                : 'border-gray-300 dark:border-gray-700 hover:border-neural-400 hover:bg-neural-50/50 dark:hover:bg-neural-900/10'
              }
            `}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={handleUpload}
              disabled={uploading}
            />

              <div className="space-y-3">
              <div className={`w-16 h-16 mx-auto rounded-2xl flex items-center justify-center transition-colors ${uploading ? 'bg-gray-100 dark:bg-gray-800' : 'bg-neural-50 dark:bg-neural-900/30'}`}>
                {uploading ? (
                  <Loader2 className="w-8 h-8 text-gray-400 animate-spin" />
                ) : (
                  <Upload className="w-8 h-8 text-neural-500" />
                )}
              </div>
              <div>
                <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
                  {uploading ? t.library.processing : t.library.upload_btn}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  {t.upload.support_hint}
                </p>
              </div>
            </div>

            {/* Animated border on drag */}
            {isDragOver && (
              <div className="absolute inset-0 rounded-2xl border-2 border-neural-500 animate-pulse" />
            )}
          </motion.div>
        ) : (
          <div className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-r from-neural-50/50 to-cortex-50/50 dark:from-neural-900/20 dark:to-cortex-900/20 border border-neural-200/50 dark:border-neural-800/50">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-neural-100 dark:bg-neural-900/50 flex items-center justify-center">
                <Upload className="w-5 h-5 text-neural-600 dark:text-neural-400" />
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {t.library.only_admin}
              </p>
            </div>
            <Link
              href="/researcher-apply"
              className="btn-neural-outline text-xs px-4 py-2"
            >
              {t.library.apply_researcher}
            </Link>
          </div>
        )}

        {/* Toast Messages */}
        <AnimatePresence>
          {message && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`
                flex items-center justify-between gap-4 p-4 rounded-xl shadow-lg
                ${message.type === 'success'
                  ? 'bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300'
                  : message.type === 'error'
                  ? 'bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300'
                  : 'bg-neural-50 dark:bg-neural-900/30 border border-neural-200 dark:border-neural-800 text-neural-700 dark:text-neural-300'
                }
              `}
            >
              <span className="text-sm">{message.text}</span>
              <button
                onClick={() => setMessage(null)}
                className="p-1 hover:bg-black/5 dark:hover:bg-white/10 rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Category Filter */}
        <div className="flex flex-wrap gap-2">
          {[
            { value: 'all', label: t.library.all, color: '' },
            { value: 'uncategorized', label: t.library.uncategorized, color: '' },
            ...categories.map((c) => ({ value: c.name, label: c.name, color: c.color })),
          ].map((cat) => {
            const count = countByCategory(cat.value);
            const isActive = activeCategory === cat.value;

            return (
              <button
                key={cat.value}
                onClick={() => setActiveCategory(cat.value)}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium
                  transition-all duration-200 ease-out
                  ${isActive
                    ? 'bg-gradient-to-r from-neural-500 to-neural-600 text-white shadow-md shadow-neural-500/25'
                    : 'bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-800 hover:border-neural-300 dark:hover:border-neural-700 hover:text-gray-900 dark:hover:text-gray-200'
                  }
                `}
                style={
                  !isActive && cat.color
                    ? catBadgeStyle(cat.color)
                    : undefined
                }
              >
                {cat.color && !isActive && (
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: cat.color }}
                  />
                )}
                <span>{cat.label}</span>
                <span
                  className={`
                    px-1.5 py-0.5 rounded-full text-xs
                    ${isActive ? 'bg-white/20' : 'bg-gray-100 dark:bg-gray-800'}
                  `}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Documents Grid */}
        {filtered.length === 0 ? (
          <NeuralCard variant="glass" className="text-center py-16">
            <div className="space-y-4">
              <div className="w-16 h-16 mx-auto rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                <FileText className="w-8 h-8 text-gray-400" />
              </div>
              <div>
                <p className="text-lg font-medium text-gray-600 dark:text-gray-400">
                  {activeCategory === 'all'
                    ? t.library.no_documents
                    : t.library.no_documents_cat}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  {activeCategory === 'all'
                    ? t.library.upload_first
                    : t.library.select_other}
                </p>
              </div>
            </div>
          </NeuralCard>
        ) : (
          <motion.div
            layout
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            <AnimatePresence mode="popLayout">
              {filtered.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  doc={doc}
                  categories={categories}
                  onView={() => handleViewPdf(doc.id)}
                  onDownload={() => handleDownloadPdf(doc.id, doc.filename)}
                  onDelete={() => handleDelete(doc.id, doc.filename)}
                  onSummarize={() => handleSummarize(doc.id)}
                  onCategoryChange={(value) => handleCategoryChange(doc.id, value)}
                  onAuthorsSave={(value) => handleAuthorsSave(doc.id, value)}
                  editingCategory={editingCategory}
                  editingAuthors={editingAuthors}
                  setEditingCategory={setEditingCategory}
                  setEditingAuthors={setEditingAuthors}
                  loadingPdf={loadingPdf === doc.id}
                  isAdmin={isAdmin}
                />
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </div>

      {/* Summary Modal */}
      <AnimatePresence>
        {summaryModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
            onClick={() => setSummaryModal(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              transition={{ type: 'spring', damping: 25 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-neural-500 to-cortex-500 flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {t.library.article_summary}
                    </h3>
                    <p className="text-xs text-gray-500">{t.library.ai_generated}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSummaryModal(null)}
                  className="p-2 rounded-xl text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-6 overflow-y-auto max-h-[60vh]">
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <div className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
                    {summaryModal.text}
                  </div>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50">
                <NeuralButton variant="ghost" onClick={() => setSummaryModal(null)}>
                  {t.common.close}
                </NeuralButton>
                <Link href="/chat" className="btn-neural">
                  {t.library.ask_ai}
                </Link>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}