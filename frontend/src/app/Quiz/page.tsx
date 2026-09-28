'use client';

import { useState, useEffect } from 'react';
import { NeuralCard } from '@/components/ui/NeuralCard';
import { NeuralBadge } from '@/components/ui/NeuralBadge';
import { ClipboardList, FileText, Zap, Loader2, ChevronRight } from 'lucide-react';
import { getDocuments, type DocumentInfo } from '@/lib/api';
import Link from 'next/link';

export default function QuizPage() {
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDocuments()
      .then(d => {
        const ready = d.filter(doc => doc.status === 'ready');
        setDocs(ready);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-surface-base transition-colors duration-300">

      {/* Hero Header */}
      <div className="relative overflow-hidden bg-gradient-to-br from-emerald-500/5 via-teal-500/5 to-cyan-500/5 dark:from-emerald-900/20 dark:via-teal-900/20 dark:to-cyan-900/20 border-b border-gray-200/50 dark:border-gray-800/50">
        <div className="absolute top-0 right-0 w-64 h-64 rounded-full bg-emerald-500/10 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full bg-teal-500/10 blur-3xl" />
        <div className="relative container mx-auto px-6 py-10 max-w-5xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <ClipboardList className="w-6 h-6 text-white" />
            </div>
            <NeuralBadge variant="neural" dot pulse>
              Review Quiz
            </NeuralBadge>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 dark:text-white mb-2">
            Psychology Review Quiz
          </h1>
          <p className="text-gray-600 dark:text-gray-400 max-w-2xl">
            AI generates quiz questions from PDF documents. Select a document and start testing your knowledge.
          </p>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8 max-w-5xl space-y-6">

        {/* Quiz Types */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <NeuralCard variant="elevated" padding="lg" hover={false}>
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center flex-shrink-0">
                <FileText className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-gray-900 dark:text-white mb-1">Quiz from Documents</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  AI generates quiz questions from uploaded PDF content.
                </p>
                <Link
                  href="/Quiz/document"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500 text-white text-sm font-medium hover:bg-emerald-600 transition-colors"
                >
                  Start <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </NeuralCard>

          <NeuralCard variant="elevated" padding="lg" hover={false}>
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
                <Zap className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-gray-900 dark:text-white mb-1">Quiz Y khoa</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  Medical psychology knowledge quiz.
                </p>
                <Link
                  href="/Quiz/medical"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-500 text-white text-sm font-medium hover:bg-blue-600 transition-colors"
                >
                  Start <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </NeuralCard>
        </div>

        {/* Available Documents */}
        <NeuralCard variant="elevated" padding="lg">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-gray-400" />
              <h3 className="font-bold text-gray-900 dark:text-white">Documents Ready</h3>
            </div>
            <span className="text-xs text-gray-500">{docs.length} documents</span>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : docs.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 dark:text-gray-400 mb-2">No documents yet</p>
              <Link
                href="/upload"
                className="text-sm text-emerald-600 dark:text-emerald-400 hover:underline"
              >
                Upload new documents
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {docs.slice(0, 10).map(doc => (
                <div
                  key={doc.id}
                  className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800"
                >
                  <FileText className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  <span className="flex-1 text-sm text-gray-700 dark:text-gray-200 truncate">
                    {doc.title || doc.filename}
                  </span>
                  <NeuralBadge variant="success" size="sm">Ready</NeuralBadge>
                </div>
              ))}
              {docs.length > 10 && (
                <p className="text-center text-xs text-gray-400 pt-2">
                  And {docs.length - 10} more documents...
                </p>
              )}
            </div>
          )}
        </NeuralCard>

        {/* Tips */}
        <NeuralCard variant="elevated" padding="md">
          <h3 className="font-bold text-gray-900 dark:text-white mb-3">💡 Study Tips</h3>
          <ul className="text-sm text-gray-600 dark:text-gray-300 space-y-1.5 list-disc list-inside">
            <li>Upload PDF documents to library to create automatic quizzes</li>
            <li>Choose the number of questions based on your study time</li>
            <li>Review answers to better understand the content</li>
          </ul>
        </NeuralCard>
      </div>
    </div>
  );
}
