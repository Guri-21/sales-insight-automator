"""
Sales Insight Automator — Backend API
A FastAPI application that processes sales data files, generates AI summaries
using Groq (Llama 3), and delivers them via email.
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from typing import Optional

from email_validator import EmailNotValidError, validate_email
from fastapi import Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from middleware.security import limiter, verify_api_key
from services.ai_service import generate_summary
from services.email_service import send_summary_email
from services.file_parser import dataframe_to_summary_text, parse_file, validate_file

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ── App Lifespan ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Sales Insight Automator starting up...")
    logger.info(f"   CORS Origins: {os.getenv('CORS_ORIGINS', '*')}")
    logger.info(f"   API Key Required: {os.getenv('API_KEY_REQUIRED', 'false')}")
    yield
    logger.info("👋 Sales Insight Automator shutting down...")


# ── FastAPI App ───────────────────────────────────────────────
app = FastAPI(
    title="Sales Insight Automator API",
    description=(
        "Upload sales data files (CSV/XLSX) and receive AI-generated executive "
        "briefs delivered directly to your inbox. Powered by Groq (Llama 3)."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Rabbitt AI Engineering",
        "url": "https://rabbitt.ai",
    },
    license_info={
        "name": "MIT",
    },
)

# ── Rate Limiter ──────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ── Health Check ──────────────────────────────────────────────
@app.get(
    "/api/health",
    tags=["System"],
    summary="Health Check",
    description="Returns the health status of the API and its connected services.",
    response_description="Service health status",
)
async def health_check():
    """Check if the API and its dependencies are operational."""
    groq_configured = bool(os.getenv("GROQ_API_KEY"))
    resend_configured = bool(os.getenv("RESEND_API_KEY"))

    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "ai_engine": "configured" if groq_configured else "not_configured",
            "email_service": "configured" if resend_configured else "not_configured",
        },
    }


# ── Upload & Process ─────────────────────────────────────────
@app.post(
    "/api/upload",
    tags=["Sales Insights"],
    summary="Upload Sales Data & Generate Insight Brief",
    description=(
        "Upload a `.csv` or `.xlsx` sales data file along with a recipient email. "
        "The system will parse the data, generate an AI-powered executive summary "
        "using Groq AI, and email the brief to the specified recipient."
    ),
    response_description="Processing result with summary preview",
    responses={
        200: {
            "description": "Successfully processed and emailed the insight brief",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Insight brief generated and sent to user@example.com",
                        "summary_preview": "Executive Summary: Q3 revenue grew by 12%...",
                        "email_status": {"status": "sent", "email_id": "abc123"},
                    }
                }
            },
        },
        400: {"description": "Invalid file or input"},
        403: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "AI or email service error"},
    },
)
@limiter.limit("10/minute")
async def upload_and_process(
    request: Request,
    file: UploadFile = File(
        ..., description="Sales data file (.csv or .xlsx, max 10MB)"
    ),
    email: str = Form(
        ..., description="Recipient email address for the insight brief"
    ),
    _api_key: Optional[str] = Depends(verify_api_key),
):
    """
    Complete pipeline: Upload → Parse → AI Summary → Email Delivery.

    **Steps:**
    1. Validates the uploaded file (type, size, structure)
    2. Parses the data into a structured format
    3. Sends the data to Groq AI for analysis
    4. Formats and emails the executive brief to the recipient
    """
    # 1. Validate email
    try:
        email_info = validate_email(email, check_deliverability=False)
        clean_email = email_info.normalized
    except EmailNotValidError as e:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": f"Invalid email address: {str(e)}"},
        )

    logger.info(f"📤 Processing upload: {file.filename} → {clean_email}")

    # 2. Validate and parse file
    content = await validate_file(file)
    df = parse_file(content, file.filename or "unknown.csv")
    logger.info(f"📊 Parsed {len(df)} rows × {len(df.columns)} columns")

    # 3. Generate AI summary
    data_text = dataframe_to_summary_text(df)
    summary = await generate_summary(data_text)
    logger.info(f"🤖 AI summary generated ({len(summary)} chars)")

    # 4. Send email
    email_result = await send_summary_email(clean_email, summary, file.filename or "data")
    logger.info(f"📧 Email sent: {email_result}")

    return {
        "status": "success",
        "message": f"Insight brief generated and sent to {clean_email}",
        "summary_preview": summary[:500] + ("..." if len(summary) > 500 else ""),
        "email_status": email_result,
        "data_shape": {"rows": len(df), "columns": len(df.columns)},
    }


# ── Global Exception Handler ─────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "detail": "An internal server error occurred. Please try again.",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENV", "development") == "development",
    )
