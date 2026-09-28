'use client';

import { Suspense, useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ExternalLink } from 'lucide-react';
import { useWorkspaceTabs } from './WorkspaceTabsContext';

interface WorkspaceBodyProps {
  /** Khi không có tab active, render children (page route hoặc landing). */
  children: React.ReactNode;
}

/**
 * Body shell centered (max-width 1100px) chứa active tab content.
 * Khi không có tab active → render children (page route).
 */
export function WorkspaceBody({ children }: WorkspaceBodyProps) {
  const { activeRoute, closeTab, clearActiveTab, loadingHref } = useWorkspaceTabs();
  const pathname = usePathname();
  const linkInterceptorRef = useRef<HTMLDivElement>(null);

  // Auto-clear active tab khi navigate về landing page `/` để render children route
  // thay vì giữ tab content cũ (vd bấm logo từ /chat sẽ về landing thật sự).
  useEffect(() => {
    if (pathname === '/' && activeRoute) {
      clearActiveTab();
    }
  }, [pathname, activeRoute, clearActiveTab]);

  // Link interceptor: nếu tab content có <Link href="/library"> thì chuyển sang tab khác
  // thay vì navigate route (giữ UX workspace).
  useEffect(() => {
    const el = linkInterceptorRef.current;
    if (!el) return;
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement | null;
      if (!target) return;
      const anchor = target.closest('a[href]') as HTMLAnchorElement | null;
      if (!anchor) return;
      const href = anchor.getAttribute('href');
      if (!href) return;
      if (
        href.startsWith('http') ||
        href.startsWith('mailto:') ||
        href.startsWith('tel:') ||
        href.startsWith('#') ||
        anchor.target === '_blank'
      ) {
        return;
      }
      const clean = href.split('?')[0].split('#')[0];
      // Nếu click vào route hiện tại → no-op (cho phép default)
      if (clean === activeRoute?.href) return;
      // Bỏ qua nếu không phải internal route trong registry — để browser xử lý
      // (workspace route map có trong context, nhưng ở đây ta delegate về default navigation)
    };
    el.addEventListener('click', handler);
    return () => el.removeEventListener('click', handler);
  }, [activeRoute?.href]);

  return (
    <div ref={linkInterceptorRef} className="flex-1 min-h-0 overflow-y-auto">
      <AnimatePresence mode="wait">
        {activeRoute ? (
          <motion.div
            key={activeRoute.href}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="mx-auto max-w-[1100px] px-4 md:px-6 py-6"
          >
            {/* Tab breadcrumb + actions */}
            <div className="flex items-center justify-between mb-5 pb-3 border-b border-slate-200/50 dark:border-slate-800/50">
              <div className="flex items-center gap-2 min-w-0">
                <activeRoute.icon className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0" />
                <h1 className="text-base font-semibold text-slate-800 dark:text-slate-100 truncate">
                  {activeRoute.title}
                </h1>
                {loadingHref === activeRoute.href && (
                  <span className="ml-2 inline-block w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse" />
                )}
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <a
                  href={activeRoute.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-8 h-8 flex items-center justify-center rounded-lg text-slate-400 dark:text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
                  aria-label="Open in new tab"
                  title="Open root route in new tab"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
                <button
                  onClick={() => closeTab(activeRoute.href)}
                  className="w-8 h-8 flex items-center justify-center rounded-lg text-slate-400 dark:text-slate-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400 transition-colors"
                  aria-label="Close tab"
                  title="Close tab (Ctrl+W)"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Active tab content */}
            <Suspense fallback={<TabLoading />}>
              <activeRoute.Component />
            </Suspense>
          </motion.div>
        ) : (
          <motion.div
            key="page-children"
            initial={{ opacity: 1 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="h-full"
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function TabLoading() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="flex flex-col items-center gap-3">
        <div className="w-8 h-8 border-2 border-teal-500/30 border-t-teal-500 rounded-full animate-spin" />
        <p className="text-sm text-slate-500 dark:text-slate-400">Loading...</p>
      </div>
    </div>
  );
}