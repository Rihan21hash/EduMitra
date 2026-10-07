from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Feedback, Response as DBResponse
from app.schemas import FeedbackRequest, FeedbackResponse

router = APIRouter(prefix="/api", tags=["feedback"])

@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)):
    resp = db.query(DBResponse).filter(DBResponse.id == payload.response_id).first()
    if not resp:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Response not found"})

    rating = 1 if payload.rating > 0 else -1
    fb = Feedback(
        response_id=resp.id,
        rating=rating
    )
    db.add(fb)
    db.commit()

    return FeedbackResponse(success=True, rating=rating)
