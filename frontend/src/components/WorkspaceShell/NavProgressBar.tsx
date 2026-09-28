'use client';

import { AnimatePresence, motion } from 'framer-motion';
import { useWorkspaceTabs } from './WorkspaceTabsContext';

/**
 * Thanh loading 2px ở top, animation gradient khi đang dynamic-import tab.
 */
export function NavProgressBar() {
  const { loadingHref } = useWorkspaceTabs();
  const visible = !!loadingHref;

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          key="nav-progress"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed top-0 left-0 right-0 h-[2px] z-[200] overflow-hidden pointer-events-none"
        >
          <motion.div
            className="h-full w-[40%]"
            style={{ background: 'linear-gradient(90deg, #3B82F6, #A855F7, #06B6D4, #3B82F6)' }}
            animate={{ x: ['-100%', '350%'] }}
            transition={{ duration: 0.9, ease: 'easeInOut', repeat: Infinity }}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}