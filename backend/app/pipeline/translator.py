import asyncio
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator

from app.config import settings
from app.services.ollama_client import ollama_client, OllamaError
from app.lexicon import lexicon_manager
from app.pipeline.prompt_builder import STYLE_GUIDES, LANGUAGE_NAMES
from app.pipeline.validator import validate_translation
from app.pipeline.content_protection import mask_content, restore_content, AnswerTermPinning

logger = logging.getLogger("edumitra.translator")

# IndicTrans2 ISO Language code mappings
INDICTRANS2_LANG_CODES = {
    "en": "eng_Latn",
    "mr": "mar_Deva",
    "hi": "hin_Deva"
}

class BaseTranslator(ABC):
    @abstractmethod
    async def translate_segment(
        self,
        text: str,
        target_lang: str,
        answer_state: Optional[AnswerTermPinning] = None
    ) -> str:
        """Translates a single segment from English to target_lang."""
        pass

    async def translate_batch(
        self,
        texts: List[str],
        target_lang: str,
        answer_state: Optional[AnswerTermPinning] = None
    ) -> List[str]:
        """Translates a batch of segments."""
        results = []
        for t in texts:
            res = await self.translate_segment(t, target_lang, answer_state)
            results.append(res)
        return results

class LLMTranslator(BaseTranslator):
    """
    Ollama-based translator.
    - Low temperature (<= 0.1)
    - Full content protection: masking formulas, code, units, numbers
    - Dictionary term pinning with per-answer first-mention memory
    - Placeholder verification and retry fallback
    """
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.get_translate_model()

    def _build_segment_prompt(self, masked_text: str, target_lang: str) -> str:
        lang_name = LANGUAGE_NAMES.get(target_lang, "Marathi")
        style_guide = STYLE_GUIDES.get(target_lang, "")

        prompt = f"""You are EduMitra's precise academic translator into {lang_name}.
Translate the following English segment into natural, grammatically correct {lang_name} (Devanagari script).

CRITICAL TRANSLATION RULES:
1. PRESERVE ALL PLACEHOLDERS EXACTLY: Tokens like `__IMATH_0__`, `__BMATH_0__`, `__UNIT_0__`, `__DEC_0__`, `__CBLOCK_0__`, `__BOLD_0__`, `__GLOSS_0__` MUST appear UNMODIFIED in your output.
2. Keep numbers and formulas identical.
3. Zero language leakage: do not mix Hindi words into Marathi, or Marathi into Hindi.
4. Maintain academic warmth and clarity.

{style_guide}

Text to translate:
---
{masked_text}
---

Provide ONLY the translated {lang_name} text with all placeholders intact. Do not add explanations or quotes.
"""
        return prompt

    async def translate_segment(
        self,
        text: str,
        target_lang: str,
        answer_state: Optional[AnswerTermPinning] = None
    ) -> str:
        if not text.strip():
            return text

        # If target language is English, no translation needed
        if target_lang == "en":
            return text

        # 1. Mask content (formulas, code, numbers, glossary terms)
        mask_res = mask_content(text, target_lang, answer_state)
        masked_text = mask_res.masked_text
        placeholders = mask_res.placeholders

        # 2. Call LLM to translate masked text
        prompt = self._build_segment_prompt(masked_text, target_lang)
        messages = [
            {"role": "system", "content": f"You are an expert academic translator into {LANGUAGE_NAMES.get(target_lang, 'Marathi')}."},
            {"role": "user", "content": prompt}
        ]

        attempt = 0
        max_attempts = 2
        restored_text = ""
        is_valid = False

        while attempt < max_attempts and not is_valid:
            attempt += 1
            try:
                raw_translation = await ollama_client.chat(
                    messages=messages,
                    temperature=0.1,
                    num_predict=600,
                    model=self.model_name
                )
                restored_text, is_valid = restore_content(raw_translation, placeholders)
                if not is_valid and attempt < max_attempts:
                    logger.warning(f"LLM translation placeholder mismatch on attempt {attempt}. Retrying...")
            except Exception as e:
                logger.warning(f"LLM translation error on attempt {attempt}: {e}")
                if attempt >= max_attempts:
                    # Fallback to English segment with marker
                    return f"{text} [translation error: {str(e)}]"

        if not is_valid:
            logger.warning(f"Translation segment failed placeholder validation after retry. Fallback to English segment.")
            return f"{text} [not translated]"

        return restored_text

