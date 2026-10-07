# EduMitra — Assumptions and Decisions

This document records architectural decisions, default choices, and assumptions made during implementation.

## 1. Authentication & Sessions
- **Guest Sessions:** No passwords or external auth providers. Guest accounts are created via `POST /api/users` on first visit and the `user_id` is persisted in the browser's `localStorage`. User display names are stored locally in SQLite.

## 2. Models & Ollama Integration
- **Default LLM:** `qwen2.5-coder:7b` / `qwen2.5:7b` running locally via Ollama at `http://localhost:11434`.
- **Model Bake-off & Fallback:** Evaluated `qwen2.5-coder:7b` (pre-installed, parameter size 7.6B) and `qwen2.5:7b` / `qwen2.5:3b`. Model name is configured via `OLLAMA_MODEL` environment variable.
- **Zero-Cost & Local-First:** No paid APIs or third-party cloud LLMs. Ollama handles all inference locally.
- **Concurrency & Latency:** Concurrency is regulated using an `asyncio.Semaphore(1)` to prevent GPU/CPU thrashing on laptop environments. A 2-call pipeline pattern (Analysis + Generation) minimizes latency.

## 3. Multilingual Design & Single Source of Truth
- **Single Source of Truth (`content.js`):** `frontend/src/content.js` contains all user-visible text, labels, messages, themes, and feature flags. No strings are hardcoded in React components or pages.
- **Trilingual UI:** The UI supports English (`en`), Hindi (`hi`), and Marathi (`mr`). All strings have translations for each language.
- **Devanagari Typography:** Noto Sans Devanagari is used with generous line height (approx. 1.7) and minimum 16px body text for optimal readability of Marathi and Hindi scripts.
- **Terminology Rule:** Academic and technical terms appear in the textbook language with English in parentheses on first mention (e.g., जड़त्व (Inertia) or जडत्व (Inertia)).

## 4. Scope, Phases & Feature Flags
- **P0 Scope:** Marathi, Hindi, English text input, auto language detection with override, Beginner/Intermediate/Advanced levels, meaning-preserving explanations, response validation, "Simplify" and "Explain again" follow-ups, chat history, and trilingual UI driven by `content.js`.
- **P1 Scope (Behind Feature Flags in `content.js`):**
  - `examMode`: Structured answers by mark count (2, 5, 7, 10 marks).
  - `quiz`: Generating 3-5 question MCQs with server-side validation and scoring.
  - `progress`: Tracking pre-quiz vs post-quiz scores to calculate Understanding Improvement.
  - `voiceInput`: Web Speech API (`webkitSpeechRecognition`) with language set to `mr-IN`, `hi-IN`, or `en-IN`.
  - `feedback`: Thumbs up/down satisfaction logging in SQLite.
- **P2 Scope:** Kept open architecturally, but deferred (teacher dashboard, offline mobile app, additional regional languages).

## 5. Endpoints & API Design
- In addition to `/api/question`, `/api/simplify`, `/api/exam-answer`, and `/api/quiz`, supplementary endpoints `/api/users`, `/api/history`, `/api/conversations/{id}`, `/api/feedback`, and `/api/health` are implemented to support persistent guest sessions, conversation management, satisfaction metrics, and system diagnostics.
