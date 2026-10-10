import pytest
from app.routers.quiz import clean_and_parse_quiz_json, build_fallback_questions

def test_quiz_json_parsing():
    # 1. Standard markdown codeblock JSON
    raw_markdown = """```json
    {
      "questions": [
        {
          "id": "q0",
          "prompt": "न्यूटनचा पहिला नियम काय सांगतो?",
          "options": ["जडत्व", "संवेग", "त्वरण", "कार्य"],
          "correct_index": 0,
          "explanation": "पहिला नियम जडत्वावर आधारलेला आहे."
        }
      ]
    }
    ```"""
    parsed = clean_and_parse_quiz_json(raw_markdown)
    assert parsed is not None
    assert len(parsed) == 1
    assert parsed[0]["correct_index"] == 0

    # 2. Raw list JSON
    raw_list = """[
        {
          "id": "q0",
          "prompt": "What is inertia?",
          "options": ["Resistance to motion change", "Acceleration", "Energy", "Work"],
          "correct_index": 0,
          "explanation": "Inertia resists change in motion."
        }
    ]"""
    parsed_list = clean_and_parse_quiz_json(raw_list)
    assert parsed_list is not None
    assert len(parsed_list) == 1

    # 3. Fallback questions structure
    mr_fallback = build_fallback_questions("Inertia", "mr")
    assert len(mr_fallback) >= 2
    assert len(mr_fallback[0]["options"]) == 4
    assert 0 <= mr_fallback[0]["correct_index"] <= 3

    hi_fallback = build_fallback_questions("Inertia", "hi")
    assert len(hi_fallback) >= 2
    assert len(hi_fallback[0]["options"]) == 4
