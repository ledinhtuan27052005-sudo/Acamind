'use client';

import { useEffect, useState } from 'react';
import { AnimatePresence } from 'framer-motion';
import { WorkspaceTabsProvider, useWorkspaceTabs } from './WorkspaceTabsContext';
import { useTabShortcuts } from './useTabShortcuts';
import { NavProgressBar } from './NavProgressBar';
import { WorkspaceMenu } from './WorkspaceMenu';
import { CommandPalette } from './CommandPalette';
import { useAppStore } from '@/store/useAppStore';

interface WorkspaceShellProviderProps {
  children: React.ReactNode;
  /** Top bar element (vd <WorkspaceHeader />). Render ở mọi route trừ auth. */
  topBar?: React.ReactNode;
}

/**
 * Provider + renderer gốc: top bar + body + overlays (menu, palette, progress bar).
 */
function ShellRoot({ children, topBar }: WorkspaceShellProviderProps) {
  const { menuOpen, closeMenu, paletteOpen } = useWorkspaceTabs();
  const user = useAppStore(state => state.user);
  const canManageDocuments = user?.role === 'admin' || user?.role === 'researcher' || user?.role === 'expert';
  const [mounted, setMounted] = useState(false);

  useTabShortcuts();
  useEffect(() => setMounted(true), []);

  // Lock body scroll khi palette mở
  useEffect(() => {
    if (paletteOpen) {
      const prev = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = prev;
      };
    }
  }, [paletteOpen]);

  if (!mounted) {
    return (
      <div className="flex flex-col h-screen bg-white dark:bg-[#0A0F1E]">
        {topBar}
        <div className="flex-1 min-h-0">{children}</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-white dark:bg-[#0A0F1E] transition-colors">
      {/* Fixed header - always on top when scrolling */}
      <div className="shrink-0">
        {topBar}
      </div>
      {/* Content area with independent scroll */}
      <div className="flex-1 min-h-0 overflow-y-auto">
        {children}
      </div>

      <NavProgressBar />

      {canManageDocuments && <AnimatePresence>{menuOpen && <WorkspaceMenu key="menu" onClose={closeMenu} />}</AnimatePresence>}
      {canManageDocuments && <CommandPalette />}
    </div>
  );
}

export default function WorkspaceShellProvider(props: WorkspaceShellProviderProps) {
  return (
    <WorkspaceTabsProvider>
      <ShellRoot {...props} />
    </WorkspaceTabsProvider>
  );
}
