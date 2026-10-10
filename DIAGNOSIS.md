# EduMitra — DIAGNOSIS.md

## Overview

This document identifies the root cause of each reported symptom, with file and line evidence, before any code changes are made.

---

## Symptom 1: App forgets conversation context

### Root Cause: No history sent to Ollama

**The pipeline is stateless.** Every call to `run_pipeline()` builds a prompt from scratch using only the current question text. No prior turns are included.

| Evidence | File | Lines |
|---|---|---|
| `run_pipeline()` accepts only `raw_text`, `level`, `exam_marks`, `language_override` — no `conversation_id` or history | `backend/app/pipeline/orchestrator.py` | 15–20 |
| `build_generation_prompts()` has no `history` or `messages` parameter | `backend/app/pipeline/prompt_builder.py` | 25–32 |
| `ollama_client.generate()` uses `/api/generate` (single prompt, no message array) — NOT `/api/chat` (multi-turn) | `backend/app/services/ollama_client.py` | 55–56 |
| `num_ctx` is hardcoded to **2048** — far too small for multi-turn context | `backend/app/services/ollama_client.py` | 63 |
| No `conversation_state` table exists in the schema | `backend/app/models.py` | entire file |

**Impact:** Follow-ups like "give an example" or "explain that again" produce unrelated answers because the model sees no prior context. The `conversation_id` is stored in the DB but never used for prompt construction.

---

## Symptom 2: Language switch doesn't produce same reply in new language

### Root Cause: No response variant storage + state resets on language change

| Evidence | File | Lines |
|---|---|---|
| No `response_variants` table exists | `backend/app/models.py` | entire file |
| No `/api/response/{id}/variant` endpoint exists | `backend/app/main.py` | 76–84 |
| `Composer.tsx` syncs `langOverride` to `uiLang` — changing language in the UI changes the answer language for **new** questions, but existing replies are not re-rendered | `frontend/src/components/Composer.tsx` | 28–30 |
| No per-answer language toggle exists in `AnswerCard.tsx` | `frontend/src/components/AnswerCard.tsx` | entire file |
| The `followup.py` translate action generates a **new response** in the DB but does not link it as a variant of the original; it creates a new chat message | `backend/app/routers/followup.py` | 61–76 |

