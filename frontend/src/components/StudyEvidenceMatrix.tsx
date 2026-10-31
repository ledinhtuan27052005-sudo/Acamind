'use client';

import { useEffect, useRef, useState } from 'react';
import { getStudyProfile, searchStudyGap, type StudyGapSearch, type StudyProfile } from '@/lib/api';
import { RankingExplanationPanel } from './RankingExplanationPanel';
import { StudyReviewEditor } from './StudyReviewEditor';

const CRITERIA = [
  ['objective', 'Mục tiêu'], ['method', 'Phương pháp'], ['sample', 'Mẫu / quần thể'],
  ['data', 'Dữ liệu'], ['measure', 'Thang đo / chỉ số'], ['finding', 'Kết quả'],
  ['limitation', 'Hạn chế'], ['timepoint', 'Thời điểm'], ['comparator', 'Can thiệp / đối chứng'],
  ['direction', 'Chiều điểm số'],
] as const;

export function StudyEvidenceMatrix({ documents, onOpenSource }: {
  documents: { id: string; title: string }[];
  onOpenSource: (id: string, page: number, quote: string) => void;
}) {
  const [profiles, setProfiles] = useState<Record<string, StudyProfile>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [started, setStarted] = useState(false);
  const [selected, setSelected] = useState<string[]>(CRITERIA.map(([key]) => key));
  const [onlyMissing, setOnlyMissing] = useState(false);
  const [focus, setFocus] = useState('');
  const [gaps, setGaps] = useState<Record<string, StudyGapSearch>>({});
  const [gapErrors, setGapErrors] = useState<Record<string, string>>({});
  const [searching, setSearching] = useState<string | null>(null);
  const gapActive = useRef<AbortController | null>(null);
  useEffect(() => () => { gapActive.current?.abort(); }, []);
  const search = async (id: string, criterion: string) => {
    if (gapActive.current) return;
    const controller = new AbortController();
    gapActive.current = controller;
    const key = `${id}:${criterion}`;
    setSearching(key);
    setGapErrors(prev => ({ ...prev, [key]: '' }));
    setGaps(prev => { const next = { ...prev }; delete next[key]; return next; });
    try {
      const result = await searchStudyGap(id, criterion, focus, controller.signal);
      if (result.document_id !== id || result.criterion !== criterion) throw new Error('Unexpected source');
      if (!controller.signal.aborted) setGaps(prev => ({ ...prev, [key]: result }));
    } catch {
      if (!controller.signal.aborted) setGapErrors(prev => ({ ...prev, [key]: 'Tìm bổ sung thất bại. Có thể thử lại; chưa thể kết luận thiếu dữ liệu.' }));
    } finally {
      if (gapActive.current === controller) { gapActive.current = null; setSearching(null); }
    }
  };
  const active = useRef<AbortController | null>(null);
  useEffect(() => () => { active.current?.abort(); }, []);

  const load = async (refresh = false) => {
    active.current?.abort();
    const controller = new AbortController();
    active.current = controller;
    setStarted(true); setLoading(true); setErrors({});
    if (refresh) { setProfiles({}); setGaps({}); setGapErrors({}); }
    const pending = documents.filter(d => refresh || !profiles[d.id]);
    let cursor = 0;
    // Two simultaneous requests bound DB work for ten selected studies.
    const worker = async () => {
      while (!controller.signal.aborted && cursor < pending.length) {
        const doc = pending[cursor++];
        try {
          const profile = await getStudyProfile(doc.id, controller.signal);
          if (profile.document_id !== doc.id) throw new Error('Unexpected source');
          if (!controller.signal.aborted) setProfiles(prev => ({ ...prev, [doc.id]: profile }));
        } catch {
          if (!controller.signal.aborted) setErrors(prev => ({ ...prev, [doc.id]: 'Không tải được hồ sơ; chưa thể kết luận thiếu bằng chứng.' }));
        }
      }
    };
    await Promise.all([worker(), worker()]);
    if (active.current === controller && !controller.signal.aborted) setLoading(false);
  };
  const rows = CRITERIA.filter(([key]) => selected.includes(key) && (!onlyMissing || documents.some(d =>
    profiles[d.id]?.fields[key]?.status === 'not_found')));
  const completed = documents.filter(d => profiles[d.id] || errors[d.id]).length;

  return <section className="rounded-xl border border-slate-300 dark:border-slate-700 p-4 space-y-3">
    <h3 className="font-semibold">Ma trận đối chiếu theo tiêu chí</h3>
    <p className="text-sm text-gray-500">Mỗi cột là một bài; mỗi ô chứa các đoạn nguồn ứng viên chưa xác minh. Thiếu đoạn trích không có nghĩa bài gốc không đề cập.</p>
    <div className="flex flex-wrap gap-3 items-center">
      <button type="button" disabled={loading || !!searching || documents.length < 2} onClick={() => void load(started && !Object.keys(errors).length)}
        className="rounded bg-blue-600 text-white px-3 py-2 disabled:opacity-50">
        {loading ? `Đang tải ${completed}/${documents.length} bài…` : !started ? 'Tạo ma trận đối chiếu' : Object.keys(errors).length ? 'Thử lại các bài bị lỗi' : 'Làm mới ma trận'}
      </button>
      {loading && <button type="button" className="underline" onClick={() => { active.current?.abort(); setLoading(false); }}>Hủy tải</button>}
      <label className="text-sm"><input type="checkbox" checked={onlyMissing} onChange={e => setOnlyMissing(e.target.checked)} /> Chỉ hiện tiêu chí có ô chưa tìm thấy</label>
    </div>
    <fieldset className="flex flex-wrap gap-3 text-sm">
      <legend className="mb-1">Tiêu chí hiển thị</legend>
      {CRITERIA.map(([key, label]) => <label key={key}><input type="checkbox" checked={selected.includes(key)}
        onChange={e => setSelected(prev => e.target.checked ? [...prev, key] : prev.filter(v => v !== key))} /> {label}</label>)}
    </fieldset>
    <label className="block text-sm">Chủ đề để tìm bổ sung (tùy chọn)
      <input value={focus} maxLength={1000} disabled={!!searching} className="block border rounded p-2 w-full dark:bg-slate-900"
        onChange={e => { setFocus(e.target.value); setGaps({}); setGapErrors({}); }} />
    </label>
    {searching && <button type="button" className="underline text-sm" onClick={() => {
      gapActive.current?.abort(); gapActive.current = null; setSearching(null);
    }}>Hủy chờ tìm bổ sung</button>}
    {started && <div className="overflow-x-auto" aria-busy={loading}>
      <table className="w-full text-sm border-collapse">
        <caption className="sr-only">Các đoạn nguồn của từng nghiên cứu theo tiêu chí được chọn</caption>
        <thead><tr><th scope="col" className="p-3 text-left sticky left-0 bg-white dark:bg-slate-900">Tiêu chí</th>
          {documents.map(doc => <th scope="col" key={doc.id} className="p-3 text-left min-w-[260px] max-w-sm">
            {doc.title}
            {errors[doc.id] && <p role="alert" className="font-normal text-red-600">{errors[doc.id]}</p>}
            {!profiles[doc.id] && !errors[doc.id] && <p className="font-normal">{loading ? 'Đang chờ hồ sơ…' : 'Chưa tải hồ sơ'}</p>}
            {profiles[doc.id] && <p className="font-normal text-gray-500">Đã quét {profiles[doc.id].coverage.chunks_scanned} đoạn{profiles[doc.id].coverage.truncated ? ' · Chưa quét hết' : ''}</p>}
          </th>)}
        </tr></thead>
        <tbody>{rows.map(([key, label]) => <tr key={key} className="border-t align-top">
          <th scope="row" className="p-3 text-left sticky left-0 bg-white dark:bg-slate-900">{label}</th>
          {documents.map(doc => {
            const field = profiles[doc.id]?.fields[key];
            return <td key={doc.id} className="p-3 min-w-[260px] max-w-sm">
              {!field ? <span className="text-gray-500">{errors[doc.id] ? 'Lỗi tải dữ liệu' : 'Chưa có dữ liệu để hiển thị'}</span>
                : field.status === 'not_found' ? <span className="text-amber-700 dark:text-amber-300">Chưa tìm thấy trong các đoạn đã quét</span>
                : <details><summary className="cursor-pointer font-medium">Xem {field.candidates.length} đoạn ứng viên · Chưa xác minh</summary>
                  {field.candidates.map((c, index) => <div key={`${c.chunk_id}-${c.start}-${index}`} className="mt-3 space-y-1 border-l-2 pl-2">
                    <p className="text-xs text-gray-500">{c.origin === 'current_study_candidate' ? 'Có dấu hiệu thuộc bài hiện tại' : c.origin === 'cited_study_candidate' ? 'Có dấu hiệu dẫn nghiên cứu khác' : 'Chưa rõ chủ thể'}</p>
                    <blockquote className="whitespace-pre-wrap break-words">{c.quote}</blockquote>
                    <button type="button" className="text-blue-600 underline" onClick={() => onOpenSource(doc.id, c.page, c.quote)}>Mở PDF và đối chiếu — trang {c.page}</button>
                  </div>)}
                  {field.candidate_count > field.candidates.length && <p className="mt-2 text-gray-500">Đang hiển thị {field.candidates.length}/{field.candidate_count} ứng viên.</p>}
                </details>}
              {field?.status === 'not_found' && <div className="mt-2 space-y-2">
                <button type="button" disabled={loading || !!searching} className="text-blue-600 underline disabled:opacity-50"
                  onClick={() => void search(doc.id, key)}>{searching === `${doc.id}:${key}` ? 'Đang tìm…' : 'Tìm bổ sung trong bài này'}</button>
                {gapErrors[`${doc.id}:${key}`] && <p role="alert" className="text-red-600">{gapErrors[`${doc.id}:${key}`]}</p>}
                {gaps[`${doc.id}:${key}`] && <div>
                  <p className="text-xs text-gray-500">Truy vấn: {gaps[`${doc.id}:${key}`].query}</p>
                  <p>{gaps[`${doc.id}:${key}`].candidates.length ? 'Đoạn gợi ý liên quan; cần đối chiếu trước khi điền ô.' : 'Chưa truy xuất được đoạn phù hợp; không chứng minh bài không đề cập.'}</p>
                  {gaps[`${doc.id}:${key}`].candidates.map(c => <details key={c.chunk_id} className="mt-2">
                    <summary className="cursor-pointer">Đoạn nguồn — trang {c.page}</summary>
                    {c.ranking && <RankingExplanationPanel ranking={c.ranking} />}
                    <blockquote className="whitespace-pre-wrap break-words max-h-80 overflow-auto">{c.quote}</blockquote>
                    <button type="button" className="underline text-blue-600" onClick={() => onOpenSource(doc.id, c.page, c.quote)}>Mở PDF đối chiếu</button>
                  </details>)}
                </div>}
              </div>}
              {field && <StudyReviewEditor documentId={doc.id} criterion={key}
                candidates={[...field.candidates, ...(gaps[`${doc.id}:${key}`]?.candidates ?? [])]}
                onOpenSource={onOpenSource} />}
            </td>;
          })}
        </tr>)}</tbody>
      </table>
      {!rows.length && <p className="p-3">Không có tiêu chí phù hợp với bộ lọc hiện tại.</p>}
    </div>}
  </section>;
}
