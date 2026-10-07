export type Locale = "en" | "hi" | "mr";

export interface LocalizedString {
  en: string;
  hi: string;
  mr: string;
}

/**
 * Resolves a trilingual string object { en, hi, mr } to the requested language.
 * Falls back to English, then the first available string.
 */
export function t(
  content: LocalizedString | string | undefined | null,
  lang: Locale = "mr"
): string {
  if (!content) return "";
  if (typeof content === "string") return content;
  return content[lang] || content.en || content.mr || content.hi || "";
}
