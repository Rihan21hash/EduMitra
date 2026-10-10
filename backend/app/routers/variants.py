import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Response as DBResponse, ResponseVariant, gen_uuid, utc_now
from app.pipeline.translator import translate_response, translate_response_stream
from app.services.ollama_client import OllamaError

logger = logging.getLogger("edumitra.variants")

router = APIRouter(prefix="/api", tags=["variants"])

class VariantRequest(BaseModel):
    language: Optional[str] = None
    target_language: Optional[str] = None

    def get_target_lang(self) -> str:
        return (self.target_language or self.language or "en").lower()

class VariantResponse(BaseModel):
    response_id: str
    language: str
    content: str
    answer_text: Optional[str] = None
    origin: str  # 'original' | 'translated'
    validation: Optional[Dict[str, Any]] = None

@router.get("/response/{response_id}/variants")
def get_response_variants(response_id: str, db: Session = Depends(get_db)):
    """Fetch all saved language variants for an answer."""
    resp = db.query(DBResponse).filter(DBResponse.id == response_id).first()
    if not resp:
        raise HTTPException(status_code=404, detail="Response not found")

    variants = db.query(ResponseVariant).filter(ResponseVariant.response_id == response_id).all()
    result = []
    # Always include the original response as a variant if not explicitly saved
    has_orig = any(v.language == resp.language for v in variants)
    if not has_orig:
        result.append({
            "language": resp.language,
            "content": resp.content,
            "origin": "original",
            "created_at": resp.created_at.isoformat() if resp.created_at else None
        })
    for v in variants:
        result.append({
            "language": v.language,
            "content": v.content,
            "origin": v.origin,
            "created_at": v.created_at.isoformat() if v.created_at else None
        })
    return {"response_id": response_id, "variants": result}

@router.post("/response/{response_id}/variant", response_model=VariantResponse)
async def get_or_create_variant(
    response_id: str,
    payload: VariantRequest,
    db: Session = Depends(get_db)
):
    """
    Returns an existing variant or generates a faithful translation in the target language.
    """
    resp = db.query(DBResponse).filter(DBResponse.id == response_id).first()
    if not resp:
        raise HTTPException(status_code=404, detail="Response not found")

    target_lang = payload.get_target_lang()

    # 1. Check if original matches target
    if resp.language == target_lang:
        return VariantResponse(
            response_id=resp.id,
            language=target_lang,
            content=resp.content,
            answer_text=resp.content,
            origin="original"
        )

    # 2. Check if variant already exists in DB
    existing = (
        db.query(ResponseVariant)
        .filter(ResponseVariant.response_id == response_id, ResponseVariant.language == target_lang)
        .first()
    )
    if existing:
        return VariantResponse(
            response_id=resp.id,
            language=target_lang,
            content=existing.content,
            answer_text=existing.content,
            origin=existing.origin
        )

    # 3. Generate translation via translator pipeline
    try:
        trans_res = await translate_response(resp.content, target_lang)
    except OllamaError as oe:
        status_code = 503 if oe.code == "MODEL_UNAVAILABLE" else 500
        raise HTTPException(status_code=status_code, detail={"code": oe.code, "message": oe.message})
    except Exception as e:
        logger.error(f"Error generating translation variant: {e}")
        raise HTTPException(status_code=500, detail={"code": "INTERNAL", "message": str(e)})

    # 4. Save variant to DB
    new_variant = ResponseVariant(
        id=gen_uuid(),
        response_id=resp.id,
        language=target_lang,
        content=trans_res["translated_text"],
        origin="translated",
        model=resp.model or "qwen2.5-coder:7b",
        created_at=utc_now()
    )
    db.add(new_variant)
    try:
        db.commit()
    except Exception as e:
        logger.warning(f"Error committing variant: {e}")
        db.rollback()

    return VariantResponse(
        response_id=resp.id,
        language=target_lang,
        content=trans_res["translated_text"],
        answer_text=trans_res["translated_text"],
        origin="translated",
        validation=trans_res.get("validation")
    )

@router.post("/response/{response_id}/variant/stream")
async def stream_variant(
    response_id: str,
    payload: VariantRequest,
    db: Session = Depends(get_db)
):
    """Streams translation tokens for an answer variant via SSE."""
    resp = db.query(DBResponse).filter(DBResponse.id == response_id).first()
    if not resp:
        raise HTTPException(status_code=404, detail="Response not found")

    target_lang = payload.get_target_lang()

    # 1. Check if cached
    existing = (
        db.query(ResponseVariant)
        .filter(ResponseVariant.response_id == response_id, ResponseVariant.language == target_lang)
        .first()
    )
    if existing or resp.language == target_lang:
        content = existing.content if existing else resp.content
        async def cached_stream():
            yield f"event: token\ndata: {json.dumps({'token': content}, ensure_ascii=False)}\n\n"
            yield f"event: done\ndata: {json.dumps({'translated_text': content, 'language': target_lang}, ensure_ascii=False)}\n\n"
        return StreamingResponse(cached_stream(), media_type="text/event-stream")

    # 2. Live translation stream
    async def event_generator():
        translated_text = ""
        try:
            async for chunk in translate_response_stream(resp.content, target_lang):
                ev = chunk.get("event")
                data = chunk.get("data", {})
                if ev == "token":
                    yield f"event: token\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                elif ev == "done":
                    translated_text = data.get("translated_text", "")
                    yield f"event: done\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"Stream variant error: {e}")
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
            return

        # Persist once finished
        if translated_text:
            try:
                new_var = ResponseVariant(
                    id=gen_uuid(),
                    response_id=resp.id,
                    language=target_lang,
                    content=translated_text,
                    origin="translated",
                    model=resp.model or "qwen2.5-coder:7b",
                    created_at=utc_now()
                )
                db.add(new_var)
                db.commit()
            except Exception as e:
                logger.warning(f"Failed to persist streamed variant: {e}")
                db.rollback()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
