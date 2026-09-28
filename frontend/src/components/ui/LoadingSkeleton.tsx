'use client';

import React from 'react';

interface LoadingSkeletonProps {
  variant?: 'text' | 'circle' | 'rect';
  width?: string | number;
  height?: string | number;
  className?: string;
  count?: number;
}

export function LoadingSkeleton({
  variant = 'text',
  width,
  height,
  className = '',
  count = 1,
}: LoadingSkeletonProps) {
  const variantClasses = {
    text: 'h-4 rounded',
    circle: 'rounded-full',
    rect: 'rounded-xl',
  };

  const defaultDimensions = {
    text: { width: '100%', height: '16px' },
    circle: { width: '40px', height: '40px' },
    rect: { width: '100%', height: '120px' },
  };

  const computedWidth = width ?? defaultDimensions[variant].width;
  const computedHeight = height ?? defaultDimensions[variant].height;

  const style: React.CSSProperties = {
    width: typeof computedWidth === 'number' ? `${computedWidth}px` : computedWidth,
    height: typeof computedHeight === 'number' ? `${computedHeight}px` : computedHeight,
  };

  if (count > 1) {
    return (
      <div className={`space-y-3 ${className}`}>
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className={`
              shimmer
              bg-gray-200 dark:bg-gray-800
              ${variantClasses[variant]}
            `}
            style={style}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={`
        shimmer
        bg-gray-200 dark:bg-gray-800
        ${variantClasses[variant]}
        ${className}
      `}
      style={style}
    />
  );
}

// Document Card Skeleton
export function DocumentCardSkeleton() {
  return (
    <div className="neural-card p-5">
      <div className="flex items-start justify-between mb-3">
        <LoadingSkeleton variant="circle" width={40} height={40} />
        <LoadingSkeleton variant="rect" width={60} height={24} />
      </div>
      <LoadingSkeleton variant="text" width="75%" height={16} />
      <div className="mt-2">
        <LoadingSkeleton variant="text" width="50%" height={14} />
      </div>
      <div className="flex gap-2 mt-4">
        <LoadingSkeleton variant="rect" width={60} height={24} />
        <LoadingSkeleton variant="rect" width={80} height={24} />
      </div>
    </div>
  );
}

// Document List Skeleton
interface DocumentListSkeletonProps {
  count?: number;
}

export function DocumentListSkeleton({ count = 6 }: DocumentListSkeletonProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <DocumentCardSkeleton key={i} />
      ))}
    </div>
  );
}

// Chat Message Skeleton
export function ChatMessageSkeleton({ isUser = false }: { isUser?: boolean }) {
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <LoadingSkeleton
        variant="circle"
        width={40}
        height={40}
        className={isUser ? 'order-2' : ''}
      />
      <div className={`flex-1 max-w-[70%] ${isUser ? 'order-1' : ''}`}>
        <div
          className={`
            p-4 rounded-2xl
            bg-gray-100 dark:bg-gray-800
          `}
        >
          <div className="space-y-2">
            <LoadingSkeleton variant="text" width="90%" />
            <LoadingSkeleton variant="text" width="75%" />
            {!isUser && <LoadingSkeleton variant="text" width="60%" />}
          </div>
        </div>
      </div>
    </div>
  );
}

// Chat Thread Skeleton
export function ChatThreadSkeleton() {
  return (
    <div className="space-y-6">
      <ChatMessageSkeleton />
      <ChatMessageSkeleton isUser />
      <ChatMessageSkeleton />
      <ChatMessageSkeleton />
      <ChatMessageSkeleton isUser />
    </div>
  );
}

// Feature Card Skeleton
export function FeatureCardSkeleton() {
  return (
    <div className="neural-card p-6">
      <div className="flex items-center gap-4 mb-4">
        <LoadingSkeleton variant="rect" width={48} height={48} />
        <div className="flex-1 space-y-2">
          <LoadingSkeleton variant="text" width="60%" height={16} />
          <LoadingSkeleton variant="text" width="40%" height={14} />
        </div>
      </div>
      <div className="space-y-2">
        <LoadingSkeleton variant="text" />
        <LoadingSkeleton variant="text" width="85%" />
        <LoadingSkeleton variant="text" width="70%" />
      </div>
    </div>
  );
}

// Table Row Skeleton
interface TableSkeletonProps {
  rows?: number;
  columns?: number;
}

export function TableSkeleton({ rows = 5, columns = 5 }: TableSkeletonProps) {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div className={`grid gap-4 grid-cols-${columns} px-4 py-3`}>
        {Array.from({ length: columns }).map((_, i) => (
          <LoadingSkeleton key={i} variant="text" height={14} />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className={`grid gap-4 grid-cols-${columns} px-4 py-3`}>
          {Array.from({ length: columns }).map((_, colIndex) => (
            <LoadingSkeleton key={colIndex} variant="text" />
          ))}
        </div>
      ))}
    </div>
  );
}

// Stats Card Skeleton
export function StatsCardSkeleton() {
  return (
    <div className="stat-card">
      <LoadingSkeleton variant="text" width={80} height={36} className="mx-auto mb-2" />
      <LoadingSkeleton variant="text" width={100} height={14} className="mx-auto" />
    </div>
  );
}

// Inline Skeleton (for inline content)
export function InlineSkeleton({ width = 100 }: { width?: number | string }) {
  return (
    <LoadingSkeleton
      variant="text"
      width={width}
      height={14}
      className="inline-block"
    />
  );
}