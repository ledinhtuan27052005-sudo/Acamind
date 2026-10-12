'use client';

import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import {
  getDocuments, chatStream, chatGeneralStream,
  getMyPlanUsage, chatFileStream, lookupDocument,
  DocumentInfo, PlanUsage,
} from '@/lib/api';
import { useAppStore } from '@/store/useAppStore';
import Link from 'next/link';
import {
  Send, Square, Brain, Globe, Trash2, Zap,
  MessageSquare, Clock, Plus, X, User, Sparkles, Paperclip, FileText, Lock,
  Copy, Check, Download, Printer, Quote, BookOpen, ChevronRight,
} from 'lucide-react';
import { SideBySidePdfViewer } from '@/components/ui/SideBySidePdfViewer';
import { AuthRequiredModal, AuthRequiredBanner } from '@/components/auth/AuthRequiredModal';
import { KatexMath } from '@/components/ui/KatexMath';
import { FigureViewer } from '@/components/ui/FigureViewer';
import { MermaidRenderer } from '@/components/ui/MermaidRenderer';

import { useI18n } from '@/lib/i18n/context';

interface ChatSession {
  id: string;
  title: string;
  createdAt: Date;
  messages: ChatMessage[];
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  attachments?: ChatFile[];
}

interface ChatFile {
  name: string;
  type: string;
  url: string;
  size?: number;
}

/* ── Chat Session Sidebar ─────────────────────────────────────────────── */

