"use client";

import React from "react";
import Link from "next/link";
import { chat, languages, site } from "@/content";
import { t, Locale } from "@/lib/i18n";
import { ConversationSummary } from "@/lib/api";
import {
  MessageSquare,
  Plus,
  Trash2,
  Globe,
  ChevronRight,
  BookOpen,
} from "lucide-react";

interface SidebarProps {
  conversations: ConversationSummary[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
  onDeleteConversation: (id: string) => void;
  uiLang: Locale;
  onLanguageChange: (lang: Locale) => void;
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  uiLang,
  onLanguageChange,
  isOpen,
  onClose,
}: SidebarProps) {
  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-stone-900/40 z-40 lg:hidden"
        />
      )}

      <aside
        className={`fixed lg:static top-0 left-0 bottom-0 z-50 w-72 bg-[var(--surface-card)] border-r border-[var(--border)] flex flex-col transition-transform duration-200 ease-in-out ${
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        {/* Header with New Chat */}
        <div className="p-4 border-b border-[var(--border)] flex items-center justify-between gap-2">
          <button
            onClick={() => {
              onNewChat();
              onClose();
            }}
            className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-[var(--brand)] text-white font-medium text-xs shadow-xs hover:bg-[#58222F] transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>{t(chat.newChat, uiLang)}</span>
          </button>
        </div>

        {/* History list */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <div className="px-2 py-1 text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">
            {t(chat.history, uiLang)}
          </div>

          {conversations.length === 0 ? (
            <div className="p-4 text-center text-xs text-[var(--text-muted)] italic">
              {t(chat.noHistory, uiLang)}
            </div>
          ) : (
            conversations.map((c) => {
              const isActive = c.id === activeConversationId;
              return (
                <div
                  key={c.id}
                  className={`group flex items-center justify-between p-2.5 rounded-xl text-xs transition-colors cursor-pointer ${
                    isActive
                      ? "bg-[var(--brand-light)] text-[var(--brand)] font-semibold"
                      : "text-[var(--text)] hover:bg-[var(--surface)]"
                  }`}
                  onClick={() => {
                    onSelectConversation(c.id);
                    onClose();
                  }}
                >
                  <div className="flex items-center gap-2.5 min-w-0 pr-2">
                    <MessageSquare className="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span className="truncate">{c.title || "Chat"}</span>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(t(chat.deleteConfirm, uiLang))) {
                        onDeleteConversation(c.id);
                      }
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-600 transition-opacity cursor-pointer"
                    title="Delete"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Bottom Language Switcher */}
        <div className="p-3 border-t border-[var(--border)] bg-[var(--surface)]/50">
          <div className="text-[11px] font-semibold text-[var(--text-muted)] mb-1.5 flex items-center gap-1.5 px-1">
            <Globe className="w-3 h-3" />
            <span>{t(chat.uiLanguage, uiLang)}</span>
          </div>
          <div className="grid grid-cols-3 gap-1">
            {languages.map((l) => (
              <button
                key={l.id}
                onClick={() => onLanguageChange(l.id as Locale)}
                className={`py-1.5 px-2 rounded-lg text-xs font-medium text-center transition-all cursor-pointer ${
                  uiLang === l.id
                    ? "bg-[var(--brand)] text-white shadow-xs"
                    : "bg-[var(--surface-card)] text-[var(--text)] hover:bg-white"
                }`}
              >
                {l.nativeName}
              </button>
            ))}
          </div>
        </div>
      </aside>
    </>
  );
}
