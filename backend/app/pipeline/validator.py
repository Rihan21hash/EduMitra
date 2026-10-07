import difflib
import json
import os
import re
from typing import Dict, Any, List, Optional
from app.pipeline.analysis import AnalysisResult
from app.pipeline.level_adapter import get_level_rules
from app.pipeline.normalize import normalize_devanagari_digits, load_glossary

GLOSSARY = load_glossary()

def get_word_count(text: str) -> int:
    return len(re.findall(r'\S+', text))

def validate_response(
    answer_text: str,
    target_language: str,
    level: str,
    analysis: AnalysisResult,
    exam_marks: Optional[int] = None,
    previous_answer: Optional[str] = None,
    is_followup: bool = False
) -> Dict[str, Any]:
    notes: List[str] = []
    passed = True

    if not answer_text or len(answer_text.strip()) < 15:
        return {"passed": False, "notes": ["Answer is too short or empty"]}

    clean_answer = answer_text.strip()
    norm_digits_answer = normalize_devanagari_digits(clean_answer)

    # 1. Script / Language check
    deva_chars = len(re.findall(r'[\u0900-\u097F]', clean_answer))
    latin_chars = len(re.findall(r'[a-zA-Z]', clean_answer))
    total_chars = deva_chars + latin_chars

    if target_language in ["mr", "hi"] and total_chars > 0:
        deva_ratio = deva_chars / total_chars
        # Expect at least 35% Devanagari characters for Marathi/Hindi answers
        if deva_ratio < 0.35:
            notes.append(f"Target language is {target_language}, but answer contains mostly non-Devanagari text ({deva_ratio*100:.1f}%)")
            passed = False
    elif target_language == "en" and total_chars > 0:
        latin_ratio = latin_chars / total_chars
        if latin_ratio < 0.5:
            notes.append(f"Target language is English, but answer contains non-Latin script ({latin_ratio*100:.1f}%)")
            passed = False

    # 2. Key terms check
    lower_answer = clean_answer.lower()
    for term in analysis.key_terms:
        term_clean = term.lower().strip()
        found = False
        # Direct English or native match
        if term_clean in lower_answer:
            found = True
        else:
            # Check glossary translations
            trans = GLOSSARY.get(term_clean, {})
            target_trans = trans.get(target_language)
            if target_trans and target_trans in clean_answer:
                found = True
        if not found and len(analysis.key_terms) <= 4:
            # Soft note, only mark passed=False if more than half are missing
            notes.append(f"Key term '{term}' not detected in output")

    # 3. Formulas check
    for formula in analysis.formulas:
        clean_formula = re.sub(r'\s+', '', formula)
        clean_norm_answer = re.sub(r'\s+', '', norm_digits_answer)
        if clean_formula not in clean_norm_answer:
            notes.append(f"Required formula '{formula}' was not preserved accurately")
            passed = False

    # 4. Length / level tolerance check
    level_rules = get_level_rules(level, exam_marks)
    word_count = get_word_count(clean_answer)
    min_w = int(level_rules["min_words"] * 0.7)
    max_w = int(level_rules["max_words"] * 1.5)

    if word_count < min_w:
        notes.append(f"Answer word count ({word_count}) is below expected minimum ({min_w}) for {level} level")
    elif word_count > max_w:
        notes.append(f"Answer word count ({word_count}) exceeds expected maximum ({max_w}) for {level} level")

    # 5. Repeat detection for follow-ups (difflib ratio < 0.65)
    if is_followup and previous_answer:
        matcher = difflib.SequenceMatcher(None, clean_answer, previous_answer.strip())
        similarity = matcher.ratio()
        if similarity >= 0.70:
            notes.append(f"Follow-up answer is too similar to previous explanation ({similarity*100:.1f}% similarity)")
            passed = False

    return {
        "passed": passed,
        "notes": notes
    }
