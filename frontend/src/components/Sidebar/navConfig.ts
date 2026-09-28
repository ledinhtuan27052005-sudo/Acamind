import {
  FileText,
  Upload,
  Timer,
  MessageSquare,
  Languages,
  BookOpen,
  Network,
  TrendingUp,
  Microscope,
  ClipboardList,
  Presentation,
  GraduationCap,
  Scan,
  Brain,
  Zap,
  FlaskConical,
  Users,
  Settings,
  UserCircle,
  LogOut,
  ShieldCheck,
  Activity,
  Stethoscope,
  HeartPulse,
  type LucideIcon,
} from 'lucide-react';

export type UserRole = 'student' | 'researcher' | 'admin';

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
  // ─────────────────────────────────────────────
  // 1. LIBRARY
  // ─────────────────────────────────────────────
  {
    groupLabel: 'Library',
    groupKey: 'library',
    collapsible: true,
    defaultOpen: true,
    items: [
      {
        label: 'Upload PDF Documents',
        href: '/upload',
        icon: Upload,
        description: 'Upload new documents (with OCR support)',
      },
      {
        label: 'Article Library',
        href: '/library',
        icon: FileText,
        description: 'View and manage all psychology PDFs',
      },
      {
        label: 'Research Timeline',
        href: '/timeline',
        icon: Timer,
        description: 'Technology development over the years',
      },
    ],
  },

  // ─────────────────────────────────────────────
  // 2. AI ASSISTANT
  // ─────────────────────────────────────────────
  {
    groupLabel: 'AI Assistant',
    groupKey: 'ai_chat',
    collapsible: true,
    defaultOpen: true,
    items: [
      {
        label: 'Chat Q&A',
        href: '/chat',
        icon: MessageSquare,
        description: 'Ask AI from psychology database — auto domain detection',
      },
      {
        label: 'Document Translation',
        href: '/translate',
        icon: Languages,
        description: 'AI translates PDF between English ↔ Vietnamese in stream',
      },
      {
        label: 'Psychology Terminology',
        href: '/Terminology',
        icon: BookOpen,
        description: 'Select keyword → AI explains instantly',
      },
    ],
  },

  // ─────────────────────────────────────────────
  // 3. ANALYSIS & RESEARCH
  // ─────────────────────────────────────────────
  {
    groupLabel: 'Analysis & Research',
    groupKey: 'research',
    collapsible: true,
    defaultOpen: true,
    items: [
      {
        label: 'Knowledge Graph',
        href: '/graph',
        icon: Network,
        description: 'Author – article network (Neo4j)',
      },
      {
        label: 'Research Trends',
        href: '/Trend',
        icon: TrendingUp,
        description: 'Most prominent research topics',
      },
      {
        label: 'Literature Review',
        href: '/Literature',
        icon: Microscope,
        description: 'AI writes Related Work & Research Gap',
      },
    ],
  },

  // ─────────────────────────────────────────────
  // 4. LEARNING
  // ─────────────────────────────────────────────
  {
    groupLabel: 'Learning',
    groupKey: 'learning',
    collapsible: true,
    defaultOpen: true,
    items: [
      {
        label: 'Review Quiz',
        href: '/Quiz',
        icon: ClipboardList,
        description: 'AI generates multiple-choice questions from PDF',
      },
      {
        label: 'AI Slide',
        href: '/Slide',
        icon: Presentation,
        description: 'Automatically generate slides from articles',
      },
      {
        label: 'Learning Mode',
        href: '/study',
        icon: GraduationCap,
        description: 'Beginner / Advanced / Researcher mode',
      },
    ],
  },

  // ─────────────────────────────────────────────
  // 5. ADVANCED PSYCHOLOGY
  // ─────────────────────────────────────────────
  {
    groupLabel: 'Advanced Psychology',
    groupKey: 'psychology',
    collapsible: true,
    defaultOpen: true,
    items: [
      {
        label: 'Health Profile',
        href: '/Health',
        icon: Stethoscope,
        description: 'DSM/ICD, treatment protocols, school comparisons',
      },
      {
        label: '3D Atlas',
        href: '/3d',
        icon: Scan,
        description: 'Report physical symptoms related to psychology',
      },
      {
        label: 'AI Critique',
        href: '/Critique',
        icon: Zap,
        description: 'AI analyzes and critiques psychology articles',
      },
    ],
  },

  // ─────────────────────────────────────────────
  // 6. QUALITY EVALUATION
  // ─────────────────────────────────────────────
  {
    groupLabel: 'Quality Evaluation',
    groupKey: 'evaluation',
    collapsible: true,
    defaultOpen: false,
    items: [
      {
        label: 'RAG Evaluation',
        href: '/RAG',
        icon: FlaskConical,
        description: 'Evaluate Faithfulness, Relevancy, Precision',
      },
    ],
  },

  // ─────────────────────────────────────────────
  // 7. SYSTEM
  // ─────────────────────────────────────────────
  {
    groupLabel: 'System',
    groupKey: 'system',
    collapsible: true,
    defaultOpen: false,
    items: [
      {
        label: 'User Management',
        href: '/admin',
        icon: Users,
        description: 'Manage Admin / Researcher / Student permissions',
        roles: ['admin'],
        badge: 'Admin',
      },
      {
        label: 'Permissions',
        href: '/admin/permissions',
        icon: ShieldCheck,
        description: 'Configure permissions for each feature',
        roles: ['admin'],
      },
      {
        label: 'Settings',
        href: '/settings',
        icon: Settings,
        description: 'Configure API keys, AI models, languages',
        roles: ['admin'],
      },
    ],
  },

  // ─────────────────────────────────────────────
  // 8. ACCOUNT
  // ─────────────────────────────────────────────
  {
    groupLabel: 'Account',
    groupKey: 'account',
    collapsible: false,
    defaultOpen: true,
    items: [
      {
        label: 'Personal Profile',
        href: '/profile',
        icon: UserCircle,
        description: 'View and update account information',
      },
      {
        label: 'Log Out',
        href: '/logout',
        icon: LogOut,
        description: 'Exit the system',
      },
    ],
  },
];

// Map href → label, dùng cho breadcrumb hoặc page title
export const HREF_LABEL_MAP: Record<string, string> = NAV_GROUPS.flatMap((g) => g.items).reduce(
  (acc, item) => ({ ...acc, [item.href]: item.label }),
  {} as Record<string, string>
);
