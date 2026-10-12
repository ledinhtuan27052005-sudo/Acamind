'use client';

import React, { useState, useEffect } from 'react';
import {
  FileText, X, ExternalLink, Download, ChevronLeft, ChevronRight,
  RotateCcw, ShieldCheck, Sparkles, Highlighter, Copy, Check,
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
  onClose: () => void;
}

// Trích xuất từ khóa ngắn gọn cho browser native #search parameter (Phương pháp 1)
function extractSearchKeyword(snippet?: string): string {
  if (!snippet) return '';

  // 1. Số liệu phần trăm hoặc chỉ số thống kê đặc trưng (ví dụ: 68.9%, 82.5%, 10.0%)
  const pctMatch = snippet.match(/\b\d+(?:\.\d+)?%/);
  if (pctMatch) return pctMatch[0];

  // 2. Các thuật ngữ viết tắt chuẩn DSM/APA (CBT, SSRI, MDD, BDI-II, PHQ-9)
  const acrMatch = snippet.match(/\b(CBT|SSRI|MDD|DSM-5|BDI-II|PHQ-9|GAD-7)\b/i);
  if (acrMatch) return acrMatch[0];

  // 3. Cụm từ 1-2 từ có ý nghĩa học thuật
  const clean = snippet.replace(/[\*\[\]\(\)\"\'`:;,\.\-]/g, ' ');
  const words = clean.split(/\s+/).filter(w => w.length >= 4);
  if (words.length > 0) {
    return words.slice(0, 2).join(' ');
  }

  return '';
}

export function SideBySidePdfViewer({
  documentId,
  filename,
  title,
  initialPage,
  totalPages,
  token,
  snippet,
  onClose,
}: SideBySidePdfViewerProps) {
  const [currentPage, setCurrentPage] = useState<number>(initialPage || 1);
  const [pageInput, setPageInput] = useState<string>(String(initialPage || 1));
  const [iframeKey, setIframeKey] = useState<number>(0);
  const [highlightEnabled, setHighlightEnabled] = useState<boolean>(true);
  const [copied, setCopied] = useState<boolean>(false);
  const [groundedEvidence, setGroundedEvidence] = useState<string>('');

  // Khi citation click trang mới, update currentPage và iframe
  useEffect(() => {
    const p = Math.max(1, initialPage || 1);
    setCurrentPage(p);
    setPageInput(String(p));
    setIframeKey((k) => k + 1);
  }, [documentId, initialPage, snippet]);

  // Tự động truy vấn metadata để lấy nguyên văn bằng chứng gốc trên trang PDF
  useEffect(() => {
    if (!documentId || !snippet) {
      setGroundedEvidence('');
      return;
    }
    let isCancelled = false;
    const metaUrl = `${API_URL}/api/v1/document/${documentId}/highlight-meta?page=${currentPage}&query=${encodeURIComponent(snippet)}${token ? `&token=${encodeURIComponent(token)}` : ''}`;
    fetch(metaUrl)
      .then(res => res.json())
      .then(data => {
        if (!isCancelled && data && data.grounded_sentence) {
          setGroundedEvidence(data.grounded_sentence);
        }
      })
      .catch(() => {});
    return () => { isCancelled = true; };
  }, [documentId, currentPage, snippet, token]);

  const handlePrevPage = () => {
    if (currentPage > 1) {
      const next = currentPage - 1;
      setCurrentPage(next);
      setPageInput(String(next));
      setIframeKey((k) => k + 1);
    }
  };

  const handleNextPage = () => {
    if (!totalPages || currentPage < totalPages) {
      const next = currentPage + 1;
      setCurrentPage(next);
      setPageInput(String(next));
      setIframeKey((k) => k + 1);
    }
  };

  const handleJumpToCited = () => {
    const p = Math.max(1, initialPage || 1);
    setCurrentPage(p);
    setPageInput(String(p));
    setIframeKey((k) => k + 1);
  };

  const handlePageSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = parseInt(pageInput, 10);
    if (!isNaN(parsed) && parsed >= 1 && (!totalPages || parsed <= totalPages)) {
      setCurrentPage(parsed);
      setIframeKey((k) => k + 1);
    } else {
      setPageInput(String(currentPage));
    }
  };

  const handleCopySnippet = () => {
    const textToCopy = groundedEvidence || snippet;
    if (textToCopy) {
      navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const tokenParam = token ? `?token=${encodeURIComponent(token)}` : '';
  const rawDownloadUrl = `${API_URL}/api/v1/document/${documentId}/file${tokenParam}`;

  // HYBRID SMART-HIGHLIGHT: Phương pháp 1 (Browser #search) + Phương pháp 2 (PyMuPDF backend highlight)
  const isHighlightActive = highlightEnabled && Boolean(snippet && currentPage === initialPage);
  const endpoint = isHighlightActive ? 'highlighted-file' : 'file';
  // Ưu tiên trích xuất từ khóa từ nguyên văn câu trong PDF nếu đã định vị thành công
  const searchKeyword = extractSearchKeyword(groundedEvidence || snippet);

  // Tham số query cho backend
  let queryParams = tokenParam;
  if (isHighlightActive && snippet) {
    const prefix = token ? '&' : '?';
    queryParams += `${prefix}page=${currentPage}&highlight=${encodeURIComponent(snippet)}`;
  }

  // Tham số hash cho native browser PDF viewer
  const searchHash = isHighlightActive && searchKeyword ? `&search=${encodeURIComponent(searchKeyword)}` : '';
  const pdfUrl = `${API_URL}/api/v1/document/${documentId}/${endpoint}${queryParams}#page=${currentPage}${searchHash}&zoom=page-width`;

  return (
    <div className="flex flex-col h-full w-full bg-gray-900 border-l border-gray-200 dark:border-white/10 shadow-2xl relative z-20">
      {/* ── Control Header ── */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-100 dark:bg-[#111827] border-b border-gray-200 dark:border-white/10 text-xs shrink-0 select-none">
        {/* Document Info */}
        <div className="flex items-center gap-2 min-w-0 max-w-[40%]">
          <div className="w-7 h-7 rounded-lg bg-teal-500/10 dark:bg-teal-500/20 text-teal-600 dark:text-teal-400 flex items-center justify-center shrink-0">
            <FileText size={15} />
          </div>
          <div className="min-w-0">
            <p className="font-semibold text-gray-800 dark:text-gray-200 truncate text-[11px]" title={title || filename}>
              {title || filename}
            </p>
            <div className="flex items-center gap-1.5 text-[10px] text-gray-500 dark:text-gray-400">
              <span className="flex items-center gap-0.5 text-teal-600 dark:text-teal-400 font-medium">
                <ShieldCheck size={11} /> Đối chiếu nguồn
              </span>
              <span>•</span>
              <span className="truncate">{filename}</span>
            </div>
          </div>
        </div>

        {/* Page Navigators */}
        <div className="flex items-center gap-1.5 bg-white dark:bg-white/5 px-2 py-1 rounded-md border border-gray-200 dark:border-white/10">
          <button
            onClick={handlePrevPage}
            disabled={currentPage <= 1}
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
              onBlur={() => setPageInput(String(currentPage))}
              className="w-9 h-5 text-center text-[11px] font-mono font-semibold rounded bg-gray-50 dark:bg-black/30 border border-gray-300 dark:border-white/20 text-gray-800 dark:text-gray-200 focus:outline-none focus:border-teal-500"
            />
            {totalPages && (
              <span className="text-[11px] text-gray-500 dark:text-gray-400">/ {totalPages}</span>
            )}
          </form>

          <button
            onClick={handleNextPage}
            disabled={!!totalPages && currentPage >= totalPages}
            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed text-gray-700 dark:text-gray-300 transition-colors"
            title="Trang kế tiếp"
          >
            <ChevronRight size={14} />
          </button>

          {currentPage !== initialPage && (
            <button
              onClick={handleJumpToCited}
              className="ml-1 px-1.5 py-0.5 rounded text-[10px] bg-teal-50 dark:bg-teal-900/40 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-700/50 flex items-center gap-0.5 hover:bg-teal-100 transition-colors"
              title={`Quay về trang trích dẫn gốc (${initialPage})`}
            >
              <RotateCcw size={10} /> Trang {initialPage}
            </button>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-1">
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
            download={filename}
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

      {/* ── Hộp trích dẫn đối sánh (Citation Excerpt Box) ── */}
      {snippet && (
        <div className="px-3 py-2 bg-amber-500/10 dark:bg-amber-500/15 border-b border-amber-500/20 text-xs flex items-center justify-between gap-3 shrink-0">
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <div className="w-5 h-5 rounded-md bg-amber-500/20 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0">
              <Sparkles size={12} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-amber-800 dark:text-amber-300 text-[11px]">
                  {groundedEvidence ? `Bằng chứng gốc trong tài liệu (Trang ${currentPage})` : `Đoạn văn được trích dẫn (Trang ${currentPage})`}
                </span>
                <span className={`px-1.5 py-0.2 rounded text-[9px] font-mono font-bold ${
                  highlightEnabled ? 'bg-amber-500 text-white' : 'bg-gray-200 dark:bg-gray-800 text-gray-600'
                }`}>
                  {highlightEnabled ? (groundedEvidence ? 'ĐÃ ĐỐI CHIẾU CHUẨN XÁC' : 'ĐÃ BÔI VÀNG') : 'TẮT BÔI VÀNG'}
                </span>
                {searchKeyword && (
                  <span className="hidden sm:inline-block px-1.5 py-0.2 rounded text-[9px] font-mono bg-white dark:bg-black/30 border border-amber-300 dark:border-amber-700/50 text-gray-700 dark:text-gray-300 truncate max-w-[130px]">
                    Từ khóa: {searchKeyword}
                  </span>
                )}
              </div>
              <p className="mt-0.5 text-gray-800 dark:text-gray-200 text-xs italic leading-tight truncate" title={groundedEvidence || snippet}>
                "{groundedEvidence || snippet}"
              </p>
              {groundedEvidence && groundedEvidence !== snippet && (
                <p className="text-[10px] text-gray-500 dark:text-gray-400 truncate mt-0.5" title={`Luận điểm AI: "${snippet}"`}>
                  <span className="font-medium text-amber-700 dark:text-amber-400">Luận điểm AI:</span> "{snippet}"
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-1 shrink-0">
            <button
              onClick={() => {
                setHighlightEnabled(prev => !prev);
                setIframeKey(k => k + 1);
              }}
              className={`px-2 py-1 rounded text-[11px] font-medium flex items-center gap-1 border transition-colors ${
                highlightEnabled
                  ? 'bg-amber-500 text-white border-amber-600 shadow-xs'
                  : 'bg-white dark:bg-white/5 text-gray-600 dark:text-gray-300 border-gray-300 dark:border-white/10'
              }`}
              title="Bật/Tắt chế độ bôi vàng (Highlight)"
            >
              <Highlighter size={12} />
              <span className="hidden md:inline">{highlightEnabled ? 'Bôi vàng' : 'Bình thường'}</span>
            </button>

            <button
              onClick={handleCopySnippet}
              className="p-1 rounded text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-white hover:bg-white/40 dark:hover:bg-white/10 transition-colors"
              title="Sao chép đoạn trích dẫn"
            >
              {copied ? <Check size={13} className="text-teal-500" /> : <Copy size={13} />}
            </button>
          </div>
        </div>
      )}

      {/* ── High-Performance PDF Frame with Highlight ── */}
      <div className="flex-1 w-full h-full min-h-0 bg-[#323639] relative">
        <iframe
          key={`${documentId}-page-${currentPage}-${iframeKey}-${highlightEnabled ? 'hl' : 'raw'}`}
          src={pdfUrl}
          title={title || filename}
          className="w-full h-full border-0"
        />
      </div>
    </div>
  );
}
