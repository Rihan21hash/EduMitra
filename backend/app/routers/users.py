from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/api", tags=["users"])

@router.post("/users", response_model=UserResponse)
def create_guest_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = User(
        display_name=payload.display_name or "Guest Student",
        preferred_language=payload.preferred_language or "mr",
        default_level=payload.default_level or "beginner"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse(
        id=user.id,
        display_name=user.display_name,
        preferred_language=user.preferred_language,
        default_level=user.default_level,
        created_at=user.created_at.isoformat()
    )
