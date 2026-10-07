import pytest
from fastapi.testclient import TestClient
from app.main import app

from app.db import Base, engine

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "active_model" in data

def test_user_creation():
    res = client.post("/api/users", json={
        "display_name": "Test Student",
        "preferred_language": "mr",
        "default_level": "beginner"
    })
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert data["display_name"] == "Test Student"

def test_conversations_empty_history():
    res = client.get("/api/history?user_id=non-existent-user")
    assert res.status_code == 200
    assert res.json() == []
