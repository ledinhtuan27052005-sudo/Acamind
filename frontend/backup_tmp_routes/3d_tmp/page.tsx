'use client';

import dynamic from 'next/dynamic';
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BODY_DATA, ORGAN_DATA, SYSTEM_COLORS } from '@/lib/bodyData';
import { getDocuments, DocumentInfo, chatStream } from '@/lib/api';
import RegionPanel from '@/components/body/RegionPanel';
import SymptomForm from '@/components/body/SymptomForm';
import { NeuralCard } from '@/components/ui/NeuralCard';
import { NeuralBadge } from '@/components/ui/NeuralBadge';

const BodyViewer3D = dynamic(
  () => import('@/components/body/BodyViewer3D'),
  { ssr: false, loading: () => <LoadingCanvas /> }
);

interface BodyRegion {
  id: string;
  name_vi: string;
  name_latin: string;
  symptoms: string[];
  description_basic: string;
  description_advanced: string;
}

function LoadingCanvas() {
  return (
    <div className="w-full h-full flex items-center justify-center bg-gray-900">
      <div className="text-center">
        <div className="text-5xl mb-4 animate-pulse">🫀</div>
        <p className="text-sm text-gray-400">Đang tải mô hình 3D...</p>
      </div>
    </div>
  );
}

function EmptyPanel() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center px-6 space-y-4">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-neural-100 to-cortex-100 dark:from-neural-900/50 dark:to-cortex-900/50 flex items-center justify-center">
        <span className="text-4xl">🫁</span>
      </div>
      <div>
        <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
          Atlas Giải Phẫu 3D
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
          Click vào từng bộ phận trên mô hình 3D để xem thông tin giải phẫu học chi tiết.
        </p>
      </div>
      <div className="text-xs text-gray-400 dark:text-gray-500 space-y-1.5">
        <p>🖱️ Kéo để xoay mô hình</p>
        <p>🔍 Cuộn để phóng to/thu nhỏ</p>
        <p>👆 Click vào bộ phận để xem chi tiết</p>
      </div>
    </div>
  );
}

