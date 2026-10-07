"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { followUps, chat, levels, subjects, featureFlags } from "@/content";
import { t, Locale } from "@/lib/i18n";
import { api } from "@/lib/api";
import {
  Sparkles,
  RotateCcw,
  BookOpen,
  Languages,
  FileText,
  CheckCircle2,
  AlertTriangle,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Check,
  HelpCircle,
} from "lucide-react";

interface AnswerCardProps {
  responseId: string;
  answerText: string;
  language: string;
  level: string;
  examMarks?: number | null;
  intent?: string;
  subject?: string;
  topic?: string;
  validationPassed?: boolean;
  explainAgainCount?: number;
  uiLang: Locale;
  onFollowUp: (action: string, responseId: string) => void;
  onStartQuiz?: (responseId: string) => void;
  isActionLoading?: boolean;
}

export function AnswerCard({
  responseId,
  answerText,
  language,
  level,
  examMarks,
  intent,
  subject,
  topic,
  validationPassed = true,
  explainAgainCount = 0,
  uiLang,
  onFollowUp,
  onStartQuiz,
  isActionLoading = false,
}: AnswerCardProps) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<number | null>(null);

  const handleCopy = () => {
    navigator.clipboard.writeText(answerText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFeedback = async (rating: number) => {
    if (feedback !== null) return;
    setFeedback(rating);
    try {
      await api.submitFeedback({ response_id: responseId, rating });
    } catch (_) {}
  };

  const levelObj = levels.find((l) => l.id === level.toLowerCase());
  const levelLabel = levelObj ? t(levelObj.label, uiLang) : level;
  const subjectLabel = subject && (subjects as any)[subject] ? t((subjects as any)[subject], uiLang) : subject;

  return (
    <div className="bg-[var(--surface-card)] rounded-2xl border border-[var(--border)] p-5 sm:p-6 shadow-xs transition-shadow hover:shadow-md mb-6">
      {/* Header Badges & Meta */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 mb-4 border-b border-[var(--border)]">
        <div className="flex flex-wrap items-center gap-2">
          {/* Level Badge */}
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-[var(--brand-light)] text-[var(--brand)]">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--brand)]" />
            {levelLabel}
            {examMarks ? ` (${examMarks}M)` : ""}
          </span>

          {/* Language Badge */}
          <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-[var(--surface)] text-[var(--text-muted)] border border-[var(--border)] uppercase">
            {language}
          </span>

          {/* Explain Again Count escalation chip */}
          {explainAgainCount > 0 && (
            <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
              #{explainAgainCount} {t(followUps.explainAgain, uiLang)}
            </span>
          )}
        </div>

        {/* Topic & Subject Metadata */}
        {(subject || topic) && (
          <div className="text-xs text-[var(--text-muted)] flex items-center gap-1.5 font-medium">
            <span>{subjectLabel}</span>
            {topic && <span>·</span>}
            {topic && <span className="text-[var(--text)]">{topic}</span>}
          </div>
        )}
      </div>

      {/* Validation Banner (if failed) */}
      {!validationPassed && (
        <div className="mb-4 flex items-center gap-2 p-3 rounded-xl bg-amber-50/80 border border-amber-200 text-amber-800 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600" />
          <span>{t(chat.verifyNotice, uiLang)}</span>
        </div>
      )}

      {/* Markdown + Math Body */}
      <div
        className="prose prose-stone max-w-none text-[var(--text)] text-[15px] sm:text-[16px] leading-relaxed break-words"
        lang={language}
      >
        <ReactMarkdown
          remarkPlugins={[remarkMath]}
          rehypePlugins={[rehypeKatex]}
          components={{
            p: ({ children }) => <p className="mb-3 leading-relaxed">{children}</p>,
            strong: ({ children }) => <strong className="font-semibold text-[var(--brand)]">{children}</strong>,
            ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1">{children}</ol>,
            h1: ({ children }) => <h1 className="text-lg font-bold text-[var(--brand)] mt-4 mb-2">{children}</h1>,
            h2: ({ children }) => <h2 className="text-base font-bold text-[var(--brand)] mt-3 mb-2">{children}</h2>,
            h3: ({ children }) => <h3 className="text-sm font-semibold text-[var(--text)] mt-2 mb-1">{children}</h3>,
            blockquote: ({ children }) => (
              <blockquote className="border-l-4 border-[var(--accent)] pl-3 italic text-[var(--text-muted)] my-2">
                {children}
              </blockquote>
            ),
          }}
        >
          {answerText}
        </ReactMarkdown>
      </div>

      {/* Action Bar & Follow-ups */}
      <div className="mt-6 pt-4 border-t border-[var(--border)] flex flex-wrap items-center justify-between gap-3">
        {/* Pedagogical Follow-up Buttons */}
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
          <button
            onClick={() => onFollowUp("simplify", responseId)}
            disabled={isActionLoading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] hover:bg-[var(--brand-light)] hover:text-[var(--brand)] hover:border-[var(--brand)] transition-colors disabled:opacity-50 cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5 text-[var(--accent)]" />
            {t(followUps.simplify, uiLang)}
          </button>

          <button
            onClick={() => onFollowUp("explain_again", responseId)}
            disabled={isActionLoading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] hover:bg-[var(--brand-light)] hover:text-[var(--brand)] hover:border-[var(--brand)] transition-colors disabled:opacity-50 cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5 text-sky-600" />
            {t(followUps.explainAgain, uiLang)}
          </button>

          <button
            onClick={() => onFollowUp("example", responseId)}
            disabled={isActionLoading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] hover:bg-[var(--brand-light)] hover:text-[var(--brand)] hover:border-[var(--brand)] transition-colors disabled:opacity-50 cursor-pointer"
          >
            <BookOpen className="w-3.5 h-3.5 text-emerald-600" />
            {t(followUps.example, uiLang)}
          </button>

          <button
            onClick={() => onFollowUp("summarize", responseId)}
            disabled={isActionLoading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--surface)] text-[var(--text)] border border-[var(--border)] hover:bg-[var(--brand-light)] hover:text-[var(--brand)] hover:border-[var(--brand)] transition-colors disabled:opacity-50 cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5 text-purple-600" />
            {t(followUps.summarize, uiLang)}
          </button>

          {featureFlags.quiz && onStartQuiz && (
            <button
              onClick={() => onStartQuiz(responseId)}
              disabled={isActionLoading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[var(--accent-light)] text-[#8C6013] border border-[#ECD19A] hover:bg-[#F5E6C8] transition-colors disabled:opacity-50 cursor-pointer"
            >
              <HelpCircle className="w-3.5 h-3.5" />
              {t(followUps.quiz, uiLang)}
            </button>
          )}
        </div>

        {/* Copy & Feedback controls */}
        <div className="flex items-center gap-1 text-[var(--text-muted)]">
          <button
            onClick={handleCopy}
            className="p-1.5 rounded-lg hover:bg-[var(--surface)] hover:text-[var(--text)] transition-colors cursor-pointer"
            title={copied ? t(followUps.copied, uiLang) : t(followUps.copy, uiLang)}
          >
            {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
          </button>

          <button
            onClick={() => handleFeedback(1)}
            disabled={feedback !== null}
            className={`p-1.5 rounded-lg hover:bg-[var(--surface)] transition-colors cursor-pointer ${
              feedback === 1 ? "text-emerald-600 font-bold" : "hover:text-emerald-600"
            }`}
            title={t(followUps.helpful, uiLang)}
          >
            <ThumbsUp className="w-4 h-4" />
          </button>

          <button
            onClick={() => handleFeedback(-1)}
            disabled={feedback !== null}
            className={`p-1.5 rounded-lg hover:bg-[var(--surface)] transition-colors cursor-pointer ${
              feedback === -1 ? "text-rose-600 font-bold" : "hover:text-rose-600"
            }`}
            title={t(followUps.notHelpful, uiLang)}
          >
            <ThumbsDown className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
