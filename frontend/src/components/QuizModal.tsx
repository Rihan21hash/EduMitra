"use client";

import React, { useState } from "react";
import { quiz, site } from "@/content";
import { t, Locale } from "@/lib/i18n";
import { api, QuizCreateResponse, QuizSubmitResponse } from "@/lib/api";
import {
  X,
  CheckCircle,
  XCircle,
  Award,
  ArrowRight,
  RotateCcw,
  HelpCircle,
} from "lucide-react";

interface QuizModalProps {
  quizData: QuizCreateResponse;
  userId: string;
  uiLang: Locale;
  onClose: () => void;
}

export function QuizModal({ quizData, userId, uiLang, onClose }: QuizModalProps) {
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, number>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<QuizSubmitResponse | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleSelect = (qid: string, optIdx: number) => {
    if (result) return;
    setSelectedAnswers((prev) => ({ ...prev, [qid]: optIdx }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const res = await api.submitQuiz(quizData.quiz_id, {
        user_id: userId,
        phase: quizData.phase || "post",
        answers: selectedAnswers,
      });
      setResult(res);
    } catch (e: any) {
      setSubmitError(e.message || "Failed to submit quiz. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const allAnswered =
    quizData.questions.length > 0 &&
    quizData.questions.every((q) => selectedAnswers[q.id] !== undefined);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/60 backdrop-blur-xs">
      <div className="bg-[var(--surface-card)] rounded-2xl border border-[var(--border)] max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-[var(--border)] flex items-center justify-between bg-[var(--surface)]/50">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base text-[var(--brand)]">
                {t(quiz.title, uiLang)}
              </span>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-[var(--accent-light)] text-[#8C6013] border border-[#ECD19A]">
                {quizData.topic}
              </span>
            </div>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              {t(quiz.subtitle, uiLang)}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[var(--text-muted)] hover:bg-[var(--border)] transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Question content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Result card if submitted */}
          {result && (
            <div className="p-5 rounded-2xl bg-[var(--surface)] border border-[var(--border)] flex flex-col sm:flex-row items-center gap-4 text-center sm:text-left">
              <div className="w-16 h-16 rounded-2xl bg-[var(--brand)] text-white flex flex-col items-center justify-center font-bold shrink-0 shadow-sm">
                <span className="text-xl">
                  {result.score}/{result.total}
                </span>
                <span className="text-[10px] uppercase tracking-wider opacity-80">
                  {result.percentage}%
                </span>
              </div>
              <div className="flex-1">
                <h4 className="font-bold text-base text-[var(--text)]">
                  {result.percentage >= 80
                    ? t(quiz.excellent, uiLang)
                    : result.percentage >= 50
                    ? t(quiz.good, uiLang)
                    : t(quiz.needsReview, uiLang)}
                </h4>
                <p className="text-xs text-[var(--text-muted)] mt-1">
                  Understanding metric recorded to your learning progress dashboard.
                </p>
              </div>
            </div>
          )}

          {/* Question List */}
          {quizData.questions.map((q, idx) => {
            const userPick = selectedAnswers[q.id];
            const review = result?.review.find((r) => r.id === q.id);

            return (
              <div
                key={q.id}
                className="p-4 rounded-xl border border-[var(--border)] bg-white/70 space-y-3"
              >
                <div className="flex items-start gap-2.5">
                  <span className="font-bold text-xs w-5 h-5 rounded-full bg-[var(--brand-light)] text-[var(--brand)] flex items-center justify-center shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <p className="font-semibold text-sm text-[var(--text)] leading-snug">
                    {q.prompt}
                  </p>
                </div>

                <div className="grid grid-cols-1 gap-2 pt-1">
                  {q.options.map((opt, optIdx) => {
                    const isSelected = userPick === optIdx;
                    let optStyle =
                      "border-[var(--border)] bg-[var(--surface)] hover:border-[var(--brand)] text-[var(--text)]";

                    if (result && review) {
                      if (optIdx === review.correct_index) {
                        optStyle =
                          "border-emerald-500 bg-emerald-50 text-emerald-900 font-medium";
                      } else if (isSelected && optIdx !== review.correct_index) {
                        optStyle =
                          "border-red-400 bg-red-50 text-red-900 line-through";
                      } else {
                        optStyle = "border-[var(--border)] opacity-60 text-stone-500";
                      }
                    } else if (isSelected) {
                      optStyle =
                        "border-[var(--brand)] bg-[var(--brand-light)] text-[var(--brand)] font-medium shadow-xs";
                    }

                    return (
                      <button
                        key={optIdx}
                        type="button"
                        onClick={() => handleSelect(q.id, optIdx)}
                        disabled={Boolean(result)}
                        className={`text-left p-3 rounded-xl border text-xs sm:text-sm transition-all flex items-center justify-between cursor-pointer ${optStyle}`}
                      >
                        <span>{opt}</span>
                        {result && review && optIdx === review.correct_index && (
                          <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
                        )}
                        {result &&
                          review &&
                          isSelected &&
                          optIdx !== review.correct_index && (
                            <XCircle className="w-4 h-4 text-red-500 shrink-0" />
                          )}
                      </button>
                    );
                  })}
                </div>

                {/* Explanation text on review */}
                {result && review && (
                  <div className="p-2.5 rounded-lg bg-[var(--surface)] text-xs text-[var(--text-muted)] border border-[var(--border)]">
                    <span className="font-semibold text-[var(--brand)]">Explanation: </span>
                    {review.explanation}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Footer controls */}
        <div className="p-4 border-t border-[var(--border)] bg-[var(--surface)]/50 flex items-center justify-between gap-3">
          <div className="flex-1">
            {submitError && (
              <p className="text-xs text-red-600 font-medium">{submitError}</p>
            )}
          </div>
          {result ? (
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-[var(--brand)] text-white text-xs font-semibold shadow-xs hover:bg-[#58222F] transition-colors cursor-pointer"
            >
              {t(quiz.backToChat, uiLang)}
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || !allAnswered}
              className="px-5 py-2.5 rounded-xl bg-[var(--brand)] text-white text-xs font-semibold shadow-xs hover:bg-[#58222F] disabled:opacity-50 transition-colors cursor-pointer"
            >
              {isSubmitting ? t(quiz.submitting, uiLang) : t(quiz.submit, uiLang)}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
