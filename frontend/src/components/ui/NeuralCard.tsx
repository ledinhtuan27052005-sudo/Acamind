'use client';

import React from 'react';

interface NeuralCardProps {
  variant?: 'default' | 'elevated' | 'glow' | 'glass';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hover?: boolean;
  style?: React.CSSProperties;
}

export function NeuralCard({
  variant = 'default',
  padding = 'md',
  children,
  className = '',
  onClick,
  hover = true,
  style,
}: NeuralCardProps) {
  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-5',
    lg: 'p-6',
  };

  const variantClasses = {
    default: 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800',
    elevated: 'bg-white dark:bg-gray-900 shadow-lg border border-gray-100 dark:border-gray-800',
    glow: `
      relative
      bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800
      before:absolute before:inset-0 before:rounded-2xl before:p-px
      before:bg-gradient-to-br before:from-neural-400/50 before:via-cortex-400/30 before:to-dopamine-400/20
      before:-z-10 before:opacity-0 hover:before:opacity-100
      before:transition-opacity before:duration-300
    `,
    glass: `
      glass bg-white/70 dark:bg-gray-900/70
      border border-white/50 dark:border-gray-800/50
      backdrop-blur-xl
    `,
  };

  const hoverClasses = hover && !onClick
    ? 'hover:shadow-card-hover hover:border-neural-200 dark:hover:border-neural-800 hover:-translate-y-0.5'
    : '';

  const cursorClass = onClick ? 'cursor-pointer' : '';

  return (
    <div
      className={`
        rounded-2xl transition-all duration-300 ease-out
        ${variantClasses[variant]}
        ${paddingClasses[padding]}
        ${hoverClasses}
        ${cursorClass}
        ${className}
      `}
      style={style}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
    >
      {children}
    </div>
  );
}

// Card Header Component
interface NeuralCardHeaderProps {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export function NeuralCardHeader({
  title,
  subtitle,
  icon,
  action,
  className = '',
}: NeuralCardHeaderProps) {
  return (
    <div className={`flex items-start justify-between gap-4 ${className}`}>
      <div className="flex items-start gap-3">
        {icon && (
          <div className="w-10 h-10 rounded-xl bg-neural-50 dark:bg-neural-900/30 flex items-center justify-center text-neural-600 dark:text-neural-400 shrink-0">
            {icon}
          </div>
        )}
        <div>
          <h3 className="font-semibold text-gray-900 dark:text-white">{title}</h3>
          {subtitle && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{subtitle}</p>
          )}
        </div>
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

// Card Footer Component
interface NeuralCardFooterProps {
  children: React.ReactNode;
  className?: string;
}

export function NeuralCardFooter({ children, className = '' }: NeuralCardFooterProps) {
  return (
    <div className={`pt-4 mt-4 border-t border-gray-100 dark:border-gray-800 ${className}`}>
      {children}
    </div>
  );
}
