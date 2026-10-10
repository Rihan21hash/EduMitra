import json
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Conversation, Question, Response as DBResponse, User
from app.schemas import ExamAnswerRequest, QuestionResponse, AnswerContent, ValidationResult, MetaInfo, TimingMeta
from app.pipeline.level_adapter import get_level_rules
from app.pipeline.orchestrator import run_pipeline
from app.pipeline.analysis import AnalysisResult
from app.pipeline.prompt_builder import build_generation_prompts
from app.pipeline.validator import validate_response
from app.services.ollama_client import ollama_client, OllamaError
from app.config import settings

router = APIRouter(prefix="/api", tags=["exam_answer"])

@router.post("/exam-answer", response_model=QuestionResponse)
async def handle_exam_answer(payload: ExamAnswerRequest, db: Session = Depends(get_db)):
    marks = payload.marks if payload.marks in [2, 5, 7, 10] else 5
    
    # Check if this is from an existing response
    if payload.response_id:
        parent_resp = db.query(DBResponse).filter(DBResponse.id == payload.response_id).first()
        if not parent_resp:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Parent response not found"})
        question = db.query(Question).filter(Question.id == parent_resp.question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Question not found"})
        
        start_total = time.perf_counter()
        analysis = AnalysisResult(
            language=parent_resp.language,
            intent="exam_answer",
            subject=question.subject,
            topic=question.topic,
            core_question=question.normalized_text,
            key_terms=[],
            formulas=[],
            expected_answer_type="exam_answer"
        )
        prompts = build_generation_prompts(
            analysis=analysis,
            target_language=parent_resp.language,
            level="exam",
            original_text=question.raw_text,
            exam_marks=marks
        )
        level_rules = get_level_rules("exam", marks)
        t0_gen = time.perf_counter()
        new_answer = await ollama_client.generate(
            prompt=prompts["user"],
            system=prompts["system"],
            temperature=0.3,
            num_predict=level_rules.get("num_predict", 400)
        )
        gen_ms = int((time.perf_counter() - t0_gen) * 1000)

        val = validate_response(
            answer_text=new_answer,
            target_language=parent_resp.language,
            level="exam",
            analysis=analysis,
            exam_marks=marks
        )
        total_latency_ms = int((time.perf_counter() - start_total) * 1000)

        db_resp = DBResponse(
            question_id=question.id,
            parent_response_id=parent_resp.id,
            action="exam_answer",
            content=new_answer,
            language=parent_resp.language,
            level="exam",
            model=settings.ollama_model,
            latency_ms=total_latency_ms,
            validation_passed=val["passed"],
            validation_notes=json.dumps(val["notes"], ensure_ascii=False),
            explain_again_count=0
        )
        db.add(db_resp)
        db.commit()
        db.refresh(db_resp)

        try:
            from app.models import ResponseVariant, gen_uuid, utc_now
            var = ResponseVariant(
                id=gen_uuid(),
                response_id=db_resp.id,
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
            response_id=db_resp.id,
            detected_language=parent_resp.language,
            intent="exam_answer",
            subject=question.subject,
            topic=question.topic,
            level="exam",
            exam_marks=marks,
            answer=AnswerContent(text=new_answer, language=parent_resp.language),
            validation=ValidationResult(passed=val["passed"], notes=val["notes"]),
            meta=MetaInfo(
                model=settings.ollama_model,
                latency_ms=total_latency_ms,
                timings=TimingMeta(analysis_ms=0, generation_ms=gen_ms, validation_ms=10)
            ),
            explain_again_count=0
        )
    else:
        # Standalone question text
        if not payload.text:
            raise HTTPException(status_code=400, detail={"code": "INVALID_INPUT", "message": "Text or response_id required"})
        
        user = db.query(User).filter(User.id == payload.user_id).first()
        if not user:
            user = User(id=payload.user_id, display_name="Guest Student")
            db.add(user)
            db.commit()

        conv_id = payload.conversation_id
        if conv_id:
            conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        else:
            conv = None
        if not conv:
            short_title = f"Exam ({marks}M): {payload.text[:30]}"
            conv = Conversation(user_id=user.id, title=short_title)
            db.add(conv)
            db.commit()
            db.refresh(conv)

        pipe_res = await run_pipeline(
            raw_text=payload.text,
            level="exam",
            exam_marks=marks,
            language_override=payload.language_override,
            conversation_id=conv.id,
            db=db
        )

        db_question = Question(
            conversation_id=conv.id,
            user_id=user.id,
            raw_text=payload.text,
            normalized_text=pipe_res["normalized_text"],
            detected_language=pipe_res["detected_language"],
            intent="exam_answer",
            subject=pipe_res["subject"],
            topic=pipe_res["topic"],
            level="exam",
            exam_marks=marks
        )
        db.add(db_question)
        db.commit()
        db.refresh(db_question)

        db_response = DBResponse(
            question_id=db_question.id,
            action="exam_answer",
            content=pipe_res["answer_text"],
            language=pipe_res["detected_language"],
            level="exam",
            model=pipe_res["model"],
            latency_ms=pipe_res["timings"]["total_ms"],
            validation_passed=pipe_res["validation"]["passed"],
            validation_notes=json.dumps(pipe_res["validation"]["notes"], ensure_ascii=False),
            explain_again_count=0
        )
        db.add(db_response)
        db.commit()
        db.refresh(db_response)

        try:
            from app.models import ResponseVariant, gen_uuid, utc_now
            var = ResponseVariant(
                id=gen_uuid(),
                response_id=db_response.id,
                language=pipe_res["detected_language"],
                content=pipe_res["answer_text"],
                origin="original",
                model=pipe_res["model"],
                created_at=utc_now()
            )
            db.add(var)
            db.commit()
        except Exception:
            db.rollback()

        return QuestionResponse(
            conversation_id=conv.id,
            question_id=db_question.id,
            response_id=db_response.id,
            detected_language=pipe_res["detected_language"],
            intent="exam_answer",
            subject=pipe_res["subject"],
            topic=pipe_res["topic"],
            level="exam",
            exam_marks=marks,
            answer=AnswerContent(text=pipe_res["answer_text"], language=pipe_res["detected_language"]),
            validation=ValidationResult(passed=pipe_res["validation"]["passed"], notes=pipe_res["validation"]["notes"]),
            meta=MetaInfo(
                model=pipe_res["model"],
                latency_ms=pipe_res["timings"]["total_ms"],
                timings=TimingMeta(
                    analysis_ms=pipe_res["timings"]["analysis_ms"],
                    generation_ms=pipe_res["timings"]["generation_ms"],
                    validation_ms=pipe_res["timings"]["validation_ms"]
                )
            ),
            explain_again_count=0
        )
