export const routing = {
  // A list of all locales that are supported
  locales: ['en', 'fa'] as const,

  // Used when no locale matches
  defaultLocale: 'en' as const,
} as const;

export type Locale = (typeof routing.locales)[number];

