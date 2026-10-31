'use client';
import { useState } from 'react';
import { getStudyReviews, saveStudyReview, type StudyReview } from '@/lib/api';

type Source = { chunk_id: string; quote: string; page: number };
export function StudyReviewEditor({ documentId, criterion, candidates, onOpenSource }: {
  documentId: string; criterion: string; candidates: Source[];
  onOpenSource: (id: string, page: number, quote: string) => void;
}) {
  const [opened, setOpened] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState<StudyReview[]>([]);
  const [before, setBefore] = useState<number | null>(null);
  const [value, setValue] = useState('');
  const [note, setNote] = useState('');
  const [source, setSource] = useState<Source | null>(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [conflict, setConflict] = useState(false);
  const latest = history[0];
  const sources = [source, ...candidates].filter((s): s is Source => !!s)
    .filter((s, i, all) => all.findIndex(v => v.chunk_id === s.chunk_id && v.quote === s.quote) === i);
  const load = async (older = false) => {
    setBusy(true); setError(''); setMessage('');
    try {
      const result = await getStudyReviews(documentId, criterion, older ? before ?? undefined : undefined);
      if (older) setHistory(prev => [...prev, ...result.items]);
      else {
        setHistory(result.items);
        const current = result.items[0];
        setValue(current?.value ?? candidates[0]?.quote.slice(0, 4000) ?? ''); setNote(current?.note ?? '');
        setSource(current ?? candidates[0] ?? null);
        setLoaded(true); setConflict(false);
      }
      setBefore(result.next_before);
    } catch { setError('Không tải được lịch sử. Hãy thử lại.'); }
    finally { setBusy(false); }
  };
  const save = async (status: 'draft' | 'confirmed') => {
    if (!source) return;
    setBusy(true); setError(''); setMessage('');
    try {
      const result = await saveStudyReview(documentId, criterion, {
        expected_revision: latest?.revision ?? 0, status, value, note,
        chunk_id: source.chunk_id, quote: source.quote,
      });
      setHistory(prev => [result, ...prev]);
      setValue(result.value); setNote(result.note); setSource(result);
      setMessage(status === 'confirmed' ? 'Đã lưu xác nhận của bạn.' : 'Đã lưu bản nháp.');
    } catch (err: unknown) {
      const response = (err as { response?: { status?: number; data?: { detail?: string } } }).response;
      if (response?.status === 409) setConflict(true);
      setError(typeof response?.data?.detail === 'string' ? response.data.detail : 'Chưa lưu được. Nội dung đang sửa vẫn được giữ lại.');
    } finally { setBusy(false); }
  };
  return <div className="mt-3 border-t pt-2 text-sm">
    <button type="button" className="text-blue-600 underline" disabled={busy} onClick={() => {
      setOpened(!opened); if (!opened && !loaded) void load();
    }}>Chỉnh sửa / xác nhận cá nhân{latest ? ` · v${latest.revision}` : ''}</button>
    {opened && <div className="mt-2 space-y-2">
      <p className="text-xs text-gray-500">Lưu riêng cho tài khoản của bạn. Bản thẩm định không tự thay thế hồ sơ máy trích xuất hoặc đầu vào so sánh liên bài.</p>
      {busy && <p role="status">Đang xử lý…</p>}
      {error && <p role="alert" className="text-red-600">{error}</p>}
      {message && <p role="status" className="text-green-700">{message}</p>}
      <button type="button" disabled={busy} className="underline" onClick={() => void load()}>Tải lại bản đã lưu (thay nội dung đang sửa)</button>
      {loaded && <>
        <p>Bản lưu hiện tại: {latest ? `v${latest.revision} · ${latest.status === 'confirmed' ? 'Bạn đã xác nhận' : 'Bản nháp'}` : 'Chưa có'}</p>
        <label className="block">Đoạn nguồn
          <select className="block w-full border rounded p-1 dark:bg-slate-900" disabled={busy}
            value={source ? sources.findIndex(s => s.chunk_id === source.chunk_id && s.quote === source.quote) : -1}
            onChange={e => setSource(sources[Number(e.target.value)] ?? null)}>
            <option value={-1}>Chọn đoạn nguồn</option>
            {sources.map((s, i) => <option key={i} value={i}>Trang {s.page} · {s.quote.slice(0, 65)}…</option>)}
          </select>
        </label>
        {source ? <div><blockquote className="max-h-48 overflow-auto whitespace-pre-wrap break-words">{source.quote}</blockquote>
          <button type="button" className="underline text-blue-600" onClick={() => onOpenSource(documentId, source.page, source.quote)}>Đối chiếu PDF — trang {source.page}</button></div>
          : <p>Chưa có nguồn. Hãy tìm bổ sung trước khi lưu.</p>}
        <label className="block">Nội dung trích xuất đã chỉnh sửa
          <textarea value={value} maxLength={4000} disabled={busy} onChange={e => setValue(e.target.value)} className="block w-full border rounded p-2 dark:bg-slate-900" rows={4} />
        </label>
        <label className="block">Ghi chú / lý do sửa
          <textarea value={note} maxLength={1000} disabled={busy} onChange={e => setNote(e.target.value)} className="block w-full border rounded p-2 dark:bg-slate-900" rows={2} />
        </label>
        <div className="flex flex-wrap gap-2">
          <button type="button" disabled={busy || conflict || !source || !value.trim()} onClick={() => void save('draft')} className="border rounded px-2 py-1 disabled:opacity-50">Lưu nháp / bỏ xác nhận</button>
          <button type="button" disabled={busy || conflict || !source || !value.trim()} onClick={() => void save('confirmed')} className="bg-blue-600 text-white rounded px-2 py-1 disabled:opacity-50">Lưu và xác nhận đã đối chiếu</button>
        </div>
        <details><summary className="cursor-pointer">Lịch sử thay đổi</summary>
          {history.map(r => <div key={r.revision} className="border-t py-2 space-y-1">
            <p>v{r.revision} · {r.status === 'confirmed' ? 'Đã xác nhận' : 'Bản nháp'} · {r.reviewer_name} · {new Date(r.created_at).toLocaleString('vi-VN')}</p>
            <p className="whitespace-pre-wrap break-words">{r.value}</p>
            {r.note && <p className="whitespace-pre-wrap break-words">Ghi chú: {r.note}</p>}
            <details><summary>Nguồn đã lưu — trang {r.page}</summary><blockquote className="whitespace-pre-wrap break-words max-h-48 overflow-auto">{r.quote}</blockquote></details>
          </div>)}
          {before !== null && <button type="button" disabled={busy} className="underline" onClick={() => void load(true)}>Xem lịch sử cũ hơn</button>}
        </details>
      </>}
    </div>}
  </div>;
}
