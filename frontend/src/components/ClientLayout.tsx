'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useEffect, useState } from 'react';
import NotificationBell from '@/components/NotificationBell';
import LanguageSelector from '@/components/LanguageSelector';
import { useRouter, usePathname } from 'next/navigation';
import { useAppStore, AuthUser } from '@/store/useAppStore';
import { useI18n } from '@/lib/i18n/context';
import { User as UserIcon, LogOut, LayoutDashboard } from 'lucide-react';
import {
  WorkspaceShellProvider,
  WorkspaceHeader,
  WorkspaceBody,
} from '@/components/WorkspaceShell';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function resolveAvatar(url: string | null | undefined): string | null {
  if (!url) return null;
  if (url.startsWith('http')) return url;
  return `${API_URL}${url}`;
}

const AVATAR_COLORS = [
  '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b',
  '#10b981', '#06b6d4', '#ef4444', '#84cc16',
];

function getAvatarColor(name: string) {
  const code = name.charCodeAt(0) + (name.charCodeAt(1) || 0);
  return AVATAR_COLORS[code % AVATAR_COLORS.length];
}

function getInitials(user: AuthUser) {
  if (user.full_name) {
    const parts = user.full_name.trim().split(/\s+/);
    if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    return parts[0].slice(0, 2).toUpperCase();
  }
  return user.email.slice(0, 2).toUpperCase();
}

// ── Avatar with dropdown ───────────────────────────────────────────────────────

export function UserAvatar({ user, onLogout }: { user: AuthUser; onLogout: () => void }) {
  const [open, setOpen] = useState(false);
  const { t } = useI18n();
  const inis = getInitials(user);
  const bgColor = getAvatarColor(user.full_name || user.email);
  const avatarSrc = resolveAvatar((user as AuthUser & { avatar_url?: string | null }).avatar_url);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('[data-user-avatar-root]')) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const AvatarCircle = ({ size }: { size: 'sm' | 'md' }) => {
    const dim = size === 'sm' ? 'w-8 h-8 text-xs' : 'w-10 h-10 text-sm';
    return avatarSrc ? (
      <img
        src={avatarSrc}
        alt={user.full_name || user.email}
        className={`${dim} rounded-full object-cover shadow shrink-0`}
      />
    ) : (
      <div
        className={`${dim} rounded-full flex items-center justify-center text-white font-bold shadow shrink-0`}
        style={{ backgroundColor: bgColor }}
      >
        {inis}
      </div>
    );
  };

  return (
    <div className="relative" data-user-avatar-root>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 focus:outline-none group"
        title={user.full_name || user.email}
      >
        <AvatarCircle size="sm" />
        <svg
          className={`w-3 h-3 text-slate-400 dark:text-slate-500 transition-transform duration-200 ${open ? 'rotate-90' : ''}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div
          className="absolute right-0 top-full mt-2 w-56 rounded-2xl overflow-hidden z-50"
          style={{
            background: 'var(--glass-bg-strong)',
            backdropFilter: 'blur(20px)',
            border: '1px solid var(--border-solid, #E2E8F0)',
            boxShadow: '0 20px 60px rgba(0,0,0,0.12), 0 8px 24px rgba(59,130,246,0.08)',
          }}
        >
          <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800 flex items-center gap-3">
            <AvatarCircle size="md" />
            <div className="min-w-0">
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate">
                {user.full_name || 'User'}
              </p>
              <p className="text-xs text-slate-400 dark:text-slate-500 truncate">{user.email}</p>
            </div>
          </div>
          <div className="py-1">
            {user.role === 'admin' && (
              <Link
                href="/dashboard"
                onClick={() => setOpen(false)}
                className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-colors"
              >
                <LayoutDashboard className="w-4 h-4" /> Dashboard
              </Link>
            )}
            <Link
              href="/profile"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-colors"
            >
              <UserIcon className="w-4 h-4" /> Personal Profile
            </Link>
          </div>
          <div className="border-t border-slate-100 dark:border-slate-800 py-1">
            <button
              onClick={() => { setOpen(false); onLogout(); }}
              className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            >
              <LogOut className="w-4 h-4" /> {t.nav.logout}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main layout ────────────────────────────────────────────────────────────────

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const { user, logout, initAuth } = useAppStore();
  const { t } = useI18n();
  const [mounted, setMounted] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  const isAuthPage = pathname === '/login' || pathname === '/register';
  // Top bar CHUNG cho mọi route (kể cả landing), trừ auth pages.
  // KHÔNG gate bằng `mounted` để top bar render ngay trong SSR HTML (good for first paint).
  const showWorkspaceHeader = !isAuthPage;

  useEffect(() => {
    initAuth();
    setMounted(true);
  }, [initAuth]);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  // Auth pages (login/register) không cần workspace shell — render bare children.
  if (isAuthPage) {
    return <>{children}</>;
  }

  return (
    <WorkspaceShellProvider
      topBar={showWorkspaceHeader ? <WorkspaceHeader onLogout={handleLogout} /> : null}
    >
      <WorkspaceBody>{children}</WorkspaceBody>
    </WorkspaceShellProvider>
  );
}