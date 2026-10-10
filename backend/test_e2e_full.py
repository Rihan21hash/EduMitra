import httpx
import json
import sys
import time

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def test_full_flow():
    print("==================================================")
    print("       EDUMITRA FULL E2E VALIDATION TEST")
    print("==================================================")

    with httpx.Client(timeout=httpx.Timeout(180.0, connect=10.0, read=180.0)) as client:
        # 1. Health check
        print("\n[1] Checking /health...")
        r = client.get(f"{BASE_URL}/health")
        assert r.status_code == 200, f"Health check failed: {r.text}"
        data = r.json()
        print(f"  -> Health status: {data.get('status')}")
        print(f"  -> Ollama reachable: {data.get('ollama')}")
        print(f"  -> Model loaded in memory: {data.get('model_loaded')}")
        print("  -> PASSED.")

        # 2. Ask question with streaming (Marathi)
        print("\n[2] Testing POST /api/question/stream (Marathi, beginner)...")
        t0 = time.perf_counter()
        events = []
        tokens = []
        meta_data = {}
        done_data = {}

        with client.stream('POST', f"{BASE_URL}/api/question/stream", json={
            'user_id': 'e2e-tester-1',
            'text': 'गुरुत्वाकर्षण म्हणजे काय? सोप्या भाषेत सांगा.',
            'level': 'beginner',
            'language_override': 'mr'
        }) as resp:
            assert resp.status_code == 200, f"Streaming failed: {resp.status_code}"
            curr_event = None
            for line in resp.iter_lines():
                if line.startswith('event:'):
                    curr_event = line.split(':', 1)[1].strip()
                    events.append(curr_event)
                elif line.startswith('data:'):
                    payload = line.split(':', 1)[1].strip()
                    if curr_event == 'meta':
                        meta_data = json.loads(payload)
                    elif curr_event == 'token':
                        tok_obj = json.loads(payload)
                        tokens.append(tok_obj.get('token', ''))
                    elif curr_event == 'done':
                        done_data = json.loads(payload)

        elapsed = time.perf_counter() - t0
        full_text = "".join(tokens)
        conv_id = meta_data.get('conversation_id') or done_data.get('conversation_id')
        resp_id = done_data.get('response_id')
        print(f"  -> Stream completed in {elapsed:.2f}s", flush=True)
        print(f"  -> Total tokens: {len(tokens)}", flush=True)
        print(f"  -> Conversation ID: {conv_id}", flush=True)
        print(f"  -> Response ID: {resp_id}", flush=True)
        print(f"  -> First 80 chars: {full_text[:80]!r}", flush=True)
        assert len(tokens) > 10, "Should have received tokens"
        assert conv_id is not None, "Should have conversation_id"
        assert resp_id is not None, "Should have response_id"
        print("  -> PASSED.", flush=True)

        # 3. Multi-turn follow-up with conversation_id
        print(f"\n[3] Testing multi-turn follow-up with conversation_id={conv_id}...")
        t0 = time.perf_counter()
        follow_tokens = []
        with client.stream('POST', f"{BASE_URL}/api/question/stream", json={
            'user_id': 'e2e-tester-1',
            'conversation_id': conv_id,
            'text': 'त्याचे एक उदाहरण द्या.',
            'level': 'beginner',
            'language_override': 'mr'
        }) as resp:
            assert resp.status_code == 200
            curr_event = None
            for line in resp.iter_lines():
                if line.startswith('event:'):
                    curr_event = line.split(':', 1)[1].strip()
                elif line.startswith('data:'):
                    if curr_event == 'token':
                        tok_obj = json.loads(line.split(':', 1)[1].strip())
                        follow_tokens.append(tok_obj.get('token', ''))
        follow_text = "".join(follow_tokens)
        print(f"  -> Follow-up response tokens: {len(follow_tokens)} in {time.perf_counter()-t0:.2f}s", flush=True)
        print(f"  -> Follow-up text preview: {follow_text[:80]!r}", flush=True)
        assert len(follow_tokens) > 5
        print("  -> PASSED.", flush=True)

        # 4. Language Switcher / Response Variant (English and Hindi variant of Marathi response)
        print(f"\n[4] Testing Language Switcher Variant: POST /api/response/{resp_id}/variant (to 'en')...", flush=True)
        t0 = time.perf_counter()
        var_resp = client.post(f"{BASE_URL}/api/response/{resp_id}/variant", json={
            'target_language': 'en'
        })
        assert var_resp.status_code == 200, f"Variant failed: {var_resp.text}"
        var_data = var_resp.json()
        print(f"  -> English Variant generated in {time.perf_counter()-t0:.2f}s", flush=True)
        print(f"  -> English text preview: {var_data.get('answer_text', '')[:80]!r}", flush=True)
        assert var_data.get('language') == 'en'
        assert len(var_data.get('answer_text', '')) > 20

        # Now test cached variant retrieval (should be instant)
        t0 = time.perf_counter()
        var_cached = client.post(f"{BASE_URL}/api/response/{resp_id}/variant", json={
            'target_language': 'en'
        })
        cached_elapsed = time.perf_counter() - t0
        print(f"  -> Cached variant fetched in {cached_elapsed*1000:.1f}ms (< 50ms expected)", flush=True)
        assert cached_elapsed < 0.5, "Cached variant should return instantly"

        # List all variants for this response
        list_resp = client.get(f"{BASE_URL}/api/response/{resp_id}/variants")
        assert list_resp.status_code == 200
        variants_list = list_resp.json().get('variants', [])
        print(f"  -> Total variants in DB for response {resp_id}: {len(variants_list)} ({[v['language'] for v in variants_list]})", flush=True)
        assert len(variants_list) >= 2  # mr and en
        print("  -> PASSED.", flush=True)

        # 5. Exam mode answer with marks
        print("\n[5] Testing POST /api/exam-answer (5 marks)...", flush=True)
        exam_resp = client.post(f"{BASE_URL}/api/exam-answer", json={
            'user_id': 'e2e-tester-1',
            'text': 'Explain Newton\'s third law of motion with examples.',
            'level': 'intermediate',
            'language_override': 'en',
            'marks': 5
        })
        assert exam_resp.status_code == 200, f"Exam answer failed: {exam_resp.text}"
        exam_data = exam_resp.json()
        exam_marks_val = exam_data.get('exam_marks') or exam_data.get('marks')
        exam_text_val = exam_data.get('answer', {}).get('text') if isinstance(exam_data.get('answer'), dict) else exam_data.get('answer_text', '')
        exam_resp_id = exam_data.get('response_id')
        print(f"  -> Exam mode response received:", flush=True)
        print(f"  -> Marks: {exam_marks_val} marks", flush=True)
        print(f"  -> Answer preview: {exam_text_val[:100]!r}", flush=True)
        assert exam_marks_val == 5
        print("  -> PASSED.", flush=True)

        # 6. Simplify answer
        print("\n[6] Testing POST /api/simplify...", flush=True)
        simp_resp = client.post(f"{BASE_URL}/api/simplify", json={
            'user_id': 'e2e-tester-1',
            'response_id': exam_resp_id or resp_id,
            'mode': 'simplify'
        })
        assert simp_resp.status_code == 200, f"Simplify failed: {simp_resp.text}"
        simp_data = simp_resp.json()
        simp_text = simp_data.get('answer', {}).get('text') if isinstance(simp_data.get('answer'), dict) else simp_data.get('answer_text', '')
        print(f"  -> Simplified text: {simp_text[:100]!r}", flush=True)
        print("  -> PASSED.", flush=True)

        # 7. Generate Quiz (regular mode)
        print("\n[7] Testing POST /api/quiz/generate (Regular Quiz)...", flush=True)
        quiz_resp = client.post(f"{BASE_URL}/api/quiz/generate", json={
            'user_id': 'e2e-tester-1',
            'topic': 'Gravity and Motion',
            'level': 'beginner',
            'language': 'en',
            'num_questions': 3,
            'is_diagnostic': False
        })
        assert quiz_resp.status_code == 200, f"Quiz generation failed: {quiz_resp.text}"
        quiz_data = quiz_resp.json()
        quiz_id = quiz_data.get('quiz_id')
        questions = quiz_data.get('questions', [])
        print(f"  -> Quiz ID: {quiz_id}", flush=True)
        print(f"  -> Questions generated: {len(questions)}", flush=True)
        assert len(questions) == 3
        for idx, q in enumerate(questions):
            print(f"    Q{idx+1}: {q.get('question')} (Options: {len(q.get('options', []))})", flush=True)
        print("  -> PASSED.", flush=True)

        # 8. Submit Quiz Attempt
        print(f"\n[8] Testing POST /api/quiz/submit (Submitting answers)...", flush=True)
        user_answers = {}
        for q in questions:
            user_answers[str(q['id'])] = q.get('correct_answer', 'A') # select correct answers for high score

        submit_resp = client.post(f"{BASE_URL}/api/quiz/submit", json={
            'quiz_id': quiz_id,
            'user_id': 'e2e-tester-1',
            'answers': user_answers,
            'time_taken_seconds': 45,
            'baseline_type': 'standard'
        })
        assert submit_resp.status_code == 200, f"Quiz submission failed: {submit_resp.text}"
        result_data = submit_resp.json()
        print(f"  -> Score: {result_data.get('score')}/{result_data.get('total_questions')} ({result_data.get('percentage')}%)", flush=True)
        print(f"  -> Feedback: {result_data.get('feedback')}", flush=True)
        assert result_data.get('score') == 3
        print("  -> PASSED.", flush=True)

        # 9. Learning Progress Analytics
        print(f"\n[9] Testing GET /api/progress for user 'e2e-tester-1'...", flush=True)
        prog_resp = client.get(f"{BASE_URL}/api/progress?user_id=e2e-tester-1")
        assert prog_resp.status_code == 200, f"Progress report failed: {prog_resp.text}"
        prog_data = prog_resp.json()
        print(f"  -> Total quizzes taken: {prog_data.get('total_quizzes_taken')}", flush=True)
        print(f"  -> Average score: {prog_data.get('average_score')}%", flush=True)
        print(f"  -> Total questions answered: {prog_data.get('total_questions_answered')}", flush=True)
        print(f"  -> Accuracy rate: {prog_data.get('accuracy_rate')}%", flush=True)
        print(f"  -> Topic breakdown count: {len(prog_data.get('topic_breakdown', []))}", flush=True)
        print(f"  -> Recent attempts: {len(prog_data.get('recent_attempts', []))}", flush=True)
        print("  -> PASSED.", flush=True)

    print("\n==================================================", flush=True)
    print("   ALL 9 END-TO-END VALIDATION TESTS PASSED! 🎉", flush=True)
    print("==================================================", flush=True)

if __name__ == '__main__':
    test_full_flow()
