import pytest
from app.db import SessionLocal
from app.models import Conversation, Question, Response as DBResponse, User, gen_uuid
from app.pipeline.context_manager import (
    get_or_create_conversation_state,
    update_conversation_state,
    load_conversation_history,
    resolve_context_for_followup
)

def test_conversation_state_lifecycle():
    db = SessionLocal()
    user_id = gen_uuid()
    user = User(id=user_id, display_name="Test Student")
    db.add(user)
    
    conv_id = gen_uuid()
    conv = Conversation(id=conv_id, user_id=user_id, title="Physics Chat")
    db.add(conv)
    db.commit()

    try:
        # 1. State creation
        state = get_or_create_conversation_state(conv_id, db)
        assert state.conversation_id == conv_id
        assert state.summary is None

        # 2. Update state
        updated = update_conversation_state(
            conv_id,
            db,
            subject="Physics",
            topic="Inertia",
            answer_language="mr",
            summary="Discussed Newton first law"
        )
        assert updated.topic == "Inertia"
        assert updated.answer_language == "mr"
        assert updated.summary == "Discussed Newton first law"

        # 3. Resolve context
        ctx = resolve_context_for_followup("give an example", updated)
        assert ctx["topic"] == "Inertia"
        assert ctx["subject"] == "Physics"

        # 4. History loading
        q_id = gen_uuid()
        q = Question(
            id=q_id,
            conversation_id=conv_id,
            user_id=user_id,
            raw_text="What is inertia?",
            normalized_text="What is inertia?",
            detected_language="en",
            intent="define",
            subject="Physics",
            topic="Inertia",
            level="beginner"
        )
        db.add(q)
        resp = DBResponse(
            id=gen_uuid(),
            question_id=q_id,
            action="answer",
            content="Inertia is resistance to change in motion.",
            language="en",
            level="beginner"
        )
        db.add(resp)
        db.commit()

        history = load_conversation_history(conv_id, db)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "What is inertia?"
        assert history[1]["role"] == "assistant"
        assert "Inertia" in history[1]["content"]

    finally:
        db.close()
