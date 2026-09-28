'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  Search, X, Sparkles,
  BookMarked, MessageCircle, LineChart, GraduationCap,
  Brain, FlaskConical, ShieldCheck, UserCircle, LayoutGrid,
  type LucideIcon,
} from 'lucide-react';
import { NAV_GROUPS, type NavItem, type UserRole } from '@/components/Sidebar/navConfig';
import { useAppStore } from '@/store/useAppStore';
import { useWorkspaceTabs } from './WorkspaceTabsContext';
import { TAB_ROUTES_MAP, resolveHref } from './registry';

// Các route có page riêng (không qua workspace tab) — bấm sẽ navigate trực tiếp.
const STANDALONE_ROUTES = new Set<string>([
  '/library/upload',
  '/chat/history',
  '/quiz/document',
  '/quiz/medical',
  '/quiz/onboarding',
  '/admin/permissions',
  '/admin/plans',
  '/thu-vien',
  '/psychology',
  '/settings',
  '/researcher-apply',
  '/org',
  '/pricing',
]);

interface WorkspaceMenuProps {
  onClose: () => void;
}

/**
 * Dropdown menu thả xuống dưới nút ☰ trong top bar.
 * - Anchor cố định: top-[60px] left-12px (mobile / sm+)
 * - Click outside / Esc → đóng
 * - Click hamburger lần 2 → toggle đóng (qua WorkspaceHeader)
 * - Scroll mượt với custom scrollbar
 */
export function WorkspaceMenu({ onClose }: WorkspaceMenuProps) {
  const { user } = useAppStore();
  const { openTab, clearActiveTab } = useWorkspaceTabs();
  const router = useRouter();
  const [query, setQuery] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  // ── Role normalization ────────────────────────────────────────────────────
  const role: UserRole | undefined = useMemo(() => {
    if (!user) return undefined;
    const r = (user.role as string) ?? 'student';
    return r === 'user' ? 'student' : (r as UserRole);
  }, [user]);

  // ── Filter groups theo search + role ─────────────────────────────────────
  const filteredGroups = useMemo(() => {
    const q = query.trim().toLowerCase();
    return NAV_GROUPS.map((group) => {
      const items = group.items.filter((item: NavItem) => {
        if (item.disabled) return false;
        if (item.roles && (!role || !item.roles.includes(role))) return false;
        if (!q) return true;
        return (
          item.label.toLowerCase().includes(q) ||
          item.description.toLowerCase().includes(q) ||
          group.groupLabel.toLowerCase().includes(q)
        );
      });
      return { ...group, items };
    }).filter((g) => g.items.length > 0);
  }, [query, role]);

  const recentItems = useMemo(() => {
    return [];
  }, []);

  const handleSelect = (href: string) => {
    onClose();
    // Luôn navigate trực tiếp đến page
    clearActiveTab();
    router.push(href);
  };

  // ── Click outside → đóng (trừ chính nút ☰) ──────────────────────────────
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (containerRef.current && containerRef.current.contains(target)) return;
      const hamburger = target.closest('[data-hamburger-button]');
      if (hamburger) return;
      onClose();
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [onClose]);

  // ── Esc → đóng ───────────────────────────────────────────────────────────
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  const totalItems = filteredGroups.reduce((sum, g) => sum + g.items.length, 0);

  return (
    <motion.div
      ref={containerRef}
      initial={{ opacity: 0, scale: 0.96, y: -4 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.96, y: -4 }}
      transition={{ duration: 0.15, ease: [0.32, 0.72, 0, 1] }}
      style={{ transformOrigin: 'top left' }}
      className="fixed top-[60px] left-3 right-3 sm:left-3 sm:right-auto sm:w-[440px] z-[90] rounded-2xl overflow-hidden shadow-2xl ring-1 ring-slate-200/70 dark:ring-slate-700/60"
      data-workspace-menu
      role="menu"
      aria-label="Features menu"
    >
      <div
        className="flex flex-col max-h-[min(75vh,720px)] bg-white/95 dark:bg-slate-900/95 backdrop-blur-2xl backdrop-saturate-150"
      >
        {/* ── Header ────────────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between px-4 pt-3 pb-2 shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-teal-500 to-emerald-500 flex items-center justify-center shadow-sm">
              <Sparkles className="w-3.5 h-3.5 text-white" />
            </div>
            <div>
              <p className="text-[13px] font-semibold text-slate-800 dark:text-slate-100 leading-tight">
                Features
              </p>
              <p className="text-[10px] text-slate-400 dark:text-slate-500 leading-tight">
                {totalItems} features available
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center rounded-lg text-slate-400 dark:text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
            aria-label="Close menu (Esc)"
            title="Close (Esc)"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* ── Search ────────────────────────────────────────────────────────── */}
        <div className="px-4 pb-3 shrink-0">
          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 dark:text-slate-500 pointer-events-none transition-colors group-focus-within:text-teal-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search features..."
              className="w-full pl-9 pr-3 py-2 text-[13px] bg-slate-100/80 dark:bg-slate-800/60 border border-transparent focus:border-teal-500/60 focus:bg-white dark:focus:bg-slate-800 rounded-xl focus:outline-none placeholder:text-slate-400 dark:placeholder:text-slate-500 text-slate-700 dark:text-slate-200 transition-all"
              autoFocus
            />
          </div>
        </div>

        {/* ── Content (scrollable) ──────────────────────────────────────────── */}
        <div className="flex-1 min-h-0 overflow-y-auto px-2 pb-2 ws-scroll">
          {filteredGroups.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
              <div className="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-3">
                <Search className="w-5 h-5 text-slate-400" />
              </div>
              <p className="text-[13px] font-medium text-slate-600 dark:text-slate-300">
                No results found
              </p>
              <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
                No features match "{query}"
              </p>
            </div>
          ) : (
            filteredGroups.map((group, gIdx) => (
                <div key={group.groupKey} className={gIdx === 0 ? '' : 'mt-3'}>
                  <SectionLabel icon={groupItemsIcon(group.groupKey)}>
                    {group.groupLabel}
                  </SectionLabel>
                  <div className="space-y-0.5 mt-1">
                    {group.items.map((item: NavItem) => (
                      <MenuItem
                        key={item.href}
                        icon={item.icon}
                        label={item.label}
                        description={item.description}
                        badge={item.isNew ? 'NEW' : undefined}
                        href={item.href}
                        onClick={() => handleSelect(item.href)}
                      />
                    ))}
                  </div>
                </div>
              ))
          )}
        </div>
      </div>
    </motion.div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────

