import pytest
from starlette.testclient import TestClient
from app.main import app
from app.db import SessionLocal
from app.models import User, Conversation, Question, Response as DBResponse, ResponseVariant, gen_uuid

client = TestClient(app)

def test_variant_endpoints():
    db = SessionLocal()
    user_id = gen_uuid()
    user = User(id=user_id, display_name="Variant Tester")
    db.add(user)

    conv_id = gen_uuid()
    conv = Conversation(id=conv_id, user_id=user_id, title="Variant Chat")
    db.add(conv)

    q_id = gen_uuid()
    q = Question(
        id=q_id,
        conversation_id=conv_id,
        user_id=user_id,
        raw_text="What is force?",
        normalized_text="What is force?",
        detected_language="en",
        intent="define",
        subject="Physics",
        topic="Force",
        level="beginner"
    )
    db.add(q)

    resp_id = gen_uuid()
    resp = DBResponse(
        id=resp_id,
        question_id=q_id,
        action="answer",
        content="Force is a push or pull that changes an object's motion.",
        language="en",
        level="beginner"
    )
    db.add(resp)
    db.commit()

    try:
        # 1. GET variants returns original
        res = client.get(f"/api/response/{resp_id}/variants")
        assert res.status_code == 200
        data = res.json()
        assert data["response_id"] == resp_id
        assert len(data["variants"]) >= 1
        assert any(v["language"] == "en" for v in data["variants"])

        # 2. POST same language variant returns original instantly
        res_same = client.post(f"/api/response/{resp_id}/variant", json={"language": "en"})
        assert res_same.status_code == 200
        assert res_same.json()["origin"] == "original"

        # 3. Pre-seed a Marathi variant and verify it fetches from DB
        var_id = gen_uuid()
        var = ResponseVariant(
            id=var_id,
            response_id=resp_id,
            language="mr",
            content="बल म्हणजे अशी क्रिया ज्यामुळे वस्तूच्या गतीत बदल होतो.",
            origin="translated"
        )
        db.add(var)
        db.commit()

        res_mr = client.post(f"/api/response/{resp_id}/variant", json={"language": "mr"})
        assert res_mr.status_code == 200
        assert "बल" in res_mr.json()["content"]
        assert res_mr.json()["origin"] == "translated"

    finally:
        db.close()
