import logging
import re
from typing import Dict, Any, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class AnalysisResult(BaseModel):
    language: str = "mr"
    intent: str = "concept_explanation"
    subject: str = "General Science"
    topic: str = "General"
    core_question: str = ""
    key_terms: List[str] = Field(default_factory=list)
    formulas: List[str] = Field(default_factory=list)
    expected_answer_type: str = "explanation"

def rule_based_pre_pass(text: str, detected_lang: str) -> Dict[str, Any]:
    """Rule-based heuristic checks for intent and subject hints."""
    lower = text.lower()

    # Intent heuristics
    intent = "concept_explanation"
    if any(k in lower for k in ["उदाहरण", "उदा.", "example", "उदा"]):
        intent = "example_request"
    elif any(k in lower for k in ["गुण", "मार्क्स", "marks", "अंक", "पॉइंट्स"]):
        intent = "exam_answer"

    # Subject heuristics
    subject = "Other"
    topic = "General Concept"

    physics_kw = ["न्यूटन", "newton", "बल", "force", "गती", "गति", "motion", "जडत्व", "जड़त्व", "inertia", "गुरुत्वाकर्षण", "gravity", "ऊर्जा", "energy", "कार्य", "work", "velocity", "वेग", "acceleration", "त्वरण", "pressure", "दाब"]
    chem_kw = ["अणू", "अणु", "रेणू", "परमाणु", "atom", "molecule", "acid", "आम्ल", "base", "alkali", "reaction", "अभिक्रिया", "oxidation", "reduction"]
    bio_kw = ["photosynthesis", "प्रकाशसंश्लेषण", "प्रकाश संश्लेषण", "cell", "पेशी", "कोशिका", "dna", "heart", "हृदय", "respiration", "श्वसन", "osmosis", "mitosis"]
    math_kw = ["त्रिकोणमिती", "trigonometry", "derivative", "integration", "समीकरण", "equation", "क्षेत्रफळ", "area", "matrix", "determinant", "probability", "संभाव्यता"]
    ee_kw = ["ohm", "ओम", "current", "विद्युतधारा", "voltage", "व्होल्टेज", "resistance", "रोध", "प्रतिरोध", "transformer", "capacitor", "inductor", "diode", "transistor", "circuit", "परिपथ"]
    cs_kw = ["algorithm", "sorting", "binary", "python", "java", "recursion", "संगणक", "प्रोग्राम", "data structure", "linked list", "stack", "queue", "tree", "graph"]

    if any(k in lower for k in physics_kw):
        subject = "Physics"
        if "newton" in lower or "न्यूटन" in lower:
            topic = "Newton's Laws of Motion"
        elif "gravity" in lower or "गुरुत्वाकर्षण" in lower:
            topic = "Gravitation"
        elif "energy" in lower or "ऊर्जा" in lower:
            topic = "Energy"
        elif "motion" in lower or "गती" in lower or "गति" in lower:
            topic = "Motion"
    elif any(k in lower for k in ee_kw):
        subject = "Electrical Engineering"
        if "ohm" in lower or "ओम" in lower:
            topic = "Ohm's Law"
        elif "transformer" in lower:
            topic = "Transformers"
        elif "capacitor" in lower:
            topic = "Capacitors"
    elif any(k in lower for k in bio_kw):
        subject = "Biology"
        if "photosynthesis" in lower or "प्रकाशसंश्लेषण" in lower or "प्रकाश संश्लेषण" in lower:
            topic = "Photosynthesis"
        elif "cell" in lower or "पेशी" in lower or "कोशिका" in lower:
            topic = "Cell Biology"
    elif any(k in lower for k in chem_kw):
        subject = "Chemistry"
        if "atom" in lower or "अणू" in lower or "अणु" in lower:
            topic = "Atomic Structure"
    elif any(k in lower for k in math_kw):
        subject = "Mathematics"
        if "trigonometry" in lower or "त्रिकोणमिती" in lower:
            topic = "Trigonometry"
        elif "derivative" in lower:
            topic = "Differentiation"
    elif any(k in lower for k in cs_kw):
        subject = "Computer Science"
        if "algorithm" in lower or "sorting" in lower:
            topic = "Algorithms"

    # Extract likely key terms (capitalized English words or Devanagari technical words)
    key_terms = []
    cap_words = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', text)
    for w in cap_words:
        if w.lower() not in {"what", "why", "how", "who", "when", "where", "which", "explain", "define", "describe"}:
            key_terms.append(w)

    return {
        "intent": intent,
        "subject": subject,
        "topic": topic,
        "key_terms": key_terms[:5]
    }


async def analyze_question(
    normalized_text: str,
    detected_lang: str,
    matched_glossary_terms: List[str]
) -> AnalysisResult:
    """
    Fast rule-based analysis — NO LLM call needed.
    Rule-based pass handles subject, topic, intent reliably.
    """
    pre = rule_based_pre_pass(normalized_text, detected_lang)

    # Merge rule-based key_terms with glossary matches
    key_terms = list(pre["key_terms"])
    for term in matched_glossary_terms:
        if term not in key_terms:
            key_terms.append(term)

    return AnalysisResult(
        language=detected_lang,
        intent=pre["intent"],
        subject=pre["subject"],
        topic=pre["topic"],
        core_question=normalized_text,
        key_terms=key_terms[:8],
        formulas=[],
        expected_answer_type="explanation"
    )
