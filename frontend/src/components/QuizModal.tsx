"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { quiz, followUps, nav } from "@/content";
import { t, Locale } from "@/lib/i18n";
import { api, QuizCreateResponse, QuizSubmitResponse } from "@/lib/api";
import {
  X,
  CheckCircle,
  XCircle,
  Award,
  ArrowRight,
  ArrowLeft,
  RotateCcw,
  Sparkles,
  TrendingUp,
  HelpCircle,
} from "lucide-react";

interface QuizModalProps {
  quizData: QuizCreateResponse;
  userId: string;
  uiLang: Locale;
  onClose: () => void;
  onExplainAgain?: () => void;
}

export function QuizModal({
  quizData,
  userId,
  uiLang,
  onClose,
  onExplainAgain,
}: QuizModalProps) {
  const router = useRouter();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, number>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<QuizSubmitResponse | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const totalQuestions = quizData.questions.length;
  const currentQ = quizData.questions[currentIndex];

  const handleSelect = (qid: string, optIdx: number) => {
    if (result) return;
    setSelectedAnswers((prev) => ({ ...prev, [qid]: optIdx }));
  };

  const handleNext = () => {
    if (currentIndex < totalQuestions - 1) {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
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

  const handleRetake = () => {
    setSelectedAnswers({});
    setResult(null);
    setCurrentIndex(0);
  };

  const allAnswered =
    totalQuestions > 0 &&
    quizData.questions.every((q) => selectedAnswers[q.id] !== undefined);

  const progressPct = totalQuestions > 0 ? ((currentIndex + 1) / totalQuestions) * 100 : 100;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/60 backdrop-blur-xs animate-fade-in">
      <div className="bg-[var(--surface-card)] rounded-2xl border border-[var(--border)] max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-[var(--border)] flex items-center justify-between bg-[var(--surface)]/50">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base text-[var(--brand)]">
                {t(quiz.title, uiLang)}
              </span>
              <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-[var(--accent-light)] text-[#8C6013] border border-[#ECD19A]">
                {quizData.topic}
              </span>
              {quizData.phase === "pre" ? (
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">
                  {t(quiz.preQuizBadge, uiLang)}
                </span>
              ) : (
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                  {t(quiz.postQuizBadge, uiLang)}
                </span>
              )}
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

        {/* Progress Bar (Before Results) */}
        {!result && totalQuestions > 0 && (
          <div className="w-full bg-[var(--border)] h-1.5 overflow-hidden">
            <div
              className="bg-[var(--brand)] h-full transition-all duration-300 ease-out"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        )}

        {/* Main Content Area */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Summary / Result View */}
          {result ? (
            <div className="space-y-6">
              {/* Score Header Card */}
              <div className="p-6 rounded-2xl bg-[var(--surface)] border border-[var(--border)] flex flex-col sm:flex-row items-center gap-5 text-center sm:text-left shadow-xs">
                <div className="w-20 h-20 rounded-2xl bg-[var(--brand)] text-white flex flex-col items-center justify-center font-bold shrink-0 shadow-md">
                  <span className="text-2xl">
                    {result.score}/{result.total}
                  </span>
                  <span className="text-[11px] uppercase tracking-wider opacity-90">
                    {result.percentage}%
                  </span>
                </div>
                <div className="flex-1">
                  <h4 className="font-bold text-lg text-[var(--text)]">
                    {result.percentage >= 80
                      ? t(quiz.excellent, uiLang)
                      : result.percentage >= 50
                      ? t(quiz.good, uiLang)
                      : t(quiz.needsReview, uiLang)}
                  </h4>

                  {result.improvement_delta !== undefined && result.improvement_delta !== null && (
                    <div className="mt-1.5 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                      <TrendingUp className="w-3.5 h-3.5" />
                      <span>
                        {t(quiz.improvementNotice, uiLang)}{" "}
                        {result.improvement_delta >= 0 ? `+${result.improvement_delta}` : result.improvement_delta}
                      </span>
                    </div>
                  )}

                  <p className="text-xs text-[var(--text-muted)] mt-1.5">
                    Your assessment has been recorded to your learning analytics dashboard.
                  </p>
                </div>
              </div>

              {/* Review of each question */}
              <div className="space-y-4">
                {quizData.questions.map((q, idx) => {
                  const userPick = selectedAnswers[q.id];
                  const review = result.review.find((r) => r.id === q.id);
                  const isCorrect = userPick !== undefined && review && userPick === review.correct_index;

                  return (
                    <div
                      key={q.id}
                      className={`p-4 rounded-xl border ${
                        isCorrect
                          ? "border-emerald-200 bg-emerald-50/40"
                          : "border-red-200 bg-red-50/40"
                      } space-y-2.5`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="font-semibold text-sm text-[var(--text)]">
                          {idx + 1}. {q.prompt}
                        </p>
                        {isCorrect ? (
                          <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        ) : (
                          <XCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
                        )}
                      </div>

                      <div className="grid grid-cols-1 gap-1.5">
                        {q.options.map((opt, optIdx) => {
                          const isPicked = userPick === optIdx;
                          const isAnswerCorrect = review && optIdx === review.correct_index;

                          let style = "border-[var(--border)] bg-white text-xs p-2.5 rounded-lg";
                          if (isAnswerCorrect) {
                            style = "border-emerald-500 bg-emerald-100 text-emerald-900 font-semibold";
                          } else if (isPicked && !isAnswerCorrect) {
                            style = "border-red-400 bg-red-100 text-red-900 line-through";
                          }

                          return (
                            <div key={optIdx} className={`border flex items-center justify-between ${style}`}>
                              <span>{opt}</span>
                            </div>
                          );
                        })}
                      </div>

                      {review && (
                        <div className="p-2.5 rounded-lg bg-white/80 border border-[var(--border)] text-xs text-[var(--text-muted)]">
                          <strong className="text-[var(--brand)]">Explanation: </strong>
                          {review.explanation}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            /* Single Question View (One at a time) */
            currentQ && (
              <div className="space-y-5">
                {/* Question Header */}
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[var(--brand)] uppercase tracking-wider">
                    {t(quiz.questionCounter, uiLang)} {currentIndex + 1} {t(quiz.of, uiLang)}{" "}
                    {totalQuestions}
                  </span>
                  <span className="text-xs text-[var(--text-muted)] font-medium">
                    {selectedAnswers[currentQ.id] !== undefined ? "Answered ✓" : "Choose one option"}
                  </span>
                </div>

                <div className="p-4 sm:p-5 rounded-2xl bg-[var(--surface)] border border-[var(--border)]">
                  <p className="font-bold text-base sm:text-lg text-[var(--text)] leading-snug">
                    {currentQ.prompt}
                  </p>
                </div>

                {/* Options */}
                <div className="grid grid-cols-1 gap-2.5">
                  {currentQ.options.map((opt, optIdx) => {
                    const isSelected = selectedAnswers[currentQ.id] === optIdx;

                    return (
                      <button
                        key={optIdx}
                        type="button"
                        onClick={() => handleSelect(currentQ.id, optIdx)}
                        className={`text-left p-3.5 sm:p-4 rounded-xl border text-sm transition-all flex items-center justify-between cursor-pointer ${
                          isSelected
                            ? "border-[var(--brand)] bg-[var(--brand-light)] text-[var(--brand)] font-semibold shadow-xs"
                            : "border-[var(--border)] bg-[var(--surface-card)] hover:border-[var(--brand)] hover:bg-[var(--surface)] text-[var(--text)]"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span
                            className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                              isSelected
                                ? "bg-[var(--brand)] text-white"
                                : "bg-[var(--surface)] text-[var(--text-muted)] border border-[var(--border)]"
                            }`}
                          >
                            {String.fromCharCode(65 + optIdx)}
                          </span>
                          <span>{opt}</span>
                        </div>
                        {isSelected && <CheckCircle className="w-4 h-4 text-[var(--brand)]" />}
                      </button>
                    );
                  })}
                </div>
              </div>
            )
          )}
        </div>

        {/* Footer controls */}
        <div className="p-4 border-t border-[var(--border)] bg-[var(--surface)]/50 flex flex-wrap items-center justify-between gap-3">
          {result ? (
            /* Result Actions: Retake, Explain Again, View Progress, Back to Chat */
            <div className="flex flex-wrap items-center justify-between w-full gap-2">
              <div className="flex items-center gap-2">
                <button
                  onClick={handleRetake}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-[var(--border)] bg-white text-xs font-semibold text-[var(--text)] hover:bg-[var(--surface)] transition-colors cursor-pointer"
                >
                  <RotateCcw className="w-3.5 h-3.5 text-sky-600" />
                  {t(quiz.retake, uiLang)}
                </button>

                {onExplainAgain && result.percentage < 100 && (
                  <button
                    onClick={() => {
                      onClose();
                      onExplainAgain();
                    }}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-amber-300 bg-amber-50 text-xs font-semibold text-amber-900 hover:bg-amber-100 transition-colors cursor-pointer"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                    {t(quiz.explainAgainPrompt, uiLang)}
                  </button>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    onClose();
                    router.push("/progress");
                  }}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-[var(--brand)] text-[var(--brand)] text-xs font-semibold hover:bg-[var(--brand-light)] transition-colors cursor-pointer"
                >
                  <TrendingUp className="w-3.5 h-3.5" />
                  {t(quiz.viewProgress, uiLang)}
                </button>

                <button
                  onClick={onClose}
                  className="px-5 py-2 rounded-xl bg-[var(--brand)] text-white text-xs font-semibold shadow-xs hover:bg-[#58222F] transition-colors cursor-pointer"
                >
                  {t(quiz.backToChat, uiLang)}
                </button>
              </div>
            </div>
          ) : (
            /* Navigation / Submit Controls */
            <div className="flex items-center justify-between w-full">
              <button
                type="button"
                onClick={handlePrev}
                disabled={currentIndex === 0}
                className="inline-flex items-center gap-1 px-3 py-2 rounded-xl border border-[var(--border)] text-xs font-medium text-[var(--text)] hover:bg-[var(--surface)] disabled:opacity-40 disabled:pointer-events-none transition-colors cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>

              <div className="flex items-center gap-2">
                {currentIndex < totalQuestions - 1 ? (
                  <button
                    type="button"
                    onClick={handleNext}
                    disabled={selectedAnswers[currentQ?.id] === undefined}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[var(--brand)] text-white text-xs font-semibold shadow-xs hover:bg-[#58222F] disabled:opacity-50 transition-colors cursor-pointer"
                  >
                    <span>{t(quiz.nextQuestion, uiLang)}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={handleSubmit}
                    disabled={isSubmitting || !allAnswered}
                    className="px-5 py-2 rounded-xl bg-[var(--brand)] text-white text-xs font-semibold shadow-xs hover:bg-[#58222F] disabled:opacity-50 transition-colors cursor-pointer"
                  >
                    {isSubmitting ? t(quiz.submitting, uiLang) : t(quiz.submit, uiLang)}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
