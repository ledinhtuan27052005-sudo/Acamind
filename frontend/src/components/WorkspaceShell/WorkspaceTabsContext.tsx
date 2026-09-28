'use client';

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { TAB_ROUTES, TAB_ROUTES_MAP, MAX_TABS, MAX_RECENT, resolveHref, type TabRoute } from './registry';

const RECENT_KEY = 'workspace.recent';
const TABS_KEY = 'workspace.tabs';
const ACTIVE_KEY = 'workspace.active';

interface WorkspaceTabsContextValue {
  // Tabs
  tabs: TabRoute[];
  activeHref: string | null;
  activeRoute: TabRoute | null;
  openTab: (href: string) => void;
  closeTab: (href: string) => void;
  switchTab: (href: string) => void;
  nextTab: () => void;
  prevTab: () => void;
  closeActiveTab: () => void;
  clearActiveTab: () => void;

  // Menu
  menuOpen: boolean;
  openMenu: () => void;
  closeMenu: () => void;
  toggleMenu: () => void;

  // Command palette
  paletteOpen: boolean;
  openPalette: () => void;
  closePalette: () => void;

  // Recently opened
  recentlyOpened: string[];

  // Loading indicator (for nav progress bar)
  loadingHref: string | null;
}

const WorkspaceTabsContext = createContext<WorkspaceTabsContextValue | null>(null);

export function useWorkspaceTabs(): WorkspaceTabsContextValue {
  const ctx = useContext(WorkspaceTabsContext);
  if (!ctx) throw new Error('useWorkspaceTabs must be used within WorkspaceShellProvider');
  return ctx;
}

// ── Helpers ────────────────────────────────────────────────────────────────

function loadFromStorage<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback;
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function saveToStorage<T>(key: string, value: T) {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* ignore */
  }
}

// ── Provider ────────────────────────────────────────────────────────────────

