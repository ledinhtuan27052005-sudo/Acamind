'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import Link from 'next/link';
import {
 Bell, CheckCheck, Trash2, Info, CheckCircle2, AlertTriangle, Settings, X,
} from 'lucide-react';
import {
 getNotifications, getUnreadCount, markNotifRead, markAllNotifsRead, deleteNotif,
 AppNotification,
} from '@/lib/api';

const TYPE_CONFIG = {
 info: { icon: Info, color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-900/20' },
 success: { icon: CheckCircle2, color: 'text-emerald-500', bg: 'bg-emerald-50 dark:bg-emerald-900/20' },
 warning: { icon: AlertTriangle, color: 'text-amber-500', bg: 'bg-amber-50 dark:bg-amber-900/20' },
 system: { icon: Settings, color: 'text-purple-500', bg: 'bg-purple-50 dark:bg-purple-900/20' },
};

function timeAgo(iso: string | null): string {
 if (!iso) return '';
 const diff = Date.now() - new Date(iso).getTime();
 const m = Math.floor(diff / 60000);
 if (m < 1) return 'Just now';
 if (m < 60) return `${m} minutes ago`;
 const h = Math.floor(m / 60);
 if (h < 24) return `${h} hours ago`;
 const d = Math.floor(h / 24);
 if (d < 7) return `${d} days ago`;
 return new Date(iso).toLocaleDateString('en-US');
}

export default function NotificationBell() {
 const [open, setOpen] = useState(false);
 const [notifs, setNotifs] = useState<AppNotification[]>([]);
 const [unread, setUnread] = useState(0);
 const [loading, setLoading] = useState(false);
 const ref = useRef<HTMLDivElement>(null);

 const fetchCount = useCallback(async () => {
 try { setUnread(await getUnreadCount()); } catch {}
 }, []);

 const fetchAll = useCallback(async () => {
 setLoading(true);
 try {
 const data = await getNotifications();
 setNotifs(data);
 setUnread(data.filter(n => !n.is_read).length);
 } catch {}
 finally { setLoading(false); }
 }, []);

 // Poll unread count every 30s
 useEffect(() => {
 fetchCount();
 const id = setInterval(fetchCount, 30_000);
 return () => clearInterval(id);
 }, [fetchCount]);

 // Close on outside click
 useEffect(() => {
 const handler = (e: MouseEvent) => {
 if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
 };
 document.addEventListener('mousedown', handler);
 return () => document.removeEventListener('mousedown', handler);
 }, []);

 const handleOpen = () => {
 setOpen(o => {
 if (!o) fetchAll();
 return !o;
 });
 };

 const handleRead = async (n: AppNotification) => {
 if (!n.is_read) {
 try {
 await markNotifRead(n.id);
 setNotifs(prev => prev.map(x => x.id === n.id ? { ...x, is_read: true } : x));
 setUnread(c => Math.max(0, c - 1));
 } catch {}
 }
 if (n.link) {
 setOpen(false);
 }
 };

 const handleDelete = async (e: React.MouseEvent, id: string) => {
 e.stopPropagation();
 try {
 await deleteNotif(id);
 const target = notifs.find(x => x.id === id);
 setNotifs(prev => prev.filter(x => x.id !== id));
 if (target && !target.is_read) setUnread(c => Math.max(0, c - 1));
 } catch {}
 };

 const handleReadAll = async () => {
 try {
 await markAllNotifsRead();
 setNotifs(prev => prev.map(x => ({ ...x, is_read: true })));
 setUnread(0);
 } catch {}
 };

 return (
 <div ref={ref} className="relative">
 {/* Bell button */}
 <button
 onClick={handleOpen}
 className="relative w-9 h-9 flex items-center justify-center rounded-xl text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 dark:hover:bg-gray-800 hover:text-[#1E88E5] dark:hover:text-[#64B5F6] transition-all"
 title="Notifications"
 >
 <Bell className="w-[18px] h-[18px]" />
 {unread > 0 && (
 <span className="absolute top-1 right-1 min-w-[16px] h-4 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center px-0.5 leading-none">
 {unread > 99 ? '99+' : unread}
 </span>
 )}
 </button>

 {/* Dropdown */}
 {open && (
 <div className="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-slate-800/60 rounded-2xl shadow-xl shadow-gray-200/60 dark:shadow-black/50 border border-slate-100 dark:border-slate-800 overflow-hidden z-50">

 {/* Header */}
 <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 dark:border-slate-800">
 <div className="flex items-center gap-2">
 <Bell className="w-4 h-4 text-[#1E88E5]" />
 <span className="text-sm font-semibold text-slate-800 dark:text-slate-100">Notifications</span>
 {unread > 0 && (
 <span className="text-[10px] font-bold bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400 px-1.5 py-0.5 rounded-full">
 {unread} new
 </span>
 )}
 </div>
 {unread > 0 && (
 <button
 onClick={handleReadAll}
 className="flex items-center gap-1 text-[11px] text-[#1E88E5] hover:underline font-medium"
 >
 <CheckCheck className="w-3 h-3" /> Mark all read
 </button>
 )}
 </div>

 {/* List */}
 <div className="max-h-[360px] overflow-y-auto divide-y divide-gray-50/50">
 {loading ? (
 <div className="py-10 flex justify-center">
 <div className="w-5 h-5 border-2 border-[#1E88E5] border-t-transparent rounded-full animate-spin" />
 </div>
 ) : notifs.length === 0 ? (
 <div className="py-12 text-center">
 <Bell className="w-8 h-8 text-slate-300 dark:text-slate-600 mx-auto mb-2" />
 <p className="text-sm text-slate-400 dark:text-slate-500">No notifications</p>
 </div>
 ) : (
 notifs.map(n => {
 const cfg = TYPE_CONFIG[n.type] ?? TYPE_CONFIG.info;
 const Icon = cfg.icon;
 const itemCls = `flex items-start gap-3 px-4 py-3 cursor-pointer transition-colors group ${
 n.is_read
 ? 'hover:bg-slate-100 dark:hover:bg-slate-800/60 dark:hover:bg-gray-800/40'
 : 'bg-blue-50/40 dark:bg-blue-900/10 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 dark:hover:bg-indigo-900/20 dark:hover:bg-blue-900/20'
 }`;
 return n.link ? (
 <Link
 key={n.id}
 href={n.link}
 onClick={() => handleRead(n)}
 className={itemCls}
 >
 {/* Icon */}
 <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${cfg.bg}`}>
 <Icon className={`w-4 h-4 ${cfg.color}`} />
 </div>

 {/* Content */}
 <div className="flex-1 min-w-0">
 <div className="flex items-start justify-between gap-1">
 <p className={`text-xs font-semibold leading-snug ${n.is_read ? 'text-slate-600 dark:text-slate-300' : 'text-slate-900 dark:text-slate-100 dark:text-white'}`}>
 {n.title}
 </p>
 <button
 onClick={(e) => handleDelete(e, n.id)}
 className="opacity-0 group-hover:opacity-100 p-0.5 text-slate-300 dark:text-slate-600 hover:text-red-400 transition-all shrink-0"
 >
 <X className="w-3 h-3" />
 </button>
 </div>
 {n.body && (
 <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2">{n.body}</p>
 )}
 <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">{timeAgo(n.created_at)}</p>
 </div>

 {/* Unread dot */}
 {!n.is_read && (
 <div className="w-2 h-2 rounded-full bg-[#1E88E5] shrink-0 mt-1.5" />
 )}
 </Link>
 ) : (
 <div
 key={n.id}
 onClick={() => handleRead(n)}
 className={itemCls}
 >
 {/* Icon */}
 <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${cfg.bg}`}>
 <Icon className={`w-4 h-4 ${cfg.color}`} />
 </div>
 {/* Content */}
 <div className="flex-1 min-w-0">
 <div className="flex items-start justify-between gap-1">
 <p className={`text-xs font-semibold leading-snug ${n.is_read ? 'text-slate-600 dark:text-slate-300' : 'text-slate-900 dark:text-slate-100 dark:text-white'}`}>
 {n.title}
 </p>
 <button
 onClick={(e) => handleDelete(e, n.id)}
 className="opacity-0 group-hover:opacity-100 p-0.5 text-slate-300 dark:text-slate-600 hover:text-red-400 transition-all shrink-0"
 >
 <X className="w-3 h-3" />
 </button>
 </div>
 {n.body && (
 <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2">{n.body}</p>
 )}
 <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">{timeAgo(n.created_at)}</p>
 </div>
 {!n.is_read && (
 <div className="w-2 h-2 rounded-full bg-[#1E88E5] shrink-0 mt-1.5" />
 )}
 </div>
 );
 })
 )}
 </div>

 {/* Footer */}
 {notifs.length > 0 && (
 <div className="px-4 py-2.5 border-t border-slate-100 dark:border-slate-800 text-center">
 <button
 onClick={() => {
 setNotifs([]);
 setUnread(0);
 Promise.all(notifs.map(n => deleteNotif(n.id))).catch(() => {});
 }}
 className="flex items-center gap-1.5 mx-auto text-[11px] text-slate-400 dark:text-slate-500 hover:text-red-400 transition-colors"
 >
 <Trash2 className="w-3 h-3" /> Clear all
 </button>
 </div>
 )}
 </div>
 )}
 </div>
 );
}
