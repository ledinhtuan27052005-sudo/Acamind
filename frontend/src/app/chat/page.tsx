'use client';

import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import {
  getDocuments, chatStream, chatGeneralStream,
  getMyPlanUsage, chatFileStream, lookupDocument,
  DocumentInfo, PlanUsage, ChatTelemetryPayload,
  verifyAtomicClaims, ClaimVerificationResult,
  fetchNeuroClinicalGraph, NeuroClinicalGraphData,
} from '@/lib/api';
import { useAppStore } from '@/store/useAppStore';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Send, Square, Brain, Globe, Trash2, Zap,
  MessageSquare, Clock, Plus, X, User, Sparkles, Paperclip, FileText, Lock,
  Copy, Check, Quote, BookOpen, ChevronRight, Table,
  Activity, ShieldCheck, Award, ChevronDown, ChevronUp, Code, Eye, ExternalLink,
} from 'lucide-react';
import { SideBySidePdfViewer } from '@/components/ui/SideBySidePdfViewer';
import { AuthRequiredModal } from '@/components/auth/AuthRequiredModal';
import { KatexMath } from '@/components/ui/KatexMath';
import { FigureViewer } from '@/components/ui/FigureViewer';
import { MermaidRenderer } from '@/components/ui/MermaidRenderer';
import { cleanMarkdownText } from '@/components/ui/AcademicDocumentRenderer';

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
  telemetryPayload?: ChatTelemetryPayload | null;
}

interface ChatFile {
  name: string;
  type: string;
  url: string;
  size?: number;
}

