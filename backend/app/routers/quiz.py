import json
import logging
import re
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Quiz, QuizAttempt, Response as DBResponse, Question, User
from app.schemas import (
    QuizCreateRequest, QuizCreateResponse, QuizQuestionClient,
    QuizSubmitRequest, QuizSubmitResponse, QuestionReview,
    ProgressResponse, TopicProgress
)
from app.pipeline.analysis import AnalysisResult
from app.pipeline.prompt_builder import build_followup_prompt
from app.services.ollama_client import ollama_client, OllamaError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["quiz"])

@router.post("/quiz", response_model=QuizCreateResponse)
async def create_quiz(payload: QuizCreateRequest, db: Session = Depends(get_db)):
    resp = db.query(DBResponse).filter(DBResponse.id == payload.response_id).first()
    if not resp:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Response not found"})
    question = db.query(Question).filter(Question.id == resp.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Question not found"})

    analysis = AnalysisResult(
        language=resp.language,
        intent="quiz",
        subject=question.subject,
        topic=question.topic,
        core_question=question.normalized_text,
        key_terms=[],
        formulas=[],
        expected_answer_type="quiz"
    )

    num_q = max(2, min(payload.num_questions, 5))
    prompts = build_followup_prompt(
        action="quiz",
        analysis=analysis,
        previous_answer=resp.content,
        target_language=resp.language,
        num_questions=num_q,
        phase=payload.phase
    )

    try:
        raw = await ollama_client.generate(
            prompt=prompts["user"],
            system=prompts["system"],
            json_format=True,
            temperature=0.2
        )
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        data = json.loads(cleaned)
        if isinstance(data, dict) and "questions" in data:
            data = data["questions"]
    except Exception as e:
        logger.warning(f"LLM quiz generation parse error ({e}), generating standard diagnostic questions.")
        lang = resp.language
        if lang == "mr":
            data = [
                {
                    "id": "q0",
                    "prompt": f"{question.topic} या संकल्पनेशी संबंधित मुख्य तत्त्व कोणते?",
                    "options": ["मूलभूत शास्त्रीय नियम", "केवळ तात्विक कल्पना", "अप्रत्यक्ष परिणाम", "यापैकी काहीही नाही"],
                    "correct_index": 0,
                    "explanation": "हे मूलभूत शास्त्रीय नियमावर आधारित आहे."
                },
                {
                    "id": "q1",
                    "prompt": "दिलेल्या नियमाचे प्रत्यक्ष व्यवहारात काय महत्त्व आहे?",
                    "options": ["दैनंदिन क्रिया समजून घेणे", "केवळ परीक्षेपुरते", "काहीही उपयोग नाही", "फक्त प्रयोगशाळेत"],
                    "correct_index": 0,
                    "explanation": "हा नियम दैनंदिन क्रियांचे शास्त्रीय कारण स्पष्ट करतो."
                }
            ]
        elif lang == "hi":
            data = [
                {
                    "id": "q0",
                    "prompt": f"{question.topic} से संबंधित मुख्य सिद्धांत क्या है?",
                    "options": ["मूलभूत वैज्ञानिक नियम", "सिर्फ एक विचार", "अप्रत्यक्ष प्रभाव", "इनमें से कोई नहीं"],
                    "correct_index": 0,
                    "explanation": "यह मौलिक वैज्ञानिक नियम पर आधारित है।"
                },
                {
                    "id": "q1",
                    "prompt": "इस नियम का व्यावहारिक जीवन में क्या महत्व है?",
                    "options": ["दैनिक क्रियाओं को समझना", "केवल परीक्षा के लिए", "कोई उपयोग नहीं", "केवल प्रयोगशाला"],
                    "correct_index": 0,
                    "explanation": "यह नियम दैनिक घटनाओं के वैज्ञानिक आधार को स्पष्ट करता है।"
                }
            ]
        else:
            data = [
                {
                    "id": "q0",
                    "prompt": f"What is the foundational principle underlying {question.topic}?",
                    "options": ["Fundamental physical law", "Hypothetical idea", "Arbitrary definition", "None of these"],
                    "correct_index": 0,
                    "explanation": "It is based on a fundamental physical principle."
                },
                {
                    "id": "q1",
                    "prompt": "What is the key takeaway of this explanation?",
                    "options": ["Practical real-world application", "Exam-only concept", "Irrelevant theory", "Laboratory only"],
                    "correct_index": 0,
                    "explanation": "It governs real-world physical interactions."
                }
            ]

    # Save Quiz to DB
    quiz = Quiz(
        response_id=resp.id,
        user_id=payload.user_id,
        questions_json=json.dumps(data, ensure_ascii=False)
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    # Prepare client-facing questions (WITHOUT correct_index or explanation)
    client_questions: List[QuizQuestionClient] = []
    for item in data:
        client_questions.append(
            QuizQuestionClient(
                id=str(item.get("id", f"q_{len(client_questions)}")),
                prompt=item.get("prompt", "Question"),
                options=item.get("options", ["A", "B", "C", "D"])
            )
        )

    return QuizCreateResponse(
        quiz_id=quiz.id,
        topic=question.topic,
        phase=payload.phase,
        questions=client_questions
    )

@router.post("/quiz/{quiz_id}/submit", response_model=QuizSubmitResponse)
def submit_quiz(quiz_id: str, payload: QuizSubmitRequest, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Quiz not found"})

    questions_data = json.loads(quiz.questions_json)
    score = 0
    total = len(questions_data)
    review_list: List[QuestionReview] = []

    for q in questions_data:
        qid = str(q.get("id"))
        correct_idx = int(q.get("correct_index", 0))
        user_ans = payload.answers.get(qid)
        if user_ans is not None and int(user_ans) == correct_idx:
            score += 1

        review_list.append(
            QuestionReview(
                id=qid,
                correct_index=correct_idx,
                explanation=q.get("explanation", "Correct textbook answer.")
            )
        )

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=payload.user_id,
        phase=payload.phase,
        score=score,
        total=total,
        answers_json=json.dumps(payload.answers)
    )
    db.add(attempt)
    db.commit()

    pct = round((score / total) * 100, 1) if total > 0 else 0.0

    return QuizSubmitResponse(
        score=score,
        total=total,
        percentage=pct,
        review=review_list
    )

@router.get("/progress", response_model=ProgressResponse)
def get_user_progress(user_id: str, db: Session = Depends(get_db)):
    # Find all attempts for user
    attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id).all()
    if not attempts:
        return ProgressResponse(total_quizzes=0, average_improvement=0.0, topics=[])

    # Group attempts by topic
    topic_map: Dict[str, Dict[str, Any]] = {}
    improvements: List[int] = []

    for att in attempts:
        quiz = db.query(Quiz).filter(Quiz.id == att.quiz_id).first()
        topic = "General Concept"
        if quiz and quiz.response_id:
            resp = db.query(DBResponse).filter(DBResponse.id == quiz.response_id).first()
            if resp:
                q = db.query(Question).filter(Question.id == resp.question_id).first()
                if q:
                    topic = q.topic

        if topic not in topic_map:
            topic_map[topic] = {"pre": None, "post": None, "total": att.total}

        if att.phase == "pre":
            topic_map[topic]["pre"] = att.score
        else:
            topic_map[topic]["post"] = att.score

    topics_list: List[TopicProgress] = []
    for top, data in topic_map.items():
        pre_s = data["pre"]
        post_s = data["post"]
        imp = None
        if pre_s is not None and post_s is not None:
            imp = post_s - pre_s
            improvements.append(imp)
        elif post_s is not None:
            imp = post_s  # direct score if no pre-test
            improvements.append(imp)

        topics_list.append(
            TopicProgress(
                topic=top,
                pre_score=pre_s,
                post_score=post_s,
                total=data["total"],
                improvement=imp
            )
        )

    avg_imp = round(sum(improvements) / len(improvements), 2) if improvements else 0.0

    return ProgressResponse(
        total_quizzes=len(attempts),
        average_improvement=avg_imp,
        topics=topics_list
    )
