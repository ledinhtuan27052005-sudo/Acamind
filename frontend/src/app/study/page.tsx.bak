'use client';

import { useEffect, useRef, useState } from 'react';
import { getDocuments, chatStream } from '@/lib/api';
import type { DocumentInfo } from '@/lib/api';
import { NeuralCard } from '@/components/ui/NeuralCard';
import { NeuralBadge } from '@/components/ui/NeuralBadge';
import { NeuralButton } from '@/components/ui/NeuralButton';
import { GraduationCap, Send, Loader2, FileText, BookOpen, Lightbulb, Zap, ChevronRight, Sparkles } from 'lucide-react';

interface Message {
 role: 'user' | 'assistant';
 content: string;
}

const LEVELS = [
 { value: 'beginner', label: 'Basic', icon: BookOpen, color: '#10B981', desc: 'Simple explanations, no jargon', bg: 'bg-emerald-500' },
 { value: 'advanced', label: 'Advanced', icon: Lightbulb, color: '#F59E0B', desc: 'In-depth analysis with examples', bg: 'bg-amber-500' },
 { value: 'researcher', label: 'Research', icon: Zap, color: '#7C3AED', desc: 'Academic, methodology comparison', bg: 'bg-violet-500' },
];

const STARTER_QUESTIONS = [
 'Summarize the key points of this document',
 'What research methods were used?',
 'What are the main results and conclusions?',
 'What are the limitations of the study?',
 'What are the practical applications?',
];

