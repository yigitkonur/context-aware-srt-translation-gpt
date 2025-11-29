"""DeepL translation service as fallback."""

import logging
from typing import Optional

import httpx

from ..config import Settings, get_settings
from .base import TranslationService, TranslationResult

logger = logging.getLogger(__name__)

# DeepL language code mapping (some codes differ from ISO 639-1)
DEEPL_LANGUAGE_MAP = {
    "en": "EN",
    "de": "DE",
    "fr": "FR",
    "es": "ES",
    "it": "IT",
    "nl": "NL",
    "pl": "PL",
    "pt": "PT-PT",
    "pt-br": "PT-BR",
    "ru": "RU",
    "ja": "JA",
    "zh": "ZH",
    "tr": "TR",
}


class DeepLTranslationService(TranslationService):
    """Translation service using DeepL API."""

    API_URL = "https://api-free.deepl.com/v2/translate"
    API_URL_PRO = "https://api.deepl.com/v2/translate"

    def __init__(
        self,
        settings: Optional[Settings] = None,
        use_pro: bool = False,
    ):
        self._settings = settings or get_settings()
        self._api_key = self._settings.deepl_api_key
        self._base_url = self.API_URL_PRO if use_pro else self.API_URL

    @property
    def name(self) -> str:
        return "deepl"

    def _get_language_code(self, code: str) -> str:
        """Convert language code to DeepL format."""
        return DEEPL_LANGUAGE_MAP.get(code.lower(), code.upper())

    async def translate(
        self,
        texts: list[str],
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        """Translate texts using DeepL."""
        if not texts:
            return TranslationResult(
                translated_texts=[],
                success=True,
                service_used=self.name,
            )

        if not self._api_key:
            return TranslationResult(
                translated_texts=[""] * len(texts),
                success=False,
                error="DeepL API key not configured",
                service_used=self.name,
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._base_url,
                    headers={"Authorization": f"DeepL-Auth-Key {self._api_key}"},
                    data={
                        "text": texts,
                        "source_lang": self._get_language_code(source_language),
                        "target_lang": self._get_language_code(target_language),
                    },
                    timeout=30.0,
                )
                response.raise_for_status()

                data = response.json()
                translated = [t["text"] for t in data.get("translations", [])]

                # Ensure we have the right number of translations
                while len(translated) < len(texts):
                    translated.append("")

                logger.debug(f"DeepL translated {len(texts)} texts successfully")

                return TranslationResult(
                    translated_texts=translated[:len(texts)],
                    success=True,
                    service_used=self.name,
                )

        except httpx.HTTPStatusError as e:
            error_msg = f"DeepL API error: {e.response.status_code}"
            logger.error(error_msg)
            return TranslationResult(
                translated_texts=[""] * len(texts),
                success=False,
                error=error_msg,
                service_used=self.name,
            )
        except Exception as e:
            logger.error(f"DeepL translation failed: {e}")
            return TranslationResult(
                translated_texts=[""] * len(texts),
                success=False,
                error=str(e),
                service_used=self.name,
            )

    async def health_check(self) -> bool:
        """Verify DeepL API is accessible."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api-free.deepl.com/v2/usage",
                    headers={"Authorization": f"DeepL-Auth-Key {self._api_key}"},
                    timeout=10.0,
                )
                return response.status_code == 200
        except Exception:
            return False
