/**
 * Utility functions for handling Right-to-Left (RTL) text and languages
 */

/**
 * RTL language codes
 * Common RTL languages include: Arabic, Hebrew, Persian, Urdu, etc.
 */
const RTL_LANGUAGES = [
  'ar', // Arabic
  'he', // Hebrew
  'fa', // Persian (Farsi)
  'ur', // Urdu
  'yi', // Yiddish
  'ji', // Yiddish (alternate code)
  'ku', // Kurdish
  'sd', // Sindhi
];

/**
 * RTL character ranges:
 * Hebrew: \u0590-\u05FF
 * Arabic: \u0600-\u06FF
 * Arabic Supplement: \u0750-\u077F
 * Arabic Extended-A: \u08A0-\u08FF
 * Arabic Presentation Forms-A: \uFB50-\uFDFF
 * Arabic Presentation Forms-B: \uFE70-\uFEFF
 */
const RTL_CHAR_REGEX = /[\u0590-\u05FF\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/;

/**
 * LTR character ranges:
 * Basic Latin (a-z, A-Z, 0-9): \u0000-\u007F
 * Latin Extended: \u0080-\u024F
 * Common punctuation and symbols
 */
const LTR_CHAR_REGEX = /[a-zA-Z0-9\u0000-\u024F]/;

/**
 * Get the first significant character in text (skip whitespace and punctuation)
 * @param text - The text to analyze
 * @returns The first significant character or null
 */
function getFirstSignificantChar(text: string): string | null {
  if (!text || text.trim().length === 0) {
    return null;
  }

  // Remove leading whitespace
  const trimmed = text.trimStart();
  if (trimmed.length === 0) {
    return null;
  }

  // Look for the first letter or digit (skip punctuation)
  const match = trimmed.match(/[a-zA-Z0-9\u0590-\u05FF\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/);
  
  return match ? match[0] : trimmed[0];
}

/**
 * Detect if a text contains RTL characters
 * @param text - The text to check
 * @returns true if the text contains RTL characters
 */
export function isRTLText(text: string): boolean {
  if (!text || text.trim().length === 0) {
    return false;
  }
  
  return RTL_CHAR_REGEX.test(text);
}

/**
 * Detect if a language code is RTL
 * @param langCode - ISO 639-1 language code (e.g., 'ar', 'he', 'en')
 * @returns true if the language is RTL
 */
export function isRTLLanguage(langCode: string | null | undefined): boolean {
  if (!langCode) {
    return false;
  }
  
  // Normalize language code (take first 2 characters, lowercase)
  const normalized = langCode.toLowerCase().substring(0, 2);
  return RTL_LANGUAGES.includes(normalized);
}

/**
 * Get the direction (dir attribute) for a text or language
 * Priority: If text starts with English/Latin characters, it's LTR.
 * Only if text starts with RTL characters, it's RTL.
 * This handles line-by-line: if any line starts with English, prioritize LTR.
 * @param text - Optional text to check for RTL characters
 * @param langCode - Optional language code to check
 * @returns 'rtl' or 'ltr'
 */
export function getTextDirection(
  text?: string | null,
  langCode?: string | null
): 'rtl' | 'ltr' {
  // If we have text, check the starting character
  if (text && text.trim().length > 0) {
    // For multi-line text, check each line starting from the first
    // Priority: if first line starts with English/Latin, it's LTR
    const lines = text.split('\n');
    
    for (const line of lines) {
      const lineTrimmed = line.trim();
      if (lineTrimmed.length > 0) {
        const lineFirstChar = getFirstSignificantChar(line);
        if (lineFirstChar) {
          // Priority to LTR: if line starts with English/Latin character, return LTR
          // This ensures "Hello مرحبا" is treated as LTR
          if (LTR_CHAR_REGEX.test(lineFirstChar)) {
            return 'ltr';
          }
          
          // If line starts with RTL character, return RTL
          // This ensures "مرحبا Hello" is treated as RTL
          if (RTL_CHAR_REGEX.test(lineFirstChar)) {
            return 'rtl';
          }
        }
      }
    }
    
    // Fallback: check if text contains any RTL characters at all
    if (isRTLText(text)) {
      return 'rtl';
    }
  }
  
  // Check language code if no text direction determined
  if (langCode && isRTLLanguage(langCode)) {
    return 'rtl';
  }
  
  // Default to LTR
  return 'ltr';
}

/**
 * Get CSS classes for RTL-aware text styling
 * @param text - Optional text to check for RTL characters
 * @param langCode - Optional language code to check
 * @returns Object with dir, textAlign, and combined className
 */
export function getRTLClasses(
  text?: string | null,
  langCode?: string | null
): {
  dir: 'rtl' | 'ltr';
  textAlign: 'text-right' | 'text-left';
  className: string;
} {
  const direction = getTextDirection(text, langCode);
  const textAlign = direction === 'rtl' ? 'text-right' : 'text-left';
  
  return {
    dir: direction,
    textAlign,
    className: `${textAlign} ${direction === 'rtl' ? 'font-[system-ui]' : ''}`,
  };
}

