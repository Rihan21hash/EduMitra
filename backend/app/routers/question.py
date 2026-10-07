import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User, Conversation, Question, Response as DBResponse
from app.schemas import QuestionRequest, QuestionResponse, AnswerContent, ValidationResult, MetaInfo, TimingMeta
from app.pipeline.orchestrator import run_pipeline
from app.services.ollama_client import OllamaError

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

    # 3. Execute NLP pipeline
    try:
        pipe_res = await run_pipeline(
            raw_text=payload.text,
            level=payload.level,
            exam_marks=payload.exam_marks,
            language_override=payload.language_override
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
