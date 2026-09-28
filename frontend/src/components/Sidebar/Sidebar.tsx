'use client';

import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  Menu,
  X,
  PanelLeftClose,
  PanelLeft,
  Settings,
  LogOut,
  User,
} from 'lucide-react';
import { NAV_GROUPS, type NavItem, type NavGroup, type UserRole } from './navConfig';
import { NeuralBadge } from '@/components/ui/NeuralBadge';

// ─── Types ────────────────────────────────────────────────────────────────────

interface SidebarProps {
  userRole?: UserRole;
  userName?: string;
  userEmail?: string;
  userAvatar?: string;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function isItemVisible(item: NavItem, userRole: UserRole): boolean {
  if (!item.roles) return true;
  return item.roles.includes(userRole);
}

function isGroupVisible(group: NavGroup, userRole: UserRole): boolean {
  return group.items.some((item) => isItemVisible(item, userRole));
}

function isActive(href: string, pathname: string): boolean {
  if (href === '/dashboard') return pathname === '/dashboard';
  return pathname.startsWith(href) && href !== '/';
}

// ─── Badge Component ─────────────────────────────────────────────────────────

function Badge({ text, variant = 'neural' }: { text: string; variant?: 'neural' | 'success' | 'warning' | 'cortex' }) {
  const variantMap = {
    neural: 'neural',
    success: 'success',
    warning: 'dopamine',
    cortex: 'cortex',
  } as const;
  return <NeuralBadge variant={variantMap[variant]} size="sm">{text}</NeuralBadge>;
}

// ─── Nav Item Row ────────────────────────────────────────────────────────────

function NavItemRow({
  item,
  pathname,
  collapsed,
}: {
  item: NavItem;
  pathname: string;
  collapsed: boolean;
}) {
  const active = isActive(item.href, pathname);
  const Icon = item.icon;

  return (
    <Link
      href={item.disabled ? '#' : item.href}
      title={collapsed ? item.label : undefined}
      aria-disabled={item.disabled}
      className={`
        group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium
        transition-all duration-200 ease-out
        ${active
          ? 'bg-gradient-to-r from-neural-500 to-neural-600 text-white shadow-md shadow-neural-500/25'
          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-100'
        }
        ${item.disabled ? 'opacity-40 cursor-not-allowed pointer-events-none' : 'cursor-pointer'}
        ${collapsed ? 'justify-center px-2' : ''}
      `}
    >
      {/* Icon */}
      <Icon
        size={18}
        className={`
          flex-shrink-0 transition-transform duration-200
          ${active
            ? 'text-white'
            : 'text-gray-400 dark:text-gray-500 group-hover:text-gray-600 dark:group-hover:text-gray-300'
          }
          ${!active && 'group-hover:scale-110'}
        `}
      />

      {/* Label + badges */}
      {!collapsed && (
        <>
          <span className="flex-1 truncate">{item.label}</span>

          {item.isNew && (
            <Badge text="New" variant="success" />
          )}
          {item.badge && item.badge !== 'Admin' && (
            <Badge text={item.badge} variant="neural" />
          )}
          {item.badge === 'Admin' && (
            <Badge text="Admin" variant="warning" />
          )}
        </>
      )}
    </Link>
  );
}

// ─── Nav Group Section ──────────────────────────────────────────────────────

function NavGroupSection({
  group,
  pathname,
  userRole,
  collapsed,
}: {
  group: NavGroup;
  pathname: string;
  userRole: UserRole;
  collapsed: boolean;
}) {
  const [open, setOpen] = useState(group.defaultOpen ?? true);

  const visibleItems = group.items.filter((item) => isItemVisible(item, userRole));
  if (visibleItems.length === 0) return null;

  // Collapsed: show only items with divider
  if (collapsed) {
    return (
      <div className="space-y-1">
        <div className="h-px bg-gradient-to-r from-transparent via-gray-200 dark:via-gray-700 to-transparent mx-2 my-2" />
        {visibleItems.map((item) => (
          <NavItemRow key={item.href} item={item} pathname={pathname} collapsed={collapsed} />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {/* Group header */}
      {group.collapsible ? (
        <button
          onClick={() => setOpen((prev) => !prev)}
          className={`
            w-full flex items-center justify-between px-3 py-2
            text-xs font-semibold uppercase tracking-wider
            transition-colors duration-150
            ${open
              ? 'text-gray-500 dark:text-gray-400'
              : 'text-gray-400 dark:text-gray-500'
            }
            hover:text-gray-700 dark:hover:text-gray-300
          `}
        >
          <span>{group.groupLabel}</span>
          <ChevronDown
            size={12}
            className={`transition-transform duration-200 ${open ? 'rotate-0' : '-rotate-90'}`}
          />
        </button>
      ) : (
        <p className="px-3 py-2 text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
          {group.groupLabel}
        </p>
      )}

      {/* Items */}
      {(!group.collapsible || open) && (
        <div className="space-y-0.5 px-1">
          {visibleItems.map((item) => (
            <NavItemRow key={item.href} item={item} pathname={pathname} collapsed={collapsed} />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── User Footer ────────────────────────────────────────────────────────────

function UserFooter({
  userName,
  userEmail,
  userRole,
  userAvatar,
  collapsed,
}: {
  userName?: string;
  userEmail?: string;
  userRole: UserRole;
  userAvatar?: string;
  collapsed: boolean;
}) {
  const ROLE_CONFIG: Record<UserRole, { label: string; variant: 'neural' | 'cortex' | 'dopamine' }> = {
    admin: { label: 'Admin', variant: 'dopamine' },
    researcher: { label: 'Researcher', variant: 'cortex' },
    student: { label: 'Student', variant: 'neural' },
  };

  const { label, variant } = ROLE_CONFIG[userRole];
  const initials = userName ? userName.charAt(0).toUpperCase() : '?';

  if (collapsed) {
    return (
      <div className="p-2 border-t border-gray-200 dark:border-gray-800">
        <div className="w-9 h-9 mx-auto rounded-xl bg-gradient-to-br from-neural-500 to-cortex-500 flex items-center justify-center text-white text-sm font-bold shadow-md">
          {initials}
        </div>
      </div>
    );
  }

  return (
    <div className="p-3 border-t border-gray-200 dark:border-gray-800">
      <div className="flex items-center gap-3 p-2 rounded-xl bg-gray-50 dark:bg-gray-800/50">
        {/* Avatar */}
        {userAvatar ? (
          <Image
            src={userAvatar}
            alt={userName || 'User'}
            width={36}
            height={36}
            className="rounded-xl object-cover"
          />
        ) : (
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-neural-500 to-cortex-500 flex items-center justify-center text-white text-sm font-bold shadow-md">
            {initials}
          </div>
        )}

        {/* Info */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
            {userName ?? 'Guest'}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{userEmail ?? ''}</p>
        </div>

        {/* Role Badge */}
        <NeuralBadge variant={variant} size="sm">{label}</NeuralBadge>
      </div>

      {/* Quick Actions */}
      <div className="flex gap-2 mt-3">
        <Link
          href="/profile"
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          <User size={14} />
          <span>Profile</span>
        </Link>
        <Link
          href="/settings"
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          <Settings size={14} />
          <span>Settings</span>
        </Link>
      </div>
    </div>
  );
}

// ─── Logo ─────────────────────────────────────────────────────────────────────

function SidebarLogo({ collapsed }: { collapsed: boolean }) {
  return (
    <div className={`flex items-center gap-3 px-4 py-4 ${collapsed ? 'justify-center' : ''}`}>
      {/* Icon */}
      <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-neural-500 via-neural-600 to-cortex-500 flex items-center justify-center flex-shrink-0 shadow-lg shadow-neural-500/25">
        <BrainIcon className="w-5 h-5 text-white" />
      </div>

      {!collapsed && (
        <div>
          <p className="font-bold text-gray-900 dark:text-white text-sm leading-tight tracking-tight">
            ACAMIND
          </p>
          <p className="text-[10px] text-gray-500 dark:text-gray-400">
            AI Psychology
          </p>
        </div>
      )}
    </div>
  );
}

// ─── Brain Icon SVG ─────────────────────────────────────────────────────────

function BrainIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 4.5a2.5 2.5 0 0 0-4.96-.46 2.5 2.5 0 0 0-1.98 3 2.5 2.5 0 0 0 1.32 4.24 3 3 0 0 0 .34 5.58 2.5 2.5 0 0 0 2.96 3.08A2.5 2.5 0 0 0 12 19.5a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0 1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 12 4.5" />
      <path d="m15.7 10.4-.9.4" />
      <path d="m9.2 13.2 1.7 1.7" />
      <path d="m12.6 19.7 1.3-1.3" />
    </svg>
  );
}

// ─── Desktop Sidebar ───────────────────────────────────────────────────────

function DesktopSidebar({
  userRole,
  userName,
  userEmail,
  userAvatar,
  collapsed,
  onToggleCollapse,
}: SidebarProps & { collapsed: boolean; onToggleCollapse: () => void }) {
  const pathname = usePathname();
  const mainGroups = NAV_GROUPS.filter((g) => g.groupKey !== 'account');
  const accountGroup = NAV_GROUPS.find((g) => g.groupKey === 'account');

  return (
    <aside
      className={`
        hidden md:flex flex-col h-screen sticky top-0
        bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl
        border-r border-gray-200/50 dark:border-gray-800/50
        transition-all duration-300 ease-out
        ${collapsed ? 'w-[72px]' : 'w-64'}
      `}
    >
      {/* Logo */}
      <SidebarLogo collapsed={collapsed} />

      {/* Toggle button */}
      <button
        onClick={onToggleCollapse}
        className={`
          absolute top-5 z-10 w-6 h-6 rounded-full
          flex items-center justify-center
          bg-white dark:bg-gray-800
          border border-gray-200 dark:border-gray-700
          text-gray-400 hover:text-gray-600 dark:hover:text-gray-300
          shadow-sm hover:shadow-md
          transition-all duration-200
          ${collapsed ? 'right-[-12px]' : '-right-3'}
        `}
        title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? (
          <PanelLeft size={12} className="transition-transform group-hover:rotate-12" />
        ) : (
          <PanelLeftClose size={12} />
        )}
      </button>

      {/* Nav items */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden px-3 py-4 space-y-6">
        {mainGroups.map((group) =>
          isGroupVisible(group, userRole ?? 'student') ? (
            <NavGroupSection
              key={group.groupKey}
              group={group}
              pathname={pathname}
              userRole={userRole ?? 'student'}
              collapsed={collapsed}
            />
          ) : null
        )}
      </nav>

      {/* Account group */}
      {accountGroup && !collapsed && (
        <div className="px-3 py-2 space-y-0.5">
          <div className="h-px bg-gradient-to-r from-transparent via-gray-200 dark:via-gray-700 to-transparent mb-2" />
          {accountGroup.items
            .filter((item) => isItemVisible(item, userRole ?? 'student'))
            .map((item) => (
              <NavItemRow key={item.href} item={item} pathname={pathname} collapsed={collapsed} />
            ))}
        </div>
      )}

      {/* User info */}
      <UserFooter
        userName={userName}
        userEmail={userEmail}
        userRole={userRole ?? 'student'}
        userAvatar={userAvatar}
        collapsed={collapsed}
      />
    </aside>
  );
}

// ─── Mobile Sidebar ────────────────────────────────────────────────────────

function MobileSidebar({
  open,
  onClose,
  userRole,
  userName,
  userEmail,
  userAvatar,
}: SidebarProps & { open: boolean; onClose: () => void }) {
  const pathname = usePathname();
  const mainGroups = NAV_GROUPS.filter((g) => g.groupKey !== 'account');
  const accountGroup = NAV_GROUPS.find((g) => g.groupKey === 'account');

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm md:hidden animate-fade-in"
          onClick={onClose}
        />
      )}

      {/* Drawer */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-50 w-72 flex flex-col
          bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl
          border-r border-gray-200/50 dark:border-gray-800/50
          transform transition-transform duration-300 ease-out md:hidden
          ${open ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200 dark:border-gray-800">
          <SidebarLogo collapsed={false} />
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {mainGroups.map((group) =>
            isGroupVisible(group, userRole ?? 'student') ? (
              <NavGroupSection
                key={group.groupKey}
                group={group}
                pathname={pathname}
                userRole={userRole ?? 'student'}
                collapsed={false}
              />
            ) : null
          )}
        </nav>

        {/* Account */}
        {accountGroup && (
          <div className="px-3 py-2 space-y-0.5 border-t border-gray-200 dark:border-gray-800">
            {accountGroup.items
              .filter((item) => isItemVisible(item, userRole ?? 'student'))
              .map((item) => (
                <NavItemRow key={item.href} item={item} pathname={pathname} collapsed={false} />
              ))}
          </div>
        )}

        <UserFooter
          userName={userName}
          userEmail={userEmail}
          userRole={userRole ?? 'student'}
          userAvatar={userAvatar}
          collapsed={false}
        />
      </aside>
    </>
  );
}

// ─── Mobile Topbar ─────────────────────────────────────────────────────────

export function MobileTopbar({ onOpenSidebar }: { onOpenSidebar: () => void }) {
  return (
    <header className="md:hidden sticky top-0 z-30 flex items-center gap-3 px-4 py-3 bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl border-b border-gray-200/50 dark:border-gray-800/50">
      <button
        onClick={onOpenSidebar}
        className="p-2 rounded-xl text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
      >
        <Menu size={20} />
      </button>

      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-neural-500 to-cortex-500 flex items-center justify-center shadow-md">
          <BrainIcon className="w-4 h-4 text-white" />
        </div>
        <span className="font-bold text-gray-900 dark:text-white text-sm">ACAMIND</span>
      </div>
    </header>
  );
}

// ─── Main Export ────────────────────────────────────────────────────────────

export default function Sidebar({ userRole, userName, userEmail, userAvatar }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {/* Desktop sidebar */}
      <DesktopSidebar
        userRole={userRole}
        userName={userName}
        userEmail={userEmail}
        userAvatar={userAvatar}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed((prev) => !prev)}
      />

      {/* Mobile topbar trigger */}
      <MobileTopbar onOpenSidebar={() => setMobileOpen(true)} />

      {/* Mobile drawer */}
      <MobileSidebar
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        userRole={userRole}
        userName={userName}
        userEmail={userEmail}
        userAvatar={userAvatar}
      />
    </>
  );
}
