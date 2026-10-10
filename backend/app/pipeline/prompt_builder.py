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

from app.lexicon import lexicon_manager

STYLE_GUIDES = {
    "mr": load_prompt_file("style/marathi.md"),
    "hi": load_prompt_file("style/hindi.md")
}

EXEMPLARS = {
    ("mr", "beginner"): load_prompt_file("examples/mr_beginner.md"),
    ("mr", "intermediate"): load_prompt_file("examples/mr_intermediate.md"),
    ("mr", "advanced"): load_prompt_file("examples/mr_advanced.md"),
    ("hi", "beginner"): load_prompt_file("examples/hi_beginner.md"),
    ("hi", "intermediate"): load_prompt_file("examples/hi_intermediate.md"),
    ("hi", "advanced"): load_prompt_file("examples/hi_advanced.md"),
}

def build_system_prompt(target_language: str, level: str, context_text: str = "") -> str:
    """Builds an enriched system prompt including style guidelines, lexicon, and exemplars."""
    lang_name = LANGUAGE_NAMES.get(target_language, "Marathi")
    base_sys = SYSTEM_TEMPLATE.replace("{language_name}", lang_name)
    parts = [base_sys]

    # 1. Style Guide
    style = STYLE_GUIDES.get(target_language)
    if style:
        parts.append(f"\n---\n{style}")

    # 2. Lexicon / Dictionary integration
    if context_text and target_language in ("mr", "hi"):
        terms = lexicon_manager.get_relevant_terms(context_text, target_language, max_terms=20)
        lex_formatted = lexicon_manager.format_for_prompt(terms, target_language)
        if lex_formatted:
            parts.append(f"\n---\n{lex_formatted}")

    # 3. Few-shot Exemplar
    exemplar = EXEMPLARS.get((target_language, level.lower()))
    if exemplar:
        parts.append(f"\n---\n### संदर्भ उदाहरण (Exemplar Format Reference):\n{exemplar}")

    return "\n".join(parts)

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
    level_rules_obj = get_level_rules(level, exam_marks, target_language=target_language)
    level_rules_text = level_rules_obj["instruction"]

    system_prompt = build_system_prompt(target_language, level, f"{original_text} {' '.join(analysis.key_terms)}")

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

def build_chat_messages(
    analysis: AnalysisResult,
    target_language: str,
    level: str,
    original_text: str,
    exam_marks: Optional[int] = None,
    validation_feedback: Optional[str] = None,
    conversation_state: Optional[Any] = None,
    history_messages: Optional[List[Dict[str, str]]] = None
) -> List[Dict[str, str]]:
    """
    Builds the messages[] array for Ollama /api/chat including:
    - Enriched system prompt (rules + style + lexicon + exemplar)
    - Conversation state summary (if present)
    - Past conversation turns
    - Current user prompt
    """
    prompts = build_generation_prompts(
        analysis=analysis,
        target_language=target_language,
        level=level,
        original_text=original_text,
        exam_marks=exam_marks,
        validation_feedback=validation_feedback
    )

    messages: List[Dict[str, str]] = []

    # 1. Main system prompt
    messages.append({
        "role": "system",
        "content": prompts["system"]
    })

    # 2. Conversation state context if present
    if conversation_state:
        state_parts = []
        if getattr(conversation_state, "subject", None):
            state_parts.append(f"Subject: {conversation_state.subject}")
        if getattr(conversation_state, "topic", None):
            state_parts.append(f"Topic: {conversation_state.topic}")
        if getattr(conversation_state, "summary", None):
            state_parts.append(f"Rolling Summary: {conversation_state.summary}")
        if state_parts:
            messages.append({
                "role": "system",
                "content": "Active Discussion Context:\n" + "\n".join(state_parts)
            })

    # 3. Dialogue history (past turns)
    if history_messages:
        for msg in history_messages:
            messages.append(msg)

    # 4. Current user prompt
    messages.append({
        "role": "user",
        "content": prompts["user"]
    })

    return messages

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
