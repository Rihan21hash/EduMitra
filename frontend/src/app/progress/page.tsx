"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { site, progress, featureFlags } from "@/content";
import { t, Locale } from "@/lib/i18n";
import { validateContent } from "@/lib/validateContent";
import { api, ProgressResponse } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import {
  TrendingUp,
  Award,
  BookOpen,
  ArrowRight,
  CheckCircle2,
  HelpCircle,
  MessageSquare,
} from "lucide-react";

export default function ProgressPage() {
  const [uiLang, setUiLang] = useState<Locale>("mr");
  const [data, setData] = useState<ProgressResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    validateContent();
    const saved = localStorage.getItem("edumitra_ui_lang") as Locale;
    if (saved && ["en", "hi", "mr"].includes(saved)) {
      setUiLang(saved);
    }

    const uid = localStorage.getItem("edumitra_user_id");
    if (uid) {
      api
        .getProgress(uid)
        .then((res) => setData(res))
        .catch((_) => {})
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const handleLanguageChange = (lang: Locale) => {
    setUiLang(lang);
    localStorage.setItem("edumitra_ui_lang", lang);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[var(--surface)] text-[var(--text)]">
      <Navbar uiLang={uiLang} onLanguageChange={handleLanguageChange} activePath="/progress" />

      <main className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-10 space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[var(--brand)]">
            {t(progress.title, uiLang)}
          </h1>
          <p className="text-xs sm:text-sm text-[var(--text-muted)] mt-1.5">
            {t(progress.subtitle, uiLang)}
          </p>
        </div>

        {/* Top Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-6 rounded-2xl bg-white border border-[var(--border)] flex items-center gap-5 shadow-xs">
            <div className="w-14 h-14 rounded-2xl bg-[var(--brand-light)] text-[var(--brand)] flex items-center justify-center shrink-0">
              <TrendingUp className="w-7 h-7" />
            </div>
            <div>
              <div className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">
                {t(progress.improvementMetric, uiLang)}
              </div>
              <div className="text-3xl font-black text-[var(--brand)] mt-1">
                {data && data.average_improvement > 0 ? `+${data.average_improvement}` : "0"} pts
              </div>
              <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
                (post-quiz score − pre-quiz score)
              </p>
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-white border border-[var(--border)] flex items-center gap-5 shadow-xs">
            <div className="w-14 h-14 rounded-2xl bg-[var(--accent-light)] text-[#8C6013] flex items-center justify-center shrink-0">
              <Award className="w-7 h-7" />
            </div>
            <div>
              <div className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">
                {t(progress.quizzesTaken, uiLang)}
              </div>
              <div className="text-3xl font-black text-[var(--text)] mt-1">
                {data ? data.total_quizzes : 0}
              </div>
              <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
                Evaluated concept checkpoints
              </p>
            </div>
          </div>
        </div>

        {/* Topic Breakdown */}
        <div className="p-6 rounded-2xl bg-white border border-[var(--border)] shadow-xs space-y-4">
          <h2 className="text-base font-bold text-[var(--text)]">
            {t(progress.topicBreakdown, uiLang)}
          </h2>

          {isLoading ? (
            <div className="p-8 text-center text-xs text-[var(--text-muted)]">
              {t(progress.loading, uiLang)}
            </div>
          ) : !data || data.topics.length === 0 ? (
            <div className="p-8 text-center space-y-4">
              <p className="text-xs text-[var(--text-muted)] italic">
                {t(progress.noData, uiLang)}
              </p>
              <Link
                href="/chat"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--brand)] text-white text-xs font-semibold shadow-xs hover:bg-[#58222F] transition-colors cursor-pointer"
              >
                <MessageSquare className="w-3.5 h-3.5" />
                <span>{t(progress.goToChat, uiLang)}</span>
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-[var(--border)]">
              {data.topics.map((top, idx) => (
                <div key={idx} className="py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div>
                    <h3 className="font-semibold text-sm text-[var(--text)]">
                      {top.topic}
                    </h3>
                    <div className="flex items-center gap-3 text-xs text-[var(--text-muted)] mt-1">
                      {top.pre_score !== null && (
                        <span>
                          {t(progress.preScore, uiLang)}: {top.pre_score}/{top.total}
                        </span>
                      )}
                      {top.post_score !== null && (
                        <span>
                          {t(progress.postScore, uiLang)}: {top.post_score}/{top.total}
                        </span>
                      )}
                    </div>
                  </div>

                  {top.improvement !== null && (
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      <TrendingUp className="w-3.5 h-3.5" />
                      <span>+{top.improvement} pts</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      <Footer uiLang={uiLang} />
    </div>
  );
}
