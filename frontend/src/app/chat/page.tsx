"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { site, chat, exampleQuestions, errors, levels, subjects, featureFlags, nav } from "@/content";
import { t, Locale } from "@/lib/i18n";
import { validateContent } from "@/lib/validateContent";
import { api, ConversationSummary, MessageItem, QuizCreateResponse } from "@/lib/api";
import { Sidebar } from "@/components/Sidebar";
import { Composer } from "@/components/Composer";
import { AnswerCard } from "@/components/AnswerCard";
import { QuizModal } from "@/components/QuizModal";
import {
  Menu,
  Sparkles,
  RotateCcw,
  AlertCircle,
  HelpCircle,
  ArrowLeft,
  ChevronRight,
  BookOpen,
  Square,
  Loader2,
} from "lucide-react";

interface StreamingState {
  rawText: string;
  partialText: string;
  language: string;
  level: string;
  examMarks?: number | null;
  subject?: string;
  topic?: string;
}

export default function ChatPage() {
  const [uiLang, setUiLang] = useState<Locale>("mr");
  const [userId, setUserId] = useState<string>("");
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isActionLoading, setIsActionLoading] = useState<boolean>(false);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [streamingState, setStreamingState] = useState<StreamingState | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastFailedAction, setLastFailedAction] = useState<(() => void) | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false);
  const [activeQuiz, setActiveQuiz] = useState<QuizCreateResponse | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const loadHistory = useCallback(async (uid: string) => {
    try {
      const history = await api.getHistory(uid);
      setConversations(history);
    } catch (_) {}
  }, []);

  // Initialize guest user and load history
  useEffect(() => {
    validateContent();
    const savedLang = localStorage.getItem("edumitra_ui_lang") as Locale;
    if (savedLang && ["en", "hi", "mr"].includes(savedLang)) {
      setUiLang(savedLang);
    }

    async function initUser() {
      let uid = localStorage.getItem("edumitra_user_id") || "";
      if (!uid) {
        try {
          const user = await api.createUser("mr", "beginner");
          uid = user.id;
          localStorage.setItem("edumitra_user_id", uid);
        } catch (_) {
          uid = "guest-" + Math.random().toString(36).substring(2, 9);
          localStorage.setItem("edumitra_user_id", uid);
        }
      }
      setUserId(uid);
      loadHistory(uid);
    }

    initUser();
  }, [loadHistory]);

  // Auto-scroll to bottom on new content
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingState, isLoading]);

  const handleSelectConversation = async (convId: string) => {
    setActiveConversationId(convId);
    setErrorMessage(null);
    setIsLoading(true);
    try {
      const detail = await api.getConversation(convId);
      setMessages(detail.messages || []);
    } catch (e: any) {
      setErrorMessage(t(errors.generic, uiLang));
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setActiveConversationId(null);
    setMessages([]);
    setStreamingState(null);
    setIsStreaming(false);
    setErrorMessage(null);
  };

  const handleDeleteConversation = async (convId: string) => {
    try {
      await api.deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConversationId === convId) {
        handleNewChat();
      }
    } catch (_) {}
  };

  const handleLanguageChange = (lang: Locale) => {
    setUiLang(lang);
    localStorage.setItem("edumitra_ui_lang", lang);
  };

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    setIsLoading(false);
  };

  // Submit question with streaming support
  const handleSend = async (
    text: string,
    level: string,
    examMarks: number | null,
    langOverride: string
  ) => {
    if (!userId) return;
    setIsLoading(true);
    setErrorMessage(null);

    // Streaming mode
    if (featureFlags.streaming) {
      const controller = new AbortController();
      abortControllerRef.current = controller;
      setIsStreaming(true);

      const streamInit: StreamingState = {
        rawText: text,
        partialText: "",
        language: langOverride !== "auto" ? langOverride : uiLang,
        level,
        examMarks,
      };
      setStreamingState(streamInit);

      let accumulated = "";
      let metaInfo: any = {};

      try {
        await api.askQuestionStream(
          {
            user_id: userId,
            conversation_id: activeConversationId,
            text,
            level,
            exam_marks: examMarks,
            language_override: langOverride,
          },
          {
            onMeta: (meta) => {
              metaInfo = meta;
              if (meta.conversation_id && !activeConversationId) {
                setActiveConversationId(meta.conversation_id);
                loadHistory(userId);
              }
              setStreamingState((prev) =>
                prev
                  ? {
                      ...prev,
                      language: meta.language || prev.language,
                      subject: meta.subject,
                      topic: meta.topic,
                    }
                  : null
              );
            },
            onToken: (token) => {
              accumulated += token;
              setStreamingState((prev) => (prev ? { ...prev, partialText: accumulated } : null));
            },
            onDone: (data) => {
              const fullMsg: MessageItem = {
                question_id: data.question_id || "q_" + Date.now(),
                response_id: data.response_id || "r_" + Date.now(),
                raw_text: text,
                answer_text: data.answer_text || accumulated,
                language: metaInfo.language || uiLang,
                level,
                exam_marks: examMarks,
                intent: metaInfo.intent || "explain",
                subject: metaInfo.subject || "General",
                topic: metaInfo.topic || "General",
                validation_passed: data.validation?.passed ?? true,
                explain_again_count: 0,
                created_at: new Date().toISOString(),
              };
              setMessages((prev) => [...prev, fullMsg]);
              setStreamingState(null);
              setIsStreaming(false);
              setIsLoading(false);
            },
            onError: (err) => {
              console.error("Stream error:", err);
              setErrorMessage(err.message || t(errors.generic, uiLang));
              setStreamingState(null);
              setIsStreaming(false);
              setIsLoading(false);
            },
          },
          controller.signal
        );
      } catch (err: any) {
        if (err.name !== "AbortError") {
          console.error("Ask question error:", err);
          setErrorMessage(t(errors.generic, uiLang));
        }
        setStreamingState(null);
        setIsStreaming(false);
        setIsLoading(false);
      }
      return;
    }

    // Buffered fallback mode
    try {
      let resp;
      if (level === "exam" && featureFlags.examMode) {
        resp = await api.examAnswer({
          user_id: userId,
          conversation_id: activeConversationId,
          text,
          marks: examMarks || 5,
          language_override: langOverride,
        });
      } else {
        resp = await api.askQuestion({
          user_id: userId,
          conversation_id: activeConversationId,
          text,
          level,
          exam_marks: examMarks,
          language_override: langOverride,
        });
      }

      if (!activeConversationId) {
        setActiveConversationId(resp.conversation_id);
        loadHistory(userId);
      }

      const newMsg: MessageItem = {
        question_id: resp.question_id,
        response_id: resp.response_id,
        raw_text: text,
        answer_text: resp.answer.text,
        language: resp.detected_language,
        level: resp.level,
        exam_marks: resp.exam_marks,
        intent: resp.intent,
        subject: resp.subject,
        topic: resp.topic,
        validation_passed: resp.validation.passed,
        explain_again_count: resp.explain_again_count || 0,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, newMsg]);
      setErrorMessage(null);
    } catch (err: any) {
      console.error("Ask question error:", err);
      const code = err.code || "INTERNAL";
      let msg = t(errors.generic, uiLang);
      if (code === "MODEL_UNAVAILABLE") msg = t(errors.modelUnavailable, uiLang);
      else if (code === "MODEL_TIMEOUT") msg = t(errors.timeout, uiLang);
      else if (code === "NETWORK_ERROR") msg = t(errors.network, uiLang);

      setErrorMessage(msg);
      setLastFailedAction(() => () => handleSend(text, level, examMarks, langOverride));
    } finally {
      setIsLoading(false);
    }
  };

  // Follow-up actions
  const handleFollowUp = async (action: string, responseId: string) => {
    if (!userId) return;
    setIsActionLoading(true);
    setErrorMessage(null);

    try {
      let resp;
      if (action === "simplify" || action === "explain_again") {
        resp = await api.simplify({
          user_id: userId,
          response_id: responseId,
          mode: action as "simplify" | "explain_again",
        });
      } else {
        resp = await api.followup({
          user_id: userId,
          response_id: responseId,
          action: action as any,
        });
      }

      const prevMsg = messages.find((m) => m.response_id === responseId);
      const qText = prevMsg ? prevMsg.raw_text : "Follow-up";

      const newMsg: MessageItem = {
        question_id: resp.question_id,
        response_id: resp.response_id,
        raw_text: `${qText} (${action})`,
        answer_text: resp.answer.text,
        language: resp.detected_language,
        level: resp.level,
        exam_marks: resp.exam_marks,
        intent: resp.intent,
        subject: resp.subject,
        topic: resp.topic,
        validation_passed: resp.validation.passed,
        explain_again_count: resp.explain_again_count || 0,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, newMsg]);
    } catch (err: any) {
      console.error("Follow-up error:", err);
      const code = err.code || "INTERNAL";
      let msg = t(errors.generic, uiLang);
      if (code === "MODEL_UNAVAILABLE") msg = t(errors.modelUnavailable, uiLang);
      else if (code === "MODEL_TIMEOUT") msg = t(errors.timeout, uiLang);
      setErrorMessage(msg);
    } finally {
      setIsActionLoading(false);
    }
  };

  // Trigger quiz
  const handleStartQuiz = async (responseId: string) => {
    if (!userId) return;
    setIsActionLoading(true);
    setErrorMessage(null);
    try {
      const qz = await api.createQuiz({
        user_id: userId,
        response_id: responseId,
        num_questions: 3,
        phase: "post",
      });
      setActiveQuiz(qz);
    } catch (e: any) {
      const msg = e.message || "Failed to generate quiz";
      setErrorMessage(
        msg.includes("Ollama") || msg.includes("connect")
          ? "AI engine is not responding. Please ensure Ollama is running and try again."
          : msg
      );
    } finally {
      setIsActionLoading(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--surface)] text-[var(--text)]">
      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        onDeleteConversation={handleDeleteConversation}
        uiLang={uiLang}
        onLanguageChange={handleLanguageChange}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full min-w-0">
        {/* Top Header */}
        <header className="h-16 border-b border-[var(--border)] bg-[var(--surface-card)] px-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="lg:hidden p-2 rounded-lg text-[var(--text)] hover:bg-[var(--surface)] cursor-pointer"
            >
              <Menu className="w-5 h-5" />
            </button>
            <Link
              href="/"
              className="font-bold text-lg text-[var(--brand)] hover:opacity-90 flex items-center gap-2"
            >
              <span>{t(site.name, uiLang)}</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--accent-light)] text-[#8C6013] border border-[#ECD19A]">
                {t(nav.tutor, uiLang)}
              </span>
            </Link>
          </div>

          <div className="flex items-center gap-3">
            {isStreaming && (
              <button
                onClick={handleStopGeneration}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-red-100 text-red-700 hover:bg-red-200 transition-colors cursor-pointer"
              >
                <Square className="w-3 h-3 fill-red-700" />
                <span>{t(chat.stop, uiLang)}</span>
              </button>
            )}

            {featureFlags.progress && (
              <Link
                href="/progress"
                className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-[var(--surface)] hover:bg-[var(--brand-light)] hover:text-[var(--brand)] transition-colors text-[var(--text)]"
              >
                {t(nav.progress, uiLang)}
              </Link>
            )}

            <button
              onClick={handleNewChat}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-[var(--brand-light)] text-[var(--brand)] hover:bg-[#E9D6DC] transition-colors cursor-pointer"
            >
              {t(chat.newChat, uiLang)}
            </button>
          </div>
        </header>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6">
          {/* Localized error banner with retry */}
          {errorMessage && (
            <div className="max-w-3xl mx-auto p-4 rounded-2xl bg-red-50 border border-red-200 text-red-800 text-xs sm:text-sm flex items-center justify-between gap-3 shadow-xs">
              <div className="flex items-center gap-2.5">
                <AlertCircle className="w-5 h-5 shrink-0 text-red-600" />
                <span>{errorMessage}</span>
              </div>
              {lastFailedAction && (
                <button
                  onClick={() => {
                    lastFailedAction();
                    setErrorMessage(null);
                  }}
                  className="px-3 py-1.5 rounded-xl bg-red-600 text-white font-semibold hover:bg-red-700 transition-colors cursor-pointer shrink-0"
                >
                  {t(errors.retry, uiLang)}
                </button>
              )}
            </div>
          )}

          {/* Empty State */}
          {messages.length === 0 && !isLoading && !streamingState && (
            <div className="max-w-2xl mx-auto my-auto py-12 text-center space-y-6">
              <div className="w-16 h-16 rounded-3xl bg-[var(--brand-light)] text-[var(--brand)] flex items-center justify-center mx-auto shadow-xs">
                <Sparkles className="w-8 h-8 text-[var(--brand)]" />
              </div>

              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-[var(--text)]">
                  {t(chat.emptyTitle, uiLang)}
                </h2>
                <p className="text-xs sm:text-sm text-[var(--text-muted)] mt-1.5">
                  {t(chat.emptySubtitle, uiLang)}
                </p>
              </div>

              {/* Clickable Example Questions */}
              <div className="space-y-3 pt-2">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-left">
                  {(exampleQuestions[uiLang] || exampleQuestions.mr).map((eq, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSend(eq, "beginner", null, "auto")}
                      className="p-3.5 rounded-xl border border-[var(--border)] bg-[var(--surface-card)] hover:border-[var(--brand)] hover:shadow-xs transition-all text-xs font-medium text-[var(--text)] flex items-center justify-between group cursor-pointer"
                    >
                      <span className="line-clamp-2">{eq}</span>
                      <ChevronRight className="w-4 h-4 text-[var(--text-muted)] group-hover:text-[var(--brand)] shrink-0 ml-2" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Messages list */}
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((m, idx) => (
              <div key={idx} className="space-y-4">
                {/* User Question Bubble */}
                <div className="flex justify-end">
                  <div className="max-w-[85%] sm:max-w-[75%] rounded-2xl rounded-tr-xs bg-[var(--brand)] text-white px-5 py-3 text-[15px] sm:text-[16px] shadow-xs">
                    {m.raw_text}
                  </div>
                </div>

                {/* AI Answer Card */}
                <AnswerCard
                  responseId={m.response_id}
                  answerText={m.answer_text}
                  language={m.language}
                  level={m.level}
                  examMarks={m.exam_marks}
                  intent={m.intent}
                  subject={m.subject}
                  topic={m.topic}
                  validationPassed={m.validation_passed}
                  explainAgainCount={m.explain_again_count}
                  uiLang={uiLang}
                  onFollowUp={handleFollowUp}
                  onStartQuiz={handleStartQuiz}
                  isActionLoading={isActionLoading}
                />
              </div>
            ))}

            {/* In-Flight Streaming Message */}
            {streamingState && (
              <div className="space-y-4">
                <div className="flex justify-end">
                  <div className="max-w-[85%] sm:max-w-[75%] rounded-2xl rounded-tr-xs bg-[var(--brand)] text-white px-5 py-3 text-[15px] sm:text-[16px] shadow-xs">
                    {streamingState.rawText}
                  </div>
                </div>

                <AnswerCard
                  responseId="streaming-temp"
                  answerText={streamingState.partialText || "..."}
                  language={streamingState.language}
                  level={streamingState.level}
                  examMarks={streamingState.examMarks}
                  subject={streamingState.subject}
                  topic={streamingState.topic}
                  uiLang={uiLang}
                  onFollowUp={() => {}}
                  isStreaming={true}
                />
              </div>
            )}

            {/* Initial thinking loader (before first stream token) */}
            {isLoading && !streamingState && (
              <div className="max-w-4xl mx-auto p-5 rounded-2xl bg-[var(--surface-card)] border border-[var(--border)] flex items-center gap-3">
                <Loader2 className="w-4 h-4 animate-spin text-[var(--brand)] shrink-0" />
                <span className="text-xs sm:text-sm font-medium text-[var(--text-muted)] animate-pulse">
                  {t(chat.thinking, uiLang)}
                </span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Composer */}
        <Composer onSend={handleSend} isLoading={isLoading || isActionLoading || isStreaming} uiLang={uiLang} />
      </div>

      {/* Quiz Modal */}
      {activeQuiz && (
        <QuizModal
          quizData={activeQuiz}
          userId={userId}
          uiLang={uiLang}
          onClose={() => setActiveQuiz(null)}
          onExplainAgain={() => {
            const lastMsg = messages[messages.length - 1];
            if (lastMsg) {
              handleFollowUp("explain_again", lastMsg.response_id);
            }
          }}
        />
      )}
    </div>
  );
}
