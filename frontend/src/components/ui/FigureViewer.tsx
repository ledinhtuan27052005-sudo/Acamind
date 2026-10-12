'use client';

import React, { useState } from 'react';
import { ZoomIn, X, ExternalLink, Download, FileText } from 'lucide-react';

interface FigureViewerProps {
  src: string;
  alt?: string;
  caption?: string;
  docFilename?: string;
  pageNumber?: number;
  onCitationClick?: (filename: string, page: number, snippet?: string) => void;
}

export const FigureViewer: React.FC<FigureViewerProps> = ({
  src,
  alt = 'Sơ đồ từ tài liệu',
  caption,
  docFilename,
  pageNumber,
  onCitationClick,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);

  // Normalize API backend URL if relative
  const imageUrl = src.startsWith('http')
    ? src
    : src.startsWith('/')
    ? `http://localhost:8000${src}`
    : `http://localhost:8000/${src}`;

  const displayCaption = caption || alt || 'Sơ đồ tài liệu';

  return (
    <>
      <div className="my-4 rounded-xl border border-gray-200 dark:border-white/10 bg-gray-50/60 dark:bg-[#161e2e] p-2.5 shadow-xs transition-all hover:shadow-md group">
        <div className="relative overflow-hidden rounded-lg bg-white dark:bg-black/30 flex items-center justify-center min-h-[140px] cursor-pointer"
             onClick={() => setIsOpen(true)}>
          <img
            src={imageUrl}
            alt={displayCaption}
            className="max-h-[380px] w-auto object-contain transition-transform duration-300 group-hover:scale-[1.02]"
            loading="lazy"
          />

          {/* Quick Action Overlay */}
          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setIsOpen(true);
              }}
              className="p-2 rounded-lg bg-white/90 dark:bg-gray-800/90 text-gray-800 dark:text-white hover:bg-white text-xs font-medium flex items-center gap-1.5 shadow-md backdrop-blur-xs transition-transform hover:scale-105"
            >
              <ZoomIn size={14} />
              <span>Phóng to</span>
            </button>

            {docFilename && pageNumber && onCitationClick && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onCitationClick(docFilename, pageNumber, displayCaption);
                }}
                className="p-2 rounded-lg bg-teal-600/90 hover:bg-teal-600 text-white text-xs font-medium flex items-center gap-1.5 shadow-md backdrop-blur-xs transition-transform hover:scale-105"
              >
                <FileText size={14} />
                <span>Xem trên PDF gốc (P.{pageNumber})</span>
              </button>
            )}
          </div>
        </div>

        {/* Caption & Metadata */}
        <div className="mt-2.5 px-1 flex flex-wrap items-center justify-between gap-2 text-xs text-gray-600 dark:text-gray-300">
          <p className="font-medium italic leading-snug flex-1">
            📷 {displayCaption}
          </p>

          {docFilename && pageNumber && onCitationClick && (
            <button
              type="button"
              onClick={() => onCitationClick(docFilename, pageNumber, displayCaption)}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-teal-50 hover:bg-teal-100 dark:bg-teal-950/60 dark:hover:bg-teal-900/80 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-700/60 transition-colors shrink-0"
              title={`Mở trang ${pageNumber} trong ${docFilename}`}
            >
              <FileText size={11} />
              <span>Trang {pageNumber}</span>
            </button>
          )}
        </div>
      </div>

      {/* Lightbox Modal */}
      {isOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex flex-col items-center justify-center p-4"
          onClick={() => setIsOpen(false)}
        >
          {/* Header bar */}
          <div
            className="w-full max-w-5xl flex items-center justify-between text-white pb-3 select-none"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-2 truncate">
              <span className="font-semibold text-sm truncate max-w-lg">
                {displayCaption}
              </span>
              {docFilename && pageNumber && (
                <span className="text-xs text-gray-300 bg-white/10 px-2 py-0.5 rounded">
                  {docFilename} (Trang {pageNumber})
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setZoomLevel((z) => Math.max(0.5, z - 0.25))}
                className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs font-mono"
                title="Thu nhỏ"
              >
                -
              </button>
              <span className="text-xs font-mono">{Math.round(zoomLevel * 100)}%</span>
              <button
                type="button"
                onClick={() => setZoomLevel((z) => Math.min(3, z + 0.25))}
                className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs font-mono"
                title="Phóng to"
              >
                +
              </button>

              <a
                href={imageUrl}
                download
                target="_blank"
                rel="noreferrer"
                className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 ml-2"
                title="Tải ảnh về máy"
              >
                <Download size={16} />
              </a>

              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg bg-red-600/80 hover:bg-red-600 ml-2"
                title="Đóng (Esc)"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Image Display */}
          <div
            className="relative max-w-5xl max-h-[82vh] overflow-auto rounded-xl bg-neutral-900/60 flex items-center justify-center p-2"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={imageUrl}
              alt={displayCaption}
              style={{ transform: `scale(${zoomLevel})`, transition: 'transform 0.15s ease' }}
              className="max-h-[78vh] w-auto object-contain rounded select-none"
            />
          </div>
        </div>
      )}
    </>
  );
};
