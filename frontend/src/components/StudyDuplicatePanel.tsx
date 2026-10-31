'use client';
import { useState } from 'react';
import { checkStudyDuplicates, type StudyDuplicateCheck } from '@/lib/api';

export function StudyDuplicatePanel({ ids, onExclude, onOpen, selectionLocked }: {
  ids: string[]; onExclude: (id: string) => void; onOpen: (id: string) => void; selectionLocked: boolean;
}) {
  const [result, setResult] = useState<StudyDuplicateCheck | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const check = async () => {
    setBusy(true); setError(''); setResult(null);
    try { setResult(await checkStudyDuplicates(ids)); }
    catch { setError('Không kiểm tra được tài liệu trùng. Hãy thử lại.'); }
    finally { setBusy(false); }
  };
  return <section className="rounded-xl border p-4 space-y-3">
    <h3 className="font-semibold">Tài liệu trùng / phiên bản liên quan</h3>
    <p className="text-sm text-gray-500">Kiểm tra trước khi tổng hợp để tránh dùng nhiều bản của một nghiên cứu như các nghiên cứu độc lập. Chọn giữ một bản chỉ thay đổi danh sách đối chiếu hiện tại; bạn có thể chọn lại từ thư viện.</p>
    <button type="button" disabled={busy} onClick={() => void check()} className="rounded bg-blue-600 text-white px-3 py-2 disabled:opacity-50">{busy ? 'Đang kiểm tra…' : 'Kiểm tra các bài đã chọn'}</button>
    {error && <p role="alert" className="text-red-600">{error}</p>}
    {result && <>
      <p className="text-sm">{result.message}</p>
      {!result.pairs.length && <p>Chưa phát hiện cặp nghi trùng theo hash và tiêu đề.</p>}
      {result.pairs.map(pair => <div key={`${pair.document_a}:${pair.document_b}`} className="border rounded p-3 space-y-2">
        <p className="font-medium">{pair.kind === 'identical_file' ? 'Trùng nội dung tệp' : 'Có thể là phiên bản liên quan — chưa xác nhận'}</p>
        <p className="text-sm">{pair.reason}</p>
        {[{ id: pair.document_a, meta: pair.metadata_a, other: pair.document_b },
          { id: pair.document_b, meta: pair.metadata_b, other: pair.document_a }].map(item => <div key={item.id} className="border-t pt-2">
          <p>{item.meta.title}</p>
          <p className="text-xs text-gray-500">{item.meta.authors || 'Chưa có tác giả'} · {item.meta.year ?? 'Chưa có năm'}</p>
          <div className="flex gap-3 text-sm">
            <button type="button" className="underline text-blue-600" onClick={() => onOpen(item.id)}>Mở PDF kiểm tra</button>
            <button type="button" disabled={selectionLocked} className="underline disabled:opacity-50" onClick={() => onExclude(item.other)}>Giữ bản này, bỏ chọn bản còn lại</button>
          </div>
        </div>)}
      </div>)}
    </>}
  </section>;
}