function chatSessionStorageKey(): string {
  const userId = useAppStore.getState().user?.id;
  return userId ? `chat.sessions.user.${userId}` : 'chat.sessions.guest';
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
    for (let i = 1; i < rows.length; i++) {
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
      const quoteContent = trimmed.replace(/^>\s*/, '').replace(/^#+/, '').trim();
      result.push({
        type: 'blockquote',
        content: quoteContent,
      });
      continue;
    }

    // 7. Heading (#, ##, ###)
    const headingMatch = trimmed.match(/^(#{1,6})\s*(.+)$/);
    if (headingMatch) {
      result.push({
        type: 'heading',
        level: headingMatch[1].length,
        content: headingMatch[2].replace(/\s*#+\s*$/, '').trim(),
      });
      continue;
    }

    // 8. Numbered item (1. item, 2. item, a) item, I. item)
    const numberedMatch = trimmed.match(/^(\d+[\.\)]|[a-zA-Z]\)|[ivxIVX]+[\.\)])\s+(.*)$/);
    if (numberedMatch) {
      result.push({
        type: 'numbered',
        numberPrefix: numberedMatch[1],
        content: numberedMatch[2].replace(/^#{1,6}\s+/, ''),
      });
      continue;
    }

    // 9. Bullet point (- item, * item, • item, — item, ▪ item)
    const bulletMatch = trimmed.match(/^[-*+•—–▪✦✓]\s+(.*)$/);
    if (bulletMatch) {
      result.push({
        type: 'bullet',
        bulletGlyph: bulletMatch[0][0],
        content: bulletMatch[1].replace(/^#{1,6}\s+/, ''),
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
  const regex = /(?:\*\*(.+?)\*\*|__(.+?)__)/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ bold: false, text: text.slice(lastIndex, match.index) });
    }
    parts.push({ bold: true, text: match[1] || match[2] });
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

  // Render inline math and clean inline code/markdown artifacts inside text
  const renderMathSpan = (raw: string, pfx: string) => {
    const mathParts = parseInlineMath(raw);
    return mathParts.map((m, mIdx) => {
      if (m.isMath) {
        return <KatexMath key={`${pfx}-math-${mIdx}`} math={m.content} block={false} />;
      }
      const codeSplit = m.content.split(/(\`[^\`\n]+?\`)/g);
      return (
        <span key={`${pfx}-txt-${mIdx}`}>
          {codeSplit.map((seg, sIdx) => {
            if (seg.startsWith('`') && seg.endsWith('`') && seg.length > 2) {
              return (
                <span
                  key={sIdx}
                  className="px-1.5 py-0.5 mx-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-semibold text-[0.92em]"
                >
                  {seg.slice(1, -1)}
                </span>
              );
            }
            const cleanSeg = seg
              .replace(/^#{1,6}\s+/g, '')
              .replace(/\*{2,}/g, '')
              .replace(/`+/g, '');
            return <span key={sIdx}>{cleanSeg}</span>;
          })}
        </span>
      );
    });
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

    // 2. Academic Citation: [filename.pdf - Page 3], [filename.pdf, Page 3], [filename.pdf - tr. 3] hoặc [file.xlsx - Sheet: DoanhThu]
    if (/(?:Page|Trang|tr\.?|p\.?|pp\.?)\s*\d+/i.test(bracketInner) || /Sheet\s*:/i.test(bracketInner)) {
      const subItems = bracketInner.split(';');
      const citationButtons: React.ReactNode[] = [];

      // Trích xuất chính xác câu từ hoặc trích đoạn trích dẫn làm snippet đối chứng
      let contextSnippet = '';
      const textBefore = text.slice(0, match.index).trim();
      if (textBefore) {
        // 1. Kiểm tra nếu có câu trích dẫn trong ngoặc kép ngay trước citation: "..." hoặc “...”
        const quoteMatch = textBefore.match(/(?:["“'«])([^"”'»\n]{6,350})(?:["”'»])\s*$/);
        if (quoteMatch) {
          contextSnippet = quoteMatch[1].trim();
        }

        // 2. Kiểm tra nếu là khối trích dẫn markdown blockquote: > "..." hoặc > ...
        if (!contextSnippet) {
          const blockquoteMatch = textBefore.match(/(?:^|\n)\s*>\s*([^\n]{6,350})$/);
          if (blockquoteMatch) {
            contextSnippet = blockquoteMatch[1].replace(/^[“"'\s]+|[”"'\s]+$/g, '').trim();
          }
        }

        // 3. Kiểm tra nếu là đầu mục danh sách (bullet point hoặc đánh số): - ... hoặc 1. ...
        if (!contextSnippet) {
          const bulletMatch = textBefore.match(/(?:^|\n)\s*(?:[-*•–—]|\d+\.)\s*([^\n]{6,350})$/);
          if (bulletMatch) {
            contextSnippet = bulletMatch[1].trim();
          }
        }

        // 4. Kiểm tra nếu trong ô bảng dữ liệu Markdown: | ... [citation] |
        if (!contextSnippet) {
          const tableCellMatch = textBefore.match(/\|([^|\n]{4,250})$/);
          if (tableCellMatch) {
            contextSnippet = tableCellMatch[1].trim();
          }
        }

        // 5. Trích xuất câu hoặc mệnh đề hoàn chỉnh trong đoạn văn
        if (!contextSnippet) {
          const cleanBefore = textBefore
            .replace(/\[[^\[\]]*?(?:Trang|Page|Sheet|tr\.?|p\.?|pp\.?)\s*\d+[^\[\]]*?\]/gi, '')
            .replace(/[\*\_]/g, '')
            .trim();
          const sentences = cleanBefore.split(/(?<=[.!?\n])\s+/);
          let candidate = sentences[sentences.length - 1] || cleanBefore;
          if (sentences.length >= 2 && candidate.length < 25) {
            candidate = `${sentences[sentences.length - 2]} ${candidate}`.trim();
          }
          if (candidate.length > 280) {
            const words = candidate.split(/\s+/);
            candidate = words.slice(-35).join(' ');
          }
          contextSnippet = candidate;
        }

        // Dọn dẹp sạch sẽ các ký tự markdown bao bọc (giữ lại khoảng tin cậy thống kê như [0.22, 0.45])
        contextSnippet = contextSnippet
          .replace(/\[[^\[\]]*?(?:Trang|Page|Sheet|tr\.?|p\.?|pp\.?)\s*\d+[^\[\]]*?\]/gi, '')
          .replace(/[\*\_`]/g, '')
          .replace(/^[“"'«\s]+|[”"'»\s]+$/g, '')
          .trim();
      }

      if (!contextSnippet && textBefore.trim().length > 0) {
        contextSnippet = text
          .replace(/\[[^\[\]]*?(?:Trang|Page|Sheet|tr\.?|p\.?|pp\.?)\s*\d+[^\[\]]*?\]/gi, '')
          .replace(/[\*\_`]/g, '')
          .trim()
          .slice(0, 180);
      }

      subItems.forEach((sub, subIdx) => {
        const pageMatch = sub.match(/([^\n]+?)\s*[-–—,:]\s*(?:Page|Trang|tr\.?|p\.?|pp\.?)\s*(\d+)/i);
        const sheetMatch = sub.match(/([^-\n]+?)\s*-\s*Sheet\s*:\s*([^\]\n;]+)/i);

        if (sheetMatch) {
          const rawFilename = sheetMatch[1].trim();
          const sheetName = sheetMatch[2].trim();
          const shortName = rawFilename.length > 20 ? rawFilename.slice(0, 18) + '…' : rawFilename;
          citationButtons.push(
            <span
              key={`cite-sheet-${match!.index}-${subIdx}`}
              className="inline-flex items-center gap-1.5 px-2 py-0.5 mx-1 my-0.5 rounded-md text-[11.5px] font-medium bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-200 border border-emerald-300 dark:border-emerald-700/60 shadow-2xs select-none"
              title={`Trích xuất từ tệp Excel: "${rawFilename}", Sheet: "${sheetName}"`}
            >
              <Table size={11} className="text-emerald-600 dark:text-emerald-400 shrink-0" />
              <span className="font-semibold truncate max-w-[130px]">{shortName}</span>
              <span className="bg-emerald-200/80 dark:bg-emerald-800/70 px-1.5 py-0.2 rounded text-[10px] font-mono font-bold text-emerald-900 dark:text-emerald-100">
                Sheet: {sheetName}
              </span>
            </span>
          );
        } else if (pageMatch) {
          const rawFilename = pageMatch[1].trim();
          const pageNum = parseInt(pageMatch[2], 10);
          const shortName = rawFilename.length > 40 ? rawFilename.slice(0, 37) + '…' : rawFilename;

          citationButtons.push(
            <button
              key={`cite-${match!.index}-${subIdx}`}
              type="button"
              onClick={() => onCitationClick?.(rawFilename, pageNum, contextSnippet)}
              className="inline-flex items-center gap-1.5 px-2 py-0.5 mx-1 my-0.5 rounded-md text-[11.5px] font-medium bg-slate-100 hover:bg-teal-50 dark:bg-slate-800/90 dark:hover:bg-teal-950/70 text-slate-700 hover:text-teal-700 dark:text-slate-200 dark:hover:text-teal-300 border border-slate-300/80 hover:border-teal-400 dark:border-slate-700 dark:hover:border-teal-600 transition-all hover:scale-105 active:scale-95 group shadow-2xs cursor-pointer select-none"
              title={`Nhấn để mở "${rawFilename}" tại trang ${pageNum}`}
            >
              <FileText size={11} className="text-teal-600 dark:text-teal-400 shrink-0 group-hover:rotate-6 transition-transform" />
              <span className="font-semibold break-all text-left">{shortName}</span>
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

/* ── AI Message Component (Word / PDF Document Paper Sheet + Live Telemetry & EBP Badges) ── */

function AiMessage({
  content,
  query,
  documentIds,
  telemetryPayload,
  onCitationClick,
  onInjectPrompt,
}: {
  content: string;
  query?: string;
  documentIds?: string[];
  telemetryPayload?: ChatTelemetryPayload | null;
  onCitationClick?: (filename: string, page: number, snippet?: string) => void;
  onInjectPrompt?: (promptText: string) => void;
}) {
  const legacyFeaturesEnabled = () => process.env.NEXT_PUBLIC_SHOW_TELEMETRY === '1';
  const router = useRouter();
  const [showTelemetryDetail, setShowTelemetryDetail] = useState(false);
  const [copiedApaId, setCopiedApaId] = useState<string | null>(null);
  const [copiedBibId, setCopiedBibId] = useState<string | null>(null);

  // Feature 1: Claim-Level Entailment & Hallucination Shield (CLHV)
  const [claimResult, setClaimResult] = useState<ClaimVerificationResult | null>(null);
  const [claimLoading, setClaimLoading] = useState(false);
  const [showClaimPanel, setShowClaimPanel] = useState(false);

  // Feature 3: Interactive Neuro-Clinical Knowledge Graph <-> 3D Brain Bridge
  const [neuroGraph, setNeuroGraph] = useState<NeuroClinicalGraphData | null>(null);
  const [neuroLoading, setNeuroLoading] = useState(false);
  const [showNeuroPanel, setShowNeuroPanel] = useState(false);

  const tel = telemetryPayload?.telemetry;
  const sourcesMeta = telemetryPayload?.sources || [];
  const evidenceTargets = telemetryPayload?.evidence_targets || [];

  // Resolve the best verbatim PDF excerpt for a given (filename, page) from telemetry
  const resolvePageExcerpt = (filename: string, page: number): string | undefined => {
    const cleanTarget = filename.trim().toLowerCase();
    for (const src of sourcesMeta) {
      if (src.filename.trim().toLowerCase() === cleanTarget || src.filename.toLowerCase().includes(cleanTarget) || cleanTarget.includes(src.filename.toLowerCase())) {
        const exc = src.page_excerpts?.[String(page)];
        if (exc && exc.trim().length > 15) return exc.trim();
      }
    }
    for (const target of evidenceTargets) {
      for (const item of target.evidence || []) {
        if (item.page === page && (item.filename.trim().toLowerCase() === cleanTarget || item.filename.toLowerCase().includes(cleanTarget))) {
          if (item.excerpt && item.excerpt.trim().length > 15) return item.excerpt.trim();
        }
      }
    }
    return undefined;
  };

  const handleSmartCitationClick = (filename: string, page: number, contextSnippet?: string) => {
    let effectiveSnippet = contextSnippet?.trim() || '';
    const isPaperTitle = effectiveSnippet && sourcesMeta.some(
      (s) => s.title && effectiveSnippet.toLowerCase().includes(s.title.trim().toLowerCase().slice(0, 28))
    );
    if ((!effectiveSnippet || isPaperTitle) && content) {
      const bodyOnly = content.split(/#{1,3}\s*(?:Tài liệu tham khảo|References|Nguồn trích dẫn)/i)[0] || content;
      const cleanName = filename.trim().toLowerCase();
      const bodyLines = bodyOnly.split('\n');
      for (let idx = 0; idx < bodyLines.length; idx++) {
        const line = bodyLines[idx];
        if (
          line.toLowerCase().includes(cleanName) &&
          new RegExp(`(?:Trang|Page|tr\\.?|p\\.?|pp\\.?)\\s*${page}\\b`, 'i').test(line)
        ) {
          let cleanedLine = line
            .replace(/\[[^\[\]]*?(?:Trang|Page|Sheet|tr\.?|p\.?|pp\.?)\s*\d+[^\[\]]*?\]/gi, '')
            .replace(/^[\s\-*•\d.)#]+/, '')
            .replace(/[\*\_`]/g, '')
            .trim();
          if (cleanedLine.length < 15) {
            for (let prev = idx - 1; prev >= 0; prev--) {
              const candPrev = bodyLines[prev]
                .replace(/\[[^\[\]]*?(?:Trang|Page|Sheet|tr\.?|p\.?|pp\.?)\s*\d+[^\[\]]*?\]/gi, '')
                .replace(/^[\s\-*•\d.)#>]+/, '')
                .replace(/[\*\_`]/g, '')
                .trim();
              if (candPrev.length >= 15 && !candPrev.startsWith('---')) {
                cleanedLine = candPrev;
                break;
              }
            }
          }
          if (cleanedLine.length < 15) {
            for (let next = idx + 1; next < bodyLines.length; next++) {
              const candNext = bodyLines[next]
                .replace(/\[[^\[\]]*?(?:Trang|Page|Sheet|tr\.?|p\.?|pp\.?)\s*\d+[^\[\]]*?\]/gi, '')
                .replace(/^[\s\-*•\d.)#>]+/, '')
                .replace(/[\*\_`]/g, '')
                .trim();
              if (candNext.length >= 15 && !candNext.startsWith('---')) {
                cleanedLine = candNext.split(/(?<=[.!?])\s+/)[0] || candNext;
                break;
              }
            }
          }
          if (cleanedLine.length >= 15) {
            effectiveSnippet = cleanedLine.slice(0, 260);
            break;
          }
        }
      }
    }

    const verbatimExcerpt = resolvePageExcerpt(filename, page);
    const combinedSnippet = verbatimExcerpt
      ? effectiveSnippet && effectiveSnippet !== verbatimExcerpt
        ? `${verbatimExcerpt} || ${effectiveSnippet}`
        : verbatimExcerpt
      : effectiveSnippet || undefined;
    onCitationClick?.(filename, page, combinedSnippet);
  };

  const handleOpenEvidenceMatrix = () => {
    const documentIdsForMatrix = Array.from(new Set(sourcesMeta.map((source) => source.document_id).filter(Boolean))).slice(0, 10);
    if (documentIdsForMatrix.length === 0) return;
    const params = new URLSearchParams();
    if (query?.trim()) params.set('focus', query.trim());
    documentIdsForMatrix.forEach((id) => params.append('document_id', id));
    router.push(`/Literature?${params.toString()}`);
  };

  const handleVerifyClaims = async () => {
    if (showClaimPanel && claimResult) {
      setShowClaimPanel(false);
      return;
    }
    setShowClaimPanel(true);
    if (claimResult || claimLoading) return;
    setClaimLoading(true);
    try {
      const res = await verifyAtomicClaims(
        query || '',
        content,
        documentIds && documentIds.length > 0 ? documentIds : undefined
      );
      setClaimResult(res);
    } catch (e) {
      console.error('Claim verification error:', e);
    } finally {
      setClaimLoading(false);
    }
  };

  const handleOpenNeuroGraph = async () => {
    if (showNeuroPanel && neuroGraph) {
      setShowNeuroPanel(false);
      return;
    }
    setShowNeuroPanel(true);
    if (neuroGraph || neuroLoading) return;
    setNeuroLoading(true);
    try {
      const res = await fetchNeuroClinicalGraph(
        query || '',
        content,
        documentIds && documentIds.length > 0 ? documentIds : undefined
      );
      setNeuroGraph(res);
    } catch (e) {
      console.error('Neuro graph error:', e);
    } finally {
      setNeuroLoading(false);
    }
  };

  const handleJumpTo3DBrain = (regionId: string) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(
        'acamind_3d_target',
        JSON.stringify({ region_id: regionId, context_text: content })
      );
    }
    router.push(`/3d?region=${encodeURIComponent(regionId)}&xray=1`);
  };

  const copySourceCitation = (id: string, textToCopy: string, type: 'apa' | 'bib') => {
    navigator.clipboard.writeText(textToCopy);
    if (type === 'apa') {
      setCopiedApaId(id);
      setTimeout(() => setCopiedApaId(null), 2000);
    } else {
      setCopiedBibId(id);
      setTimeout(() => setCopiedBibId(null), 2000);
    }
  };

  const routeLabel =
    tel?.route === 'cross_article_comparison'
      ? `Cross-Article (M=${tel.num_targets})`
      : tel?.route === 'literature_synthesis'
      ? `Lit-Synthesis (M=${tel.num_targets})`
      : 'Single-Focus (M=1)';

  return (
    <div className="group relative bg-white dark:bg-[#151a23] border border-slate-200/90 dark:border-slate-800 rounded-2xl shadow-[0_4px_24px_rgba(0,0,0,0.05)] dark:shadow-[0_4px_24px_rgba(0,0,0,0.35)] overflow-hidden transition-all hover:border-slate-300 dark:hover:border-slate-700">
      {/* ── Document Page Header Bar (Word / PDF Document Style) ── */}
      {telemetryPayload?.evidence_matrix && (
        <details className="border-b border-slate-200 dark:border-slate-800 px-4 py-3 text-xs">
          <summary className="cursor-pointer font-semibold text-teal-700 dark:text-teal-300">
            {telemetryPayload.evidence_matrix.action === 'partial' ? 'Chỉ đủ bằng chứng cho một phần câu hỏi' : 'Bằng chứng theo tiêu chí'}
            {' · '}{telemetryPayload.evidence_matrix.supported_cells}/{telemetryPayload.evidence_matrix.total_cells} tiêu chí có đoạn hỗ trợ
          </summary>
          <p className="my-2 text-slate-500">Các đoạn dưới đây đã được đối chiếu nguyên văn; đánh giá nội dung do mô hình thực hiện.</p>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead><tr><th className="p-2">Nghiên cứu / Câu hỏi</th><th className="p-2">Tiêu chí</th><th className="p-2">Bằng chứng</th></tr></thead>
              <tbody>{telemetryPayload.evidence_matrix.cells.map((cell, index) => (
                <tr key={index} className="border-t border-slate-200 dark:border-slate-800 align-top">
                  <td className="p-2">{cell.target}</td>
                  <td className="p-2">{({ sample: 'Mẫu', method: 'Phương pháp', measure: 'Thang đo', finding: 'Kết quả', limitation: 'Hạn chế', answer: 'Nội dung trả lời' } as Record<string, string>)[cell.facet] || cell.facet}</td>
                  <td className="p-2">{cell.evidence.length ? cell.evidence.map((e, i) => (
                    <div key={i} className="mb-2"><p>“{e.quote}”</p>
                      <button type="button" className="text-teal-700 dark:text-teal-300 underline mt-1"
                        onClick={() => onCitationClick?.(e.filename, e.page, e.quote)}>{e.filename} · Trang {e.page}</button>
                    </div>
                  )) : 'Chưa tìm thấy trong các đoạn đã truy xuất'}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </details>
      )}
      {/* ── Live RAG Pipeline Telemetry Bar (Proposal 1: DCSR + Multi-Target Router + CRAG Gate) ── */}
      {legacyFeaturesEnabled() && tel && (
        <div className="border-b border-slate-200/80 dark:border-slate-800/90 bg-slate-50/70 dark:bg-[#111722] px-4 sm:px-6 py-2 text-[11px]">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-1.5">
              {/* Memory / Hybrid Tier */}
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-semibold bg-teal-500/10 text-teal-700 dark:text-teal-300 border border-teal-500/25">
                <Activity size={11} />
                {tel.memory_tier === 'L1_FAST_MEMORY' ? 'L1 Fast Memory' : `Hybrid RRF (k=${tel.rrf_k})`}
              </span>

              {/* Query Router */}
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-medium bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border border-indigo-500/25">
                Router: {routeLabel}
              </span>

              {/* DCSR Gate */}
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-medium border ${
                  tel.dcsr_fast_skip
                    ? 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/25'
                    : 'bg-purple-500/10 text-purple-700 dark:text-purple-300 border-purple-500/25'
                }`}
              >
                <Zap size={11} />
                {tel.dcsr_fast_skip
                  ? `DCSR Fast-Skip (Δ=${tel.dominance_ratio}, Conf=${tel.dcsr_confidence})`
                  : `Cross-Encoder Rerank (Conf=${tel.dcsr_confidence})`}
              </span>

              {/* CRAG Gate */}
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-medium bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/25">
                <ShieldCheck size={11} />
                CRAG: {tel.crag_passed ? 'Verified' : 'Abstain'} (S₂={tel.crag_score} ≥ τ={tel.crag_threshold})
              </span>

              {/* Epistemic Uncertainty & Shannon Entropy Badge */}
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-medium border ${
                  (tel.epistemic_level || 'LOW') === 'LOW'
                    ? 'bg-cyan-500/10 text-cyan-800 dark:text-cyan-300 border-cyan-500/25'
                    : (tel.epistemic_level || 'LOW') === 'MODERATE'
                    ? 'bg-amber-500/10 text-amber-800 dark:text-amber-300 border-amber-500/25'
                    : 'bg-rose-500/10 text-rose-800 dark:text-rose-300 border-rose-500/25'
                }`}
                title={tel.epistemic_label || 'Định lượng Độ Bất định Nhận thức & Entropy Bằng chứng Shannon'}
              >
                H(q)={tel.shannon_entropy_bits ?? 0}b • U_epist={tel.epistemic_uncertainty ?? 0} ({tel.epistemic_level || 'LOW'})
              </span>

              {/* Latency */}
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-mono text-[10.5px] bg-slate-200/70 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                ⏱ {tel.latency_ms} ms
              </span>
            </div>

            <button
              type="button"
              onClick={() => setShowTelemetryDetail((s) => !s)}
              className="inline-flex items-center gap-1 text-[11px] font-semibold text-teal-700 dark:text-teal-400 hover:underline cursor-pointer shrink-0"
            >
              <span>{showTelemetryDetail ? 'Ẩn thông số' : 'Chi tiết thuật toán'}</span>
              {showTelemetryDetail ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </button>
          </div>

          {showTelemetryDetail && (
            <div className="mt-2.5 pt-2.5 border-t border-slate-200/70 dark:border-slate-800 space-y-2.5 text-[11px]">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5">
                <div className="p-2.5 rounded-xl bg-white dark:bg-slate-900/80 border border-slate-200/80 dark:border-slate-800">
                  <div className="font-bold text-slate-800 dark:text-slate-200 mb-1">1. Phân rã Đa mục tiêu (Eq. 9)</div>
                  <div className="text-slate-600 dark:text-slate-400 space-y-0.5">
                    <div>Chế độ: <span className="font-mono font-semibold text-indigo-600 dark:text-indigo-400">{tel.route}</span></div>
                    <div>Số mục tiêu (M): <span className="font-mono font-semibold">{tel.num_targets}</span> (Quota: {tel.quota_per_target}/mục tiêu)</div>
                    <div className="truncate" title={tel.sub_queries?.join(' | ')}>
                      Truy vấn con: <span className="italic">{tel.sub_queries?.join(' • ')}</span>
                    </div>
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-white dark:bg-slate-900/80 border border-slate-200/80 dark:border-slate-800">
                  <div className="font-bold text-slate-800 dark:text-slate-200 mb-1">2. Truy hồi Lai RRF (k = {tel.rrf_k})</div>
                  <div className="text-slate-600 dark:text-slate-400 space-y-0.5">
                    <div>Dense HNSW (384-d): <span className="font-mono font-semibold">{tel.vector_hits} ứng viên</span></div>
                    <div>Title-Boosted GIN FTS: <span className="font-mono font-semibold">{tel.fts_hits} ứng viên</span></div>
                    <div>Top-1 RRF Score: <span className="font-mono font-semibold text-teal-600 dark:text-teal-400">{tel.top_rrf_score}</span></div>
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-white dark:bg-slate-900/80 border border-slate-200/80 dark:border-slate-800">
                  <div className="font-bold text-slate-800 dark:text-slate-200 mb-1">3. Chọn lọc DCSR (Eq. 5–8)</div>
                  <div className="text-slate-600 dark:text-slate-400 space-y-0.5">
                    <div>Độ tin cậy C(q): <span className="font-mono font-semibold">{tel.dcsr_confidence}</span> (τ_conf = 0.35)</div>
                    <div>Tỷ số áp đảo Δ_RRF: <span className="font-mono font-semibold">{tel.dominance_ratio}</span> (τ_Δ = 1.05)</div>
                    <div>Quyết định: <span className="font-semibold text-amber-600 dark:text-amber-400">{tel.dcsr_fast_skip ? 'Fast-Skip Cross-Encoder' : 'Chạy Cross-Encoder (K=16)'}</span></div>
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-white dark:bg-slate-900/80 border border-slate-200/80 dark:border-slate-800">
                  <div className="font-bold text-slate-800 dark:text-slate-200 mb-1">4. Cổng Kiểm định CRAG</div>
                  <div className="text-slate-600 dark:text-slate-400 space-y-0.5">
                    <div>Điểm cổng S₂(q): <span className="font-mono font-semibold text-emerald-600 dark:text-emerald-400">{tel.crag_score}</span> (τ_min = {tel.crag_threshold})</div>
                    <div>Số đoạn trích (Chunks): <span className="font-mono font-semibold">{tel.chunks_count} chunks / {tel.unique_docs} bài báo</span></div>
                    <div>Thời gian truy hồi: <span className="font-mono font-semibold">{tel.latency_ms} ms</span></div>
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-cyan-50/50 dark:bg-cyan-950/25 border border-cyan-200/80 dark:border-cyan-800/70">
                  <div className="font-bold text-cyan-900 dark:text-cyan-200 mb-1">5. Entropy &amp; Độ Bất định Nhận thức</div>
                  <div className="text-slate-600 dark:text-slate-400 space-y-0.5">
                    <div>Shannon H(q): <span className="font-mono font-semibold text-cyan-700 dark:text-cyan-300">{tel.shannon_entropy_bits ?? 0} bits</span> (H_max={tel.max_entropy_bits ?? 0})</div>
                    <div>Bất định U_epist(q): <span className="font-mono font-semibold text-indigo-600 dark:text-indigo-400">{tel.epistemic_uncertainty ?? 0}</span> ({tel.epistemic_level || 'LOW'})</div>
                    <div>Đa dạng nguồn Gini D: <span className="font-mono font-semibold text-emerald-600 dark:text-emerald-400">{tel.source_diversity_index ?? 0}</span></div>
                  </div>
                </div>
              </div>

              {tel.chunk_probabilities && tel.chunk_probabilities.length > 0 && (
                <div className="p-2.5 rounded-xl bg-white dark:bg-slate-900/80 border border-slate-200/80 dark:border-slate-800 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-slate-700 dark:text-slate-300">
                      Phân phối Xác suất Hậu nghiệm P(c_k | q) = softmax(S_k / τ):
                    </span>
                    {tel.chunk_probabilities.map((prob, pIdx) => (
                      <span
                        key={pIdx}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 font-mono text-[10.5px] text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
                      >
                        <span>c_{pIdx + 1}:</span>
                        <span className="font-bold text-teal-600 dark:text-teal-400">{(prob * 100).toFixed(1)}%</span>
                      </span>
                    ))}
                  </div>
                  <span className="text-[10.5px] font-medium text-cyan-700 dark:text-cyan-300">
                    {tel.epistemic_label || 'Bất định nhận thức thấp (Bằng chứng hội tụ vững chắc)'}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Feature 1: Claim-Level Entailment & Hallucination Shield (CLHV) Panel ── */}
      {legacyFeaturesEnabled() && showClaimPanel && claimResult && (
        <div className="border-b border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/40 dark:bg-emerald-950/20 px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
            <div className="flex items-center gap-2">
              <ShieldCheck size={16} className="text-emerald-600 dark:text-emerald-400" />
              <span className="font-bold text-xs uppercase tracking-wider text-emerald-900 dark:text-emerald-200">
                Đối chiếu mệnh đề với đoạn nguồn ứng viên
              </span>
            </div>
            <button
              type="button"
              onClick={() => setShowClaimPanel(false)}
              className="text-xs text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
            >
              Đóng ✕
            </button>
          </div>

          {claimLoading ? (
            <div className="text-xs text-emerald-700 dark:text-emerald-300 py-3 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
              <span>Đang phân rã câu trả lời thành các mệnh đề nguyên tử (Atomic Claims) và đối chiếu hàm kéo theo ngữ nghĩa...</span>
            </div>
          ) : claimResult ? (
            <div className="space-y-3">
              {/* Summary Bar */}
              <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-xl bg-white dark:bg-slate-900/90 border border-emerald-200/80 dark:border-emerald-800/60 text-xs">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-bold text-slate-800 dark:text-slate-100">
                    Độ Trung thực Học thuật (Faithfulness):{' '}
                    <span className="text-emerald-600 dark:text-emerald-400 font-mono text-sm">
                      {claimResult.faithfulness_score === null ? 'Chưa xác minh' : `${claimResult.faithfulness_score}%`}
                    </span>
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 font-semibold">
                    🟢 Bảo chứng ({claimResult.entailed_count})
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-700 dark:text-amber-300 font-semibold">
                    🟡 Suy luận ({claimResult.extrapolated_count})
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-700 dark:text-rose-300 font-semibold">
                    🔴 Chưa đủ bằng chứng ({claimResult.unverified_count})
                  </span>
                </div>
                <span className="font-mono text-[10.5px] text-slate-500 dark:text-slate-400">
                  {claimResult.formula}
                </span>
              </div>

              {/* Atomic Claims List */}
              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {claimResult.claims.map((c) => {
                  const isGreen = c.status === 'ENTAILED';
                  const isAmber = c.status === 'EXTRAPOLATED';
                  const cardCls = isGreen
                    ? 'border-emerald-300/80 dark:border-emerald-800/70 bg-white dark:bg-slate-900/80'
                    : isAmber
                    ? 'border-amber-300/80 dark:border-amber-800/70 bg-white dark:bg-slate-900/80'
                    : 'border-rose-300/80 dark:border-rose-800/70 bg-white dark:bg-slate-900/80';
                  const badgeCls = isGreen
                    ? 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border-emerald-500/30'
                    : isAmber
                    ? 'bg-amber-500/15 text-amber-800 dark:text-amber-300 border-amber-500/30'
                    : 'bg-rose-500/15 text-rose-800 dark:text-rose-300 border-rose-500/30';

                  return (
                    <div key={c.index} className={`p-3 rounded-xl border ${cardCls} text-xs space-y-1.5`}>
                      <div className="flex items-center justify-between flex-wrap gap-1.5">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className={`px-2 py-0.5 rounded-md font-bold text-[10.5px] border ${badgeCls}`}>
                            Mệnh đề #{c.index}: {c.status_label}
                          </span>
                          {c.key_terms_matched && c.key_terms_matched.length > 0 && (
                            <span className="font-mono text-[10.5px] text-slate-500 dark:text-slate-400">
                              Khớp thuật ngữ: {c.key_terms_matched.slice(0, 4).join(', ')}
                            </span>
                          )}
                        </div>
                        {c.matched_filename && c.matched_page > 0 && (
                          <button
                            type="button"
                            onClick={() => onCitationClick?.(c.matched_filename, c.matched_page, c.evidence_snippet)}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10.5px] font-semibold bg-teal-50 hover:bg-teal-100 dark:bg-teal-950/60 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800 cursor-pointer"
                          >
                            <Eye size={10} />
                            <span>Đối chiếu PDF ({(c.matched_title || c.matched_filename).slice(0, 28)} - Tr. {c.matched_page})</span>
                          </button>
                        )}
                      </div>
                      <p className="text-slate-800 dark:text-slate-200 font-medium leading-relaxed">
                        {cleanMarkdownText(c.clean_text || c.claim_text)}
                      </p>
                      {c.evidence_snippet && (
                        <div className="text-[11px] text-slate-600 dark:text-slate-400 italic bg-slate-50 dark:bg-slate-800/60 px-2.5 py-1.5 rounded-lg border-l-2 border-teal-500">
                          Bằng chứng gốc ({c.matched_filename} - Tr. {c.matched_page}): “{cleanMarkdownText(c.evidence_snippet)}”
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* ── Feature 3: Interactive Neuro-Clinical Knowledge Graph <-> 3D Brain Bridge Panel ── */}
      {legacyFeaturesEnabled() && showNeuroPanel && neuroGraph && (
        <div className="border-b border-indigo-200 dark:border-indigo-900/60 bg-indigo-50/40 dark:bg-indigo-950/20 px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
            <div className="flex items-center gap-2">
              <Brain size={16} className="text-indigo-600 dark:text-indigo-400" />
              <span className="font-bold text-xs uppercase tracking-wider text-indigo-900 dark:text-indigo-200">
                Đồ thị Tri thức Thần kinh – Tâm lý 4 Tầng &amp; Cầu nối Giải phẫu Não 3D
              </span>
            </div>
            <button
              type="button"
              onClick={() => setShowNeuroPanel(false)}
              className="text-xs text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
            >
              Đóng ✕
            </button>
          </div>

          {neuroLoading ? (
            <div className="text-xs text-indigo-700 dark:text-indigo-300 py-3 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-ping" />
              <span>Đang trích xuất mạng lưới Hội chứng – Vùng não 3D – Chất dẫn truyền thần kinh – Trị liệu...</span>
            </div>
          ) : neuroGraph ? (
            <div className="space-y-3">
              {neuroGraph.summary && (
                <p className="text-xs text-indigo-900 dark:text-indigo-200 font-medium">
                  {cleanMarkdownText(neuroGraph.summary)}
                </p>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {neuroGraph.brain_regions.map((reg) => (
                  <div
                    key={reg.region_3d_id}
                    className="p-3.5 rounded-xl bg-white dark:bg-slate-900/90 border border-indigo-200/80 dark:border-indigo-800/70 space-y-2 text-xs shadow-2xs"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span
                            className="w-2.5 h-2.5 rounded-full shrink-0"
                            style={{ backgroundColor: reg.color }}
                          />
                          <span className="font-bold text-slate-900 dark:text-white">
                            {cleanMarkdownText(reg.name_vi)}
                          </span>
                        </div>
                        <div className="text-[10.5px] text-slate-500 dark:text-slate-400 mt-0.5">
                          {cleanMarkdownText(reg.name_latin)}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleJumpTo3DBrain(reg.region_3d_id)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition-all cursor-pointer shrink-0"
                      >
                        <ExternalLink size={11} />
                        <span>Mở Não 3D X-Ray</span>
                      </button>
                    </div>

                    <div className="text-[11px] font-medium text-rose-700 dark:text-rose-300 bg-rose-50 dark:bg-rose-950/40 px-2.5 py-1 rounded-md border border-rose-200/60 dark:border-rose-800/50">
                      ⚡ {cleanMarkdownText(reg.role_in_pathology)}
                    </div>

                    <div className="space-y-1 text-[11px]">
                      <div>
                        <span className="font-semibold text-slate-700 dark:text-slate-300">Chất dẫn truyền: </span>
                        <span className="text-purple-700 dark:text-purple-300 font-medium">{reg.neurotransmitters.join(' • ')}</span>
                      </div>
                      <div>
                        <span className="font-semibold text-slate-700 dark:text-slate-300">Can thiệp chuẩn: </span>
                        <span className="text-emerald-700 dark:text-emerald-300">{cleanMarkdownText(reg.therapy_mechanism)}</span>
                      </div>
                      <div className="text-[10.5px] text-slate-500 dark:text-slate-400 italic">
                        📚 {cleanMarkdownText(reg.citation)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* ── Document Page Body (A4 / Document Page Content) ── */}
      <div className="px-5 py-5 sm:px-7 sm:py-6 md:px-8 md:py-7">
        <StructuredMessage content={content} onCitationClick={handleSmartCitationClick} />

        {legacyFeaturesEnabled() && evidenceTargets.length > 0 && (
          <details className="mt-4 rounded-xl border border-teal-200 dark:border-teal-900/70 bg-teal-50/50 dark:bg-teal-950/20">
            <summary className="cursor-pointer list-none px-4 py-3 flex items-center justify-between gap-3">
              <span className="inline-flex items-center gap-2 text-xs font-bold text-teal-900 dark:text-teal-200">
                <BookOpen size={15} /> Bằng chứng theo từng ý hỏi ({evidenceTargets.filter((target) => target.has_retrieved_evidence).length}/{evidenceTargets.length} ý có đoạn được truy hồi)
              </span>
              <ChevronDown size={15} className="text-teal-700 dark:text-teal-300 shrink-0" />
            </summary>
            <div className="px-4 pb-4 space-y-3">
              {evidenceTargets.map((target, targetIndex) => (
                <section key={`${targetIndex}-${target.sub_query}`} className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/70 p-3">
                  <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                    <p className="text-xs font-semibold text-slate-800 dark:text-slate-100">{targetIndex + 1}. {target.sub_query}</p>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${target.has_retrieved_evidence ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'}`}>
                      {target.has_retrieved_evidence ? `Đã truy hồi ${target.retrieved_count} đoạn` : 'Chưa tìm thấy đoạn'}
                    </span>
                  </div>
                  {target.evidence.length > 0 ? (
                    <div className="space-y-2">
                      {target.evidence.map((item, evidenceIndex) => (
                        <div key={`${item.document_id}-${item.page}-${evidenceIndex}`} className="rounded-md bg-slate-50 dark:bg-slate-950/70 p-2.5">
                          <button type="button" onClick={() => handleSmartCitationClick(item.filename, item.page, item.excerpt)} className="text-left text-[11px] font-bold text-teal-700 hover:underline dark:text-teal-300">
                            {item.title} · {item.filename} · Trang {item.page} <ExternalLink size={10} className="inline" />
                          </button>
                          <p className="mt-1 whitespace-pre-wrap text-[11px] leading-relaxed text-slate-600 dark:text-slate-300">{item.excerpt}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-[11px] text-amber-800 dark:text-amber-300">Chưa có đoạn tài liệu được truy hồi cho ý này. Hãy bổ sung nguồn hoặc thử diễn đạt lại câu hỏi.</p>
                  )}
                </section>
              ))}
              <p className="text-[10px] text-slate-500 dark:text-slate-400">Có đoạn được truy hồi không đồng nghĩa đoạn đó đã chứng minh câu trả lời; hãy mở trang PDF để kiểm tra nội dung.</p>
            </div>
          </details>
        )}

        {legacyFeaturesEnabled() && sourcesMeta.length >= 2 && (
          <div className="mt-3 flex justify-end">
            <button type="button" onClick={handleOpenEvidenceMatrix} className="inline-flex items-center gap-2 rounded-lg border border-violet-200 bg-violet-50 px-3 py-2 text-xs font-semibold text-violet-800 transition-colors hover:bg-violet-100 dark:border-violet-900 dark:bg-violet-950/40 dark:text-violet-200 dark:hover:bg-violet-950/70">
              <Table size={14} /> Lập bảng tổng hợp {Math.min(new Set(sourcesMeta.map((source) => source.document_id)).size, 10)} nghiên cứu
            </button>
          </div>
        )}

        {/* ── Clinical Evidence Hierarchy Badges & One-Click APA 7th / BibTeX Citations (Proposal 5) ── */}
        {legacyFeaturesEnabled() && sourcesMeta.length > 0 && (
          <div className="mt-6 pt-5 border-t-2 border-slate-200/90 dark:border-slate-800">
            <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
              <div className="flex items-center gap-2">
                <Award size={16} className="text-teal-600 dark:text-teal-400 shrink-0" />
                <h4 className="font-bold text-xs uppercase tracking-wider text-slate-800 dark:text-slate-200">
                  Phân tầng Bằng chứng Y khoa (Oxford CEBM) & Trích dẫn Chuẩn Quốc tế ({sourcesMeta.length} nguồn)
                </h4>
              </div>
            </div>

            <div className="space-y-2.5">
              {sourcesMeta.map((src, sIdx) => {
                const isTier1 = src.authority_tier === 'tier_1' || src.cebm_level.startsWith('1');
                const isTier2 = src.authority_tier === 'tier_2' || src.cebm_level.startsWith('2');
                const badgeClass = isTier1
                  ? 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border-emerald-500/30'
                  : isTier2
                  ? 'bg-blue-500/15 text-blue-800 dark:text-blue-300 border-blue-500/30'
                  : 'bg-violet-500/15 text-violet-800 dark:text-violet-300 border-violet-500/30';

                return (
                  <div
                    key={`${src.document_id}-${sIdx}`}
                    className="p-3 rounded-xl bg-slate-50/90 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800/90 flex flex-col gap-2"
                  >
                    <div className="flex items-start justify-between gap-2 flex-wrap">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5 flex-wrap mb-1">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10.5px] font-bold border ${badgeClass}`}>
                            {src.cebm_level === 'unverified' ? '📄' : isTier1 ? '🥇' : isTier2 ? '🥈' : '🥉'} {src.cebm_label} • {src.study_design || src.authority_label}
                          </span>
                          {src.pages?.map((pNum) => (
                            <button
                              key={pNum}
                              type="button"
                              onClick={() => handleSmartCitationClick(src.filename, pNum, src.page_excerpts?.[String(pNum)] || src.title)}
                              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10.5px] font-semibold bg-teal-50 hover:bg-teal-100 dark:bg-teal-950/60 dark:hover:bg-teal-900 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800 transition-colors cursor-pointer"
                              title={`Mở PDF "${src.filename}" tại trang ${pNum} và tô sáng bằng chứng`}
                            >
                              <FileText size={10} />
                              <span>Mở PDF & Highlight Trang {pNum}</span>
                            </button>
                          ))}
                        </div>
                        <div className="font-bold text-xs text-slate-900 dark:text-slate-100">
                          {src.title}
                        </div>
                        <div className="text-[11px] text-slate-600 dark:text-slate-400 italic mt-0.5">
                          {src.apa7}
                        </div>
                      </div>

                      <div className="flex items-center gap-1.5 shrink-0">
                        <button
                          type="button"
                          onClick={() => copySourceCitation(src.document_id, src.apa7, 'apa')}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-white dark:bg-slate-800 hover:bg-teal-50 dark:hover:bg-teal-950/50 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 transition-colors cursor-pointer"
                          title="Copy trích dẫn chuẩn APA 7th Edition"
                        >
                          {copiedApaId === src.document_id ? <Check size={11} className="text-emerald-500" /> : <Copy size={11} />}
                          <span>{copiedApaId === src.document_id ? 'Đã copy APA' : 'Copy APA 7th'}</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => copySourceCitation(src.document_id, src.bibtex, 'bib')}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-white dark:bg-slate-800 hover:bg-purple-50 dark:hover:bg-purple-950/50 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 transition-colors cursor-pointer"
                          title="Copy mã trích dẫn BibTeX cho Overleaf / LaTeX"
                        >
                          {copiedBibId === src.document_id ? <Check size={11} className="text-emerald-500" /> : <Code size={11} />}
                          <span>{copiedBibId === src.document_id ? 'Đã copy .bib' : 'BibTeX'}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
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
  const [isAnalyzingFiles, setIsAnalyzingFiles] = useState(false);
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
    directUrl?: string;
    filename: string;
    title?: string;
    page: number;
    totalPages?: number | null;
    snippet?: string;
  } | null>(null);
  const [citationNotice, setCitationNotice] = useState<string | null>(null);

  const handleCitationClick = async (filename: string, page: number, snippet?: string) => {
    setCitationNotice(null);
    const inlinePdf = chatMessages
      .flatMap(message => message.attachments || [])
      .find(file => file.name.toLowerCase() === filename.toLowerCase() && file.type === 'application/pdf');
    if (inlinePdf) {
      setActivePdfViewer({
        documentId: `inline:${inlinePdf.url}`,
        directUrl: inlinePdf.url,
        filename: inlinePdf.name,
        title: inlinePdf.name,
        page,
        snippet,
      });
      return;
    }
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
        if (lookedUp.has_file === false) {
          setCitationNotice(`Đã tìm thấy hồ sơ “${lookedUp.filename}” nhưng tệp PDF hiện không khả dụng.`);
          return;
        }
        setActivePdfViewer({
          documentId: lookedUp.id,
          filename: lookedUp.filename,
          title: lookedUp.title || lookedUp.filename,
          page: page,
          totalPages: lookedUp.total_pages,
          snippet: snippet,
        });
      } else {
        setCitationNotice(`Không tìm thấy PDF “${filename}” trong thư viện tài liệu. Nếu đây là tệp đính kèm trong chat, hãy đính kèm lại sau khi tải lại trang.`);
      }
    } catch (e) {
      console.error('Error looking up document:', e);
      setCitationNotice('Không thể mở tài liệu nguồn. Hãy kiểm tra kết nối rồi thử lại.');
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
    initAuth();
    getDocuments().then(setDocuments).catch(() => {});
  }, []);

  useEffect(() => {
    loadSessions();
  }, [user?.id]);

  useEffect(() => {
    if (token) {
      getMyPlanUsage().then(setPlanUsage).catch(() => {});
      getDocuments().then(setDocuments).catch(() => {});
    }
  }, [token]);

  const loadSessions = () => {
    try {
      const saved = sessionStorage.getItem(chatSessionStorageKey());
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
      sessionStorage.setItem(chatSessionStorageKey(), JSON.stringify(next));
      return next;
    });
  };

  const createNewSession = () => {
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

  const MAX_CHAT_FILES = 20;
  const [isChatDragging, setIsChatDragging] = useState(false);

  const appendChatFiles = (fileList: FileList | File[]) => {
    const files = Array.from(fileList || []);
    if (!files.length) return;
    const valid = files.filter(f => f.type.startsWith('image/') || f.type === 'application/pdf' || f.name.match(/\.(pdf|docx?|xlsx?|jpg|jpeg|png|gif|webp|bmp)$/i));
    if (!valid.length) return;
    if (uploadedFiles.length + valid.length > MAX_CHAT_FILES) {
      setCitationNotice(`Mỗi lượt phân tích tối đa ${MAX_CHAT_FILES} tài liệu. Các tệp vượt giới hạn chưa được đính kèm.`);
    }
    setUploadedFiles(prev => {
      const remaining = Math.max(0, MAX_CHAT_FILES - prev.length);
      return [...prev, ...valid.slice(0, remaining)];
    });
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      appendChatFiles(e.target.files);
    }
    e.target.value = '';
  };

  const handleChatDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!isLoading) setIsChatDragging(true);
  };

  const handleChatDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.currentTarget.contains(e.relatedTarget as Node)) return;
    setIsChatDragging(false);
  };

  const handleChatDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsChatDragging(false);
    if (isLoading) return;
    if (e.dataTransfer?.files?.length) {
      appendChatFiles(e.dataTransfer.files);
    }
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
    if ((!input.trim() && uploadedFiles.length === 0) || isLoading) return;

    const filesToSend = [...uploadedFiles];
    const hasFilesToAnalyze = filesToSend.length > 0;
    const rawQuery = input.trim() || 'Hãy phân tích và tóm tắt nội dung chính của tài liệu đính kèm.';

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
    setIsAnalyzingFiles(hasFilesToAnalyze);

    // Inject mode instruction vào query gửi lên LLM (chỉ phía request, user vẫn thấy raw text).
    // 'basic' → trả lời ngắn gọn (2-4 câu), 'advanced' → trả lời đầy đủ, sâu, chi tiết.
    const isEnglish = !/[áàảãạâấầẩẫậăắằẳẵặéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđÁÀẢÃẠÂẤẦẨẪẬĂẮẰẲẴẶÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ]/i.test(rawQuery) &&
      /\b(what|is|how|to|the|in|of|and|a|an|depression|anxiety|cbt|ocd|bipolar|stress|hello|hi|who|why|where|affect|people|psychology)\b/i.test(rawQuery);

    const modeInstruction = isEnglish
      ? (mode === 'basic'
          ? '[System: MODE=BRIEF. Reply in about 2-4 sentences. Answer only the question and avoid unasked topics.] '
          : '[System: MODE=DEEP. Give a detailed answer. For a straightforward question, aim for 5-8 useful sentences; for a complex or comparative question, use 4-8 focused paragraphs with clear structure. Explain relevant reasoning, evidence, nuance, and limitations, and cite document page numbers. Stay strictly within the question and do not add filler.] ')
      : (mode === 'basic'
          ? '[He thong: MODE=BRIEF. Hay tra loi trong khoang 2-4 cau, dung trong tam cau hoi va khong mo rong sang chu de khac.] '
          : '[He thong: MODE=DEEP. Hay tra loi chuyen sau. Voi cau hoi don gian, huong den 5-8 cau co gia tri; voi cau hoi phuc tap hoac so sanh, trinh bay 4-8 doan co cau truc. Giai thich lap luan, bang chung, diem tinh te va gioi han lien quan; trich dan so trang tai lieu. Chi tap trung vao cau hoi, khong them noi dung lap day.] ');
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
      if (filesToSend.length > 0) {
        // Use file-chat endpoint when files are attached
        await chatFileStream({
          query: sentQuery,
          files: filesToSend,
          documentIds: docIds,
          onChunk,
          signal: abortRef.current.signal,
        });
      } else {
        await chatStream(sentQuery, docIds, onChunk, abortRef.current.signal, {
          onTelemetry: (payload) => {
            setChatMessages(prev => {
              const newPrev = prev.map(m =>
                m.id === assistantMsg.id ? { ...m, telemetryPayload: payload } : m
              );
              if (activeSessionId) updateSessionMessages(activeSessionId, newPrev);
              return newPrev;
            });
          },
        });
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
      setIsAnalyzingFiles(false);
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
        <main
          onDragOver={handleChatDragOver}
          onDragLeave={handleChatDragLeave}
          onDrop={handleChatDrop}
          className={`relative flex-1 flex flex-col min-w-0 min-h-0 bg-white dark:bg-[#0A0F1A] overflow-hidden transition-all duration-300 ${activePdfViewer ? 'hidden sm:flex' : 'flex'}`}
        >
          {isChatDragging && (
            <div className="absolute inset-3 z-50 rounded-2xl border-2 border-dashed border-teal-500 bg-teal-500/10 backdrop-blur-[2px] flex flex-col items-center justify-center pointer-events-none">
              <div className="px-5 py-3 rounded-xl bg-white/95 dark:bg-slate-900/95 shadow-lg border border-teal-500/30 text-center">
                <p className="text-sm font-semibold text-teal-600 dark:text-teal-400">
                  Thả nhiều tài liệu vào đây để đính kèm cùng lúc
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Hỗ trợ PDF, Word, Excel, Hình ảnh (tối đa 20 tệp/lượt)
                </p>
              </div>
            </div>
          )}
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
                        <span>Chế độ Khách</span>
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-300 mb-3 leading-relaxed">
                        Bạn có thể đặt câu hỏi ngay. Đăng nhập để tải tài liệu riêng lên và phân tích cùng AI.
                      </p>
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
                            telemetryPayload={msg.telemetryPayload}
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
                <div className="bg-gray-100 dark:bg-white/10 rounded-xl px-3 py-2 flex items-center gap-2">
                  {[0, 1, 2].map(i => (
                    <div
                      key={i}
                      className="w-1 h-1 rounded-full bg-gray-400 dark:bg-gray-500 animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                  {isAnalyzingFiles && <span className="text-[11px] text-gray-500 dark:text-gray-400">Đang đọc tài liệu và đối chiếu bằng chứng…</span>}
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="shrink-0 px-4 py-4 border-t border-gray-200 dark:border-white/10 bg-white dark:bg-[#0A0F1A] transition-colors">
          <div className="max-w-3xl mx-auto space-y-2">
                {/* File preview chips */}
                {uploadedFiles.length > 0 && (
                  <div className="flex flex-wrap items-center gap-2 px-1">
                    <span className="text-[11px] font-medium text-teal-600 dark:text-teal-400">
                      Đã chọn {uploadedFiles.length} tệp:
                    </span>
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
                    {uploadedFiles.length > 1 && (
                      <button
                        type="button"
                        onClick={() => setUploadedFiles([])}
                        className="text-[11px] text-red-500 hover:text-red-600 dark:text-red-400 underline ml-1"
                      >
                        Xóa tất cả
                      </button>
                    )}
                  </div>
                )}

                <div className="flex gap-2 items-center bg-white dark:bg-white/5 rounded-full border border-gray-300 dark:border-white/10 px-4 py-2 shadow-sm transition-colors">
                  {/* Hidden file input */}
                  <input
                    ref={fileInputRef}
                    id="chat-file-input"
                    name="chat-files"
                    type="file"
                    multiple
                    accept="image/jpeg,image/png,image/gif,image/webp,image/bmp,application/pdf,.pdf,.jpg,.jpeg,.png,.gif,.webp,.bmp,.doc,.docx,.xls,.xlsx"
                    onChange={handleFileSelect}
                    className="hidden"
                  />

                  {/* Upload remains account-only; guests can still use chat. */}
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isLoading}
                    className="shrink-0 p-1.5 rounded-full text-gray-400 hover:text-teal-600 dark:hover:text-teal-400 hover:bg-teal-50 dark:hover:bg-teal-900/20 transition-colors"
                    title={t.chat.attach_file}
                  >
                    <Paperclip size={16} />
                  </button>

                  <textarea
                    ref={textareaRef}
                    id="chat-message-input"
                    name="message"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                      }
                    }}
                    placeholder={`${t.chat.type_message} (kéo thả hoặc chọn nhiều tệp; tối đa 20 tệp)`}
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
                <p className="mt-1 px-3 text-[10px] text-slate-400 dark:text-slate-500">
                  Hỗ trợ đính kèm hoặc kéo thả nhiều tài liệu cùng lúc (tối đa 20 tệp/lượt). Có thể dán URL công khai vào câu hỏi.
                </p>
          </div>
        </div>
      </main>

        {/* ── Side-by-Side PDF Viewer Panel (Nhóm 4) ── */}
        {activePdfViewer && (
          <aside className="w-full sm:w-[48%] md:w-[50%] lg:w-[52%] h-full shrink-0 flex flex-col min-h-0 z-10 transition-all duration-300">
            <SideBySidePdfViewer
              documentId={activePdfViewer.documentId}
              directUrl={activePdfViewer.directUrl}
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
        title="Đăng nhập để tải tài liệu lên"
        description="Khách vẫn có thể đặt câu hỏi. Đăng nhập để tải tài liệu riêng lên và phân tích trực tiếp trong cuộc trò chuyện."
      />
      {citationNotice && (
        <div role="status" className="fixed bottom-5 right-5 z-[100] max-w-sm rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900 shadow-xl dark:border-amber-800 dark:bg-amber-950 dark:text-amber-100">
          <div className="flex items-start gap-3">
            <span className="flex-1">{citationNotice}</span>
            <button type="button" onClick={() => setCitationNotice(null)} aria-label="Đóng thông báo" className="font-bold">×</button>
          </div>
        </div>
      )}
    </div>
  );
}
