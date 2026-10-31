'use client';

import { useState } from 'react';
import { getStudyProfile, type StudyProfile } from '@/lib/api';

export function StudyProfilePanel({ documentId, onOpenSource }: {
  documentId: string;
  onOpenSource: (quote: string, page: number) => void;
}) {
  const [profile, setProfile] = useState<StudyProfile | null>(null);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const load = async () => {
    setLoading(true);
    setError('');
    try { setProfile(await getStudyProfile(documentId)); }
    catch { setError('Không tải được hồ sơ. Hãy thử lại hoặc kiểm tra quyền truy cập tài liệu.'); }
    finally { setLoading(false); }
  };
  return <div className="mt-2 text-xs">
    <button type="button" aria-expanded={open} className="text-blue-600 underline"
      onClick={() => { setOpen(!open); if (!open && !profile && !loading) void load(); }}>
      {open ? 'Ẩn hồ sơ nghiên cứu' : 'Xem hồ sơ nghiên cứu'}
    </button>
    {open && <div className="mt-2 space-y-3 rounded border p-3">
      {loading && <p role="status">Đang trích xuất hồ sơ…</p>}
      {error && <p role="alert">{error} <button type="button" onClick={() => void load()} className="underline">Thử lại</button></p>}
      {profile && <>
        <p>{profile.message}</p>
        <p>Đã quét {profile.coverage.chunks_scanned} đoạn. {profile.coverage.truncated && 'Đã chạm giới hạn xử lý; hồ sơ chưa bao phủ hết dữ liệu.'}</p>
        {Object.entries(profile.fields).map(([key, field]) => <section key={key}>
          <h4 className="font-semibold">{field.label}</h4>
          {field.status === 'not_found' && <p className="text-gray-500">Chưa tìm thấy trong dữ liệu đã quét.</p>}
          {field.candidates.map((candidate, index) => <div key={`${candidate.chunk_id}-${candidate.start}-${index}`} className="mt-2 border-l-2 pl-2">
            <p className="text-gray-500">{candidate.origin === 'current_study_candidate' ? 'Có dấu hiệu thuộc bài hiện tại' : candidate.origin === 'cited_study_candidate' ? 'Có dấu hiệu dẫn nghiên cứu khác' : 'Chưa rõ chủ thể'} · Chưa xác minh</p>
            <blockquote className="whitespace-pre-wrap">{candidate.quote}</blockquote>
            <button type="button" className="text-blue-600 underline" onClick={() => onOpenSource(candidate.quote, candidate.page)}>Mở nguồn — trang {candidate.page}</button>
          </div>)}
          {field.candidate_count > field.candidates.length && <p className="text-gray-500">Hiển thị {field.candidates.length}/{field.candidate_count} đoạn ứng viên.</p>}
        </section>)}
        <button type="button" disabled={loading} className="underline" onClick={() => void load()}>Tạo lại hồ sơ từ dữ liệu hiện tại</button>
      </>}
    </div>}
  </div>;
}