export default function LearnPage() {
 const [docs, setDocs] = useState<DocumentInfo[]>([]);
 const [docId, setDocId] = useState('');
 const [level, setLevel] = useState('beginner');
 const [messages, setMessages] = useState<Message[]>([]);
 const [input, setInput] = useState('');
 const [loading, setLoading] = useState(false);
 const [error, setError] = useState('');
 const bottomRef = useRef<HTMLDivElement>(null);

 useEffect(() => {
 getDocuments().then(d => {
 const ready = d.filter(doc => doc.status === 'ready');
 setDocs(ready);
 if (ready.length > 0 && !docId) setDocId(ready[0].id);
 });
 }, []);

 useEffect(() => {
 bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
 }, [messages]);

 const levelConfig = LEVELS.find(l => l.value === level) ?? LEVELS[0];

 const buildSystemNote = () => {
 if (level === 'beginner') return 'Explain as if to a first-year student, avoid technical jargon, use simple language and easy examples.';
 if (level === 'advanced') return 'In-depth explanation with academic examples, may use technical terms but explain clearly.';
 return 'Analyze from research perspective: methodology, research design, limitations, comparison with related documents.';
 };

 const sendMessage = async (text?: string) => {
 const q = (text ?? input).trim();
 if (!q || !docId) return;
 setInput('');
 const fullQuestion = `[Learning mode: ${levelConfig.label}] ${buildSystemNote()}\n\nQuestion: ${q}`;

 setMessages(prev => [...prev, { role: 'user', content: q }]);
 setLoading(true); setError('');
 let aiText = '';
 setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

 try {
 await chatStream(fullQuestion, [docId], (chunk) => {
 aiText += chunk;
 setMessages(prev => {
 const next = [...prev];
 next[next.length - 1] = { role: 'assistant', content: aiText };
 return next;
 });
 });
 } catch (e: unknown) {
 const err = e as Error;
 setError(err?.message ?? 'Cannot answer. Try again later.');
 setMessages(prev => prev.slice(0, -2));
 } finally {
 setLoading(false);
 }
 };

 return (
 <div className="min-h-screen bg-gray-50 dark:bg-surface-base transition-colors duration-300 flex flex-col">

 {/* Hero Header */}
 <div className="relative overflow-hidden bg-gradient-to-br from-emerald-500/5 via-neural-500/5 to-teal-500/5 dark:from-emerald-900/20 dark:via-neural-900/20 dark:to-teal-900/20 border-b border-gray-200/50 dark:border-gray-800/50 flex-shrink-0">
 <div className="absolute top-0 right-0 w-64 h-64 rounded-full bg-emerald-500/10 blur-3xl" />
 <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full bg-teal-500/10 blur-3xl" />
 <div className="relative container mx-auto px-6 py-8 max-w-5xl">
 <div className="flex items-center gap-3 mb-3">
 <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
 <GraduationCap className="w-6 h-6 text-white" />
 </div>
 <NeuralBadge variant="neural" dot pulse>
 Learning Mode
 </NeuralBadge>
 </div>
 <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 dark:text-white mb-2">
 Learn by Level
 </h1>
 <p className="text-gray-600 dark:text-gray-400 max-w-2xl">
 Ask AI about documents at 3 levels: Basic, Advanced, or In-depth Research.
 </p>
 </div>
 </div>

 {/* Config bar */}
 <div className="flex-shrink-0 border-b border-gray-200/50 dark:border-gray-800/50 bg-white/80 dark:bg-gray-900/50 backdrop-blur-sm">
 <div className="container mx-auto px-6 py-4 max-w-5xl">
 <div className="flex flex-wrap gap-4 items-center">
 {/* Doc select */}
 <div className="flex items-center gap-3 flex-1 min-w-[200px]">
 <FileText className="w-5 h-5 text-gray-400 flex-shrink-0" />
 <select
 value={docId}
 onChange={e => { setDocId(e.target.value); setMessages([]); }}
 className="flex-1 text-sm bg-transparent border-none focus:outline-none text-gray-700 dark:text-gray-200 cursor-pointer"
 disabled={docs.length === 0}
 >
 {docs.length === 0
 ? <option>No documents</option>
 : docs.map(d => <option key={d.id} value={d.id}>{d.title || d.filename}</option>)
 }
 </select>
 </div>

 <div className="w-px h-8 bg-gray-200 dark:bg-gray-700 hidden sm:block" />

 {/* Level tabs */}
 <div className="flex gap-2">
 {LEVELS.map(l => {
 const Icon = l.icon;
 const isActive = level === l.value;
 return (
 <button
 key={l.value}
 onClick={() => setLevel(l.value)}
 title={l.desc}
 className={`flex items-center gap-2 text-sm px-4 py-2 rounded-xl font-medium transition-all ${
 isActive
 ? `text-white shadow-lg`
 : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
 }`}
 style={isActive ? { background: l.bg, boxShadow: `0 4px 12px ${l.color}30` } : {}}
 >
 <Icon className="w-4 h-4" /> {l.label}
 </button>
 );
 })}
 </div>

 {/* Current mode description */}
 <div className="hidden md:block text-xs text-gray-400 max-w-[200px] truncate">
 {levelConfig.desc}
 </div>
 </div>
 </div>
 </div>

 {/* Messages area */}
 <div className="flex-1 container mx-auto px-6 py-6 max-w-5xl">
 {messages.length === 0 ? (
 <div className="h-full flex flex-col items-center justify-center py-16">
 <NeuralCard variant="elevated" padding="lg" className="text-center max-w-lg">
 <div className="w-16 h-16 rounded-full bg-gradient-to-br from-emerald-100 to-teal-100 dark:from-emerald-900/30 dark:to-teal-900/30 flex items-center justify-center mx-auto mb-4">
 <GraduationCap className="w-8 h-8 text-emerald-600 dark:text-emerald-400" />
 </div>
 <h3 className="font-bold text-gray-900 dark:text-white mb-2">Start with suggested questions</h3>
 <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
 Mode: <span className="font-semibold" style={{ color: levelConfig.color }}>{levelConfig.label}</span>
 </p>
 <div className="flex flex-wrap gap-2 justify-center">
 {STARTER_QUESTIONS.map(q => (
 <button
 key={q}
 onClick={() => sendMessage(q)}
 disabled={!docId || loading}
 className="text-xs px-4 py-2 rounded-full transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
 style={{ background: `${levelConfig.color}15`, color: levelConfig.color }}
 >
 {q}
 </button>
 ))}
 </div>
 </NeuralCard>
 </div>
 ) : (
 <div className="space-y-4 pb-24">
 {messages.map((msg, i) => (
 <div key={i} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
 {msg.role === 'assistant' && (
 <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center flex-shrink-0 mt-1 shadow-lg shadow-emerald-500/20">
 <GraduationCap className="w-5 h-5 text-white" />
 </div>
 )}
 <div className={`max-w-[75%] rounded-2xl px-5 py-4 ${
 msg.role === 'user'
 ? 'bg-gradient-to-r from-neural-500 to-teal-500 text-white rounded-tr-sm shadow-lg shadow-neural-500/20'
 : 'bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 text-gray-800 dark:text-gray-100 rounded-tl-sm'
 }`}>
 <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
 </div>
 {msg.role === 'user' && (
 <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-600 flex items-center justify-center flex-shrink-0 mt-1">
 <Sparkles className="w-5 h-5 text-gray-600 dark:text-gray-300" />
 </div>
 )}
 </div>
 ))}
 {loading && (
 <div className="flex gap-4 justify-start">
 <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center flex-shrink-0 shadow-lg shadow-emerald-500/20">
 <GraduationCap className="w-5 h-5 text-white" />
 </div>
 <div className="bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-2xl rounded-tl-sm px-5 py-4">
 <Loader2 className="w-5 h-5 animate-spin text-emerald-500" />
 </div>
 </div>
 )}
 {error && (
 <div className="text-center">
 <p className="text-sm text-red-500">{error}</p>
 </div>
 )}
 <div ref={bottomRef} />
 </div>
 )}
 </div>

 {/* Input */}
 <div className="flex-shrink-0 border-t border-gray-200/50 dark:border-gray-800/50 bg-white/80 dark:bg-gray-900/50 backdrop-blur-sm">
 <div className="container mx-auto px-6 py-4 max-w-5xl">
 <div className="flex gap-3 items-center bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-3 shadow-lg">
 <input
 value={input}
 onChange={e => setInput(e.target.value)}
 onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), sendMessage())}
 placeholder={docId ? `Ask about documents (${levelConfig.label} mode)...` : 'Select a document first...'}
 disabled={!docId || loading}
 className="flex-1 text-sm bg-transparent focus:outline-none placeholder-gray-400 dark:placeholder-gray-500 disabled:opacity-50"
 />
 <button
 onClick={() => sendMessage()}
 disabled={!input.trim() || !docId || loading}
 className="p-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:shadow-lg hover:shadow-emerald-500/25 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-all"
 style={{ boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)' }}
 >
 {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
 </button>
 </div>
 </div>
 </div>
 </div>
 );
}