export function WorkspaceTabsProvider({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);

  const [tabs, setTabs] = useState<TabRoute[]>([]);
  const [activeHref, setActiveHref] = useState<string | null>(null);
  const [recentlyOpened, setRecentlyOpened] = useState<string[]>([]);
  const [menuOpen, setMenuOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [loadingHref, setLoadingHref] = useState<string | null>(null);

  // Hydrate từ localStorage sau mount (tránh hydration mismatch)
  // Delete tabs cũ nếu version key không khớp hoặc có vấn đề
  useEffect(() => {
    // Clear tabs cũ - reset về trạng thái sạch
    setTabs([]);
    setActiveHref(null);
    setRecentlyOpened([]);

    // Delete luôn localStorage để không còn tabs cũ
    localStorage.removeItem(TABS_KEY);
    localStorage.removeItem(RECENT_KEY);
    localStorage.removeItem(ACTIVE_KEY);

    setMounted(true);
  }, []);

  // Persist
  useEffect(() => {
    if (!mounted) return;
    saveToStorage(TABS_KEY, tabs.map((t) => t.href));
  }, [tabs, mounted]);

  useEffect(() => {
    if (!mounted) return;
    saveToStorage(ACTIVE_KEY, activeHref);
  }, [activeHref, mounted]);

  useEffect(() => {
    if (!mounted) return;
    saveToStorage(RECENT_KEY, recentlyOpened);
  }, [recentlyOpened, mounted]);

  // Lookup active route
  const activeRoute = useMemo<TabRoute | null>(() => {
    if (!activeHref) return null;
    return TAB_ROUTES_MAP[resolveHref(activeHref)] ?? null;
  }, [activeHref]);

  // Mark loading state khi chuyển tab (auto-clear sau 800ms fallback)
  useEffect(() => {
    if (!activeHref) {
      setLoadingHref(null);
      return;
    }
    setLoadingHref(activeHref);
    const t = setTimeout(() => setLoadingHref(null), 700);
    return () => clearTimeout(t);
  }, [activeHref]);

  // ── Actions ──────────────────────────────────────────────────────────────

  const pushRecent = useCallback((href: string) => {
    const normalized = resolveHref(href);
    setRecentlyOpened((prev) => {
      const next = [normalized, ...prev.filter((h) => h !== normalized)].slice(0, MAX_RECENT);
      return next;
    });
  }, []);

  const openTab = useCallback(
    (href: string) => {
      const normalized = resolveHref(href);
      const route = TAB_ROUTES_MAP[normalized];
      if (!route) return; // not in registry → skip

      setTabs((prev) => {
        if (prev.some((t) => t.href === normalized)) return prev;
        // Add tab mới, nếu vượt MAX_TABS thì đóng tab cũ nhất (LRU)
        const next = [...prev, route];
        if (next.length > MAX_TABS) {
          return next.slice(next.length - MAX_TABS);
        }
        return next;
      });
      setActiveHref(normalized);
      pushRecent(normalized);
    },
    [pushRecent]
  );

  const closeTab = useCallback(
    (href: string) => {
      const normalized = resolveHref(href);
      setTabs((prev) => {
        const idx = prev.findIndex((t) => t.href === normalized);
        if (idx === -1) return prev;
        const next = prev.filter((_, i) => i !== idx);
        // Nếu đang đóng tab active → switch sang tab kề
        setActiveHref((cur) => {
          if (cur !== normalized) return cur;
          if (next.length === 0) return null;
          const fallbackIdx = Math.min(idx, next.length - 1);
          return next[fallbackIdx].href;
        });
        return next;
      });
    },
    []
  );

  const switchTab = useCallback((href: string) => {
    const normalized = resolveHref(href);
    if (!TAB_ROUTES_MAP[normalized]) return;
    setActiveHref(normalized);
    pushRecent(normalized);
  }, [pushRecent]);

  const nextTab = useCallback(() => {
    setActiveHref((cur) => {
      if (!cur || tabs.length === 0) return cur;
      const idx = tabs.findIndex((t) => t.href === cur);
      return tabs[(idx + 1) % tabs.length].href;
    });
  }, [tabs]);

  const prevTab = useCallback(() => {
    setActiveHref((cur) => {
      if (!cur || tabs.length === 0) return cur;
      const idx = tabs.findIndex((t) => t.href === cur);
      return tabs[(idx - 1 + tabs.length) % tabs.length].href;
    });
  }, [tabs]);

  const closeActiveTab = useCallback(() => {
    if (activeHref) closeTab(activeHref);
  }, [activeHref, closeTab]);

  // Clear active tab (không đóng tab khỏi danh sách, chỉ bỏ highlight).
  // Dùng khi navigate tới standalone route để WorkspaceBody render children route.
  const clearActiveTab = useCallback(() => {
    setActiveHref(null);
  }, []);

  // ── Menu ────────────────────────────────────────────────────────────────
  const openMenu = useCallback(() => setMenuOpen(true), []);
  const closeMenu = useCallback(() => setMenuOpen(false), []);
  const toggleMenu = useCallback(() => setMenuOpen((o) => !o), []);

  // ── Palette ──────────────────────────────────────────────────────────────
  const openPalette = useCallback(() => setPaletteOpen(true), []);
  const closePalette = useCallback(() => setPaletteOpen(false), []);

  const value = useMemo<WorkspaceTabsContextValue>(
    () => ({
      tabs,
      activeHref,
      activeRoute,
      openTab,
      closeTab,
      switchTab,
      nextTab,
      prevTab,
      closeActiveTab,
      clearActiveTab,
      menuOpen,
      openMenu,
      closeMenu,
      toggleMenu,
      paletteOpen,
      openPalette,
      closePalette,
      recentlyOpened,
      loadingHref,
    }),
    [
      tabs,
      activeHref,
      activeRoute,
      openTab,
      closeTab,
      switchTab,
      nextTab,
      prevTab,
      closeActiveTab,
      clearActiveTab,
      menuOpen,
      openMenu,
      closeMenu,
      toggleMenu,
      paletteOpen,
      openPalette,
      closePalette,
      recentlyOpened,
      loadingHref,
    ]
  );

  return <WorkspaceTabsContext.Provider value={value}>{children}</WorkspaceTabsContext.Provider>;
}

// ── Hook chỉ dùng nội bộ ────────────────────────────────────────────────────
export function useTabRoute(href: string | null): TabRoute | null {
  return useMemo(() => {
    if (!href) return null;
    return TAB_ROUTES_MAP[resolveHref(href)] ?? null;
  }, [href]);
}

// Re-export for convenience
export { TAB_ROUTES, TAB_ROUTES_MAP };