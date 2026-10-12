'use client';

import { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { fetchGraph, fetchAuthorPapers, GraphData } from '@/lib/api';
import KnowledgeGraph from '@/components/graph/KnowledgeGraph';
import { useAppStore } from '@/store/useAppStore';
import { GuestBlockScreen } from '@/components/auth/AuthRequiredModal';
import Link from 'next/link';
import {
  Search,
  RefreshCw,
  X,
  Network,
  ArrowLeft,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { NeuralCard } from '@/components/ui/NeuralCard';
import { NeuralBadge } from '@/components/ui/NeuralBadge';

export default function GraphPage() {
  const { user } = useAppStore();
  const [mounted, setMounted] = useState(false);
  const [data, setData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [searching, setSearching] = useState(false);
  const [filtered, setFiltered] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const loadAll = async () => {
    setLoading(true);
    setError('');
    setFiltered(false);
    setSearch('');
    try {
      setData(await fetchGraph());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const searchAuthor = async () => {
    const name = search.trim();
    if (!name) {
      loadAll();
      return;
    }
    setSearching(true);
    setError('');
    try {
      setData(await fetchAuthorPapers(name));
      setFiltered(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSearching(false);
    }
  };

  const clearFilter = () => {
    setSearch('');
    loadAll();
  };

  useEffect(() => {
    if (user) {
      loadAll();
    } else {
      setLoading(false);
    }
  }, [user]);

  if (mounted && !user) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-4">
        <GuestBlockScreen
          title="Yêu cầu đăng nhập để khám phá Đồ thị Tri thức"
          description="Hệ thống Knowledge Graph liên kết tác giả, bài báo và chủ đề nghiên cứu chuyên sâu chỉ dành cho tài khoản đã đăng nhập."
        />
      </div>
    );
  }

  const busy = loading || searching;
  const authorCount = data?.stats?.total_authors ?? data?.nodes.filter((n) => n.type === 'author').length ?? 0;
  const docCount = data?.stats?.total_documents ?? data?.nodes.filter((n) => n.type === 'document').length ?? 0;

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-surface-base">
      {/* ── Header ──────────────────────────────────────────────────── */}
      <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 md:px-6 py-4">
          {/* Top row */}
          <div className="flex items-center justify-between gap-4 mb-4">
            {/* Title */}
            <div className="flex items-center gap-4">
              <Link
                href="/library"
                className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-neural-600 dark:text-gray-400 dark:hover:text-neural-400 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Library</span>
              </Link>

              <div className="w-px h-6 bg-gray-200 dark:bg-gray-700" />

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-neural-500 via-cortex-500 to-dopamine-500 flex items-center justify-center shadow-lg shadow-neural-500/25">
                  <Network className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-lg font-bold text-gray-900 dark:text-white">
                    Knowledge Graph
                  </h1>
                  <p className="text-xs text-gray-500">Author & Article Network</p>
                </div>
              </div>
            </div>

            {/* Badges */}
            <div className="flex items-center gap-2">
              <NeuralBadge variant="neural" size="sm" dot pulse>
                Real-time
              </NeuralBadge>
              <NeuralBadge variant="cortex" size="sm">
                AI Mapped
              </NeuralBadge>
            </div>
          </div>

          {/* Bottom row - Stats & Search */}
          <div className="flex items-center justify-between gap-4">
            {/* Stats */}
            <div className="flex items-center gap-3">
              {data && !busy ? (
                <>
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-neural-50 dark:bg-neural-900/30 border border-neural-200 dark:border-neural-800">
                    <span className="w-2 h-2 rounded-full bg-neural-500" />
                    <span className="text-sm font-medium text-neural-700 dark:text-neural-300">
                      {authorCount} authors
                    </span>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-cortex-50 dark:bg-cortex-900/30 border border-cortex-200 dark:border-cortex-800">
                    <span className="w-2 h-2 rounded-full bg-cortex-500" />
                    <span className="text-sm font-medium text-cortex-700 dark:text-cortex-300">
                      {docCount} documents
                    </span>
                  </div>
                  {filtered && (
                    <button
                      onClick={clearFilter}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-dopamine-50 dark:bg-dopamine-900/30 border border-dopamine-200 dark:border-dopamine-800 text-sm font-medium text-dopamine-700 dark:text-dopamine-300 hover:bg-dopamine-100 dark:hover:bg-dopamine-900/50 transition-colors"
                    >
                      Filtered
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </>
              ) : (
                <span className="text-sm text-gray-500">Loading graph...</span>
              )}
            </div>

            {/* Search & Actions */}
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                <input
                  ref={inputRef}
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && searchAuthor()}
                  placeholder="Search authors..."
                  className="w-48 pl-9 pr-4 py-2 text-sm bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-xl border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-neural-500/30 focus:border-neural-500 transition-all placeholder:text-gray-400"
                />
              </div>

              <button
                onClick={searchAuthor}
                disabled={busy || !search.trim()}
                className="btn-neural px-4 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {searching ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  'Search'
                )}
              </button>

              <button
                onClick={loadAll}
                disabled={busy}
                title="Refresh"
                className="p-2 rounded-xl text-gray-400 hover:text-neural-600 hover:bg-neural-50 dark:hover:bg-neural-900/30 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── Canvas ─────────────────────────────────────────────────── */}
      <div className="flex-1 relative overflow-hidden">
        {/* Loading State */}
        <AnimatePresence>
          {busy && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 flex flex-col items-center justify-center gap-4 z-10 bg-gray-50/80 dark:bg-surface-base/80 backdrop-blur-sm"
            >
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-neural-500 to-cortex-500 flex items-center justify-center shadow-lg shadow-neural-500/25">
                <Network className="w-6 h-6 text-white animate-pulse" />
              </div>
              <div className="text-center">
                <p className="text-base font-medium text-gray-700 dark:text-gray-300">
                  {searching ? 'Searching...' : 'Loading graph...'}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Please wait a moment
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error State */}
        {!busy && error && (
          <div className="absolute inset-0 flex items-center justify-center p-6">
            <NeuralCard variant="glass" className="text-center py-12 px-8 max-w-md">
              <div className="w-16 h-16 mx-auto rounded-2xl bg-red-50 dark:bg-red-900/20 flex items-center justify-center mb-6">
                <AlertCircle className="w-8 h-8 text-red-500" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                Cannot load graph
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                {error}
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mb-6">
                Check that Neo4j is running at localhost:7474
              </p>
              <button onClick={loadAll} className="btn-neural">
                <RefreshCw className="w-4 h-4 mr-2" />
                Try again
              </button>
            </NeuralCard>
          </div>
        )}

        {/* Empty State */}
        {!busy && !error && data && data.nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center p-6">
            <NeuralCard variant="glass" className="text-center py-12 px-8 max-w-md">
              <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-neural-100 to-cortex-100 dark:from-neural-900/50 dark:to-cortex-900/50 flex items-center justify-center mb-6">
                <Network className="w-8 h-8 text-neural-600 dark:text-neural-400" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                {filtered ? 'No authors found' : 'Graph is empty'}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                {filtered
                  ? 'Try another name or clear the filter to see all.'
                  : 'Upload PDF documents and the system will automatically build the knowledge graph.'}
              </p>
              <div className="flex items-center justify-center gap-3">
                {filtered && (
                  <button onClick={clearFilter} className="btn-neural-outline">
                    Clear Filter
                  </button>
                )}
                <Link href="/library/upload" className="btn-neural">
                  Upload documents
                </Link>
              </div>
            </NeuralCard>
          </div>
        )}

        {/* Graph */}
        {!busy && !error && data && data.nodes.length > 0 && (
          <KnowledgeGraph data={data} />
        )}
      </div>
    </div>
  );
}