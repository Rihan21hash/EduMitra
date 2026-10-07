"use client";

import React from "react";
import Link from "next/link";
import { site, languages, featureFlags, nav } from "@/content";
import { t, Locale } from "@/lib/i18n";
import { BookOpen, BarChart2, MessageSquare, Globe } from "lucide-react";

interface NavbarProps {
  uiLang: Locale;
  onLanguageChange: (lang: Locale) => void;
  activePath?: string;
}

export function Navbar({ uiLang, onLanguageChange, activePath }: NavbarProps) {
  return (
    <header className="sticky top-0 z-40 bg-[var(--surface-card)] border-b border-[var(--border)] shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo & Name */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-[var(--brand)] text-white flex items-center justify-center font-bold text-lg shadow-sm group-hover:bg-[#58222F] transition-colors">
            EM
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg text-[var(--brand)] tracking-tight">
                {t(site.name, uiLang)}
              </span>
              <span className="hidden sm:inline-block text-[11px] font-medium px-2 py-0.5 rounded-full bg-[var(--accent-light)] text-[#8C6013] border border-[#ECD19A]">
                {t(site.event, uiLang)}
              </span>
            </div>
            <p className="text-xs text-[var(--text-muted)] line-clamp-1">
              {t(site.tagline, uiLang)}
            </p>
          </div>
        </Link>

        {/* Navigation Links */}
        <div className="flex items-center gap-2 sm:gap-4">
          <Link
            href="/chat"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              activePath === "/chat"
                ? "bg-[var(--brand-light)] text-[var(--brand)] font-semibold"
                : "text-[var(--text)] hover:bg-[var(--surface)]"
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            <span className="hidden md:inline">{t(nav.chat, uiLang)}</span>
          </Link>

          {featureFlags.progress && (
            <Link
              href="/progress"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                activePath === "/progress"
                  ? "bg-[var(--brand-light)] text-[var(--brand)] font-semibold"
                  : "text-[var(--text)] hover:bg-[var(--surface)]"
              }`}
            >
              <BarChart2 className="w-4 h-4" />
              <span className="hidden md:inline">{t(nav.progress, uiLang)}</span>
            </Link>
          )}

          {/* UI Language Switcher Dropdown */}
          <div className="flex items-center gap-1 bg-[var(--surface)] border border-[var(--border)] rounded-lg p-1 text-xs">
            <Globe className="w-3.5 h-3.5 text-[var(--text-muted)] ml-1 mr-0.5" />
            {languages.map((l) => (
              <button
                key={l.id}
                onClick={() => onLanguageChange(l.id as Locale)}
                className={`px-2 py-1 rounded-md font-medium transition-all ${
                  uiLang === l.id
                    ? "bg-[var(--brand)] text-white shadow-xs"
                    : "text-[var(--text)] hover:bg-[var(--surface-card)]"
                }`}
                title={l.englishName}
              >
                {l.nativeName}
              </button>
            ))}
          </div>
        </div>
      </div>
    </header>
  );
}
