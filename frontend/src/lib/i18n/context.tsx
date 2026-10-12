'use client';

import { createContext, useContext, ReactNode, useState, useEffect } from 'react';
import en from './en';
import vi from './vi';
import { Locale, LOCALES } from './index';

export type Translations = typeof en;

interface I18nContextValue {
  locale: Locale;
  t: Translations;
  setLocale: (l: Locale) => void;
  locales: { code: Locale; label: string; flag: string }[];
}

const I18nContext = createContext<I18nContextValue>({
  locale: 'vi',
  t: vi,
  setLocale: () => {},
  locales: LOCALES,
});

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>('vi');

  useEffect(() => {
    try {
      const saved = localStorage.getItem('acamind_locale') as Locale | null;
      if (saved && (saved === 'vi' || saved === 'en')) {
        setLocaleState(saved);
      }
    } catch {}
  }, []);

  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale);
    try {
      localStorage.setItem('acamind_locale', newLocale);
    } catch {}
  };

  const t = locale === 'en' ? en : vi;

  return (
    <I18nContext.Provider value={{ locale, t, setLocale, locales: LOCALES }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  return useContext(I18nContext);
}
