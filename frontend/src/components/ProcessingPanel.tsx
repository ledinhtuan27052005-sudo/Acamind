'use client';
import { useEffect, useRef, useState } from 'react';
import { controlProcessing, getProcessingStatus, type ProcessingStatus } from '@/lib/api';

export function ProcessingPanel({ documentId, onStatus }: { documentId: string; onStatus?: (status: string) => void }) {
  const [state, setState] = useState<ProcessingStatus | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const callback = useRef(onStatus); callback.current = onStatus;
  useEffect(() => {
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      let again = true;
      try {
        const next = await getProcessingStatus(documentId);
        if (stopped) return;
        setState(next); setError(''); callback.current?.(next.status);
        again = next.status === 'processing' || next.status === 'cancel_requested';
      } catch {
        if (!stopped) setError('Không lấy được tiến độ. Dữ liệu hiển thị có thể đã cũ.');
        again = false;
      }
      if (!stopped && again) timer = setTimeout(() => void poll(), 4000);
    };
    void poll();
    return () => { stopped = true; clearTimeout(timer); };
  }, [documentId, refresh]);
  const act = async (action: 'cancel' | 'retry') => {
    setBusy(true); setError('');
    try {
      const next = await controlProcessing(documentId, action);
      callback.current?.(next.status);
      setState(null);
      setRefresh(n => n + 1);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Không thực hiện được thao tác. Hãy tải lại tiến độ.');
    } finally { setBusy(false); }
  };
  return <div className="mt-2 space-y-1 text-xs">
    <p role="status">{state?.label ?? 'Đang lấy tiến độ…'}</p>
    {state?.status === 'cancel_requested' && <p>Hủy ở mốc kế tiếp; OCR hoặc tạo embedding hiện tại có thể cần thêm thời gian.</p>}
    {error && <p role="alert" className="text-red-500">{error}</p>}
    <div className="flex gap-2">
      <button type="button" disabled={busy} className="underline" onClick={() => setRefresh(n => n + 1)}>Tải lại tiến độ</button>
      {state?.status === 'processing' && <button type="button" disabled={busy} className="underline" onClick={() => void act('cancel')}>Yêu cầu hủy xử lý</button>}
      {(state?.status === 'error' || state?.status === 'cancelled') && <button type="button" disabled={busy} className="underline text-blue-600" onClick={() => void act('retry')}>Thử lại từ PDF đã lưu</button>}
    </div>
  </div>;
}
