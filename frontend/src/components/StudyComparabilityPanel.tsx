'use client';
import { useState } from 'react';
import { compareStudyConditions, compareStudyFindings, type StudyComparability, type StudyRelations } from '@/lib/api';

export function StudyComparabilityPanel({ documents, focus, onOpenSource }: {
  documents: { id: string; title: string }[]; focus: string;
  onOpenSource: (documentId: string, page: number, quote: string) => void;
}) {
  const [first, setFirst] = useState(documents[0]?.id || '');
  const [second, setSecond] = useState(documents[1]?.id || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<StudyComparability | null>(null);
  const [signature, setSignature] = useState('');
  const [relations, setRelations] = useState<StudyRelations | null>(null);
  const a = documents.some(d => d.id === first) ? first : documents[0]?.id || '';
  const b = documents.some(d => d.id === second) ? second : documents[1]?.id || '';
  const current = JSON.stringify([a, b, focus]);
  const run = async (findings = false) => {
    setLoading(true); setError(''); setResult(null); setRelations(null); setSignature(current);
    try {
      if (findings) {
        const response = await compareStudyFindings(a, b, focus);
        setRelations(response); setResult(response.comparability);
      } else setResult(await compareStudyConditions(a, b, focus));
    }
    catch { setError('Chưa thể đánh giá. Kiểm tra quyền đọc hai bài và mô hình Ollama cục bộ rồi thử lại.'); }
    finally { setLoading(false); }
  };
  return <section className="rounded-xl border p-4 space-y-3">
    <h3 className="font-semibold">Kiểm tra điều kiện so sánh hai nghiên cứu</h3>
    <div className="flex flex-wrap gap-2">
      <select aria-label="Nghiên cứu A" className="border rounded p-2 max-w-full" disabled={loading} value={a} onChange={e => setFirst(e.target.value)}>
        {documents.map(d => <option key={d.id} value={d.id}>{d.title}</option>)}
      </select>
      <select aria-label="Nghiên cứu B" className="border rounded p-2 max-w-full" disabled={loading} value={b} onChange={e => setSecond(e.target.value)}>
        {documents.map(d => <option key={d.id} value={d.id}>{d.title}</option>)}
      </select>
      <button type="button" disabled={loading || !a || !b || a === b} onClick={() => void run()} className="rounded bg-blue-600 text-white p-2 disabled:opacity-50">
        {loading ? 'Đang kiểm tra…' : 'Kiểm tra điều kiện'}
      </button>
      <button type="button" disabled={loading || !a || !b || a === b || !focus.trim()} onClick={() => void run(true)} className="rounded bg-violet-600 text-white p-2 disabled:opacity-50">
        Đối chiếu đồng thuận / mâu thuẫn
      </button>
    </div>
    {!focus.trim() && <p className="text-sm text-gray-500">Nhập chủ đề hoặc kết cục ở ô câu hỏi phía trên để đối chiếu nhận định.</p>}
    {loading && <p role="status" className="text-sm">Mô hình cục bộ đang kiểm tra điều kiện và bằng chứng; quá trình có thể mất vài phút.</p>}
    {error && signature === current && <p role="alert">{error}</p>}
    {result && signature === current && <>
      <p className="font-semibold">{result.status === 'comparable' ? 'Có thể so sánh theo đánh giá của mô hình' : result.status === 'conditions_differ' ? 'Có khác biệt điều kiện — cần xem từng tiêu chí' : 'Chưa đủ dữ liệu để kết luận'}</p>
      <p className="text-sm">{result.message}</p>
      <div className="overflow-x-auto"><table className="w-full text-sm text-left">
        <thead><tr><th>Tiêu chí</th><th>Đánh giá</th><th>Bằng chứng bài A</th><th>Bằng chứng bài B</th></tr></thead>
        <tbody>{result.criteria.map(c => <tr key={c.key} className="border-t align-top">
          <td className="p-2">{c.label}</td>
          <td className="p-2">{c.status === 'matched' ? 'Tương đương (mô hình)' : c.status === 'different' ? 'Khác điều kiện (mô hình)' : 'Thiếu dữ liệu'}<p>{c.reason}</p></td>
          {[c.evidence_a, c.evidence_b].map((ev, index) => <td className="p-2" key={index}>{ev ? <>
            <blockquote>{ev.quote}</blockquote><button type="button" className="text-blue-600 underline" onClick={() => onOpenSource(ev.document_id, ev.page, ev.quote)}>Mở nguồn — trang {ev.page}</button>
          </> : 'Chưa có nguồn hợp lệ'}</td>)}
        </tr>)}</tbody>
      </table></div>
    </>}
    {relations && signature === current && <div className="space-y-3 border-t pt-3">
      <h4 className="font-semibold">Quan hệ giữa các nhận định</h4>
      <p className="text-sm">{relations.message}</p>
      {!relations.relations.length && <p>Chưa xác lập được quan hệ có đủ nguồn hợp lệ. Điều này không chứng minh hai bài đồng thuận hoặc không có mâu thuẫn.</p>}
      {relations.relations.map((relation, index) => <article key={index} className="border rounded p-3 space-y-2">
        <h5 className="font-semibold">{relation.relation === 'agreement' ? 'Đồng thuận — mô hình đánh giá' : 'Mâu thuẫn — mô hình đánh giá'}: {relation.aspect}</h5>
        <p>{relation.reason}</p>
        <div className="grid md:grid-cols-2 gap-3">
          {[relation.evidence_a, relation.evidence_b].map((ev, side) => <div key={side}>
            <p className="font-medium">Bài {side === 0 ? 'A' : 'B'}: {documents.find(d => d.id === ev.document_id)?.title}</p>
            <blockquote className="border-l-2 pl-2 whitespace-pre-wrap">{ev.quote}</blockquote>
            <button type="button" className="text-blue-600 underline" onClick={() => onOpenSource(ev.document_id, ev.page, ev.quote)}>Mở nguồn — trang {ev.page}</button>
          </div>)}
        </div>
      </article>)}
    </div>}
  </section>;
}
