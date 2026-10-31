import type { RankingExplanation } from '@/lib/api';

export function RankingExplanationPanel({ ranking }: { ranking: RankingExplanation }) {
  const scores = [
    ['Điểm Cross-Encoder', ranking.model_score],
    ['Điểm xếp hạng', ranking.ranking_score],
    ['Điểm heuristic', ranking.heuristic_score],
    ['Điểm hợp nhất truy xuất (RRF)', ranking.rrf_score],
    ['Điểm ưu tiên tổng hợp', ranking.composite_score],
  ] as const;
  const format = (score: number | null) => score === null ? 'Không có điểm' : score.toFixed(5);
  return <details className="mt-2 rounded border p-2 text-xs">
    <summary className="cursor-pointer font-medium">Giải thích xếp hạng · vị trí truy xuất {ranking.retrieval_position}</summary>
    <p className="mt-2">{ranking.summary}</p>
    <dl className="mt-2 space-y-1">{scores.map(([label, score]) => <div key={label} className="flex justify-between gap-3">
      <dt>{label}</dt><dd>{format(score)}</dd>
    </div>)}</dl>
    {ranking.facets.length > 0 && <ul className="mt-2 space-y-1">{ranking.facets.map(f =>
      <li key={f.key}>{f.label}: {format(f.score)}{f.selected ? ' · Được chọn ở lượt tiêu chí này' : ''}</li>)}</ul>}
    <p className="mt-2 text-gray-500">{ranking.note}</p>
  </details>;
}
