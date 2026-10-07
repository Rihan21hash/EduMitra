import os
from pydantic import BaseModel

class Settings(BaseModel):
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    ollama_timeout_s: float = float(os.getenv("OLLAMA_TIMEOUT_S", "120"))
    ollama_max_concurrency: int = int(os.getenv("OLLAMA_MAX_CONCURRENCY", "1"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./edumitra.db")
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
        if origin.strip()
    ]

settings = Settings()
