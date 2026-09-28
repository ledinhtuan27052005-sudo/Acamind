'use client';

import dynamic from 'next/dynamic';
import {
  FileText,
  Upload,
  Timer,
  MessageSquare,
  Languages,
  BookOpen,
  Network,
  TrendingUp,
  Microscope,
  ClipboardList,
  Presentation,
  GraduationCap,
  Scan,
  FlaskConical,
  ShieldCheck,
  Users,
  UserCircle,
  BarChart3,
  Zap,
  Stethoscope,
  Brain,
} from 'lucide-react';
import type { ComponentType } from 'react';
import type { LucideIcon } from 'lucide-react';

export interface TabRoute {
  href: string;
  title: string;
  icon: LucideIcon;
  /** Dynamic-loaded component. Mount trực tiếp. */
  Component: ComponentType;
}

/**
 * Sub-route fallback map
 */
const SUB_ROUTE_FALLBACK: Record<string, string> = {
  '/admin/permissions': '/admin',
  '/admin/plans': '/admin',
  '/settings': '/profile',
  '/researcher-apply': '/profile',
  '/org': '/library',
  '/pricing': '/chat',
  '/literature': '/Literature',
  '/literature/review': '/Literature',
};

export function resolveHref(href: string): string {
  const clean = href.split('?')[0].split('#')[0];
  return SUB_ROUTE_FALLBACK[clean] ?? clean;
}

/**
 * Sign up tất cả tab workspace
 */
export const TAB_ROUTES: TabRoute[] = [
  // Upload & Library
  { href: '/upload', title: 'Upload Documents', icon: Upload,
    Component: dynamic(() => import('@/app/upload/page'), { ssr: false, loading: () => null }) },
  { href: '/library', title: 'Article Library', icon: FileText,
    Component: dynamic(() => import('@/app/library/page'), { ssr: false, loading: () => null }) },
  { href: '/timeline', title: 'Timeline', icon: Timer,
    Component: dynamic(() => import('@/app/timeline/page'), { ssr: false, loading: () => null }) },

  // Chat & Translate
  { href: '/chat', title: 'Chat Q&A', icon: MessageSquare,
    Component: dynamic(() => import('@/app/chat/page'), { ssr: false, loading: () => null }) },
  { href: '/translate', title: 'Translate Document', icon: Languages,
    Component: dynamic(() => import('@/app/translate/page'), { ssr: false, loading: () => null }) },
  { href: '/Terminology', title: 'Psychology Terminology', icon: BookOpen,
    Component: dynamic(() => import('@/app/Terminology/page'), { ssr: false, loading: () => null }) },

  // Research
  { href: '/graph', title: 'Knowledge Graph', icon: Network,
    Component: dynamic(() => import('@/app/graph/page'), { ssr: false, loading: () => null }) },
  { href: '/Trend', title: 'Research Trends', icon: TrendingUp,
    Component: dynamic(() => import('@/app/Trend/page'), { ssr: false, loading: () => null }) },
  { href: '/Literature', title: 'Literature Review', icon: Microscope,
    Component: dynamic(() => import('@/app/Literature/page'), { ssr: false, loading: () => null }) },

  // Learning
  { href: '/Quiz', title: 'Quiz', icon: ClipboardList,
    Component: dynamic(() => import('@/app/Quiz/page'), { ssr: false, loading: () => null }) },
  { href: '/Slide', title: 'AI Slide', icon: Presentation,
    Component: dynamic(() => import('@/app/Slide/page'), { ssr: false, loading: () => null }) },
  { href: '/study', title: 'Learning Mode', icon: GraduationCap,
    Component: dynamic(() => import('@/app/study/page'), { ssr: false, loading: () => null }) },

  // Psychology
  { href: '/Health', title: 'Health Profile', icon: Stethoscope,
    Component: dynamic(() => import('@/app/Health/page'), { ssr: false, loading: () => null }) },
  { href: '/3d', title: '3D Atlas', icon: Scan,
    Component: dynamic(() => import('@/app/3d/page'), { ssr: false, loading: () => null }) },
  { href: '/Critique', title: 'AI Critique', icon: Zap,
    Component: dynamic(() => import('@/app/Critique/page'), { ssr: false, loading: () => null }) },

  // Evaluation
  { href: '/RAG', title: 'RAG Evaluation', icon: FlaskConical,
    Component: dynamic(() => import('@/app/RAG/page'), { ssr: false, loading: () => null }) },

  // Account
  { href: '/profile', title: 'Profile', icon: UserCircle,
    Component: dynamic(() => import('@/app/profile/page'), { ssr: false, loading: () => null }) },
  { href: '/admin', title: 'Admin', icon: ShieldCheck,
    Component: dynamic(() => import('@/app/admin/page'), { ssr: false, loading: () => null }) },
];

export const TAB_ROUTES_MAP: Record<string, TabRoute> = Object.fromEntries(
  TAB_ROUTES.map((r) => [r.href, r])
);

export const MAX_TABS = 8;
export const MAX_RECENT = 5;
