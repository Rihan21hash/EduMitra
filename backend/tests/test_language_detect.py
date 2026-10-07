import pytest
from app.pipeline.language_detect import detect_language

def test_marathi_detection():
    res = detect_language("न्यूटनचा पहिला नियम काय आहे?")
    assert res["language"] == "mr"
    assert res["script"] == "devanagari"

def test_hindi_detection():
    res = detect_language("न्यूटन का पहला नियम क्या है?")
    assert res["language"] == "hi"
    assert res["script"] == "devanagari"

def test_english_detection():
    res = detect_language("What is Newton's first law of motion?")
    assert res["language"] == "en"
    assert res["script"] == "latin"

def test_mixed_language_marathi():
    res = detect_language("Photosynthesis म्हणजे काय?")
    assert res["language"] == "mr"
    assert res["is_mixed"] is True

def test_romanized_marathi():
    res = detect_language("newton cha pahila niyam kay ahe")
    assert res["language"] == "mr"

def test_romanized_hindi():
    res = detect_language("newton ka pehla niyam kya hai")
    assert res["language"] == "hi"

def test_manual_override():
    res = detect_language("What is photosynthesis?", override="mr")
    assert res["language"] == "mr"
    assert res["confidence"] == 1.0
