'use client';

import dynamic from 'next/dynamic';
import { FileText, Upload, MessageSquare, ShieldCheck, UserCircle } from 'lucide-react';
import type { ComponentType } from 'react';
import type { LucideIcon } from 'lucide-react';

export interface TabRoute {
  href: string;
  title: string;
  icon: LucideIcon;
  Component: ComponentType;
}

const LEGACY_FEATURE_PATHS = new Set([
  '/timeline', '/translate', '/Terminology', '/graph', '/Trend',
  '/literature/review', '/Quiz', '/Slide', '/study', '/Health', '/3d', '/Critique', '/RAG',
  '/debate', '/trends', '/authors', '/analysis',
]);

const SUB_ROUTE_FALLBACK: Record<string, string> = {
  '/admin/permissions': '/admin',
  '/admin/plans': '/admin',
  '/settings': '/profile',
  '/researcher-apply': '/profile',
  '/org': '/library',
  '/pricing': '/chat',
};

export function resolveHref(href: string): string {
  const clean = href.split('?')[0].split('#')[0];
  return LEGACY_FEATURE_PATHS.has(clean) ? '/chat' : SUB_ROUTE_FALLBACK[clean] ?? clean;
}

export const TAB_ROUTES: TabRoute[] = [
  { href: '/Literature', title: 'Đối chiếu nghiên cứu', icon: FileText,
    Component: dynamic(() => import('@/app/Literature/page'), { ssr: false, loading: () => null }) },
  { href: '/upload', title: 'Upload Documents', icon: Upload,
    Component: dynamic(() => import('@/app/upload/page'), { ssr: false, loading: () => null }) },
  { href: '/library', title: 'Document Library', icon: FileText,
    Component: dynamic(() => import('@/app/library/page'), { ssr: false, loading: () => null }) },
  { href: '/chat', title: 'Research Chatbot', icon: MessageSquare,
    Component: dynamic(() => import('@/app/chat/page'), { ssr: false, loading: () => null }) },
  { href: '/profile', title: 'Profile', icon: UserCircle,
    Component: dynamic(() => import('@/app/profile/page'), { ssr: false, loading: () => null }) },
  { href: '/admin', title: 'Admin', icon: ShieldCheck,
    Component: dynamic(() => import('@/app/admin/page'), { ssr: false, loading: () => null }) },
];

export const TAB_ROUTES_MAP: Record<string, TabRoute> = Object.fromEntries(
  TAB_ROUTES.map((route) => [route.href, route])
);

export const MAX_TABS = 5;
export const MAX_RECENT = 5;
