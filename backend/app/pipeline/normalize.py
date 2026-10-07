import json
import os
import re
import unicodedata
from typing import Dict, Any, List

GLOSSARY_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "glossary.json")

def load_glossary():
    try:
        with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

GLOSSARY = load_glossary()

DEVA_TO_ASCII_DIGITS = {
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
}

def normalize_devanagari_digits(text: str) -> str:
    """Converts Devanagari digits to ASCII digits for parsing."""
    result = []
    for ch in text:
        result.append(DEVA_TO_ASCII_DIGITS.get(ch, ch))
    return "".join(result)

def clean_zero_width_chars(text: str) -> str:
    """
    Remove zero-width characters except ZWJ (\u200D) and ZWNJ (\u200C)
    when surrounded by Devanagari characters.
    """
    # Replace zero-width space (\u200B), byte order mark (\uFEFF), etc.
    text = re.sub(r'[\u200B\uFEFF\u2060]', '', text)
    
    # Filter ZWJ / ZWNJ if not in Devanagari context
    def preserve_devanagari_zw(match):
        char = match.group(0)
        # Keep ZWJ / ZWNJ
        return char

    return text

def normalize_text(text: str) -> Dict[str, Any]:
    """
    Normalizes input text according to PRD 8.2.
    Returns:
        {
            "original_text": text,
            "normalized_text": normalized_text,
            "digit_ascii_text": text_with_ascii_digits,
            "matched_glossary_terms": List[str]
        }
    """
    if not text:
        return {
            "original_text": "",
            "normalized_text": "",
            "digit_ascii_text": "",
            "matched_glossary_terms": []
        }

    # 1. Unicode NFC
    norm = unicodedata.normalize("NFC", text)

    # 2. Clean non-essential zero-width chars
    norm = clean_zero_width_chars(norm)

    # 3. Map danda । to .
    norm = norm.replace("।", ".")

    # 4. Collapse multiple spaces/tabs while preserving linebreaks cleanly
    lines = norm.splitlines()
    cleaned_lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in lines]
    normalized_text = "\n".join(cleaned_lines).strip()

    # Digits mapping for parsing
    digit_ascii_text = normalize_devanagari_digits(normalized_text)

    # Find glossary terms in text
    matched_terms = []
    lower_text = normalized_text.lower()
    for eng_term, translations in GLOSSARY.items():
        if eng_term in lower_text:
            matched_terms.append(eng_term)
        elif translations.get("mr") and translations["mr"] in normalized_text:
            matched_terms.append(eng_term)
        elif translations.get("hi") and translations["hi"] in normalized_text:
            matched_terms.append(eng_term)

    return {
        "original_text": text,
        "normalized_text": normalized_text,
        "digit_ascii_text": digit_ascii_text,
        "matched_glossary_terms": list(set(matched_terms))
    }
