"""FastAPI application for subtitle translation service."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from rich.logging import RichHandler

from .config import get_settings
from .models import TranslationRequest, TranslationResponse, TranslationStatus
from .translator import SubtitleTranslator

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, show_time=True)],
)
logger = logging.getLogger(__name__)

# Global translator instance
translator: SubtitleTranslator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown."""
    global translator

    logger.info("Starting subtitle translation service")
    logger.info(f"OpenAI model: {settings.openai_model}")
    logger.info(f"Context window size: {settings.context_window_size}")

    # Initialize translator
    translator = SubtitleTranslator(settings=settings)

    yield

    logger.info("Shutting down subtitle translation service")


# Create FastAPI app
app = FastAPI(
    title="Context-Aware SRT Translation",
    description=(
        "A subtitle translation service that uses context windows "
        "for more accurate and natural translations."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


@app.post(
    "/subtitle-translate",
    response_model=TranslationResponse,
    summary="Translate SRT subtitles",
    description=(
        "Translate SRT subtitle content using context-aware translation. "
        "Uses OpenAI as primary service with DeepL as fallback."
    ),
)
async def translate_subtitle(request: TranslationRequest) -> TranslationResponse:
    """
    Translate SRT subtitle content.

    The service uses a context window approach, translating sentences
    in groups to maintain contextual understanding and produce more
    natural translations.

    - **srt_content**: Raw SRT file content
    - **source_language**: ISO 639-1 code (e.g., 'en', 'es')
    - **target_language**: ISO 639-1 code (e.g., 'tr', 'de')
    """
    if translator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Translation service not initialized",
        )

    logger.info(
        f"Translation request: {request.source_language} -> {request.target_language}"
    )

    try:
        job = await translator.translate(
            srt_content=request.srt_content,
            source_language=request.source_language,
            target_language=request.target_language,
        )

        if job.status == TranslationStatus.FAILURE:
            logger.error(f"Translation failed: {job.error}")
            return TranslationResponse(
                translated_srt_content="",
                status=TranslationStatus.FAILURE,
                error_message=job.error or "Translation failed",
                stats=job.stats.to_dict(),
            )

        return TranslationResponse(
            translated_srt_content=job.translated_content,
            status=job.status,
            error_message=job.error,
            stats=job.stats.to_dict(),
        )

    except Exception as e:
        logger.exception("Unexpected error during translation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation error: {str(e)}",
        )


@app.post(
    "/translate",
    response_model=TranslationResponse,
    summary="Alias for /subtitle-translate",
    include_in_schema=False,  # Hide from docs, keep for compatibility
)
async def translate_subtitle_alias(request: TranslationRequest) -> TranslationResponse:
    """Alias endpoint for backwards compatibility."""
    return await translate_subtitle(request)
