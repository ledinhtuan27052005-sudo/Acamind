'use client';

import React from 'react';
import { Loader2 } from 'lucide-react';

interface NeuralButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  type?: 'button' | 'submit' | 'reset';
}

export function NeuralButton({
  variant = 'primary',
  size = 'md',
  children,
  className = '',
  onClick,
  disabled = false,
  loading = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  type = 'button',
}: NeuralButtonProps) {
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs gap-1.5',
    md: 'px-4 py-2.5 text-sm gap-2',
    lg: 'px-6 py-3 text-base gap-2.5',
  };

  const variantClasses = {
    primary: `
      bg-gradient-to-r from-neural-500 to-neural-600 text-white
      shadow-btn-neural hover:from-neural-600 hover:to-neural-700
      hover:shadow-lg hover:shadow-neural-500/30
      disabled:from-gray-300 disabled:to-gray-400 disabled:shadow-none
    `,
    secondary: `
      bg-gradient-to-r from-cortex-500 to-cortex-600 text-white
      shadow-btn-cortex hover:from-cortex-600 hover:to-cortex-700
      hover:shadow-lg hover:shadow-cortex-500/30
      disabled:from-gray-300 disabled:to-gray-400 disabled:shadow-none
    `,
    outline: `
      border-2 border-neural-500 text-neural-600 dark:text-neural-400
      hover:bg-neural-50 dark:hover:bg-neural-900/30
      disabled:border-gray-300 disabled:text-gray-400
    `,
    ghost: `
      text-gray-600 dark:text-gray-400
      hover:bg-gray-100 dark:hover:bg-gray-800
      hover:text-gray-900 dark:hover:text-gray-100
      disabled:text-gray-400 disabled:hover:bg-transparent disabled:hover:text-gray-400
    `,
    danger: `
      bg-gradient-to-r from-red-500 to-red-600 text-white
      shadow-red-500/30 hover:from-red-600 hover:to-red-700
      hover:shadow-lg hover:shadow-red-500/30
      disabled:from-gray-300 disabled:to-gray-400 disabled:shadow-none
    `,
  };

  const iconSizes = {
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  const IconComponent = icon
    ? (icon as React.ReactElement)
    : loading
    ? <Loader2 className={`${iconSizes[size]} animate-spin`} />
    : null;

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`
        inline-flex items-center justify-center
        font-semibold rounded-xl
        transition-all duration-200 ease-out
        disabled:cursor-not-allowed
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neural-500 focus-visible:ring-offset-2
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        ${fullWidth ? 'w-full' : ''}
        ${className}
      `}
    >
      {loading || icon ? (
        <>
          {IconComponent && iconPosition === 'left' && (
            <span className={loading ? 'mr-1' : 'mr-2'}>
              {IconComponent}
            </span>
          )}
          {children}
          {!loading && icon && iconPosition === 'right' && (
            <span className="ml-2">{icon}</span>
          )}
        </>
      ) : (
        children
      )}
    </button>
  );
}

// Icon Button (for toolbar actions)
interface NeuralIconButtonProps {
  icon: React.ReactNode;
  label: string;
  variant?: 'default' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
}

export function NeuralIconButton({
  icon,
  label,
  variant = 'default',
  size = 'md',
  className = '',
  onClick,
  disabled = false,
}: NeuralIconButtonProps) {
  const sizeClasses = {
    sm: 'w-7 h-7',
    md: 'w-9 h-9',
    lg: 'w-11 h-11',
  };

  const variantClasses = {
    default: 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700',
    ghost: 'hover:bg-gray-100 dark:hover:bg-gray-800',
    outline: 'border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800',
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
      className={`
        inline-flex items-center justify-center rounded-lg
        text-gray-600 dark:text-gray-400
        transition-all duration-150
        disabled:opacity-50 disabled:cursor-not-allowed
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neural-500
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        ${className}
      `}
    >
      {icon}
    </button>
  );
}
