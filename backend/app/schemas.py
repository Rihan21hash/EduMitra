from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# Health
class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool
    active_model: str
    available_models: List[str]
    model_loaded: Optional[bool] = False

# User
class UserCreate(BaseModel):
    display_name: Optional[str] = "Guest Student"
    preferred_language: Optional[str] = "mr"
    default_level: Optional[str] = "beginner"

class UserResponse(BaseModel):
    id: str
    display_name: str
    preferred_language: str
    default_level: str
    created_at: str

# Question Pipeline
class QuestionRequest(BaseModel):
    user_id: str
    conversation_id: Optional[str] = None
    text: str = Field(..., max_length=1500)
    level: str = "beginner"  # beginner, intermediate, advanced, exam
    exam_marks: Optional[int] = None
    language_override: str = "auto"  # auto, mr, hi, en

class AnswerContent(BaseModel):
    text: str
    language: str

class ValidationResult(BaseModel):
    passed: bool
    notes: List[str] = []

class TimingMeta(BaseModel):
    analysis_ms: int = 0
    generation_ms: int = 0
    validation_ms: int = 0

class MetaInfo(BaseModel):
    model: str
    latency_ms: int
    timings: TimingMeta

class QuestionResponse(BaseModel):
    conversation_id: str
    question_id: str
    response_id: str
    detected_language: str
    intent: str
    subject: str
    topic: str
    level: str
    exam_marks: Optional[int] = None
    answer: AnswerContent
    validation: ValidationResult
    meta: MetaInfo
    explain_again_count: Optional[int] = 0

# Simplify & Explain Again
class SimplifyRequest(BaseModel):
    user_id: str
    response_id: str
    mode: str = "simplify"  # simplify | explain_again

# Follow-up
class FollowUpRequest(BaseModel):
    user_id: str
    response_id: str
    action: str  # example, translate, summarize
    target_language: Optional[str] = None

# Exam Answer
class ExamAnswerRequest(BaseModel):
    user_id: str
    conversation_id: Optional[str] = None
    response_id: Optional[str] = None
    text: Optional[str] = None
    marks: int = 5
    language_override: str = "auto"

# Quiz
class QuizCreateRequest(BaseModel):
    user_id: str
    response_id: Optional[str] = None
    topic_text: Optional[str] = None
    topic: Optional[str] = None
    language: Optional[str] = "mr"
    num_questions: int = 3
    phase: str = "post"  # pre | post
    is_diagnostic: Optional[bool] = False

class QuizQuestionClient(BaseModel):
    id: str
    prompt: str
    question: Optional[str] = None
    options: List[str]
    correct_answer: Optional[str] = None
    correct_index: Optional[int] = None

class QuizCreateResponse(BaseModel):
    quiz_id: str
    topic: str
    phase: str
    questions: List[QuizQuestionClient]

class QuizSubmitRequest(BaseModel):
    user_id: str
    quiz_id: Optional[str] = None
    phase: str = "post"
    baseline_type: Optional[str] = "standard"
    time_taken_seconds: Optional[int] = 0
    answers: Dict[str, Any]  # { "q0": 1, "q1": "A" }

class QuestionReview(BaseModel):
    id: str
    correct_index: int
    explanation: str

class QuizSubmitResponse(BaseModel):
    score: int
    total: int
    total_questions: Optional[int] = None
    percentage: float
    feedback: Optional[str] = "Good attempt! Keep practicing."
    review: List[QuestionReview] = []
    improvement_delta: Optional[int] = None

# Progress
class TopicProgress(BaseModel):
    topic: str
    baseline_score: Optional[int] = None
    latest_score: Optional[int] = None
    pre_score: Optional[int] = None
    post_score: Optional[int] = None
    total: int
    improvement: Optional[int] = None
    attempts_count: int = 1

class ProgressTimelineItem(BaseModel):
    topic: str
    score: int
    total: int
    percentage: float
    phase: str
    created_at: str

class ProgressResponse(BaseModel):
    total_quizzes: int
    total_quizzes_taken: Optional[int] = None
    average_improvement: float
    average_score: Optional[float] = None
    total_questions_answered: Optional[int] = 0
    accuracy_rate: Optional[float] = 0.0
    questions_asked: int = 0
    languages_used: List[str] = []
    levels_used: List[str] = []
    satisfaction_pct: float = 100.0
    topics: List[TopicProgress] = []
    topic_breakdown: Optional[List[Dict[str, Any]]] = []
    timeline: List[ProgressTimelineItem] = []
    recent_attempts: Optional[List[Dict[str, Any]]] = []

# Feedback
class FeedbackRequest(BaseModel):
    response_id: str
    rating: int  # 1 or -1

class FeedbackResponse(BaseModel):
    success: bool
    rating: int

# History
class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str

class MessageItem(BaseModel):
    question_id: str
    response_id: str
    raw_text: str
    answer_text: str
    language: str
    level: str
    exam_marks: Optional[int] = None
    intent: str
    subject: str
    topic: str
    validation_passed: bool
    explain_again_count: int
    created_at: str

class ConversationDetail(BaseModel):
    id: str
    title: str
    messages: List[MessageItem]
