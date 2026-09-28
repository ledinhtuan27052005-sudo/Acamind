'use client';

import { X } from 'lucide-react';
import { useI18n } from '@/lib/i18n/context';

interface BodyRegion {
 id: string; name_vi: string; name_latin: string;
 symptoms: string[]; description_basic: string; description_advanced: string;
}

interface Props {
 region: BodyRegion | null;
 userType: 'patient' | 'student' | 'expert';
 onClose: () => void;
 onReportSymptom: (regionId: string, regionName: string) => void;
}

export default function RegionPanel({ region, userType, onClose, onReportSymptom }: Props) {
 const { t } = useI18n();

 if (!region) return null;
 const isAdvanced = userType !== 'patient';

  return (
    <div className="absolute top-4 right-4 w-72 bg-[#0F172A]/60 backdrop-blur-md rounded-2xl shadow-2xl p-4 z-10 border border-white/10">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-[17px] font-bold text-white">{region.name_vi}</h3>
          {isAdvanced && <p className="text-xs font-medium text-slate-300 italic">{region.name_latin}</p>}
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
          <X size={16} />
        </button>
      </div>

      <p className="text-[13px] text-slate-100 mb-4 leading-relaxed font-medium">
        {isAdvanced ? region.description_advanced : region.description_basic}
      </p>

      <div className="mb-4">
        <p className="text-[11px] font-bold text-slate-300 uppercase mb-2 tracking-wider">{t.atlas.common_symptoms}</p>
        <div className="flex flex-wrap gap-1.5">
          {region.symptoms.map((s) => (
            <span key={s} className="px-2.5 py-1 bg-[#FFF9F0] text-red-600 text-xs font-bold rounded-full shadow-sm">
              {s}
            </span>
          ))}
        </div>
      </div>

      <button
        onClick={() => onReportSymptom(region.id, region.name_vi)}
        className="w-full bg-blue-500/80 text-white rounded-xl py-2 text-[13px] font-bold hover:bg-blue-500 transition-colors shadow-md backdrop-blur-sm"
      >
        {t.atlas.report_symptom}
      </button>
    </div>
  );
}
