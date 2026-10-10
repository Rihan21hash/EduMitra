import time
import logging
from typing import Dict, Any, Optional, AsyncIterator
from sqlalchemy.orm import Session

from app.pipeline.language_detect import detect_language
from app.pipeline.normalize import normalize_text
from app.pipeline.analysis import analyze_question, AnalysisResult
from app.pipeline.level_adapter import get_level_rules
from app.pipeline.prompt_builder import build_generation_prompts, build_chat_messages
from app.pipeline.validator import validate_response
from app.pipeline.translator import get_translator, translate_response
from app.pipeline.context_manager import (
    get_or_create_conversation_state,
    update_conversation_state,
    load_conversation_history
)
from app.services.ollama_client import ollama_client, OllamaError
from app.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_chat(analysis, target_lang, level, raw_text, exam_marks, conv_state, history_messages, validation_feedback=None):
    return build_chat_messages(
        analysis=analysis,
        target_language=target_lang,
        level=level,
        original_text=raw_text,
        exam_marks=exam_marks,
        conversation_state=conv_state,
        history_messages=history_messages,
        validation_feedback=validation_feedback,
    )


def _build_en_chat(analysis, level, raw_text, exam_marks, conv_state, history_messages):
    """Build prompts forcing English output — used by pivot mode."""
    return build_chat_messages(
        analysis=analysis,
        target_language="en",       # Force English generation
        level=level,
        original_text=raw_text,
        exam_marks=exam_marks,
        conversation_state=conv_state,
        history_messages=history_messages,
    )

