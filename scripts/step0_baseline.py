import asyncio
import json
import os
import re
import sys
import httpx

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.config import settings
from app.pipeline.language_detect import detect_language
from app.pipeline.normalize import normalize_text
from app.pipeline.analysis import analyze_question
from app.pipeline.level_adapter import get_level_rules
from app.pipeline.prompt_builder import build_chat_messages
from app.pipeline.validator import validate_response

QUESTIONS = [
    {"id": "mr_01", "text": "न्यूटनचा पहिला नियम काय आहे?", "level": "beginner"},
    {"id": "mr_02", "text": "गुरुत्वाकर्षण म्हणजे काय आणि त्याचे सूत्र काय आहे?", "level": "beginner"},
    {"id": "mr_03", "text": "प्रकाशसंश्लेषण प्रक्रियेचे महत्त्व काय आहे?", "level": "beginner"},
    {"id": "mr_04", "text": "ओहमचा नियम स्पष्ट करा आणि V = IR चे महत्त्व सांगा.", "level": "beginner"},
    {"id": "mr_05", "text": "अणू आणि रेणू यातील फरक काय आहे?", "level": "beginner"},
]

def count_words(text: str) -> int:
    return len(re.findall(r'\S+', text))

async def run_baseline_question(item):
    raw_text = item["text"]
    level = item["level"]
    lang_info = detect_language(raw_text)
    target_lang = lang_info["language"]
    norm_result = normalize_text(raw_text)
    norm_text = norm_result["normalized_text"]
    glossary_terms = norm_result["matched_glossary_terms"]

    analysis = await analyze_question(norm_text, target_lang, glossary_terms)
    level_rules = get_level_rules(level)
    token_limit = level_rules.get("num_predict", 350)

    chat_messages = build_chat_messages(
        analysis=analysis,
        target_language=target_lang,
        level=level,
        original_text=raw_text
    )

    options = {
        "temperature": 0.3,
        "num_thread": max(1, (os.cpu_count() or 4) - 1),
        "num_ctx": settings.ollama_num_ctx,
        "num_predict": token_limit
    }

    payload = {
        "model": settings.ollama_model,
        "messages": chat_messages,
        "stream": False,
        "keep_alive": settings.ollama_keep_alive,
        "options": options
    }

    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(url, json=payload)
        data = resp.json()

    content = data.get("message", {}).get("content", "")
    words = count_words(content)
    done_reason = data.get("done_reason")
    eval_count = data.get("eval_count")
    prompt_eval_count = data.get("prompt_eval_count")
    prompt_truncated = prompt_eval_count >= settings.ollama_num_ctx if prompt_eval_count else False
    length_truncated = (done_reason == "length")

    val = validate_response(content, target_lang, level, analysis)

    return {
        "id": item["id"],
        "question": raw_text,
        "model": settings.ollama_model,
        "word_count": words,
        "done_reason": done_reason,
        "eval_count": eval_count,
        "prompt_eval_count": prompt_eval_count,
        "num_predict": token_limit,
        "num_ctx": settings.ollama_num_ctx,
        "options_sent": options,
        "length_truncated": length_truncated,
        "prompt_truncated": prompt_truncated,
        "validation_passed": val["passed"],
        "validation_notes": val["notes"],
        "content_snippet": content[:180] + ("..." if len(content) > 180 else ""),
        "full_content": content
    }

async def main():
    print(f"Running Baseline Measurements on model '{settings.ollama_model}'...")
    results = []
    for q in QUESTIONS:
        print(f"Testing {q['id']}: {q['text']}...")
        res = await run_baseline_question(q)
        results.append(res)
        print(f" -> Words: {res['word_count']}, eval_count: {res['eval_count']}, done_reason: {res['done_reason']}, length_truncated: {res['length_truncated']}")

    with open("baseline_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Baseline measurement complete. Results saved to baseline_results.json.")

if __name__ == "__main__":
    asyncio.run(main())
