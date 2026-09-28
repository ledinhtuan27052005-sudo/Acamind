'use client';

import { Canvas, ThreeEvent, useFrame } from '@react-three/fiber';
import { OrbitControls, useGLTF, useFBX, Environment, Billboard } from '@react-three/drei';
import { useState, useRef, Suspense, useEffect, useMemo } from 'react';
import * as THREE from 'three';
import { ORGAN_DATA, OrganInfo } from '@/lib/bodyData';

// ── Part colors ───────────────────────────────────────────────────────────────

const PART_COLORS: Record<string, number> = {
 head: 0xf4a261,
 neck: 0xe9c46a,
 chest: 0xe76f51,
 abdomen: 0x2a9d8f,
 pelvis: 0x457b9d,
 left_shoulder: 0x6a9fb5,
 right_shoulder: 0x6a9fb5,
 left_arm: 0x88b4c8,
 right_arm: 0x88b4c8,
 left_leg: 0xa8dadc,
 right_leg: 0xa8dadc,
 left_lower_leg: 0x76c8d0,
 right_lower_leg: 0x76c8d0,
 left_foot: 0x52b6c0,
 right_foot: 0x52b6c0,
};

// ── Mesh-name classifier ──────────────────────────────────────────────────────

function classifyByMeshName(object: THREE.Object3D): string | null {
 let obj: THREE.Object3D | null = object;
 while (obj) {
 const n = obj.name.toLowerCase().replace(/[\s\-]/g, '_');
 if (n && !['scene','root','armature','skeleton','body','mesh','object',''].includes(n)) {
 const isL = n.includes('left') || n.includes('_l_') || n.endsWith('_l') || n.includes('.l');
 const isR = n.includes('right') || n.includes('_r_') || n.endsWith('_r') || n.includes('.r');
 if (n.includes('head') || n.includes('skull') || n.includes('cranium') || n.includes('face')) return 'head';
 if (n.includes('neck') || n.includes('cervical')) return 'neck';
 if (n.includes('chest') || n.includes('thorax') || n.includes('ribcage') || n.includes('torso')) return 'chest';
 if (n.includes('abdomen') || n.includes('belly') || n.includes('stomach')) return 'abdomen';
 if (n.includes('pelvis') || n.includes('hip') || n.includes('groin')) return 'pelvis';
 if (n.includes('shoulder') || n.includes('clavicle') || n.includes('deltoid')) {
 if (isL) return 'left_shoulder'; if (isR) return 'right_shoulder';
 }
 if (n.includes('upper_arm') || n.includes('bicep') || n.includes('forearm') || n.includes('wrist') || n.includes('hand')) {
 if (isL) return 'left_arm'; if (isR) return 'right_arm';
 }
 if (n.includes('arm') && !n.includes('forearm')) {
 if (isL) return 'left_arm'; if (isR) return 'right_arm';
 }
 if (n.includes('foot') || n.includes('toe') || n.includes('ankle')) {
 if (isL) return 'left_foot'; if (isR) return 'right_foot';
 }
 if (n.includes('shin') || n.includes('calf') || n.includes('tibia') || n.includes('lower_leg')) {
 if (isL) return 'left_lower_leg'; if (isR) return 'right_lower_leg';
 }
 if (n.includes('thigh') || n.includes('femur') || n.includes('knee')) {
 if (isL) return 'left_leg'; if (isR) return 'right_leg';
 }
 if (n.includes('leg') && !n.includes('lower')) {
 if (isL) return 'left_leg'; if (isR) return 'right_leg';
 }
 }
 obj = obj.parent;
 }
 return null;
}

function classifyByPosition(point: THREE.Vector3, bbox: THREE.Box3): string {
 const size = new THREE.Vector3();
 const center = new THREE.Vector3();
 bbox.getSize(size);
 bbox.getCenter(center);
 const ny = Math.max(0, Math.min(1, (point.y - bbox.min.y) / size.y));
 const dx = point.x - center.x;
 const nx = Math.abs(dx) / (size.x * 0.5);
 if (nx > 0.52) return dx < 0 ? 'left_arm' : 'right_arm';
 if (nx > 0.30 && ny > 0.660) return dx < 0 ? 'left_shoulder' : 'right_shoulder';
 if (ny > 0.875) return 'head';
 if (ny > 0.813) return 'neck';
 if (ny > 0.660) return 'chest';
 if (ny > 0.520) return 'abdomen';
 if (ny > 0.420) return 'pelvis';
 if (ny > 0.220) return dx < -0.01 ? 'left_leg' : 'right_leg';
 if (ny > 0.075) return dx < -0.01 ? 'left_lower_leg' : 'right_lower_leg';
 return dx < -0.01 ? 'left_foot' : 'right_foot';
}

function classifyMesh(point: THREE.Vector3, bbox: THREE.Box3, object?: THREE.Object3D): string {
 if (object) { const n = classifyByMeshName(object); if (n) return n; }
 return classifyByPosition(point, bbox);
}

// ── Pulse ring ────────────────────────────────────────────────────────────────

