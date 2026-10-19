'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Stethoscope,
  Loader2,
  AlertCircle,
  X,
  Brain,
  HeartPulse,
  ExternalLink,
  Trash2,
  Sparkles,
  FileText,
  Send,
  ClipboardCheck,
  Award,
  UserCheck,
  Activity,
  CheckCircle2,
} from 'lucide-react';
import {
  PsychologySource,
  SymptomRecord,
  analyzeSymptoms,
  deleteSymptom,
  getDocuments,
  getProfileSymptoms,
  listOsceCases,
  chatOscePatient,
  evaluateOsceSession,
  type DocumentInfo,
  type OsceCasePublic,
  type OsceEvaluationResult,
} from '@/lib/api';
import { AcademicDocumentRenderer, cleanMarkdownText } from '@/components/ui/AcademicDocumentRenderer';
import { useAppStore } from '@/store/useAppStore';
import { NeuralCard } from '@/components/ui/NeuralCard';
import { NeuralBadge } from '@/components/ui/NeuralBadge';
import { NeuralButton } from '@/components/ui/NeuralButton';

interface OsceScaleItem {
  scale_code: string;
  total_score: string;
  severity: string;
  breakdown?: string;
}

interface OsceMessage {
  role: 'clinician' | 'patient';
  content: string;
  scaleResult?: OsceScaleItem | null;
}

