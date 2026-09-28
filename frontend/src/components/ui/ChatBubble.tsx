'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Brain, User, FileText, Loader2 } from 'lucide-react';

interface Citation {
  id: string;
  title: string;
  pageNumber?: number;
  snippet?: string;
}

interface ChatBubbleProps {
  role: 'user' | 'assistant' | 'system';
  content: string;
  isStreaming?: boolean;
  citations?: Citation[];
  timestamp?: Date;
  onCitationClick?: (citation: Citation) => void;
  className?: string;
}

export function ChatBubble({
  role,
  content,
  isStreaming = false,
  citations = [],
  timestamp,
  onCitationClick,
  className = '',
}: ChatBubbleProps) {
  const isUser = role === 'user';
  const isSystem = role === 'system';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''} ${className}`}>
      {/* Avatar */}
      <div
        className={`
          w-10 h-10 rounded-xl flex items-center justify-center shrink-0
          ${isUser
            ? 'bg-gradient-to-br from-neural-500 to-neural-600 text-white shadow-md'
            : isSystem
            ? 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
            : 'bg-gradient-to-br from-neural-500 via-cortex-500 to-cortex-600 text-white shadow-md'
          }
        `}
      >
        {isUser ? (
          <User className="w-5 h-5" />
        ) : isSystem ? (
          <FileText className="w-5 h-5" />
        ) : (
          <Brain className="w-5 h-5" />
        )}
      </div>

      {/* Bubble */}
      <div
        className={`
          max-w-[85%] rounded-2xl px-4 py-3 shadow-sm
          ${isUser
            ? 'bg-gradient-to-r from-neural-500 to-neural-600 text-white rounded-tr-sm'
            : isSystem
            ? 'bg-gray-100 dark:bg-gray-800/50 text-gray-500 dark:text-gray-400 text-sm italic rounded-tl-sm'
            : 'bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-800 rounded-tl-sm'
          }
        `}
      >
        {/* Message Content */}
        <div className={`prose-chat ${isUser ? 'text-white' : ''}`}>
          {isUser ? (
            <p className="text-sm leading-relaxed">{content}</p>
          ) : (
            <div className="text-sm leading-relaxed">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Custom link rendering
                  a: ({ href, children }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-neural-600 dark:text-neural-400 hover:underline"
                    >
                      {children}
                    </a>
                  ),
                }}
              >
                {content}
              </ReactMarkdown>

              {/* Streaming cursor */}
              {isStreaming && (
                <span className="inline-block w-2 h-4 bg-neural-500 ml-1 animate-pulse" />
              )}
            </div>
          )}
        </div>

        {/* Citations */}
        {!isUser && citations.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-800">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 font-medium">
              📚 Source Citations:
            </p>
            <div className="space-y-2">
              {citations.map((citation, index) => (
                <button
                  key={citation.id}
                  onClick={() => onCitationClick?.(citation)}
                  className={`
                    w-full text-left p-2 rounded-lg
                    bg-gray-50 dark:bg-gray-800/50
                    hover:bg-neural-50 dark:hover:bg-neural-900/20
                    border border-transparent hover:border-neural-200 dark:hover:border-neural-800
                    transition-all duration-150
                    ${onCitationClick ? 'cursor-pointer' : 'cursor-default'}
                  `}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-xs font-mono font-semibold text-neural-600 dark:text-neural-400 bg-neural-100 dark:bg-neural-900/50 px-1.5 py-0.5 rounded">
                      [{index + 1}]
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">
                        {citation.title}
                      </p>
                      {citation.pageNumber && (
                        <p className="text-[10px] text-gray-400 mt-0.5">
                          Page {citation.pageNumber}
                        </p>
                      )}
                      {citation.snippet && (
                        <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-1 line-clamp-2 italic">
                          "{citation.snippet}"
                        </p>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Timestamp */}
        {timestamp && !isStreaming && (
          <p className={`text-[10px] mt-2 ${isUser ? 'text-white/60' : 'text-gray-400'}`}>
            {timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
          </p>
        )}
      </div>
    </div>
  );
}

// Empty Chat State
export function ChatEmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4 py-12">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-neural-500 to-cortex-500 flex items-center justify-center mb-4 shadow-lg">
        <Brain className="w-8 h-8 text-white" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
        Start a Conversation
      </h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm">
        Select documents from the left sidebar and ask questions about psychology article content.
      </p>
      <div className="mt-6 space-y-2 text-xs text-gray-400">
        <p>💡 Suggestion: "What is the main objective of the study?"</p>
        <p>💡 Suggestion: "What research methods were used?"</p>
        <p>💡 Suggestion: "What are the main findings?"</p>
      </div>
    </div>
  );
}

// Chat Input
interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onStop?: () => void;
  placeholder?: string;
  disabled?: boolean;
  isLoading?: boolean;
  maxLength?: number;
}

export function ChatInput({
  value,
  onChange,
  onSubmit,
  onStop,
  placeholder = 'Type your question...',
  disabled = false,
  isLoading = false,
  maxLength = 2000,
}: ChatInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading && value.trim()) {
        onSubmit();
      }
    }
  };

  return (
    <div className="flex items-end gap-3">
      <div className="flex-1 relative">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          maxLength={maxLength}
          rows={1}
          className={`
            w-full resize-none rounded-xl border border-gray-200 dark:border-gray-700
            bg-white dark:bg-gray-900
            text-gray-900 dark:text-gray-100
            placeholder-gray-400 dark:placeholder-gray-500
            px-4 py-3
            focus:outline-none focus:ring-2 focus:ring-neural-500/30 focus:border-neural-500
            transition-all duration-200
            disabled:opacity-50 disabled:cursor-not-allowed
            max-h-40
          `}
          style={{
            minHeight: '48px',
            height: 'auto',
          }}
          onInput={(e) => {
            const target = e.target as HTMLTextAreaElement;
            target.style.height = 'auto';
            target.style.height = Math.min(target.scrollHeight, 160) + 'px';
          }}
        />
      </div>

      <button
        onClick={isLoading ? onStop : onSubmit}
        disabled={(!isLoading && !value.trim()) || disabled}
        className={`
          flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center
          transition-all duration-200
          ${isLoading
            ? 'bg-red-500 hover:bg-red-600 text-white'
            : value.trim()
            ? 'bg-gradient-to-r from-neural-500 to-neural-600 hover:from-neural-600 hover:to-neural-700 text-white shadow-lg shadow-neural-500/30'
            : 'bg-gray-100 dark:bg-gray-800 text-gray-400 cursor-not-allowed'
          }
        `}
      >
        {isLoading ? (
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
        ) : (
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="19" x2="12" y2="5" />
            <polyline points="5 12 12 5 19 12" />
          </svg>
        )}
      </button>
    </div>
  );
}