'use client';

import { useState } from 'react';
import { translateText } from '@/lib/api';
import { NeuralCard } from '@/components/ui/NeuralCard';
import { NeuralBadge } from '@/components/ui/NeuralBadge';
import { Languages, ArrowLeftRight, Copy, Check, RefreshCw, Loader2 } from 'lucide-react';

type Lang = 'en' | 'vi';

const MAX_CHARS = 5000;

export default function TranslatePage() {
  const [inputText, setInputText] = useState('');
  const [sourceLang, setSourceLang] = useState<Lang>('en');
  const [targetLang, setTargetLang] = useState<Lang>('vi');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const swap = () => {
    setSourceLang(targetLang);
    setTargetLang(sourceLang);
    setInputText(result);
    setResult('');
  };

  async function handleTranslate() {
    if (!inputText.trim()) return;
    setLoading(true);
    setError('');
    setResult('');
    try {
      const res = await translateText(inputText, targetLang, sourceLang);
      setResult(res.translation);
    } catch (e: unknown) {
      const errWithResponse = e as { response?: { data?: { detail?: string } } };
      setError(errWithResponse?.response?.data?.detail ?? 'Translation failed. Try again later.');
    } finally {
      setLoading(false);
    }
  }

  const copyResult = async () => {
    await navigator.clipboard.writeText(result);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-surface-base transition-colors duration-300">

      {/* Hero Header */}
      <div className="relative overflow-hidden bg-gradient-to-br from-neural-500/5 via-cortex-500/5 to-dopamine-500/5 dark:from-neural-900/20 dark:via-cortex-900/20 dark:to-dopamine-900/20 border-b border-gray-200/50 dark:border-gray-800/50">
        <div className="absolute top-0 right-0 w-64 h-64 rounded-full bg-neural-500/10 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full bg-cortex-500/10 blur-3xl" />
        <div className="relative container mx-auto px-6 py-10 max-w-5xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-teal-500 to-emerald-500 flex items-center justify-center shadow-lg shadow-teal-500/20">
              <Languages className="w-6 h-6 text-white" />
            </div>
            <NeuralBadge variant="neural" dot pulse>
              AI Translation
            </NeuralBadge>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 dark:text-white mb-2">
            Translate Academic Documents
          </h1>
          <p className="text-gray-600 dark:text-gray-400 max-w-2xl">
            AI translates academic text English ↔ Vietnamese. Preserves specialized psychology terminology.
          </p>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8 max-w-5xl space-y-6">

        {/* Language selector */}
        <NeuralCard variant="elevated" padding="md">
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <button
              onClick={() => setSourceLang('en')}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                sourceLang === 'en'
                  ? 'bg-neural-500 text-white shadow-md'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300'
              }`}
            >
              🇬🇧 English
            </button>
            <button
              onClick={swap}
              className="p-2 rounded-xl border-2 border-gray-200 dark:border-gray-700 hover:border-neural-400 text-gray-600 dark:text-gray-300 transition-all"
            >
              <ArrowLeftRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => setSourceLang('vi')}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                sourceLang === 'vi'
                  ? 'bg-neural-500 text-white shadow-md'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300'
              }`}
            >
              🇻🇳 Vietnamese
            </button>
          </div>
        </NeuralCard>

        {/* Two panels */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Input */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
              <span className="text-xs font-medium text-gray-500">
                {sourceLang === 'en' ? '🇬🇧 English' : '🇻🇳 Vietnamese'} · Source
              </span>
              {inputText && (
                <button onClick={() => { setInputText(''); setResult(''); }} className="text-xs text-gray-400 hover:text-red-500">
                  <RefreshCw className="w-3 h-3" />
                </button>
              )}
            </div>
            <textarea
              value={inputText}
              onChange={e => setInputText(e.target.value.slice(0, MAX_CHARS))}
              placeholder="Enter text to translate..."
              className="w-full h-64 p-4 text-sm text-gray-800 dark:text-gray-100 bg-transparent resize-none focus:outline-none"
            />
            <div className="px-4 py-2 border-t border-gray-100 dark:border-gray-700 flex justify-between items-center">
              <span className="text-xs text-gray-400">{inputText.length}/{MAX_CHARS}</span>
              <button
                onClick={handleTranslate}
                disabled={!inputText.trim() || loading}
                className="flex items-center gap-2 text-sm px-4 py-1.5 rounded-lg bg-neural-500 text-white font-medium disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Languages className="w-4 h-4" />}
                Translate
              </button>
            </div>
          </div>

          {/* Output */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
              <span className="text-xs font-medium text-neural-600 dark:text-neural-400">
                {targetLang === 'vi' ? '🇻🇳 Vietnamese' : '🇬🇧 English'} · Translation
              </span>
              {result && (
                <button onClick={copyResult} className="text-xs text-gray-400 hover:text-neural-500">
                  {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                </button>
              )}
            </div>
            <div className="h-64 p-4 overflow-y-auto">
              {loading ? (
                <div className="space-y-2">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-4/5" />
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-3/5" />
                </div>
              ) : error ? (
                <p className="text-sm text-red-500">{error}</p>
              ) : result ? (
                <p className="text-sm text-gray-800 dark:text-gray-100 whitespace-pre-wrap">{result}</p>
              ) : (
                <p className="text-sm text-gray-400">Translation will appear here...</p>
              )}
            </div>
          </div>
        </div>

        {/* Tips */}
        <NeuralCard variant="elevated" padding="md">
          <h3 className="font-bold text-gray-900 dark:text-white mb-2">💡 Usage Tips</h3>
          <ul className="text-sm text-gray-600 dark:text-gray-300 space-y-1 list-disc list-inside">
            <li>Paste excerpts from articles and translate for quick reading</li>
            <li>AI preserves technical terms (p-value, meta-analysis...)</li>
            <li>Maximum 5,000 characters per translation</li>
          </ul>
        </NeuralCard>

      </div>
    </div>
  );
}
