'use client';

import { motion } from 'framer-motion';
import { X } from 'lucide-react';
import { useWorkspaceTabs } from './WorkspaceTabsContext';
import { useI18n } from '@/lib/i18n/context';

const tabKeys: Record<string, string> = {
  '/upload': 'upload',
  '/library': 'thu_vien',
  '/timeline': 'timeline',
  '/chat': 'chat',
  '/translate': 'translate',
  '/Terminology': 'explain',
  '/graph': 'graph',
  '/Trend': 'trends',
  '/Literature': 'literature',
  '/Quiz': 'quiz',
  '/Slide': 'slides',
  '/study': 'learn',
  '/Health': 'profile',
  '/3d': 'body',
  '/Critique': 'debate',
  '/RAG': 'evaluate',
  '/profile': 'profile',
  '/admin': 'admin'
};

/**
 * Dãy tab pills hiển thị trên header.
 * Pill active có background + accent, pill không active trong suốt.
 * Click pill = switch active; click X = close tab.
 */
export function WorkspaceTabBar() {
  const { tabs, activeHref, switchTab, closeTab } = useWorkspaceTabs();
  const { t } = useI18n();

  if (tabs.length === 0) {
    return null;
  }

  const getLocalizedTitle = (href: string, defaultTitle: string) => {
    const clean = href.split('?')[0].split('#')[0];
    const key = tabKeys[clean];
    if (key && (t.nav as any)[key]) {
      return (t.nav as any)[key];
    }
    return defaultTitle;
  };

  return (
    <div className="hidden md:flex items-center gap-1 overflow-x-auto max-w-[55vw] [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
      {tabs.map((tab) => {
        const active = tab.href === activeHref;
        const Icon = tab.icon;
        const localizedTitle = getLocalizedTitle(tab.href, tab.title);
        return (
          <motion.div
            key={tab.href}
            layout
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.15 }}
            onClick={() => switchTab(tab.href)}
            className={`group flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium whitespace-nowrap transition-colors cursor-pointer ${
              active
                ? 'bg-teal-500/15 text-teal-700 dark:text-teal-300 ring-1 ring-teal-500/30'
                : 'text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-700 dark:hover:text-slate-200'
            }`}
            title={localizedTitle}
          >
            <Icon className="w-3 h-3 shrink-0" />
            <span className="truncate max-w-[90px]">{localizedTitle}</span>
            <span
              onClick={(e) => {
                e.stopPropagation();
                closeTab(tab.href);
              }}
              className={`shrink-0 -mr-0.5 p-0.5 rounded transition-colors cursor-pointer ${
                active
                  ? 'hover:bg-teal-500/25 text-teal-700/70 dark:text-teal-300/70'
                  : 'opacity-0 group-hover:opacity-100 hover:bg-slate-300/60 dark:hover:bg-slate-700/60 text-slate-400'
              }`}
              role="button"
              aria-label={`Close tab ${localizedTitle}`}
            >
              <X className="w-2.5 h-2.5" />
            </span>
          </motion.div>
        );
      })}
    </div>
  );
}