function RagDrawer({
  open, query, answer, loading, onClose,
}: {
  open: boolean; query: string; answer: string; loading: boolean; onClose: () => void;
}) {
  if (!open) return null;

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/40 z-20 flex justify-end"
          onClick={onClose}
        >
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-md bg-white dark:bg-gray-900 h-full shadow-xl flex flex-col"
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-gray-800">
              <h3 className="font-semibold text-gray-900 dark:text-white">Kết quả tìm kiếm</h3>
              <button
                onClick={onClose}
                className="w-8 h-8 flex items-center justify-center rounded-xl text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1 font-medium">Câu hỏi:</p>
                <p className="text-sm text-gray-700 dark:text-gray-300 italic">{query}</p>
              </div>
              {loading ? (
                <div className="flex items-center gap-2 text-gray-400">
                  <span className="w-2 h-2 rounded-full bg-neural-500 animate-bounce" />
                  <span className="w-2 h-2 rounded-full bg-neural-500 animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <span className="w-2 h-2 rounded-full bg-neural-500 animate-bounce" style={{ animationDelay: '0.2s' }} />
                  <span className="text-sm ml-2">AI đang trả lời...</span>
                </div>
              ) : (
                <div className="prose-chat text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                  {answer || 'Không tìm thấy thông tin liên quan trong tài liệu.'}
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default function BodyPage() {
  const [selected, setSelected] = useState<string | null>(null);
  const [selectedRegion, setSelectedRegion] = useState<BodyRegion | null>(null);
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [ragQuery, setRagQuery] = useState('');
  const [ragAnswer, setRagAnswer] = useState('');
  const [ragLoading, setRagLoading] = useState(false);
  const [symptomFormOpen, setSymptomFormOpen] = useState(false);
  const [symptomTarget, setSymptomTarget] = useState<{
    id: string; name: string; conditions: string[];
  } | null>(null);
  const [savedCount, setSavedCount] = useState(0);
  const [savedNotif, setSavedNotif] = useState(false);
  const [xray, setXray] = useState(false);

  const getUserType = (): 'patient' | 'student' | 'expert' => {
    if (typeof window === 'undefined') return 'patient';
    return (localStorage.getItem('user_type') ?? 'patient') as 'patient' | 'student' | 'expert';
  };

  useEffect(() => {
    getDocuments()
      .then((d) => setDocs(d.filter((doc) => doc.status === 'ready')))
      .catch(console.error);
  }, []);

  const handleSelect = (id: string) => {
    setSelected(id);
    const bodyInfo = BODY_DATA[id];
    const organInfo = ORGAN_DATA[id];
    if (bodyInfo) {
      setSelectedRegion({
        id: bodyInfo.id,
        name_vi: bodyInfo.name,
        name_latin: '',
        symptoms: bodyInfo.commonConditions,
        description_basic: bodyInfo.description,
        description_advanced: `${bodyInfo.description}\n\nChức năng: ${bodyInfo.functions.join('; ')}`,
      });
    } else if (organInfo) {
      setSelectedRegion({
        id: organInfo.id,
        name_vi: organInfo.name,
        name_latin: organInfo.system,
        symptoms: organInfo.commonConditions,
        description_basic: organInfo.description,
        description_advanced: `${organInfo.description}\n\nChức năng: ${organInfo.functions.join('; ')}`,
      });
    } else {
      setSelectedRegion(null);
    }
  };

  const handleCloseRegion = () => {
    setSelected(null);
    setSelectedRegion(null);
  };

  const handleSearch = async (query: string) => {
    if (docs.length === 0) {
      alert('Chưa có tài liệu nào sẵn sàng. Hãy upload PDF trong Thư viện trước.');
      return;
    }
    setRagQuery(query);
    setRagAnswer('');
    setRagLoading(true);
    setDrawerOpen(true);
    const docIds = docs.map((d) => d.id);
    let full = '';
    try {
      await chatStream(query, docIds, (chunk) => {
        full += chunk;
        setRagAnswer(full);
      });
    } catch (e) {
      setRagAnswer('Lỗi tìm kiếm: ' + (e as Error).message);
    } finally {
      setRagLoading(false);
    }
  };

  const handleReportSymptom = (id: string, name: string) => {
    const info = BODY_DATA[id] ?? ORGAN_DATA[id];
    setSymptomTarget({ id, name, conditions: info?.commonConditions ?? [] });
    setSymptomFormOpen(true);
  };

  const handleSymptomSaved = () => {
    setSavedCount((c) => c + 1);
    setSavedNotif(true);
    setTimeout(() => setSavedNotif(false), 3000);
  };

  const getUserId = () => {
    if (typeof window === 'undefined') return undefined;
    return localStorage.getItem('user_id') ?? undefined;
  };

  const selectedInfo = selected ? (BODY_DATA[selected] ?? ORGAN_DATA[selected] ?? null) : null;

  return (
    <div className="flex h-full relative overflow-hidden">
      {/* 3D Viewer */}
      <div className="flex-1 relative">
        <BodyViewer3D selected={selected} onSelect={handleSelect} xray={xray} />

        {/* Top bar */}
        <div className="absolute top-3 left-1/2 -translate-x-1/2 flex items-center gap-2 pointer-events-none">
          <div className="bg-gray-900/80 backdrop-blur text-gray-300 text-xs px-4 py-2 rounded-full">
            {selected
              ? `✦ ${(BODY_DATA[selected] ?? ORGAN_DATA[selected])?.name ?? selected}`
              : xray
              ? 'X-Ray — Click vào nội tạng để xem chi tiết'
              : 'Click vào bộ phận để xem thông tin'}
          </div>
          <button
            onClick={() => setXray((v) => !v)}
            className={`pointer-events-auto flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 ${
              xray
                ? 'bg-neural-500/90 text-white shadow-lg shadow-neural-500/30'
                : 'bg-gray-800/80 text-gray-300 hover:bg-gray-700/80'
            }`}
          >
            <span className="text-sm">🔬</span>
            {xray ? 'X-Ray BẬT' : 'X-Ray'}
          </button>
        </div>

        {/* Region Panel */}
        <RegionPanel
          region={selectedRegion}
          userType={getUserType()}
          onClose={handleCloseRegion}
          onReportSymptom={handleReportSymptom}
        />

        {/* Saved notification */}
        <AnimatePresence>
          {savedNotif && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="absolute bottom-4 right-4 bg-neural-500 text-white text-xs px-4 py-2 rounded-full shadow-lg"
            >
              ✓ Đã lưu triệu chứng ({savedCount} tổng cộng)
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Sidebar */}
      <div className="w-72 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-800 flex flex-col">
        {/* Systems list */}
        <div className="p-4 border-b border-gray-100 dark:border-gray-800">
          <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3 font-semibold">Hệ thống</p>
          <div className="space-y-3 max-h-72 overflow-auto pr-1">
            {Object.entries(SYSTEM_COLORS).map(([sys, color]) => {
              const parts = Object.values(BODY_DATA).filter((p) => p.system === sys);
              if (parts.length === 0) return null;
              return (
                <div key={sys} className="text-xs">
                  <div className="flex items-center gap-2 mb-1.5">
                    <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                    <div className="text-gray-700 dark:text-gray-200 font-medium">{sys}</div>
                  </div>
                  <div className="grid grid-cols-2 gap-x-2 gap-y-0.5">
                    {parts.map((part) => (
                      <button
                        key={part.id}
                        onClick={() => handleSelect(part.id)}
                        className="text-left text-gray-600 dark:text-gray-300 hover:text-neural-600 dark:hover:text-neural-400 hover:bg-neural-50 dark:hover:bg-neural-900/30 px-2 py-0.5 rounded transition-colors truncate text-xs"
                        title={part.name}
                      >
                        {part.name}
                      </button>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected region info */}
        {selectedInfo ? (
          <div className="flex-1 p-5 space-y-4 overflow-y-auto">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2 font-semibold">Hệ thống</p>
              <NeuralBadge
                style={{ backgroundColor: `${SYSTEM_COLORS[selectedInfo.system] ?? '#6b7280'}20`, color: SYSTEM_COLORS[selectedInfo.system] ?? '#6b7280', borderColor: `${SYSTEM_COLORS[selectedInfo.system] ?? '#6b7280'}30` } as React.CSSProperties}
                className="text-white"
              >
                {selectedInfo.system}
              </NeuralBadge>
            </div>

            <div>
              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">Chức năng</p>
              <ul className="space-y-1.5">
                {selectedInfo.functions.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <span className="text-emerald-500 mt-0.5 flex-shrink-0">✓</span>
                    {f}
                  </li>
                ))}
              </ul>
            </div>

            {docs.length > 0 && (
              <div className="border-t border-gray-100 dark:border-gray-800 pt-4">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-3 leading-relaxed">
                  Tìm thông tin về{' '}
                  <strong className="text-gray-700 dark:text-gray-300">{selectedInfo.name}</strong>{' '}
                  trong {docs.length} tài liệu đã upload.
                </p>
                <button
                  onClick={() =>
                    handleSearch(
                      `Thông tin về ${selectedInfo.name} trong y học: chức năng, bệnh lý và điều trị`
                    )
                  }
                  className="w-full btn-neural py-2.5 text-sm"
                >
                  🔍 Tìm trong tài liệu
                </button>
              </div>
            )}
          </div>
        ) : (
          <EmptyPanel />
        )}
      </div>

      {/* RAG Drawer */}
      <RagDrawer
        open={drawerOpen}
        query={ragQuery}
        answer={ragAnswer}
        loading={ragLoading}
        onClose={() => setDrawerOpen(false)}
      />

      {/* Symptom Form Modal */}
      {symptomFormOpen && symptomTarget && (
        <SymptomForm
          regionId={symptomTarget.id}
          regionName={symptomTarget.name}
          suggestedConditions={symptomTarget.conditions}
          userId={getUserId()}
          onClose={() => setSymptomFormOpen(false)}
          onSaved={handleSymptomSaved}
        />
      )}
    </div>
  );
}