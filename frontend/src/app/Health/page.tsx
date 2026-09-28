'use client';

import { useEffect, useState } from 'react';
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
  }, []);

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
        <div className="max-w-5xl mx-auto px-4 md:px-6 py-6">
          <div className="flex items-center justify-between gap-4">
            {/* Title */}
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-cortex-500 to-neural-500 flex items-center justify-center shadow-lg shadow-cortex-500/25">
                <HeartPulse className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  Health Profile
                </h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Data reported from the 3D Body Model
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
              Health Analysis
            </NeuralButton>
          </div>
        </div>
      </div>

      {/* Helper text */}
      <div className="max-w-5xl mx-auto px-4 md:px-6 py-4">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {loadingSymptoms
            ? '⏳ Loading profile...'
            : symptoms.length === 0
            ? '⚠️ No symptoms yet — go to 3D Body Model to report first.'
            : `✓ Ready to analyze ${symptoms.length} reported symptoms.`}
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
            <p className="text-sm text-gray-500 dark:text-gray-400">Loading profile...</p>
          </div>
        )}

        {/* Empty state */}
        {!loadingSymptoms && !loadError && symptoms.length === 0 && (
          <NeuralCard variant="glass" className="text-center py-16">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-neural-100 to-cortex-100 dark:from-neural-900/50 dark:to-cortex-900/50 flex items-center justify-center mb-6">
              <Brain className="w-8 h-8 text-neural-600 dark:text-neural-400" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
              No data yet
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto mb-6">
              Go to the 3D Body Model, click on body parts and press <strong>"Report Symptoms"</strong> to report.
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

        {/* Symptom list */}
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
                  {/* Delete button */}
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
                      <span>Reported: {new Date(s.reported_at).toLocaleDateString('en-US')}</span>
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
                      {healthError.includes('not reported') && (
                        <a href="/3d" className="text-xs text-neural-600 dark:text-neural-400 underline mt-1 inline-block">
                          → Open 3D Body Model
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
                      AI is analyzing health profile...
                    </p>
                  </div>
                )}

                {/* Result */}
                {healthResult && !healthLoading && (
                  <div className="space-y-4">
                    <div className="rounded-xl p-5 bg-gradient-to-br from-neural-50/50 to-cortex-50/50 dark:from-neural-950/20 dark:to-cortex-950/20 border border-neural-100 dark:border-neural-800">
                      <div className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap leading-relaxed">
                        {healthResult}
                      </div>
                    </div>

                    {/* Sources */}
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

                    {/* Disclaimer */}
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
