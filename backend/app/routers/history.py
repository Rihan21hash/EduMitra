from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Conversation, Question, Response as DBResponse
from app.schemas import ConversationSummary, ConversationDetail, MessageItem

router = APIRouter(prefix="/api", tags=["history"])

@router.get("/history", response_model=List[ConversationSummary])
def list_history(user_id: str, db: Session = Depends(get_db)):
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .limit(30)
        .all()
    )
    return [
        ConversationSummary(
            id=c.id,
            title=c.title or "New Chat",
            created_at=c.created_at.isoformat() if c.created_at else "",
            updated_at=c.updated_at.isoformat() if c.updated_at else ""
        )
        for c in convs
    ]

@router.get("/conversations/{id}", response_model=ConversationDetail)
def get_conversation_detail(id: str, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == id).first()
    if not conv:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Conversation not found"})

    questions = db.query(Question).filter(Question.conversation_id == id).order_by(Question.created_at.asc()).all()
    messages: List[MessageItem] = []

    for q in questions:
        # Get the latest response for this question
        latest_resp = (
            db.query(DBResponse)
            .filter(DBResponse.question_id == q.id)
            .order_by(DBResponse.created_at.desc())
            .first()
        )
        if latest_resp:
            messages.append(
                MessageItem(
                    question_id=q.id,
                    response_id=latest_resp.id,
                    raw_text=q.raw_text,
                    answer_text=latest_resp.content,
                    language=latest_resp.language,
                    level=latest_resp.level,
                    exam_marks=q.exam_marks,
                    intent=q.intent,
                    subject=q.subject,
                    topic=q.topic,
                    validation_passed=latest_resp.validation_passed,
                    explain_again_count=latest_resp.explain_again_count or 0,
                    created_at=latest_resp.created_at.isoformat() if latest_resp.created_at else ""
                )
            )

    return ConversationDetail(
        id=conv.id,
        title=conv.title or "Chat",
        messages=messages
    )

@router.delete("/conversations/{id}")
def delete_conversation(id: str, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == id).first()
    if not conv:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Conversation not found"})
    db.delete(conv)
    db.commit()
    return {"success": True, "id": id}
