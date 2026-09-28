'use client';

import { useEffect, useCallback, useState } from 'react';
import ReactFlow, {
 Node, Edge, Background, Controls,
 useNodesState, useEdgesState, BackgroundVariant,
 Handle, Position, NodeProps, EdgeProps, getSmoothStepPath,
 BaseEdge, EdgeLabelRenderer,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { GraphData, GraphNode, GraphEdge } from '@/lib/api';
import { X } from 'lucide-react';

// ── Vibrant palette ─────────────────────────────────────────────────────────

const PALETTE = [
 '#818CF8', '#38BDF8', '#34D399', '#FBBF24',
 '#F87171', '#A78BFA', '#F472B6', '#2DD4BF',
 '#60A5FA', '#FB923C', '#4ADE80', '#E879F9',
];

function getInitials(name: string) {
 const parts = name.trim().split(/\s+/);
 if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
 return name.slice(0, 2).toUpperCase();
}

// ── Electric Edge ────────────────────────────────────────────────────────────

function ElectricEdge({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, style, data }: EdgeProps) {
 const [edgePath] = getSmoothStepPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition });
 const color = data?.color ?? '#818CF8';

 return (
 <>
 {/* Glow layer */}
 <path
 id={`glow-${id}`}
 d={edgePath}
 fill="none"
 stroke={color}
 strokeWidth={6}
 strokeOpacity={0.08}
 strokeLinecap="round"
 />
 {/* Main edge */}
 <BaseEdge
 id={id}
 path={edgePath}
 style={{
 stroke: color,
 strokeWidth: 1.5,
 strokeOpacity: 0.55,
 filter: `drop-shadow(0 0 3px ${color}80)`,
 ...style,
 }}
 />
 {/* Animated pulse dot */}
 <circle r={3} fill={color} opacity={0.9} style={{ filter: `drop-shadow(0 0 4px ${color})` }}>
 <animateMotion dur="2.5s" repeatCount="indefinite" path={edgePath} />
 </circle>
 </>
 );
}

// ── Author Node ──────────────────────────────────────────────────────────────

function AuthorNode({ data, selected }: NodeProps) {
 const name = data.label as string;
 const short = name.length > 22 ? name.slice(0, 22) + '…' : name;

 return (
 <div
 title={name}
 style={{
 background: selected
 ? `linear-gradient(135deg, ${data.color}30, ${data.color}50)`
 : `linear-gradient(135deg, ${data.color}10, ${data.color}18)`,
 border: `1.5px solid ${data.color}${selected ? 'cc' : '50'}`,
 boxShadow: selected
 ? `0 0 0 3px ${data.color}25, 0 0 16px ${data.color}40, 0 4px 16px rgba(0,0,0,0.12)`
 : `0 0 8px ${data.color}15, 0 1px 4px rgba(0,0,0,0.06)`,
 color: selected ? data.color : data.color,
 backdropFilter: 'blur(12px)',
 transition: 'all 0.2s ease',
 }}
 className="flex items-center gap-2 px-3 py-2 rounded-full cursor-pointer select-none whitespace-nowrap"
 >
 <Handle type="source" position={Position.Bottom} style={{ opacity: 0, width: 0, height: 0 }} />
 <div
 className="w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-[8px] font-black"
 style={{
 background: selected ? data.color : `${data.color}25`,
 color: selected ? '#fff' : data.color,
 boxShadow: selected ? `0 2px 6px ${data.color}60` : 'none',
 }}
 >
 {getInitials(name)}
 </div>
 <span className="text-[11px] font-bold tracking-tight leading-none">{short}</span>
 <span
 className="text-[9px] font-bold px-1.5 py-px rounded-full leading-none"
 style={{
 background: selected ? `${data.color}30` : `${data.color}15`,
 border: `1px solid ${data.color}30`,
 }}
 >
 {data.paperCount}
 </span>
 </div>
 );
}

// ── Document Node ────────────────────────────────────────────────────────────

function DocumentNode({ data, selected }: NodeProps) {
 const title = data.label as string;
 const short = title.length > 55 ? title.slice(0, 55) + '…' : title;

 return (
 <div
 title={title}
 style={{
 background: selected
 ? `linear-gradient(135deg, var(--glass-bg-strong), var(--glass-bg-strong))`
 : 'var(--glass-bg)',
 border: `1.5px solid ${selected ? data.color : 'var(--border-solid, #E2E8F0)'}`,
 boxShadow: selected
 ? `0 0 0 3px ${data.color}20, 0 0 20px ${data.color}30, 0 8px 24px rgba(0,0,0,0.12)`
 : '0 2px 8px rgba(0,0,0,0.06)',
 backdropFilter: 'blur(12px)',
 transition: 'all 0.2s ease',
 }}
 className="rounded-xl cursor-pointer select-none w-[140px] overflow-hidden"
 >
 <Handle type="target" position={Position.Top} style={{ opacity: 0, width: 0, height: 0 }} />
 <div className="h-1 w-full" style={{ background: selected ? `linear-gradient(90deg, ${data.color}, ${data.color}80)` : `${data.color}60` }} />
 <div className="px-2.5 py-2.5">
 <p className="text-[10px] font-semibold text-slate-700 leading-snug line-clamp-2">
 {short}
 </p>
 {data.year && (
 <span
 className="inline-block mt-1.5 text-[9px] font-bold px-1.5 py-px rounded-md leading-none"
 style={{ background: `${data.color}15`, color: data.color, border: `1px solid ${data.color}25` }}
 >
 {data.year}
 </span>
 )}
 </div>
 </div>
 );
}

