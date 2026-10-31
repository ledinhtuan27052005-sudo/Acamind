'use client';

import dynamic from 'next/dynamic';
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BODY_DATA, ORGAN_DATA, SYSTEM_COLORS } from '@/lib/bodyData';
import { getDocuments, DocumentInfo, chatStream, fetchNeuroClinicalGraph, NeuroClinicalGraphData, NeuroBrainRegionCard } from '@/lib/api';
import RegionPanel from '@/components/body/RegionPanel';
import SymptomForm from '@/components/body/SymptomForm';
import { NeuralCard } from '@/components/ui/NeuralCard';
import { NeuralBadge } from '@/components/ui/NeuralBadge';
import { AcademicDocumentRenderer, cleanMarkdownText } from '@/components/ui/AcademicDocumentRenderer';
import { useI18n } from '@/lib/i18n/context';

const NEURO_BRAIN_IDS = [
  'prefrontal_cortex',
  'amygdala',
  'hippocampus',
  'anterior_cingulate',
  'hypothalamus_hpa',
  'striatum_nucleus',
];

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
  const { t } = useI18n();
  return (
    <div className="w-full h-full flex items-center justify-center bg-gray-900">
      <div className="text-center">
        <div className="text-5xl mb-4 animate-pulse">🫀</div>
        <p className="text-sm text-gray-400">{t.atlas.loading_model}</p>
      </div>
    </div>
  );
}

function EmptyPanel() {
  const { t } = useI18n();
  return (
    <div className="h-full flex flex-col items-center justify-center text-center px-6 space-y-4">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-neural-100 to-cortex-100 dark:from-neural-900/50 dark:to-cortex-900/50 flex items-center justify-center">
        <span className="text-4xl">🧠</span>
      </div>
      <div>
        <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
          {t.atlas.title}
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
          {t.atlas.subtitle}
        </p>
      </div>
      <div className="text-xs text-gray-400 dark:text-gray-500 space-y-1.5">
        <p>{t.atlas.drag_rotate}</p>
        <p>{t.atlas.scroll_zoom}</p>
        <p>{t.atlas.click_part}</p>
      </div>
    </div>
  );
}

