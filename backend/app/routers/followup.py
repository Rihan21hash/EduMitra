import json
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Response as DBResponse, Question
from app.schemas import FollowUpRequest, QuestionResponse, AnswerContent, ValidationResult, MetaInfo, TimingMeta
from app.pipeline.analysis import AnalysisResult
from app.pipeline.prompt_builder import build_followup_prompt
from app.pipeline.validator import validate_response
from app.services.ollama_client import ollama_client, OllamaError
from app.config import settings

router = APIRouter(prefix="/api", tags=["followup"])

@router.post("/followup", response_model=QuestionResponse)
async def handle_followup(payload: FollowUpRequest, db: Session = Depends(get_db)):
    parent_resp = db.query(DBResponse).filter(DBResponse.id == payload.response_id).first()
    if not parent_resp:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Parent response not found"})
    question = db.query(Question).filter(Question.id == parent_resp.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Question not found"})

    target_lang = payload.target_language or parent_resp.language

    analysis = AnalysisResult(
        language=target_lang,
        intent=question.intent,
        subject=question.subject,
        topic=question.topic,
        core_question=question.normalized_text,
        key_terms=[],
        formulas=[],
        expected_answer_type="explanation"
    )

    prompts = build_followup_prompt(
        action=payload.action,
        analysis=analysis,
        previous_answer=parent_resp.content,
        target_language=target_lang,
        level=parent_resp.level
    )

    start_total = time.perf_counter()
    t0_gen = time.perf_counter()
    new_answer = await ollama_client.generate(prompt=prompts["user"], system=prompts["system"], temperature=0.4)
    gen_ms = int((time.perf_counter() - t0_gen) * 1000)

    val = validate_response(
        answer_text=new_answer,
        target_language=target_lang,
        level=parent_resp.level,
        analysis=analysis,
        previous_answer=parent_resp.content,
        is_followup=True
    )
    total_latency_ms = int((time.perf_counter() - start_total) * 1000)

    db_resp = DBResponse(
        question_id=question.id,
        parent_response_id=parent_resp.id,
        action=payload.action,
        content=new_answer,
        language=target_lang,
        level=parent_resp.level,
        model=settings.ollama_model,
        latency_ms=total_latency_ms,
        validation_passed=val["passed"],
        validation_notes=json.dumps(val["notes"], ensure_ascii=False),
        explain_again_count=0
    )
    db.add(db_resp)
    db.commit()
    db.refresh(db_resp)

    return QuestionResponse(
        conversation_id=question.conversation_id,
        question_id=question.id,
        response_id=db_resp.id,
        detected_language=target_lang,
        intent=question.intent,
        subject=question.subject,
        topic=question.topic,
        level=parent_resp.level,
        exam_marks=question.exam_marks,
        answer=AnswerContent(text=new_answer, language=target_lang),
        validation=ValidationResult(passed=val["passed"], notes=val["notes"]),
        meta=MetaInfo(
            model=settings.ollama_model,
            latency_ms=total_latency_ms,
            timings=TimingMeta(analysis_ms=0, generation_ms=gen_ms, validation_ms=10)
        ),
        explain_again_count=0
    )
