import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import Conversation, ConversationState, Question, Response as DBResponse, gen_uuid, utc_now
from app.config import settings

logger = logging.getLogger("edumitra.context_manager")

def get_or_create_conversation_state(conversation_id: str, db: Session) -> ConversationState:
    """Gets existing conversation state or creates a new record."""
    state = db.query(ConversationState).filter(ConversationState.conversation_id == conversation_id).first()
    if not state:
        state = ConversationState(
            id=gen_uuid(),
            conversation_id=conversation_id,
            summary=None,
            subject=None,
            topic=None,
            last_response_id=None,
            answer_language=None,
            updated_at=utc_now()
        )
        db.add(state)
        try:
            db.commit()
            db.refresh(state)
        except Exception:
            db.rollback()
            state = db.query(ConversationState).filter(ConversationState.conversation_id == conversation_id).first()
    return state

def update_conversation_state(
    conversation_id: str,
    db: Session,
    subject: Optional[str] = None,
    topic: Optional[str] = None,
    last_response_id: Optional[str] = None,
    answer_language: Optional[str] = None,
    summary: Optional[str] = None
) -> ConversationState:
    """Updates the state record for a given conversation."""
    state = get_or_create_conversation_state(conversation_id, db)
    if subject:
        state.subject = subject
    if topic:
        state.topic = topic
    if last_response_id:
        state.last_response_id = last_response_id
    if answer_language:
        state.answer_language = answer_language
    if summary:
        state.summary = summary
    state.updated_at = utc_now()
    try:
        db.commit()
        db.refresh(state)
    except Exception as e:
        logger.warning(f"Failed to commit conversation_state update: {e}")
        db.rollback()
    return state

def load_conversation_history(
    conversation_id: str,
    db: Session,
    max_turns: Optional[int] = None
) -> List[Dict[str, str]]:
    """
    Loads the last K dialogue turns for a conversation as a list of message dicts.
    Returns: [{'role': 'user', 'content': ...}, {'role': 'assistant', 'content': ...}, ...]
    """
    if not conversation_id:
        return []

    turns_limit = max_turns or settings.max_history_turns
    
    # Query questions for this conversation in chronological order
    questions = (
        db.query(Question)
        .filter(Question.conversation_id == conversation_id)
        .order_by(Question.created_at.asc())
        .all()
    )

    if not questions:
        return []

    # Slice the last K questions
    recent_questions = questions[-turns_limit:]
    history_messages: List[Dict[str, str]] = []

    for q in recent_questions:
        # Add user question
        history_messages.append({
            "role": "user",
            "content": q.raw_text
        })
        # Find latest answer for this question
        latest_resp = (
            db.query(DBResponse)
            .filter(DBResponse.question_id == q.id)
            .order_by(desc(DBResponse.created_at))
            .first()
        )
        if latest_resp and latest_resp.content:
            # Token budgeting: keep assistant history concise so prompt context stays lean
            content = latest_resp.content
            if len(content) > 1200:
                content = content[:1200] + "..."
            history_messages.append({
                "role": "assistant",
                "content": content
            })

    return history_messages

def resolve_context_for_followup(
    current_text: str,
    state: Optional[ConversationState]
) -> Dict[str, Optional[str]]:
    """
    If the question is brief or a follow-up (e.g. 'explain with an example', 'third law', 'give details'),
    enriches the subject/topic context from conversation_state.
    """
    inferred_subject = state.subject if state else None
    inferred_topic = state.topic if state else None
    return {
        "subject": inferred_subject,
        "topic": inferred_topic,
        "summary": state.summary if state else None
    }
