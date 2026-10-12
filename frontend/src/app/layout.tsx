import type { Metadata } from 'next';
import { Inter, Manrope } from 'next/font/google';
import './globals.css';
import 'katex/dist/katex.min.css';
import ClientLayout from '@/components/ClientLayout';
import { I18nProvider } from '@/lib/i18n/context';

const inter = Inter({
 subsets: ['latin', 'vietnamese'],
 variable: '--font-inter',
 display: 'swap',
});

const manrope = Manrope({
 subsets: ['latin'],
 variable: '--font-manrope',
 display: 'swap',
});

export const metadata: Metadata = {
 title: 'Acamind',
 description: 'Intelligent Academic Q&A System',
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
 <body className={`${inter.variable} ${manrope.variable} font-[family-name:var(--font-inter)]`}>
 <I18nProvider>
 <ClientLayout>{children}</ClientLayout>
 </I18nProvider>
 </body>
 </html>
 );
}