function SectionLabel({ children, icon: Icon }: { children: React.ReactNode; icon: LucideIcon }) {
  return (
    <div className="flex items-center gap-1.5 px-3 pt-1.5 pb-1">
      <Icon className="w-3 h-3 text-slate-400 dark:text-slate-500" />
      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
        {children}
      </span>
    </div>
  );
}

interface MenuItemProps {
  icon: LucideIcon;
  label: string;
  description?: string;
  badge?: string;
  href: string;
  onClick: () => void;
}

function MenuItem({ icon: Icon, label, description, badge, onClick }: MenuItemProps) {
  return (
    <button
      onClick={onClick}
      role="menuitem"
      className="group w-full flex items-center gap-3 px-3 py-2 rounded-xl text-left transition-all duration-150 hover:bg-gradient-to-r hover:from-teal-50 hover:to-emerald-50/50 dark:hover:from-teal-500/10 dark:hover:to-emerald-500/5 hover:shadow-sm"
    >
      {/* Icon with light background */}
      <div className="shrink-0 w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800/80 group-hover:bg-white dark:group-hover:bg-slate-800 group-hover:scale-105 flex items-center justify-center transition-all duration-150 shadow-sm">
        <Icon className="w-4 h-4 text-slate-600 dark:text-slate-300 group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors" />
      </div>

      {/* Label + description */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-[13px] font-medium text-slate-700 dark:text-slate-200 group-hover:text-teal-700 dark:group-hover:text-teal-300 truncate transition-colors">
            {label}
          </span>
          {badge && (
            <span className="shrink-0 text-[9px] font-bold px-1.5 py-0.5 rounded-md bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400 tracking-wide">
              {badge}
            </span>
          )}
        </div>
        {description && (
          <p className="text-[11px] text-slate-400 dark:text-slate-500 leading-snug mt-0.5 line-clamp-1">
            {description}
          </p>
        )}
      </div>
    </button>
  );
}

// ── Helpers ─────────────────────────────────────────────────────────────────

// Map group label → icon gọn
const GROUP_ICONS: Record<string, LucideIcon> = {
  'Library': BookMarked,
  'AI Assistant': MessageCircle,
  'Analysis & Research': LineChart,
  'Learning': GraduationCap,
  'Advanced Psychology': Brain,
  'Quality Evaluation': FlaskConical,
  'System': ShieldCheck,
  'Account': UserCircle,
};

function groupItemsIcon(groupLabel: string): LucideIcon {
  return GROUP_ICONS[groupLabel] ?? LayoutGrid;
}