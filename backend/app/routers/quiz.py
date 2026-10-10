import json
import logging
import re
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db import get_db
from app.models import Quiz, QuizAttempt, Response as DBResponse, Question, User, Feedback
from app.schemas import (
    QuizCreateRequest, QuizCreateResponse, QuizQuestionClient,
    QuizSubmitRequest, QuizSubmitResponse, QuestionReview,
    ProgressResponse, TopicProgress, ProgressTimelineItem
)
from app.pipeline.analysis import AnalysisResult
from app.pipeline.prompt_builder import build_followup_prompt, LANGUAGE_NAMES
from app.services.ollama_client import ollama_client, OllamaError

logger = logging.getLogger("edumitra.quiz")
router = APIRouter(prefix="/api", tags=["quiz"])

def clean_and_parse_quiz_json(raw: str) -> Optional[List[Dict[str, Any]]]:
    """Robustly cleans and parses LLM JSON output for quiz questions."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    
    # Try finding first JSON object or array
    match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', cleaned)
    if match:
        cleaned = match.group(1)

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            if "questions" in data and isinstance(data["questions"], list):
                return data["questions"]
            for v in data.values():
                if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict) and "prompt" in v[0]:
                    return v
        elif isinstance(data, list):
            return data
    except Exception:
        pass
    return None

def build_fallback_questions(topic: str, lang: str) -> List[Dict[str, Any]]:
    if lang == "mr":
        return [
            {
                "id": "q0",
                "prompt": f"'{topic}' या संकल्पनेशी संबंधित मूलभूत वैज्ञानिक तत्त्व कोणते?",
                "options": ["मूलभूत वैज्ञानिक नियम व सिद्धांत", "केवळ सैद्धांतिक धारणा", "अप्रत्यक्ष योगायोग", "यांपैकी काहीही नाही"],
                "correct_index": 0,
                "explanation": f"'{topic}' ही संकल्पना शास्त्राच्या मूलभूत नियमांवर आधारलेली आहे."
            },
            {
                "id": "q1",
                "prompt": f"'{topic}' चा दैनंदिन व्यवहारात अथवा तंत्रज्ञानात मुख्य उपयोग काय आहे?",
                "options": ["वैज्ञानिक प्रक्रिया समजून अचूक वापर करणे", "केवळ घोकंपट्टी करणे", "काहीही उपयोग नसणे", "फक्त ऐतिहासिक माहितीसाठी"],
                "correct_index": 0,
                "explanation": "या नियमाचा उपयोग दैनंदिन घटनांचे शास्त्रीय कारण स्पष्ट करण्यासाठी आणि तंत्रज्ञानात होतो."
            }
        ]
    elif lang == "hi":
        return [
            {
                "id": "q0",
                "prompt": f"'{topic}' से संबंधित मूलभूत वैज्ञानिक सिद्धांत क्या है?",
                "options": ["मूलभूत वैज्ञानिक नियम और सिद्धांत", "केवल काल्पनिक विचार", "अप्रत्यक्ष संयोग", "इनमें से कोई नहीं"],
                "correct_index": 0,
                "explanation": f"'{topic}' की अवधारणा विज्ञान के मूलभूत नियमों पर आधारित है।"
            },
            {
                "id": "q1",
                "prompt": f"'{topic}' का व्यावहारिक जीवन अथवा तकनीक में मुख्य महत्व क्या है?",
                "options": ["वैज्ञानिक प्रक्रियाओं को समझना और लागू करना", "केवल रटना", "कोई उपयोग नहीं", "केवल परीक्षा तक सीमित"],
                "correct_index": 0,
                "explanation": "यह सिद्धांत वास्तविक जीवन की घटनाओं के वैज्ञानिक आधार को स्पष्ट करता है।"
            }
        ]
    else:
        return [
            {
                "id": "q0",
                "prompt": f"What is the core scientific principle behind '{topic}'?",
                "options": ["Fundamental physical law & principles", "Purely speculative hypothesis", "Coincidental observation", "None of these"],
                "correct_index": 0,
                "explanation": f"'{topic}' is anchored in fundamental academic principles."
            },
            {
                "id": "q1",
                "prompt": f"What is the primary real-world application of '{topic}'?",
                "options": ["Understanding natural processes & engineering systems", "Rote memorization only", "No practical utility", "Historical trivia"],
                "correct_index": 0,
                "explanation": "It provides the governing rules for real-world interactions and engineering."
            }
        ]

@router.post("/quiz", response_model=QuizCreateResponse)
@router.post("/quiz/generate", response_model=QuizCreateResponse)
async def create_quiz(payload: QuizCreateRequest, db: Session = Depends(get_db)):
    topic = "General Concept"
    subject = "General"
    target_lang = payload.language or "mr"
    previous_answer = ""
    resp_id = payload.response_id

    if resp_id:
        resp = db.query(DBResponse).filter(DBResponse.id == resp_id).first()
        if resp:
            target_lang = resp.language
            previous_answer = resp.content
            question = db.query(Question).filter(Question.id == resp.question_id).first()
            if question:
                topic = question.topic
                subject = question.subject
    elif payload.topic:
        topic = payload.topic.strip()
    elif payload.topic_text:
        topic = payload.topic_text.strip()

    analysis = AnalysisResult(
        language=target_lang,
        intent="quiz",
        subject=subject,
        topic=topic,
        core_question=topic,
        key_terms=[],
        formulas=[],
        expected_answer_type="quiz"
    )

    num_q = max(2, min(payload.num_questions, 5))
    lang_name = LANGUAGE_NAMES.get(target_lang, "Marathi")

    prompt = f"""Generate a high quality {num_q}-question multiple choice quiz testing student understanding of '{topic}'.
