import pytest
from app.pipeline.normalize import normalize_text, normalize_devanagari_digits

def test_digit_normalization():
    assert normalize_devanagari_digits("१० + २५ = ३५") == "10 + 25 = 35"

def test_whitespace_and_danda():
    raw = "  न्यूटनचा नियम आहे  ।   F = ma  "
    res = normalize_text(raw)
    assert "." in res["normalized_text"]
    assert "F = ma" in res["normalized_text"]
    assert not res["normalized_text"].startswith(" ")

def test_glossary_matching():
    raw = "जडत्व आणि बल यावर आधारित नियम सांगा."
    res = normalize_text(raw)
    assert "inertia" in res["matched_glossary_terms"]
    assert "force" in res["matched_glossary_terms"]
