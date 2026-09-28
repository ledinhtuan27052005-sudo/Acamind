'use client';

import { useEffect, useState } from 'react';
import { FileText, Loader2, Microscope, Search, Sparkles } from 'lucide-react';
import { generateLiteratureReview, getDocuments, type DocumentInfo } from '@/lib/api';
import { NeuralBadge } from '@/components/ui/NeuralBadge';
import { NeuralCard } from '@/components/ui/NeuralCard';

export default function LiteraturePage() {
  const [topic, setTopic] = useState('');
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [loadingDocuments, setLoadingDocuments] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    getDocuments()
      .then((items) => setDocuments(items.filter((item) => item.status === 'ready')))
      .catch(() => setError('Không thể tải thư viện tài liệu. Kiểm tra backend rồi thử lại.'))
      .finally(() => setLoadingDocuments(false));
  }, []);

  const toggleDocument = (id: string) => setSelectedIds((current) => current.includes(id)
    ? current.filter((item) => item !== id)
    : [...current, id].slice(0, 10));

  const handleGenerate = async () => {
    if (!topic.trim() || selectedIds.length === 0 || loading) return;
    setLoading(true); setError(''); setResult('');
    try {
      const response = await generateLiteratureReview(selectedIds, topic.trim());
      if (!response.ok) {
        let message = 'Không thể tạo Literature Review. Vui lòng thử lại.';
        try { message = (await response.json()).detail || message; } catch { /* non-JSON error */ }
        throw new Error(message);
      }
      const reader = response.body?.getReader();
      if (!reader) throw new Error('Backend không trả về nội dung để hiển thị.');
      const decoder = new TextDecoder();
      let fullText = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        fullText += decoder.decode(value, { stream: true });
        setResult(fullText);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không thể tạo Literature Review.');
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-surface-base transition-colors duration-300">
      <div className="border-b border-gray-200/50 bg-gradient-to-br from-violet-500/5 via-purple-500/5 to-pink-500/5 dark:border-gray-800/50 dark:from-violet-900/20 dark:via-purple-900/20 dark:to-pink-900/20">
        <div className="container mx-auto max-w-5xl px-6 py-10">
          <div className="mb-4 flex items-center gap-3"><div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-purple-500"><Microscope className="h-6 w-6 text-white" /></div><NeuralBadge variant="cortex" dot pulse>Literature Review</NeuralBadge></div>
          <h1 className="mb-2 text-3xl font-extrabold text-gray-900 dark:text-white md:text-4xl">Literature Review Generator</h1>
          <p className="max-w-2xl text-gray-600 dark:text-gray-400">Tổng hợp có căn cứ từ các tài liệu bạn chọn trong thư viện.</p>
        </div>
      </div>
      <div className="container mx-auto max-w-5xl space-y-6 px-6 py-8">
        <NeuralCard variant="elevated" padding="lg"><div className="space-y-4">
          <div className="flex items-center gap-2"><Search className="h-5 w-5 text-violet-500" /><h2 className="font-bold text-gray-900 dark:text-white">Chủ đề nghiên cứu</h2></div>
          <input value={topic} onChange={(event) => setTopic(event.target.value)} placeholder="Ví dụ: Động lực học tập và trì hoãn học tập" className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-violet-500/50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100" />
          <div><p className="mb-2 text-sm font-semibold text-gray-800 dark:text-gray-100">Chọn tài liệu ({selectedIds.length}/10)</p>
            {loadingDocuments ? <p className="text-sm text-gray-500">Đang tải thư viện…</p> : documents.length === 0 ? <p className="text-sm text-amber-600">Chưa có tài liệu sẵn sàng để phân tích.</p> : <div className="max-h-64 space-y-2 overflow-y-auto rounded-xl border border-gray-200 p-3 dark:border-gray-700">{documents.map((document) => <label key={document.id} className="flex cursor-pointer items-start gap-3 rounded-lg p-2 hover:bg-violet-50 dark:hover:bg-violet-950/30"><input type="checkbox" checked={selectedIds.includes(document.id)} onChange={() => toggleDocument(document.id)} /><span className="text-sm text-gray-700 dark:text-gray-200">{document.title || document.filename}</span></label>)}</div>}
          </div>
          <button onClick={handleGenerate} disabled={!topic.trim() || selectedIds.length === 0 || loading} className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-violet-500 to-purple-500 py-3 font-semibold text-white disabled:opacity-50">{loading ? <><Loader2 className="h-5 w-5 animate-spin" />Đang tổng hợp…</> : <><Sparkles className="h-5 w-5" />Tạo Literature Review</>}</button>
          {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-300">{error}</p>}
        </div></NeuralCard>
        {result && <NeuralCard variant="elevated" padding="lg"><div className="mb-4 flex items-center gap-2"><FileText className="h-5 w-5 text-violet-500" /><h3 className="font-bold text-gray-900 dark:text-white">Kết quả</h3></div><pre className="whitespace-pre-wrap font-sans text-sm text-gray-700 dark:text-gray-200">{result}</pre></NeuralCard>}
      </div>
    </div>
  );
}
