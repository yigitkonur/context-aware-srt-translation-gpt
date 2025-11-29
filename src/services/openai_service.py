"""OpenAI translation service with context-aware prompting."""

import logging
from typing import Optional

from openai import AsyncOpenAI

from ..config import Settings, get_settings
from .base import TranslationService, TranslationResult

logger = logging.getLogger(__name__)


class OpenAITranslationService(TranslationService):
    """Translation service using OpenAI's chat models."""

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._client = AsyncOpenAI(api_key=self._settings.openai_api_key)

    @property
    def name(self) -> str:
        return "openai"

    def _build_system_prompt(
        self,
        source_language: str,
        target_language: str,
        num_lines: int,
    ) -> str:
        """Build the system prompt for translation."""
        line_refs = ", ".join([f"{i+1})" for i in range(num_lines)])

        return f"""You are a professional subtitle translator. Translate the following lines from {source_language} to {target_language}.

CRITICAL RULES:
1. Output EXACTLY {num_lines} lines, numbered {line_refs}
2. Preserve the meaning while making it natural in {target_language}
3. Keep sentences concise - subtitles need to be readable quickly
4. Maintain the speaker's tone and intent
5. Consider context between lines - they are sequential subtitles
6. Never add explanations or notes - only output translations

INPUT FORMAT:
{line_refs}

OUTPUT FORMAT (must match exactly):
{line_refs}

Translate now:"""

    def _build_user_prompt(self, texts: list[str]) -> str:
        """Build the user prompt with numbered texts."""
        return "\n".join([f"{i+1}) {text}" for i, text in enumerate(texts)])

    def _parse_response(self, response_text: str, expected_count: int) -> list[str]:
        """Parse the response and extract translations."""
        lines = response_text.strip().split("\n")
        results = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to extract text after the number prefix
            # Handle formats like "1) text", "1. text", "1: text"
            for sep in [") ", ". ", ": ", ")"]:
                if sep in line:
                    parts = line.split(sep, 1)
                    if parts[0].strip().isdigit() and len(parts) > 1:
                        results.append(parts[1].strip())
                        break
            else:
                # No number prefix found, use the line as-is
                results.append(line)

        # Ensure we have exactly the expected count
        while len(results) < expected_count:
            results.append("")

        return results[:expected_count]

    async def translate(
        self,
        texts: list[str],
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        """Translate texts using OpenAI."""
        if not texts:
            return TranslationResult(
                translated_texts=[],
                success=True,
                service_used=self.name,
            )

        try:
            system_prompt = self._build_system_prompt(
                source_language, target_language, len(texts)
            )
            user_prompt = self._build_user_prompt(texts)

            response = await self._client.chat.completions.create(
                model=self._settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self._settings.openai_temperature,
                max_tokens=self._settings.openai_max_tokens,
            )

            response_text = response.choices[0].message.content or ""
            translated = self._parse_response(response_text, len(texts))

            logger.debug(f"OpenAI translated {len(texts)} texts successfully")

            return TranslationResult(
                translated_texts=translated,
                success=True,
                service_used=self.name,
            )

        except Exception as e:
            logger.error(f"OpenAI translation failed: {e}")
            return TranslationResult(
                translated_texts=[""] * len(texts),
                success=False,
                error=str(e),
                service_used=self.name,
            )

    async def health_check(self) -> bool:
        """Verify OpenAI API is accessible."""
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False
