'use client';

import { useEffect } from 'react';
import { useWorkspaceTabs } from './WorkspaceTabsContext';

/**
 * Lắng nghe keyboard shortcuts:
 *  - ⌘/Ctrl+K        → mở Command Palette
 *  - Alt+ArrowLeft   → tab trước
 *  - Alt+ArrowRight  → tab sau
 *  - Ctrl+W          → đóng tab active
 *  - Escape          → đóng palette, menu (ưu tiên)
 */
export function useTabShortcuts() {
  const { paletteOpen, menuOpen, openPalette, closePalette, closeMenu, nextTab, prevTab, closeActiveTab, openMenu } = useWorkspaceTabs();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const isMod = e.metaKey || e.ctrlKey;
      const target = e.target as HTMLElement | null;
      const isInInput =
        target?.tagName === 'INPUT' ||
        target?.tagName === 'TEXTAREA' ||
        target?.isContentEditable;

      // Cmd/Ctrl+K — luôn hoạt động (trừ khi đang gõ trong input)
      if (isMod && (e.key === 'k' || e.key === 'K') && !e.shiftKey && !e.altKey) {
        e.preventDefault();
        if (paletteOpen) closePalette();
        else openPalette();
        return;
      }

      // Ctrl+W — đóng tab active
      if (isMod && (e.key === 'w' || e.key === 'W') && !e.shiftKey && !e.altKey) {
        e.preventDefault();
        closeActiveTab();
        return;
      }

      // Alt+Arrow — switch tab (chỉ khi không trong input để tránh đụng text editor)
      if (e.altKey && !isInInput) {
        if (e.key === 'ArrowLeft') {
          e.preventDefault();
          prevTab();
          return;
        }
        if (e.key === 'ArrowRight') {
          e.preventDefault();
          nextTab();
          return;
        }
      }

      // Escape — đóng theo thứ tự ưu tiên
      if (e.key === 'Escape') {
        if (paletteOpen) {
          e.preventDefault();
          closePalette();
        } else if (menuOpen) {
          e.preventDefault();
          closeMenu();
        }
        return;
      }

      // Phím "M" đơn lẻ — mở menu (chỉ khi không trong input)
      if (!isInInput && !isMod && !e.altKey && (e.key === 'm' || e.key === 'M')) {
        // Tránh trigger khi user đang gõ
        if (!e.shiftKey) {
          e.preventDefault();
          openMenu();
        }
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [paletteOpen, menuOpen, openPalette, closePalette, closeMenu, openMenu, nextTab, prevTab, closeActiveTab]);
}