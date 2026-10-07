from typing import Dict, Any, Optional

LEVEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    "beginner": {
        "name": "Beginner",
        "min_words": 70,
        "max_words": 160,
        "audience": "First exposure / school student",
        "vocabulary": "Everyday words, short sentences, every term explained simply before use.",
        "structure": "One idea per paragraph. Include exactly one relatable real-world example. Conclude with a one-line takeaway summary."
    },
    "intermediate": {
        "name": "Intermediate",
        "min_words": 140,
        "max_words": 260,
        "audience": "Student with basic familiarity / first-year college",
        "vocabulary": "Standard textbook terminology with clear contextual definitions.",
        "structure": "Clear formal definition -> step-by-step conceptual explanation -> real-world example. If formulas are present, clearly explain every symbol."
    },
    "advanced": {
        "name": "Advanced",
        "min_words": 240,
        "max_words": 420,
        "audience": "Advanced student / engineering / strong conceptual foundation",
        "vocabulary": "Rigorous technical language, physical principles, mathematical relations.",
        "structure": "Formal definition -> physical/mathematical reasoning or derivation -> edge cases / limitations -> real-world applications."
    },
    "exam": {
        "name": "Exam Mode",
        "min_words": 50,
        "max_words": 550,
        "audience": "Exam aspirant writing standard board / university exams",
        "vocabulary": "Standard textbook academic phrasing, formal headings and bullet points.",
        "structure": "Structured precisely for academic scoring with headings and bullet points."
    }
}

EXAM_MARKS_CONFIGS: Dict[int, Dict[str, Any]] = {
    2: {
        "min_words": 35,
        "max_words": 70,
        "structure": "Crisp 1-2 sentence definition. State the formula/law if applicable. 2 crisp points.",
    },
    5: {
        "min_words": 130,
        "max_words": 210,
        "structure": "Heading: Definition. Heading: Key Points (provide 4-5 numbered points). Heading: Example or Formula.",
    },
    7: {
        "min_words": 230,
        "max_words": 360,
        "structure": "Introduction -> Detailed explanation under clear sub-headings -> Steps / Derivation / Working principle -> Example -> Conclusion.",
    },
    10: {
        "min_words": 380,
        "max_words": 580,
        "structure": "Introduction & Principle -> Sub-headings: Working / In-depth Explanation -> Derivation or Diagrammatic description -> Real-world Applications -> Advantages & Limitations -> Conclusion.",
    }
}

def get_level_rules(level: str, exam_marks: Optional[int] = None) -> Dict[str, Any]:
    """Retrieve length and structure guidance for the specified level."""
    normalized_level = level.lower() if level else "beginner"
    if normalized_level == "exam":
        marks = exam_marks if exam_marks in EXAM_MARKS_CONFIGS else 5
        marks_info = EXAM_MARKS_CONFIGS[marks]
        return {
            "level": "exam",
            "marks": marks,
            "min_words": marks_info["min_words"],
            "max_words": marks_info["max_words"],
            "instruction": f"Format this answer for a {marks}-mark academic exam question. Structure: {marks_info['structure']}"
        }
    
    cfg = LEVEL_CONFIGS.get(normalized_level, LEVEL_CONFIGS["beginner"])
    return {
        "level": normalized_level,
        "marks": None,
        "min_words": cfg["min_words"],
        "max_words": cfg["max_words"],
        "instruction": f"Target audience: {cfg['audience']}. Vocabulary: {cfg['vocabulary']} Structure: {cfg['structure']} Target word count: {cfg['min_words']}-{cfg['max_words']} words."
    }
