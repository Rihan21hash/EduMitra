import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User, Conversation, Question, Response as DBResponse, ResponseVariant, gen_uuid, utc_now
from app.schemas import QuestionRequest, QuestionResponse, AnswerContent, ValidationResult, MetaInfo, TimingMeta
from app.pipeline.orchestrator import run_pipeline, run_pipeline_stream
from app.services.ollama_client import OllamaError
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["question"])

@router.post("/question", response_model=QuestionResponse)
async def handle_question(payload: QuestionRequest, db: Session = Depends(get_db)):
    # 1. Verify user or create guest fallback
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        user = User(id=payload.user_id, display_name="Guest Student")
        db.add(user)
        db.commit()

    # 2. Get or create conversation
    conv_id = payload.conversation_id
    if conv_id:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    else:
        conv = None

    if not conv:
        short_title = payload.text.strip().split("\n")[0][:40] or "New Chat"
        conv = Conversation(user_id=user.id, title=short_title)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # 3. Execute NLP pipeline with conversation memory
    try:
        pipe_res = await run_pipeline(
            raw_text=payload.text,
            level=payload.level,
            exam_marks=payload.exam_marks,
            language_override=payload.language_override,
            conversation_id=conv.id,
            db=db
        )
    except OllamaError as oe:
        status_code = 503 if oe.code == "MODEL_UNAVAILABLE" else (504 if oe.code == "MODEL_TIMEOUT" else 500)
        raise HTTPException(
            status_code=status_code,
            detail={"code": oe.code, "message": oe.message}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL", "message": str(e)}
        )

    # 4. Save Question to DB
    db_question = Question(
        conversation_id=conv.id,
        user_id=user.id,
        raw_text=payload.text,
        normalized_text=pipe_res["normalized_text"],
        detected_language=pipe_res["detected_language"],
        intent=pipe_res["intent"],
        subject=pipe_res["subject"],
        topic=pipe_res["topic"],
        level=pipe_res["level"],
        exam_marks=pipe_res["exam_marks"]
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)

    # 5. Save Response to DB
    db_response = DBResponse(
        question_id=db_question.id,
        action="answer",
        content=pipe_res["answer_text"],
        language=pipe_res["detected_language"],
        level=pipe_res["level"],
        model=pipe_res["model"],
        latency_ms=pipe_res["timings"]["total_ms"],
        validation_passed=pipe_res["validation"]["passed"],
        validation_notes=json.dumps(pipe_res["validation"]["notes"], ensure_ascii=False),
        explain_again_count=0
    )
    db.add(db_response)
    db.commit()
    db.refresh(db_response)

    # 6. Save initial ResponseVariant
    try:
        variant = ResponseVariant(
            id=gen_uuid(),
            response_id=db_response.id,
            language=pipe_res["detected_language"],
            content=pipe_res["answer_text"],
            origin="original",
            model=pipe_res["model"],
            created_at=utc_now()
        )
        db.add(variant)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to save initial response variant: {e}")
        db.rollback()

    return QuestionResponse(
        conversation_id=conv.id,
        question_id=db_question.id,
        response_id=db_response.id,
        detected_language=pipe_res["detected_language"],
        intent=pipe_res["intent"],
        subject=pipe_res["subject"],
        topic=pipe_res["topic"],
        level=pipe_res["level"],
        exam_marks=pipe_res["exam_marks"],
        answer=AnswerContent(
            text=pipe_res["answer_text"],
            language=pipe_res["detected_language"]
        ),
        validation=ValidationResult(
            passed=pipe_res["validation"]["passed"],
            notes=pipe_res["validation"]["notes"]
        ),
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

@router.post("/question/stream")
async def handle_question_stream(payload: QuestionRequest, db: Session = Depends(get_db)):
    """
    Streaming endpoint returning Server-Sent Events (SSE) for low TTFT interactive experience.
    """
    # 1. User resolution
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        user = User(id=payload.user_id, display_name="Guest Student")
        db.add(user)
        db.commit()

    # 2. Conversation resolution
    conv_id = payload.conversation_id
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first() if conv_id else None
    if not conv:
        short_title = payload.text.strip().split("\n")[0][:40] or "New Chat"
        conv = Conversation(user_id=user.id, title=short_title)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    async def sse_event_stream():
        meta_data = {}
        full_text = ""
        timings_data = {}
        val_result = {}

        try:
            async for chunk in run_pipeline_stream(
                raw_text=payload.text,
                level=payload.level,
                exam_marks=payload.exam_marks,
                language_override=payload.language_override,
                conversation_id=conv.id,
                db=db
            ):
                ev = chunk.get("event")
                data = chunk.get("data", {})

                if ev == "meta":
                    meta_data = data
                    meta_data["conversation_id"] = conv.id
                    yield f"event: meta\ndata: {json.dumps(meta_data, ensure_ascii=False)}\n\n"

                elif ev == "token":
                    yield f"event: token\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

                elif ev == "done":
                    full_text = data.get("answer_text", "")
                    timings_data = data.get("timings", {})

                elif ev == "validation":
                    val_result = data

            # Save Question and Response to DB
            db_question = Question(
                conversation_id=conv.id,
                user_id=user.id,
                raw_text=payload.text,
                normalized_text=payload.text,
                detected_language=meta_data.get("language", "mr"),
                intent=meta_data.get("intent", "explain"),
                subject=meta_data.get("subject", "General"),
                topic=meta_data.get("topic", "General"),
                level=payload.level,
                exam_marks=payload.exam_marks
            )
            db.add(db_question)
            db.commit()
            db.refresh(db_question)

            db_response = DBResponse(
                question_id=db_question.id,
                action="answer",
                content=full_text,
                language=meta_data.get("language", "mr"),
                level=payload.level,
                model=settings.ollama_model,
                latency_ms=timings_data.get("total_ms", 0),
                validation_passed=val_result.get("passed", True),
                validation_notes=json.dumps(val_result.get("notes", []), ensure_ascii=False),
                explain_again_count=0
            )
            db.add(db_response)
            db.commit()
            db.refresh(db_response)

            # Save initial ResponseVariant
            try:
                variant = ResponseVariant(
                    id=gen_uuid(),
                    response_id=db_response.id,
                    language=meta_data.get("language", "mr"),
                    content=full_text,
                    origin="original",
                    model=settings.ollama_model,
                    created_at=utc_now()
                )
                db.add(variant)
                db.commit()
            except Exception as e:
                logger.warning(f"Error persisting initial variant: {e}")
                db.rollback()

            done_payload = {
                "conversation_id": conv.id,
                "question_id": db_question.id,
                "response_id": db_response.id,
                "answer_text": full_text,
                "timings": timings_data,
                "validation": val_result
            }
            yield f"event: done\ndata: {json.dumps(done_payload, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'code': 'INTERNAL', 'message': str(e)})}\n\n"

    return StreamingResponse(
        sse_event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
