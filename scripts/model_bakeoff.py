import asyncio
import json
import os
import re
import sys
import time
import httpx

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
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
    {'id': 'mr_01', 'text': 'न्यूटनचा पहिला नियम काय आहे?', 'level': 'beginner'},
    {'id': 'mr_02', 'text': 'गुरुत्वाकर्षण म्हणजे काय आणि त्याचे सूत्र काय आहे?', 'level': 'beginner'},
    {'id': 'mr_03', 'text': 'प्रकाशसंश्लेषण प्रक्रियेचे महत्त्व काय आहे?', 'level': 'beginner'},
    {'id': 'mr_04', 'text': 'ओहमचा नियम स्पष्ट करा.', 'level': 'intermediate'},
    {'id': 'mr_05', 'text': 'अणू आणि रेणू यातील फरक काय आहे?', 'level': 'beginner'},
]

CANDIDATES = [
    {'name': 'coder-direct', 'model': 'qwen2.5-coder:7b', 'mode': 'direct'},
    {'name': 'qwen3-direct',  'model': 'qwen3:8b',          'mode': 'direct'},
    {'name': 'qwen3-pivot',   'model': 'qwen3:8b',          'mode': 'pivot'},
]

def count_words(text):
    return len(re.findall(r'\S+', text))

async def run_direct(client, model, chat_messages, token_limit):
    payload = {
        'model': model,
        'messages': chat_messages,
        'stream': False,
        'keep_alive': settings.ollama_keep_alive,
        'options': {
            'temperature': 0.3,
            'repeat_penalty': 1.08,
            'num_thread': max(1, (os.cpu_count() or 4) - 1),
            'num_ctx': settings.ollama_num_ctx,
            'num_predict': token_limit,
        }
    }
    if 'qwen3' in model.lower():
        payload['think'] = False
        payload['options']['think'] = False

    url = f'{settings.ollama_base_url.rstrip("/")}/api/chat'
    t0 = time.perf_counter()
    resp = await client.post(url, json=payload, timeout=180)
    elapsed = time.perf_counter() - t0
    data = resp.json()
    content = data.get('message', {}).get('content', '').strip()
    return content, elapsed, data.get('done_reason'), data.get('eval_count')

async def run_pivot(client, model, en_messages, token_limit, target_lang):
    from app.pipeline.translator import translate_response
    content, elapsed, done_reason, eval_count = await run_direct(client, model, en_messages, token_limit)
    t0t = time.perf_counter()
    trans = await translate_response(content, target_lang)
    trans_elapsed = time.perf_counter() - t0t
    return trans['translated_text'], elapsed, trans_elapsed, done_reason, eval_count, content

async def test_candidate(candidate, question):
    raw_text = question['text']
    level = question['level']

    lang_info = detect_language(raw_text)
    target_lang = lang_info['language']
    norm = normalize_text(raw_text)
    analysis = await analyze_question(norm['normalized_text'], target_lang, norm['matched_glossary_terms'])
    level_rules = get_level_rules(level, target_language=target_lang)
    token_limit = level_rules.get('num_predict', 850)

    model = candidate['model']
    mode = candidate['mode']

    async with httpx.AsyncClient(timeout=240) as client:
        if mode == 'pivot':
            en_msgs = build_chat_messages(analysis=analysis, target_language='en', level=level, original_text=raw_text)
            translated, gen_s, trans_s, done_reason, eval_count, en_text = await run_pivot(client, model, en_msgs, token_limit, target_lang)
            answer = translated
            gen_ms = int(gen_s * 1000)
            trans_ms = int(trans_s * 1000)
        else:
            msgs = build_chat_messages(analysis=analysis, target_language=target_lang, level=level, original_text=raw_text)
            answer, gen_s, done_reason, eval_count = await run_direct(client, model, msgs, token_limit)
            gen_ms = int(gen_s * 1000)
            trans_ms = 0
            en_text = ''

    val = validate_response(answer, target_lang, level, analysis)
    wc = count_words(answer)

    result = {
        'candidate': candidate['name'],
        'model': model,
        'mode': mode,
        'question_id': question['id'],
        'level': level,
        'word_count': wc,
        'gen_ms': gen_ms,
        'trans_ms': trans_ms,
        'total_ms': gen_ms + trans_ms,
        'done_reason': done_reason,
        'eval_count': eval_count,
        'token_limit': token_limit,
        'length_truncated': done_reason == 'length',
        'validation_passed': val['passed'],
        'validation_notes': val['notes'],
        'answer_snippet': answer[:200] + ('...' if len(answer) > 200 else ''),
        'full_answer': answer,
        'english_pivot': en_text[:200] + ('...' if en_text and len(en_text) > 200 else '') if en_text else '',
    }
    return result

async def main():
    all_results = []
    for c in CANDIDATES:
        print(f'\n=== Candidate: {c["name"]} ({c["model"]}, mode={c["mode"]}) ===')
        for q in QUESTIONS:
            print(f'  Q {q["id"]}: {q["text"][:50]}...')
            try:
                res = await test_candidate(c, q)
                all_results.append(res)
                wc = res['word_count']
                gm = res['gen_ms']
                tm = res['trans_ms']
                vp = 'PASS' if res['validation_passed'] else 'FAIL'
                trunc = ' TRUNCATED' if res['length_truncated'] else ''
                print(f'     words={wc} gen={gm}ms trans={tm}ms val={vp}{trunc}')
                print(f'     snippet: {res["answer_snippet"][:120]}')
            except Exception as e:
                print(f'     ERROR: {e}')
                all_results.append({'candidate': c['name'], 'question_id': q['id'], 'error': str(e)})

    out = 'bakeoff_results.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f'\nBake-off complete. Results saved to {out}')

    # Print summary table
    print('\n--- SUMMARY ---')
    print(f'{"Candidate":<20} {"Q":<8} {"Words":<8} {"gen_ms":<10} {"Val":<6} {"Trunc":<8}')
    print('-' * 70)
    for r in all_results:
        if 'error' not in r:
            print(f'{r["candidate"]:<20} {r["question_id"]:<8} {r["word_count"]:<8} {r["gen_ms"]:<10} {"Y" if r["validation_passed"] else "N":<6} {"Y" if r["length_truncated"] else "N":<8}')

if __name__ == '__main__':
    asyncio.run(main())
