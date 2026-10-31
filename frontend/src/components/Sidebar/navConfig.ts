import {
  Upload, FileText, MessageSquare, Users, ShieldCheck, Settings, UserCircle, LogOut,
  type LucideIcon,
} from 'lucide-react';

export type UserRole = 'student' | 'researcher' | 'expert' | 'admin';

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  description: string;
  badge?: string;
  roles?: UserRole[];
  isNew?: boolean;
  disabled?: boolean;
}

export interface NavGroup {
  groupLabel: string;
  groupKey: string;
  collapsible?: boolean;
  defaultOpen?: boolean;
  items: NavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
  {
    groupLabel: 'Documents',
    groupKey: 'documents',
    collapsible: true,
    defaultOpen: true,
    items: [
      { label: 'Upload Documents', href: '/upload', icon: Upload, description: 'Upload research files for analysis' },
      { label: 'Document Library', href: '/library', icon: FileText, description: 'View and manage uploaded documents' },
    ],
  },
  {
    groupLabel: 'AI Assistant',
    groupKey: 'ai_chat',
    collapsible: true,
    defaultOpen: true,
    items: [
      { label: 'Research Chatbot', href: '/chat', icon: MessageSquare, description: 'Ask questions and compare research with citations' },
    ],
  },
  {
    groupLabel: 'System',
    groupKey: 'system',
    collapsible: true,
    defaultOpen: false,
    items: [
      { label: 'User Management', href: '/admin', icon: Users, description: 'Manage account roles', roles: ['admin'], badge: 'Admin' },
      { label: 'Permissions', href: '/admin/permissions', icon: ShieldCheck, description: 'Configure account permissions', roles: ['admin'] },
      { label: 'Settings', href: '/settings', icon: Settings, description: 'Configure account and system settings', roles: ['admin'] },
    ],
  },
  {
    groupLabel: 'Account',
    groupKey: 'account',
    collapsible: false,
    defaultOpen: true,
    items: [
      { label: 'Personal Profile', href: '/profile', icon: UserCircle, description: 'View and update account information' },
      { label: 'Log Out', href: '/logout', icon: LogOut, description: 'Exit the system' },
    ],
  },
];

export const HREF_LABEL_MAP: Record<string, string> = NAV_GROUPS.flatMap((group) => group.items).reduce(
  (acc, item) => ({ ...acc, [item.href]: item.label }),
  {} as Record<string, string>,
);
