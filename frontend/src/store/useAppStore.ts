import { create } from 'zustand';

export interface AuthUser {
 id: string;
 email: string;
 full_name: string;
 role: string;
 plan?: string; // "free" | "pro" | "researcher" | "enterprise"
 avatar_url?: string | null;
 is_oauth?: boolean;
}

interface Message {
 id: string;
 role: 'user' | 'assistant';
 content: string;
 timestamp: Date;
}

interface AppStore {
 // Auth
 user: AuthUser | null;
 token: string | null;
 setAuth: (user: AuthUser, token: string) => void;
 updateUser: (updates: Partial<AuthUser>) => void;
 logout: () => void;
 initAuth: () => void;

 // Documents
 selectedDocumentIds: string[];
 toggleDocument: (id: string) => void;
 clearSelection: () => void;

 // Chat
 chatMessages: Message[];
 addMessage: (msg: Omit<Message, 'id' | 'timestamp'>) => void;
 updateLastMessage: (content: string) => void;
 clearChat: () => void;

 // Theme
 darkMode: boolean;
 toggleDarkMode: () => void;
}

export const useAppStore = create<AppStore>((set) => ({
 // Auth
 user: null,
 token: null,
 setAuth: (user, token) => {
 if (typeof window !== 'undefined') {
 localStorage.setItem('token', token);
 localStorage.setItem('user', JSON.stringify(user));
 localStorage.setItem('user_id', user.id);
 }
 set({ user, token });
 },
 updateUser: (updates) => {
 set((state) => {
 if (!state.user) return {};
 const updated = { ...state.user, ...updates };
 if (typeof window !== 'undefined') {
 localStorage.setItem('user', JSON.stringify(updated));
 }
 return { user: updated };
 });
 },
 logout: () => {
 if (typeof window !== 'undefined') {
 localStorage.removeItem('token');
 localStorage.removeItem('user');
 localStorage.removeItem('user_id');
 }
 set({ user: null, token: null });
 },
 initAuth: () => {
 if (typeof window === 'undefined') return;
 const token = localStorage.getItem('token');
 const userStr = localStorage.getItem('user');
 const darkMode = localStorage.getItem('darkMode') === 'true';
 if (token && userStr) {
 try {
 set({ token, user: JSON.parse(userStr) });
 } catch {}
 }
 set({ darkMode });
 if (darkMode) document.documentElement.classList.add('dark');
 },

 // Documents
 selectedDocumentIds: [],
 toggleDocument: (id) =>
 set((state) => ({
 selectedDocumentIds: state.selectedDocumentIds.includes(id)
 ? state.selectedDocumentIds.filter((d) => d !== id)
 : [...state.selectedDocumentIds, id],
 })),
 clearSelection: () => set({ selectedDocumentIds: [] }),

 // Chat
 chatMessages: [],
 addMessage: (msg) =>
 set((state) => ({
 chatMessages: [
 ...state.chatMessages,
 { ...msg, id: crypto.randomUUID(), timestamp: new Date() },
 ],
 })),
 updateLastMessage: (content) =>
 set((state) => {
 const msgs = [...state.chatMessages];
 if (msgs.length > 0) msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], content };
 return { chatMessages: msgs };
 }),
 clearChat: () => set({ chatMessages: [] }),

 // Theme
 darkMode: false,
 toggleDarkMode: () =>
 set((state) => {
 const next = !state.darkMode;
 if (typeof window !== 'undefined') {
 localStorage.setItem('darkMode', String(next));
 document.documentElement.classList.toggle('dark', next);
 }
 return { darkMode: next };
 }),
}));