function PulseRing({ color, delay }: { color: number; delay: number }) {
 const meshRef = useRef<THREE.Mesh>(null!);
 const matRef = useRef<THREE.MeshBasicMaterial>(null!);
 const t = useRef(delay);
 useFrame((_, delta) => {
 t.current = (t.current + delta * 0.85) % 1;
 if (meshRef.current) meshRef.current.scale.setScalar(0.02 + t.current * 0.14);
 if (matRef.current) matRef.current.opacity = Math.max(0, (1 - t.current) * 0.88);
 });
 return (
 <mesh ref={meshRef}>
 <ringGeometry args={[0.78, 1.0, 40]} />
 <meshBasicMaterial ref={matRef} color={new THREE.Color(color)} transparent depthTest={false} side={THREE.DoubleSide} />
 </mesh>
 );
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Normalize a cloned scene to fit within targetScale (half-extents) */
function normalizeToScale(obj: THREE.Object3D, targetScale: [number, number, number]): THREE.Group {
 const wrapper = new THREE.Group();
 wrapper.add(obj);

 const box = new THREE.Box3().setFromObject(wrapper);
 const size = new THREE.Vector3();
 const ctr = new THREE.Vector3();
 box.getSize(size);
 box.getCenter(ctr);

 const maxTarget = Math.max(...targetScale) * 2.4;
 const maxSize = Math.max(size.x, size.y, size.z);
 const s = maxSize > 0 ? maxTarget / maxSize : 1;

 obj.scale.setScalar(s);
 const newCtr = ctr.clone().multiplyScalar(s);
 obj.position.sub(newCtr);

 return wrapper;
}

/**
 * Normalize a scene với scale anisotropic — mỗi trục scale độc lập để vừa targetScale.
 * Dùng cho model có tỉ lệ width:height:depth cố định mà muốn áp tỉ lệ mới.
 */
function normalizeToScaleAniso(
 obj: THREE.Object3D,
 targetSize: [number, number, number] // Target size (X×Y×Z) after normalize
): THREE.Group {
 const wrapper = new THREE.Group();
 wrapper.add(obj);

 const box = new THREE.Box3().setFromObject(wrapper);
 const size = new THREE.Vector3();
 const ctr = new THREE.Vector3();
 box.getSize(size);
 box.getCenter(ctr);

 // Scale mỗi trục để bbox gốc vừa targetSize
 const sx = size.x > 0 ? targetSize[0] / size.x : 1;
 const sy = size.y > 0 ? targetSize[1] / size.y : 1;
 const sz = size.z > 0 ? targetSize[2] / size.z : 1;

 obj.scale.set(sx, sy, sz);
 const newCtr = ctr.clone();
 newCtr.x *= sx; newCtr.y *= sy; newCtr.z *= sz;
 obj.position.sub(newCtr);

 return wrapper;
}

/** Overwrite all mesh materials with an X-ray emissive material. */
function overrideMaterials(
 obj: THREE.Object3D,
 color: THREE.Color,
 emissiveIntensity: number,
 opacity: number,
) {
 obj.traverse((child) => {
 if (!(child instanceof THREE.Mesh)) return;
 child.material = new THREE.MeshPhysicalMaterial({
 color,
 emissive: color,
 emissiveIntensity,
 transparent: true,
 opacity,
 roughness: 0.35,
 metalness: 0.04,
 depthWrite: false,
 });
 child.renderOrder = 500;
 });
}

// ── GLB organ mesh ────────────────────────────────────────────────────────────

interface OrganMeshProps {
 organ: OrganInfo;
 selected: string | null;
 onSelect: (id: string) => void;
 onHover: (id: string | null) => void;
}

function GlbOrganMesh({
 gltfScene,
 organ,
 selected,
 onSelect,
 onHover,
}: OrganMeshProps & { gltfScene: THREE.Object3D }) {
 const isSel = selected === organ.id;
 const [hov, setHov] = useState(false);
 const heartRef = useRef<THREE.Group>(null!);
 const t = useRef(0);
 const color = useMemo(() => new THREE.Color(organ.color), [organ.color]);

 // Heartbeat
 useFrame((_, delta) => {
 if (organ.id !== 'heart' || !heartRef.current) return;
 t.current += delta * 2.2;
 const beat = 1 + Math.pow(Math.max(0, Math.sin(t.current * Math.PI)), 8) * 0.12;
 heartRef.current.scale.setScalar(beat);
 });

 // Clone + normalize once
 const normalizedGroup = useMemo(() => {
 if (!gltfScene) return null;
 return normalizeToScale(gltfScene.clone(true), organ.scale);
 }, [gltfScene, organ.scale]);

 // Re-apply material khi state thay đổi
 useEffect(() => {
 if (!normalizedGroup) return;
 const ei = isSel ? 2.4 : hov ? 1.4 : 0.60;
 const op = isSel ? 1.0 : hov ? 0.92 : 0.84;
 overrideMaterials(normalizedGroup, color, ei, op);
 }, [normalizedGroup, isSel, hov, color]);

 if (!normalizedGroup) return null;

 return (
 <group position={organ.pos}>
 {/* Visual model - no click event */}
 <group ref={organ.id === 'heart' ? heartRef : undefined}>
 <primitive object={normalizedGroup} />
 </group>

 {/* Hit zone - minimum 0.12 per axis for easy clicking */}
 <group scale={organ.scale.map(s => Math.max(s, 0.12)) as [number,number,number]}>
 <mesh
 renderOrder={600}
 onClick={(e) => { e.stopPropagation(); onSelect(organ.id); }}
 onPointerOver={(e) => { e.stopPropagation(); setHov(true); onHover(organ.id); document.body.style.cursor = 'pointer'; }}
 onPointerOut={() => { setHov(false); onHover(null); document.body.style.cursor = 'default'; }}
 >
 <boxGeometry args={[2, 2, 2]} />
 <meshBasicMaterial transparent opacity={0} depthWrite={false} />
 </mesh>
 </group>

 </group>
 );
}

// ── FBX organ mesh ────────────────────────────────────────────────────────────

function FbxOrganMesh({
 fbxScene,
 organ,
 mirrorX = false,
 selected,
 onSelect,
 onHover,
}: OrganMeshProps & { fbxScene: THREE.Group; mirrorX?: boolean }) {
 const isSel = selected === organ.id;
 const [hov, setHov] = useState(false);
 const color = useMemo(() => new THREE.Color(organ.color), [organ.color]);

 const normalizedGroup = useMemo(() => {
 const clone = fbxScene.clone(true);
 if (mirrorX) clone.scale.x *= -1;
 return normalizeToScale(clone, organ.scale);
 }, [fbxScene, organ.scale, mirrorX]);

 useEffect(() => {
 if (!normalizedGroup) return;
 const ei = isSel ? 1.8 : hov ? 1.2 : 0.55;
 const op = isSel ? 0.97 : hov ? 0.90 : 0.82;
 overrideMaterials(normalizedGroup, color, ei, op);
 }, [normalizedGroup, isSel, hov, color]);

 return (
 <group position={organ.pos}>
 {/* Visual model – no click events */}
 <primitive object={normalizedGroup} />

 {/* Hit zone – minimum 0.12 per axis */}
 <group scale={organ.scale.map(s => Math.max(s, 0.12)) as [number,number,number]}>
 <mesh
 renderOrder={600}
 onClick={(e) => { e.stopPropagation(); onSelect(organ.id); }}
 onPointerOver={(e) => { e.stopPropagation(); setHov(true); onHover(organ.id); document.body.style.cursor = 'pointer'; }}
 onPointerOut={() => { setHov(false); onHover(null); document.body.style.cursor = 'default'; }}
 >
 <boxGeometry args={[2, 2, 2]} />
 <meshBasicMaterial transparent opacity={0} depthWrite={false} />
 </mesh>
 </group>

 </group>
 );
}

// ── Lungs FBX (both lungs in one file – click routes by X position) ───────────

function FbxLungsMesh({
 fbxScene,
 selected,
 onSelect,
 onHover,
}: {
 fbxScene: THREE.Group;
 selected: string | null;
 onSelect: (id: string) => void;
 onHover: (id: string | null) => void;
}) {
 const leftOrgan = ORGAN_DATA.left_lung;

 const isSelLeft = selected === 'left_lung';
 const isSelRight = selected === 'right_lung';
 const [hov, setHov] = useState<'left_lung' | 'right_lung' | null>(null);

 // Combined position & scale (center between both lungs)
 // Phổi ở giữa lồng ngực, Y ≈ 0.51 trong hệ chuẩn hóa [-1, 1].
 // Kích thước mỗi phổi (giải phẫu người): cao 25cm, rộng 13-14cm, sâu 10-12cm.
 // Tỉ lệ trong hệ chuẩn hóa (đã thu nhỏ 20%): height 0.092, width mỗi bên 0.046, depth 0.040.
 const combinedPos: [number, number, number] = [0, 0.51, 0.02];
 // Bbox mục tiêu của 2 phổi (X = 2× khoảng cách + width mỗi bên)
 const combinedScale: [number, number, number] = [0.20, 0.10, 0.08];

 const color = useMemo(() => new THREE.Color(leftOrgan.color), [leftOrgan.color]);

 const normalizedGroup = useMemo(() => {
 const clone = fbxScene.clone(true);
 return normalizeToScale(clone, combinedScale);
 }, [fbxScene]);

 const isAnySel = isSelLeft || isSelRight;
 const isAnyHov = hov !== null;

 useEffect(() => {
 if (!normalizedGroup) return;
 const ei = isAnySel ? 1.8 : isAnyHov ? 1.2 : 0.55;
 const op = isAnySel ? 0.97 : isAnyHov ? 0.90 : 0.82;
 overrideMaterials(normalizedGroup, color, ei, op);
 }, [normalizedGroup, isAnySel, isAnyHov, color]);

 return (
 <group position={combinedPos}
 onClick={(e) => {
 e.stopPropagation();
 // Route to left or right lung by click X
 onSelect(e.point.x < 0 ? 'left_lung' : 'right_lung');
 }}
 onPointerOver={(e) => {
 e.stopPropagation();
 const side: 'left_lung' | 'right_lung' = e.point.x < 0 ? 'left_lung' : 'right_lung';
 setHov(side);
 onHover(side);
 document.body.style.cursor = 'pointer';
 }}
 onPointerOut={() => { setHov(null); onHover(null); document.body.style.cursor = 'default'; }}
 >
 <primitive object={normalizedGroup} />
 </group>
 );
}

// ── Kidneys FBX (both kidneys in one file – click routes by X position) ───────
// File kidney.fbx chứa sẵn 2 quả thận (trái + phải) trong cùng model, nên chỉ
// cần load 1 lần và route click theo X position (giống phổi).

function FbxKidneysMesh({
 fbxScene,
 selected,
 onSelect,
 onHover,
}: {
 fbxScene: THREE.Group;
 selected: string | null;
 onSelect: (id: string) => void;
 onHover: (id: string | null) => void;
}) {
 const leftOrgan = ORGAN_DATA.left_kidney;

 const isSelLeft = selected === 'left_kidney';
 const isSelRight = selected === 'right_kidney';
 const [hov, setHov] = useState<'left_kidney' | 'right_kidney' | null>(null);

 // Vị trí giải phẫu: thận nằm ở vùng bụng sau (retroperitoneal), ngang đốt sống
 // T12–L3, hai bên cột sống. Thận phải thấp hơn thận trái ~1–2cm do gan đẩy.
 // Trong hệ chuẩn hóa [-1, 1], Y ≈ 0.26 (dưới gan/dạ dày).
 const combinedPos: [number, number, number] = [0, 0.26, -0.04];

 // Tỉ lệ GIẢI PHẪU người thật (mỗi thận): width × height × depth = 6 × 11 × 3 cm.
 // Hệ tọa độ chuẩn hóa (Y từ -1 đến +1 ứng với cơ thể cao 1.8m):
 // mỗi thận rộng 0.033, cao 0.061, dày 0.017 (width:height:depth = 1:1.83:0.5).
 // Model FBX gốc có tỉ lệ mesh = 1:1.38:0.61 (gần giải phẫu nhưng cần điều chỉnh).
 // Ta scale:
 // - đồng đều (uniform) để width mỗi thận = 0.045 (một chút lớn hơn để dễ nhìn)
 // - sau đó stretch Y thêm 1.33× (= 1.83/1.38) để có height đúng giải phẫu
 // - và compress Z 0.82× (= 0.5/0.61) để có depth đúng giải phẫu
 // Hai thận cách nhau X ≈ 0.06 (cách nhau ~5.5cm) — sát cột sống.
 const kidneyW = 0.045; // half-width (X) of each kidney
 const kidneyH = 0.082; // half-height (Y) of each kidney (0.045 × 1.83)
 const kidneyD = 0.023; // half-depth (Z) of each kidney (0.045 × 0.5)
 const kidneyGap = 0.04; // gap between kidneys along X (each offset from center)

 // targetBboxSize = toàn bộ bbox gồm 2 thận
 // X: kidneyGap×2 + kidneyW×2 = 0.08 + 0.09 = 0.17
 // Y: kidneyH×2 = 0.164
 // Z: kidneyD×2 = 0.046
 const targetBboxSize: [number, number, number] = [
 (kidneyGap + kidneyW) * 2,
 kidneyH * 2,
 kidneyD * 2,
 ];

 const color = useMemo(() => new THREE.Color(leftOrgan.color), [leftOrgan.color]);

 const normalizedGroup = useMemo(() => {
 const clone = fbxScene.clone(true);
 // Scale anisotropic để giữ tỉ lệ width:height:depth đúng giải phẫu
 return normalizeToScaleAniso(clone, targetBboxSize);
 }, [fbxScene]);

 const isAnySel = isSelLeft || isSelRight;
 const isAnyHov = hov !== null;

 useEffect(() => {
 if (!normalizedGroup) return;
 const ei = isAnySel ? 1.8 : isAnyHov ? 1.2 : 0.55;
 const op = isAnySel ? 0.97 : isAnyHov ? 0.90 : 0.82;
 overrideMaterials(normalizedGroup, color, ei, op);
 }, [normalizedGroup, isAnySel, isAnyHov, color]);

 // Hit zones cho 2 thận — box lớn hơn mesh thật để dễ click
 // Thận phải (anatomical right) ở X âm (bên trái màn hình)
 // Thận trái (anatomical left) ở X dương (bên phải màn hình)
 // Sau normalize, mỗi thận có center ở ±(kidneyGap + kidneyW/2)
 const leftKidneyHitPos: [number, number, number] = [kidneyGap + kidneyW / 2, 0, 0];
 const rightKidneyHitPos: [number, number, number] = [-(kidneyGap + kidneyW / 2), 0, 0];
 const hitScale: [number, number, number] = [kidneyW * 2.5, kidneyH * 2.0, kidneyD * 4.0];

 return (
 <group position={combinedPos}>
 {/* Visual model */}
 <primitive object={normalizedGroup} />

 {/* Left kidney (anatomical) - right side of screen */}
 <group
 position={leftKidneyHitPos}
 scale={hitScale}
 onClick={(e) => { e.stopPropagation(); onSelect('left_kidney'); }}
 onPointerOver={(e) => {
 e.stopPropagation();
 setHov('left_kidney');
 onHover('left_kidney');
 document.body.style.cursor = 'pointer';
 }}
 onPointerOut={() => { setHov(null); onHover(null); document.body.style.cursor = 'default'; }}
 >
 <mesh renderOrder={600}>
 <boxGeometry args={[1, 1, 1]} />
 <meshBasicMaterial transparent opacity={0} depthWrite={false} />
 </mesh>
 </group>

 {/* Right kidney (anatomical) - left side of screen */}
 <group
 position={rightKidneyHitPos}
 scale={hitScale}
 onClick={(e) => { e.stopPropagation(); onSelect('right_kidney'); }}
 onPointerOver={(e) => {
 e.stopPropagation();
 setHov('right_kidney');
 onHover('right_kidney');
 document.body.style.cursor = 'pointer';
 }}
 onPointerOut={() => { setHov(null); onHover(null); document.body.style.cursor = 'default'; }}
 >
 <mesh renderOrder={600}>
 <boxGeometry args={[1, 1, 1]} />
 <meshBasicMaterial transparent opacity={0} depthWrite={false} />
 </mesh>
 </group>
 </group>
 );
}

// ── GLB-based organs loader ───────────────────────────────────────────────────

function GlbOrgans({ selected, onSelect, onHover }: {
 selected: string | null; onSelect: (id: string) => void; onHover: (id: string | null) => void;
}) {
 const brainGltf = useGLTF('/models/brain.glb');
 const heartGltf = useGLTF('/models/heart.glb');
 const liverGltf = useGLTF('/models/liver.glb');
 const intestinesGltf = useGLTF('/models/intestines.glb');

 return (
 <>
 {brainGltf.scene && (
 <GlbOrganMesh gltfScene={brainGltf.scene} organ={ORGAN_DATA.brain}
 selected={selected} onSelect={onSelect} onHover={onHover} />
 )}
 {heartGltf.scene && (
 <GlbOrganMesh gltfScene={heartGltf.scene} organ={ORGAN_DATA.heart}
 selected={selected} onSelect={onSelect} onHover={onHover} />
 )}
 {liverGltf.scene && (
 <GlbOrganMesh gltfScene={liverGltf.scene} organ={ORGAN_DATA.liver}
 selected={selected} onSelect={onSelect} onHover={onHover} />
 )}
 {intestinesGltf.scene && (
 <GlbOrganMesh gltfScene={intestinesGltf.scene} organ={ORGAN_DATA.intestines}
 selected={selected} onSelect={onSelect} onHover={onHover} />
 )}
 </>
 );
}

// ── FBX-based organs loader ───────────────────────────────────────────────────

function FbxOrgans({ selected, onSelect, onHover }: {
 selected: string | null; onSelect: (id: string) => void; onHover: (id: string | null) => void;
}) {
 const lungsFbx = useFBX('/models/lungs.fbx');
 const kidneyFbx = useFBX('/models/kidney.fbx');

 return (
 <>
 <FbxLungsMesh fbxScene={lungsFbx} selected={selected} onSelect={onSelect} onHover={onHover} />
 {/* kidney.fbx contains both kidneys (left + right) in 1 model —
 load once and route click by X position. */}
 <FbxKidneysMesh fbxScene={kidneyFbx} selected={selected} onSelect={onSelect} onHover={onHover} />
 </>
 );
}

// ── Geometric fallback for remaining organs (stomach, intestines, bladder) ────

function OrganGeo({ organ }: { organ: OrganInfo }) {
 if (organ.geo === 'sphere') return <sphereGeometry args={[1, 28, 28]} />;
 if (organ.geo === 'box') return <boxGeometry args={[1, 1, 1]} />;
 if (organ.geo === 'capsule') return <capsuleGeometry args={[0.5, 1, 6, 14]} />;
 if (organ.geo === 'torus') return <torusGeometry args={[1, 0.38, 10, 28]} />;
 // Ellipsoid: sphere bị scale theo relScale để thành hình trứng / hạt đậu / bầu dục
 if (organ.geo === 'ellipsoid') return <sphereGeometry args={[1, 28, 28]} />;
 return null;
}

function CompoundPartMesh({ part, color, isSel, hov }: {
 part: NonNullable<OrganInfo['compoundParts']>[number];
 color: THREE.Color; isSel: boolean; hov: boolean;
}) {
 // Render 1 phần của compound organ (đã scale theo relScale)
 return (
 <group position={part.relPos} scale={part.relScale}>
 <mesh renderOrder={500}>
 {part.geo === 'sphere' && <sphereGeometry args={[1, 24, 24]} />}
 {part.geo === 'box' && <boxGeometry args={[1, 1, 1]} />}
 {part.geo === 'capsule' && <capsuleGeometry args={(part.args ?? [0.5, 1, 6, 14]) as [number, number, number, number]} />}
 {part.geo === 'torus' && <torusGeometry args={[1, 0.38, 10, 28]} />}
 {part.geo === 'ellipsoid' && <sphereGeometry args={[1, 24, 24]} />}
 <meshPhysicalMaterial color={color} emissive={color}
 emissiveIntensity={isSel ? 2.0 : hov ? 1.2 : 0.55}
 transparent opacity={isSel ? 0.96 : hov ? 0.90 : 0.80}
 roughness={0.25} metalness={0.05} depthWrite={false} />
 </mesh>
 </group>
 );
}

function GeoOrganMesh({ organ, selected, onSelect, onHover }: OrganMeshProps) {
 const isSel = selected === organ.id;
 const [hov, setHov] = useState(false);
 const color = new THREE.Color(organ.color);
 const hitS = organ.scale.map(s => Math.max(s, 0.12)) as [number,number,number];
 const isCompound = organ.geo === 'compound';

 return (
 <group position={organ.pos}>
 {/* Visual */}
 <group scale={organ.scale}>
 {isCompound ? (
 <>
 {(organ.compoundParts ?? []).map((part, i) => (
 <CompoundPartMesh key={i} part={part} color={color} isSel={isSel} hov={hov} />
 ))}
 </>
 ) : (
 <mesh renderOrder={500}>
 <OrganGeo organ={organ} />
 <meshPhysicalMaterial color={color} emissive={color}
 emissiveIntensity={isSel ? 2.0 : hov ? 1.2 : 0.55}
 transparent opacity={isSel ? 0.96 : hov ? 0.90 : 0.80}
 roughness={0.25} metalness={0.05} depthWrite={false} />
 </mesh>
 )}
 </group>
 {/* Hit zone – minimum 0.12 per axis */}
 <group scale={hitS}>
 <mesh renderOrder={600}
 onClick={(e) => { e.stopPropagation(); onSelect(organ.id); }}
 onPointerOver={(e) => { e.stopPropagation(); setHov(true); onHover(organ.id); document.body.style.cursor = 'pointer'; }}
 onPointerOut={() => { setHov(false); onHover(null); document.body.style.cursor = 'default'; }}
 >
 <boxGeometry args={[2, 2, 2]} />
 <meshBasicMaterial transparent opacity={0} depthWrite={false} />
 </mesh>
 </group>
 </group>
 );
}

// ── Full organ layer (model + fallback geo) ───────────────────────────────────

// Các cơ quan dùng hình học (chưa có model 3D) — bao gồm cơ quan thêm mới
// theo ảnh tham chiếu "Internal organs" (stomach, bladder, reproductive_system).
const GEO_ORGAN_IDS = [
 'stomach',
 'bladder',
 'reproductive_system',
];

function OrganLayer({ selected, onSelect, onHover }: {
 selected: string | null; onSelect: (id: string) => void; onHover: (id: string | null) => void;
}) {
 return (
 <group>
 <Suspense fallback={null}>
 <GlbOrgans selected={selected} onSelect={onSelect} onHover={onHover} />
 </Suspense>
 <Suspense fallback={null}>
 <FbxOrgans selected={selected} onSelect={onSelect} onHover={onHover} />
 </Suspense>
 {GEO_ORGAN_IDS.map((id) => (
 <GeoOrganMesh key={id} organ={ORGAN_DATA[id]}
 selected={selected} onSelect={onSelect} onHover={onHover} />
 ))}
 </group>
 );
}

// ── Human GLB with X-ray + click detection ────────────────────────────────────

function GltfHuman({ selected, onSelect, onHover, xray }: {
 selected: string | null; onSelect: (id: string) => void;
 onHover: (id: string | null) => void; xray: boolean;
}) {
 const gltf = useGLTF('/models/body_male.glb');
 const scene = gltf.scene ?? gltf.scenes?.[0];
 const groupRef = useRef<THREE.Group>(null!);
 const bboxRef = useRef<THREE.Box3>(new THREE.Box3());
 const readyRef = useRef(false);
 const scaleRef = useRef(1);
 const origMatsRef = useRef<Map<THREE.Material, { opacity: number; transparent: boolean }>>(new Map());
 const [markerLocalPos, setMarkerLocalPos] = useState<THREE.Vector3 | null>(null);
 const [markerColor, setMarkerColor] = useState<number>(0x4a7c96);

 useEffect(() => {
 if (!scene) return;
 scene.updateMatrixWorld(true);
 const box = new THREE.Box3().setFromObject(scene);
 const size = new THREE.Vector3();
 const center = new THREE.Vector3();
 box.getSize(size);
 box.getCenter(center);
 const maxDim = Math.max(size.x, size.y, size.z);
 const s = maxDim > 0 ? 2.0 / maxDim : 1;
 scaleRef.current = s;
 if (groupRef.current) {
 groupRef.current.scale.setScalar(s);
 // Re-center về gốc 0,0,0 để hệ tọa độ Y đối xứng [-1, +1],
 // khớp với hệ toạ độ mà ORGAN_DATA và FbxLungsMesh/FbxKidneysMesh sử dụng.
 groupRef.current.position.set(-center.x * s, -center.y * s, -center.z * s);
 }
 bboxRef.current.copy(new THREE.Box3(
 new THREE.Vector3((box.min.x - center.x) * s, (box.min.y - center.y) * s, (box.min.z - center.z) * s),
 new THREE.Vector3((box.max.x - center.x) * s, (box.max.y - center.y) * s, (box.max.z - center.z) * s),
 ));
 scene.traverse((obj) => {
 if (!(obj instanceof THREE.Mesh)) return;
 const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
 mats.forEach((m: THREE.Material) => {
 if (!origMatsRef.current.has(m))
 origMatsRef.current.set(m, { opacity: (m as THREE.MeshStandardMaterial).opacity ?? 1, transparent: m.transparent });
 });
 });
 readyRef.current = true;
 }, [scene]);

 useEffect(() => {
 if (!scene || !readyRef.current) return;
 scene.traverse((obj) => {
 if (!(obj instanceof THREE.Mesh)) return;
 const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
 mats.forEach((m: THREE.Material) => {
 const orig = origMatsRef.current.get(m);
 if (xray) {
 m.transparent = true;
 (m as THREE.MeshStandardMaterial).opacity = 0.12;
 m.depthWrite = false;
 } else {
 m.transparent = orig?.transparent ?? false;
 (m as THREE.MeshStandardMaterial).opacity = orig?.opacity ?? 1;
 m.depthWrite = true;
 }
 m.needsUpdate = true;
 });
 });
 }, [xray, scene]);

 useEffect(() => { if (!selected) setMarkerLocalPos(null); }, [selected]);

 if (!scene) return null;
 return (
 <group ref={groupRef}>
 <primitive
 object={scene}
 onClick={(e: ThreeEvent<MouseEvent>) => {
 e.stopPropagation();
 if (!readyRef.current || !e.object) return;
 const part = classifyMesh(e.point, bboxRef.current, e.object);
 const localPoint = groupRef.current.worldToLocal(e.point.clone());
 setMarkerLocalPos(localPoint);
 setMarkerColor(PART_COLORS[part] ?? 0x4a7c96);
 onSelect(part);
 }}
 onPointerOver={(e: ThreeEvent<PointerEvent>) => {
 e.stopPropagation();
 if (!readyRef.current) { document.body.style.cursor = 'default'; return; }
 onHover(classifyMesh(e.point, bboxRef.current, e.object));
 document.body.style.cursor = 'pointer';
 }}
 onPointerOut={() => { onHover(null); document.body.style.cursor = 'default'; }}
 />
 {markerLocalPos && (
 <Billboard position={markerLocalPos}>
 <group scale={1 / scaleRef.current}>
 <mesh renderOrder={1000}><circleGeometry args={[0.034, 40]} /><meshBasicMaterial color="white" depthTest={false} /></mesh>
 <mesh renderOrder={1001}><circleGeometry args={[0.024, 40]} /><meshBasicMaterial color={new THREE.Color(markerColor)} depthTest={false} /></mesh>
 <mesh renderOrder={1002}><circleGeometry args={[0.008, 20]} /><meshBasicMaterial color="white" depthTest={false} /></mesh>
 <PulseRing color={markerColor} delay={0.0} />
 <PulseRing color={markerColor} delay={0.5} />
 </group>
 </Billboard>
 )}
 </group>
 );
}

// ── Holographic fallback body (no GLB) ────────────────────────────────────────

type GeoType = 'sphere' | 'box' | 'cylinder' | 'capsule';
interface PartDef { id: string; geo: GeoType; args: number[]; pos: [number,number,number]; rot?: [number,number,number]; }
const PARTS: PartDef[] = [
 { id:'head', geo:'sphere', args:[0.210,40,40], pos:[0, 1.800, 0 ] },
 { id:'neck', geo:'capsule', args:[0.082,0.145,8,14], pos:[0, 1.520, 0 ] },
 { id:'chest', geo:'box', args:[0.800,0.480,0.310], pos:[0, 1.085, 0 ] },
 { id:'chest', geo:'box', args:[0.710,0.150,0.285], pos:[0, 0.800, 0 ] },
 { id:'abdomen', geo:'box', args:[0.600,0.270,0.245], pos:[0, 0.585, 0 ] },
 { id:'pelvis', geo:'box', args:[0.740,0.350,0.295], pos:[0, 0.230, 0 ] },
 { id:'left_shoulder', geo:'sphere', args:[0.158,24,24], pos:[-0.546,1.170, 0 ] },
 { id:'right_shoulder', geo:'sphere', args:[0.158,24,24], pos:[ 0.546,1.170, 0 ] },
 { id:'left_arm', geo:'capsule', args:[0.087,0.440,6,14], pos:[-0.745,0.812, 0 ], rot:[0,0, 0.130] },
 { id:'right_arm', geo:'capsule', args:[0.087,0.440,6,14], pos:[ 0.745,0.812, 0 ], rot:[0,0,-0.130] },
 { id:'left_arm', geo:'capsule', args:[0.072,0.410,6,12], pos:[-0.878,0.125, 0.010], rot:[0.04,0, 0.060] },
 { id:'right_arm', geo:'capsule', args:[0.072,0.410,6,12], pos:[ 0.878,0.125, 0.010], rot:[0.04,0,-0.060] },
 { id:'left_leg', geo:'capsule', args:[0.135,0.600,6,16], pos:[-0.210,-0.260, 0 ] },
 { id:'right_leg', geo:'capsule', args:[0.135,0.600,6,16], pos:[ 0.210,-0.260, 0 ] },
 { id:'left_lower_leg', geo:'capsule', args:[0.090,0.430,6,14], pos:[-0.210,-1.010, 0 ] },
 { id:'right_lower_leg',geo:'capsule', args:[0.090,0.430,6,14], pos:[ 0.210,-1.010, 0 ] },
 { id:'left_foot', geo:'box', args:[0.155,0.092,0.350], pos:[-0.210,-1.370,0.110] },
 { id:'right_foot', geo:'box', args:[0.155,0.092,0.350], pos:[ 0.210,-1.370,0.110] },
];

function HoloGeo({ geo, args }: { geo: GeoType; args: number[] }) {
 if (geo === 'sphere') return <sphereGeometry args={args as [number,number,number]} />;
 if (geo === 'box') return <boxGeometry args={args as [number,number,number]} />;
 if (geo === 'capsule') return <capsuleGeometry args={args as [number,number,number,number]} />;
 return null;
}

function HoloPart({ part, selected, hovered, onSelect, onHover }: {
 part: PartDef; selected: string|null; hovered: string|null;
 onSelect:(id:string)=>void; onHover:(id:string|null)=>void;
}) {
 const isSel = selected === part.id;
 const isHov = hovered === part.id && !isSel;
 return (
 <group position={part.pos} rotation={part.rot ?? [0,0,0]}>
 <mesh castShadow
 onClick={(e) => { e.stopPropagation(); onSelect(part.id); }}
 onPointerOver={(e) => { e.stopPropagation(); onHover(part.id); document.body.style.cursor='pointer'; }}
 onPointerOut={() => { onHover(null); document.body.style.cursor='default'; }}
 >
 <HoloGeo geo={part.geo} args={part.args} />
 <meshPhysicalMaterial color={isSel?'#2d8fff':isHov?'#1358c8':'#07194d'}
 emissive={isSel?'#60c8ff':isHov?'#2266ee':'#0c38b8'}
 emissiveIntensity={isSel?1.4:isHov?0.85:0.5}
 transparent opacity={isSel?0.96:isHov?0.93:0.88} roughness={0.18} metalness={0.08} />
 </mesh>
 <mesh scale={[1.058,1.058,1.058]}>
 <HoloGeo geo={part.geo} args={part.args} />
 <meshPhysicalMaterial color="#0066cc"
 emissive={isSel?'#aaddff':isHov?'#44aaff':'#0088ee'}
 emissiveIntensity={isSel?5.0:isHov?3.5:2.2}
 transparent opacity={isSel?0.72:isHov?0.58:0.42} roughness={0} side={THREE.BackSide} />
 </mesh>
 </group>
 );
}

function HoloBody({ selected, hovered, onSelect, onHover }: {
 selected:string|null; hovered:string|null;
 onSelect:(id:string)=>void; onHover:(id:string|null)=>void;
}) {
 return (
 <group>
 {PARTS.map((part, i) => (
 <HoloPart key={`${part.id}-${i}`} part={part} selected={selected} hovered={hovered} onSelect={onSelect} onHover={onHover} />
 ))}
 </group>
 );
}

// ── GLB availability check ────────────────────────────────────────────────────

function useHasGlb() {
 const [has, setHas] = useState<boolean | null>(false);
 useEffect(() => {
 let timeout: NodeJS.Timeout;
 const checkGlb = async () => {
 try {
 timeout = setTimeout(() => setHas(false), 3000);
 const res = await fetch('/models/body_male.glb', { method: 'HEAD' });
 clearTimeout(timeout);
 setHas(res.ok);
 } catch {
 clearTimeout(timeout);
 setHas(false);
 }
 };
 checkGlb();
 return () => clearTimeout(timeout);
 }, []);
 return has;
}

// ── Scene ─────────────────────────────────────────────────────────────────────

function Scene({ useGlb, selected, hovered, onSelect, onHover, xray }: {
 useGlb: boolean; selected: string|null; hovered: string|null;
 onSelect:(id:string)=>void; onHover:(id:string|null)=>void; xray: boolean;
}) {
 return (
 <>
 {useGlb ? (
 <>
 <ambientLight intensity={xray ? 0.20 : 3.0} color={xray ? '#88ccff' : '#ffffff'} />
 <directionalLight position={[3, 8, 5]} intensity={xray ? 0.5 : 3.0} color="#ffffff" castShadow />
 <directionalLight position={[-4, 4, -3]} intensity={xray ? 0.3 : 1.2} color="#ffffff" />
 <pointLight position={[0, 2, 5]} intensity={xray ? 0.0 : 2.0} color="#ffffff" />
 <pointLight position={[0, 3, -4]} intensity={xray ? 0.2 : 0.6} color="#ffffff" />
 {!xray && <Environment preset="studio" backgroundIntensity={0.1} />}
 {xray && <pointLight position={[0, 0, 2]} intensity={0.8} color="#224466" />}
 <GltfHuman selected={selected} onSelect={onSelect} onHover={onHover} xray={xray} />
 {xray && (
 <OrganLayer selected={selected} onSelect={onSelect} onHover={onHover} />
 )}
 </>
 ) : (
 <>
 <ambientLight intensity={0.12} color="#2244aa" />
 <directionalLight position={[2,6,4]} intensity={0.55} color="#4488ff" />
 <directionalLight position={[-3,4,-3]} intensity={0.25} color="#224488" />
 <pointLight position={[0,2,-5]} intensity={0.6} color="#0055cc" />
 <gridHelper args={[14,28,'#0a1e40','#06132a']} position={[0,-1.52,0]} />
 <HoloBody selected={selected} hovered={hovered} onSelect={onSelect} onHover={onHover} />
 </>
 )}
 </>
 );
}

// ── Main export ───────────────────────────────────────────────────────────────

export default function BodyViewer3D({
 selected,
 onSelect,
 xray = false,
}: {
 selected: string | null;
 onSelect: (id: string) => void;
 xray?: boolean;
}) {
 const [hovered, setHovered] = useState<string | null>(null);
 const hasGlb = useHasGlb();

 return (
 <Canvas shadows camera={{ fov: 45, near: 0.1, far: 100, position: [0, 0, 4.5] }}>
 <color attach="background" args={[xray ? '#050d18' : '#0d1117']} />
 <Suspense fallback={null}>
 <Scene
 useGlb={hasGlb === true}
 selected={selected}
 hovered={hovered}
 onSelect={onSelect}
 onHover={setHovered}
 xray={xray}
 />
 </Suspense>
 <OrbitControls enablePan panSpeed={0.8} minDistance={3} maxDistance={8}
 target={[0, 0, 0]} enableDamping dampingFactor={0.08} />
 </Canvas>
 );
}

// Preload organ models để tránh giật khi bật X-ray lần đầu
useGLTF.preload('/models/body_male.glb');
useGLTF.preload('/models/brain.glb');
useGLTF.preload('/models/heart.glb');
useGLTF.preload('/models/liver.glb');
useGLTF.preload('/models/intestines.glb');
useFBX.preload('/models/lungs.fbx');
useFBX.preload('/models/kidney.fbx');
