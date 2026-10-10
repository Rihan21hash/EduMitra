import json
import os
import re
from typing import Dict, Any

MARKERS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "markers.json")

def load_markers():
    try:
        with open(MARKERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "devanagari": {
                "mr": ["आहे", "काय", "कसे", "म्हणजे", "आणि", "मला", "चा", "ची", "चे", "च्या", "नाही", "सांगा"],
                "hi": ["है", "क्या", "कैसे", "मतलब", "और", "मुझे", "का", "की", "के", "नहीं", "बताइए"]
            },
            "romanized": {
                "mr": ["ahe", "kay", "kase", "mhanje", "ani", "mala", "sanga", "nahi", "cha", "chi", "che"],
                "hi": ["hai", "kya", "kaise", "matlab", "aur", "mujhe", "bataiye", "nahi"]
            }
        }

MARKERS = load_markers()

def detect_language(text: str, override: str = "auto") -> Dict[str, Any]:
    """
    Detect language (mr, hi, en) and script (devanagari, latin, mixed).
    Returns:
        { "language": "mr"|"hi"|"en", "script": "devanagari"|"latin"|"mixed", "confidence": float, "is_mixed": bool }
    """
    clean_text = text.strip()
    if override in ["mr", "hi", "en"]:
        return {
            "language": override,
            "script": "manual_override",
            "confidence": 1.0,
            "is_mixed": False,
            "override": True
        }

    devanagari_chars = len(re.findall(r'[\u0900-\u097F]', clean_text))
    latin_chars = len(re.findall(r'[a-zA-Z]', clean_text))
    total_letters = devanagari_chars + latin_chars

    if total_letters == 0:
        return {
            "language": "en",
            "script": "latin",
            "confidence": 0.5,
            "is_mixed": False
        }

    deva_ratio = devanagari_chars / total_letters
    latin_ratio = latin_chars / total_letters
    is_mixed = deva_ratio > 0.15 and latin_ratio > 0.15

    if is_mixed:
        script = "mixed"
    elif deva_ratio > 0.5:
        script = "devanagari"
    else:
        script = "latin"

    # If Devanagari is present, discriminate Marathi vs Hindi
    words = re.findall(r'[\u0900-\u097F]+|[a-zA-Z]+', clean_text.lower())
    
    if deva_ratio > 0.2:
        mr_set = set(MARKERS["devanagari"]["mr"])
        hi_set = set(MARKERS["devanagari"]["hi"])

        def deva_matches_marker(word: str, marker_set: set) -> bool:
            """Exact match OR the word starts with a marker (handles inflections like आहे→आहेत)."""
            if word in marker_set:
                return True
            return any(word.startswith(m) and len(m) >= 2 for m in marker_set)

        mr_matches = sum(1 for w in words if deva_matches_marker(w, mr_set))
        hi_matches = sum(1 for w in words if deva_matches_marker(w, hi_set))

        # Check for Marathi suffixes/postpositions like -चे, -च्या, -ला, -चे, -काचे, etc.
        for w in words:
            if re.search(r'[\u0900-\u097F]+(च्या|चे|चा|ची|काचे|काचा|काची|त|ने|ला|आहेत|आहे)$', w):
                mr_matches += 1

        if mr_matches > hi_matches:
            confidence = min(0.95, 0.65 + (mr_matches * 0.1))
            return {
                "language": "mr",
                "script": script,
                "confidence": round(confidence, 2),
                "is_mixed": is_mixed
            }
        elif hi_matches > mr_matches:
            confidence = min(0.95, 0.65 + (hi_matches * 0.1))
            return {
                "language": "hi",
                "script": script,
                "confidence": round(confidence, 2),
                "is_mixed": is_mixed
            }
        else:
            # Default to Marathi if tie in Devanagari regional context
            return {
                "language": "mr",
                "script": script,
                "confidence": 0.6,
                "is_mixed": is_mixed
            }

    # If Roman script, check romanized markers
    mr_markers = set(MARKERS["romanized"]["mr"])
    hi_markers = set(MARKERS["romanized"]["hi"])

    def matches_marker(word: str, marker_set: set) -> bool:
        """Exact match OR any marker is a prefix of the word (handles inflections like ahe->ahet)."""
        if word in marker_set:
            return True
        return any(word.startswith(m) and len(m) >= 3 for m in marker_set)

    lower_words = [w.lower() for w in words]
    mr_rom_matches = sum(1 for w in lower_words if matches_marker(w, mr_markers))
    hi_rom_matches = sum(1 for w in lower_words if matches_marker(w, hi_markers))

    if mr_rom_matches > hi_rom_matches and mr_rom_matches > 0:
        confidence = min(0.92, 0.70 + (mr_rom_matches * 0.05))
        return {
            "language": "mr",
            "script": "latin",
            "confidence": round(confidence, 2),
            "is_mixed": True
        }
    elif hi_rom_matches > mr_rom_matches and hi_rom_matches > 0:
        confidence = min(0.92, 0.70 + (hi_rom_matches * 0.05))
        return {
            "language": "hi",
            "script": "latin",
            "confidence": round(confidence, 2),
            "is_mixed": True
        }

    # Otherwise Latin -> English
    return {
        "language": "en",
        "script": "latin",
        "confidence": 0.9,
        "is_mixed": False
    }
