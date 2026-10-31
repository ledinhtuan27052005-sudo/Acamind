import type { Metadata } from 'next';
import './globals.css';
import 'katex/dist/katex.min.css';
import ClientLayout from '@/components/ClientLayout';
import { I18nProvider } from '@/lib/i18n/context';

export const metadata: Metadata = {
 title: 'Acamind',
 description: 'Intelligent Academic Q&A System',
 icons: { icon: '/Logo.jpeg' },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
 return (
 <html lang="vi" suppressHydrationWarning>
 <head>
 {/* Apply dark class before paint to prevent FOUC */}
 <script
 dangerouslySetInnerHTML={{
 __html: `
 (function() {
 try {
 var t = localStorage.getItem('darkMode');
 if (t === null) {
 t = window.matchMedia('(prefers-color-scheme: dark)').matches ? '1' : '0';
 }
 if (t === '1') document.documentElement.classList.add('dark');
 } catch (e) {}
 })();
 `,
 }}
 />
 </head>
 <body className="font-sans">
 <I18nProvider>
 <ClientLayout>{children}</ClientLayout>
 </I18nProvider>
 </body>
 </html>
 );
}
