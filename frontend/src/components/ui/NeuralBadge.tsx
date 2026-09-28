'use client';

import React from 'react';

interface NeuralBadgeProps {
  variant?: 'default' | 'neural' | 'cortex' | 'dopamine' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md';
  children: React.ReactNode;
  className?: string;
  dot?: boolean;
  pulse?: boolean;
  icon?: React.ReactNode;
  style?: React.CSSProperties;
}

export function NeuralBadge({
  variant = 'default',
  size = 'md',
  children,
  className = '',
  dot = false,
  pulse = false,
  icon,
  style,
}: NeuralBadgeProps) {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-[10px]',
    md: 'px-2.5 py-1 text-xs',
  };

  const variantClasses = {
    default: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
    neural: 'bg-neural-100 text-neural-700 dark:bg-neural-900/50 dark:text-neural-300',
    cortex: 'bg-cortex-100 text-cortex-700 dark:bg-cortex-900/50 dark:text-cortex-300',
    dopamine: 'bg-dopamine-100 text-dopamine-700 dark:bg-dopamine-900/50 dark:text-dopamine-300',
    success: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300',
    warning: 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300',
    error: 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-300',
    info: 'bg-sky-100 text-sky-700 dark:bg-sky-900/50 dark:text-sky-300',
  };

  const dotColors = {
    default: 'bg-gray-500',
    neural: 'bg-neural-500',
    cortex: 'bg-cortex-500',
    dopamine: 'bg-dopamine-500',
    success: 'bg-emerald-500',
    warning: 'bg-amber-500',
    error: 'bg-red-500',
    info: 'bg-sky-500',
  };

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 rounded-full font-medium
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        ${className}
      `}
      style={style}
    >
      {dot && (
        <span
          className={`
            w-1.5 h-1.5 rounded-full ${dotColors[variant]}
            ${pulse ? 'animate-pulse' : ''}
          `}
        />
      )}
      {icon && <span className="flex-shrink-0">{icon}</span>}
      {children}
    </span>
  );
}

// Status Badge (for document status, etc.)
interface StatusBadgeProps {
  status: 'processing' | 'ready' | 'error' | 'pending';
  children?: React.ReactNode;
  className?: string;
}

export function StatusBadge({ status, children, className = '' }: StatusBadgeProps) {
  const statusConfig = {
    processing: {
      variant: 'warning' as const,
      icon: (
        <svg className="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      ),
      animation: 'badge-processing',
      label: children || 'Processing',
    },
    ready: {
      variant: 'success' as const,
      icon: (
        <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M20 6L9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ),
      animation: 'badge-ready',
      label: children || 'Ready',
    },
    error: {
      variant: 'error' as const,
      icon: (
        <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="15" y1="9" x2="9" y2="15" />
          <line x1="9" y1="9" x2="15" y2="15" />
        </svg>
      ),
      animation: '',
      label: children || 'Error',
    },
    pending: {
      variant: 'default' as const,
      icon: null,
      animation: '',
      label: children || 'Pending',
    },
  };

  const config = statusConfig[status];

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium
        ${config.animation ? `animate-${config.animation.replace('badge-', '')}` : ''}
        ${className}
      `}
    >
      {config.icon}
      {config.label}
    </span>
  );
}

// Category Badge (for psychology categories)
interface CategoryBadgeProps {
  category: string;
  color?: string;
  className?: string;
}

export function CategoryBadge({ category, color = '#6366F1', className = '' }: CategoryBadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium
        bg-white dark:bg-gray-900
        border
        ${className}
      `}
      style={{
        borderColor: `${color}30`,
        color: color,
        backgroundColor: `${color}10`,
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{ backgroundColor: color }}
      />
      {category}
    </span>
  );
}