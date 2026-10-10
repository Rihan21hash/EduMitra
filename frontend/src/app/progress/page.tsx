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
  BarChart3,
  Activity,
  Smile,
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

  const timeline = data?.timeline || [];
  const topics = data?.topics || [];

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

        {/* 4 Summary Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Average Gain */}
          <div className="p-5 rounded-2xl bg-white border border-[var(--border)] flex items-center gap-4 shadow-xs">
            <div className="w-12 h-12 rounded-xl bg-[var(--brand-light)] text-[var(--brand)] flex items-center justify-center shrink-0">
              <TrendingUp className="w-6 h-6" />
            </div>
            <div>
              <div className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">
                {t(progress.improvementMetric, uiLang)}
              </div>
              <div className="text-2xl font-black text-[var(--brand)] mt-0.5">
                {data && data.average_improvement > 0 ? `+${data.average_improvement}` : "0"} {t(progress.pts, uiLang)}
              </div>
            </div>
          </div>

          {/* Quizzes Taken */}
          <div className="p-5 rounded-2xl bg-white border border-[var(--border)] flex items-center gap-4 shadow-xs">
            <div className="w-12 h-12 rounded-xl bg-[var(--accent-light)] text-[#8C6013] flex items-center justify-center shrink-0">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <div className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">
                {t(progress.quizzesTaken, uiLang)}
              </div>
              <div className="text-2xl font-black text-[var(--text)] mt-0.5">
                {data ? data.total_quizzes : 0}
              </div>
            </div>
          </div>

          {/* Questions Asked */}
          <div className="p-5 rounded-2xl bg-white border border-[var(--border)] flex items-center gap-4 shadow-xs">
            <div className="w-12 h-12 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center shrink-0">
              <MessageSquare className="w-6 h-6" />
            </div>
            <div>
              <div className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">
                {t(progress.questionsAsked, uiLang)}
              </div>
              <div className="text-2xl font-black text-[var(--text)] mt-0.5">
                {data?.questions_asked ?? 0}
              </div>
            </div>
          </div>

          {/* Satisfaction Rate */}
          <div className="p-5 rounded-2xl bg-white border border-[var(--border)] flex items-center gap-4 shadow-xs">
            <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
              <Smile className="w-6 h-6" />
            </div>
            <div>
              <div className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">
                {t(progress.satisfaction, uiLang)}
              </div>
              <div className="text-2xl font-black text-emerald-700 mt-0.5">
                {data?.satisfaction_pct ?? 100}%
              </div>
            </div>
          </div>
        </div>

        {/* Learning Analytics SVG Charts */}
        {data && (topics.length > 0 || timeline.length > 0) && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Chart 1: Topic Mastery (Baseline vs Latest) */}
            <div className="p-6 rounded-2xl bg-white border border-[var(--border)] shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-sm text-[var(--text)] flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-[var(--brand)]" />
                  <span>{t(progress.baselineVsLatest, uiLang)}</span>
                </h3>
              </div>

              <div className="space-y-3 pt-2">
                {topics.slice(0, 5).map((top, idx) => {
                  const basePct = top.total > 0 ? ((top.baseline_score ?? 0) / top.total) * 100 : 0;
                  const latestPct = top.total > 0 ? ((top.latest_score ?? 0) / top.total) * 100 : 0;

                  return (
                    <div key={idx} className="space-y-1 text-xs">
                      <div className="flex items-center justify-between font-medium">
                        <span className="text-[var(--text)] line-clamp-1">{top.topic}</span>
                        <span className="text-[var(--text-muted)] font-bold">
                          {top.latest_score}/{top.total}
                        </span>
                      </div>
                      <div className="w-full bg-[var(--surface)] h-3 rounded-full overflow-hidden flex gap-1 p-0.5 border border-[var(--border)]">
                        {/* Baseline Bar */}
                        <div
                          className="bg-stone-300 h-full rounded-full transition-all duration-500"
                          style={{ width: `${basePct}%` }}
                          title={`Baseline: ${top.baseline_score}`}
                        />
                        {/* Latest Bar */}
                        <div
                          className="bg-[var(--brand)] h-full rounded-full transition-all duration-500"
                          style={{ width: `${Math.max(0, latestPct - basePct)}%` }}
                          title={`Latest: ${top.latest_score}`}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Chart 2: Timeline Learning Curve (SVG Line Chart) */}
            <div className="p-6 rounded-2xl bg-white border border-[var(--border)] shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-sm text-[var(--text)] flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-600" />
                  <span>{t(progress.scoreTrend, uiLang)}</span>
                </h3>
              </div>

              {timeline.length > 1 ? (
                <div className="h-40 w-full pt-2 flex items-end">
                  <svg className="w-full h-full overflow-visible" viewBox="0 0 300 100" preserveAspectRatio="none">
                    <polyline
                      fill="none"
                      stroke="var(--brand)"
                      strokeWidth="3"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      points={timeline
                        .map((tl, i) => {
                          const x = (i / (timeline.length - 1)) * 280 + 10;
                          const y = 90 - (tl.percentage / 100) * 80;
                          return `${x},${y}`;
                        })
                        .join(" ")}
                    />
                    {timeline.map((tl, i) => {
                      const x = (i / (timeline.length - 1)) * 280 + 10;
                      const y = 90 - (tl.percentage / 100) * 80;
                      return (
                        <circle
                          key={i}
                          cx={x}
                          cy={y}
                          r="4"
                          className="fill-[var(--accent)] stroke-white stroke-2"
                        />
                      );
                    })}
                  </svg>
                </div>
              ) : (
                <div className="h-40 flex items-center justify-center text-xs text-[var(--text-muted)] italic">
                  Complete 2 or more quizzes to see your score trajectory line chart.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Topic Breakdown Table */}
        <div className="p-6 rounded-2xl bg-white border border-[var(--border)] shadow-xs space-y-4">
          <h2 className="text-base font-bold text-[var(--text)]">
            {t(progress.topicBreakdown, uiLang)}
          </h2>

          {isLoading ? (
            <div className="p-8 text-center text-xs text-[var(--text-muted)] animate-pulse">
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
                      {top.baseline_score !== null && top.baseline_score !== undefined && (
                        <span>
                          {t(progress.preScore, uiLang)}: {top.baseline_score}/{top.total}
                        </span>
                      )}
                      {top.latest_score !== null && top.latest_score !== undefined && (
                        <span>
                          {t(progress.postScore, uiLang)}: {top.latest_score}/{top.total}
                        </span>
                      )}
                      {top.attempts_count ? (
                        <span>
                          ({top.attempts_count} {t(progress.attempts, uiLang)})
                        </span>
                      ) : null}
                    </div>
                  </div>

                  {top.improvement !== null && top.improvement !== undefined && (
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      <TrendingUp className="w-3.5 h-3.5" />
                      <span>
                        {top.improvement >= 0 ? `+${top.improvement}` : top.improvement} {t(progress.pts, uiLang)}
                      </span>
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
