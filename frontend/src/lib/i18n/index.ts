import en from './en';
import vi from './vi';

export type Locale = 'vi' | 'en';

export const LOCALES: { code: Locale; label: string; flag: string }[] = [
  { code: 'vi', label: 'Tiếng Việt', flag: '🇻🇳' },
  { code: 'en', label: 'English', flag: '🇬🇧' },
];

export function getTranslations(locale?: string) {
  if (locale === 'en') return en;
  return vi;
}

export type Translations = typeof en;
export default { en, vi };
