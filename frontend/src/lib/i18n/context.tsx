'use client';

import { createContext, useContext, ReactNode } from 'react';
import en from './en';

export type Translations = typeof en;

interface I18nContextValue {
  locale: 'en';
  t: Translations;
  setLocale: (l: string) => void;
  locales: { code: string; label: string; flag: string }[];
}

const I18nContext = createContext<I18nContextValue>({
  locale: 'en',
  t: en,
  setLocale: () => {},
  locales: [{ code: 'en', label: 'English', flag: '🇬🇧' }],
});

export function I18nProvider({ children }: { children: ReactNode }) {
  return (
    <I18nContext.Provider value={{ locale: 'en', t: en, setLocale: () => {}, locales: [{ code: 'en', label: 'English', flag: '🇬🇧' }] }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  return useContext(I18nContext);
}
