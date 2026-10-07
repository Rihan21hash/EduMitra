# EduMitra — Multilingual Academic Support System

> **Learn in your language. Understand at your level.**

**Team:** The Penguins — Atharva, Rihan, Ashutosh, Sonal  
**Event:** AARAMBH · WCE-Hackathon 2026 — Dept. of Electrical Engineering, Walchand College of Engineering, Sangli  
**Category:** Software (AI / NLP) · Education Technology (EdTech)

---

## What is EduMitra?

EduMitra is an AI tutor for **Marathi, Hindi, and English** that:
- Understands questions in any mix of these three languages
- Adapts answers for **Beginner**, **Intermediate**, **Advanced**, and **Exam** levels
- Preserves technical terms and formulas without word-by-word translation
- Runs **100% locally** using Ollama — no internet required, no paid API keys

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Ollama | Latest | [ollama.com](https://ollama.com) |
| A Qwen model | 7B recommended | `ollama pull qwen2.5:7b` |

> **Your machine already has:** `qwen2.5-coder:7b` and `llama3:latest`

---

## Setup (First Time Only)

### 1. Clone / navigate to project
```powershell
cd d:\Hackathon\WalchandHackathon
```

### 2. Copy environment config
```powershell
Copy-Item .env.example .env
```

The `.env` file controls which Ollama model is used. Default:
```
OLLAMA_MODEL=qwen2.5-coder:7b
```

### 3. Create Python virtual environment
```powershell
python -m venv .venv
```

### 4. Install backend dependencies
```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

### 5. Install frontend dependencies
```powershell
cd frontend
npm install
cd ..
```

---

## Running the App (3 terminals)

### Terminal 1 — Start Ollama AI Engine
```powershell
ollama serve
```
Ollama starts at `http://localhost:11434`. Leave this running.

### Terminal 2 — Start Backend (FastAPI)
```powershell
cd d:\Hackathon\WalchandHackathon\backend
..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend starts at `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`

### Terminal 3 — Start Frontend (Next.js)
```powershell
cd d:\Hackathon\WalchandHackathon\frontend
npm run dev
```

App opens at `http://localhost:3000`

---

## Verifying Everything Works

```powershell
# Check Ollama is running and connected
curl http://127.0.0.1:8000/api/health
```

Expected response:
```json
{
  "status": "ok",
  "ollama_connected": true,
  "active_model": "qwen2.5-coder:7b",
  "available_models": ["qwen2.5-coder:7b", "llama3:latest"]
}
```

---

## Running Tests

```powershell
cd d:\Hackathon\WalchandHackathon\backend
..\.venv\Scripts\python.exe -m pytest -v
```

All 16 unit tests should pass in ~1 second (no Ollama required).

---

## How to Change the AI Model

Edit the `.env` file (or set environment variables):

```env
# Use a different Qwen model
OLLAMA_MODEL=qwen2.5:7b

# Use a smaller model for low-RAM machines
OLLAMA_MODEL=qwen2.5:3b

# Use Llama (also on your machine)
OLLAMA_MODEL=llama3:latest
```

Then restart the backend. The model name is the only change needed.

---

## How to Edit Content

**Everything user-visible lives in one file:** [`frontend/src/content.js`](frontend/src/content.js)

| What you want to change | Where in `content.js` |
|---|---|
| App name, tagline | `site` |
| Landing page text | `landing` |
| Example questions | `exampleQuestions` |
| Chat placeholder, button labels | `chat` |
| Level descriptions | `levels` |
| Follow-up button labels | `followUps` |
| Error messages | `errors` |
| Team member names/roles | `team` |
| Color theme | `theme` |
| Feature flags (on/off) | `featureFlags` |
| Quiz / progress text | `quiz`, `progress` |

**To turn a P1 feature on or off**, edit `featureFlags`:
```js
export const featureFlags = {
  voiceInput: true,   // turn off → false
  examMode: true,     // turn off → false  
  quiz: true,         // turn off → false
  progress: true,     // turn off → false
};
```

Save the file → the dev server hot-reloads instantly. No code changes needed.

---

## Editing AI Prompts

The AI system prompts are plain text files in `backend/app/prompts/`:
- `system.txt` — core identity and language rules
- `user_template.txt` — generation prompt template
- `followups/simplify.txt` — simplify instruction
- `followups/explain_again.txt` — explain-again instruction
- `followups/quiz.txt` — quiz generation prompt
- etc.

Edit and save → changes take effect on the next request (no restart needed).

---

## Architecture Overview

```
Student
  ↓ (text in Marathi/Hindi/English)
Next.js Frontend (port 3000)
  ↓ REST/JSON
FastAPI Backend (port 8000)
  ↓ 8-stage NLP Pipeline:
  │  1. Language Detection (Devanagari ratio + marker words)
  │  2. Text Normalization (Unicode NFC, digit mapping)
  │  3-5. Analysis LLM Call → intent, subject, topic, core_question
  │  6. Level Adapter (Beginner/Intermediate/Advanced/Exam rules)
  │  7. Prompt Builder (structured academic prompt)
  │  8. Response Validator (terms, formulas, script, length)
  ↓
Ollama (port 11434) → qwen2.5-coder:7b (local, offline)
  ↓
SQLite Database (edumitra.db — local file)
```

---

## Project Structure

```
WalchandHackathon/
├── .env.example               # Environment config template
├── .env                       # Your local config (copy from .env.example)
├── ASSUMPTIONS.md             # Architecture decisions
├── README.md                  # This file
├── .venv/                     # Python virtual environment
│
├── backend/
│   ├── requirements.txt
│   ├── edumitra.db            # SQLite database (auto-created on startup)
│   └── app/
│       ├── main.py            # FastAPI application entry point
│       ├── config.py          # Settings from .env
│       ├── db.py              # Database session management
│       ├── models.py          # SQLAlchemy table definitions
│       ├── schemas.py         # Pydantic request/response types
│       ├── routers/           # API endpoint handlers
│       ├── pipeline/          # 8-stage NLP pipeline files
│       ├── services/          # Ollama client
│       ├── prompts/           # Editable system prompts (plain text)
│       └── data/              # glossary.json, formulas.json, subjects.json
│   └── tests/
│       ├── eval/questions.json  # Gold evaluation set (30 questions)
│       ├── test_api.py
│       ├── test_language_detect.py
│       ├── test_normalize.py
│       └── test_validator.py
│
└── frontend/
    └── src/
        ├── content.js         # ← ALL editable text, labels, theme, flags
        ├── app/
        │   ├── layout.tsx     # Root layout with theme injection
        │   ├── page.tsx       # Landing page (/)
        │   ├── chat/page.tsx  # Chat workspace (/chat)
        │   └── progress/page.tsx  # Progress dashboard (/progress)
        ├── components/
        │   ├── Navbar.tsx
        │   ├── Footer.tsx
        │   ├── Sidebar.tsx
        │   ├── Composer.tsx   # Question input + voice + level selector
        │   ├── AnswerCard.tsx # Markdown+Math answer with follow-ups
        │   └── QuizModal.tsx  # Comprehension quiz overlay
        └── lib/
            ├── api.ts         # All backend API calls
            ├── i18n.ts        # t() helper for trilingual strings
            ├── speech.ts      # Web Speech API for voice input
            └── validateContent.ts  # Dev-time content.js validator
```

---

## Hackathon Demo Flow (3 minutes)

1. **Landing page** — show tagline, 5-step flow, features, impact numbers
2. **Marathi Beginner** — ask *"न्यूटनचा पहिला नियम काय आहे?"* in Marathi at Beginner level — show detected language badge, preserved key terms, validation status
3. **Advanced level** — switch to Advanced, ask the same question — show depth difference
4. **Mixed query** — ask *"Photosynthesis म्हणजे काय?"* — show mixed-language handling
5. **Explain again** — click "पुन्हा समजावा" — show fresh explanation with different analogy
6. **Exam mode** — switch to Exam, pick 5 marks — show structured answer with headings
7. **Quiz** — click "मला क्विझ द्या" — show comprehension quiz and score
8. **Live edit** — change a label in `content.js`, save — show UI updating instantly

---

## Team

| Name | Role |
|---|---|
| Atharva | Team Lead & ML Architect |
| Rihan | Full-Stack & Systems Engineer |
| Ashutosh | NLP Pipeline & Prompt Engineer |
| Sonal | Frontend & UI/UX Specialist |

---

*Built for AARAMBH · WCE-Hackathon 2026 — Walchand College of Engineering, Sangli*
