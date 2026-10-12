'use client';

import React from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { Lock, ArrowRight, Sparkles, X, ShieldAlert } from 'lucide-react';
import { useI18n } from '@/lib/i18n/context';

interface AuthRequiredModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
}

export function AuthRequiredModal({
  isOpen,
  onClose,
  title,
  description,
}: AuthRequiredModalProps) {
  const { t } = useI18n();

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.2 }}
          className="relative w-full max-w-md overflow-hidden rounded-2xl bg-white dark:bg-[#111827] border border-gray-200 dark:border-white/10 shadow-2xl p-6 text-center"
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors"
          >
            <X size={16} />
          </button>

          {/* Icon Badge */}
          <div className="mx-auto w-14 h-14 rounded-2xl bg-gradient-to-tr from-amber-500/20 via-teal-500/20 to-purple-500/20 border border-amber-500/30 flex items-center justify-center text-amber-500 dark:text-amber-400 mb-4 shadow-lg shadow-amber-500/10">
            <Lock size={26} />
          </div>

          {/* Title & Description */}
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
            {title || 'Yêu cầu đăng nhập tài khoản'}
          </h3>
          <p className="text-xs text-gray-600 dark:text-gray-300 leading-relaxed mb-6">
            {description ||
              'Bạn đang truy cập ở chế độ Khách. Vui lòng đăng nhập hoặc tạo tài khoản miễn phí để sử dụng đầy đủ các tính năng thông minh của Acamind (Chat AI, Phân tích học thuật, Khai phá đồ thị tri thức, Tra cứu đối chiếu nguồn PDF).'}
          </p>

          {/* Action Buttons */}
          <div className="flex flex-col gap-2.5">
            <Link
              href="/login"
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-teal-500 via-cortex-500 to-purple-600 hover:opacity-95 shadow-md shadow-teal-500/20 transition-all hover:scale-[1.01] active:scale-[0.99]"
            >
              <span>Đăng nhập ngay</span>
              <ArrowRight size={14} />
            </Link>

            <Link
              href="/register"
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-semibold text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/15 transition-colors"
            >
              <Sparkles size={14} className="text-teal-500" />
              <span>Tạo tài khoản mới miễn phí</span>
            </Link>

            <button
              onClick={onClose}
              className="mt-1 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 py-1 transition-colors"
            >
              Để sau
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

/**
 * Banner nhắc nhở đăng nhập ngay trong giao diện
 */
export function AuthRequiredBanner({
  message = 'Bạn đang xem ở chế độ Khách. Vui lòng đăng nhập để sử dụng tính năng này.',
}: {
  message?: string;
}) {
  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3.5 rounded-2xl bg-gradient-to-r from-teal-500/10 via-purple-500/10 to-amber-500/10 border border-teal-500/30 dark:border-white/10 shadow-sm">
      <div className="flex items-center gap-2.5 min-w-0 w-full sm:w-auto">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-teal-500 to-purple-600 flex items-center justify-center text-white shrink-0 shadow-md">
          <Lock size={15} />
        </div>
        <div className="min-w-0">
          <p className="text-xs font-semibold text-gray-800 dark:text-gray-100">
            Tài khoản Khách (Chưa đăng nhập)
          </p>
          <p className="text-[11px] text-gray-500 dark:text-gray-400 truncate">
            {message}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto justify-end">
        <Link
          href="/login"
          className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-gradient-to-r from-teal-500 to-purple-600 hover:opacity-90 transition-opacity shadow-sm"
        >
          Đăng nhập
        </Link>
        <Link
          href="/register"
          className="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/15 transition-colors"
        >
          Đăng ký
        </Link>
      </div>
    </div>
  );
}

/**
 * Toàn trang hiển thị chặn khách và yêu cầu đăng nhập
 */
export function GuestBlockScreen({
  title = 'Yêu cầu đăng nhập tài khoản',
  description = 'Tính năng chuyên sâu này yêu cầu đăng nhập tài khoản Acamind để lưu trữ lịch sử, quản lý dữ liệu và truy cập trích dẫn học thuật.',
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] p-6 text-center">
      <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-amber-500/20 via-teal-500/20 to-purple-500/20 border border-amber-500/30 flex items-center justify-center text-amber-500 dark:text-amber-400 mb-5 shadow-xl shadow-amber-500/10">
        <Lock size={32} />
      </div>
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
        {title}
      </h2>
      <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 max-w-md leading-relaxed mb-6">
        {description}
      </p>
      <div className="flex items-center gap-3">
        <Link
          href="/login"
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-white bg-gradient-to-r from-teal-500 via-cortex-500 to-purple-600 hover:opacity-95 shadow-md shadow-teal-500/20 transition-all hover:scale-[1.02]"
        >
          <span>Đăng nhập ngay</span>
          <ArrowRight size={15} />
        </Link>
        <Link
          href="/register"
          className="px-4 py-2.5 rounded-xl text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/15 transition-colors"
        >
          Tạo tài khoản miễn phí
        </Link>
      </div>
    </div>
  );
}