async def run_pipeline(
    raw_text: str,
    level: str = "beginner",
    exam_marks: Optional[int] = None,
    language_override: str = "auto",
    conversation_id: Optional[str] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Executes the EduMitra NLP pipeline with conversation memory, token budgeting,
    and pivot-mode support (English generation → translate to Marathi/Hindi).
    """
    start_total = time.perf_counter()

    # 1. Language Detection
    lang_info = detect_language(raw_text, override=language_override)
    target_lang = lang_info["language"]

    # 2. Text Normalization
    norm_result = normalize_text(raw_text)
    norm_text = norm_result["normalized_text"]
    glossary_terms = norm_result["matched_glossary_terms"]

    # 3. Context & History Retrieval
    conv_state = None
    history_messages = []
    if conversation_id and db:
        try:
            conv_state = get_or_create_conversation_state(conversation_id, db)
            history_messages = load_conversation_history(conversation_id, db)
        except Exception as e:
            logger.warning(f"Error loading conversation context: {e}")

    # 4. Analysis (Fast rule-based)
    t0_analysis = time.perf_counter()
    analysis = await analyze_question(norm_text, target_lang, glossary_terms)
    analysis_ms = int((time.perf_counter() - t0_analysis) * 1000)

    # 5. Token Limit, model, mode, and sampling
    level_rules = get_level_rules(level, exam_marks, target_language=target_lang)
    num_predict = level_rules.get("num_predict", 850)
    sampling = settings.get_sampling_options(target_lang, num_predict=num_predict)
    mode = settings.get_generation_mode(target_lang)   # "direct" | "pivot"
    gen_model = settings.get_gen_model()
    extra_opts = {k: v for k, v in sampling.items() if k not in ("temperature", "num_predict")}

    translation_meta: Dict[str, Any] = {}
    t0_gen = time.perf_counter()

    if mode == "pivot" and target_lang != "en":
        # --- PIVOT MODE: generate in English, then translate ---
        en_messages = _build_en_chat(analysis, level, raw_text, exam_marks, conv_state, history_messages)
        en_answer = await ollama_client.chat(
            messages=en_messages,
            model=gen_model,
            temperature=sampling["temperature"],
            num_predict=num_predict,
            options=extra_opts,
        )
        generation_ms = int((time.perf_counter() - t0_gen) * 1000)

        t0_trans = time.perf_counter()
        trans_result = await translate_response(en_answer, target_lang)
        answer_text = trans_result["translated_text"]
        translation_meta = {
            "mode": "pivot",
            "english_source": en_answer,
            "translation_validation": trans_result.get("validation", {}),
            "translation_ms": int((time.perf_counter() - t0_trans) * 1000),
        }
    else:
        # --- DIRECT MODE: generate in target language directly ---
        chat_messages = _build_chat(analysis, target_lang, level, raw_text, exam_marks, conv_state, history_messages)
        answer_text = await ollama_client.chat(
            messages=chat_messages,
            model=gen_model,
            temperature=sampling["temperature"],
            num_predict=num_predict,
            options=extra_opts,
        )
        generation_ms = int((time.perf_counter() - t0_gen) * 1000)

    # 7. Validation
    t0_val = time.perf_counter()
    val_result = validate_response(
        answer_text=answer_text,
        target_language=target_lang,
        level=level,
        analysis=analysis,
        exam_marks=exam_marks
    )
    validation_ms = int((time.perf_counter() - t0_val) * 1000)

    # Retry once if critically broken (direct mode only)
    if mode != "pivot" and not val_result["passed"] and len(answer_text.strip()) < 25:
        feedback_str = "; ".join(val_result["notes"])
        logger.info(f"Critical validation failure ({feedback_str}). Retrying once...")
        retry_messages = _build_chat(analysis, target_lang, level, raw_text, exam_marks, conv_state, history_messages, validation_feedback=feedback_str)
        try:
            t0_retry = time.perf_counter()
            retry_answer = await ollama_client.chat(
                messages=retry_messages,
                model=gen_model,
                temperature=sampling["temperature"],
                num_predict=num_predict,
                options=extra_opts,
            )
            generation_ms += int((time.perf_counter() - t0_retry) * 1000)
            retry_val = validate_response(
                answer_text=retry_answer,
                target_language=target_lang,
                level=level,
                analysis=analysis,
                exam_marks=exam_marks
            )
            answer_text = retry_answer
            val_result = retry_val
        except Exception as e:
            logger.warning(f"Retry generation failed: {e}. Keeping first answer.")

    # 8. Update conversation state in DB
    if conversation_id and db:
        try:
            update_conversation_state(
                conversation_id=conversation_id,
                db=db,
                subject=analysis.subject,
                topic=analysis.topic,
                answer_language=target_lang
            )
        except Exception as e:
            logger.warning(f"Failed to update conversation state: {e}")

    total_latency_ms = int((time.perf_counter() - start_total) * 1000)

    return {
        "raw_text": raw_text,
        "normalized_text": norm_text,
        "detected_language": target_lang,
        "language_info": lang_info,
        "intent": analysis.intent,
        "subject": analysis.subject,
        "topic": analysis.topic,
        "level": level,
        "exam_marks": exam_marks,
        "answer_text": answer_text,
        "validation": val_result,
        "analysis": analysis,
        "generation_mode": mode,
        "translation": translation_meta,
        "timings": {
            "analysis_ms": analysis_ms,
            "generation_ms": generation_ms,
            "validation_ms": validation_ms,
            "total_ms": total_latency_ms
        },
        "model": gen_model,
    }

async def run_pipeline_stream(
    raw_text: str,
    level: str = "beginner",
    exam_marks: Optional[int] = None,
    language_override: str = "auto",
    conversation_id: Optional[str] = None,
    db: Optional[Session] = None
) -> AsyncIterator[Dict[str, Any]]:
    """
    Streaming variant of run_pipeline yielding SSE events:
    - thinking  : early "Preparing your answer…" signal (emitted before generation)
    - meta      : question classification and initial metadata
    - token     : individual text tokens (Ollama direct, or translated words in pivot)
    - pivot_en  : (pivot mode only) the full English source text
    - done      : final completion stats including TTFT and tokens/sec
    - validation: post-generation quality validation result
    """
    start_total = time.perf_counter()

    # 1. Language Detection & Normalization
    lang_info = detect_language(raw_text, override=language_override)
    target_lang = lang_info["language"]
    norm_result = normalize_text(raw_text)
    norm_text = norm_result["normalized_text"]
    glossary_terms = norm_result["matched_glossary_terms"]

    # 2. Context Loading
    conv_state = None
    history_messages = []
    if conversation_id and db:
        try:
            conv_state = get_or_create_conversation_state(conversation_id, db)
            history_messages = load_conversation_history(conversation_id, db)
        except Exception as e:
            logger.warning(f"Error loading conversation context for stream: {e}")

    # 3. Fast Analysis
    t0_analysis = time.perf_counter()
    analysis = await analyze_question(norm_text, target_lang, glossary_terms)
    analysis_ms = int((time.perf_counter() - t0_analysis) * 1000)

    # Determine generation config
    level_rules = get_level_rules(level, exam_marks, target_language=target_lang)
    num_predict = level_rules.get("num_predict", 850)
    sampling = settings.get_sampling_options(target_lang, num_predict=num_predict)
    mode = settings.get_generation_mode(target_lang)
    gen_model = settings.get_gen_model()
    extra_opts = {k: v for k, v in sampling.items() if k not in ("temperature", "num_predict")}

    # Early UX signal: "Preparing your answer…"
    yield {
        "event": "thinking",
        "data": {"message": "Preparing your answer\u2026", "model": gen_model, "mode": mode}
    }

    # Metadata event
    yield {
        "event": "meta",
        "data": {
            "language": target_lang,
            "language_name": lang_info.get("detected_display", target_lang),
            "intent": analysis.intent,
            "subject": analysis.subject,
            "topic": analysis.topic,
            "level": level,
            "exam_marks": exam_marks,
            "analysis_ms": analysis_ms,
            "generation_mode": mode,
            "model": gen_model,
        }
    }

    full_text_parts = []
    t0_gen = time.perf_counter()
    first_token_time = None
    token_count = 0

    if mode == "pivot" and target_lang != "en":
        # ------------------------------------------------------------------
        # PIVOT MODE: stream English generation, then batch-translate
        # ------------------------------------------------------------------
        en_messages = _build_en_chat(analysis, level, raw_text, exam_marks, conv_state, history_messages)
        en_parts = []

        async for chunk in ollama_client.chat_stream(
            messages=en_messages,
            model=gen_model,
            temperature=sampling["temperature"],
            num_predict=num_predict,
            options=extra_opts,
        ):
            token = chunk.get("token", "")
            if token:
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                en_parts.append(token)
                token_count += 1
            if chunk.get("done", False):
                break

        en_answer_text = "".join(en_parts).strip()
        gen_duration_en = time.perf_counter() - t0_gen

        # Emit full English source to frontend
        yield {
            "event": "pivot_en",
            "data": {
                "english_text": en_answer_text,
                "generation_ms": int(gen_duration_en * 1000),
            }
        }

        # Translate English → target language
        t0_trans = time.perf_counter()
        trans_result = await translate_response(en_answer_text, target_lang)
        translated_text = trans_result["translated_text"]
        trans_ms = int((time.perf_counter() - t0_trans) * 1000)

        # Stream translated text word-by-word
        words = translated_text.split(" ")
        for idx, w in enumerate(words):
            tok = w + (" " if idx < len(words) - 1 else "")
            full_text_parts.append(tok)
            yield {"event": "token", "data": {"token": tok, "phase": "translated"}}

        full_answer = translated_text
        gen_duration = time.perf_counter() - t0_gen
        ttft_ms = int((first_token_time - t0_gen) * 1000) if first_token_time else 0
        generation_ms = int(gen_duration_en * 1000)
        total_ms = int((time.perf_counter() - start_total) * 1000)

        yield {
            "event": "done",
            "data": {
                "answer_text": full_answer,
                "english_source": en_answer_text,
                "generation_mode": "pivot",
                "timings": {
                    "ttft_ms": ttft_ms,
                    "generation_ms": generation_ms,
                    "translation_ms": trans_ms,
                    "total_ms": total_ms,
                },
                "tokens_generated": token_count,
                "tokens_per_sec": round(token_count / gen_duration_en, 1) if gen_duration_en > 0 else 0.0,
                "model": gen_model,
            }
        }

    else:
        # ------------------------------------------------------------------
        # DIRECT MODE: stream target-language tokens directly from Ollama
        # ------------------------------------------------------------------
        chat_messages = _build_chat(analysis, target_lang, level, raw_text, exam_marks, conv_state, history_messages)

        async for chunk in ollama_client.chat_stream(
            messages=chat_messages,
            model=gen_model,
            temperature=sampling["temperature"],
            num_predict=num_predict,
            options=extra_opts,
        ):
            token = chunk.get("token", "")
            if token:
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                full_text_parts.append(token)
                token_count += 1
                yield {"event": "token", "data": {"token": token, "phase": "direct"}}

            if chunk.get("done", False):
                break

        full_answer = "".join(full_text_parts).strip()
        gen_duration = time.perf_counter() - t0_gen
        ttft_ms = int((first_token_time - t0_gen) * 1000) if first_token_time else 0
        generation_ms = int(gen_duration * 1000)
        total_ms = int((time.perf_counter() - start_total) * 1000)

        yield {
            "event": "done",
            "data": {
                "answer_text": full_answer,
                "generation_mode": "direct",
                "timings": {
                    "ttft_ms": ttft_ms,
                    "generation_ms": generation_ms,
                    "total_ms": total_ms,
                },
                "tokens_generated": token_count,
                "tokens_per_sec": round(token_count / gen_duration, 1) if gen_duration > 0 else 0.0,
                "model": gen_model,
            }
        }

    # Post-stream: Validation & state update
    val_result = validate_response(
        answer_text=full_answer,
        target_language=target_lang,
        level=level,
        analysis=analysis,
        exam_marks=exam_marks
    )

    yield {"event": "validation", "data": val_result}

    if conversation_id and db:
        try:
            update_conversation_state(
                conversation_id=conversation_id,
                db=db,
                subject=analysis.subject,
                topic=analysis.topic,
                answer_language=target_lang
            )
        except Exception as e:
            logger.warning(f"Failed to update conversation state after stream: {e}")
