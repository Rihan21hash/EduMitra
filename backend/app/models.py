import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db import Base

def gen_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    display_name = Column(String(100), default="Guest Student")
    preferred_language = Column(String(10), default="mr")
    default_level = Column(String(20), default="beginner")
    created_at = Column(DateTime, default=utc_now)

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="user")
    quizzes = relationship("Quiz", back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), default="New Chat")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="conversations")
    questions = relationship("Question", back_populates="conversation", cascade="all, delete-orphan")
    state = relationship("ConversationState", back_populates="conversation", uselist=False, cascade="all, delete-orphan")

class ConversationState(Base):
    __tablename__ = "conversation_state"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, unique=True)
    summary = Column(Text, nullable=True)
    subject = Column(String(50), nullable=True)
    topic = Column(String(100), nullable=True)
    last_response_id = Column(String(36), nullable=True)
    answer_language = Column(String(10), nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    conversation = relationship("Conversation", back_populates="state")

class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    raw_text = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=False)
    detected_language = Column(String(10), nullable=False)
    intent = Column(String(50), nullable=False)
    subject = Column(String(50), nullable=False)
    topic = Column(String(100), nullable=False)
    level = Column(String(20), nullable=False)
    exam_marks = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="questions")
    conversation = relationship("Conversation", back_populates="questions")
    responses = relationship("Response", back_populates="question", cascade="all, delete-orphan")

class Response(Base):
    __tablename__ = "responses"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    question_id = Column(String(36), ForeignKey("questions.id"), nullable=False)
    parent_response_id = Column(String(36), nullable=True)
    action = Column(String(30), default="answer")  # answer, simplify, explain_again, example, translate, summarize, exam_answer
    content = Column(Text, nullable=False)
    language = Column(String(10), nullable=False)
    level = Column(String(20), nullable=False)
    model = Column(String(50), default="qwen2.5-coder:7b")
    latency_ms = Column(Integer, default=0)
    validation_passed = Column(Boolean, default=True)
    validation_notes = Column(Text, default="[]")  # JSON string
    explain_again_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

    question = relationship("Question", back_populates="responses")
    feedback = relationship("Feedback", back_populates="response", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="response", cascade="all, delete-orphan")
    variants = relationship("ResponseVariant", back_populates="response", cascade="all, delete-orphan")

class ResponseVariant(Base):
    __tablename__ = "response_variants"
    __table_args__ = (UniqueConstraint("response_id", "language", name="uq_response_language"),)

    id = Column(String(36), primary_key=True, default=gen_uuid)
    response_id = Column(String(36), ForeignKey("responses.id", ondelete="CASCADE"), nullable=False)
    language = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    origin = Column(String(20), default="generated")  # generated | translated | original
    model = Column(String(50), default="qwen2.5-coder:7b")
    created_at = Column(DateTime, default=utc_now)

    response = relationship("Response", back_populates="variants")

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    response_id = Column(String(36), ForeignKey("responses.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # +1 or -1
    created_at = Column(DateTime, default=utc_now)

    response = relationship("Response", back_populates="feedback")

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    response_id = Column(String(36), ForeignKey("responses.id"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    topic_key = Column(String(100), nullable=True)
    language = Column(String(10), nullable=True)
    subject = Column(String(50), nullable=True)
    topic = Column(String(100), nullable=True)
    questions_json = Column(Text, nullable=False)  # includes correct answers, server-side only
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="quizzes")
    response = relationship("Response", back_populates="quizzes")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    quiz_id = Column(String(36), ForeignKey("quizzes.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    phase = Column(String(10), default="post")  # pre | post
    baseline_type = Column(String(30), default="first-attempt")
    score = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    answers_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    quiz = relationship("Quiz", back_populates="attempts")
