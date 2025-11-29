"""Base translation service interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class TranslationResult:
    """Result of a translation operation."""

    translated_texts: list[str]
    success: bool
    error: Optional[str] = None
    service_used: str = "unknown"


class TranslationService(ABC):
    """Abstract base class for translation services."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Service name identifier."""
        pass

    @abstractmethod
    async def translate(
        self,
        texts: list[str],
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        """
        Translate a list of texts.

        Args:
            texts: List of texts to translate
            source_language: Source language code
            target_language: Target language code

        Returns:
            TranslationResult with translated texts
        """
        pass

    async def health_check(self) -> bool:
        """Check if service is available."""
        return True
