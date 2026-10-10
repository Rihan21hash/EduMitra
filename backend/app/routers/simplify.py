import json
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Response as DBResponse, Question, User
from app.schemas import SimplifyRequest, QuestionResponse, AnswerContent, ValidationResult, MetaInfo, TimingMeta
from app.pipeline.analysis import AnalysisResult
from app.pipeline.prompt_builder import build_followup_prompt
from app.pipeline.validator import validate_response
from app.services.ollama_client import ollama_client, OllamaError
from app.config import settings

router = APIRouter(prefix="/api", tags=["simplify"])

@router.post("/simplify", response_model=QuestionResponse)
async def handle_simplify(payload: SimplifyRequest, db: Session = Depends(get_db)):
    # 1. Fetch parent response & question
    parent_resp = db.query(DBResponse).filter(DBResponse.id == payload.response_id).first()
    if not parent_resp:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Parent response not found"})

    question = db.query(Question).filter(Question.id == parent_resp.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Associated question not found"})

    start_total = time.perf_counter()

    # Determine target level and explain_again_count
    explain_again_count = parent_resp.explain_again_count
    if payload.mode == "explain_again":
        explain_again_count += 1
        current_level = parent_resp.level
    else:  # simplify
        step_down = {
            "advanced": "intermediate",
            "intermediate": "beginner",
            "exam": "beginner",
            "beginner": "beginner"
        }
        current_level = step_down.get(parent_resp.level.lower(), "beginner")

    # Reconstruct lightweight AnalysisResult from question record
    analysis = AnalysisResult(
        language=parent_resp.language,
        intent=question.intent,
        subject=question.subject,
        topic=question.topic,
        core_question=question.normalized_text,
        key_terms=[],
        formulas=[],
        expected_answer_type="explanation"
    )

    prompts = build_followup_prompt(
        action=payload.mode,
        analysis=analysis,
        previous_answer=parent_resp.content,
        target_language=parent_resp.language,
        level=current_level,
        explain_again_count=explain_again_count
    )

    t0_gen = time.perf_counter()
    try:
        new_answer = await ollama_client.generate(
            prompt=prompts["user"],
            system=prompts["system"],
            temperature=0.4,
            num_predict=320
        )
    except OllamaError as oe:
        status_code = 503 if oe.code == "MODEL_UNAVAILABLE" else 500
        raise HTTPException(status_code=status_code, detail={"code": oe.code, "message": oe.message})

    gen_ms = int((time.perf_counter() - t0_gen) * 1000)

    # Validate output
    val = validate_response(
        answer_text=new_answer,
        target_language=parent_resp.language,
        level=current_level,
        analysis=analysis,
        previous_answer=parent_resp.content,
        is_followup=True
    )

    total_latency_ms = int((time.perf_counter() - start_total) * 1000)

    # Save new DB response
    db_response = DBResponse(
        question_id=question.id,
        parent_response_id=parent_resp.id,
        action=payload.mode,
        content=new_answer,
        language=parent_resp.language,
        level=current_level,
        model=settings.ollama_model,
        latency_ms=total_latency_ms,
        validation_passed=val["passed"],
        validation_notes=json.dumps(val["notes"], ensure_ascii=False),
        explain_again_count=explain_again_count
    )
    db.add(db_response)
    db.commit()
    db.refresh(db_response)

    try:
        from app.models import ResponseVariant, gen_uuid, utc_now
        var = ResponseVariant(
            id=gen_uuid(),
            response_id=db_response.id,
            language=parent_resp.language,
            content=new_answer,
            origin="original",
            model=settings.ollama_model,
            created_at=utc_now()
        )
        db.add(var)
        db.commit()
    except Exception:
        db.rollback()

    return QuestionResponse(
        conversation_id=question.conversation_id,
        question_id=question.id,
        response_id=db_response.id,
        detected_language=parent_resp.language,
        intent=question.intent,
        subject=question.subject,
        topic=question.topic,
        level=current_level,
        exam_marks=question.exam_marks,
        answer=AnswerContent(
            text=new_answer,
            language=parent_resp.language
        ),
        validation=ValidationResult(
            passed=val["passed"],
            notes=val["notes"]
        ),
        meta=MetaInfo(
            model=settings.ollama_model,
            latency_ms=total_latency_ms,
            timings=TimingMeta(
                analysis_ms=0,
                generation_ms=gen_ms,
                validation_ms=10
            )
        ),
        explain_again_count=explain_again_count
    )