function ChatSidebar({
  sessions,
  currentSession,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  userName,
  onOpenAuth,
}: {
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string) => void;
  userName: string;
  onOpenAuth?: () => void;
}) {
  const { t } = useI18n();

  return (
    <aside className="w-20 md:w-64 h-full bg-white dark:bg-[#111827] flex flex-col shrink-0 border-r border-gray-200 dark:border-white/10 overflow-hidden pt-4 transition-colors">
      {/* New chat button */}
      <button
        onClick={onNewChat}
        className="flex items-center gap-2 mx-2 mt-2 px-2 md:px-3 py-2 rounded-lg border border-gray-300 dark:border-white/10 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors text-gray-800 dark:text-gray-200"
      >
        <Plus size={18} />
        <span className="hidden md:inline text-sm font-medium">{t.chat.new_chat}</span>
      </button>

      {/* Recents section */}
      <div
        className="flex-1 min-h-0 overflow-y-auto overscroll-contain mt-3 px-1 md:px-2"
        style={{ scrollbarWidth: 'thin' }}
      >
        <div className="flex items-center gap-1 px-1 md:px-2 py-2 text-[10px] md:text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">
          <Clock size={12} />
          <span className="hidden md:inline">{t.chat.recents}</span>
        </div>

        <div className="space-y-0.5">
          {sessions.map((session) => {
            const displayTitle = session.title === 'New chat' ? t.chat.new_chat : session.title;
            return (
              <div
                key={session.id}
                className={`group flex items-center gap-1 px-1 md:px-2 py-2 rounded-lg transition-colors text-sm ${
                  currentSession?.id === session.id
                    ? 'bg-gray-200 dark:bg-white/10 text-gray-900 dark:text-white'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                <button
                  onClick={() => onSelectSession(session.id)}
                  className="flex items-center gap-1.5 flex-1 min-w-0 text-left"
                >
                  <MessageSquare size={14} className="shrink-0" />
                  <span className="truncate hidden md:inline">{displayTitle}</span>
                  <span className="truncate md:hidden">{displayTitle.slice(0, 8)}...</span>
                </button>
                <button
                  onClick={() => onDeleteSession(session.id)}
                  className="opacity-0 group-hover:opacity-100 shrink-0 text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-all p-1"
                  title={t.common.delete}
                >
                  <Trash2 size={12} />
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* User block */}
      <div className="shrink-0 border-t border-gray-200 dark:border-white/10">
        <div className="flex items-center gap-1 px-1 md:px-2 py-2 text-[10px] md:text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">
          <User size={12} />
          <span className="hidden md:inline">{t.chat.user}</span>
        </div>
        <div className="px-1 md:px-2 pb-3">
          {userName === 'Guest' ? (
            <button
              onClick={onOpenAuth}
              className="w-full flex items-center justify-between gap-1.5 px-2 md:px-2.5 py-2 rounded-lg border border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/20 text-amber-700 dark:text-amber-300 transition-colors"
              title="Đăng nhập tài khoản"
            >
              <div className="flex items-center gap-1.5 min-w-0">
                <div className="w-5 h-5 rounded-full bg-amber-500 flex items-center justify-center shrink-0 text-white shadow-xs">
                  <Lock size={11} />
                </div>
                <span className="hidden md:inline text-xs font-semibold truncate">
                  Khách
                </span>
              </div>
              <span className="hidden md:inline text-[10px] font-bold bg-amber-500 hover:bg-amber-600 text-white px-1.5 py-0.5 rounded shadow-xs transition-colors">
                Đăng nhập
              </span>
            </button>
          ) : (
            <button
              className="w-full flex items-center gap-2 px-2 md:px-3 py-2 rounded-lg border border-gray-200 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
              title="Account"
            >
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-teal-500 to-purple-600 flex items-center justify-center shrink-0">
                <User size={12} className="text-white" />
              </div>
              <span className="hidden md:inline text-xs text-gray-700 dark:text-gray-300 truncate">
                {userName}
              </span>
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}

/* ── Word / PDF Export & Printing Utilities ──────────────────────── */

function convertMarkdownToWordHtml(content: string): string {
  if (!content) return '';
  const lines = content.split('\n');
  const out: string[] = [];
  let inList = false;
  let listType: 'ul' | 'ol' = 'ul';
  let inTable = false;

  const closeList = () => {
    if (inList) {
      out.push(listType === 'ul' ? '</ul>' : '</ol>');
      inList = false;
    }
  };

  const closeTable = () => {
    if (inTable) {
      out.push('</tbody></table>');
      inTable = false;
    }
  };

  const formatInline = (text: string) => {
    return text
      .replace(/\*\*([^\*]+?)\*\*/g, '<b>$1</b>')
      .replace(/(?:\*([^\*\n]+?)\*|_([^\_\n]+?)_)/g, '<i>$1</i>')
      .replace(/\[([^\]]+?)\s*-\s*(?:Page|Trang)\s*(\d+)\]/gi, '<span class="citation">[$1, tr. $2]</span>')
      .replace(/\$([^\$\n]+?)\$/g, '<code>$1</code>');
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Table
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      closeList();
      if (/^\|[\s\-:|]+\|$/.test(trimmed)) {
        continue;
      }
      const cells = trimmed
        .split('|')
        .filter((_, idx, arr) => idx > 0 && idx < arr.length - 1)
        .map(c => c.trim());
      if (!inTable) {
        inTable = true;
        out.push('<table style="border-collapse:collapse; width:100%; margin:14pt 0;"><thead><tr style="border-top:2pt solid #0f172a; border-bottom:1pt solid #0f172a; background-color:#f1f5f9;">');
        cells.forEach(c => out.push(`<th style="padding:6pt 8pt; text-align:left; font-weight:bold;">${formatInline(c)}</th>`));
        out.push('</tr></thead><tbody>');
      } else {
        out.push('<tr style="border-bottom:0.5pt solid #cbd5e1;">');
        cells.forEach(c => out.push(`<td style="padding:5pt 8pt;">${formatInline(c)}</td>`));
        out.push('</tr>');
      }
      continue;
    } else {
      closeTable();
    }

    if (!trimmed) {
      closeList();
      continue;
    }

    // Divider
    if (/^(\-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      closeList();
      out.push('<hr style="border:none; border-top:1pt solid #cbd5e1; margin:14pt 0;"/>');
      continue;
    }

    // Heading
    const hMatch = trimmed.match(/^(#{1,6})\s+(.*)$/);
    if (hMatch) {
      closeList();
      const level = Math.min(3, hMatch[1].length);
      out.push(`<h${level}>${formatInline(hMatch[2])}</h${level}>`);
      continue;
    }

    // Blockquote
    if (trimmed.startsWith('>')) {
      closeList();
      out.push(`<blockquote style="border-left:3.5pt solid #0d9488; margin:10pt 0; padding:8pt 12pt; background-color:#f0fdfa; font-style:italic; color:#134e4a;">${formatInline(trimmed.replace(/^>\s*/, ''))}</blockquote>`);
      continue;
    }

    // Numbered item
    const numMatch = trimmed.match(/^(\d+[\.\)]|[a-zA-Z]\))\s+(.*)$/);
    if (numMatch) {
      if (!inList || listType !== 'ol') {
        closeList();
        inList = true;
        listType = 'ol';
        out.push('<ol>');
      }
      out.push(`<li>${formatInline(numMatch[2])}</li>`);
      continue;
    }

    // Bullet item
    const bulletMatch = trimmed.match(/^[-*•—–▪✦✓]\s+(.*)$/);
    if (bulletMatch) {
      if (!inList || listType !== 'ul') {
        closeList();
        inList = true;
        listType = 'ul';
        out.push('<ul>');
      }
      out.push(`<li>${formatInline(bulletMatch[1])}</li>`);
      continue;
    }

    // Regular paragraph
    closeList();
    out.push(`<p>${formatInline(trimmed)}</p>`);
  }

  closeList();
  closeTable();

  return out.join('\n');
}

function exportToWord(content: string, title: string = 'Bao_Cao_Trich_Xuat_Acamind') {
  const htmlBody = convertMarkdownToWordHtml(content);
  const fullHtml = `<!DOCTYPE html>
<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
<head>
  <meta charset='utf-8'>
  <title>${title}</title>
  <style>
    @page { size: A4; margin: 25mm 20mm; }
    body { font-family: 'Calibri', 'Segoe UI', Arial, sans-serif; font-size: 11pt; line-height: 1.6; color: #1e293b; background-color: #ffffff; }
    h1 { font-size: 18pt; font-weight: bold; color: #0f766e; border-bottom: 2pt solid #0f766e; padding-bottom: 6pt; margin-top: 18pt; margin-bottom: 10pt; }
    h2 { font-size: 13pt; font-weight: bold; color: #0f172a; border-bottom: 1pt solid #cbd5e1; padding-bottom: 4pt; margin-top: 14pt; margin-bottom: 8pt; }
    h3 { font-size: 11.5pt; font-weight: bold; color: #334155; margin-top: 10pt; margin-bottom: 4pt; }
    p { margin-top: 4pt; margin-bottom: 8pt; text-align: justify; }
    ul, ol { margin-top: 4pt; margin-bottom: 8pt; padding-left: 20pt; }
    li { margin-bottom: 4pt; }
    blockquote { border-left: 3.5pt solid #0d9488; margin: 10pt 0; padding: 8pt 12pt; background-color: #f0fdfa; font-style: italic; color: #134e4a; }
    table { border-collapse: collapse; width: 100%; margin: 14pt 0; font-size: 10pt; }
    th { border-top: 2pt solid #0f172a; border-bottom: 1pt solid #0f172a; padding: 6pt 8pt; background-color: #f1f5f9; font-weight: bold; text-align: left; }
    td { border-bottom: 0.5pt solid #cbd5e1; padding: 5pt 8pt; }
    .citation { color: #0d9488; font-weight: 600; font-size: 9.5pt; background-color: #f0fdfa; border: 0.5pt solid #99f6e4; padding: 2pt 4pt; border-radius: 3pt; }
    .doc-header { text-align: center; border-bottom: 1.5pt solid #94a3b8; padding-bottom: 10pt; margin-bottom: 20pt; }
    .doc-header h2 { border: none; margin: 0 0 4pt 0; color: #0f766e; font-size: 16pt; }
    .doc-header p { font-size: 9pt; color: #64748b; margin: 2pt 0; text-align: center; }
  </style>
</head>
<body>
  <div class="doc-header">
    <h2>ACAMIND — BÁO CÁO TRÍCH XUẤT & PHÂN TÍCH HỌC THUẬT</h2>
    <p>Trợ lý Nghiên cứu & Học tập AI • Trích xuất đối chiếu tài liệu y khoa & tâm lý học</p>
    <p>Ngày tạo: ${new Date().toLocaleDateString('vi-VN')} • Định dạng văn bản: Microsoft Word Document</p>
  </div>
  <div>
    ${htmlBody}
  </div>
</body>
</html>`;

  const blob = new Blob(['\ufeff' + fullHtml], { type: 'application/msword;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${title}.doc`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function printDocument(content: string, title: string = 'Bao_Cao_Trich_Xuat_Acamind') {
  const htmlBody = convertMarkdownToWordHtml(content);
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    window.print();
    return;
  }
  printWindow.document.write(`<!DOCTYPE html>
<html>
<head>
  <meta charset='utf-8'>
  <title>${title}</title>
  <style>
    @page { size: A4; margin: 20mm; }
    body { font-family: 'Times New Roman', 'Georgia', serif; font-size: 12pt; line-height: 1.6; color: #111; margin: 0; padding: 20px; }
    h1, h2, h3 { font-family: Arial, sans-serif; color: #111; }
    h1 { font-size: 18pt; border-bottom: 2pt solid #111; padding-bottom: 6px; margin-top: 20px; }
    h2 { font-size: 14pt; border-bottom: 1.5pt solid #333; padding-bottom: 4px; margin-top: 18px; }
    h3 { font-size: 12pt; margin-top: 14px; }
    p { margin-bottom: 10px; text-align: justify; }
    ul, ol { margin: 8px 0; padding-left: 24px; }
    li { margin-bottom: 4px; }
    table { border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 11pt; }
    th { border-top: 2pt solid #111; border-bottom: 1pt solid #111; padding: 6px 8px; text-align: left; }
    td { border-bottom: 0.5pt solid #ccc; padding: 6px 8px; }
    blockquote { border-left: 3.5pt solid #0d9488; margin: 12px 0; padding: 8px 14px; font-style: italic; background: #f0fdfa; color: #134e4a; }
    .citation { font-size: 10pt; font-weight: bold; color: #0d9488; }
    .header { text-align: center; border-bottom: 2pt solid #111; padding-bottom: 12px; margin-bottom: 22px; }
  </style>
</head>
<body>
  <div class="header">
    <h2 style="border:none; margin:0 0 6px 0;">ACAMIND — BÁO CÁO TRÍCH XUẤT & PHÂN TÍCH HỌC THUẬT</h2>
    <p style="font-size:10pt; color:#555; margin:2px 0; text-align:center;">Trợ lý Nghiên cứu & Học tập AI • Định dạng Văn bản In ấn / PDF</p>
  </div>
  <div>
    ${htmlBody}
  </div>
  <script>
    window.onload = function() {
      setTimeout(function() {
        window.print();
      }, 300);
    }
  </script>
</body>
</html>`);
  printWindow.document.close();
}

/* ── Structured Message Component ─────────────────────────────────── */

interface TableCell {
  content: string;
  isBold?: boolean;
}

interface TableRow {
  cells: TableCell[];
}

interface StructuredItem {
  type:
    | 'text'
    | 'table'
    | 'heading'
    | 'bullet'
    | 'numbered'
    | 'blockquote'
    | 'divider'
    | 'figure'
    | 'mermaid'
    | 'math_block'
    | 'code';
  content?: string;
  level?: number;
  numberPrefix?: string;
  bulletGlyph?: string;
  rows?: TableRow[];
  headerRow?: TableRow;
  src?: string;
  caption?: string;
  docFilename?: string;
  pageNumber?: number;
  language?: string;
}

// Parse một dòng table thành các cells
function parseTableRow(line: string): TableCell[] {
  const cells = line
    .split('|')
    .filter((_, i, arr) => i > 0 && i < arr.length - 1)
    .map(cell => {
      const trimmed = cell.trim();
      const boldMatch = trimmed.match(/^\*\*(.+)\*\*$/);
      return {
        content: boldMatch ? boldMatch[1] : trimmed,
        isBold: !!boldMatch,
      };
    });
  return cells;
}

// Kiểm tra xem dòng có phải là table row không
function isTableRow(line: string): boolean {
  const trimmed = line.trim();
  return trimmed.startsWith('|') && trimmed.endsWith('|') && trimmed.includes('|');
}

// Kiểm tra xem dòng có phải là separator row (|---|---|) không
function isTableSeparator(line: string): boolean {
  const trimmed = line.trim();
  return /^\|[\s\-:|]+\|$/.test(trimmed);
}

// Trích xuất metadata sơ đồ / hình ảnh từ cú pháp markdown: ![caption](url) [file.pdf - Page X]
function extractFigureInfo(line: string): {
  src: string;
  caption: string;
  docFilename?: string;
  pageNumber?: number;
} | null {
  const match = line.match(/!\[([^\]]*)\]\(([^)]+)\)(?:\s*\[([^\]]+)\])?/);
  if (!match) return null;

  const caption = match[1].trim();
  const src = match[2].trim();
  const citePart = match[3]?.trim();

  let docFilename: string | undefined;
  let pageNumber: number | undefined;

  // 1. Trích xuất từ citation đi kèm [file.pdf - Page 2]
  if (citePart) {
    const pageMatch = citePart.match(/([^-\n]+?)\s*-\s*(?:Page|Trang)\s*(\d+)/i);
    if (pageMatch) {
      docFilename = pageMatch[1].trim();
      pageNumber = parseInt(pageMatch[2], 10);
    }
  }

  // 2. Trích xuất từ đường dẫn URL (ví dụ: .../p2_figure_0.png)
  if (!pageNumber) {
    const pMatch = src.match(/[\/_]p(\d+)_[a-zA-Z0-9_]+\.png/i);
    if (pMatch) {
      pageNumber = parseInt(pMatch[1], 10);
    }
  }

  // 3. Trích xuất từ caption nếu có "Trang X" hoặc "Page X"
  if (!pageNumber && caption) {
    const capMatch = caption.match(/(?:Trang|Page)\s*(\d+)/i);
    if (capMatch) {
      pageNumber = parseInt(capMatch[1], 10);
    }
  }

  return { src, caption, docFilename, pageNumber };
}

// Parse nội dung - xử lý headings, bullets, numbered lists, blockquotes, tables, diagrams/figures, mermaid, math formulas và text
function parseToStructured(content: string): StructuredItem[] {
  const lines = content.split('\n');
  const result: StructuredItem[] = [];
  let pendingTableRows: string[] = [];

  let inCodeBlock = false;
  let codeBlockLang = '';
  let codeBlockLines: string[] = [];

  let inMathBlock = false;
  let mathLines: string[] = [];

  const flushTable = (rows: string[]) => {
    if (rows.length < 2) return null;
    const headerCells = parseTableRow(rows[0]);
    const dataRows: TableRow[] = [];
    for (let i = 2; i < rows.length; i++) {
      if (!isTableSeparator(rows[i])) {
        dataRows.push({ cells: parseTableRow(rows[i]) });
      }
    }
    return {
      type: 'table' as const,
      headerRow: { cells: headerCells },
      rows: dataRows,
    } as StructuredItem;
  };

  const flushPendingTable = () => {
    if (pendingTableRows.length > 0) {
      const table = flushTable(pendingTableRows);
      if (table) result.push(table);
      pendingTableRows = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // 1. Xử lý Code Block & Mermaid Block
    if (trimmed.startsWith('```')) {
      flushPendingTable();
      if (!inCodeBlock) {
        inCodeBlock = true;
        codeBlockLang = trimmed.slice(3).trim().toLowerCase();
        codeBlockLines = [];
      } else {
        inCodeBlock = false;
        if (codeBlockLang === 'mermaid') {
          result.push({
            type: 'mermaid',
            content: codeBlockLines.join('\n').trim(),
          });
        } else {
          result.push({
            type: 'code',
            language: codeBlockLang,
            content: codeBlockLines.join('\n'),
          });
        }
        codeBlockLang = '';
        codeBlockLines = [];
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockLines.push(line);
      continue;
    }

    // 2. Xử lý Math Block $$
    if (trimmed.startsWith('$$') && trimmed.endsWith('$$') && trimmed.length > 2) {
      flushPendingTable();
      const mathContent = trimmed.slice(2, -2).trim();
      if (mathContent) {
        result.push({
          type: 'math_block',
          content: mathContent,
        });
      }
      continue;
    }

    if (!inMathBlock && trimmed.startsWith('$$')) {
      flushPendingTable();
      inMathBlock = true;
      const initial = trimmed.slice(2).trim();
      mathLines = initial ? [initial] : [];
      continue;
    }

    if (inMathBlock) {
      if (trimmed.endsWith('$$')) {
        const lastPart = trimmed.slice(0, -2).trim();
        if (lastPart) mathLines.push(lastPart);
        inMathBlock = false;
        result.push({
          type: 'math_block',
          content: mathLines.join('\n'),
        });
        mathLines = [];
      } else {
        mathLines.push(line);
      }
      continue;
    }

    // 3. Xử lý Table
    if (isTableRow(trimmed)) {
      pendingTableRows.push(trimmed);
      continue;
    } else {
      flushPendingTable();
    }

    if (!trimmed) continue;

    // 4. Xử lý Figure / Image ![caption](url)
    const figInfo = extractFigureInfo(trimmed);
    if (figInfo) {
      result.push({
        type: 'figure',
        src: figInfo.src,
        caption: figInfo.caption,
        docFilename: figInfo.docFilename,
        pageNumber: figInfo.pageNumber,
      });
      continue;
    }

    // 5. Divider (---, ***, ___)
    if (/^(\-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      result.push({ type: 'divider' });
      continue;
    }

    // 6. Blockquote (> Quote) - Khối trích lục từ tài liệu gốc
    if (trimmed.startsWith('>')) {
      const quoteContent = trimmed.replace(/^>\s*/, '');
      result.push({
        type: 'blockquote',
        content: quoteContent,
      });
      continue;
    }

    // 7. Heading (#, ##, ###)
    const headingMatch = trimmed.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      result.push({
        type: 'heading',
        level: headingMatch[1].length,
        content: headingMatch[2],
      });
      continue;
    }

    // 8. Numbered item (1. item, 2. item, a) item, I. item)
    const numberedMatch = trimmed.match(/^(\d+[\.\)]|[a-zA-Z]\)|[ivxIVX]+[\.\)])\s+(.*)$/);
    if (numberedMatch) {
      result.push({
        type: 'numbered',
        numberPrefix: numberedMatch[1],
        content: numberedMatch[2],
      });
      continue;
    }

    // 9. Bullet point (- item, * item, • item, — item, ▪ item)
    const bulletMatch = trimmed.match(/^[-*•—–▪✦✓]\s+(.*)$/);
    if (bulletMatch) {
      result.push({
        type: 'bullet',
        bulletGlyph: bulletMatch[0][0],
        content: bulletMatch[1],
      });
      continue;
    }

    // 10. Dòng text thông thường
    result.push({
      type: 'text',
      content: trimmed,
    });
  }

  // Flush table cuối cùng nếu còn
  flushPendingTable();

  // If still in code block at EOF
  if (inCodeBlock && codeBlockLines.length > 0) {
    if (codeBlockLang === 'mermaid') {
      result.push({ type: 'mermaid', content: codeBlockLines.join('\n').trim() });
    } else {
      result.push({ type: 'code', language: codeBlockLang, content: codeBlockLines.join('\n') });
    }
  }

  // If still in math block at EOF
  if (inMathBlock && mathLines.length > 0) {
    result.push({ type: 'math_block', content: mathLines.join('\n') });
  }

  return result;
}

// Parse bold text helper
function parseBoldText(text: string): { bold: boolean; text: string }[] {
  const parts: { bold: boolean; text: string }[] = [];
  const regex = /\*\*(.+?)\*\*/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ bold: false, text: text.slice(lastIndex, match.index) });
    }
    parts.push({ bold: true, text: match[1] });
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push({ bold: false, text: text.slice(lastIndex) });
  }

  return parts;
}

// Parse italic text helper (*italic* or _italic_)
function parseItalicText(text: string): { italic: boolean; text: string }[] {
  const parts: { italic: boolean; text: string }[] = [];
  const regex = /(?:\*([^\*\n]+?)\*|_([^\_\n]+?)_)/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ italic: false, text: text.slice(lastIndex, match.index) });
    }
    parts.push({ italic: true, text: match[1] || match[2] });
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push({ italic: false, text: text.slice(lastIndex) });
  }

  return parts;
}

// Parse inline math helper ($...$)
function parseInlineMath(text: string): { isMath: boolean; content: string }[] {
  const parts: { isMath: boolean; content: string }[] = [];
  const regex = /\$([^\$\n]+?)\$/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ isMath: false, content: text.slice(lastIndex, match.index) });
    }
    parts.push({ isMath: true, content: match[1] });
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push({ isMath: false, content: text.slice(lastIndex) });
  }

  return parts;
}

// Render rich text: hỗ trợ KaTeX $formula$, **bold**, *italic*, citation [file.pdf - Page X] clickable, [Source: URL]
function renderRichText({
  text,
  className,
  onCitationClick,
}: {
  text?: string;
  className?: string;
  onCitationClick?: (filename: string, page: number, snippet?: string) => void;
}) {
  if (!text) return null;

  const bracketRegex = /\[([^\]]+)\]/g;
  const elements: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  // Render inline math inside text
  const renderMathSpan = (raw: string, pfx: string) => {
    const mathParts = parseInlineMath(raw);
    return mathParts.map((m, mIdx) =>
      m.isMath ? (
        <KatexMath key={`${pfx}-math-${mIdx}`} math={m.content} block={false} />
      ) : (
        <span key={`${pfx}-txt-${mIdx}`}>{m.content}</span>
      )
    );
  };

  // Render italic inside non-bold or bold segments
  const renderItalicSpan = (plainStr: string, keyPrefix: string) => {
    const italicParts = parseItalicText(plainStr);
    return italicParts.map((ip, ipIdx) =>
      ip.italic ? (
        <em key={`${keyPrefix}-it-${ipIdx}`} className="italic text-slate-800 dark:text-slate-200">
          {renderMathSpan(ip.text, `${keyPrefix}-it-m-${ipIdx}`)}
        </em>
      ) : (
        <span key={`${keyPrefix}-it-s-${ipIdx}`}>
          {renderMathSpan(ip.text, `${keyPrefix}-s-${ipIdx}`)}
        </span>
      )
    );
  };

  const renderBoldSpan = (plainStr: string, keyPrefix: string) => {
    const boldParts = parseBoldText(plainStr);
    return boldParts.map((p, pIdx) =>
      p.bold ? (
        <strong key={`${keyPrefix}-${pIdx}`} className="font-bold text-slate-900 dark:text-white">
          {renderItalicSpan(p.text, `${keyPrefix}-b-${pIdx}`)}
        </strong>
      ) : (
        <span key={`${keyPrefix}-${pIdx}`}>
          {renderItalicSpan(p.text, `${keyPrefix}-nb-${pIdx}`)}
        </span>
      )
    );
  };

  while ((match = bracketRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      const before = text.slice(lastIndex, match.index);
      elements.push(renderBoldSpan(before, `before-${lastIndex}`));
    }

    const bracketInner = match[1].trim();

    // 1. Web Source: [Source: https://...] hoặc [https://...]
    const webMatch = bracketInner.match(/^(?:Source:\s*)?(https?:\/\/[^\s\]]+)/i);
    if (webMatch) {
      const url = webMatch[1];
      let displayHost = url;
      try {
        displayHost = new URL(url).hostname.replace(/^www\./, '');
      } catch {}
      elements.push(
        <a
          key={`web-${match.index}`}
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 px-1.5 py-0.5 mx-1 my-0.5 rounded text-[11px] font-medium bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/60 dark:hover:bg-blue-900/80 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-700/60 transition-all hover:scale-105 active:scale-95 shadow-2xs"
          title={`Mở nguồn web: ${url}`}
        >
          <Globe size={11} className="shrink-0" />
          <span className="truncate max-w-[130px]">{displayHost}</span>
        </a>
      );
      lastIndex = bracketRegex.lastIndex;
      continue;
    }

    // 2. Academic Citation: [filename.pdf - Page 3] hoặc [file1.pdf - Page 2; file2.pdf - Trang 5]
    if (/(?:Page|Trang)\s*\d+/i.test(bracketInner)) {
      const subItems = bracketInner.split(';');
      const citationButtons: React.ReactNode[] = [];

      // Trích xuất câu hoặc đoạn văn ngữ cảnh làm snippet đối chứng
      let contextSnippet = '';
      const textBefore = text.slice(0, match.index).trim();
      if (textBefore) {
        const cleanBefore = textBefore.replace(/\[[^\]]+\]/g, '').replace(/[\*\_]/g, '').trim();
        const sentences = cleanBefore.split(/(?<=[.!?\n])\s+/);
        contextSnippet = sentences[sentences.length - 1] || cleanBefore;
        if (contextSnippet.length > 220) {
          contextSnippet = contextSnippet.slice(-220).trim();
        }
      }
      if (!contextSnippet) {
        contextSnippet = text.replace(/\[[^\]]+\]/g, '').replace(/[\*\_]/g, '').trim().slice(0, 180);
      }

      subItems.forEach((sub, subIdx) => {
        const pageMatch = sub.match(/([^-\n]+?)\s*-\s*(?:Page|Trang)\s*(\d+)/i);
        if (pageMatch) {
          const rawFilename = pageMatch[1].trim();
          const pageNum = parseInt(pageMatch[2], 10);
          const shortName = rawFilename.length > 22 ? rawFilename.slice(0, 19) + '…' : rawFilename;

          citationButtons.push(
            <button
              key={`cite-${match!.index}-${subIdx}`}
              type="button"
              onClick={() => onCitationClick?.(rawFilename, pageNum, contextSnippet)}
              className="inline-flex items-center gap-1.5 px-2 py-0.5 mx-1 my-0.5 rounded-md text-[11.5px] font-medium bg-slate-100 hover:bg-teal-50 dark:bg-slate-800/90 dark:hover:bg-teal-950/70 text-slate-700 hover:text-teal-700 dark:text-slate-200 dark:hover:text-teal-300 border border-slate-300/80 hover:border-teal-400 dark:border-slate-700 dark:hover:border-teal-600 transition-all hover:scale-105 active:scale-95 group shadow-2xs cursor-pointer select-none"
              title={`Nhấn để mở đối chiếu "${rawFilename}" tại trang ${pageNum} bên cạnh (Tự động bôi vàng đoạn trích)`}
            >
              <FileText size={11} className="text-teal-600 dark:text-teal-400 shrink-0 group-hover:rotate-6 transition-transform" />
              <span className="font-semibold truncate max-w-[140px]">{shortName}</span>
              <span className="bg-slate-200/90 dark:bg-slate-700/90 group-hover:bg-teal-200/70 dark:group-hover:bg-teal-800/70 px-1.5 py-0.2 rounded text-[10px] font-mono font-bold text-slate-800 dark:text-slate-200 group-hover:text-teal-900 dark:group-hover:text-teal-200 transition-colors">
                Trang {pageNum}
              </span>
            </button>
          );
        }
      });

      if (citationButtons.length > 0) {
        elements.push(
          <span key={`cite-group-${match.index}`} className="inline-flex flex-wrap items-center">
            {citationButtons}
          </span>
        );
        lastIndex = bracketRegex.lastIndex;
        continue;
      }
    }

    // 3. Fallback bracket thường
    elements.push(
      <span key={`bracket-${match.index}`}>
        [{renderBoldSpan(bracketInner, `inner-${match.index}`)}]
      </span>
    );
    lastIndex = bracketRegex.lastIndex;
  }

  if (lastIndex < text.length) {
    const after = text.slice(lastIndex);
    elements.push(renderBoldSpan(after, `after-${lastIndex}`));
  }

  return <span className={className}>{elements}</span>;
}

