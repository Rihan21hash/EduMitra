"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { site, landing, featureFlags, theme } from "@/content";
import { t, Locale } from "@/lib/i18n";
import { validateContent } from "@/lib/validateContent";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import {
  ArrowRight,
  BookOpen,
  Sparkles,
  Award,
  Layers,
  ShieldCheck,
  Cpu,
  BarChart2,
  CheckCircle2,
} from "lucide-react";

export default function LandingPage() {
  const [uiLang, setUiLang] = useState<Locale>("mr");

  useEffect(() => {
    validateContent();
    const saved = localStorage.getItem("edumitra_ui_lang") as Locale;
    if (saved && ["en", "hi", "mr"].includes(saved)) {
      setUiLang(saved);
    }
  }, []);

  const handleLanguageChange = (lang: Locale) => {
    setUiLang(lang);
    localStorage.setItem("edumitra_ui_lang", lang);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[var(--surface)] text-[var(--text)]">
      <Navbar uiLang={uiLang} onLanguageChange={handleLanguageChange} activePath="/" />

      {/* Hero Section */}
      <section className="relative py-16 sm:py-24 px-4 sm:px-6 lg:px-8 border-b border-[var(--border)] bg-gradient-to-b from-white to-[var(--surface)]">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--brand-light)] text-[var(--brand)] text-xs font-semibold border border-[#E9D6DC]">
            <Sparkles className="w-3.5 h-3.5 text-[var(--accent)]" />
            <span>{t(site.fullName, uiLang)}</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold text-[var(--text)] tracking-tight leading-tight">
            {t(landing.heroTitle, uiLang)}
          </h1>

          <p className="text-base sm:text-lg text-[var(--text-muted)] max-w-2xl mx-auto leading-relaxed">
            {t(landing.heroSubtitle, uiLang)}
          </p>

          <div className="pt-4 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-[var(--brand)] text-white font-semibold text-sm shadow-md hover:bg-[#58222F] transition-all cursor-pointer"
            >
              <span>{t(landing.startLearning, uiLang)}</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            {featureFlags.progress && (
              <Link
                href="/progress"
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-white text-[var(--text)] font-semibold text-sm border border-[var(--border)] hover:bg-[var(--surface)] transition-all cursor-pointer"
              >
                <BarChart2 className="w-4 h-4 text-[var(--brand)]" />
                <span>{t(landing.viewProgress, uiLang)}</span>
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* 5-Step User Journey */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto w-full">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="text-2xl sm:text-3xl font-bold text-[var(--brand)]">
            {t(landing.howItWorksTitle, uiLang)}
          </h2>
          <p className="text-sm text-[var(--text-muted)] mt-2">
            {t(landing.howItWorksSubtitle, uiLang)}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {landing.steps.map((s) => (
            <div
              key={s.step}
              className="p-5 rounded-2xl bg-white border border-[var(--border)] relative flex flex-col justify-between shadow-xs hover:border-[var(--brand)] transition-all"
            >
              <div>
                <span className="w-8 h-8 rounded-xl bg-[var(--brand-light)] text-[var(--brand)] font-bold text-xs flex items-center justify-center mb-4">
                  0{s.step}
                </span>
                <h3 className="font-bold text-base text-[var(--text)] mb-2">
                  {t(s.title, uiLang)}
                </h3>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                  {t(s.desc, uiLang)}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Key Features */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 border-y border-[var(--border)] bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-[var(--text)]">
              {t(landing.featuresTitle, uiLang)}
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {landing.features.map((f, i) => (
              <div
                key={i}
                className="p-6 rounded-2xl bg-[var(--surface)] border border-[var(--border)] space-y-3"
              >
                <div className="w-10 h-10 rounded-xl bg-[var(--brand-light)] text-[var(--brand)] flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5 text-[var(--brand)]" />
                </div>
                <h3 className="font-bold text-base text-[var(--text)]">
                  {t(f.title, uiLang)}
                </h3>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                  {t(f.desc, uiLang)}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Impact Numbers */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto w-full">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h2 className="text-2xl sm:text-3xl font-bold text-[var(--brand)]">
            {t(landing.impactTitle, uiLang)}
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {landing.impacts.map((imp, idx) => (
            <div
              key={idx}
              className="p-8 rounded-2xl bg-white border border-[var(--border)] text-center space-y-2 shadow-xs"
            >
              <div className="text-4xl sm:text-5xl font-black text-[var(--brand)]">
                {imp.stat}
              </div>
              <div className="font-bold text-sm text-[var(--text)]">
                {t(imp.label, uiLang)}
              </div>
              <div className="text-xs text-[var(--text-muted)]">
                {t(imp.sub, uiLang)}
              </div>
            </div>
          ))}
        </div>
      </section>

      <Footer uiLang={uiLang} />
    </div>
  );
}
