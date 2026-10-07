import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.db import Base, engine
from app.routers import health, users, question, simplify, exam_answer, followup, quiz, history, feedback

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("edumitra")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing EduMitra database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("EduMitra backend started successfully.")
    yield
    logger.info("EduMitra backend shutting down.")

app = FastAPI(
    title="EduMitra API",
    description="Multilingual Academic Support System Backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for hackathon local dev flexibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standard error handler for HTTP exceptions
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        code = detail.get("code", "INTERNAL")
        msg = detail.get("message", str(detail))
    else:
        code = "HTTP_ERROR"
        msg = str(detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": msg}}
    )

# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "INVALID_INPUT", "message": "Input validation error", "details": exc.errors()}}
    )

# Fallback generic exception handler (never leak raw stack trace)
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL", "message": "An unexpected error occurred. Please try again."}}
    )

# Include Routers
app.include_router(health.router)
app.include_router(users.router)
app.include_router(question.router)
app.include_router(simplify.router)
app.include_router(exam_answer.router)
app.include_router(followup.router)
app.include_router(quiz.router)
app.include_router(history.router)
app.include_router(feedback.router)

@app.get("/")
def root():
    return {
        "app": "EduMitra Backend",
        "status": "online",
        "docs": "/docs"
    }
