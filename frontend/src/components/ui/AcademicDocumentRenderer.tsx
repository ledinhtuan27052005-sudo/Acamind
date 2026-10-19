'use client';

import React from 'react';
import { FileText, Globe, Quote, BookOpen, Table } from 'lucide-react';
import { KatexMath } from '@/components/ui/KatexMath';
import { FigureViewer } from '@/components/ui/FigureViewer';
import { MermaidRenderer } from '@/components/ui/MermaidRenderer';

/**
 * Strips raw Markdown formatting syntax (#, **, *, __, `, ~~, >) from a single-line or short string
 * so plain text UI elements (table cells, previews, summaries) look like clean PDF text.
 */
export function cleanMarkdownText(raw?: string | null): string {
  if (!raw) return '';
  return raw
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/\*\*\*(.+?)\*\*\*/g, '$1')
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/__(.+?)__/g, '$1')
    .replace(/(?:\*([^\*\n]+?)\*|_([^\_\n]+?)_)/g, '$1$2')
    .replace(/~~(.+?)~~/g, '$1')
    .replace(/`([^`\n]+?)`/g, '$1')
    .replace(/^\s*>\s?/gm, '')
    .replace(/\*{2,}/g, '')
    .replace(/`+/g, '')
    .trim();
}

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
  rows?: TableRow[];
  headerRow?: TableRow;
  src?: string;
  caption?: string;
  docFilename?: string;
  pageNumber?: number;
  language?: string;
}

function parseTableRow(line: string): TableCell[] {
  return line
    .split('|')
    .filter((_, i, arr) => i > 0 && i < arr.length - 1)
    .map((cell) => {
      const trimmed = cell.trim();
      const boldMatch = trimmed.match(/^\*\*(.+)\*\*$/);
      return {
        content: boldMatch ? boldMatch[1] : trimmed,
        isBold: !!boldMatch,
      };
    });
}

function isTableRow(line: string): boolean {
  const trimmed = line.trim();
  return trimmed.startsWith('|') && trimmed.endsWith('|') && trimmed.includes('|');
}

function isTableSeparator(line: string): boolean {
  const trimmed = line.trim();
  return /^\|[\s\-:|]+\|$/.test(trimmed);
}

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

  if (citePart) {
    const pageMatch = citePart.match(/([^\n]+?)\s*[-–—,:]\s*(?:Page|Trang|tr\.?|p\.?|pp\.?)\s*(\d+)/i);
    if (pageMatch) {
      docFilename = pageMatch[1].trim();
      pageNumber = parseInt(pageMatch[2], 10);
    }
  }

  if (!pageNumber) {
    const pMatch = src.match(/[\/_]p(\d+)_[a-zA-Z0-9_]+\.png/i);
    if (pMatch) {
      pageNumber = parseInt(pMatch[1], 10);
    }
  }

  if (!pageNumber && caption) {
    const capMatch = caption.match(/(?:Trang|Page|tr\.)\s*(\d+)/i);
    if (capMatch) {
      pageNumber = parseInt(capMatch[1], 10);
    }
  }

  return { src, caption, docFilename, pageNumber };
}

