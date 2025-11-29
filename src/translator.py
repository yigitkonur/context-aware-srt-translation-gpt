"""Main translation orchestrator with context-aware processing."""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional

from .config import Settings, get_settings
from .models import TranslationChunk, TranslationStatus
from .srt_parser import SRTParser, create_chunks
from .services.base import TranslationService
from .services.openai_service import OpenAITranslationService
from .services.deepl_service import DeepLTranslationService

logger = logging.getLogger(__name__)


@dataclass
class TranslationStats:
    """Statistics for a translation job."""

    total_sentences: int = 0
    translated_sentences: int = 0
    failed_sentences: int = 0
    openai_calls: int = 0
    deepl_calls: int = 0
    elapsed_seconds: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.total_sentences == 0:
            return 1.0
        return self.translated_sentences / self.total_sentences

    def to_dict(self) -> dict:
        return {
            "total_sentences": self.total_sentences,
            "translated_sentences": self.translated_sentences,
            "failed_sentences": self.failed_sentences,
            "success_rate": round(self.success_rate * 100, 2),
            "openai_calls": self.openai_calls,
            "deepl_calls": self.deepl_calls,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
        }


@dataclass
class TranslationJob:
    """Result of a complete translation job."""

    translated_content: str
    status: TranslationStatus
    stats: TranslationStats
    error: Optional[str] = None


class SubtitleTranslator:
    """
    Context-aware subtitle translator.

    Uses a sliding window approach to translate subtitles in chunks,
    maintaining context between sequential lines for more accurate
    and natural translations.
    """

    def __init__(
        self,
        primary_service: Optional[TranslationService] = None,
        fallback_service: Optional[TranslationService] = None,
        settings: Optional[Settings] = None,
    ):
        self._settings = settings or get_settings()
        self._parser = SRTParser()

        # Initialize services
        self._primary = primary_service or OpenAITranslationService(self._settings)
        self._fallback = fallback_service or DeepLTranslationService(self._settings)

        # Concurrency control
        self._semaphore = asyncio.Semaphore(
            self._settings.max_concurrent_requests
        )

    async def translate(
        self,
        srt_content: str,
        source_language: str,
        target_language: str,
    ) -> TranslationJob:
        """
        Translate SRT content from source to target language.

        Args:
            srt_content: Raw SRT file content
            source_language: Source language code (e.g., 'en')
            target_language: Target language code (e.g., 'tr')

        Returns:
            TranslationJob with results and statistics
        """
        start_time = time.time()
        stats = TranslationStats()

        try:
            # Parse the SRT content
            parsed = self._parser.parse(srt_content)
            sentences = parsed.sentences
            stats.total_sentences = len(sentences)

            logger.info(
                f"Starting translation of {len(parsed.entries)} subtitles "
                f"({len(sentences)} sentences)"
            )

            # Create chunks for context-aware translation
            chunks = list(create_chunks(
                sentences,
                chunk_size=self._settings.context_window_size,
            ))

            # Translate all chunks concurrently
            tasks = [
                self._translate_chunk(chunk, source_language, target_language, stats)
                for chunk in chunks
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Flatten results and handle errors
            translated_sentences = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Chunk {i} failed: {result}")
                    # Use placeholders for failed chunks
                    chunk_size = len(chunks[i].sentences)
                    translated_sentences.extend(["[Translation Error]"] * chunk_size)
                    stats.failed_sentences += chunk_size
                else:
                    translated_sentences.extend(result)
                    stats.translated_sentences += len(result)

            # Reconstruct the SRT
            translated_content = self._parser.reconstruct(parsed, translated_sentences)

            stats.elapsed_seconds = time.time() - start_time

            # Determine final status
            if stats.failed_sentences == 0:
                status = TranslationStatus.SUCCESS
            elif stats.translated_sentences > 0:
                status = TranslationStatus.PARTIAL
            else:
                status = TranslationStatus.FAILURE

            logger.info(
                f"Translation completed: {stats.translated_sentences}/{stats.total_sentences} "
                f"sentences in {stats.elapsed_seconds:.2f}s"
            )

            return TranslationJob(
                translated_content=translated_content,
                status=status,
                stats=stats,
            )

        except Exception as e:
            logger.exception("Translation job failed")
            stats.elapsed_seconds = time.time() - start_time
            return TranslationJob(
                translated_content="",
                status=TranslationStatus.FAILURE,
                stats=stats,
                error=str(e),
            )

    async def _translate_chunk(
        self,
        chunk: TranslationChunk,
        source_language: str,
        target_language: str,
        stats: TranslationStats,
    ) -> list[str]:
        """Translate a single chunk with fallback handling."""
        async with self._semaphore:
            # Try primary service first
            result = await self._primary.translate(
                chunk.sentences,
                source_language,
                target_language,
            )

            if result.success:
                stats.openai_calls += 1
                return result.translated_texts

            # Fall back to secondary service
            logger.warning(
                f"Primary service failed ({result.error}), trying fallback"
            )

            fallback_result = await self._fallback.translate(
                chunk.sentences,
                source_language,
                target_language,
            )

            if fallback_result.success:
                stats.deepl_calls += 1
                return fallback_result.translated_texts

            # Both failed
            logger.error(
                f"All translation services failed. "
                f"Primary: {result.error}, Fallback: {fallback_result.error}"
            )
            raise RuntimeError(
                f"Translation failed: {result.error} / {fallback_result.error}"
            )
