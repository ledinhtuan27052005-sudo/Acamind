'use client';

import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
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
} from 'lucide-react';
import {
  PsychologySource,
  SymptomRecord,
  analyzeSymptoms,
  deleteSymptom,
  getDocuments,
  getProfileSymptoms,
  type DocumentInfo,
} from '@/lib/api';
import { useAppStore } from '@/store/useAppStore';
import { NeuralCard } from '@/components/ui/NeuralCard';
import { NeuralBadge } from '@/components/ui/NeuralBadge';
import { NeuralButton } from '@/components/ui/NeuralButton';

export default function PsychologyPage() {
  const { user } = useAppStore();
  const [symptoms, setSymptoms] = useState<SymptomRecord[]>([]);
  const [loadingSymptoms, setLoadingSymptoms] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [healthLoading, setHealthLoading] = useState(false);
  const [healthError, setHealthError] = useState('');
  const [healthResult, setHealthResult] = useState('');
  const [healthSources, setHealthSources] = useState<PsychologySource[]>([]);

  const getUserId = (): string | undefined => {
    if (user?.id) return user.id;
    if (typeof window === 'undefined') return undefined;
    return localStorage.getItem('user_id') ?? undefined;
  };

  const fetchSymptoms = async () => {
    const uid = getUserId();
    if (!uid) {
      setLoadError('Vui lòng đăng nhập để xem hồ sơ sức khoẻ.');
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
      setLoadError(msg || 'Không thể tải hồ sơ. Kiểm tra kết nối server.');
    } finally {
      setLoadingSymptoms(false);
    }
  };

  useEffect(() => {
    fetchSymptoms();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm('Xoá triệu chứng này khỏi hồ sơ?')) return;
    setDeletingId(id);
    try {
      await deleteSymptom(id);
      setSymptoms((prev) => prev.filter((s) => s.id !== id));
    } catch {
      setLoadError('Không thể xoá. Thử lại.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleAnalyze = async () => {
    const uid = getUserId();
    if (!uid) {
      setHealthError('Vui lòng đăng nhập.');
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
        setHealthError('Bạn chưa khai báo triệu chứng nào ở Mô hình 3D cơ thể. Vào /body → click bộ phận → "Báo cáo triệu chứng" trước.');
        setHealthLoading(false);
        return;
      }

      const aggregated = fresh
        .map((s, i) => `${i + 1}. [${s.region_name}] Mức đau ${s.pain_level}/10${s.duration ? `, kéo dài ${s.duration}` : ''}: ${s.description}`)
        .join('\n');

      const prompt =
        `Dựa trên các triệu chứng thể chất sau đây do người dùng khai báo ở mô hình 3D cơ thể:\n\n${aggregated}\n\n` +
        `Hãy phân tích CHỈ về khía cạnh **tâm lý** và **sức khỏe tâm thần** có thể liên quan (nếu có). ` +
        `Nếu triệu chứng không liên quan đến tâm lý, nói rõ là "không đủ dấu hiệu tâm lý để phân tích", KHÔNG đoán mò các bệnh lý khác.\n\n` +
        `Trả lời theo đúng 3 phần sau, dùng tiêu đề Markdown ##:\n` +
        `## 1. Các vấn đề tâm lý có thể liên quan\n` +
        `(Liệt kê các rối loạn/tình trạng tâm lý có thể liên quan — kèm mức độ gợi ý: thấp/trung bình/cao. Nếu không có, ghi "Không phát hiện dấu hiệu tâm lý rõ ràng".)\n\n` +
        `## 2. Lời khuyên\n` +
        `(Hành động cụ thể người dùng có thể làm: tự chăm sóc, thay đổi lối sống, khi nào nên đi khám chuyên gia tâm lý.)\n\n` +
        `## 3. Bệnh viện / Phòng khám tâm lý gợi ý\n` +
        `(Liệt kê 3-5 cơ sở y tế/phòng khám tâm lý uy tín tại Việt Nam: tên, địa chỉ, hotline. Nếu không chắc chắn, ghi "Vui lòng tra cứu thêm tại Sở Y tế địa phương".)`;

      const docs = await getDocuments();
      const readyDocs: DocumentInfo[] = docs.filter((d) => d.status === 'ready').slice(0, 10);
      if (readyDocs.length === 0) {
        setHealthError('Chưa có tài liệu tâm lý. Vào Thư viện để upload PDF tâm lý học trước.');
        setHealthLoading(false);
        return;
      }
      const docIds = readyDocs.map((d) => d.id);

      const data = await analyzeSymptoms(prompt, docIds, 8);
      setHealthResult(data.analysis);
      setHealthSources(data.sources);
    } catch (err: unknown) {
      const errWithResponse = err as { response?: { data?: { detail?: string } } };
      const msg = errWithResponse?.response?.data?.detail;
      setHealthError(msg || 'Không thể phân tích. Vui lòng thử lại.');
    } finally {
      setHealthLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-surface-base transition-colors duration-500">
      {/* Header */}
      <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-5xl mx-auto px-4 md:px-6 py-6">
          <div className="flex items-center justify-between gap-4">
            {/* Title */}
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-cortex-500 to-neural-500 flex items-center justify-center shadow-lg shadow-cortex-500/25">
                <HeartPulse className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  Hồ sơ sức khỏe
                </h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Dữ liệu được khai báo từ Mô hình 3D cơ thể
                </p>
              </div>
            </div>

            {/* Action Button */}
            <NeuralButton
              variant="primary"
              onClick={handleAnalyze}
              loading={healthLoading}
              icon={<Stethoscope className="w-4 h-4" />}
            >
              Phân tích sức khoẻ
            </NeuralButton>
          </div>
        </div>
      </div>

      {/* Helper text */}
      <div className="max-w-5xl mx-auto px-4 md:px-6 py-4">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {loadingSymptoms
            ? '⏳ Đang tải hồ sơ...'
            : symptoms.length === 0
            ? '⚠️ Chưa có triệu chứng nào — vào Mô hình 3D cơ thể để khai báo trước.'
            : `✓ Sẵn sàng phân tích ${symptoms.length} triệu chứng đã khai báo.`}
        </p>
      </div>

      {/* Content */}
      <div className="max-w-5xl mx-auto px-4 md:px-6 pb-8">
        {/* Error */}
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

        {/* Loading */}
        {loadingSymptoms && (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-neural-500 to-cortex-500 flex items-center justify-center mb-4 animate-pulse">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Đang tải hồ sơ...</p>
          </div>
        )}

        {/* Empty state */}
        {!loadingSymptoms && !loadError && symptoms.length === 0 && (
          <NeuralCard variant="glass" className="text-center py-16">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-neural-100 to-cortex-100 dark:from-neural-900/50 dark:to-cortex-900/50 flex items-center justify-center mb-6">
              <Brain className="w-8 h-8 text-neural-600 dark:text-neural-400" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
              Chưa có dữ liệu hồ sơ
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto mb-6">
              Vào Mô hình 3D cơ thể, click vào từng bộ phận và bấm <strong>"Báo cáo triệu chứng"</strong> để khai báo.
            </p>
            <a
              href="/body"
              className="btn-neural inline-flex items-center gap-2"
            >
              <ExternalLink className="w-4 h-4" />
              Mở Mô hình 3D cơ thể
            </a>
          </NeuralCard>
        )}

        {/* Symptom list */}
        {!loadingSymptoms && symptoms.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-gray-700 dark:text-gray-200">
                Dữ liệu đã khai báo ({symptoms.length})
              </h2>
              <button
                onClick={fetchSymptoms}
                className="text-xs text-gray-400 hover:text-neural-600 transition-colors"
              >
                Làm mới
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
                  {/* Delete button */}
                  {s.id && (
                    <button
                      onClick={() => handleDelete(s.id!)}
                      disabled={deletingId === s.id}
                      className="absolute top-3 right-3 w-7 h-7 flex items-center justify-center rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50"
                      title="Xoá triệu chứng"
                    >
                      {deletingId === s.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Trash2 className="w-3.5 h-3.5" />
                      )}
                    </button>
                  )}

                  {/* Header */}
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-neural-100 to-cortex-100 dark:from-neural-900/50 dark:to-cortex-900/50 flex items-center justify-center text-xs font-bold text-neural-600 dark:text-neural-400">
                      {i + 1}
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-gray-900 dark:text-white">{s.region_name}</p>
                      <PainBadge level={s.pain_level} />
                    </div>
                  </div>

                  {/* Description */}
                  <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                    {s.description}
                  </p>

                  {/* Meta */}
                  <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
                    {s.duration && <span>⏱ {s.duration}</span>}
                    {s.reported_at && (
                      <span>Khai báo: {new Date(s.reported_at).toLocaleDateString('vi-VN')}</span>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </div>

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
              {/* Modal Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800 bg-gradient-to-r from-neural-50 to-cortex-50 dark:from-neural-950/30 dark:to-cortex-950/30">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-neural-500 to-cortex-500 flex items-center justify-center">
                    <Stethoscope className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-gray-900 dark:text-white">
                      Phân tích sức khoẻ tâm lý
                    </h2>
                    <p className="text-xs text-gray-500">
                      AI phân tích từ {symptoms.length} triệu chứng đã khai báo
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

              {/* Modal Body */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {/* Error */}
                {healthError && !healthLoading && (
                  <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800">
                    <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                        {healthError}
                      </p>
                      {healthError.includes('chưa khai báo') && (
                        <a href="/body" className="text-xs text-neural-600 dark:text-neural-400 underline mt-1 inline-block">
                          → Mở Mô hình 3D cơ thể
                        </a>
                      )}
                    </div>
                  </div>
                )}

                {/* Loading */}
                {healthLoading && (
                  <div className="flex flex-col items-center justify-center py-12">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-neural-500 to-cortex-500 flex items-center justify-center mb-4 animate-pulse">
                      <Sparkles className="w-6 h-6 text-white" />
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      AI đang phân tích hồ sơ sức khoẻ...
                    </p>
                  </div>
                )}

                {/* Result */}
                {healthResult && !healthLoading && (
                  <div className="space-y-4">
                    <div className="rounded-xl p-5 bg-gradient-to-br from-neural-50/50 to-cortex-50/50 dark:from-neural-950/20 dark:to-cortex-950/20 border border-neural-100 dark:border-neural-800">
                      <div className="prose prose-sm max-w-none text-gray-800 dark:text-gray-200 [&_h2]:text-base [&_h2]:font-bold [&_h2]:text-neural-700 [&_h2]:dark:text-neural-300 [&_h2]:mt-4 [&_h2]:mb-2 [&_h2:first-child]:mt-0 [&_ul]:my-2 [&_li]:my-1">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {healthResult}
                        </ReactMarkdown>
                      </div>
                    </div>

                    {/* Sources */}
                    {healthSources.length > 0 && (
                      <div>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">
                          📎 Nguồn tham khảo ({healthSources.length} đoạn trích)
                        </h4>
                        <div className="grid gap-2">
                          {healthSources.map((src, i) => (
                            <SourceCard key={i} source={src} index={i} />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Disclaimer */}
                    <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800/60 rounded-xl px-4 py-3 text-xs text-amber-700 dark:text-amber-300 leading-relaxed">
                      ⚠️ <strong>Quan trọng:</strong> Kết quả CHỈ mang tính tham khảo về khía cạnh <strong>tâm lý</strong>,
                      dựa trên RAG từ kho tài liệu tâm lý học. Không phải chẩn đoán y khoa.
                      Vui lòng liên hệ chuyên gia tâm lý lâm sàng có chứng chỉ hành nghề.
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
      Đau {level}/10
    </NeuralBadge>
  );
}

function SourceCard({ source, index }: { source: PsychologySource; index: number }) {
  return (
    <div className="flex gap-3 text-xs text-gray-600 dark:text-gray-300 bg-neural-50 dark:bg-neural-950/30 rounded-lg px-4 py-3">
      <span className="text-neural-600 dark:text-neural-400 font-bold flex-shrink-0">[{index + 1}]</span>
      <div>
        <p className="font-medium text-gray-900 dark:text-gray-200">{source.doc_title || 'Tài liệu không tên'}</p>
        {source.doc_authors && <p className="text-gray-400">{source.doc_authors}</p>}
        <p className="text-gray-400">Trang {source.page_number}</p>
      </div>
    </div>
  );
}