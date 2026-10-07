import time
import logging
from typing import Dict, Any, Optional
from app.pipeline.language_detect import detect_language
from app.pipeline.normalize import normalize_text
from app.pipeline.analysis import analyze_question, AnalysisResult
from app.pipeline.prompt_builder import build_generation_prompts
from app.pipeline.validator import validate_response
from app.services.ollama_client import ollama_client, OllamaError
from app.config import settings

logger = logging.getLogger(__name__)

async def run_pipeline(
    raw_text: str,
    level: str = "beginner",
    exam_marks: Optional[int] = None,
    language_override: str = "auto"
) -> Dict[str, Any]:
    """
    Executes the 8-stage EduMitra NLP pipeline with single retry on validation failure.
    """
    start_total = time.perf_counter()

    # 1. Language Detection
    lang_info = detect_language(raw_text, override=language_override)
    target_lang = lang_info["language"]

    # 2. Text Normalization
    norm_result = normalize_text(raw_text)
    norm_text = norm_result["normalized_text"]
    glossary_terms = norm_result["matched_glossary_terms"]

    # 3-5. Analysis (Combined LLM call)
    t0_analysis = time.perf_counter()
    analysis = await analyze_question(norm_text, target_lang, glossary_terms)
    analysis_ms = int((time.perf_counter() - t0_analysis) * 1000)

    # 6-7. Prompt Builder & Generation
    t0_gen = time.perf_counter()
    prompts = build_generation_prompts(
        analysis=analysis,
        target_language=target_lang,
        level=level,
        original_text=raw_text,
        exam_marks=exam_marks
    )

    answer_text = await ollama_client.generate(
        prompt=prompts["user"],
        system=prompts["system"],
        temperature=0.4
    )
    generation_ms = int((time.perf_counter() - t0_gen) * 1000)

    # 8. Validation
    t0_val = time.perf_counter()
    val_result = validate_response(
        answer_text=answer_text,
        target_language=target_lang,
        level=level,
        analysis=analysis,
        exam_marks=exam_marks
    )
    validation_ms = int((time.perf_counter() - t0_val) * 1000)

    # If validation failed, RETRY ONCE with feedback
    if not val_result["passed"] and len(val_result["notes"]) > 0:
        feedback_str = "; ".join(val_result["notes"])
        logger.info(f"First validation attempt failed ({feedback_str}). Retrying once...")

        retry_prompts = build_generation_prompts(
            analysis=analysis,
            target_language=target_lang,
            level=level,
            original_text=raw_text,
            exam_marks=exam_marks,
            validation_feedback=feedback_str
        )

        try:
            t0_retry = time.perf_counter()
            retry_answer = await ollama_client.generate(
                prompt=retry_prompts["user"],
                system=retry_prompts["system"],
                temperature=0.3
            )
            generation_ms += int((time.perf_counter() - t0_retry) * 1000)

            retry_val = validate_response(
                answer_text=retry_answer,
                target_language=target_lang,
                level=level,
                analysis=analysis,
                exam_marks=exam_marks
            )
            # Accept retry result
            answer_text = retry_answer
            val_result = retry_val
        except Exception as e:
            logger.warning(f"Validation retry generation failed: {e}. Keeping first answer.")

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
        "timings": {
            "analysis_ms": analysis_ms,
            "generation_ms": generation_ms,
            "validation_ms": validation_ms,
            "total_ms": total_latency_ms
        },
        "model": settings.ollama_model
    }