**Impact:** Switching language generates a completely new answer (possibly about a different topic since there's no context), not a translation of the same answer. There is no way to get byte-for-byte identical content back.

---

## Symptom 3: 30–40 second reply latency

### Root Causes (multiple, compounding):

#### 3a. No streaming — response is fully buffered

| Evidence | File | Lines |
|---|---|---|
| `ollama_client.generate()` sets `"stream": False` | `backend/app/services/ollama_client.py` | 59 |
| `generate_stream()` exists but is **never called** from any router | Grep for `generate_stream` usage — only defined, never imported | — |
| `question.py` router returns a synchronous JSON response, not a `StreamingResponse` | `backend/app/routers/question.py` | 12 |
| Frontend uses `fetch` + `res.json()` — no ReadableStream processing | `frontend/src/lib/api.ts` | 152–157 |

#### 3b. Tiny `num_ctx` causing prompt truncation → bad output → retry

| Evidence | File | Lines |
|---|---|---|
| `num_ctx` hardcoded to **2048** | `backend/app/services/ollama_client.py` | 63 |
| Devanagari text is very token-heavy (each Unicode character may be 2–4 tokens). A system prompt + user template + Devanagari question easily exceeds 2048 tokens. The model silently truncates the prompt, producing garbled output. | — | — |

#### 3c. No model warm-up — cold load on first request

| Evidence | File | Lines |
|---|---|---|
| No `keep_alive` parameter sent in any Ollama call | `backend/app/services/ollama_client.py` | 56–64 |
| No warm-up call on backend startup (`lifespan` only creates DB tables) | `backend/app/main.py` | 19–25 |
| Health endpoint checks `/api/tags` but not `/api/ps` (model loaded status) | `backend/app/routers/health.py` | entire file |

#### 3d. Retry loop on failed validation

| Evidence | File | Lines |
|---|---|---|
| If validation fails (e.g. due to truncated output from `num_ctx=2048`), the orchestrator retries with a **second full LLM call** | `backend/app/pipeline/orchestrator.py` | 72–106 |

**Total impact:** Cold load (~10–15s) + generation with truncated context (~10–15s) + possible retry (~10–15s) = 30–40s. User sees nothing until the entire response is buffered.

---

## Symptom 4: Marathi and Hindi replies sound blunt/unnatural

### Root Causes:

#### 4a. No style/register guidance in prompts

| Evidence | File | Lines |
|---|---|---|
| System prompt only says "Write in {language_name}" — no register, tone, politeness, or sentence structure guidance | `backend/app/prompts/system.txt` | 1–28 |
| No style files exist (`marathi.md`, `hindi.md`) | `backend/app/prompts/` directory | — |
| No few-shot exemplars exist | — | — |

#### 4b. Dictionary files unused

| Evidence | File | Lines |
|---|---|---|
| Dictionary files exist at `Dictionary/English-to-Hindi-Dictionary.txt` (891KB, ~22K words) and `Dictionary/English-to-Marathi-Dictionary.txt` (527KB) | `Dictionary/` directory | — |
| No `lexicon.py` exists | — | — |
| The `glossary.json` has only ~20 entries — useful but tiny | `backend/app/data/glossary.json` | 1–23 |

#### 4c. No cross-language leakage detection

| Evidence | File | Lines |
|---|---|---|
| Validator checks Devanagari ratio but does NOT check for Hindi markers in Marathi output or vice versa | `backend/app/pipeline/validator.py` | 33–48 |

**Impact:** The model defaults to terse, robotic Hindi-esque Devanagari. Without explicit style guidance, polite register instructions, or vocabulary from the dictionaries, the output reads like literal translation rather than natural Marathi or Hindi.

---

## Symptom 5: Exam mode ignores marks

### Root Causes:

#### 5a. Marks value not used effectively in the prompt

| Evidence | File | Lines |
|---|---|---|
| `get_level_rules("exam", marks)` returns correct structure text per marks value | `backend/app/pipeline/level_adapter.py` | 42–67 |
| BUT `user_template.txt` only has `{level_rules}` as a generic instruction — no strict per-section word budgets, no explicit "this is a {marks}-mark question" framing | `backend/app/prompts/user_template.txt` | 1–11 |
| The prompt says "Level: exam" but doesn't say "Marks: 2" or "Marks: 10" explicitly | — | — |

#### 5b. num_predict too generic for Devanagari

| Evidence | File | Lines |
|---|---|---|
| 2-mark `num_predict` is 160, but num_ctx is only 2048 — leaving barely any room for generation after the prompt | `backend/app/pipeline/level_adapter.py` | 43–46 |
| 10-mark answer needs `num_predict=800` but with `num_ctx=2048` and a ~500 token prompt, only ~1548 tokens available for output — may truncate | — | — |

#### 5c. Validator doesn't enforce exam structure

| Evidence | File | Lines |
|---|---|---|
| Validator checks word count but doesn't validate required headings, section counts, or point counts per marks | `backend/app/pipeline/validator.py` | 76–85 |
| Word count tolerance is ±30% (`min*0.7`, `max*1.5`) — far too loose | `backend/app/pipeline/validator.py` | 79–80 |

**Impact:** A 2-mark question gets the same verbose answer as a 10-mark question because the model doesn't see a strict structure or budget.

---

## Symptom 6: Quiz and Progress don't fully work

### Root Causes:

#### 6a. Quiz: fragile LLM JSON parsing

| Evidence | File | Lines |
|---|---|---|
| Quiz uses `ollama_client.generate()` with `json_format=True` but sets `"format": "json"` — this is Ollama's old free-form JSON mode, not structured output with a schema. The model frequently returns malformed JSON. | `backend/app/services/ollama_client.py` | 71 |
| On JSON parse failure, the quiz router falls back to hardcoded questions (always 2 questions, always the same) | `backend/app/routers/quiz.py` | 67–119 |
| Quiz has no `topic_key` or stable question ID for retake comparisons | `backend/app/models.py` | 89–100 |

#### 6b. Quiz: no retake, no explain-again on missed, no pre-check toggle

| Evidence | File | Lines |
|---|---|---|
| `QuizModal.tsx` only has "Back to Chat" after results — no "Retake", "Explain again", or "View progress" buttons | `frontend/src/components/QuizModal.tsx` | 192–198 |
| QuizModal shows all questions at once, not one-at-a-time | `frontend/src/components/QuizModal.tsx` | 111–182 |
| No pre-check UI toggle exists | — | — |

#### 6c. Progress: data model too shallow

| Evidence | File | Lines |
|---|---|---|
| Progress endpoint calculates improvement as `post_score - pre_score` but only takes the LAST attempt per phase per topic — not baseline vs latest | `backend/app/routers/quiz.py` | 195–252 |
| No `questions_asked`, `languages_used`, `levels_used`, `satisfaction_pct`, or timeline data | — | — |
| Progress page has no charts (SVG or otherwise), only a simple list | `frontend/src/app/progress/page.tsx` | entire file |
| Some text is hardcoded in English (`"pts"`, `"Evaluated concept checkpoints"`, etc.) instead of using `content.js` | `frontend/src/app/progress/page.tsx` | 79, 97 |

---

## Implicit Issue: `streaming` feature flag is `false`

| Evidence | File | Lines |
|---|---|---|
| `featureFlags.streaming = false` in `content.js` | `frontend/src/content.js` | 15 |

---

## Dictionary File Inspection

### English-to-Hindi-Dictionary.txt
- **Format:** Two-column layout split vertically on the page. Lines 1–61 contain English words in order, Lines 63+ contain their Hindi meanings in parallel order. The file has a header (lines 1–8) and a form-feed separator (`\f`).
- **Entry count:** ~22,000 entries (stated in header, 48,270 lines total)
- **Fields:** English word → Hindi meaning (Devanagari)
- **Encoding:** UTF-8 with some rendering artifacts (broken Devanagari conjuncts suggesting PDF extraction artifacts)
- **Sample:** `a → एक, कोई` | `aback → पीछे, पीछे की ओर`

### English-to-Marathi-Dictionary.txt
- **Format:** Multi-line blocks: English word, Marathi meaning, romanization, English synonyms/usage. Entries separated by blank lines. Contains form-feed separators.
- **Entry count:** ~57,149 lines, estimated ~5,000–8,000 word entries
- **Fields:** English word, Marathi meaning (Devanagari), romanized form, English synonyms
- **Encoding:** UTF-8 with some artifacts (broken conjuncts, partial characters)
- **Sample:** `a → एक (ek)` | `ability → योग्यता (yoogythaa)`

**Both files have encoding/rendering artifacts from PDF extraction.** Conjunct characters are sometimes split (e.g., `यो यता` instead of `योग्यता`). This will need NFC normalization and possibly heuristic repair.

---

## Summary of Root Causes → Workstreams

| # | Symptom | Primary Root Cause | Fix Workstream |
|---|---|---|---|
| 1 | Forgets context | `/api/generate` with no history; `num_ctx=2048` | **A** |
| 2 | Language switch → different answer | No variant storage; no per-answer language toggle | **B** |
| 3 | 30–40s latency | No streaming; `num_ctx=2048` truncation; no warm-up; retry loop | **C** |
| 4 | Blunt Marathi/Hindi | No style guide; dictionary unused; no leakage detection | **D** |
| 5 | Exam ignores marks | Weak prompt; no strict structure; no structural validation | **E** |
| 6 | Quiz/Progress broken | Fragile JSON; no retake/pre-check; shallow progress model | **F, G** |

---

## Timing Profile (estimated, before changes)

| Stage | Estimated Time | Notes |
|---|---|---|
| Cold model load | 10–15s | No `keep_alive`, no warm-up |
| Analysis (rule-based) | <5ms | Already fast, no LLM call |
| Prompt build | <1ms | String formatting |
| LLM generation (buffered) | 15–25s | `num_ctx=2048` truncates, Devanagari token-heavy |
| Validation | <10ms | Regex checks |
| Retry (if validation fails) | 15–25s | Full second generation |
| Network overhead | <50ms | localhost |
| **Total (cold, no retry)** | **25–40s** | |
| **Total (warm, no retry)** | **15–25s** | |

> **Target after fix:** TTFT ≤ ~3s (warm), tokens streaming continuously.