export default function PsychologyPage() {
  const router = useRouter();
  const { user } = useAppStore();

  // Tab switcher: 'osce' (Feature 4: Virtual Patient OSCE Sandbox) | 'profile' (3D Symptom Profile)
  const [activeTab, setActiveTab] = useState<'osce' | 'profile'>('osce');

  // ── 3D Symptom Profile State ──
  const [symptoms, setSymptoms] = useState<SymptomRecord[]>([]);
  const [loadingSymptoms, setLoadingSymptoms] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [healthLoading, setHealthLoading] = useState(false);
  const [healthError, setHealthError] = useState('');
  const [healthResult, setHealthResult] = useState('');
  const [healthSources, setHealthSources] = useState<PsychologySource[]>([]);

  // ── Feature 4: OSCE Virtual Patient & Clinical Sandbox State ──
  const [osceCases, setOsceCases] = useState<OsceCasePublic[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('case_mdd_severe');
  const [osceMessages, setOsceMessages] = useState<OsceMessage[]>([]);
  const [osceInput, setOsceInput] = useState('');
  const [osceChatLoading, setOsceChatLoading] = useState(false);
  const [administeredScales, setAdministeredScales] = useState<OsceScaleItem[]>([]);

  // OSCE Diagnostic & Treatment Submission
  const [primaryDiagnosis, setPrimaryDiagnosis] = useState('');
  const [differentialDiagnosis, setDifferentialDiagnosis] = useState('');
  const [treatmentPlan, setTreatmentPlan] = useState('');
  const [osceEvaluating, setOsceEvaluating] = useState(false);
  const [osceEvaluation, setOsceEvaluation] = useState<OsceEvaluationResult | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);

  const getUserId = (): string | undefined => {
    if (user?.id) return user.id;
    if (typeof window === 'undefined') return undefined;
    return localStorage.getItem('user_id') ?? undefined;
  };

  const fetchSymptoms = async () => {
    const uid = getUserId();
    if (!uid) {
      setLoadError('Please log in to view your health profile.');
      setLoadingSymptoms(false);
      return;
    }
    setLoadingSymptoms(true);
    setLoadError('');
    try {
      const profile = await getProfileSymptoms(uid);
      setSymptoms(profile.symptoms);
    } catch (err: unknown) {
      const errWithResponse = err as { response?: { data?: { detail?: string } } };
      const msg = errWithResponse?.response?.data?.detail;
      setLoadError(msg || 'Failed to load profile. Check server connection.');
    } finally {
      setLoadingSymptoms(false);
    }
  };

  useEffect(() => {
    fetchSymptoms();
    listOsceCases()
      .then((res) => {
        if (res.cases && res.cases.length > 0) {
          setOsceCases(res.cases);
          initOsceCase(res.cases[0]);
        }
      })
      .catch(console.error);
  }, []);

  const initOsceCase = (c: OsceCasePublic) => {
    setSelectedCaseId(c.case_id);
    setOsceMessages([
      {
        role: 'patient',
        content: `Chào bác sĩ... Tôi là ${c.patient_name} (${c.patient_age} tuổi, ${c.occupation}). ${c.chief_complaint}`,
      },
    ]);
    setAdministeredScales([]);
    setPrimaryDiagnosis('');
    setDifferentialDiagnosis('');
    setTreatmentPlan('');
    setOsceEvaluation(null);
  };

  const currentOsceCase = osceCases.find((c) => c.case_id === selectedCaseId) || null;

  const handleSendOsceMessage = async (customMsg?: string, requestScale?: string) => {
    const msgToSend = (customMsg ?? osceInput).trim();
    if ((!msgToSend && !requestScale) || osceChatLoading) return;

    const displayClinicianMsg = requestScale
      ? `[Chỉ định Thang đo Lâm sàng: ${requestScale}] ${msgToSend || `Bác sĩ tiến hành đánh giá thang đo ${requestScale} cho bệnh nhân.`}`
      : msgToSend;

    const nextHistory: OsceMessage[] = [
      ...osceMessages,
      { role: 'clinician', content: displayClinicianMsg },
    ];
    setOsceMessages(nextHistory);
    if (!customMsg) setOsceInput('');
    setOsceChatLoading(true);

    try {
      const res = await chatOscePatient({
        case_id: selectedCaseId,
        messages: nextHistory.map((m) => ({
          role: m.role === 'clinician' ? 'user' : 'assistant',
          content: m.content,
        })),
        administer_scale: requestScale || undefined,
      });

      const scaleObj: OsceScaleItem | null =
        res.scale_code && res.total_score
          ? {
              scale_code: res.scale_code,
              total_score: res.total_score,
              severity: res.severity || '',
              breakdown: res.breakdown,
            }
          : null;

      if (scaleObj) {
        setAdministeredScales((prev) => {
          if (prev.some((s) => s.scale_code === scaleObj.scale_code)) return prev;
          return [...prev, scaleObj];
        });
      }

      setOsceMessages((prev) => [
        ...prev,
        {
          role: 'patient',
          content: cleanMarkdownText(res.patient_reply),
          scaleResult: scaleObj,
        },
      ]);
      setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    } catch (e) {
      console.error('OSCE chat error:', e);
    } finally {
      setOsceChatLoading(false);
    }
  };

  const handleEvaluateOsce = async () => {
    if (!primaryDiagnosis.trim() || !treatmentPlan.trim() || osceEvaluating) return;
    setOsceEvaluating(true);
    try {
      const res = await evaluateOsceSession({
        case_id: selectedCaseId,
        messages: osceMessages.map((m) => ({
          role: m.role === 'clinician' ? 'user' : 'assistant',
          content: m.content,
        })),
        administered_scales: administeredScales.map((s) => s.scale_code),
        user_diagnosis: primaryDiagnosis.trim(),
        user_differential: differentialDiagnosis.trim(),
        user_treatment: treatmentPlan.trim(),
      });
      setOsceEvaluation(res);
    } catch (e) {
      console.error('OSCE evaluation error:', e);
    } finally {
      setOsceEvaluating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Remove this symptom from profile?')) return;
    setDeletingId(id);
    try {
      await deleteSymptom(id);
      setSymptoms((prev) => prev.filter((s) => s.id !== id));
    } catch {
      setLoadError('Failed to delete. Try again.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleAnalyze = async () => {
    const uid = getUserId();
    if (!uid) {
      setHealthError('Please log in.');
      setModalOpen(true);
      return;
    }

    setHealthLoading(true);
    setHealthError('');
    setHealthResult('');
    setHealthSources([]);
    setModalOpen(true);

    try {
      const profile = await getProfileSymptoms(uid);
      const fresh = profile.symptoms;
      setSymptoms(fresh);

      if (fresh.length === 0) {
        setHealthError('You have not reported any symptoms in the 3D body model. Go to /3d → click a body part → "Report Symptoms" first.');
        setHealthLoading(false);
        return;
      }

      const aggregated = fresh
        .map((s, i) => `${i + 1}. [${s.region_name}] Pain Level ${s.pain_level}/10${s.duration ? `, duration: ${s.duration}` : ''}: ${s.description}`)
        .join('\n');

      const prompt =
        `Based on the following physical symptoms reported by the user in the 3D body model:\n\n${aggregated}\n\n` +
        `Please analyze ONLY the psychological and mental health aspects that may be relevant (if any). ` +
        `If symptoms are not related to psychology, clearly state "insufficient psychological signs for analysis", DO NOT guess other conditions.\n\n` +
        `Respond in exactly 3 sections using plain text (DO NOT use any markdown syntax like ##, **, -, or tables):\n\n` +
        `1. POTENTIALLY RELATED PSYCHOLOGICAL ISSUES\n` +
        `List potential psychological disorders/conditions with suggested severity: low/medium/high. If none, state "No clear psychological signs detected".\n\n` +
        `2. RECOMMENDATIONS\n` +
        `Specific actions the user can take: self-care, lifestyle changes, when to see a mental health professional.\n\n` +
        `3. SUGGESTED MENTAL HEALTH FACILITIES\n` +
        `List 3-5 reputable mental health facilities: name, address, hotline. If unsure, state "Please check with your local health department".\n\n` +
        `IMPORTANT: Use only plain text. Use line breaks and numbering for structure. Do NOT use any markdown formatting symbols.`;

      const docs = await getDocuments();
      const readyDocs: DocumentInfo[] = docs.filter((d) => d.status === 'ready').slice(0, 10);
      const docIds = readyDocs.map((d) => d.id);

      const data = await analyzeSymptoms(prompt, docIds, 8);
      setHealthResult(data.analysis);
      setHealthSources(data.sources);
    } catch (err: unknown) {
      const errWithResponse = err as { response?: { data?: { detail?: string } } };
      const msg = errWithResponse?.response?.data?.detail;
      setHealthError(msg || 'Analysis failed. Please try again.');
    } finally {
      setHealthLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-surface-base transition-colors duration-500">
      {/* Header */}
      <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-6xl mx-auto px-4 md:px-6 py-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-cortex-500 to-neural-500 flex items-center justify-center shadow-lg shadow-cortex-500/25">
                <HeartPulse className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  Phòng Lâm sàng Tâm lý & Hồ sơ Sức khỏe (OSCE & 3D Health)
                </h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Mô phỏng Bệnh nhân Ảo DSM-5 / ICD-11 (OSCE Clinical Sandbox) & Phân tích Triệu chứng Tâm thể 3D
                </p>
              </div>
            </div>

            {/* Tab Switcher */}
            <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 p-1 rounded-xl">
              <button
                type="button"
                onClick={() => setActiveTab('osce')}
                className={`px-3.5 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                  activeTab === 'osce'
                    ? 'bg-white dark:bg-gray-900 text-teal-600 dark:text-teal-400 shadow-xs'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900'
                }`}
              >
                <UserCheck className="w-4 h-4" />
                <span>Phòng Mô phỏng Bệnh nhân Ảo (OSCE)</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('profile')}
                className={`px-3.5 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                  activeTab === 'profile'
                    ? 'bg-white dark:bg-gray-900 text-teal-600 dark:text-teal-400 shadow-xs'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900'
                }`}
              >
                <Stethoscope className="w-4 h-4" />
                <span>Hồ sơ Triệu chứng 3D ({symptoms.length})</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════════════════════
          TAB 1: FEATURE 4 — AI VIRTUAL PATIENT & OSCE CLINICAL SANDBOX (DSM-5 / ICD-11)
         ══════════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'osce' && (
        <div className="max-w-6xl mx-auto px-4 md:px-6 py-6 space-y-6">
          {/* Case Selector Bar */}
          <NeuralCard variant="elevated" padding="md">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
              <div>
                <h2 className="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <span>🏥 Chọn Ca Lâm sàng Mô phỏng Chuẩn hóa (DSM-5 / ICD-11 OSCE Scenarios)</span>
                </h2>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  AI đóng vai bệnh nhân với hồ sơ bệnh sử ẩn. Hãy hỏi bệnh, chỉ định thang đo tâm lý và lập chẩn đoán để hệ thống chấm điểm OSCE (thang 100 điểm).
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {osceCases.map((c) => {
                const isSel = c.case_id === selectedCaseId;
                return (
                  <button
                    key={c.case_id}
                    type="button"
                    onClick={() => initOsceCase(c)}
                    className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                      isSel
                        ? 'border-teal-500 bg-teal-50/60 dark:bg-teal-950/30 shadow-sm'
                        : 'border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-teal-300'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="font-bold text-xs text-gray-900 dark:text-white">
                        {c.avatar_emoji} {c.patient_name} ({c.patient_age}t)
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-teal-500/15 text-teal-700 dark:text-teal-300">
                        {c.occupation}
                      </span>
                    </div>
                    <p className="text-[11px] font-semibold text-indigo-600 dark:text-indigo-400 mb-0.5">
                      {cleanMarkdownText(c.title)} • {c.difficulty}
                    </p>
                    <p className="text-[11px] text-gray-600 dark:text-gray-300 line-clamp-2 leading-relaxed">
                      Than phiền chính: “{c.chief_complaint}”
                    </p>
                  </button>
                );
              })}
            </div>
          </NeuralCard>

          {/* Main 2-Column Clinical Sandbox */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left 7 Cols: Interactive Clinical Interview & Psychometric Scale Lab */}
            <div className="lg:col-span-7 flex flex-col gap-4">
              <NeuralCard variant="elevated" padding="md" className="flex flex-col h-[560px]">
                <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-800 pb-3 mb-3">
                  <div>
                    <h3 className="text-sm font-bold text-gray-900 dark:text-white">
                      💬 Phòng Vấn chẩn Lâm sàng (Clinical Interview) — {currentOsceCase?.patient_name}
                    </h3>
                    <p className="text-[11px] text-gray-500 dark:text-gray-400">
                      Số lượt hỏi bệnh: {osceMessages.filter((m) => m.role === 'clinician').length} lượt • Thang đo đã chỉ định: {administeredScales.length}
                    </p>
                  </div>
                  {currentOsceCase && (
                    <button
                      type="button"
                      onClick={() => {
                        const targetReg = currentOsceCase.case_id.includes('mdd')
                          ? 'prefrontal_cortex'
                          : currentOsceCase.case_id.includes('gad')
                          ? 'amygdala'
                          : 'hippocampus';
                        router.push(`/3d?region=${targetReg}&xray=1`);
                      }}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-bold bg-indigo-600 hover:bg-indigo-700 text-white cursor-pointer"
                    >
                      <Brain className="w-3.5 h-3.5" />
                      <span>Xem Não 3D X-Ray</span>
                    </button>
                  )}
                </div>

                {/* Psychometric Scale Quick Buttons */}
                <div className="flex flex-wrap items-center gap-1.5 mb-3">
                  <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 mr-1">
                    📋 Chỉ định Thang đo Tâm lý:
                  </span>
                  {(currentOsceCase?.available_scales || ['PHQ-9', 'GAD-7', 'BDI-II', 'DASS-21']).map((sc) => {
                    const done = administeredScales.some((s) => s.scale_code === sc);
                    return (
                      <button
                        key={sc}
                        type="button"
                        disabled={osceChatLoading}
                        onClick={() => handleSendOsceMessage(`Thực hiện đánh giá thang đo ${sc}`, sc)}
                        className={`px-2.5 py-1 rounded-lg text-[11px] font-bold border transition-all cursor-pointer ${
                          done
                            ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/30'
                            : 'bg-violet-50 hover:bg-violet-100 dark:bg-violet-950/50 text-violet-700 dark:text-violet-300 border-violet-200 dark:border-violet-800'
                        }`}
                      >
                        {done ? `✓ ${sc}` : `+ Đo ${sc}`}
                      </button>
                    );
                  })}
                </div>

                {/* Interview Messages */}
                <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                  {osceMessages.map((m, idx) => (
                    <div
                      key={idx}
                      className={`flex flex-col ${m.role === 'clinician' ? 'items-end' : 'items-start'}`}
                    >
                      <div
                        className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-xs leading-relaxed ${
                          m.role === 'clinician'
                            ? 'bg-teal-600 text-white'
                            : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-100 border border-gray-200 dark:border-gray-700'
                        }`}
                      >
                        <div className="font-bold text-[10px] uppercase tracking-wider opacity-75 mb-0.5">
                          {m.role === 'clinician' ? 'Bác sĩ / Nhà lâm sàng' : `Bệnh nhân (${currentOsceCase?.patient_name})`}
                        </div>
                        <p>{m.content}</p>
                      </div>

                      {m.scaleResult && (
                        <div className="mt-1.5 max-w-[85%] p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-xs">
                          <div className="font-bold text-amber-900 dark:text-amber-300">
                            📊 Kết quả Thang đo {m.scaleResult.scale_code}: {m.scaleResult.total_score}
                          </div>
                          <div className="text-[11px] text-amber-800 dark:text-amber-200">
                            Phân loại mức độ: {m.scaleResult.severity}
                          </div>
                          {m.scaleResult.breakdown && (
                            <div className="text-[10.5px] text-amber-700 dark:text-amber-300 mt-0.5">
                              {cleanMarkdownText(m.scaleResult.breakdown)}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                  {osceChatLoading && (
                    <div className="text-xs text-gray-400 italic">Bệnh nhân đang trả lời...</div>
                  )}
                  <div ref={chatEndRef} />
                </div>

                {/* Suggested Clinical Questions */}
                <div className="flex flex-wrap gap-1.5 pt-2 border-t border-gray-100 dark:border-gray-800 mt-2">
                  {[
                    'Tình trạng này kéo dài bao lâu và ảnh hưởng công việc thế nào?',
                    'Bạn có từng xuất hiện ý nghĩ bi quan hay muốn làm hại bản thân không?',
                    'Giấc ngủ và các triệu chứng cơ thể (tim đập nhanh, đau đầu) diễn ra ra sao?',
                  ].map((q, idx) => (
                    <button
                      key={idx}
                      type="button"
                      disabled={osceChatLoading}
                      onClick={() => handleSendOsceMessage(q)}
                      className="text-[10.5px] px-2.5 py-1 rounded-full bg-gray-100 hover:bg-teal-50 dark:bg-gray-800 dark:hover:bg-teal-950/50 text-gray-600 dark:text-gray-300 transition-colors cursor-pointer truncate max-w-full"
                    >
                      “{q}”
                    </button>
                  ))}
                </div>

                {/* Chat Input */}
                <div className="flex items-center gap-2 mt-2.5">
                  <input
                    value={osceInput}
                    onChange={(e) => setOsceInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleSendOsceMessage();
                      }
                    }}
                    placeholder="Nhập câu hỏi khai thác triệu chứng lâm sàng (DSM-5 / ICD-11)..."
                    className="flex-1 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3.5 py-2 text-xs text-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-teal-500/40"
                  />
                  <button
                    type="button"
                    disabled={!osceInput.trim() || osceChatLoading}
                    onClick={() => handleSendOsceMessage()}
                    className="px-3.5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold disabled:opacity-50 cursor-pointer flex items-center gap-1"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Hỏi</span>
                  </button>
                </div>
              </NeuralCard>
            </div>

            {/* Right 5 Cols: OSCE Diagnostic Submission & 100-Point Rubric Grading */}
            <div className="lg:col-span-5 flex flex-col gap-4">
              <NeuralCard variant="elevated" padding="md">
                <div className="flex items-center gap-2 mb-3 border-b border-gray-200 dark:border-gray-800 pb-3">
                  <ClipboardCheck className="w-5 h-5 text-teal-600 dark:text-teal-400" />
                  <div>
                    <h3 className="text-sm font-bold text-gray-900 dark:text-white">
                      Phiếu Lập Chẩn đoán & Phác đồ Điều trị (OSCE Exam)
                    </h3>
                    <p className="text-[11px] text-gray-500 dark:text-gray-400">
                      Hệ thống chấm điểm tự động trên thang 100 điểm theo chuẩn DSM-5 / ICD-11
                    </p>
                  </div>
                </div>

                <div className="space-y-3 text-xs">
                  <div>
                    <label className="block font-bold text-gray-700 dark:text-gray-300 mb-1">
                      1. Chẩn đoán Sơ bộ (DSM-5 / ICD-11 Primary Diagnosis) *
                    </label>
                    <input
                      value={primaryDiagnosis}
                      onChange={(e) => setPrimaryDiagnosis(e.target.value)}
                      placeholder="VD: Rối loạn Trầm cảm Chủ yếu (MDD - F32.1) mức độ trung bình - nặng"
                      className="w-full rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-xs text-gray-800 dark:text-gray-100"
                    />
                  </div>

                  <div>
                    <label className="block font-bold text-gray-700 dark:text-gray-300 mb-1">
                      2. Chẩn đoán Phân biệt (Differential Diagnosis)
                    </label>
                    <input
                      value={differentialDiagnosis}
                      onChange={(e) => setDifferentialDiagnosis(e.target.value)}
                      placeholder="VD: Rối loạn Lo âu Lan tỏa (GAD), Rối loạn Thích ứng, Suy giáp"
                      className="w-full rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-xs text-gray-800 dark:text-gray-100"
                    />
                  </div>

                  <div>
                    <label className="block font-bold text-gray-700 dark:text-gray-300 mb-1">
                      3. Kế hoạch Can thiệp & Trị liệu Dựa trên Bằng chứng (Treatment Plan) *
                    </label>
                    <textarea
                      rows={3}
                      value={treatmentPlan}
                      onChange={(e) => setTreatmentPlan(e.target.value)}
                      placeholder="VD: Liệu pháp Nhận thức Hành vi (CBT - tái cấu trúc nhận thức & kích hoạt hành vi) kết hợp SSRI (Sertraline/Escitalopram) và theo dõi PHQ-9 định kỳ..."
                      className="w-full rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-xs text-gray-800 dark:text-gray-100"
                    />
                  </div>

                  <button
                    type="button"
                    onClick={handleEvaluateOsce}
                    disabled={!primaryDiagnosis.trim() || !treatmentPlan.trim() || osceEvaluating}
                    className="w-full py-2.5 rounded-xl bg-gradient-to-r from-teal-600 to-indigo-600 hover:opacity-95 text-white font-bold text-xs shadow-md disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2"
                  >
                    {osceEvaluating ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Đang chấm điểm bệnh án OSCE...</span>
                      </>
                    ) : (
                      <>
                        <Award className="w-4 h-4" />
                        <span>Nộp Bệnh Án & Chấm Điểm OSCE (Thang 100)</span>
                      </>
                    )}
                  </button>
                </div>

                {/* OSCE Grading Result Panel */}
                {osceEvaluation && (
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-800 space-y-3 text-xs">
                    <div className="p-3.5 rounded-xl bg-gradient-to-r from-teal-500/10 to-indigo-500/10 border border-teal-500/30 flex items-center justify-between">
                      <div>
                        <div className="text-[11px] font-bold uppercase tracking-wider text-teal-700 dark:text-teal-300">
                          Tổng điểm Hội đồng Lâm sàng OSCE
                        </div>
                        <div className="text-2xl font-extrabold text-gray-900 dark:text-white font-mono">
                          {osceEvaluation.total_score} / 100 điểm
                        </div>
                      </div>
                      <span className="px-3 py-1 rounded-full bg-teal-600 text-white font-bold text-xs">
                        {osceEvaluation.grade_rank}
                      </span>
                    </div>

                    {/* 4 Rubric Bars */}
                    <div className="space-y-2.5 bg-gray-50 dark:bg-gray-900/70 p-3 rounded-xl border border-gray-200 dark:border-gray-800">
                      {osceEvaluation.rubric_breakdown.map((r, idx) => (
                        <div key={idx} className="space-y-1">
                          <div className="flex justify-between text-[11px] font-semibold">
                            <span>{cleanMarkdownText(r.criterion)}</span>
                            <span className="font-mono">{r.score}/{r.max_score}</span>
                          </div>
                          <div className="w-full h-2 rounded-full bg-gray-200 dark:bg-gray-800 overflow-hidden">
                            <div
                              style={{ width: `${Math.round((r.score / r.max_score) * 100)}%` }}
                              className="h-full bg-teal-500 rounded-full"
                            />
                          </div>
                          <p className="text-[10.5px] text-gray-500 dark:text-gray-400">
                            {cleanMarkdownText(r.comment)}
                          </p>
                        </div>
                      ))}
                    </div>

                    {/* Gold Standard Reveal */}
                    <div className="p-3 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800/60 space-y-1.5">
                      <div className="font-bold text-indigo-900 dark:text-indigo-300">
                        🔑 Đáp án Chuẩn Vàng Lâm sàng (Gold Standard):
                      </div>
                      <div>
                        <span className="font-semibold">Chẩn đoán Chính: </span>
                        <span>{cleanMarkdownText(osceEvaluation.ground_truth_revealed.primary_diagnosis)}</span>
                      </div>
                      <div>
                        <span className="font-semibold">Chẩn đoán Phân biệt: </span>
                        <span>{cleanMarkdownText(osceEvaluation.ground_truth_revealed.differential_diagnosis)}</span>
                      </div>
                      <div>
                        <span className="font-semibold">Vùng não Giải phẫu 3D: </span>
                        <button
                          type="button"
                          onClick={() => router.push(`/3d?region=${osceEvaluation.ground_truth_revealed.target_brain_region_3d}&xray=1`)}
                          className="text-indigo-600 dark:text-indigo-400 font-bold underline cursor-pointer"
                        >
                          {cleanMarkdownText(osceEvaluation.ground_truth_revealed.target_brain_label)} (Mở 3D X-Ray)
                        </button>
                      </div>
                      <div>
                        <span className="font-semibold">Phác đồ Chuẩn: </span>
                        <span>{cleanMarkdownText(osceEvaluation.ground_truth_revealed.evidence_treatment)}</span>
                      </div>
                      <div className="text-[10.5px] text-gray-500 italic">
                        📚 {cleanMarkdownText(osceEvaluation.ground_truth_revealed.cited_evidence)}
                      </div>
                    </div>
                  </div>
                )}
              </NeuralCard>
            </div>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════════════
          TAB 2: 3D SYMPTOM PROFILE & PSYCHOSOMATIC ANALYSIS
         ══════════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'profile' && (
        <>
          <div className="max-w-5xl mx-auto px-4 md:px-6 py-4 flex items-center justify-between">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {loadingSymptoms
                ? '⏳ Loading profile...'
                : symptoms.length === 0
                ? '⚠️ No symptoms yet — go to 3D Body Model to report first.'
                : `✓ Ready to analyze ${symptoms.length} reported symptoms.`}
            </p>
            <NeuralButton
              variant="primary"
              onClick={handleAnalyze}
              loading={healthLoading}
              icon={<Stethoscope className="w-4 h-4" />}
            >
              Health Analysis
            </NeuralButton>
          </div>

          <div className="max-w-5xl mx-auto px-4 md:px-6 pb-8">
            {loadError && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-start gap-3 p-4 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 mb-6"
              >
                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
                <p className="text-sm text-red-700 dark:text-red-300">{loadError}</p>
              </motion.div>
            )}

            {loadingSymptoms && (
              <div className="flex flex-col items-center justify-center py-16">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-neural-500 to-cortex-500 flex items-center justify-center mb-4 animate-pulse">
                  <Brain className="w-6 h-6 text-white" />
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Loading profile...</p>
              </div>
            )}

            {!loadingSymptoms && !loadError && symptoms.length === 0 && (
              <NeuralCard variant="glass" className="text-center py-16">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-neural-100 to-cortex-100 dark:from-neural-900/50 dark:to-cortex-900/50 flex items-center justify-center mb-6">
                  <Brain className="w-8 h-8 text-neural-600 dark:text-neural-400" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                  No data yet
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto mb-6">
                  Go to the 3D Body Model, click on body parts and press <strong>&quot;Report Symptoms&quot;</strong> to report.
                </p>
                <a
                  href="/3d"
                  className="btn-neural inline-flex items-center gap-2"
                >
                  <ExternalLink className="w-4 h-4" />
                  Open 3D Body Model
                </a>
              </NeuralCard>
            )}

            {!loadingSymptoms && symptoms.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-bold text-gray-700 dark:text-gray-200">
                    Reported Data ({symptoms.length})
                  </h2>
                  <button
                    onClick={fetchSymptoms}
                    className="text-xs text-gray-400 hover:text-neural-600 transition-colors"
                  >
                    Refresh
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {symptoms.map((s, i) => (
                    <motion.div
                      key={s.id ?? i}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="neural-card p-5 relative"
                    >
                      {s.id && (
                        <button
                          onClick={() => handleDelete(s.id!)}
                          disabled={deletingId === s.id}
                          className="absolute top-3 right-3 w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50"
                          title="Delete symptom"
                        >
                          {deletingId === s.id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Trash2 className="w-3.5 h-3.5" />
                          )}
                        </button>
                      )}

                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-neural-100 to-cortex-100 dark:from-neural-900/50 dark:to-cortex-900/50 flex items-center justify-center text-xs font-bold text-neural-600 dark:text-neural-400">
                          {i + 1}
                        </div>
                        <div className="flex-1">
                          <p className="font-semibold text-gray-900 dark:text-white">{s.region_name}</p>
                          <PainBadge level={s.pain_level} />
                        </div>
                      </div>

                      <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                        {s.description}
                      </p>

                      <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
                        {s.duration && <span>⏱ {s.duration}</span>}
                        {s.reported_at && (
                          <span>Reported: {new Date(s.reported_at).toLocaleDateString('en-US')}</span>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {/* Analysis Modal */}
      <AnimatePresence>
        {modalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
            onClick={() => setModalOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              transition={{ type: 'spring', damping: 25 }}
              onClick={(e) => e.stopPropagation()}
              className="relative w-full max-w-4xl max-h-[90vh] bg-white dark:bg-gray-900 rounded-2xl shadow-2xl flex flex-col overflow-hidden"
            >
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800 bg-gradient-to-r from-neural-50 to-cortex-50 dark:from-neural-950/30 dark:to-cortex-950/30">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-neural-500 to-cortex-500 flex items-center justify-center">
                    <Stethoscope className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-gray-900 dark:text-white">
                      Mental Health Analysis
                    </h2>
                    <p className="text-xs text-gray-500">
                      AI analysis from {symptoms.length} reported symptoms
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setModalOpen(false)}
                  className="p-2 rounded-xl text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {healthError && !healthLoading && (
                  <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800">
                    <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                        {healthError}
                      </p>
                      {healthError.includes('not reported') && (
                        <a href="/3d" className="text-xs text-neural-600 dark:text-neural-400 underline mt-1 inline-block">
                          → Open 3D Body Model
                        </a>
                      )}
                    </div>
                  </div>
                )}

                {healthLoading && (
                  <div className="flex flex-col items-center justify-center py-12">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-neural-500 to-cortex-500 flex items-center justify-center mb-4 animate-pulse">
                      <Sparkles className="w-6 h-6 text-white" />
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      AI is analyzing health profile...
                    </p>
                  </div>
                )}

                {healthResult && !healthLoading && (
                  <div className="space-y-4">
                    <div className="rounded-xl p-5 bg-gradient-to-br from-neural-50/50 to-cortex-50/50 dark:from-neural-950/20 dark:to-cortex-950/20 border border-neural-100 dark:border-neural-800">
                      <AcademicDocumentRenderer content={healthResult} />
                    </div>

                    {healthSources.length > 0 && (
                      <div>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">
                          📎 References ({healthSources.length} excerpts)
                        </h4>
                        <div className="grid gap-2">
                          {healthSources.map((src, i) => (
                            <SourceCard key={i} source={src} index={i} />
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/60 rounded-xl px-4 py-3 text-xs text-amber-700 dark:text-amber-300 leading-relaxed">
                      ⚠️ <strong>Important:</strong> Results are for reference only regarding <strong>psychological aspects</strong>,
                      based on RAG from psychology document library. Not a medical diagnosis.
                      Please consult a licensed clinical psychologist.
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Sub-components ───────────────────────────────────────────────

function PainBadge({ level }: { level: number }) {
  const variant = level >= 8 ? 'error' : level >= 5 ? 'warning' : level >= 3 ? 'neural' : 'success';
  return (
    <NeuralBadge variant={variant} size="sm">
      Pain {level}/10
    </NeuralBadge>
  );
}

function SourceCard({ source, index }: { source: PsychologySource; index: number }) {
  const isWebSource = !source.document_id && source.doc_authors?.startsWith('http');
  return (
    <div className="flex gap-3 text-xs text-gray-600 dark:text-gray-300 bg-neural-50 dark:bg-neural-950/30 rounded-lg px-4 py-3">
      <span className={`font-bold flex-shrink-0 ${isWebSource ? 'text-cortex-600 dark:text-cortex-400' : 'text-neural-600 dark:text-neural-400'}`}>
        [{index + 1}]
      </span>
      <div className="min-w-0">
        <p className="font-medium text-gray-900 dark:text-gray-200">{source.doc_title || 'Untitled'}</p>
        {isWebSource ? (
          <a
            href={source.doc_authors}
            target="_blank"
            rel="noopener noreferrer"
            className="text-cortex-500 hover:text-cortex-400 truncate block transition-colors"
          >
            🌐 {source.doc_authors}
          </a>
        ) : (
          <>
            {source.doc_authors && <p className="text-gray-400">{source.doc_authors}</p>}
            {source.page_number != null && <p className="text-gray-400">Page {source.page_number}</p>}
          </>
        )}
      </div>
    </div>
  );
}
