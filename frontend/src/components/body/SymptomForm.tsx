'use client';

import { useState } from 'react';
import { reportSymptom } from '@/lib/api';
import { useI18n } from '@/lib/i18n/context';

interface Props {
  regionId: string;
  regionName: string;
  suggestedConditions: string[];
  userId?: string;
  onClose: () => void;
  onSaved: () => void;
}

function PainColor(level: number): string {
  if (level <= 3) return '#16a34a';
  if (level <= 5) return '#ca8a04';
  if (level <= 7) return '#ea580c';
  return '#dc2626';
}

export default function SymptomForm({
  regionId,
  regionName,
  suggestedConditions,
  userId,
  onClose,
  onSaved,
}: Props) {
  const { t } = useI18n();
  const [description, setDescription] = useState('');
  const [painLevel, setPainLevel] = useState(5);
  const [duration, setDuration] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleChipClick = (condition: string) => {
    setDescription((prev) =>
      prev ? `${prev}, ${condition.toLowerCase()}` : condition
    );
  };

  const handleSubmit = async () => {
    if (!description.trim()) {
      setError(t.atlas.desc_error);
      return;
    }
    setSaving(true);
    setError('');
    try {
      await reportSymptom({
        user_id: userId,
        region_id: regionId,
        region_name: regionName,
        description,
        pain_level: painLevel,
        duration: duration || null,
      });
      onSaved();
      onClose();
    } catch {
      setError(t.atlas.save_error);
    } finally {
      setSaving(false);
    }
  };

  const currentPainLabel = (t.atlas.pain_labels as any)[painLevel] || painLevel.toString();

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div className="bg-white dark:bg-slate-800/60 rounded-2xl shadow-2xl w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b">
          <div>
            <h3 className="font-bold text-slate-800 dark:text-slate-100">{t.atlas.report_title}</h3>
            <p className="text-xs text-blue-600 dark:text-blue-400 mt-0.5">{t.atlas.region.replace('{name}', regionName)}</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 dark:text-slate-500 dark:hover:text-gray-200 text-xl leading-none"
          >
            ✕
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Symptom suggestions */}
          {suggestedConditions.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">
                {t.atlas.suggested_diseases}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {suggestedConditions.map((c) => (
                  <button
                    key={c}
                    onClick={() => handleChipClick(c)}
                    className="text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-100 dark:border-blue-700 px-2.5 py-1 rounded-full hover:bg-blue-100 dark:hover:bg-blue-800 transition-colors"
                  >
                    + {c}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1">
              {t.atlas.desc_label} <span className="text-red-500">*</span>
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t.atlas.desc_placeholder}
              className="w-full border border-slate-300 dark:border-slate-600 dark:border-gray-600 rounded-xl px-3 py-2 text-sm bg-white dark:bg-slate-800/60 dark:bg-gray-700 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none h-24"
            />
          </div>

          {/* Pain level */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-2">
              {t.atlas.pain_level}{' '}
              <span className="font-bold text-base" style={{ color: PainColor(painLevel) }}>
                {painLevel}/10 — {currentPainLabel}
              </span>
            </label>
            <input
              type="range"
              min={1}
              max={10}
              value={painLevel}
              onChange={(e) => setPainLevel(+e.target.value)}
              className="w-full accent-blue-600"
              style={{ accentColor: PainColor(painLevel) }}
            />
            <div className="flex justify-between text-xs text-slate-400 dark:text-slate-500 mt-1">
              <span>{t.atlas.pain_level_1}</span>
              <span>{t.atlas.pain_level_5}</span>
              <span>{t.atlas.pain_level_10}</span>
            </div>
          </div>

          {/* Time */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1">
              {t.atlas.duration_label}
            </label>
            <input
              type="text"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              placeholder={t.atlas.duration_placeholder}
              className="w-full border border-slate-300 dark:border-slate-600 dark:border-gray-600 rounded-xl px-3 py-2 text-sm bg-white dark:bg-slate-800/60 dark:bg-gray-700 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          {/* Buttons */}
          <div className="flex gap-3 pt-1">
            <button
              onClick={onClose}
              className="flex-1 border border-slate-300 dark:border-slate-600 dark:border-gray-600 rounded-xl py-2 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/60 dark:hover:bg-gray-700 transition-colors"
            >
              {t.atlas.cancel}
            </button>
            <button
              onClick={handleSubmit}
              disabled={saving}
              className="flex-1 bg-blue-600 text-white rounded-xl py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {saving ? t.atlas.saving : t.atlas.save_to_profile}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