function RagDrawer({
  open, query, answer, loading, onClose,
}: {
  open: boolean; query: string; answer: string; loading: boolean; onClose: () => void;
}) {
  const { t } = useI18n();
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
              <h3 className="font-semibold text-gray-900 dark:text-white">{t.atlas.search_results}</h3>
              <button
                onClick={onClose}
                className="w-8 h-8 flex items-center justify-center rounded-xl text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1 font-medium">{t.atlas.question}</p>
                <p className="text-sm text-gray-700 dark:text-gray-300 italic">{query}</p>
              </div>
              {loading ? (
                <div className="flex items-center gap-2 text-gray-400">
                  <span className="w-2 h-2 rounded-full bg-neural-500 animate-bounce" />
                  <span className="w-2 h-2 rounded-full bg-neural-500 animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <span className="w-2 h-2 rounded-full bg-neural-500 animate-bounce" style={{ animationDelay: '0.2s' }} />
                  <span className="text-sm ml-2">{t.atlas.thinking}</span>
                </div>
              ) : (
                <AcademicDocumentRenderer content={answer || t.atlas.no_info} />
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default function BodyPage() {
  const { t, locale } = useI18n();

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

  // Neuro-Clinical 3D Graph state
  const [neuroGraph, setNeuroGraph] = useState<NeuroClinicalGraphData | null>(null);
  const [neuroLoading, setNeuroLoading] = useState(false);

  const getUserType = (): 'patient' | 'student' | 'expert' => {
    if (typeof window === 'undefined') return 'patient';
    return (sessionStorage.getItem('user_type') ?? 'patient') as 'patient' | 'student' | 'expert';
  };

  useEffect(() => {
    getDocuments()
      .then((d) => setDocs(d.filter((doc) => doc.status === 'ready')))
      .catch(console.error);

    // Load default Neuro-Clinical 3D Knowledge Graph catalog
    setNeuroLoading(true);
    fetchNeuroClinicalGraph('Trầm cảm, lo âu, PTSD, mất ngủ, stress, động lực')
      .then((res) => setNeuroGraph(res))
      .catch(console.error)
      .finally(() => setNeuroLoading(false));

    // Check deep-link from URL query or localStorage (from Chat / Literature / Health)
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const qRegion = params.get('region');
      const qXray = params.get('xray');
      const storedTarget = localStorage.getItem('acamind_3d_target');

      if (qRegion) {
        if (qXray === '1' || NEURO_BRAIN_IDS.includes(qRegion) || ORGAN_DATA[qRegion]) {
          setXray(true);
        }
        handleSelect(qRegion);
      } else if (storedTarget) {
        try {
          const parsed = JSON.parse(storedTarget);
          localStorage.removeItem('acamind_3d_target');
          if (parsed.region_id) {
            setXray(true);
            handleSelect(parsed.region_id);
          }
          if (parsed.context_text) {
            fetchNeuroClinicalGraph(parsed.context_text)
              .then((res) => setNeuroGraph(res))
              .catch(console.error);
          }
        } catch {
          // ignore
        }
      }
    }
  }, []);

  const handleSelect = (id: string) => {
    setSelected(id);
    if (NEURO_BRAIN_IDS.includes(id) || ORGAN_DATA[id]) {
      setXray(true);
    }
    const bodyInfo = BODY_DATA[id];
    const organInfo = ORGAN_DATA[id];
    if (bodyInfo) {
      setSelectedRegion({
        id: bodyInfo.id,
        name_vi: bodyInfo.name,
        name_latin: '',
        symptoms: bodyInfo.commonConditions,
        description_basic: bodyInfo.description,
        description_advanced: `${bodyInfo.description}\n\nFunctions: ${bodyInfo.functions.join('; ')}`,
      });
    } else if (organInfo) {
      setSelectedRegion({
        id: organInfo.id,
        name_vi: organInfo.name,
        name_latin: organInfo.system,
        symptoms: organInfo.commonConditions,
        description_basic: organInfo.description,
        description_advanced: `${organInfo.description}\n\nFunctions: ${organInfo.functions.join('; ')}`,
      });
    } else {
      setSelectedRegion(null);
    }
  };

  useEffect(() => {
    if (selected) {
      handleSelect(selected);
    }
  }, [locale]);

  const handleCloseRegion = () => {
    setSelected(null);
    setSelectedRegion(null);
  };

  const handleSearch = async (query: string) => {
    if (docs.length === 0) {
      alert(t.atlas.no_docs_ready);
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
      setRagAnswer(t.atlas.search_error + (e as Error).message);
    } finally {
      setRagLoading(false);
    }
  };

  const handleReportSymptom = (id: string, name: string) => {
    const info = BODY_DATA[id] ?? ORGAN_DATA[id];
    setSymptomTarget({ 
      id, 
      name, 
      conditions: (info?.commonConditions ?? []) 
    });
    setSymptomFormOpen(true);
  };

  const handleSymptomSaved = () => {
    setSavedCount((c) => c + 1);
    setSavedNotif(true);
    setTimeout(() => setSavedNotif(false), 3000);
  };

  const getUserId = () => {
    if (typeof window === 'undefined') return undefined;
    return sessionStorage.getItem('user_id') ?? undefined;
  };

  const selectedInfo = selected ? (BODY_DATA[selected] ?? ORGAN_DATA[selected] ?? null) : null;
  const activeNeuroNode: NeuroBrainRegionCard | null =
    selected && neuroGraph?.brain_regions
      ? neuroGraph.brain_regions.find((r) => r.region_3d_id === selected) ?? null
      : null;

  return (
    <div className="flex h-full relative overflow-hidden">
      {/* 3D Viewer */}
      <div className="flex-1 relative">
        <BodyViewer3D selected={selected} onSelect={handleSelect} xray={xray} />

        {/* Top bar */}
        <div className="absolute top-3 left-1/2 -translate-x-1/2 flex items-center gap-2 pointer-events-none z-10">
          <div className="bg-gray-900/80 backdrop-blur text-gray-300 text-xs px-4 py-2 rounded-full border border-white/10">
            {selected
              ? `✦ ${((BODY_DATA[selected] ?? ORGAN_DATA[selected])?.name)}`
              : xray
              ? t.atlas.xray_on_hint
              : t.atlas.xray_off_hint}
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
            {xray ? t.atlas.xray_btn_on : t.atlas.xray_btn_off}
          </button>
        </div>

        {/* Floating Neuro-Clinical 3D Quick Bar on Top-Left */}
        <div className="absolute top-14 left-3 z-10 w-64 bg-gray-950/85 backdrop-blur-md border border-indigo-500/30 rounded-2xl p-3 text-white shadow-xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-300">
              🧠 Bản đồ Thần kinh – Tâm lý 3D
            </span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              X-Ray Bridge
            </span>
          </div>
          <p className="text-[11px] text-gray-400 mb-2 leading-snug">
            Chọn vùng não chuyên biệt để bật X-Ray 3D &amp; xem Đồ thị Nhân quả 4 Tầng:
          </p>
          <div className="grid grid-cols-1 gap-1 max-h-52 overflow-y-auto pr-1">
            {NEURO_BRAIN_IDS.map((nid) => {
              const organ = ORGAN_DATA[nid];
              if (!organ) return null;
              const isSel = selected === nid;
              return (
                <button
                  key={nid}
                  onClick={() => {
                    setXray(true);
                    handleSelect(nid);
                  }}
                  className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-left text-xs transition-all ${
                    isSel
                      ? 'bg-indigo-600/90 text-white font-semibold shadow-sm'
                      : 'bg-gray-900/70 text-gray-300 hover:bg-gray-800/90'
                  }`}
                >
                  <span
                    className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: organ.color, boxShadow: isSel ? `0 0 8px ${organ.color}` : undefined }}
                  />
                  <span className="truncate">{organ.name}</span>
                </button>
              );
            })}
          </div>
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
              {t.atlas.symptom_saved.replace('{count}', savedCount.toString())}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Sidebar */}
      <div className="w-80 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-800 flex flex-col">
        {/* Systems list */}
        <div className="p-4 border-b border-gray-100 dark:border-gray-800">
          <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3 font-semibold">{t.atlas.systems}</p>
          <div className="space-y-3 max-h-56 overflow-auto pr-1">
            {Object.entries(SYSTEM_COLORS).map(([sys, color]) => {
              const parts = Object.values(BODY_DATA).filter((p) => p.system === sys);
              if (parts.length === 0) return null;
              const sysName = sys;
              return (
                <div key={sys} className="text-xs">
                  <div className="flex items-center gap-2 mb-1.5">
                    <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                    <div className="text-gray-700 dark:text-gray-200 font-medium">{sysName}</div>
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
          <div className="flex-1 p-4 space-y-4 overflow-y-auto">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1.5 font-semibold">{t.atlas.system}</p>
              <NeuralBadge
                style={{ backgroundColor: `${SYSTEM_COLORS[selectedInfo.system] ?? '#6b7280'}20`, color: SYSTEM_COLORS[selectedInfo.system] ?? '#6b7280', borderColor: `${SYSTEM_COLORS[selectedInfo.system] ?? '#6b7280'}30` } as React.CSSProperties}
                className="text-white"
              >
                {selectedInfo.system}
              </NeuralBadge>
            </div>

            {/* 4-Layer Causal Neuro-Clinical Graph Panel when a Neuro Region is selected */}
            {activeNeuroNode && (
              <div className="rounded-xl border border-indigo-200 dark:border-indigo-800/60 bg-indigo-50/60 dark:bg-indigo-950/30 p-3.5 space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-bold text-indigo-800 dark:text-indigo-300">
                    🧬 Đồ thị Nhân quả 4 Tầng
                  </span>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 truncate">
                    {cleanMarkdownText(activeNeuroNode.name_latin)}
                  </span>
                </div>

                <div>
                  <p className="text-[11px] font-bold text-gray-700 dark:text-gray-300 mb-1">
                    1. Hội chứng Lâm sàng (DSM-5 / ICD-11):
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {(selectedInfo.commonConditions ?? []).map((s, idx) => (
                      <span key={idx} className="text-[11px] px-2 py-0.5 rounded-md bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300">
                        {cleanMarkdownText(s)}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-[11px] font-bold text-gray-700 dark:text-gray-300 mb-1">
                    2. Cơ chế Sinh lý bệnh (Pathology):
                  </p>
                  <div className="text-[11px] font-medium text-rose-700 dark:text-rose-300 bg-rose-50 dark:bg-rose-950/40 border border-rose-200/70 dark:border-rose-800/50 rounded-lg px-2.5 py-1.5 leading-relaxed">
                    ⚡ {cleanMarkdownText(activeNeuroNode.role_in_pathology)}
                  </div>
                </div>

                <div>
                  <p className="text-[11px] font-bold text-gray-700 dark:text-gray-300 mb-1">
                    3. Chất dẫn truyền Thần kinh:
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {activeNeuroNode.neurotransmitters.map((nt, idx) => (
                      <span key={idx} className="text-[11px] px-2 py-0.5 rounded-md bg-purple-100/70 dark:bg-purple-900/40 text-purple-800 dark:text-purple-200">
                        {cleanMarkdownText(nt)}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-[11px] font-bold text-gray-700 dark:text-gray-300 mb-1">
                    4. Can thiệp &amp; Trị liệu Dựa trên Bằng chứng:
                  </p>
                  <div className="text-[11px] text-emerald-800 dark:text-emerald-300 bg-emerald-50/70 dark:bg-emerald-950/40 border border-emerald-200/70 dark:border-emerald-800/50 rounded-lg px-2.5 py-1.5 leading-relaxed">
                    {cleanMarkdownText(activeNeuroNode.therapy_mechanism)}
                  </div>
                  <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-1 italic">
                    📚 {cleanMarkdownText(activeNeuroNode.citation)}
                  </p>
                </div>
              </div>
            )}

            <div>
              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">{t.atlas.functions}</p>
              <ul className="space-y-1.5">
                {(selectedInfo.functions).map((f, i) => (
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
                  {t.atlas.find_info.replace('{name}', selectedInfo.name)}
                </p>
                <button
                  onClick={() =>
                    handleSearch(
                      `Phân tích cơ chế sinh học thần kinh, giải phẫu chức năng, bệnh lý học và phác đồ điều trị liên quan đến ${selectedInfo.name}`
                    )
                  }
                  className="w-full btn-neural py-2.5 text-sm"
                >
                  {t.atlas.search_in_docs}
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