// ── Node type registry ────────────────────────────────────────────────────────

const nodeTypes = { authorNode: AuthorNode, documentNode: DocumentNode };
const edgeTypes = { electric: ElectricEdge };

// ── Layout ────────────────────────────────────────────────────────────────────

function buildLayout(nodes: GraphNode[], edges: GraphEdge[]) {
 const authors = nodes.filter(n => n.type === 'author');
 const docs = nodes.filter(n => n.type === 'document');

 const colorMap: Record<string, string> = {};
 authors.forEach((a, i) => { colorMap[a.id] = PALETTE[i % PALETTE.length]; });

 const docAuthorsMap: Record<string, string[]> = {};
 edges.forEach(e => {
 if (!docAuthorsMap[e.target]) docAuthorsMap[e.target] = [];
 docAuthorsMap[e.target].push(e.source);
 });

 const AUTH_GAP = 200;
 const authorXMap: Record<string, number> = {};
 const totalW = (authors.length - 1) * AUTH_GAP;
 authors.forEach((a, i) => { authorXMap[a.id] = i * AUTH_GAP - totalW / 2; });

 const DOC_W = 140, DOC_Y_START = 170, DOC_ROW_H = 120, BUCKET_W = 148;
 const colRowCount: Record<number, number> = {};

 const docRFNodes: Node[] = docs
 .map(doc => {
 const authIds = docAuthorsMap[doc.id] || [];
 const avgX = authIds.length ? authIds.reduce((s, id) => s + (authorXMap[id] ?? 0), 0) / authIds.length : 0;
 return { doc, avgX, authIds };
 })
 .sort((a, b) => a.avgX - b.avgX)
 .map(({ doc, avgX, authIds }) => {
 const col = Math.round(avgX / BUCKET_W);
 const row = colRowCount[col] ?? 0;
 colRowCount[col] = row + 1;
 const primaryColor = authIds[0] ? colorMap[authIds[0]] : '#94a3b8';
 return {
 id: doc.id, type: 'documentNode', selectable: true,
 data: {
 label: doc.data.label, year: doc.data.year, color: primaryColor,
 authorNames: authIds.map(id => authors.find(a => a.id === id)?.data.label).filter(Boolean),
 },
 position: { x: avgX - DOC_W / 2, y: DOC_Y_START + row * DOC_ROW_H },
 };
 });

 const authorRFNodes: Node[] = authors.map(a => ({
 id: a.id, type: 'authorNode', selectable: true,
 data: {
 label: a.data.label, color: colorMap[a.id],
 paperCount: docs.filter(d => (docAuthorsMap[d.id] || []).includes(a.id)).length,
 },
 position: { x: authorXMap[a.id] - 65, y: 0 },
 }));

 const rfEdges: Edge[] = edges.map(e => ({
 id: e.id,
 source: e.source,
 target: e.target,
 type: 'electric',
 data: { color: colorMap[e.source] ?? '#818CF8' },
 animated: false,
 style: { strokeWidth: 1.5 },
 }));

 return { rfNodes: [...authorRFNodes, ...docRFNodes], rfEdges };
}

// ── Main component ────────────────────────────────────────────────────────────

interface Props { data: GraphData }

type SelectedInfo = {
 type: 'author' | 'document';
 label: string;
 color: string;
 year?: number;
 paperCount?: number;
 authorNames?: string[];
};

