import os
from typing import Dict, Any, List, Optional
from app.pipeline.analysis import AnalysisResult
from app.pipeline.level_adapter import get_level_rules

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")

LANGUAGE_NAMES = {
    "mr": "Marathi (मराठी)",
    "hi": "Hindi (हिंदी)",
    "en": "English"
}

def load_prompt_file(rel_path: str) -> str:
    full_path = os.path.join(PROMPTS_DIR, rel_path)
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""

SYSTEM_TEMPLATE = load_prompt_file("system.txt")
USER_TEMPLATE = load_prompt_file("user_template.txt")

def build_generation_prompts(
    analysis: AnalysisResult,
    target_language: str,
    level: str,
    original_text: str,
    exam_marks: Optional[int] = None,
    validation_feedback: Optional[str] = None
) -> Dict[str, str]:
    """
    Builds system and user prompts for generation stage.
    """
    lang_name = LANGUAGE_NAMES.get(target_language, "Marathi")
    level_rules_obj = get_level_rules(level, exam_marks)
    level_rules_text = level_rules_obj["instruction"]

    system_prompt = SYSTEM_TEMPLATE.replace("{language_name}", lang_name)

    val_str = ""
    if validation_feedback:
        val_str = f"\nNote from validator on previous attempt: {validation_feedback}. Please address this."

    user_prompt = USER_TEMPLATE.format(
        language_name=lang_name,
        level=level,
        subject=analysis.subject,
        topic=analysis.topic,
        intent=analysis.intent,
        core_question=analysis.core_question,
        key_terms=", ".join(analysis.key_terms) if analysis.key_terms else "None",
        formulas=", ".join(analysis.formulas) if analysis.formulas else "None",
        level_rules=level_rules_text,
        original_text=original_text,
        validation_feedback=val_str
    )

    return {
        "system": system_prompt,
        "user": user_prompt
    }

def build_followup_prompt(
    action: str,
    analysis: AnalysisResult,
    previous_answer: str,
    target_language: str,
    level: str = "beginner",
    explain_again_count: int = 1,
    num_questions: int = 3,
    phase: str = "post"
) -> Dict[str, str]:
    lang_name = LANGUAGE_NAMES.get(target_language, "Marathi")
    system_prompt = SYSTEM_TEMPLATE.replace("{language_name}", lang_name)

    if action == "simplify":
        template = load_prompt_file("followups/simplify.txt")
        # Step down level
        level_step_down = {
            "advanced": "intermediate",
            "intermediate": "beginner",
            "exam": "beginner",
            "beginner": "beginner"
        }
        target_level = level_step_down.get(level.lower(), "beginner")
        user_prompt = template.format(
            language_name=lang_name,
            target_level=target_level,
            core_question=analysis.core_question,
            previous_answer=previous_answer,
            key_terms=", ".join(analysis.key_terms)
        )
    elif action == "explain_again":
        template = load_prompt_file("followups/explain_again.txt")
        escalation = ""
        if explain_again_count >= 3:
            escalation = "ATTENTION: This is attempt #3. Explain in the absolute simplest child-like story or visual analogy. Conclude by warmly suggesting the student discuss with their teacher and offer a quick diagnostic quiz."
        user_prompt = template.format(
            language_name=lang_name,
            level=level,
            core_question=analysis.core_question,
            key_terms=", ".join(analysis.key_terms),
            explain_again_count=explain_again_count,
            previous_answer=previous_answer,
            escalation_note=escalation
        )
    elif action == "example":
        template = load_prompt_file("followups/example.txt")
        user_prompt = template.format(
            language_name=lang_name,
            subject=analysis.subject,
            topic=analysis.topic,
            core_question=analysis.core_question,
            previous_answer=previous_answer
        )
    elif action == "translate":
        template = load_prompt_file("followups/translate.txt")
        user_prompt = template.format(
            target_language_name=lang_name,
            previous_answer=previous_answer
        )
    elif action == "summarize":
        template = load_prompt_file("followups/summarize.txt")
        user_prompt = template.format(
            language_name=lang_name,
            previous_answer=previous_answer
        )
    elif action == "quiz":
        template = load_prompt_file("followups/quiz.txt")
        user_prompt = template.format(
            num_questions=num_questions,
            language_name=lang_name,
            subject=analysis.subject,
            topic=analysis.topic,
            core_question=analysis.core_question,
            phase=phase
        )
    else:
        user_prompt = f"Explain {analysis.core_question} in {lang_name}."

    return {
        "system": system_prompt,
        "user": user_prompt
    }
