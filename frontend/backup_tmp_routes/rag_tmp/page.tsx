'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { getDocuments, DocumentInfo, runEvaluation, EvalResult } from '@/lib/api';

function ScoreBar({ label, value }: { label: string; value: number }) {
 const pct = Math.round(value * 100);
 const color =
 pct >= 75 ? 'bg-green-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-red-500';
 return (
 <div className="mb-4">
 <div className="flex justify-between text-sm mb-1">
 <span className="font-medium text-slate-700 dark:text-slate-200">{label}</span>
 <span className={`font-bold ${pct >= 75 ? 'text-green-600' : pct >= 50 ? 'text-yellow-600' : 'text-red-500'}`}>
 {pct}%
 </span>
 </div>
 <div className="w-full h-2.5 bg-slate-100 dark:bg-slate-800/60 dark:bg-gray-700 rounded-full overflow-hidden">
 <div className={`h-2.5 rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
 </div>
 </div>
 );
}

export default function EvaluatePage() {
 const [docs, setDocs] = useState<DocumentInfo[]>([]);
 const [selectedIds, setSelectedIds] = useState<string[]>([]);
 const [question, setQuestion] = useState('');
 const [loading, setLoading] = useState(false);
 const [result, setResult] = useState<EvalResult | null>(null);
 const [error, setError] = useState('');

 useEffect(() => {
 getDocuments()
 .then(d => setDocs(d.filter(doc => doc.status === 'ready')))
 .catch(console.error);
 }, []);

 const toggleDoc = (id: string) =>
 setSelectedIds(prev =>
 prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
 );

 const handleRun = async () => {
 if (!question.trim()) { setError('Vui lòng nhập câu hỏi'); return; }
 if (selectedIds.length === 0) { setError('Vui lòng chọn ít nhất 1 tài liệu'); return; }
 setLoading(true);
 setError('');
 setResult(null);
 try {
 const res = await runEvaluation(question, selectedIds);
 setResult(res);
 } catch (e: unknown) {
 const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
 setError(msg || (e as Error).message || 'Lỗi đánh giá');
 } finally {
 setLoading(false);
 }
 };

 const avgScore = result
 ? Math.round(((result.faithfulness + result.answer_relevancy + result.context_quality) / 3) * 100)
 : 0;

 return (
 <div className="max-w-3xl mx-auto p-6">
 <Link href="/profile" className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-[#1E88E5] dark:hover:text-[#1E88E5] transition-colors mb-4">
 <ArrowLeft className="w-3.5 h-3.5" />
 Hồ sơ
 </Link>
 <h1 className="text-2xl font-bold mb-1 text-slate-800 dark:text-slate-100">Đánh giá RAG</h1>
 <p className="text-sm text-slate-400 dark:text-slate-500 mb-6">
 Nhập câu hỏi + chọn tài liệu → hệ thống tự tạo câu trả lời rồi đánh giá chất lượng RAG bằng LLM.
 </p>

 <div className="grid md:grid-cols-2 gap-6 mb-6">
 {/* Input */}
 <div className="bg-white dark:bg-slate-800/60 rounded-xl shadow-sm border border-slate-100 dark:border-slate-800 p-5">
 <h2 className="font-semibold text-slate-700 dark:text-slate-200 mb-4">Câu hỏi đánh giá</h2>
 <textarea
 value={question}
 onChange={e => setQuestion(e.target.value)}
 rows={4}
 placeholder="Ví dụ: Phương pháp nghiên cứu trong bài báo này là gì?"
 className="w-full border border-slate-200 dark:border-slate-700 dark:border-gray-600 dark:bg-gray-700 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
 />

 <h3 className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-2">Tài liệu nguồn</h3>
 <div className="max-h-48 overflow-y-auto space-y-1">
 {docs.length === 0 ? (
 <p className="text-xs text-slate-400 dark:text-slate-500">Chưa có tài liệu. Upload PDF trong Thư viện.</p>
 ) : (
 docs.map(d => (
 <label
 key={d.id}
 className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-200 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800/60 dark:hover:bg-gray-700 px-2 py-1 rounded"
 >
 <input
 type="checkbox"
 checked={selectedIds.includes(d.id)}
 onChange={() => toggleDoc(d.id)}
 className="accent-blue-600"
 />
 <span className="truncate">{d.title || d.filename}</span>
 </label>
 ))
 )}
 </div>

 {error && (
 <div className="mt-3 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-3 py-2">
 {error}
 </div>
 )}

 <button
 onClick={handleRun}
 disabled={loading}
 className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-lg font-medium text-sm transition-colors disabled:opacity-50"
 >
 {loading ? '⏳ Đang đánh giá...' : '🔬 Chạy đánh giá'}
 </button>
 </div>

 {/* Scores */}
 <div className="bg-white dark:bg-slate-800/60 rounded-xl shadow-sm border border-slate-100 dark:border-slate-800 p-5">
 <h2 className="font-semibold text-slate-700 dark:text-slate-200 mb-4">Kết quả</h2>

 {!result && !loading && (
 <div className="flex flex-col items-center justify-center h-40 text-slate-300 dark:text-slate-600">
 <div className="text-5xl mb-2">📊</div>
 <p className="text-sm">Chưa có kết quả</p>
 </div>
 )}

 {loading && (
 <div className="flex flex-col items-center justify-center h-40 text-slate-400 dark:text-slate-500">
 <div className="text-4xl mb-2 animate-pulse">🔍</div>
 <p className="text-sm">AI đang đánh giá...</p>
 </div>
 )}

 {result && (
 <>
 <div className="text-center mb-5">
 <p className="text-xs text-slate-400 dark:text-slate-500 uppercase tracking-wide">Điểm tổng</p>
 <p className={`text-4xl font-bold mt-1 ${avgScore >= 75 ? 'text-green-600' : avgScore >= 50 ? 'text-yellow-600' : 'text-red-500'}`}>
 {avgScore}%
 </p>
 </div>
 <ScoreBar label="Độ trung thực (Faithfulness)" value={result.faithfulness} />
 <ScoreBar label="Độ liên quan (Answer Relevancy)" value={result.answer_relevancy} />
 <ScoreBar label="Chất lượng context" value={result.context_quality} />
 <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded-lg text-xs text-blue-700 dark:text-blue-300">
 💬 {result.feedback}
 </div>
 </>
 )}
 </div>
 </div>

 {/* Answer + Sources */}
 {result && (
 <div className="space-y-4">
 <div className="bg-white dark:bg-slate-800/60 rounded-xl shadow-sm border border-slate-100 dark:border-slate-800 p-5">
 <h2 className="font-semibold text-slate-700 dark:text-slate-200 mb-3">Câu trả lời được tạo</h2>
 <p className="text-sm text-slate-600 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
 {result.answer}
 </p>
 </div>

 {result.sources?.length > 0 && (
 <div className="bg-white dark:bg-slate-800/60 rounded-xl shadow-sm border border-slate-100 dark:border-slate-800 p-5">
 <h2 className="font-semibold text-slate-700 dark:text-slate-200 mb-3">Nguồn tham chiếu</h2>
 <div className="space-y-2">
 {result.sources.map((s, i) => (
 <div key={i} className="border border-slate-100 dark:border-slate-800 rounded-lg p-3 text-sm">
 <p className="text-xs text-slate-400 dark:text-slate-500 mb-1">Trang {s.page}</p>
 <p className="text-slate-600 dark:text-slate-300 text-xs leading-relaxed">{s.preview}…</p>
 </div>
 ))}
 </div>
 </div>
 )}
 </div>
 )}
 </div>
 );
}