function StructuredMessage({
  content,
  onCitationClick,
}: {
  content: string;
  onCitationClick?: (filename: string, page: number, snippet?: string) => void;
}) {
  const structured = parseToStructured(content);

  return (
    <div className="structured-content text-[13.5px] leading-relaxed text-slate-800 dark:text-slate-200 space-y-2.5">
      {structured.map((item, idx) => (
        <div key={idx}>
          {/* Heading */}
          {item.type === 'heading' && (
            /^(?:References|Tài liệu tham khảo)$/i.test((item.content || '').trim()) ? (
              <div className="mt-6 pt-4 border-t-2 border-slate-300 dark:border-slate-700/80 mb-3">
                <div className="flex items-center gap-2">
                  <BookOpen size={16} className="text-teal-600 dark:text-teal-400 shrink-0" />
                  <h3 className="font-bold text-sm tracking-wider uppercase text-slate-900 dark:text-slate-100">
                    {item.content}
                  </h3>
                </div>
              </div>
            ) : item.level && item.level <= 2 ? (
              <div className="mt-5 mb-2.5 pb-1.5 border-b-2 border-slate-200 dark:border-slate-700/80">
                <h3 className="font-bold text-[15px] sm:text-[16px] text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
                  {renderRichText({ text: item.content, onCitationClick })}
                </h3>
              </div>
            ) : (
              <h4 className="font-semibold text-[13.5px] sm:text-[14px] text-slate-800 dark:text-slate-200 mt-3.5 mb-1.5 flex items-center gap-1.5">
                {renderRichText({ text: item.content, onCitationClick })}
              </h4>
            )
          )}

          {/* Numbered item (Word/PDF hanging indent) */}
          {item.type === 'numbered' && (
            <div className="flex items-start gap-2.5 my-1 text-[13.5px] leading-relaxed">
              <span className="font-bold text-slate-700 dark:text-slate-300 min-w-[20px] text-right shrink-0 select-none">
                {item.numberPrefix}
              </span>
              <div className="flex-1 min-w-0 text-slate-800 dark:text-slate-200">
                {renderRichText({ text: item.content, onCitationClick })}
              </div>
            </div>
          )}

          {/* Bullet point (Word/PDF bullet) */}
          {item.type === 'bullet' && (
            <div className="flex items-start gap-2.5 my-1 text-[13.5px] leading-relaxed">
              <span className="text-teal-600 dark:text-teal-400 font-bold shrink-0 mt-0.5 select-none text-[15px] leading-none">
                •
              </span>
              <div className="flex-1 min-w-0 text-slate-800 dark:text-slate-200">
                {renderRichText({ text: item.content, onCitationClick })}
              </div>
            </div>
          )}

          {/* Blockquote / Khối trích lục từ tài liệu gốc */}
          {item.type === 'blockquote' && item.content && (
            <div className="my-3 p-3.5 sm:p-4 rounded-r-xl border-l-[3.5px] border-teal-600 dark:border-teal-500 bg-teal-50/40 dark:bg-teal-950/20 border border-teal-200/50 dark:border-teal-800/40 shadow-2xs">
              <div className="flex items-center gap-1.5 text-[11px] font-bold text-teal-800 dark:text-teal-300 uppercase tracking-wider mb-1">
                <Quote size={13} className="shrink-0" />
                <span>Trích lục từ tài liệu gốc</span>
              </div>
              <div className="text-[13px] sm:text-[13.5px] italic text-slate-700 dark:text-slate-300 leading-relaxed">
                “{renderRichText({ text: item.content, onCitationClick })}”
              </div>
            </div>
          )}

          {/* Divider (---) */}
          {item.type === 'divider' && (
            <div className="my-5 flex items-center gap-3">
              <div className="flex-1 border-t border-slate-200 dark:border-slate-800"></div>
              <span className="text-[11px] uppercase font-bold tracking-widest text-slate-400 dark:text-slate-500 select-none">
                • § •
              </span>
              <div className="flex-1 border-t border-slate-200 dark:border-slate-800"></div>
            </div>
          )}

          {/* Math Block $$...$$ */}
          {item.type === 'math_block' && item.content && (
            <KatexMath math={item.content} block={true} />
          )}

          {/* Mermaid Flowchart Block */}
          {item.type === 'mermaid' && item.content && (
            <MermaidRenderer chart={item.content} />
          )}

          {/* Figure / Diagram Card */}
          {item.type === 'figure' && item.src && (
            <FigureViewer
              src={item.src}
              caption={item.caption}
              docFilename={item.docFilename}
              pageNumber={item.pageNumber}
              onCitationClick={onCitationClick}
            />
          )}

          {/* Code Block */}
          {item.type === 'code' && item.content && (
            <pre className="my-2.5 p-3 rounded-lg bg-gray-900 text-gray-100 font-mono text-xs overflow-x-auto border border-gray-800 shadow-xs">
              <code>{item.content}</code>
            </pre>
          )}

          {/* Table block (APA / Word publication table) */}
          {item.type === 'table' && item.headerRow && (
            <div className="overflow-x-auto my-4 rounded-lg shadow-2xs border-t-2 border-b-2 border-slate-800 dark:border-slate-200">
              <table className="w-full text-[13px] border-collapse">
                <thead>
                  <tr className="bg-slate-100/80 dark:bg-slate-800/80 border-b border-slate-800 dark:border-slate-200">
                    {item.headerRow.cells.map((cell, cIdx) => (
                      <th
                        key={cIdx}
                        className="px-3.5 py-2.5 text-left font-bold uppercase tracking-wider text-[11.5px] text-slate-900 dark:text-slate-100"
                      >
                        {renderRichText({ text: cell.content, onCitationClick })}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                  {item.rows?.map((row, rIdx) => (
                    <tr
                      key={rIdx}
                      className="hover:bg-teal-50/30 dark:hover:bg-teal-950/20 transition-colors odd:bg-transparent even:bg-slate-50/50 dark:even:bg-white/[0.02]"
                    >
                      {row.cells.map((cell, cIdx) => (
                        <td
                          key={cIdx}
                          className="px-3.5 py-2 text-slate-800 dark:text-slate-200"
                        >
                          {renderRichText({ text: cell.content, onCitationClick })}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Regular text */}
          {item.type === 'text' && (
            <p className="text-[13.5px] text-slate-800 dark:text-slate-200 leading-relaxed my-1.5 text-justify">
              {renderRichText({ text: item.content, onCitationClick })}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

/* ── AI Message Component (Word / PDF Document Paper Sheet) ────────── */

function AiMessage({
  content,
  query,
  documentIds,
  onCitationClick,
  onInjectPrompt,
}: {
  content: string;
  query?: string;
  documentIds?: string[];
  onCitationClick?: (filename: string, page: number, snippet?: string) => void;
  onInjectPrompt?: (promptText: string) => void;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const cleanText = content
      .replace(/^#{1,6}\s+/gm, '')
      .replace(/\*\*([^\*]+?)\*\*/g, '$1')
      .replace(/(?:\*([^\*\n]+?)\*|_([^\_\n]+?)_)/g, '$1')
      .replace(/\[([^\]]+?)\s*-\s*(?:Page|Trang)\s*(\d+)\]/gi, '[$1, tr. $2]');
    navigator.clipboard.writeText(cleanText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExportWord = () => {
    exportToWord(content, 'Bao_Cao_Trich_Xuat_Acamind');
  };

  const handlePrint = () => {
    printDocument(content, 'Bao_Cao_Trich_Xuat_Acamind');
  };

  return (
    <div className="group relative bg-white dark:bg-[#151a23] border border-slate-200/90 dark:border-slate-800 rounded-2xl shadow-[0_4px_24px_rgba(0,0,0,0.05)] dark:shadow-[0_4px_24px_rgba(0,0,0,0.35)] overflow-hidden transition-all hover:border-slate-300 dark:hover:border-slate-700">
      {/* ── Document Page Header Bar (Word / PDF Document Style) ── */}
      <div className="flex items-center justify-between px-4 sm:px-6 py-2.5 bg-gradient-to-r from-slate-50 via-slate-100/70 to-slate-50 dark:from-[#1a202c] dark:via-[#1e2634] dark:to-[#1a202c] border-b border-slate-200 dark:border-slate-800 text-xs select-none">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-6 h-6 rounded bg-teal-600/10 dark:bg-teal-400/20 text-teal-700 dark:text-teal-400 flex items-center justify-center shrink-0">
            <FileText size={14} />
          </div>
          <div className="flex items-center gap-2 min-w-0">
            <span className="font-bold text-[11px] sm:text-xs tracking-wider uppercase text-slate-800 dark:text-slate-200 truncate">
              VĂN BẢN TRÍCH XUẤT & PHÂN TÍCH
            </span>
            <span className="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800/60">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse"></span>
              Định dạng Word / PDF
            </span>
          </div>
        </div>

        {/* Toolbar actions */}
        <div className="flex items-center gap-1 sm:gap-1.5 shrink-0">
          <button
            onClick={handleCopy}
            className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition-colors shadow-2xs cursor-pointer"
            title="Sao chép toàn bộ nội dung văn bản"
          >
            {copied ? <Check size={12} className="text-emerald-500" /> : <Copy size={12} />}
            <span className="hidden md:inline">{copied ? 'Đã sao chép' : 'Sao chép'}</span>
          </button>

          <button
            onClick={handleExportWord}
            className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium bg-teal-50 hover:bg-teal-100 dark:bg-teal-950/50 dark:hover:bg-teal-900/60 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800 transition-colors shadow-2xs cursor-pointer"
            title="Tải văn bản về dưới dạng tệp Microsoft Word (.doc)"
          >
            <Download size={12} />
            <span className="hidden md:inline">Xuất Word</span>
          </button>

          <button
            onClick={handlePrint}
            className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition-colors shadow-2xs cursor-pointer"
            title="In hoặc lưu thành tệp PDF"
          >
            <Printer size={12} />
            <span className="hidden md:inline">In / PDF</span>
          </button>
        </div>
      </div>

      {/* ── Document Page Body (A4 / Document Page Content) ── */}
      <div className="px-5 py-5 sm:px-7 sm:py-6 md:px-8 md:py-7">
        <StructuredMessage content={content} onCitationClick={onCitationClick} />
      </div>


      {/* ── Document Page Footer ── */}
      <div className="px-5 sm:px-8 py-2 bg-slate-50/50 dark:bg-slate-900/40 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 select-none">
        <div className="flex items-center gap-1.5">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
          <span>Acamind Academic Assistant • Trích xuất đối chiếu từ tài liệu gốc</span>
        </div>
        <div className="hidden sm:flex items-center gap-2">
          <span>Chuẩn học thuật DSM/APA</span>
        </div>
      </div>
    </div>
  );
}

/* ── Main Chat Component ──────────────────────────────────────────── */

export default function ChatPage() {
  const { user, token, initAuth, darkMode } = useAppStore();
  const { t } = useI18n();

  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [planUsage, setPlanUsage] = useState<PlanUsage | null>(null);
  const [learningMode] = useState<'beginner' | 'advanced' | 'researcher'>('advanced');

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentDomain, setCurrentDomain] = useState<'psychology' | 'general' | null>(null);
  const [mode, setMode] = useState<'basic' | 'advanced'>('advanced');
  const [showModeMenu, setShowModeMenu] = useState(false);

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [showAuthModal, setShowAuthModal] = useState(false);

  // Phase 4: Side-by-Side PDF Viewer State & Citation Handler
  const [activePdfViewer, setActivePdfViewer] = useState<{
    documentId: string;
    filename: string;
    title?: string;
    page: number;
    totalPages?: number | null;
    snippet?: string;
  } | null>(null);

  const handleCitationClick = async (filename: string, page: number, snippet?: string) => {
    const cleanTarget = filename.replace(/\.pdf$/i, '').trim().toLowerCase();
    const matched = documents.find(d => 
      d.filename.toLowerCase() === filename.toLowerCase() ||
      d.filename.toLowerCase().includes(cleanTarget) ||
      (d.title && d.title.toLowerCase().includes(cleanTarget))
    );

    if (matched) {
      setActivePdfViewer({
        documentId: matched.id,
        filename: matched.filename,
        title: matched.title || matched.filename,
        page: page,
        totalPages: matched.total_pages,
        snippet: snippet,
      });
      return;
    }

    try {
      const lookedUp = await lookupDocument(filename);
      if (lookedUp) {
        setActivePdfViewer({
          documentId: lookedUp.id,
          filename: lookedUp.filename,
          title: lookedUp.title || lookedUp.filename,
          page: page,
          totalPages: lookedUp.total_pages,
          snippet: snippet,
        });
      }
    } catch (e) {
      console.error('Error looking up document:', e);
    }
  };

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    loadSessions();
    initAuth();
    getDocuments().then(setDocuments).catch(() => {});
  }, []);

  useEffect(() => {
    if (token) {
      getMyPlanUsage().then(setPlanUsage).catch(() => {});
      getDocuments().then(setDocuments).catch(() => {});
    }
  }, [token]);

  const loadSessions = () => {
    try {
      const saved = localStorage.getItem('chat.sessions');
      if (saved) {
        const parsed = JSON.parse(saved);
        setSessions(parsed.map((s: any) => ({
          ...s,
          createdAt: new Date(s.createdAt),
        })));
      }
    } catch {}
  };

  const saveSessions = (updater: ChatSession[] | ((prev: ChatSession[]) => ChatSession[])) => {
    setSessions(prev => {
      const next = typeof updater === 'function' ? updater(prev) : updater;
      localStorage.setItem('chat.sessions', JSON.stringify(next));
      return next;
    });
  };

  const createNewSession = () => {
    if (!user) {
      setShowAuthModal(true);
      return;
    }
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: 'New chat',
      createdAt: new Date(),
      messages: [],
    };
    saveSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
    setChatMessages([]);
    setUploadedFiles([]);
  };

  const ACCEPTED_TYPES = {
    'application/pdf': '.pdf',
    'image/jpeg': '.jpg',
    'image/png': '.jpg',
    'image/gif': '.gif',
    'image/webp': '.webp',
    'image/bmp': '.bmp',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'application/vnd.ms-excel': '.xls',
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!user) {
      setShowAuthModal(true);
      if (e.target) e.target.value = '';
      return;
    }
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    const valid = files.filter(f => f.type.startsWith('image/') || f.type === 'application/pdf' || f.name.match(/\.(pdf|docx?|xlsx?|jpg|jpeg|png|gif|webp|bmp)$/i));
    if (!valid.length) return;
    setUploadedFiles(prev => [...prev, ...valid]);
    e.target.value = '';
  };

  const removeFile = (idx: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== idx));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const deleteSession = (id: string) => {
    saveSessions(prev => prev.filter(s => s.id !== id));
    if (currentSessionId === id) {
      setCurrentSessionId(null);
      setChatMessages([]);
    }
  };

  const updateSessionMessages = (sessionId: string, messages: ChatMessage[]) => {
    saveSessions(prev =>
      prev.map(s =>
        s.id === sessionId
          ? {
              ...s,
              // Strip attachments (blob URLs) from saved messages — they won't work after reload
              messages: messages.map(m => ({ ...m, attachments: undefined })),
              title: messages.length > 0 && s.title === 'New chat'
                ? messages[0].content.slice(0, 20) + (messages[0].content.length > 20 ? '...' : '')
                : s.title,
            }
          : s
      )
    );
  };

  const selectSession = (id: string) => {
    const session = sessions.find(s => s.id === id);
    if (session) {
      setCurrentSessionId(id);
      setChatMessages(session.messages);
    }
  };

  const clearChat = () => {
    if (currentSessionId) {
      updateSessionMessages(currentSessionId, []);
    }
    setChatMessages([]);
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleSend = async () => {
    if (!user) {
      setShowAuthModal(true);
      return;
    }
    if (!input.trim() || isLoading) return;

    const rawQuery = input.trim();

    // Create session lazily on first message (when no session exists yet)
    let activeSessionId = currentSessionId;
    if (!activeSessionId) {
      const newSession: ChatSession = {
        id: Date.now().toString(),
        title: 'New chat',
        createdAt: new Date(),
        messages: [],
      };
      saveSessions(prev => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
      activeSessionId = newSession.id;
    }

    // Build attachment previews from uploaded files (object URLs for display)
    const attachments: ChatFile[] = uploadedFiles.map(file => ({
      name: file.name,
      type: file.type,
      url: URL.createObjectURL(file),
      size: file.size,
    }));

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: rawQuery,
      attachments: attachments.length > 0 ? attachments : undefined,
    };

    const updatedMessages = [...chatMessages, userMsg];
    setChatMessages(updatedMessages);
    if (activeSessionId) updateSessionMessages(activeSessionId, updatedMessages);
    setInput('');
    // Reset uploaded files immediately when sending (don't wait for API)
    setUploadedFiles([]);
    setIsLoading(true);

    // Inject mode instruction vào query gửi lên LLM (chỉ phía request, user vẫn thấy raw text).
    // 'basic' → trả lời ngắn gọn (2-4 câu), 'advanced' → trả lời đầy đủ, sâu, chi tiết.
    const isEnglish = !/[áàảãạâấầẩẫậăắằẳẵặéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđÁÀẢÃẠÂẤẦẨẪẬĂẮẰẲẴẶÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ]/i.test(rawQuery) &&
      /\b(what|is|how|to|the|in|of|and|a|an|depression|anxiety|cbt|ocd|bipolar|stress|hello|hi|who|why|where|affect|people|psychology)\b/i.test(rawQuery);

    const modeInstruction = isEnglish
      ? (mode === 'basic'
          ? '[System: Please reply concisely in about 2-4 sentences strictly answering the question. Avoid unasked topics.] '
          : '[System: Please provide a thorough, accurate response focused strictly on what is asked. Cite page numbers from documents. Strictly do not expand into unasked topics.] ')
      : (mode === 'basic'
          ? '[He thong: Hay tra loi ngan gon, suc tich trong khoang 2-4 cau, dung trong tam cau hoi. Tranh liet ke dai va khong mo rong sang chu de khac.] '
          : '[He thong: Hay tra loi day du, sau sac, dung trong tam cau hoi. Trinh bay ro rang kem trich dan so trang tu tai lieu. Tuyet doi khong mo rong lan man sang cac chu de ngoai pham vi cau hoi.] ');
    const sentQuery = modeInstruction + rawQuery;

    // Fast domain detection via keywords (no API call — instant, ~0ms).
    // LLM detect-domain chỉ chạy nền để cập nhật UI, KHÔNG block streaming.
    const FAST_KEYWORDS = [
      'psychology', 'psychiatric', 'therapist', 'therapy',
      'cognitive', 'behavioral', 'emotion',
      'stress', 'anxiety', 'depression', 'trauma',
      'psychoanalysis', 'freud', 'jung', 'attachment',
      'dsm', 'icd', 'diagnosis', 'treatment',
      'mental health', 'counseling',
      'cbt', 'dbt', 'act', 'psychotherapy',
      'personality', 'perception', 'memory',
      'neuroscience', 'brain', 'mood',
      'schizophrenia', 'bipolar', 'ocd', 'ptsd', 'adhd', 'autism',
      'self-esteem', 'motivation',
      'social psychology', 'developmental',
    ];
    const queryLower = rawQuery.toLowerCase();
    const fastDomain = FAST_KEYWORDS.some(kw => queryLower.includes(kw)) ? 'psychology' : 'general';
    setCurrentDomain(fastDomain as 'psychology' | 'general');

    const assistantMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
    };
    setChatMessages(prev => [...prev, assistantMsg]);

    abortRef.current = new AbortController();
    // Khi hỏi đáp thông thường, truyền mảng rỗng [] để backend tìm kiếm toàn cục trên toàn bộ 500+ tài liệu
    const docIds: string[] = [];
    if (documents.length <= 2) {
      getDocuments().then(setDocuments).catch(() => {});
    }
    const usePsychology = fastDomain === 'psychology';

    const onChunk = (chunk: string) => {
      setChatMessages(prev => {
        const newPrev = prev.map(m =>
          m.id === assistantMsg.id ? { ...m, content: m.content + chunk } : m
        );
        if (activeSessionId) updateSessionMessages(activeSessionId, newPrev);
        return newPrev;
      });
    };

    try {
      if (uploadedFiles.length > 0) {
        // Use file-chat endpoint when files are attached
        await chatFileStream({
          query: sentQuery,
          files: uploadedFiles,
          documentIds: docIds,
          onChunk,
          signal: abortRef.current.signal,
        });
      } else {
        await chatStream(sentQuery, docIds, onChunk, abortRef.current.signal);
      }
    } catch (err: any) {
      if (err?.name !== 'AbortError') {
        const detail = err instanceof Error && err.message ? `\n\n${err.message}` : '';
        setChatMessages(prev => {
          const newPrev: ChatMessage[] = [
            ...prev,
            { id: (Date.now() + 1).toString(), role: 'assistant', content: `${t.chat.error_occurred}${detail}` },
          ];
          if (activeSessionId) updateSessionMessages(activeSessionId, newPrev);
          return newPrev;
        });
      }
    } finally {
      setIsLoading(false);
      setUploadedFiles([]);
    }
  };

  const handleStop = () => {
    abortRef.current?.abort();
    setIsLoading(false);
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 144) + 'px';
    }
  }, [input]);

  const allDocIds = documents.filter(d => d.status === 'ready').map(d => d.id);

  const displayName =
    (user as any)?.full_name ||
    (user as any)?.fullName ||
    (user as any)?.username ||
    (user as any)?.name ||
    (user as any)?.email ||
    'Guest';

  return (
    <div className="flex w-full bg-white dark:bg-[#0A0F1A] transition-colors" style={{ height: 'calc(100vh - 56px)' }}>
      {/* ── Left Sidebar ── */}
      <ChatSidebar
        sessions={sessions}
        currentSession={sessions.find(s => s.id === currentSessionId) || null}
        onSelectSession={selectSession}
        onNewChat={createNewSession}
        onDeleteSession={deleteSession}
        userName={displayName}
        onOpenAuth={() => setShowAuthModal(true)}
      />

      {/* ── Main Chat + Side-by-Side PDF Container (Nhóm 4) ── */}
      <div className="flex-1 flex min-w-0 min-h-0 relative overflow-hidden">
        {/* Main Chat Area */}
        <main className={`flex-1 flex flex-col min-w-0 min-h-0 bg-white dark:bg-[#0A0F1A] overflow-hidden transition-all duration-300 ${activePdfViewer ? 'hidden sm:flex' : 'flex'}`}>
          {/* Messages - scrollable */}
          <div
            className="flex-1 min-h-0 overflow-y-auto overscroll-contain"
            style={{ scrollbarWidth: 'thin' }}
          >
            <div className={`mx-auto px-4 md:px-6 py-6 space-y-3 h-full transition-all ${activePdfViewer ? 'max-w-2xl' : 'max-w-3xl'}`}>
              {/* Empty state — logo + greeting when no messages */}
              {chatMessages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full min-h-[60vh] gap-3">
                  <div className="w-20 h-20 rounded-full overflow-hidden shadow-lg ring-2 ring-teal-500/30">
                    <img src="/Logo.jpeg" alt="Acamind" className="w-full h-full object-cover" />
                  </div>
                  <p className="text-base text-gray-600 dark:text-gray-300 text-center">
                    {t.chat.hello} <span className="font-semibold text-teal-600 dark:text-teal-400">{displayName === 'Guest' ? t.chat.guest : displayName}</span>!!!
                  </p>
                  {!user && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="mt-3 p-4 rounded-2xl border border-amber-500/30 bg-amber-500/10 dark:bg-amber-500/5 max-w-md text-center shadow-sm"
                    >
                      <div className="flex items-center justify-center gap-1.5 text-amber-700 dark:text-amber-400 font-semibold text-xs sm:text-sm mb-1.5">
                        <Lock size={15} />
                        <span>Chế độ Khách (Chưa đăng nhập)</span>
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-300 mb-3 leading-relaxed">
                        Bạn cần đăng nhập tài khoản để gửi tin nhắn, đính kèm tài liệu và sử dụng đầy đủ chức năng của Trợ lý học tập AI Acamind.
                      </p>
                      <button
                        onClick={() => setShowAuthModal(true)}
                        className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-teal-500 via-cortex-500 to-purple-600 hover:opacity-90 shadow-md shadow-teal-500/20 transition-all cursor-pointer"
                      >
                        Đăng nhập ngay
                      </button>
                    </motion.div>
                  )}
                </div>
              )}

              {/* Chat messages */}
              {chatMessages.map((msg, idx) => {
                const isPendingAssistant = msg.role === 'assistant' && !msg.content && isLoading && idx === chatMessages.length - 1;
                if (isPendingAssistant) return null;
                return (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="w-full"
                  >
                    {msg.role === 'assistant' ? (
                      <div className="w-full flex items-start gap-2.5 my-2.5">
                        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-teal-500 to-purple-600 flex items-center justify-center shrink-0 mt-1 shadow-xs">
                          <Brain size={14} className="text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <AiMessage
                            content={msg.content}
                            query={chatMessages.slice(0, idx).reverse().find(m => m.role === 'user')?.content || ''}
                            documentIds={allDocIds}
                            onCitationClick={handleCitationClick}
                            onInjectPrompt={(promptText) => {
                              setInput(promptText);
                              textareaRef.current?.focus();
                            }}
                          />
                        </div>

                      </div>
                    ) : (
                      <div className="flex justify-end w-full my-2">
                        <div className="max-w-[80%] rounded-2xl px-4 py-2.5 text-xs sm:text-sm leading-relaxed bg-gradient-to-br from-teal-500 to-purple-600 text-white shadow-xs">
                          {msg.content && <p className="whitespace-pre-wrap">{msg.content}</p>}
                          {msg.attachments && msg.attachments.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-2">
                              {msg.attachments.map((att, i) => (
                                <a
                                  key={i}
                                  href={att.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-white/20 hover:bg-white/30 transition-colors text-xs max-w-[180px]"
                                  title={att.name}
                                >
                                  {att.type.startsWith('image/') ? (
                                    <img src={att.url} alt={att.name} className="w-10 h-10 object-cover rounded" />
                                  ) : (
                                    <div className="w-10 h-10 flex items-center justify-center bg-white/20 rounded text-xs text-center leading-tight">
                                      {att.name.split('.').pop()?.toUpperCase()}
                                    </div>
                                  )}
                                  <span className="truncate">{att.name}</span>
                                </a>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </motion.div>
                );
              })}

            {/* Typing indicator — only shown while waiting, replaces the empty assistant bubble */}
            {isLoading && chatMessages[chatMessages.length - 1]?.content === '' && (
              <motion.div
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-1.5"
              >
                <div className="w-5 h-5 rounded-full bg-gradient-to-br from-teal-500 to-purple-600 flex items-center justify-center shrink-0 mt-0.5">
                  <Brain size={8} className="text-white" />
                </div>
                <div className="bg-gray-100 dark:bg-white/10 rounded-xl px-3 py-2 flex gap-1">
                  {[0, 1, 2].map(i => (
                    <div
                      key={i}
                      className="w-1 h-1 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="shrink-0 px-4 py-4 border-t border-gray-200 dark:border-white/10 bg-white dark:bg-[#0A0F1A] transition-colors">
          <div className="max-w-3xl mx-auto space-y-2">
            {!user ? (
              <AuthRequiredBanner
                message="Vui lòng đăng nhập để gửi tin nhắn, tải file đối chiếu và khai thác tài liệu cùng AI"
              />
            ) : (
              <>
                {/* File preview chips */}
                {uploadedFiles.length > 0 && (
                  <div className="flex flex-wrap gap-2 px-1">
                    {uploadedFiles.map((file, idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-1.5 pl-2 pr-1 py-1 rounded-full bg-teal-50 dark:bg-teal-900/20 border border-teal-200 dark:border-teal-700/30 text-xs text-teal-700 dark:text-teal-300 max-w-[200px]"
                      >
                        <Paperclip size={10} className="shrink-0" />
                        <span className="truncate">{file.name}</span>
                        <button
                          onClick={() => removeFile(idx)}
                          className="shrink-0 hover:text-red-500 dark:hover:text-red-400 ml-1"
                        >
                          <X size={10} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                <div className="flex gap-2 items-center bg-white dark:bg-white/5 rounded-full border border-gray-300 dark:border-white/10 px-4 py-2 shadow-sm transition-colors">
                  {/* Hidden file input */}
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept="image/jpeg,image/png,image/gif,image/webp,image/bmp,application/pdf,.pdf,.jpg,.jpeg,.png,.gif,.webp,.bmp,.doc,.docx,.xls,.xlsx"
                    onChange={handleFileSelect}
                    className="hidden"
                  />

                  {/* Upload button */}
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="shrink-0 p-1.5 rounded-full text-gray-400 hover:text-teal-600 dark:hover:text-teal-400 hover:bg-teal-50 dark:hover:bg-teal-900/20 transition-colors"
                    title={t.chat.attach_file}
                    disabled={isLoading}
                  >
                    <Paperclip size={16} />
                  </button>

                  <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                      }
                    }}
                    placeholder={t.chat.type_message}
                    rows={1}
                    disabled={isLoading}
                    className="flex-1 bg-transparent text-gray-800 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 resize-none focus:outline-none text-sm"
                  />
                  {/* Mode */}
                  <div className="relative">
                    <button
                      onClick={() => setShowModeMenu(s => !s)}
                      className="shrink-0 px-3 py-1.5 rounded-full border border-gray-300 dark:border-white/10 text-xs text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors flex items-center gap-1"
                      title={t.chat.choose_mode}
                    >
                      <Sparkles size={12} />
                      <span>{mode === 'basic' ? t.chat.basic : t.chat.advanced}</span>
                    </button>
                    {showModeMenu && (
                      <div className="absolute bottom-full mb-2 right-0 bg-white dark:bg-[#1F2937] border border-gray-200 dark:border-white/10 rounded-lg shadow-lg overflow-hidden min-w-[120px]">
                        {[
                          { v: 'basic', label: t.chat.basic },
                          { v: 'advanced', label: t.chat.advanced },
                        ].map(opt => (
                          <button
                            key={opt.v}
                            onClick={() => { setMode(opt.v as any); setShowModeMenu(false); }}
                            className={`w-full text-left px-3 py-2 text-xs hover:bg-gray-100 dark:hover:bg-white/5 ${
                              mode === opt.v
                                ? 'text-gray-900 dark:text-white font-medium bg-gray-50 dark:bg-white/5'
                                : 'text-gray-700 dark:text-gray-300'
                            }`}
                          >
                            {opt.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  {/* Send */}
                  <button
                    onClick={isLoading ? handleStop : handleSend}
                    disabled={!isLoading && !input.trim() && uploadedFiles.length === 0}
                    className="shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-purple-600 flex items-center justify-center text-white disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
                    title={isLoading ? t.chat.stop : t.chat.send}
                  >
                    {isLoading ? <Square size={14} /> : <Send size={14} />}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </main>

        {/* ── Side-by-Side PDF Viewer Panel (Nhóm 4) ── */}
        {activePdfViewer && (
          <aside className="w-full sm:w-[48%] md:w-[50%] lg:w-[52%] h-full shrink-0 flex flex-col min-h-0 z-10 transition-all duration-300">
            <SideBySidePdfViewer
              documentId={activePdfViewer.documentId}
              filename={activePdfViewer.filename}
              title={activePdfViewer.title}
              initialPage={activePdfViewer.page}
              totalPages={activePdfViewer.totalPages}
              token={token}
              snippet={activePdfViewer.snippet}
              onClose={() => setActivePdfViewer(null)}
            />
          </aside>
        )}
      </div>

      {/* ── Auth Required Modal ── */}
      <AuthRequiredModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        title="Đăng nhập để sử dụng tính năng Chat AI"
        description="Bạn cần đăng nhập tài khoản Acamind để gửi tin nhắn, tải lên tài liệu học tập và khai thác trích dẫn đối chiếu PDF."
      />
    </div>
  );
}