Target Language: {lang_name}
Phase: {payload.phase} (pre-check diagnostic or post-explanation mastery)

Rules:
1. Every question prompt, all 4 options, and the explanation MUST be in {lang_name}.
2. Provide exactly 4 options per question.
3. Mark correct_index as an integer between 0 and 3.
4. Output STRICT JSON in the following format and nothing else:
{{
  "questions": [
    {{
      "id": "q0",
      "prompt": "Question text in {lang_name}",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_index": 0,
      "explanation": "Why this option is correct in {lang_name}"
    }}
  ]
}}
"""
    messages = [
        {"role": "system", "content": f"You are a strict educational quiz generator. Return only valid JSON in {lang_name}."},
        {"role": "user", "content": prompt}
    ]

    data = None
    try:
        raw = await ollama_client.chat(
            messages=messages,
            json_format=True,
            temperature=0.2,
            num_predict=800
        )
        data = clean_and_parse_quiz_json(raw)
    except Exception as e:
        logger.warning(f"Ollama quiz generation error: {e}")

    if not data or len(data) < 2:
        data = build_fallback_questions(topic, target_lang)

    # Sanitize data
    sanitized_data = []
    for idx, item in enumerate(data[:num_q]):
        opts = item.get("options", [])
        if len(opts) < 4:
            while len(opts) < 4:
                opts.append(f"Option {len(opts) + 1}")
        elif len(opts) > 4:
            opts = opts[:4]

        corr = item.get("correct_index", 0)
        try:
            corr = int(corr)
            if corr < 0 or corr >= 4:
                corr = 0
        except Exception:
            corr = 0

        sanitized_data.append({
            "id": str(item.get("id", f"q{idx}")),
            "prompt": str(item.get("prompt", f"Question {idx+1}")),
            "options": [str(o) for o in opts],
            "correct_index": corr,
            "explanation": str(item.get("explanation", "Correct textbook answer."))
        })

    # Save Quiz in DB
    topic_key = re.sub(r'[^a-zA-Z0-9]', '_', topic.lower())
    quiz = Quiz(
        response_id=resp_id,
        user_id=payload.user_id,
        topic_key=topic_key,
        language=target_lang,
        subject=subject,
        topic=topic,
        questions_json=json.dumps(sanitized_data, ensure_ascii=False)
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    # Prepare client-facing questions
    client_questions: List[QuizQuestionClient] = [
        QuizQuestionClient(
            id=q["id"],
            prompt=q["prompt"],
            question=q["prompt"],
            options=q["options"],
            correct_answer=chr(65 + int(q["correct_index"])) if 0 <= int(q["correct_index"]) < 4 else "A",
            correct_index=int(q["correct_index"])
        )
        for q in sanitized_data
    ]

    return QuizCreateResponse(
        quiz_id=quiz.id,
        topic=topic,
        phase=payload.phase,
        questions=client_questions
    )

@router.post("/quiz/submit", response_model=QuizSubmitResponse)
@router.post("/quiz/{quiz_id}/submit", response_model=QuizSubmitResponse)
def submit_quiz(
    payload: QuizSubmitRequest,
    quiz_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    target_quiz_id = quiz_id or payload.quiz_id
    if not target_quiz_id:
        raise HTTPException(status_code=400, detail={"code": "INVALID_INPUT", "message": "quiz_id required"})

    quiz = db.query(Quiz).filter(Quiz.id == target_quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Quiz not found"})

    questions_data = json.loads(quiz.questions_json)
    score = 0
    total = len(questions_data)
    review_list: List[QuestionReview] = []

    letter_map = {"A": 0, "B": 1, "C": 2, "D": 3, "a": 0, "b": 1, "c": 2, "d": 3}

    for q in questions_data:
        qid = str(q.get("id"))
        correct_idx = int(q.get("correct_index", 0))
        user_ans = payload.answers.get(qid)
        user_ans_idx = None

        if user_ans is not None:
            if isinstance(user_ans, int):
                user_ans_idx = user_ans
            elif isinstance(user_ans, str):
                if user_ans in letter_map:
                    user_ans_idx = letter_map[user_ans]
                else:
                    try:
                        user_ans_idx = int(user_ans)
                    except ValueError:
                        user_ans_idx = None

        if user_ans_idx is not None and user_ans_idx == correct_idx:
            score += 1

        review_list.append(
            QuestionReview(
                id=qid,
                correct_index=correct_idx,
                explanation=q.get("explanation", "Correct textbook answer.")
            )
        )

    # Check previous attempts for baseline comparison
    prev_attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.quiz_id == quiz.id, QuizAttempt.user_id == payload.user_id)
        .order_by(QuizAttempt.created_at.asc())
        .all()
    )
    is_retake = len(prev_attempts) > 0
    baseline_type = "retake" if is_retake else "first-attempt"

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=payload.user_id,
        phase=payload.phase,
        baseline_type=baseline_type,
        score=score,
        total=total,
        answers_json=json.dumps(payload.answers)
    )
    db.add(attempt)
    db.commit()

    pct = round((score / total) * 100, 1) if total > 0 else 0.0

    delta = None
    if prev_attempts:
        baseline_score = prev_attempts[0].score
        delta = score - baseline_score

    feedback_msg = "Outstanding! Perfect score." if score == total else ("Good attempt! Review explanations to improve." if score > 0 else "Keep practicing!")

    return QuizSubmitResponse(
        score=score,
        total=total,
        total_questions=total,
        percentage=pct,
        feedback=feedback_msg,
        review=review_list,
        improvement_delta=delta
    )

@router.get("/progress", response_model=ProgressResponse)
def get_user_progress(user_id: str, db: Session = Depends(get_db)):
    # 1. Total questions asked by user
    user_questions = db.query(Question).filter(Question.user_id == user_id).all()
    questions_count = len(user_questions)
    languages_used = list({q.detected_language for q in user_questions if q.detected_language})
    levels_used = list({q.level for q in user_questions if q.level})

    # 2. Feedback satisfaction
    user_feedback = (
        db.query(Feedback)
        .join(DBResponse, Feedback.response_id == DBResponse.id)
        .join(Question, DBResponse.question_id == Question.id)
        .filter(Question.user_id == user_id)
        .all()
    )
    positive_fb = sum(1 for f in user_feedback if f.rating > 0)
    total_fb = len(user_feedback)
    satisfaction_pct = round((positive_fb / total_fb) * 100, 1) if total_fb > 0 else 100.0

    # 3. Quiz attempts
    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == user_id)
        .order_by(QuizAttempt.created_at.asc())
        .all()
    )
    if not attempts:
        return ProgressResponse(
            total_quizzes=0,
            total_quizzes_taken=0,
            average_improvement=0.0,
            average_score=0.0,
            total_questions_answered=0,
            accuracy_rate=0.0,
            questions_asked=questions_count,
            languages_used=languages_used,
            levels_used=levels_used,
            satisfaction_pct=satisfaction_pct,
            topics=[],
            topic_breakdown=[],
            timeline=[],
            recent_attempts=[]
        )

    # 4. Group by topic
    topic_data: Dict[str, Dict[str, Any]] = {}
    improvements: List[int] = []
    timeline: List[ProgressTimelineItem] = []
    recent_attempts_list: List[Dict[str, Any]] = []

    total_score_sum = sum(att.score for att in attempts)
    total_questions_sum = sum(att.total for att in attempts)
    avg_score_pct = round((total_score_sum / max(1, total_questions_sum)) * 100, 1)

    for att in attempts:
        quiz = db.query(Quiz).filter(Quiz.id == att.quiz_id).first()
        topic = quiz.topic if (quiz and quiz.topic) else "General Concept"
        
        # Timeline entry
        att_pct = round((att.score / att.total) * 100, 1) if att.total > 0 else 0.0
        time_str = att.created_at.strftime("%b %d, %H:%M") if att.created_at else ""
        
        timeline.append(ProgressTimelineItem(
            topic=topic,
            score=att.score,
            total=att.total,
            percentage=att_pct,
            phase=att.phase or "post",
            created_at=time_str
        ))
        
        recent_attempts_list.append({
            "quiz_id": att.quiz_id,
            "topic": topic,
            "score": att.score,
            "total": att.total,
            "percentage": att_pct,
            "created_at": time_str
        })

        if topic not in topic_data:
            topic_data[topic] = {
                "baseline": att.score,
                "latest": att.score,
                "total": att.total,
                "pre": None,
                "post": None,
                "count": 0
            }

        topic_data[topic]["latest"] = att.score
        topic_data[topic]["count"] += 1
        if att.phase == "pre":
            topic_data[topic]["pre"] = att.score
        else:
            topic_data[topic]["post"] = att.score

    topics_list: List[TopicProgress] = []
    topic_breakdown_list: List[Dict[str, Any]] = []

    for top, d in topic_data.items():
        base = d["baseline"]
        latest = d["latest"]
        imp = latest - base
        if d["count"] > 1:
            improvements.append(imp)
        elif d["post"] is not None and d["pre"] is not None:
            imp = d["post"] - d["pre"]
            improvements.append(imp)
        else:
            imp = latest

        topics_list.append(TopicProgress(
            topic=top,
            baseline_score=base,
            latest_score=latest,
            pre_score=d["pre"],
            post_score=d["post"],
            total=d["total"],
            improvement=imp,
            attempts_count=d["count"]
        ))
        topic_breakdown_list.append({
            "topic": top,
            "score": latest,
            "total": d["total"],
            "attempts": d["count"],
            "improvement": imp
        })

    avg_imp = round(sum(improvements) / len(improvements), 2) if improvements else 0.0

    return ProgressResponse(
        total_quizzes=len(attempts),
        total_quizzes_taken=len(attempts),
        average_improvement=avg_imp,
        average_score=avg_score_pct,
        total_questions_answered=total_questions_sum,
        accuracy_rate=avg_score_pct,
        questions_asked=questions_count,
        languages_used=languages_used,
        levels_used=levels_used,
        satisfaction_pct=satisfaction_pct,
        topics=topics_list,
        topic_breakdown=topic_breakdown_list,
        timeline=timeline,
        recent_attempts=recent_attempts_list
    )
