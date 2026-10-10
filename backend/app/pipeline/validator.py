import difflib
import json
import os
import re
from typing import Dict, Any, List, Optional
from app.pipeline.analysis import AnalysisResult
from app.pipeline.level_adapter import get_level_rules
from app.pipeline.normalize import normalize_devanagari_digits, load_glossary

GLOSSARY = load_glossary()

# Cross-language markers for leakage detection
HINDI_MARKERS = {"है", "था", "थी", "थे", "होगा", "होगी", "नहीं", "क्या", "लेकिन", "क्योंकि", "कहा", "गया"}
MARATHI_MARKERS = {"आहे", "आहेत", "नाही", "नाहीत", "झाले", "झाला", "असेल", "असतात", "म्हणजे", "कसे", "कसा", "त्यामुळे", "तसेच"}

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

    # 1b. Cross-language leakage detection
    words_in_answer = set(re.findall(r'[\u0900-\u097F]+', clean_answer))
    if target_language == "mr":
        leaked_hi = words_in_answer.intersection(HINDI_MARKERS)
        if len(leaked_hi) >= 2:
            notes.append(f"Cross-language leakage: detected Hindi grammatical words in Marathi answer: {list(leaked_hi)[:4]}")
            # Soft note unless excessive
            if len(leaked_hi) >= 4:
                passed = False
    elif target_language == "hi":
        leaked_mr = words_in_answer.intersection(MARATHI_MARKERS)
        if len(leaked_mr) >= 2:
            notes.append(f"Cross-language leakage: detected Marathi grammatical words in Hindi answer: {list(leaked_mr)[:4]}")
            if len(leaked_mr) >= 4:
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
            notes.append(f"Key term '{term}' not detected in output")

    # 3. Formulas check
    for formula in analysis.formulas:
        clean_formula = re.sub(r'\s+', '', formula)
        clean_norm_answer = re.sub(r'\s+', '', norm_digits_answer)
        if clean_formula not in clean_norm_answer:
            notes.append(f"Required formula '{formula}' was not preserved accurately")
            passed = False

    # 4. Length / level tolerance check
    level_rules = get_level_rules(level, exam_marks, target_language=target_language)
    word_count = get_word_count(clean_answer)
    min_w = int(level_rules["min_words"] * 0.7)
    max_w = int(level_rules["max_words"] * 1.5)

    if word_count < min_w:
        notes.append(f"Answer word count ({word_count}) is below expected minimum ({min_w}) for {level} level")
    elif word_count > max_w:
        notes.append(f"Answer word count ({word_count}) exceeds expected maximum ({max_w}) for {level} level")

    # 5. Exam structure validation
    if level == "exam" and exam_marks:
        if exam_marks == 2:
            # Expect concise answer
            if word_count > 110:
                notes.append(f"2-mark answer is too long ({word_count} words; expected ~25-70)")
        elif exam_marks in (5, 7, 10):
            # Check for bullet points or headings
            has_bullets = bool(re.search(r'(?:^|\n)\s*[-*•\d\.]+\s+', clean_answer))
            has_headings = bool(re.search(r'(?:^|\n)\s*#+\s+|(?:\*\*[\w\s\(\)]+\*\*:?)', clean_answer))
            if not (has_bullets or has_headings):
                notes.append(f"{exam_marks}-mark answer lacks structured headings or bullet points")

    # 6. Repeat detection for follow-ups (difflib ratio < 0.65)
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

def validate_translation(
    original_text: str,
    translated_text: str,
    target_language: str
) -> Dict[str, Any]:
    """Validates structural, numerical, formula and linguistic fidelity of a translation."""
    notes: List[str] = []
    passed = True

    if not translated_text or len(translated_text.strip()) < 15:
        return {"passed": False, "notes": ["Translated text is empty or too short"]}

    # 1. Script check
    deva_chars = len(re.findall(r'[\u0900-\u097F]', translated_text))
    latin_chars = len(re.findall(r'[a-zA-Z]', translated_text))
    total_chars = deva_chars + latin_chars
    if target_language in ["mr", "hi"] and total_chars > 0:
        deva_ratio = deva_chars / total_chars
        if deva_ratio < 0.35:
            notes.append(f"Target language is {target_language}, but translation lacks Devanagari ({deva_ratio*100:.1f}%)")
            passed = False

    # 2. Number preservation check
    orig_digits = set(re.findall(r'\d+', normalize_devanagari_digits(original_text)))
    trans_digits = set(re.findall(r'\d+', normalize_devanagari_digits(translated_text)))
    missing_digits = orig_digits - trans_digits
    if missing_digits and len(missing_digits) > 1:
        notes.append(f"Numbers missing in translation: {missing_digits}")

    # 3. Formulas check
    orig_formulas = re.findall(r'\$[^\$\n]+?\$', original_text)
    for formula in orig_formulas:
        clean_f = re.sub(r'\s+', '', formula)
        clean_trans = re.sub(r'\s+', '', translated_text)
        if clean_f not in clean_trans:
            notes.append(f"Formula '{formula}' was lost or altered in translation")

    # 4. Structure check (bullet and heading count comparison)
    orig_bullets = len(re.findall(r'(?:^|\n)\s*[-*•\d\.]+\s+', original_text))
    trans_bullets = len(re.findall(r'(?:^|\n)\s*[-*•\d\.]+\s+', translated_text))
    if orig_bullets > 2 and trans_bullets == 0:
        notes.append("Translation lost list / bullet structure")

    orig_headings = len(re.findall(r'(?:^|\n)\s*#+\s+', original_text))
    trans_headings = len(re.findall(r'(?:^|\n)\s*#+\s+', translated_text))
    if orig_headings > 0 and trans_headings == 0:
        notes.append("Translation lost markdown heading structure")

    # 5. Cross-language leakage check
    words_in_trans = set(re.findall(r'[\u0900-\u097F]+', translated_text))
    if target_language == "mr":
        leaked_hi = words_in_trans.intersection(HINDI_MARKERS)
        if len(leaked_hi) >= 3:
            notes.append(f"Cross-language leakage: detected Hindi grammatical words in Marathi translation: {list(leaked_hi)[:4]}")
            passed = False
    elif target_language == "hi":
        leaked_mr = words_in_trans.intersection(MARATHI_MARKERS)
        if len(leaked_mr) >= 3:
            notes.append(f"Cross-language leakage: detected Marathi grammatical words in Hindi translation: {list(leaked_mr)[:4]}")
            passed = False

    # 6. Word count ratio band check
    orig_words = get_word_count(original_text)
    trans_words = get_word_count(translated_text)
    if orig_words > 0:
        ratio = trans_words / orig_words
        if ratio < 0.4 or ratio > 2.2:
            notes.append(f"Suspicious translation length ratio: {ratio:.2f} ({trans_words} vs {orig_words} words)")

    return {
        "passed": passed,
        "notes": notes
    }
