'use client';

import React, { useMemo } from 'react';
import katex from 'katex';

interface KatexMathProps {
  math: string;
  block?: boolean;
  className?: string;
}

export const KatexMath: React.FC<KatexMathProps> = ({
  math,
  block = false,
  className = '',
}) => {
  const html = useMemo(() => {
    try {
      return katex.renderToString(math.trim(), {
        displayMode: block,
        throwOnError: false,
        strict: false,
      });
    } catch (e) {
      console.warn('KaTeX render error:', e);
      return null;
    }
  }, [math, block]);

  if (!html) {
    return <code className={`font-mono text-xs ${className}`}>{math}</code>;
  }

  if (block) {
    return (
      <div
        className={`my-3 py-2 px-3 rounded-lg bg-gray-50/70 dark:bg-gray-800/40 border border-gray-200/60 dark:border-white/5 overflow-x-auto text-center ${className}`}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    );
  }

  return (
    <span
      className={`inline-block px-1 ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};
