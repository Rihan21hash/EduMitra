import asyncio
import json
import logging
from typing import Dict, Any, Optional, AsyncIterator, Tuple
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

class OllamaError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

class OllamaClient:
    def __init__(self):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout_s
        self._semaphore = asyncio.Semaphore(settings.ollama_max_concurrency)

    async def check_health(self) -> Dict[str, Any]:
        """Check if Ollama service is reachable and list models."""
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    return {
                        "connected": True,
                        "active_model": self.model,
                        "available_models": models
                    }
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
        return {
            "connected": False,
            "active_model": self.model,
            "available_models": []
        }

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_format: bool = False,
        temperature: float = 0.3,
        num_predict: Optional[int] = None,
    ) -> str:
        """Call Ollama /api/generate with concurrency lock and timeout."""
        url = f"{self.base_url}/api/generate"
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
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
                    if resp.status_code != 200:
                        raise OllamaError("MODEL_UNAVAILABLE", f"Ollama returned status {resp.status_code}: {resp.text}")
                    data = resp.json()
                    response_text = data.get("response", "").strip()
                    if not response_text:
                        raise OllamaError("INTERNAL", "Empty response from Ollama model")
                    return response_text
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

    async def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.4,
        num_predict: Optional[int] = None,
    ) -> AsyncIterator[Tuple[str, bool]]:
        """
        Stream tokens from Ollama one by one.
        Yields (token_text, is_done) tuples.
        Acquires the concurrency semaphore for the full duration of the stream.
        """
        url = f"{self.base_url}/api/generate"
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system
        if num_predict:
            payload["options"]["num_predict"] = num_predict

        async with self._semaphore:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    async with client.stream("POST", url, json=payload) as resp:
                        if resp.status_code != 200:
                            raise OllamaError(
                                "MODEL_UNAVAILABLE",
                                f"Ollama returned status {resp.status_code}"
                            )
                        async for line in resp.aiter_lines():
                            if not line:
                                continue
                            try:
                                chunk = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            token = chunk.get("response", "")
                            done = chunk.get("done", False)
                            yield token, done
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

ollama_client = OllamaClient()
