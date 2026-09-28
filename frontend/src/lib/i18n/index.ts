import en from './en';

export type Locale = 'en';

export const LOCALES: { code: Locale; label: string; flag: string }[] = [
  { code: 'en', label: 'English', flag: '🇬🇧' },
];

export function getTranslations(_locale?: string) {
  return en;
}

export type Translations = typeof en;
export default { en };
