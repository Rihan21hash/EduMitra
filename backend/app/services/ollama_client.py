import asyncio
import json
import logging
import os
import re
from typing import Dict, Any, Optional, AsyncIterator, Tuple
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

class OllamaError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

def strip_reasoning(text: str) -> str:
    """Removes any <think>...</think> reasoning blocks from model text."""
    if not text:
        return ""
    cleaned = re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'<thought>[\s\S]*?</thought>', '', cleaned, flags=re.IGNORECASE)
    # If a dangling <think> tag opened without closing
    cleaned = re.sub(r'<think>[\s\S]*$', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

class OllamaClient:
    def __init__(self):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout_s
        self._semaphore = asyncio.Semaphore(settings.ollama_max_concurrency)

    async def warmup(self, model: Optional[str] = None) -> bool:
        """Pre-loads the model weights into memory with keep_alive."""
        target_model = model or settings.get_gen_model()
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": target_model,
            "messages": [{"role": "user", "content": "hi"}],
            "stream": False,
            "keep_alive": settings.ollama_keep_alive,
            "options": {"num_predict": 1}
        }
        if "qwen3" in target_model.lower() or settings.qwen3_send_no_think:
            payload["think"] = False
            payload["options"]["think"] = False

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    logger.info(f"Ollama model '{target_model}' warmed up successfully.")
                    return True
                elif res.status_code == 404 and target_model != settings.ollama_model:
                    logger.warning(f"Model '{target_model}' not found, warming up fallback '{settings.ollama_model}'")
                    return await self.warmup(model=settings.ollama_model)
        except Exception as e:
            logger.warning(f"Ollama warm-up warning: {e}")
        return False

    async def check_health(self) -> Dict[str, Any]:
        """Check if Ollama service is reachable, list models, and check loaded status."""
        tags_url = f"{self.base_url}/api/tags"
        ps_url = f"{self.base_url}/api/ps"
        connected = False
        available_models = []
        model_loaded = False
        active = settings.get_gen_model()

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                t_res = await client.get(tags_url)
                if t_res.status_code == 200:
                    connected = True
                    available_models = [m.get("name") for m in t_res.json().get("models", [])]

                ps_res = await client.get(ps_url)
                if ps_res.status_code == 200:
                    running_models = [m.get("name") for m in ps_res.json().get("models", [])]
                    model_loaded = any(active in rm or settings.ollama_model in rm for rm in running_models)
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")

        return {
            "connected": connected,
            "active_model": active,
            "fallback_model": settings.ollama_model,
            "available_models": available_models,
            "model_loaded": model_loaded
        }

    def _build_payload(
        self,
        messages: list[Dict[str, str]],
        model: str,
        stream: bool,
        temperature: float = 0.3,
        repeat_penalty: float = 1.05,
        num_predict: Optional[int] = None,
        json_format: bool = False
    ) -> Dict[str, Any]:
        options: Dict[str, Any] = {
            "temperature": temperature,
            "repeat_penalty": repeat_penalty,
            "num_thread": max(1, (os.cpu_count() or 4) - 1),
            "num_ctx": settings.ollama_num_ctx,
        }
        if num_predict:
            options["num_predict"] = num_predict

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "keep_alive": settings.ollama_keep_alive,
            "options": options
        }

        # Qwen3 reasoning suppression
        if "qwen3" in model.lower() or settings.qwen3_send_no_think:
            payload["think"] = False
            options["think"] = False

        if json_format:
            payload["format"] = "json"

        return payload

    async def chat(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.3,
        repeat_penalty: float = 1.08,
        num_predict: Optional[int] = None,
        json_format: bool = False,
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Call Ollama /api/chat with messages array, auto-handling truncation retry."""
        target_model = model or settings.get_gen_model()
        url = f"{self.base_url}/api/chat"

        payload = self._build_payload(
            messages=messages,
            model=target_model,
            stream=False,
            temperature=temperature,
            repeat_penalty=repeat_penalty,
            num_predict=num_predict,
            json_format=json_format
        )
        # Merge any extra options from caller
        if options:
            payload["options"].update(options)

        async with self._semaphore:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, json=payload)

                    # Graceful fallback if model is unavailable
                    if resp.status_code == 404 and target_model != settings.ollama_model:
                        logger.warning(f"Model '{target_model}' not found in Ollama. Falling back to '{settings.ollama_model}'.")
                        payload["model"] = settings.ollama_model
                        resp = await client.post(url, json=payload)

                    if resp.status_code != 200:
                        raise OllamaError("MODEL_UNAVAILABLE", f"Ollama returned status {resp.status_code}: {resp.text}")

                    data = resp.json()
                    msg = data.get("message", {})
                    response_text = msg.get("content", "").strip()
                    done_reason = data.get("done_reason")
                    eval_count = data.get("eval_count")

                    # Handle truncation by token cap
                    if done_reason == "length" and num_predict:
                        higher_cap = min(settings.ollama_num_ctx - 1000, int(num_predict * 1.8))
                        logger.warning(
                            f"Answer truncated due to token cap (eval_count={eval_count}, num_predict={num_predict}). "
                            f"Auto-retrying once with higher cap ({higher_cap})..."
                        )
                        payload["options"]["num_predict"] = higher_cap
                        retry_resp = await client.post(url, json=payload)
                        if retry_resp.status_code == 200:
                            retry_data = retry_resp.json()
                            retry_content = retry_data.get("message", {}).get("content", "").strip()
                            if retry_content:
                                response_text = retry_content
                                done_reason = retry_data.get("done_reason")

                    cleaned = strip_reasoning(response_text)
                    if not cleaned:
                        raise OllamaError("INTERNAL", "Empty response from Ollama model")
                    return cleaned

            except httpx.TimeoutException:
                logger.error("Ollama chat timed out")
                raise OllamaError("MODEL_TIMEOUT", f"Ollama call timed out after {self.timeout}s")
            except httpx.ConnectError:
                logger.error("Could not connect to Ollama")
                raise OllamaError("MODEL_UNAVAILABLE", f"Cannot connect to Ollama at {self.base_url}")
            except OllamaError:
                raise
            except Exception as e:
                logger.error(f"Unexpected error calling Ollama chat: {e}")
                raise OllamaError("INTERNAL", str(e))

    async def chat_stream(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.3,
        repeat_penalty: float = 1.08,
        num_predict: Optional[int] = None,
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream tokens from Ollama /api/chat.
        Filters out any reasoning tokens (<think>...</think>).
        Yields dicts: {'token': str, 'done': bool, 'meta': Optional[dict]}
        """
        target_model = model or settings.get_gen_model()
        url = f"{self.base_url}/api/chat"

        payload = self._build_payload(
            messages=messages,
            model=target_model,
            stream=True,
            temperature=temperature,
            repeat_penalty=repeat_penalty,
            num_predict=num_predict
        )
        # Merge any extra options from caller
        if options:
            payload["options"].update(options)

        in_think = False

        async with self._semaphore:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, json=payload)

                    # Fallback if model not found
                    if resp.status_code == 404 and target_model != settings.ollama_model:
                        logger.warning(f"Stream model '{target_model}' not found in Ollama. Falling back to '{settings.ollama_model}'.")
                        payload["model"] = settings.ollama_model

                    async with client.stream("POST", url, json=payload) as stream_resp:
                        if stream_resp.status_code != 200:
                            raise OllamaError("MODEL_UNAVAILABLE", f"Ollama returned status {stream_resp.status_code}")

                        async for line in stream_resp.aiter_lines():
                            if not line:
                                continue
                            try:
                                chunk = json.loads(line)
                            except json.JSONDecodeError:
                                continue

                            msg = chunk.get("message", {})
                            token = msg.get("content", "")
                            done = chunk.get("done", False)

                            # Filter reasoning tags
                            if "<think>" in token.lower():
                                in_think = True
                            if in_think:
                                if "</think>" in token.lower():
                                    in_think = False
                                    parts = re.split(r'</think>', token, flags=re.IGNORECASE)
                                    token = parts[-1]
                                else:
                                    token = ""

                            meta = None
                            if done:
                                meta = {
                                    "done_reason": chunk.get("done_reason"),
                                    "total_duration": chunk.get("total_duration"),
                                    "load_duration": chunk.get("load_duration"),
                                    "prompt_eval_count": chunk.get("prompt_eval_count"),
                                    "eval_count": chunk.get("eval_count"),
                                    "eval_duration": chunk.get("eval_duration"),
                                    "model": target_model
                                }
                                if chunk.get("done_reason") == "length":
                                    logger.warning(f"Streaming answer truncated by token cap (eval_count={chunk.get('eval_count')})")

                            if token or done:
                                yield {"token": token, "done": done, "meta": meta}
                            if done:
                                break

            except httpx.ConnectError:
                raise OllamaError("MODEL_UNAVAILABLE", f"Cannot connect to Ollama at {self.base_url}")
            except httpx.TimeoutException:
                raise OllamaError("MODEL_TIMEOUT", f"Ollama stream timed out after {self.timeout}s")
            except OllamaError:
                raise
            except Exception as e:
                logger.error(f"Ollama stream error: {e}")
                raise OllamaError("INTERNAL", str(e))

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_format: bool = False,
        temperature: float = 0.3,
        num_predict: Optional[int] = None,
        model: Optional[str] = None,
    ) -> str:
        """Call Ollama /api/generate with concurrency lock and timeout."""
        target_model = model or settings.get_gen_model()
        url = f"{self.base_url}/api/generate"
        payload: Dict[str, Any] = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": settings.ollama_keep_alive,
            "options": {
                "temperature": temperature,
                "num_thread": max(1, (os.cpu_count() or 4) - 1),
                "num_ctx": settings.ollama_num_ctx,
            }
        }
        if num_predict:
            payload["options"]["num_predict"] = num_predict
        if system:
            payload["system"] = system
        if json_format:
            payload["format"] = "json"

        async with self._semaphore:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 404 and target_model != settings.ollama_model:
                        payload["model"] = settings.ollama_model
                        resp = await client.post(url, json=payload)

                    if resp.status_code != 200:
                        raise OllamaError("MODEL_UNAVAILABLE", f"Ollama returned status {resp.status_code}: {resp.text}")
                    data = resp.json()
                    response_text = data.get("response", "").strip()
                    cleaned = strip_reasoning(response_text)
                    if not cleaned:
                        raise OllamaError("INTERNAL", "Empty response from Ollama model")
                    return cleaned
            except httpx.TimeoutException:
                logger.error("Ollama generation timed out")
                raise OllamaError("MODEL_TIMEOUT", f"Ollama call timed out after {self.timeout}s")
            except httpx.ConnectError:
                logger.error("Could not connect to Ollama")
                raise OllamaError("MODEL_UNAVAILABLE", f"Cannot connect to Ollama at {self.base_url}")
            except OllamaError:
                raise
            except Exception as e:
                logger.error(f"Unexpected error calling Ollama: {e}")
                raise OllamaError("INTERNAL", str(e))

ollama_client = OllamaClient()
