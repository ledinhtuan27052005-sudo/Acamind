'use client';

import Link from 'next/link';
import Image from 'next/image';
import { Menu, Sun, Moon, Command } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { useI18n } from '@/lib/i18n/context';

import NotificationBell from '@/components/NotificationBell';
import LanguageSelector from '@/components/LanguageSelector';
import { UserAvatar } from '@/components/ClientLayout';
import { useWorkspaceTabs } from './WorkspaceTabsContext';
import { WorkspaceTabBar } from './WorkspaceTabBar';

interface WorkspaceHeaderProps {
  onLogout: () => void;
}

/**
 * Top bar (1 dòng, cao 56px): hamburger | logo | tab pills | ⌘K | theme | lang | auth.
 */
export function WorkspaceHeader({ onLogout }: WorkspaceHeaderProps) {
  const { user, darkMode, toggleDarkMode } = useAppStore();
  const { t } = useI18n();
  const { toggleMenu, openPalette, menuOpen } = useWorkspaceTabs();

  return (
    <header
      className="sticky top-0 z-30 h-14 flex items-center gap-2 md:gap-3 px-3 md:px-4 w-full"
      style={{
        background: 'var(--glass-bg-strong)',
        backdropFilter: 'blur(20px) saturate(180%)',
        WebkitBackdropFilter: 'blur(20px) saturate(180%)',
        borderBottom: '1px solid var(--border-solid, #E2E8F0)',
        boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
      }}
    >
      {/* Hamburger */}
      <button
        onClick={toggleMenu}
        data-hamburger-button
        className={`shrink-0 w-9 h-9 md:w-10 md:h-10 flex items-center justify-center rounded-lg transition-colors ${
          menuOpen
            ? 'bg-teal-500/15 text-teal-700 dark:text-teal-300'
            : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/60'
        }`}
        aria-label={menuOpen ? 'Close features menu' : 'Open features menu'}
        title={menuOpen ? 'Close menu' : 'Open menu (M)'}
        aria-expanded={menuOpen}
      >
        <Menu className="w-[18px] h-[18px]" />
      </button>

      {/* Logo */}
      <Link href="/" className="flex items-center gap-2 shrink-0 mr-1">
        <div className="relative w-7 h-7 rounded-md overflow-hidden border border-teal-500/30">
          <Image src="/Logo.jpeg" alt="Acamind" fill className="object-cover" sizes="28px" />
        </div>
        <span className="hidden md:flex font-bold text-[#002D72] dark:text-white text-sm tracking-tight items-center gap-1">
          ACAMIND
          <span className="text-[9px] bg-teal-500/10 text-teal-600 dark:text-teal-400 dark:bg-teal-500/20 px-1 py-0.5 rounded font-mono font-semibold">
            AI
          </span>
        </span>
      </Link>

      {/* Tab pills (flex-1, scroll ngang) */}
      <div className="flex-1 min-w-0 flex items-center">
        <WorkspaceTabBar />
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-1 shrink-0">
        {/* Command palette button */}
        <button
          onClick={openPalette}
          className="w-9 h-9 flex items-center justify-center rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
          aria-label="Open Command Palette"
          title="Command Palette (⌘K)"
        >
          <Command className="w-[16px] h-[16px]" />
        </button>

        <button
          onClick={toggleDarkMode}
          className="w-9 h-9 flex items-center justify-center rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-[#1E88E5] dark:hover:text-[#64B5F6] transition-all"
          title={darkMode ? 'Light Mode' : 'Dark Mode'}
        >
          {darkMode ? <Sun className="w-[16px] h-[16px]" /> : <Moon className="w-[16px] h-[16px]" />}
        </button>

        <LanguageSelector />

        {user && <NotificationBell />}

        <div className="w-px h-5 bg-slate-200 dark:bg-slate-700 mx-0.5" />

        {user ? (
          <UserAvatar user={user} onLogout={onLogout} />
        ) : (
          <div className="flex items-center gap-1.5">
            <Link
              href="/login"
              className="text-xs text-slate-600 dark:text-slate-300 hover:text-[#1E88E5] px-2.5 py-1.5 rounded-lg transition-colors font-medium"
            >
              {t.auth.login}
            </Link>
            <Link
              href="/register"
              className="text-xs bg-[#002D72] hover:bg-[#1E88E5] text-white px-2.5 py-1.5 rounded-lg font-medium transition-colors shadow-sm"
            >
              {t.auth.register}
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}