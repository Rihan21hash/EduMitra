"use client";

import React from "react";
import { footer, site, team, links } from "@/content";
import { t, Locale } from "@/lib/i18n";

interface FooterProps {
  uiLang: Locale;
}

export function Footer({ uiLang }: FooterProps) {
  return (
    <footer className="mt-auto border-t border-[var(--border)] bg-[var(--surface-card)] py-8 text-xs text-[var(--text-muted)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <p className="font-medium text-[var(--text)]">
            {t(footer.copyright, uiLang)}
          </p>
          <p className="mt-1">
            {t(site.institution, uiLang)}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <span className="font-semibold text-[var(--brand)]">
            {team.name}:
          </span>
          {team.members.map((m, idx) => (
            <span key={idx} className="hover:text-[var(--text)]">
              {m.name}
            </span>
          ))}
        </div>
      </div>
    </footer>
  );
}
