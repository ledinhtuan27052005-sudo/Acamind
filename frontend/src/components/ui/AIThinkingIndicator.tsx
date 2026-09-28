'use client';

import React from 'react';

interface AIThinkingIndicatorProps {
  variant?: 'dots' | 'pulse' | 'typing';
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  className?: string;
}

export function AIThinkingIndicator({
  variant = 'dots',
  size = 'md',
  text = 'AI is processing...',
  className = '',
}: AIThinkingIndicatorProps) {
  const sizeClasses = {
    sm: {
      dot: 'w-1.5 h-1.5',
      text: 'text-xs',
      gap: 'gap-1',
    },
    md: {
      dot: 'w-2 h-2',
      text: 'text-sm',
      gap: 'gap-1.5',
    },
    lg: {
      dot: 'w-2.5 h-2.5',
      text: 'text-base',
      gap: 'gap-2',
    },
  };

  const { dot, text: textClass, gap } = sizeClasses[size];

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Animated dots */}
      <div className={`flex ${gap}`}>
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className={`
              ${dot} rounded-full bg-neural-500
              ${variant === 'dots' ? 'animate-bounce' : ''}
              ${variant === 'pulse' ? 'animate-pulse' : ''}
            `}
            style={{
              animationDelay: `${i * 0.15}s`,
              animationDuration: '0.6s',
            }}
          />
        ))}
      </div>

      {/* Text */}
      <span className={`text-gray-500 dark:text-gray-400 ${textClass}`}>
        {text}
      </span>
    </div>
  );
}

// Pipeline Progress Indicator
interface PipelineStep {
  id: string;
  label: string;
  description?: string;
}

interface PipelineProgressProps {
  steps: PipelineStep[];
  currentStepId: string;
  completedStepIds: string[];
  className?: string;
}

export function PipelineProgress({
  steps,
  currentStepId,
  completedStepIds,
  className = '',
}: PipelineProgressProps) {
  const currentStepIndex = steps.findIndex((s) => s.id === currentStepId);

  return (
    <div className={`space-y-4 ${className}`}>
      {steps.map((step, index) => {
        const isComplete = completedStepIds.includes(step.id);
        const isActive = step.id === currentStepId;
        const isPending = !isComplete && !isActive;

        return (
          <div key={step.id} className="flex items-center gap-3">
            {/* Status Icon */}
            <div
              className={`
                w-8 h-8 rounded-full flex items-center justify-center shrink-0
                ${isComplete
                  ? 'bg-neural-500 text-white'
                  : isActive
                  ? 'bg-cortex-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-400'
                }
              `}
            >
              {isComplete ? (
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              ) : isActive ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <span className="text-sm font-medium">{index + 1}</span>
              )}
            </div>

            {/* Step Info */}
            <div className="flex-1">
              <p
                className={`
                  text-sm font-medium
                  ${isActive ? 'text-cortex-600 dark:text-cortex-400' : ''}
                  ${isComplete ? 'text-gray-900 dark:text-gray-100' : ''}
                  ${isPending ? 'text-gray-400' : ''}
                `}
              >
                {step.label}
              </p>
              {step.description && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {step.description}
                </p>
              )}
            </div>

            {/* Progress indicator for active step */}
            {isActive && (
              <div className="w-16 h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-cortex-500 to-neural-500 rounded-full animate-pulse"
                  style={{ width: '60%' }}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// Streaming Text with cursor
interface StreamingTextProps {
  text: string;
  isStreaming: boolean;
  className?: string;
}

export function StreamingText({ text, isStreaming, className = '' }: StreamingTextProps) {
  return (
    <span className={`relative ${className}`}>
      {text}
      {isStreaming && (
        <span className="typing-cursor ml-0.5" />
      )}
    </span>
  );
}

// Loading Spinner
interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div
      className={`
        ${sizeClasses[size]} border-2 border-neural-200 border-t-neural-500 rounded-full animate-spin
        ${className}
      `}
    />
  );
}

// Full Page Loader
interface LoadingScreenProps {
  message?: string;
}

export function LoadingScreen({ message = 'Loading...' }: LoadingScreenProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="text-center">
        <div className="w-12 h-12 mx-auto mb-4 border-3 border-neural-200 border-t-neural-500 rounded-full animate-spin" />
        <p className="text-sm text-gray-500 dark:text-gray-400">{message}</p>
      </div>
    </div>
  );
}
