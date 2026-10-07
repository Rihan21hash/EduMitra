import pytest
from app.pipeline.validator import validate_response
from app.pipeline.analysis import AnalysisResult

def test_validator_marathi_pass():
    analysis = AnalysisResult(
        language="mr",
        intent="concept_explanation",
        subject="Physics",
        topic="Newton's Laws",
        core_question="Newton's first law",
        key_terms=["inertia", "force"],
        formulas=["F = ma"]
    )
    # 80+ words answer in Marathi with key terms and formula
    sample_answer = """
न्यूटनचा पहिला गतीविषयक नियम:
कोणत्याही वस्तूवर बाह्य असंतुलित बल (Force) कार्य करत नसेल, तर ती वस्तू तिच्या विराम अवस्थेत किंवा सरळ रेषेतील एकसमान गतीत कायम राहते.
या गुणधर्माला जडत्व (Inertia) असे म्हणतात. 
उदाहरणार्थ, बस अचानक थांबल्यास प्रवासी पुढे झुकतात.
न्यूटनचा दुसरा नियम सांगतो की $F = ma$. 
हा नियम आपल्या दैनंदिन जीवनातील अनेक घटना स्पष्ट करतो.
    """
    res = validate_response(
        answer_text=sample_answer,
        target_language="mr",
        level="beginner",
        analysis=analysis
    )
    assert res["passed"] is True

def test_validator_script_mismatch():
    analysis = AnalysisResult(
        language="mr",
        intent="concept_explanation",
        subject="Physics",
        topic="Newton's Laws",
        core_question="Newton's first law",
        key_terms=[]
    )
    english_answer = "This is a purely English answer when the target language requested was Marathi."
    res = validate_response(
        answer_text=english_answer,
        target_language="mr",
        level="beginner",
        analysis=analysis
    )
    assert res["passed"] is False

def test_validator_repeat_detection():
    analysis = AnalysisResult(
        language="mr",
        intent="concept_explanation",
        subject="Physics",
        topic="Newton's Laws",
        core_question="Newton's first law",
        key_terms=[]
    )
    prev = "न्यूटनचा पहिला नियम जडत्वाचा नियम म्हणून ओळखला जातो."
    followup = "न्यूटनचा पहिला नियम जडत्वाचा नियम म्हणून ओळखला जातो."
    res = validate_response(
        answer_text=followup,
        target_language="mr",
        level="beginner",
        analysis=analysis,
        previous_answer=prev,
        is_followup=True
    )
    assert res["passed"] is False
