'use client';

import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { ArrowRight, Workflow } from 'lucide-react';

interface MermaidRendererProps {
  chart: string;
}

/**
 * Xóa bỏ các phần tử lỗi (Error SVG / Bomb icons) mà thư viện Mermaid tự ý gắn vào document.body
 */
function cleanupMermaidRogueElements() {
  if (typeof document === 'undefined') return;
  try {
    const rogueElements = document.querySelectorAll(
      'body > svg[id^="mermaid-"], body > [id^="dmermaid-"], body > .error-icon, body > svg[aria-roledescription="error"], body > div[id^="dmermaid-"]'
    );
    rogueElements.forEach((el) => el.remove());
  } catch {
    // Ignore cleanup errors
  }
}

/**
 * Tự động chuẩn hóa và sửa các lỗi cú pháp Mermaid thường gặp từ LLM
 */
function sanitizeMermaidChart(rawChart: string): string {
  if (!rawChart) return '';
  let chart = rawChart.trim();

  // 1. Gỡ bỏ code fence markdown nếu còn sót
  chart = chart.replace(/^```(?:mermaid)?/i, '').replace(/```$/i, '').trim();

  // 2. Kiểm tra header diagram
  const validHeaders = /^(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|journey|gantt|pie|gitGraph|mindmap)/m;
  if (!validHeaders.test(chart)) {
    chart = `flowchart TD\n${chart}`;
  } else if (/^graph\s+(TD|TB|BT|RL|LR)/m.test(chart)) {
    // Chuyển graph sang flowchart vì flowchart hỗ trợ Unicode tiếng Việt và ký tự đặc biệt tốt hơn nhiều
    chart = chart.replace(/^graph\s+/m, 'flowchart ');
  }

  // 3. Xử lý từng dòng để sửa các lỗi cú pháp
  const lines = chart.split('\n');
  const sanitizedLines: string[] = [];

  for (const line of lines) {
    let l = line.trim();
    if (!l) continue;

    // Giữ nguyên dòng tiêu đề
    if (validHeaders.test(l)) {
      sanitizedLines.push(l);
      continue;
    }

    // Sửa mũi tên: thay thế ' -> ' bằng ' --> '
    l = l.replace(/\s+->\s+/g, ' --> ');
    l = l.replace(/\s+-\.->\s+/g, ' -.-> ');
    l = l.replace(/\s+==>\s+/g, ' ==> ');

    // Sửa các nhãn node dạng id[Nội dung không có nháy kép] -> id["Nội dung an toàn"]
    // Điều này tránh lỗi khi nội dung có dấu ngoặc tròn ( ), dấu sao *, dấu hai chấm :
    l = l.replace(/([a-zA-Z0-9_-]+)\[([^"\]]+)\]/g, (_, id, text) => {
      const safeText = text.replace(/"/g, "'").trim();
      return `${id}["${safeText}"]`;
    });

    // Sửa các nhãn node dạng id(Nội dung) -> id("Nội dung an toàn")
    l = l.replace(/([a-zA-Z0-9_-]+)\(([^"\)]+)\)/g, (_, id, text) => {
      const safeText = text.replace(/"/g, "'").trim();
      return `${id}("${safeText}")`;
    });

    // Sửa lỗi hai node liền kề trên một dòng bị thiếu mũi tên (ví dụ: ] B[)
    l = l.replace(/\]\s*([a-zA-Z0-9_-]+)\[/g, '] --> $1[');

    sanitizedLines.push(`  ${l}`);
  }

  return sanitizedLines.join('\n');
}

/**
 * Trích xuất chuỗi các bước (steps) từ cú pháp sơ đồ khi Mermaid không thể render
 */
function extractFallbackSteps(rawChart: string): string[] {
  const steps: string[] = [];
  const lines = rawChart.split('\n');

  for (const line of lines) {
    const parts = line.split(/-->|->|==>|-\.->/);
    for (const part of parts) {
      // Tìm nhãn bên trong ["..."] hoặc [...] hoặc (...)
      const quoteMatch = part.match(/["']([^"']+)["']/);
      if (quoteMatch && quoteMatch[1].trim()) {
        const text = quoteMatch[1].trim();
        if (!steps.includes(text)) steps.push(text);
        continue;
      }
      const bracketMatch = part.match(/\[([^\]]+)\]/);
      if (bracketMatch && bracketMatch[1].trim()) {
        const text = bracketMatch[1].replace(/["']/g, '').trim();
        if (!steps.includes(text)) steps.push(text);
        continue;
      }
      const parenMatch = part.match(/\(([^\)]+)\)/);
      if (parenMatch && parenMatch[1].trim()) {
        const text = parenMatch[1].replace(/["']/g, '').trim();
        if (!steps.includes(text)) steps.push(text);
      }
    }
  }

  return steps;
}

export const MermaidRenderer: React.FC<MermaidRendererProps> = ({ chart }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>('');
  const [renderFailed, setRenderFailed] = useState<boolean>(false);

  useEffect(() => {
    // Khởi tạo Mermaid với chế độ suppressErrorRendering: true để tuyệt đối KHÔNG gắn icon bom lỗi vào DOM
    mermaid.initialize({
      startOnLoad: false,
      suppressErrorRendering: true,
      theme: 'neutral',
      securityLevel: 'loose',
      fontFamily: 'var(--font-inter), sans-serif',
      flowchart: {
        htmlLabels: true,
        curve: 'basis',
      },
    });

    let isMounted = true;

    const renderChart = async () => {
      cleanupMermaidRogueElements();

      if (!chart || !chart.trim()) {
        if (isMounted) setRenderFailed(true);
        return;
      }

      const sanitized = sanitizeMermaidChart(chart);
      const uniqueId = `mermaid-${Math.random().toString(36).substring(2, 9)}`;

      try {
        // Kiểm tra tính hợp lệ trước khi render
        const isValid = await mermaid.parse(sanitized, { suppressErrors: true }).catch(() => false);
        if (!isValid) {
          cleanupMermaidRogueElements();
          if (isMounted) {
            setRenderFailed(true);
            setSvg('');
          }
          return;
        }

        const { svg: renderedSvg } = await mermaid.render(uniqueId, sanitized);
        cleanupMermaidRogueElements();

        if (isMounted) {
          setSvg(renderedSvg);
          setRenderFailed(false);
        }
      } catch (err) {
        cleanupMermaidRogueElements();
        console.warn('Mermaid rendering caught and handled gracefully:', err);
        if (isMounted) {
          setRenderFailed(true);
          setSvg('');
        }
      }
    };

    renderChart();

    return () => {
      isMounted = false;
      cleanupMermaidRogueElements();
    };
  }, [chart]);

  // Nếu Mermaid không parse được -> Hiển thị sơ đồ dạng thẻ tiến trình (Visual Process Cards) thanh lịch, không lỗi
  if (renderFailed || (!svg && chart)) {
    const steps = extractFallbackSteps(chart);
    if (steps.length > 0) {
      return (
        <div className="my-3 p-3.5 sm:p-4 rounded-xl bg-gradient-to-r from-teal-50/60 via-slate-50 to-teal-50/40 dark:from-teal-950/20 dark:via-slate-900/40 dark:to-teal-950/10 border border-teal-200/80 dark:border-teal-800/60 shadow-2xs">
          <div className="flex items-center gap-1.5 mb-2.5 text-xs font-semibold text-teal-800 dark:text-teal-300 uppercase tracking-wider">
            <Workflow size={13} className="text-teal-600 dark:text-teal-400" />
            <span>Sơ đồ tiến trình & Mối liên hệ logic</span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {steps.map((step, idx) => (
              <React.Fragment key={idx}>
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200/90 dark:border-slate-700 text-xs font-medium text-slate-800 dark:text-slate-200 shadow-2xs">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-500 shrink-0"></span>
                  <span>{step}</span>
                </div>
                {idx < steps.length - 1 && (
                  <ArrowRight size={13} className="text-teal-500 dark:text-teal-400 shrink-0" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      );
    }

    // Nếu không trích xuất được step nào, hiển thị khối ghi chú nhẹ nhàng thay vì bom lỗi
    return (
      <div className="my-2 px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-400 flex items-center gap-2">
        <Workflow size={14} className="text-teal-600 dark:text-teal-400 shrink-0" />
        <span>Sơ đồ tiến trình mô tả quy trình can thiệp và mối liên hệ trong nghiên cứu.</span>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="my-3 p-3 sm:p-4 rounded-xl bg-white dark:bg-[#151a23] border border-slate-200 dark:border-slate-800 overflow-x-auto flex justify-center shadow-xs select-none"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
};