export default function KnowledgeGraph({ data }: Props) {
 const [nodes, setNodes, onNodesChange] = useNodesState([]);
 const [edges, setEdges, onEdgesChange] = useEdgesState([]);
 const [selected, setSelected] = useState<SelectedInfo | null>(null);

 useEffect(() => {
 if (!data?.nodes?.length) return;
 const { rfNodes, rfEdges } = buildLayout(data.nodes, data.edges);
 setNodes(rfNodes as Node[]);
 setEdges(rfEdges as Edge[]);
 setSelected(null);
 }, [data]);

 const onNodeClick = useCallback((_: unknown, node: Node) => {
 setSelected({
 type: node.type === 'authorNode' ? 'author' : 'document',
 label: node.data.label,
 color: node.data.color,
 year: node.data.year,
 paperCount: node.data.paperCount,
 authorNames: node.data.authorNames,
 });
 }, []);

 const onPaneClick = useCallback(() => setSelected(null), []);

 return (
 <div className="w-full h-full relative">
 <ReactFlow
 nodes={nodes}
 edges={edges}
 nodeTypes={nodeTypes}
 edgeTypes={edgeTypes}
 onNodesChange={onNodesChange}
 onEdgesChange={onEdgesChange}
 onNodeClick={onNodeClick}
 onPaneClick={onPaneClick}
 fitView
 fitViewOptions={{ padding: 0.28 }}
 minZoom={0.12}
 attributionPosition="bottom-left"
 style={{ background: 'transparent' }}
 >
 <Background
 variant={BackgroundVariant.Dots}
 color="rgba(99,102,241,0.12)"
 gap={24}
 size={1.2}
 />
 <Controls
 className="!bottom-4 !left-4"
 style={{
 background: 'rgba(255,255,255,0.8)',
 backdropFilter: 'blur(12px)',
 border: '1px solid var(--border-solid, #E2E8F0)',
 borderRadius: '12px',
 boxShadow: '0 4px 16px rgba(0,0,0,0.06)',
 }}
 />
 </ReactFlow>

 {/* ── Legend ── */}
 <div
 className="absolute bottom-4 right-4 flex items-center gap-3 px-3 py-2 rounded-xl z-10"
 style={{
 background: 'var(--glass-bg)',
 backdropFilter: 'blur(12px)',
 border: '1px solid var(--border-solid, #E2E8F0)',
 boxShadow: '0 4px 16px rgba(0,0,0,0.06)',
 }}
 >
 <div className="flex items-center gap-1.5">
 <div className="w-5 h-3.5 rounded-full" style={{ background: 'linear-gradient(135deg, #818CF840, #818CF860)', border: '1px solid #818CF880' }} />
 <span className="text-[10px] text-slate-500 font-medium">Authors</span>
 </div>
 <div className="w-px h-3 bg-slate-200" />
 <div className="flex items-center gap-1.5">
 <div className="w-5 h-3.5 rounded-md" style={{ background: 'rgba(255,255,255,0.9)', border: '1.5px solid var(--border-solid, #E2E8F0)' }} />
 <span className="text-[10px] text-slate-500 font-medium">Documents</span>
 </div>
 <div className="w-px h-3 bg-slate-200" />
 <div className="flex items-center gap-1.5">
 <div className="w-5 h-0.5 rounded-full" style={{ background: 'linear-gradient(90deg, #818CF8, #38BDF8)', boxShadow: '0 0 4px #818CF840' }} />
 <span className="text-[10px] text-slate-500 font-medium">Links</span>
 </div>
 </div>

 {/* ── Info panel ── */}
 {selected && (
 <div
 className="absolute top-3 right-3 w-60 rounded-2xl overflow-hidden z-10"
 style={{
 background: 'var(--glass-bg-strong)',
 backdropFilter: 'blur(20px)',
 border: `1.5px solid ${selected.color}40`,
 boxShadow: `0 0 24px ${selected.color}20, 0 8px 32px rgba(0,0,0,0.10)`,
 }}
 >
 <div className="h-1 w-full" style={{ background: `linear-gradient(90deg, ${selected.color}, ${selected.color}80)` }} />
 <div className="px-4 py-3.5">
 <div className="flex items-center justify-between mb-3">
 <div className="flex items-center gap-2">
 <div
 className="w-7 h-7 rounded-full flex items-center justify-center text-[9px] font-black text-white shrink-0"
 style={{ background: `linear-gradient(135deg, ${selected.color}, ${selected.color}bb)`, boxShadow: `0 2px 8px ${selected.color}50` }}
 >
 {selected.type === 'author' ? getInitials(selected.label) : '·'}
 </div>
 <span className="text-[9px] font-bold uppercase tracking-widest" style={{ color: selected.color }}>
 {selected.type === 'author' ? 'Author' : 'Document'}
 </span>
 </div>
 <button onClick={() => setSelected(null)} className="text-slate-400 hover:text-slate-600 transition-colors">
 <X size={14} />
 </button>
 </div>

 <p className="text-xs font-semibold text-slate-700 leading-snug mb-3">{selected.label}</p>

 <div className="space-y-2 text-[11px] text-slate-500">
 {selected.year && (
 <div className="flex items-center justify-between">
 <span>Published</span>
 <span className="font-bold text-slate-700">{selected.year}</span>
 </div>
 )}
 {selected.type === 'author' && selected.paperCount !== undefined && (
 <div className="flex items-center justify-between">
 <span>Articles</span>
 <span
 className="font-black px-2 py-0.5 rounded-lg text-[10px]"
 style={{ background: `${selected.color}15`, color: selected.color }}
 >
 {selected.paperCount}
 </span>
 </div>
 )}
 {selected.authorNames && (selected.authorNames as string[]).length > 0 && (
 <div>
 <p className="text-slate-400 mb-1.5 text-[10px] uppercase tracking-wider font-semibold">Authors</p>
 <div className="flex flex-wrap gap-1">
 {(selected.authorNames as string[]).map((name, i) => (
 <span
 key={i}
 className="px-2 py-0.5 rounded-lg text-[9px] font-semibold"
 style={{ background: `${selected.color}12`, color: selected.color, border: `1px solid ${selected.color}25` }}
 >
 {name}
 </span>
 ))}
 </div>
 </div>
 )}
 </div>
 </div>
 </div>
 )}
 </div>
 );
}
