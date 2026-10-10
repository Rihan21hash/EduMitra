from typing import Dict, Any, Optional

# Per-language word count bands (since Marathi/Hindi words are longer and fewer)
WORD_COUNT_BANDS = {
    "en": {
        "beginner": (70, 160),
        "intermediate": (140, 260),
        "advanced": (240, 420),
        "exam_2": (35, 70),
        "exam_5": (130, 210),
        "exam_7": (230, 360),
        "exam_10": (380, 580),
    },
    "mr": {
        "beginner": (45, 120),
        "intermediate": (90, 190),
        "advanced": (160, 320),
        "exam_2": (25, 55),
        "exam_5": (90, 160),
        "exam_7": (160, 260),
        "exam_10": (250, 420),
    },
    "hi": {
        "beginner": (55, 130),
        "intermediate": (100, 210),
        "advanced": (180, 350),
        "exam_2": (30, 60),
        "exam_5": (100, 180),
        "exam_7": (180, 290),
        "exam_10": (280, 460),
    }
}

# Per-language token budget caps (Devanagari is token-heavy: ~6 tokens/word vs English ~1.3 tokens/word)
NUM_PREDICT_CAPS = {
    "en": {
        "beginner": 380,
        "intermediate": 550,
        "advanced": 800,
        "exam_2": 220,
        "exam_5": 500,
        "exam_7": 750,
        "exam_10": 1100,
    },
    "mr": {
        "beginner": 850,
        "intermediate": 1300,
        "advanced": 1900,
        "exam_2": 450,
        "exam_5": 1150,
        "exam_7": 1700,
        "exam_10": 2500,
    },
    "hi": {
        "beginner": 850,
        "intermediate": 1300,
        "advanced": 1900,
        "exam_2": 450,
        "exam_5": 1150,
        "exam_7": 1700,
        "exam_10": 2500,
    }
}

LEVEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    "beginner": {
        "name": "Beginner",
        "audience": "First exposure / school student",
        "vocabulary": "Everyday words, short sentences, every term explained simply before use.",
        "structure": (
            "Structural requirements:\n"
            "1. Clear, simple definition.\n"
            "2. At least 3 key explanation points presented as bullet points.\n"
            "3. Exactly one relatable everyday real-world example.\n"
            "4. A one-line takeaway summary."
        )
    },
    "intermediate": {
        "name": "Intermediate",
        "audience": "Student with basic familiarity / first-year college",
        "vocabulary": "Standard textbook terminology with clear contextual definitions.",
        "structure": (
            "Structural requirements:\n"
            "1. Clear formal textbook definition.\n"
            "2. Step-by-step conceptual explanation with 3-4 structured points.\n"
            "3. Practical example (and explanation of all formula symbols if present).\n"
            "4. Summary takeaway."
        )
    },
    "advanced": {
        "name": "Advanced",
        "audience": "Advanced student / engineering / strong conceptual foundation",
        "vocabulary": "Rigorous technical language, physical principles, mathematical relations.",
        "structure": (
            "Structural requirements:\n"
            "1. Formal rigorous definition.\n"
            "2. Physical or mathematical principles/derivation.\n"
            "3. Formulas and mathematical relationships clearly defined.\n"
            "4. Edge cases, limitations, and real-world engineering applications.\n"
            "5. Technical conclusion."
        )
    },
    "exam": {
        "name": "Exam Mode",
        "audience": "Exam aspirant writing standard board / university exams",
        "vocabulary": "Standard textbook academic phrasing, formal headings and bullet points.",
        "structure": "Structured precisely for academic scoring with headings and bullet points."
    }
}

EXAM_MARKS_CONFIGS: Dict[int, Dict[str, Any]] = {
    2: {
        "structure": (
            "2-mark structural requirements:\n"
            "1. Crisp 1-2 sentence definition.\n"
            "2. State the formula or governing law if applicable.\n"
            "3. Exactly 2 crisp bullet points."
        )
    },
    5: {
        "structure": (
            "5-mark structural requirements:\n"
            "1. Heading: Definition.\n"
            "2. Heading: Key Points (provide 4-5 numbered points).\n"
            "3. Heading: Example or Formula with units."
        )
    },
    7: {
        "structure": (
            "7-mark structural requirements:\n"
            "1. Introduction & Principle.\n"
            "2. Detailed explanation under clear sub-headings.\n"
            "3. Working mechanism or derivation steps.\n"
            "4. Real-world example.\n"
            "5. Conclusion."
        )
    },
    10: {
        "structure": (
            "10-mark structural requirements:\n"
            "1. Introduction & Core Principle.\n"
            "2. Detailed in-depth explanation with sub-headings.\n"
            "3. Derivation or diagrammatic working description.\n"
            "4. Real-world engineering applications.\n"
            "5. Advantages and limitations.\n"
            "6. Summary conclusion."
        )
    }
}

def get_level_rules(
    level: str,
    exam_marks: Optional[int] = None,
    target_language: str = "mr"
) -> Dict[str, Any]:
    """
    Retrieve length bands, token limit, and structural prompt guidance.
    Uses structural requirements instead of rigid word targets.
    """
    normalized_level = level.lower() if level else "beginner"
    lang_key = target_language if target_language in WORD_COUNT_BANDS else "en"
    bands = WORD_COUNT_BANDS[lang_key]
    caps = NUM_PREDICT_CAPS[lang_key]

    if normalized_level == "exam":
        marks = exam_marks if exam_marks in EXAM_MARKS_CONFIGS else 5
        marks_info = EXAM_MARKS_CONFIGS[marks]
        min_w, max_w = bands.get(f"exam_{marks}", (100, 200))
        num_predict = caps.get(f"exam_{marks}", 1100)

        return {
            "level": "exam",
            "marks": marks,
            "min_words": min_w,
            "max_words": max_w,
            "num_predict": num_predict,
            "instruction": f"Format this answer for a {marks}-mark academic exam question. {marks_info['structure']}"
        }

    cfg = LEVEL_CONFIGS.get(normalized_level, LEVEL_CONFIGS["beginner"])
    min_w, max_w = bands.get(normalized_level, (50, 130))
    num_predict = caps.get(normalized_level, 850)

    return {
        "level": normalized_level,
        "marks": None,
        "min_words": min_w,
        "max_words": max_w,
        "num_predict": num_predict,
        "instruction": f"Target audience: {cfg['audience']}. Vocabulary: {cfg['vocabulary']}\n{cfg['structure']}"
    }