class IndicTrans2Translator(BaseTranslator):
    """
    AI4Bharat IndicTrans2 distilled model via Hugging Face.
    Model: ai4bharat/indictrans2-en-indic-dist-200M (~200M parameters).
    Lazy-loaded on first use and executes inference in thread pool.
    """
    def __init__(self, model_id: str = "ai4bharat/indictrans2-en-indic-dist-200M"):
        self.model_id = model_id
        self.tokenizer = None
        self.model = None
        self.is_initialized = False
        self._load_lock = asyncio.Lock()
        self._fallback_translator = LLMTranslator()

    async def _ensure_loaded(self) -> bool:
        if self.is_initialized:
            return True

        async with self._load_lock:
            if self.is_initialized:
                return True
            try:
                # Run heavy imports & load in background thread
                def _load():
                    import torch
                    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
                    logger.info(f"Loading IndicTrans2 model '{self.model_id}'...")
                    tokenizer = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=True)
                    model = AutoModelForSeq2SeqLM.from_pretrained(
                        self.model_id,
                        trust_remote_code=True,
                        torch_dtype=torch.float32
                    )
                    model.eval()
                    return tokenizer, model

                self.tokenizer, self.model = await asyncio.to_thread(_load)
                self.is_initialized = True
                logger.info("IndicTrans2 model initialized successfully.")
                return True
            except ImportError:
                logger.warning("IndicTrans2 dependencies (torch, transformers) not installed. Falling back to LLM translator.")
                return False
            except Exception as e:
                logger.warning(f"Failed to load IndicTrans2 model ({e}). Falling back to LLM translator.")
                return False

    async def translate_segment(
        self,
        text: str,
        target_lang: str,
        answer_state: Optional[AnswerTermPinning] = None
    ) -> str:
        if not text.strip() or target_lang == "en":
            return text

        loaded = await self._ensure_loaded()
        if not loaded:
            return await self._fallback_translator.translate_segment(text, target_lang, answer_state)

        # 1. Mask content
        mask_res = mask_content(text, target_lang, answer_state)
        masked_text = mask_res.masked_text
        placeholders = mask_res.placeholders

        src_lang = INDICTRANS2_LANG_CODES.get("en", "eng_Latn")
        tgt_lang = INDICTRANS2_LANG_CODES.get(target_lang, "mar_Deva")

        def _infer():
            import torch
            inputs = self.tokenizer(
                [masked_text],
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            with torch.no_grad():
                generated_tokens = self.model.generate(
                    **inputs,
                    use_cache=True,
                    max_length=512,
                    num_beams=4,
                    early_stopping=True
                )
            decoded = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
            return decoded[0] if decoded else ""

        try:
            raw_out = await asyncio.to_thread(_infer)
            restored, is_valid = restore_content(raw_out, placeholders)
            if not is_valid:
                logger.warning("IndicTrans2 output had missing placeholders. Retrying with LLM translator.")
                return await self._fallback_translator.translate_segment(text, target_lang, answer_state)
            return restored
        except Exception as e:
            logger.warning(f"IndicTrans2 inference failed: {e}. Falling back to LLM translator.")
            return await self._fallback_translator.translate_segment(text, target_lang, answer_state)

_TRANSLATOR_INSTANCES: Dict[str, BaseTranslator] = {}

def get_translator(name: Optional[str] = None) -> BaseTranslator:
    """Returns requested translator instance ('indictrans2' or 'llm') with caching."""
    chosen_name = (name or settings.translator or "llm").lower().strip()
    if chosen_name in _TRANSLATOR_INSTANCES:
        return _TRANSLATOR_INSTANCES[chosen_name]

    if chosen_name == "indictrans2":
        instance = IndicTrans2Translator()
    else:
        instance = LLMTranslator()

    _TRANSLATOR_INSTANCES[chosen_name] = instance
    return instance

async def translate_response(
    original_text: str,
    target_language: str,
    translator_name: Optional[str] = None
) -> Dict[str, Any]:
    """Translates an entire response to the target language and validates."""
    if target_language == "en":
        return {
            "translated_text": original_text,
            "language": "en",
            "validation": {"passed": True, "notes": []}
        }

    translator = get_translator(translator_name)
    answer_state = AnswerTermPinning(target_language)

    # Split into paragraphs or major segments to maintain high fidelity
    paragraphs = original_text.split("\n\n")
    translated_paras = []
    for p in paragraphs:
        if not p.strip():
            translated_paras.append("")
            continue
        trans_p = await translator.translate_segment(p, target_language, answer_state)
        translated_paras.append(trans_p)

    full_translated = "\n\n".join(translated_paras).strip()
    validation = validate_translation(original_text, full_translated, target_language)

    return {
        "translated_text": full_translated,
        "language": target_language,
        "validation": validation
    }

async def translate_response_stream(
    original_text: str,
    target_language: str,
    translator_name: Optional[str] = None
) -> AsyncIterator[Dict[str, Any]]:
    """Streams translation token by token or segment by segment."""
    trans_res = await translate_response(original_text, target_language, translator_name)
    translated_text = trans_res["translated_text"]

    # Stream out words/tokens progressively
    words = translated_text.split(" ")
    for idx, w in enumerate(words):
        token = w + (" " if idx < len(words) - 1 else "")
        yield {
            "event": "token",
            "data": {"token": token}
        }
        await asyncio.sleep(0.01)

    yield {
        "event": "done",
        "data": {
            "translated_text": translated_text,
            "validation": trans_res["validation"]
        }
    }