export function parseAcademicBlocks(content: string): StructuredItem[] {
  const lines = (content || '').split('\n');
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

    if (isTableRow(trimmed)) {
      pendingTableRows.push(trimmed);
      continue;
    } else {
      flushPendingTable();
    }

    if (!trimmed) continue;

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

    if (/^(\-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      result.push({ type: 'divider' });
      continue;
    }

    if (trimmed.startsWith('>')) {
      const quoteContent = trimmed.replace(/^>\s*/, '').replace(/^#+/, '').trim();
      result.push({
        type: 'blockquote',
        content: quoteContent,
      });
      continue;
    }

    const headingMatch = trimmed.match(/^(#{1,6})\s*(.+)$/);
    if (headingMatch) {
      const cleanHeading = headingMatch[2].replace(/\s*#+\s*$/, '').trim();
      result.push({
        type: 'heading',
        level: headingMatch[1].length,
        content: cleanHeading,
      });
      continue;
    }

    const numberedMatch = trimmed.match(/^(\d+[\.\)]|[a-zA-Z]\)|[ivxIVX]+[\.\)])\s+(.*)$/);
    if (numberedMatch) {
      result.push({
        type: 'numbered',
        numberPrefix: numberedMatch[1],
        content: numberedMatch[2].replace(/^#{1,6}\s+/, ''),
      });
      continue;
    }

    const bulletMatch = trimmed.match(/^[-*+•—–▪✦✓]\s+(.*)$/);
    if (bulletMatch) {
      result.push({
        type: 'bullet',
        content: bulletMatch[1].replace(/^#{1,6}\s+/, ''),
      });
      continue;
    }

    result.push({
      type: 'text',
      content: trimmed,
    });
  }

  flushPendingTable();

  if (inCodeBlock && codeBlockLines.length > 0) {
    if (codeBlockLang === 'mermaid') {
      result.push({ type: 'mermaid', content: codeBlockLines.join('\n').trim() });
    } else {
      result.push({ type: 'code', language: codeBlockLang, content: codeBlockLines.join('\n') });
    }
  }

  if (inMathBlock && mathLines.length > 0) {
    result.push({ type: 'math_block', content: mathLines.join('\n') });
  }

  return result;
}

function renderFormattedInlineTokens(rawText: string, keyPrefix: string): React.ReactNode[] {
  if (!rawText) return [];
  // Normalize any triple asterisks or double underscores into standard bold/italic,
  // and strip any stray unclosed markdown tokens at boundaries
  const tokenRegex = /(\*\*\*[^\*\n]+?\*\*\*|\*\*[^\*\n]+?\*\*|__[^_\n]+?__|\*[^\*\n]+?\*|_[^_\n]+?_|\`[^\`\n]+?\`|\$[^\$\n]+?\$)/g;
  const parts = rawText.split(tokenRegex);

  return parts.map((part, idx) => {
    if (!part) return null;
    const k = `${keyPrefix}-tk-${idx}`;

    if (part.startsWith('***') && part.endsWith('***') && part.length > 6) {
      return (
        <strong key={k} className="font-bold italic text-slate-900 dark:text-white">
          {part.slice(3, -3)}
        </strong>
      );
    }
    if (
      (part.startsWith('**') && part.endsWith('**') && part.length > 4) ||
      (part.startsWith('__') && part.endsWith('__') && part.length > 4)
    ) {
      const inner = part.slice(2, -2);
      return (
        <strong key={k} className="font-bold text-slate-900 dark:text-white">
          {renderFormattedInlineTokens(inner, `${k}-b`)}
        </strong>
      );
    }
    if (
      (part.startsWith('*') && part.endsWith('*') && part.length > 2) ||
      (part.startsWith('_') && part.endsWith('_') && part.length > 2)
    ) {
      const inner = part.slice(1, -1);
      return (
        <em key={k} className="italic text-slate-800 dark:text-slate-200">
          {inner}
        </em>
      );
    }
    if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
      const inner = part.slice(1, -1);
      return (
        <span
          key={k}
          className="px-1.5 py-0.5 mx-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-semibold text-[0.92em]"
        >
          {inner}
        </span>
      );
    }
    if (part.startsWith('$') && part.endsWith('$') && part.length > 2) {
      const mathStr = part.slice(1, -1);
      return <KatexMath key={k} math={mathStr} block={false} />;
    }

    // Strip any leftover stray markdown symbols (e.g. unclosed **, ###, `)
    const cleaned = part
      .replace(/^#{1,6}\s+/g, '')
      .replace(/\*{2,}/g, '')
      .replace(/`+/g, '');
    return <span key={k}>{cleaned}</span>;
  });
}

export function renderAcademicRichText({
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

  while ((match = bracketRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      const before = text.slice(lastIndex, match.index);
      elements.push(...renderFormattedInlineTokens(before, `before-${lastIndex}`));
    }

    const bracketInner = match[1].trim();

    // 1. Web Source: [Source: https://...] or [https://...]
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

    // 2. Academic Page Citation: [filename.pdf - Page 3], [filename.pdf, Trang 3], [filename.pdf - tr. 3]
    if (/(?:Page|Trang|tr\.?|p\.?|pp\.?)\s*\d+/i.test(bracketInner) || /Sheet\s*:/i.test(bracketInner)) {
      const subItems = bracketInner.split(';');
      const citationButtons: React.ReactNode[] = [];

      let contextSnippet = '';
      const textBefore = text.slice(0, match.index).trim();
      if (textBefore) {
        const cleanBefore = cleanMarkdownText(textBefore.replace(/\[[^\]]+\]/g, ''));
        const sentences = cleanBefore.split(/(?<=[.!?\n])\s+/);
        let candidate = sentences[sentences.length - 1] || cleanBefore;
        if (sentences.length >= 2 && candidate.length < 25) {
          candidate = `${sentences[sentences.length - 2]} ${candidate}`.trim();
        }
        if (candidate.length > 260) {
          const words = candidate.split(/\s+/);
          candidate = words.slice(-35).join(' ');
        }
        contextSnippet = candidate.trim();
      }

      if (!contextSnippet) {
        contextSnippet = cleanMarkdownText(text.replace(/\[[^\]]+\]/g, '')).slice(0, 180);
      }

      subItems.forEach((sub, subIdx) => {
        const pageMatch = sub.match(/([^\n]+?)\s*(?:[-–—,:]|\s+)\s*(?:Page|Trang|tr\.?|p\.?|pp\.?)\s*(\d+)/i);
        const sheetMatch = sub.match(/([^-\n]+?)\s*-\s*Sheet\s*:\s*([^\]\n;]+)/i);

        if (sheetMatch) {
          const rawFilename = sheetMatch[1].trim();
          const sheetName = sheetMatch[2].trim();
          const shortName = rawFilename.length > 20 ? rawFilename.slice(0, 18) + '…' : rawFilename;
          citationButtons.push(
            <span
              key={`cite-sheet-${match!.index}-${subIdx}`}
              className="inline-flex items-center gap-1.5 px-2 py-0.5 mx-1 my-0.5 rounded-md text-[11.5px] font-medium bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-200 border border-emerald-300 dark:border-emerald-700/60 shadow-2xs select-none"
            >
              <Table size={11} className="text-emerald-600 dark:text-emerald-400 shrink-0" />
              <span className="font-semibold truncate max-w-[130px]">{shortName}</span>
              <span className="bg-emerald-200/80 dark:bg-emerald-800/70 px-1.5 py-0.2 rounded text-[10px] font-mono font-bold">
                Sheet: {sheetName}
              </span>
            </span>
          );
        } else if (pageMatch) {
          const rawFilename = cleanMarkdownText(pageMatch[1]);
          const pageNum = parseInt(pageMatch[2], 10);
          const shortName = rawFilename.length > 24 ? rawFilename.slice(0, 21) + '…' : rawFilename;

          citationButtons.push(
            <button
              key={`cite-${match!.index}-${subIdx}`}
              type="button"
              onClick={() => onCitationClick?.(rawFilename, pageNum, contextSnippet)}
              className={`inline-flex items-center gap-1.5 px-2 py-0.5 mx-1 my-0.5 rounded-md text-[11.5px] font-medium bg-slate-100 hover:bg-teal-50 dark:bg-slate-800/90 dark:hover:bg-teal-950/70 text-slate-700 hover:text-teal-700 dark:text-slate-200 dark:hover:text-teal-300 border border-slate-300/80 hover:border-teal-400 dark:border-slate-700 dark:hover:border-teal-600 transition-all group shadow-2xs select-none ${
                onCitationClick ? 'hover:scale-105 active:scale-95 cursor-pointer' : 'cursor-default'
              }`}
              title={
                onCitationClick
                  ? `Nhấn để mở đối chiếu PDF "${rawFilename}" tại trang ${pageNum} (Tự động bôi vàng đoạn trích)`
                  : `Trích dẫn từ "${rawFilename}" — Trang ${pageNum}`
              }
            >
              <FileText size={11} className="text-teal-600 dark:text-teal-400 shrink-0" />
              <span className="font-semibold truncate max-w-[150px]">{shortName}</span>
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

    // 3. Regular brackets
    elements.push(
      <span key={`bracket-${match.index}`}>
        [{renderFormattedInlineTokens(bracketInner, `inner-${match.index}`)}]
      </span>
    );
    lastIndex = bracketRegex.lastIndex;
  }

  if (lastIndex < text.length) {
    const after = text.slice(lastIndex);
    elements.push(...renderFormattedInlineTokens(after, `after-${lastIndex}`));
  }

  return <span className={className}>{elements}</span>;
}

export function AcademicDocumentRenderer({
  content,
  onCitationClick,
  className = '',
}: {
  content: string;
  onCitationClick?: (filename: string, page: number, snippet?: string) => void;
  className?: string;
}) {
  const structured = parseAcademicBlocks(content);

  return (
    <div className={`structured-content text-[13.5px] leading-relaxed text-slate-800 dark:text-slate-200 space-y-2.5 ${className}`}>
      {structured.map((item, idx) => (
        <div key={idx}>
          {/* Heading */}
          {item.type === 'heading' && (
            /^(?:References|Tài liệu tham khảo)$/i.test(cleanMarkdownText(item.content)) ? (
              <div className="mt-6 pt-4 border-t-2 border-slate-300 dark:border-slate-700/80 mb-3">
                <div className="flex items-center gap-2">
                  <BookOpen size={16} className="text-teal-600 dark:text-teal-400 shrink-0" />
                  <h3 className="font-bold text-sm tracking-wider uppercase text-slate-900 dark:text-slate-100">
                    {cleanMarkdownText(item.content)}
                  </h3>
                </div>
              </div>
            ) : item.level && item.level <= 2 ? (
              <div className="mt-5 mb-2.5 pb-1.5 border-b border-slate-200 dark:border-slate-700/80">
                <h3 className="font-bold text-[15px] sm:text-[16px] text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
                  {renderAcademicRichText({ text: item.content, onCitationClick })}
                </h3>
              </div>
            ) : (
              <h4 className="font-semibold text-[13.5px] sm:text-[14px] text-slate-900 dark:text-slate-100 mt-3.5 mb-1.5 flex items-center gap-1.5">
                {renderAcademicRichText({ text: item.content, onCitationClick })}
              </h4>
            )
          )}

          {/* Numbered item */}
          {item.type === 'numbered' && (
            <div className="flex items-start gap-2.5 my-1 text-[13.5px] leading-relaxed">
              <span className="font-bold text-slate-700 dark:text-slate-300 min-w-[22px] text-right shrink-0 select-none">
                {item.numberPrefix}
              </span>
              <div className="flex-1 min-w-0 text-slate-800 dark:text-slate-200">
                {renderAcademicRichText({ text: item.content, onCitationClick })}
              </div>
            </div>
          )}

          {/* Bullet point */}
          {item.type === 'bullet' && (
            <div className="flex items-start gap-2.5 my-1 text-[13.5px] leading-relaxed">
              <span className="text-teal-600 dark:text-teal-400 font-bold shrink-0 mt-0.5 select-none text-[15px] leading-none">
                •
              </span>
              <div className="flex-1 min-w-0 text-slate-800 dark:text-slate-200">
                {renderAcademicRichText({ text: item.content, onCitationClick })}
              </div>
            </div>
          )}

          {/* Blockquote */}
          {item.type === 'blockquote' && item.content && (
            <div className="my-3 p-3.5 sm:p-4 rounded-r-xl border-l-[3.5px] border-teal-600 dark:border-teal-500 bg-teal-50/40 dark:bg-teal-950/20 border border-teal-200/50 dark:border-teal-800/40 shadow-2xs">
              <div className="flex items-center gap-1.5 text-[11px] font-bold text-teal-800 dark:text-teal-300 uppercase tracking-wider mb-1">
                <Quote size={13} className="shrink-0" />
                <span>Trích lục từ tài liệu gốc</span>
              </div>
              <div className="text-[13px] sm:text-[13.5px] italic text-slate-700 dark:text-slate-300 leading-relaxed">
                “{renderAcademicRichText({ text: item.content, onCitationClick })}”
              </div>
            </div>
          )}

          {/* Divider */}
          {item.type === 'divider' && (
            <div className="my-4 border-t border-slate-200 dark:border-slate-800" />
          )}

          {/* Math Block */}
          {item.type === 'math_block' && item.content && (
            <KatexMath math={item.content} block={true} />
          )}

          {/* Mermaid Flowchart */}
          {item.type === 'mermaid' && item.content && (
            <MermaidRenderer chart={item.content} />
          )}

          {/* Figure */}
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
            <div className="my-2.5 p-3 rounded-lg bg-slate-100 dark:bg-slate-800/90 text-slate-800 dark:text-slate-100 font-sans text-xs overflow-x-auto border border-slate-200 dark:border-slate-700 shadow-xs whitespace-pre-wrap">
              {cleanMarkdownText(item.content)}
            </div>
          )}

          {/* Publication Table */}
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
                        {renderAcademicRichText({ text: cell.content, onCitationClick })}
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
                          {renderAcademicRichText({ text: cell.content, onCitationClick })}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Regular Paragraph */}
          {item.type === 'text' && (
            <p className="text-[13.5px] text-slate-800 dark:text-slate-200 leading-relaxed my-1.5 text-justify">
              {renderAcademicRichText({ text: item.content, onCitationClick })}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
