from fastapi import APIRouter
from app.schemas import HealthResponse
from app.services.ollama_client import ollama_client

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def check_health():
    ollama_info = await ollama_client.check_health()
    return HealthResponse(
        status="ok" if ollama_info["connected"] else "degraded",
        ollama_connected=ollama_info["connected"],
        active_model=ollama_info["active_model"],
        available_models=ollama_info["available_models"],
        model_loaded=ollama_info.get("model_loaded", False)
    )

root_health_router = APIRouter(tags=["health"])
@root_health_router.get("/health", response_model=HealthResponse)
async def check_health_root():
    return await check_health()

