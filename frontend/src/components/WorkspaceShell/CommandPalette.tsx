'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search } from 'lucide-react';
import { NAV_GROUPS, type NavItem, type UserRole } from '@/components/Sidebar/navConfig';
import { useAppStore } from '@/store/useAppStore';
import { useWorkspaceTabs } from './WorkspaceTabsContext';
import { resolveHref } from './registry';

interface PaletteItem {
  href: string;
  label: string;
  description: string;
  icon: NavItem['icon'];
  groupLabel: string;
}

/**
 * Command palette overlay (Cmd+K / Ctrl+K). Fuzzy search + role filter.
 */
export function CommandPalette() {
  const { paletteOpen, closePalette, openTab } = useWorkspaceTabs();
  const { user } = useAppStore();
  const [query, setQuery] = useState('');
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Role normalization
  const role: UserRole | undefined = useMemo(() => {
    if (!user) return undefined;
    const r = (user.role as string) ?? 'student';
    return r === 'user' ? 'student' : (r as UserRole);
  }, [user]);

  // Flatten to items (sau role filter)
  const allItems = useMemo<PaletteItem[]>(() => {
    return NAV_GROUPS.flatMap((group) =>
      group.items
        .filter((item: NavItem) => {
          if (item.disabled) return false;
          if (item.roles && (!role || !item.roles.includes(role))) return false;
          return true;
        })
        .map((item) => ({
          href: item.href,
          label: item.label,
          description: item.description,
          icon: item.icon,
          groupLabel: group.groupLabel,
        }))
    );
  }, [role]);

  // Filter theo query (fuzzy)
  const filteredItems = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return allItems;
    return allItems.filter(
      (item) =>
        item.label.toLowerCase().includes(q) ||
        item.description.toLowerCase().includes(q) ||
        item.groupLabel.toLowerCase().includes(q)
    );
  }, [query, allItems]);

  // Auto-focus input khi mở + reset state
  useEffect(() => {
    if (paletteOpen) {
      setQuery('');
      setSelectedIdx(0);
      // Focus sau khi animation start
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [paletteOpen]);

  // Reset selectedIdx khi filter thay đổi
  useEffect(() => {
    setSelectedIdx(0);
  }, [query]);

  // Keyboard navigation
  useEffect(() => {
    if (!paletteOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIdx((i) => Math.min(i + 1, filteredItems.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIdx((i) => Math.max(i - 1, 0));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        const item = filteredItems[selectedIdx];
        if (item) {
          openTab(resolveHref(item.href));
          closePalette();
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        closePalette();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [paletteOpen, filteredItems, selectedIdx, openTab, closePalette]);

  if (!paletteOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.15 }}
        className="fixed inset-0 z-[150] flex items-start justify-center pt-[15vh] px-4"
        onClick={closePalette}
      >
        <div className="absolute inset-0 bg-black/40 backdrop-blur-[3px]" />

        <motion.div
          initial={{ opacity: 0, y: -12, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -8, scale: 0.96 }}
          transition={{ duration: 0.18, ease: [0.32, 0.72, 0, 1] }}
          onClick={(e) => e.stopPropagation()}
          className="relative w-full max-w-[600px] rounded-2xl overflow-hidden shadow-2xl"
          style={{
            background: 'var(--glass-bg-strong)',
            backdropFilter: 'blur(24px) saturate(180%)',
            WebkitBackdropFilter: 'blur(24px) saturate(180%)',
            border: '1px solid var(--border-solid, #E2E8F0)',
          }}
        >
          {/* Search input */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-200/50 dark:border-slate-800/50">
            <Search className="w-4 h-4 text-slate-400 shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search features or type a command..."
              className="flex-1 bg-transparent text-sm text-slate-700 dark:text-slate-200 placeholder:text-slate-400 focus:outline-none"
            />
            <kbd className="hidden sm:inline-block px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-200/70 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400">
              ESC
            </kbd>
          </div>

          {/* Results */}
          <div className="max-h-[50vh] overflow-y-auto py-2 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
            {filteredItems.length === 0 ? (
              <p className="text-center text-xs text-slate-400 dark:text-slate-500 py-10">
                No results found
              </p>
            ) : (
              filteredItems.map((item, idx) => {
                const active = idx === selectedIdx;
                const Icon = item.icon;
                return (
                  <button
                    key={item.href}
                    onMouseEnter={() => setSelectedIdx(idx)}
                    onClick={() => {
                      openTab(resolveHref(item.href));
                      closePalette();
                    }}
                    className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors ${
                      active
                        ? 'bg-teal-500/10 text-teal-700 dark:text-teal-300'
                        : 'text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/40'
                    }`}
                  >
                    <Icon className={`w-4 h-4 shrink-0 ${active ? 'text-teal-600 dark:text-teal-400' : 'text-slate-500 dark:text-slate-400'}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-medium truncate">{item.label}</span>
                      </div>
                      <p className="text-[11px] text-slate-400 dark:text-slate-500 truncate">
                        {item.groupLabel} · {item.description}
                      </p>
                    </div>
                    {active && (
                      <kbd className="hidden sm:inline-block px-1.5 py-0.5 rounded text-[10px] font-mono bg-teal-500/20 text-teal-700 dark:text-teal-300">
                        ↵
                      </kbd>
                    )}
                  </button>
                );
              })
            )}
          </div>

          {/* Footer hint */}
          <div className="flex items-center gap-3 px-4 py-2 border-t border-slate-200/50 dark:border-slate-800/50 text-[10px] text-slate-400 dark:text-slate-500">
            <span className="flex items-center gap-1">
              <kbd className="px-1 py-0.5 rounded bg-slate-200/70 dark:bg-slate-800/60 font-mono">↑</kbd>
              <kbd className="px-1 py-0.5 rounded bg-slate-200/70 dark:bg-slate-800/60 font-mono">↓</kbd>
              navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1 py-0.5 rounded bg-slate-200/70 dark:bg-slate-800/60 font-mono">↵</kbd>
              open
            </span>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}