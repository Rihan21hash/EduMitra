"use client";

import React, { useState, useEffect, useRef } from "react";
import { chat, levels, examMarks, languages, limits, featureFlags, errors } from "@/content";
import { t, Locale } from "@/lib/i18n";
import { startSpeechRecognition, isSpeechSupported } from "@/lib/speech";
import { Send, Mic, MicOff, Sparkles, AlertCircle } from "lucide-react";

interface ComposerProps {
  onSend: (text: string, level: string, examMarks: number | null, langOverride: string) => void;
  isLoading: boolean;
  uiLang: Locale;
}

export function Composer({ onSend, isLoading, uiLang }: ComposerProps) {
  const [text, setText] = useState("");
  const [selectedLevel, setSelectedLevel] = useState("beginner");
  const [selectedMarks, setSelectedMarks] = useState<number>(5);
  const [langOverride, setLangOverride] = useState("auto");
  const [isListening, setIsListening] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const speechRecognizerRef = useRef<{ stop: () => void } | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const maxChars = limits.maxQuestionChars || 1000;
  const charsLeft = maxChars - text.length;

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (isLoading) return;
    const trimmed = text.trim();
    if (!trimmed) {
      setErrorMessage(t(errors.emptyInput, uiLang));
      return;
    }
    if (trimmed.length > maxChars) {
      setErrorMessage(t(errors.tooLong, uiLang));
      return;
    }

    setErrorMessage("");
    onSend(
      trimmed,
      selectedLevel,
      selectedLevel === "exam" ? selectedMarks : null,
      langOverride
    );
    setText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const toggleVoiceInput = () => {
    if (isListening) {
      speechRecognizerRef.current?.stop();
      setIsListening(false);
      return;
    }

    const currentLangObj = languages.find((l) => l.id === (langOverride === "auto" ? uiLang : langOverride));
    const locale = currentLangObj?.speechLocale || "mr-IN";

    const recognizer = startSpeechRecognition({
      locale,
      onResult: (transcript) => {
        setText((prev) => (prev ? `${prev} ${transcript}` : transcript));
        setIsListening(false);
      },
      onError: (err) => {
        setErrorMessage(t(chat.voiceUnsupported, uiLang));
        setIsListening(false);
      },
      onEnd: () => {
        setIsListening(false);
      },
    });

    if (recognizer) {
      speechRecognizerRef.current = recognizer;
      setIsListening(true);
      setErrorMessage("");
    }
  };

  return (
    <div className="bg-[var(--surface-card)] border-t border-[var(--border)] p-4 sm:p-5 shadow-lg">
      <div className="max-w-4xl mx-auto space-y-3">
        {/* Error Notice */}
        {errorMessage && (
          <div className="flex items-center gap-2 p-2.5 rounded-lg bg-red-50 text-red-700 text-xs border border-red-200">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Level & Mode Selection Tabs */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
            <span className="font-semibold text-[var(--text-muted)] mr-1">
              {t(chat.levelLabel, uiLang)}
            </span>
            {levels
              .filter((l) => l.id !== "exam" || featureFlags.examMode)
              .map((lvl) => (
                <button
                  key={lvl.id}
                  type="button"
                  onClick={() => setSelectedLevel(lvl.id)}
                  className={`px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer ${
                    selectedLevel === lvl.id
                      ? "bg-[var(--brand)] text-white shadow-xs"
                      : "bg-[var(--surface)] text-[var(--text)] hover:bg-[var(--brand-light)] hover:text-[var(--brand)]"
                  }`}
                >
                  {t(lvl.label, uiLang)}
                </button>
              ))}
          </div>

          {/* Exam Marks Selector (Only visible if Exam mode is active) */}
          {selectedLevel === "exam" && featureFlags.examMode && (
            <div className="flex items-center gap-1.5 bg-[var(--surface)] p-1 rounded-lg border border-[var(--border)]">
              <span className="text-[var(--text-muted)] font-medium px-1">
                {t(chat.marksLabel, uiLang)}
              </span>
              {examMarks.map((m) => (
                <button
                  key={m.marks}
                  type="button"
                  onClick={() => setSelectedMarks(m.marks)}
                  className={`px-2 py-0.5 rounded-md font-semibold transition-colors cursor-pointer ${
                    selectedMarks === m.marks
                      ? "bg-[var(--accent)] text-stone-900"
                      : "text-[var(--text)] hover:bg-[var(--surface-card)]"
                  }`}
                >
                  {t(m.label, uiLang)}
                </button>
              ))}
            </div>
          )}

          {/* Target Language Override Selector */}
          <div className="flex items-center gap-1.5">
            <select
              value={langOverride}
              onChange={(e) => setLangOverride(e.target.value)}
              className="bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] text-xs rounded-lg px-2.5 py-1.5 focus:outline-hidden focus:ring-1 focus:ring-[var(--brand)] cursor-pointer"
            >
              <option value="auto">{t(chat.autoLanguage, uiLang)}</option>
              {languages.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.nativeName} ({l.englishName})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Text Input Box */}
        <div className="relative rounded-2xl border border-[var(--border)] bg-[var(--surface)] focus-within:border-[var(--brand)] focus-within:ring-2 focus-within:ring-[var(--brand-light)] transition-all">
          <textarea
            ref={textareaRef}
            rows={2}
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              if (errorMessage) setErrorMessage("");
            }}
            onKeyDown={handleKeyDown}
            placeholder={
              isListening
                ? t(chat.voiceListening, uiLang)
                : t(chat.placeholder, uiLang)
            }
            disabled={isLoading}
            className="w-full resize-none p-3.5 pr-24 text-[15px] sm:text-[16px] text-[var(--text)] placeholder-[var(--text-muted)] bg-transparent outline-hidden"
          />

          {/* Action buttons inside composer */}
          <div className="absolute right-2.5 bottom-2.5 flex items-center gap-1.5">
            {/* Mic button */}
            {featureFlags.voiceInput && isSpeechSupported() && (
              <button
                type="button"
                onClick={toggleVoiceInput}
                disabled={isLoading}
                className={`p-2 rounded-xl transition-colors cursor-pointer ${
                  isListening
                    ? "bg-red-500 text-white animate-pulse"
                    : "text-[var(--text-muted)] hover:bg-[var(--surface-card)] hover:text-[var(--brand)]"
                }`}
                title="Voice Input"
              >
                {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>
            )}

            {/* Send Button */}
            <button
              type="button"
              onClick={() => handleSubmit()}
              disabled={isLoading || !text.trim()}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-[var(--brand)] text-white font-medium text-xs shadow-xs hover:bg-[#58222F] disabled:opacity-50 disabled:cursor-not-allowed transition-all cursor-pointer"
            >
              {isLoading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>{t(chat.thinking, uiLang)}</span>
                </>
              ) : (
                <>
                  <span>{t(chat.send, uiLang)}</span>
                  <Send className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Footer character counter */}
        <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)] px-1">
          <span className="italic">
            Shift + Enter for new line · Enter to send
          </span>
          <span className={charsLeft < 50 ? "text-amber-600 font-semibold" : ""}>
            {text.length} / {maxChars} {t(chat.charsRemaining, uiLang)}
          </span>
        </div>
      </div>
    </div>
  );
}
