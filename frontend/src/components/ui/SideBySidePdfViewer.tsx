'use client';

import React, { useState, useEffect } from 'react';
import {
  FileText, X, ExternalLink, Download, ChevronLeft, ChevronRight,
  RotateCcw, ShieldCheck, Columns, Layers,
} from 'lucide-react';
import { API_URL } from '@/lib/api';

interface SideBySidePdfViewerProps {
  documentId: string;
  filename: string;
  title?: string;
  initialPage: number;
  totalPages?: number | null;
  token?: string | null;
  snippet?: string;
  directUrl?: string;
  onClose: () => void;
}

interface PdfTabItem {
  key: string;
  documentId: string;
  filename: string;
  title?: string;
  citedPage: number;
  currentPage: number;
  totalPages?: number | null;
  directUrl?: string;
}

export function SideBySidePdfViewer({
  documentId,
  filename,
  title,
  initialPage,
  totalPages,
  token,
  snippet,
  directUrl,
  onClose,
}: SideBySidePdfViewerProps) {
  const [openTabs, setOpenTabs] = useState<PdfTabItem[]>([]);
  const [activeKey, setActiveKey] = useState<string>('');
  const [secondaryKey, setSecondaryKey] = useState<string>('');
  const [isSplitView, setIsSplitView] = useState<boolean>(false);
  const [pageInput, setPageInput] = useState<string>(String(initialPage || 1));
  const [secondaryPageInput, setSecondaryPageInput] = useState<string>('1');
  const [iframeKey, setIframeKey] = useState<number>(0);

  // Khi người dùng nhấn vào trích dẫn mới trong bài trả lời, tự động thêm/cập nhật vào thanh Đa Tab PDF
  useEffect(() => {
    const p = Math.max(1, initialPage || 1);
    const tabKey = documentId || filename || 'default-doc';

    setOpenTabs((prev) => {
      const existingIdx = prev.findIndex((t) => t.key === tabKey);
      if (existingIdx >= 0) {
        const updated = [...prev];
        updated[existingIdx] = {
          ...updated[existingIdx],
          filename: filename || updated[existingIdx].filename,
          title: title || updated[existingIdx].title,
          citedPage: p,
          currentPage: p,
          totalPages: totalPages ?? updated[existingIdx].totalPages,
          directUrl: directUrl ?? updated[existingIdx].directUrl,
        };
        return updated;
      }
      const nextTab: PdfTabItem = {
        key: tabKey,
        documentId,
        filename,
        title,
        citedPage: p,
        currentPage: p,
        totalPages,
        directUrl,
      };
      return [...prev.slice(-5), nextTab];
    });

    setActiveKey((prevActive) => {
      if (prevActive && prevActive !== tabKey) {
        setSecondaryKey((prevSec) => prevSec || prevActive);
      }
      return tabKey;
    });
    setPageInput(String(p));
    setIframeKey((k) => k + 1);
  }, [documentId, filename, title, initialPage, totalPages, directUrl, snippet]);

  const activeTab: PdfTabItem = openTabs.find((t) => t.key === activeKey) || {
    key: documentId || filename || 'default-doc',
    documentId,
    filename,
    title,
    citedPage: Math.max(1, initialPage || 1),
    currentPage: Math.max(1, initialPage || 1),
    totalPages,
    directUrl,
  };

  const secondaryTab: PdfTabItem | undefined =
    openTabs.find((t) => t.key === secondaryKey && t.key !== activeTab.key) ||
    openTabs.find((t) => t.key !== activeTab.key);

  useEffect(() => {
    if (secondaryTab) {
      setSecondaryPageInput(String(secondaryTab.currentPage));
    }
  }, [secondaryTab?.key, secondaryTab?.currentPage]);

  const updateTabPage = (targetKey: string, nextPage: number) => {
    setOpenTabs((prev) =>
      prev.map((t) => (t.key === targetKey ? { ...t, currentPage: nextPage } : t))
    );
    if (targetKey === activeTab.key) {
      setPageInput(String(nextPage));
    } else {
      setSecondaryPageInput(String(nextPage));
    }
    setIframeKey((k) => k + 1);
  };

  const handlePrevPage = () => {
    if (activeTab.currentPage > 1) {
      updateTabPage(activeTab.key, activeTab.currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (activeTab.currentPage < (activeTab.totalPages || activeTab.citedPage)) {
      updateTabPage(activeTab.key, activeTab.currentPage + 1);
    }
  };

  const handleJumpToCited = () => {
    updateTabPage(activeTab.key, Math.max(1, activeTab.citedPage || 1));
  };

  const handlePageSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = parseInt(pageInput, 10);
    if (!isNaN(parsed) && parsed >= 1 && (activeTab.totalPages ? parsed <= activeTab.totalPages : parsed <= activeTab.citedPage)) {
      updateTabPage(activeTab.key, parsed);
    } else {
      setPageInput(String(activeTab.currentPage));
    }
  };

  const handleSecondaryPageSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!secondaryTab) return;
    const parsed = parseInt(secondaryPageInput, 10);
    if (!isNaN(parsed) && parsed >= 1 && (secondaryTab.totalPages ? parsed <= secondaryTab.totalPages : parsed <= secondaryTab.citedPage)) {
      updateTabPage(secondaryTab.key, parsed);
    } else {
      setSecondaryPageInput(String(secondaryTab.currentPage));
    }
  };

  const handleRemoveTab = (tabKey: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (openTabs.length <= 1) {
      onClose();
      return;
    }
    const remaining = openTabs.filter((t) => t.key !== tabKey);
    setOpenTabs(remaining);
    if (activeTab.key === tabKey && remaining.length > 0) {
      const nextActive = remaining[remaining.length - 1];
      setActiveKey(nextActive.key);
      setPageInput(String(nextActive.currentPage));
    }
    if (remaining.length < 2) {
      setIsSplitView(false);
    }
  };

  const tokenParam = token ? `?token=${encodeURIComponent(token)}` : '';

  const buildPdfUrl = (tab: PdfTabItem) => {
    return tab.directUrl
      ? `${tab.directUrl.split('#')[0]}#page=${tab.currentPage}&zoom=page-width`
      : `${API_URL}/api/v1/document/${tab.documentId}/file${tokenParam}#page=${tab.currentPage}&zoom=page-width`;
  };

  const buildDownloadUrl = (tab: PdfTabItem) => {
    return tab.directUrl || `${API_URL}/api/v1/document/${tab.documentId}/file${tokenParam}`;
  };

  const pdfUrl = buildPdfUrl(activeTab);
  const rawDownloadUrl = buildDownloadUrl(activeTab);

  return (
    <div className="flex flex-col h-full w-full bg-gray-900 border-l border-gray-200 dark:border-white/10 shadow-2xl relative z-20">
      {/* ── Control Header ── */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-100 dark:bg-[#111827] border-b border-gray-200 dark:border-white/10 text-xs shrink-0 select-none">
        {/* Document Info */}
        <div className="flex items-center gap-2 min-w-0 max-w-[38%]">
          <div className="w-7 h-7 rounded-lg bg-teal-500/10 dark:bg-teal-500/20 text-teal-600 dark:text-teal-400 flex items-center justify-center shrink-0">
            <FileText size={15} />
          </div>
          <div className="min-w-0">
            <p className="font-semibold text-gray-800 dark:text-gray-200 truncate text-[11px]" title={activeTab.title || activeTab.filename}>
              {activeTab.title || activeTab.filename}
            </p>
            <div className="flex items-center gap-1.5 text-[10px] text-gray-500 dark:text-gray-400">
              <span className="flex items-center gap-0.5 text-teal-600 dark:text-teal-400 font-medium">
                <ShieldCheck size={11} /> Đối chiếu nguồn
              </span>
              <span>•</span>
              <span className="truncate">{activeTab.filename}</span>
            </div>
          </div>
        </div>

        {/* Page Navigators */}
        <div className="flex items-center gap-1.5 bg-white dark:bg-white/5 px-2 py-1 rounded-md border border-gray-200 dark:border-white/10">
          <button
            onClick={handlePrevPage}
            disabled={activeTab.currentPage <= 1}
            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed text-gray-700 dark:text-gray-300 transition-colors"
            title="Trang trước"
          >
            <ChevronLeft size={14} />
          </button>

          <form onSubmit={handlePageSubmit} className="flex items-center gap-1">
            <span className="text-[11px] text-gray-500 dark:text-gray-400">Trang</span>
            <input
              type="text"
              value={pageInput}
              onChange={(e) => setPageInput(e.target.value)}
              onBlur={() => setPageInput(String(activeTab.currentPage))}
              className="w-9 h-5 text-center text-[11px] font-mono font-semibold rounded bg-gray-50 dark:bg-black/30 border border-gray-300 dark:border-white/20 text-gray-800 dark:text-gray-200 focus:outline-none focus:border-teal-500"
            />
            {activeTab.totalPages && (
              <span className="text-[11px] text-gray-500 dark:text-gray-400">/ {activeTab.totalPages}</span>
            )}
          </form>

          <button
            onClick={handleNextPage}
            disabled={activeTab.currentPage >= (activeTab.totalPages || activeTab.citedPage)}
            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed text-gray-700 dark:text-gray-300 transition-colors"
            title="Trang kế tiếp"
          >
            <ChevronRight size={14} />
          </button>

          {activeTab.currentPage !== activeTab.citedPage && (
            <button
              onClick={handleJumpToCited}
              className="ml-1 px-1.5 py-0.5 rounded text-[10px] bg-teal-50 dark:bg-teal-900/40 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-700/50 flex items-center gap-0.5 hover:bg-teal-100 transition-colors"
              title={`Quay về trang trích dẫn gốc (${activeTab.citedPage})`}
            >
              <RotateCcw size={10} /> Trang {activeTab.citedPage}
            </button>
          )}
        </div>

        {/* Action Buttons + Split-View Toggle */}
        <div className="flex items-center gap-1">
          {openTabs.length >= 2 && (
            <button
              onClick={() => setIsSplitView((v) => !v)}
              className={`px-2 py-1 rounded-md text-[10px] font-medium flex items-center gap-1 border transition-colors ${
                isSplitView
                  ? 'bg-teal-600 text-white border-teal-500 shadow-sm'
                  : 'bg-white dark:bg-white/5 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-white/10 hover:bg-teal-50 dark:hover:bg-teal-950/30'
              }`}
              title="Bật/Tắt chế độ đối chiếu song song 2 tài liệu PDF"
            >
              <Columns size={12} />
              <span className="hidden sm:inline">So sánh 2 PDF</span>
            </button>
          )}
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1.5 rounded-md hover:bg-gray-200 dark:hover:bg-white/10 text-gray-600 dark:text-gray-400 transition-colors"
            title="Mở tài liệu trong tab mới"
          >
            <ExternalLink size={14} />
          </a>
          <a
            href={rawDownloadUrl}
            download={activeTab.filename}
            className="p-1.5 rounded-md hover:bg-gray-200 dark:hover:bg-white/10 text-gray-600 dark:text-gray-400 transition-colors"
            title="Tải xuống PDF"
          >
            <Download size={14} />
          </a>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-red-50 dark:hover:bg-red-950/40 text-gray-500 hover:text-red-600 dark:hover:text-red-400 transition-colors"
            title="Đóng bảng xem tài liệu"
          >
            <X size={15} />
          </button>
        </div>
      </div>

      {/* ── Multi-Document Comparison Tab Bar (Hiển thị khi người dùng mở >= 2 trích dẫn PDF) ── */}
      {openTabs.length >= 2 && (
        <div className="flex items-center gap-1 px-2.5 py-1.5 bg-gray-50 dark:bg-[#0d1320] border-b border-gray-200 dark:border-white/10 overflow-x-auto shrink-0 select-none">
          <span className="flex items-center gap-1 text-[10px] font-semibold text-teal-600 dark:text-teal-400 pr-1.5 shrink-0">
            <Layers size={11} /> Đa tài liệu ({openTabs.length}):
          </span>
          {openTabs.map((tab) => {
            const isPrimary = tab.key === activeTab.key;
            const isSecondary = isSplitView && secondaryTab?.key === tab.key;
            return (
              <div
                key={tab.key}
                onClick={() => {
                  setActiveKey(tab.key);
                  setPageInput(String(tab.currentPage));
                }}
                className={`group flex items-center gap-1.5 px-2 py-1 rounded text-[10px] cursor-pointer border transition-all shrink-0 max-w-[190px] ${
                  isPrimary
                    ? 'bg-teal-600 text-white border-teal-500 font-semibold shadow-xs'
                    : isSecondary
                    ? 'bg-indigo-600/20 text-indigo-300 border-indigo-500/40 font-medium'
                    : 'bg-white dark:bg-white/5 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-white/10 hover:bg-gray-100 dark:hover:bg-white/10'
                }`}
                title={`${tab.title || tab.filename} (Trang ${tab.currentPage})`}
              >
                <span className="truncate">{tab.filename}</span>
                <span className={`px-1 py-0.2 rounded text-[9px] font-mono ${isPrimary ? 'bg-black/20 text-white' : 'bg-gray-200 dark:bg-white/10 text-gray-600 dark:text-gray-300'}`}>
                  Tr.{tab.currentPage}
                </span>
                <button
                  onClick={(e) => handleRemoveTab(tab.key, e)}
                  className="opacity-60 hover:opacity-100 p-0.5 rounded hover:bg-black/20"
                  title="Đóng tab PDF này"
                >
                  <X size={10} />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* ── PDF Frame Area (1 PDF hoặc Split-View 2 PDF đối chiếu liên bài) ── */}
      <div className={`flex-1 w-full h-full min-h-0 bg-[#323639] relative ${isSplitView && secondaryTab ? 'grid grid-rows-2 xl:grid-rows-1 xl:grid-cols-2 divide-y xl:divide-y-0 xl:divide-x divide-gray-700' : ''}`}>
        {/* Primary PDF Pane */}
        <div className="w-full h-full min-h-0 flex flex-col">
          {isSplitView && secondaryTab && (
            <div className="flex items-center justify-between px-2.5 py-1 bg-[#1e2433] text-gray-200 text-[10px] border-b border-white/10 shrink-0">
              <span className="font-semibold text-teal-400 truncate">
                [Tài liệu A] {activeTab.filename} — Trang {activeTab.currentPage}
              </span>
              <span className="text-gray-400">Trích dẫn gốc: Tr.{activeTab.citedPage}</span>
            </div>
          )}
          <iframe
            key={`${activeTab.key}-page-${activeTab.currentPage}-${iframeKey}`}
            src={pdfUrl}
            title={activeTab.title || activeTab.filename}
            className="w-full flex-1 border-0"
          />
        </div>

        {/* Secondary PDF Pane (chỉ hiển thị khi bật So sánh 2 PDF) */}
        {isSplitView && secondaryTab && (
          <div className="w-full h-full min-h-0 flex flex-col">
            <div className="flex items-center justify-between gap-2 px-2.5 py-1 bg-[#1e2433] text-gray-200 text-[10px] border-b border-white/10 shrink-0">
              <div className="flex items-center gap-1.5 min-w-0">
                <span className="font-semibold text-indigo-400 shrink-0">[Tài liệu B]</span>
                <select
                  value={secondaryTab.key}
                  onChange={(e) => setSecondaryKey(e.target.value)}
                  className="bg-black/30 text-gray-200 border border-white/15 rounded px-1.5 py-0.5 text-[10px] truncate max-w-[160px] focus:outline-none focus:border-indigo-400"
                >
                  {openTabs
                    .filter((t) => t.key !== activeTab.key)
                    .map((t) => (
                      <option key={t.key} value={t.key} className="bg-gray-900 text-gray-100">
                        {t.filename} (Tr.{t.currentPage})
                      </option>
                    ))}
                </select>
              </div>

              <div className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => secondaryTab.currentPage > 1 && updateTabPage(secondaryTab.key, secondaryTab.currentPage - 1)}
                  disabled={secondaryTab.currentPage <= 1}
                  className="p-0.5 rounded hover:bg-white/10 disabled:opacity-30"
                  title="Trang trước (Tài liệu B)"
                >
                  <ChevronLeft size={12} />
                </button>
                <form onSubmit={handleSecondaryPageSubmit} className="flex items-center gap-1">
                  <span className="text-[10px] text-gray-400">Tr.</span>
                  <input
                    type="text"
                    value={secondaryPageInput}
                    onChange={(e) => setSecondaryPageInput(e.target.value)}
                    onBlur={() => setSecondaryPageInput(String(secondaryTab.currentPage))}
                    className="w-8 h-4 text-center text-[10px] font-mono rounded bg-black/40 border border-white/20 text-white"
                  />
                </form>
                <button
                  onClick={() =>
                    secondaryTab.currentPage < (secondaryTab.totalPages || secondaryTab.citedPage) &&
                    updateTabPage(secondaryTab.key, secondaryTab.currentPage + 1)
                  }
                  disabled={secondaryTab.currentPage >= (secondaryTab.totalPages || secondaryTab.citedPage)}
                  className="p-0.5 rounded hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed"
                  title="Trang sau (Tài liệu B)"
                >
                  <ChevronRight size={12} />
                </button>
              </div>
            </div>

            <iframe
              key={`${secondaryTab.key}-sec-page-${secondaryTab.currentPage}-${iframeKey}`}
              src={buildPdfUrl(secondaryTab)}
              title={secondaryTab.title || secondaryTab.filename}
              className="w-full flex-1 border-0"
            />
          </div>
        )}
      </div>
    </div>
  );
}
