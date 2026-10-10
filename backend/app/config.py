import os
from typing import Optional
from pydantic import BaseModel

MODEL_PRESETS = {
    "quality": "qwen3:8b",
    "fast": "qwen3:4b",
    "candidate": "gemma3",
    "coder": "qwen2.5-coder:7b",
}

class Settings(BaseModel):
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    # Base fallback model
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    # Model profiles & presets
    gen_model: str = os.getenv("GEN_MODEL", "quality")
    translate_model: str = os.getenv("TRANSLATE_MODEL", "quality")
    
    # Generation mode: direct | pivot
    generation_mode: str = os.getenv("GENERATION_MODE", "pivot")
    generation_mode_mr: str = os.getenv("GENERATION_MODE_MR", "")
    generation_mode_hi: str = os.getenv("GENERATION_MODE_HI", "")
    
    # Translator selection: indictrans2 | llm
    translator: str = os.getenv("TRANSLATOR", "llm")
    translate_question_to_en: bool = os.getenv("TRANSLATE_QUESTION_TO_EN", "false").lower() in ("true", "1")
    
    # Per-language sampling options
    mr_hi_temperature: float = float(os.getenv("MR_HI_TEMPERATURE", "0.3"))
    mr_hi_repeat_penalty: float = float(os.getenv("MR_HI_REPEAT_PENALTY", "1.08"))
    en_temperature: float = float(os.getenv("EN_TEMPERATURE", "0.3"))
    en_repeat_penalty: float = float(os.getenv("EN_REPEAT_PENALTY", "1.02"))
    
    # Context window & timeouts
    ollama_timeout_s: float = float(os.getenv("OLLAMA_TIMEOUT_S", "180"))
    ollama_max_concurrency: int = int(os.getenv("OLLAMA_MAX_CONCURRENCY", "2"))
    ollama_num_ctx: int = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
    ollama_keep_alive: str = os.getenv("OLLAMA_KEEP_ALIVE", "30m")
    
    # Qwen3 reasoning suppression
    qwen3_send_no_think: bool = True
    
    max_history_turns: int = int(os.getenv("MAX_HISTORY_TURNS", "6"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./edumitra.db")
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        if origin.strip()
    ]

    def resolve_model_name(self, model_or_preset: str) -> str:
        """Resolves preset key ('quality', 'fast', 'candidate', 'coder') or returns model tag."""
        key = (model_or_preset or "").lower().strip()
        return MODEL_PRESETS.get(key, model_or_preset)

    def get_gen_model(self) -> str:
        return self.resolve_model_name(self.gen_model or self.ollama_model)

    def get_translate_model(self) -> str:
        return self.resolve_model_name(self.translate_model or self.gen_model or self.ollama_model)

    def get_generation_mode(self, lang: str) -> str:
        """Returns direct or pivot mode for target language."""
        if lang == "en":
            return "direct"
        if lang == "mr" and self.generation_mode_mr:
            return self.generation_mode_mr.lower()
        if lang == "hi" and self.generation_mode_hi:
            return self.generation_mode_hi.lower()
        return (self.generation_mode or "pivot").lower()

    def get_sampling_options(self, lang: str, num_predict: Optional[int] = None) -> dict:
        is_indic = lang in ("mr", "hi")
        temp = self.mr_hi_temperature if is_indic else self.en_temperature
        rep = self.mr_hi_repeat_penalty if is_indic else self.en_repeat_penalty
        opts = {
            "temperature": temp,
            "repeat_penalty": rep,
            "num_thread": max(1, (os.cpu_count() or 4) - 1),
            "num_ctx": self.ollama_num_ctx,
        }
        if num_predict:
            opts["num_predict"] = num_predict
        return opts

settings = Settings()

