"""Pydantic models for API requests and responses."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TranslationStatus(str, Enum):
    """Status of translation operation."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"


class TranslationRequest(BaseModel):
    """Request model for subtitle translation."""

    srt_content: str = Field(
        ...,
        description="The SRT subtitle content to translate",
        min_length=1,
    )
    source_language: str = Field(
        ...,
        description="ISO 639-1 language code of source (e.g., 'en', 'es')",
        min_length=2,
        max_length=5,
    )
    target_language: str = Field(
        ...,
        description="ISO 639-1 language code of target (e.g., 'tr', 'de')",
        min_length=2,
        max_length=5,
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "srt_content": "1\n00:00:01,000 --> 00:00:04,000\nHello, world!\n\n2\n00:00:05,000 --> 00:00:08,000\nHow are you?",
                    "source_language": "en",
                    "target_language": "tr",
                }
            ]
        }
    }


class TranslationResponse(BaseModel):
    """Response model for subtitle translation."""

    translated_srt_content: str = Field(
        ...,
        description="The translated SRT content",
    )
    status: TranslationStatus = Field(
        ...,
        description="Status of the translation operation",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if translation failed",
    )
    stats: Optional[dict] = Field(
        default=None,
        description="Translation statistics",
    )


class SubtitleEntry(BaseModel):
    """Represents a single subtitle entry."""

    index: int
    start_time: str
    end_time: str
    text: str

    @property
    def timestamp(self) -> str:
        """Get formatted timestamp string."""
        return f"{self.start_time} --> {self.end_time}"


class TranslationChunk(BaseModel):
    """A chunk of sentences for context-aware translation."""

    sentences: list[str]
