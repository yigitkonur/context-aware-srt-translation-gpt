"""Tests for the FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.main import app
from src.models import TranslationStatus
from src.translator import TranslationJob, TranslationStats


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns ok."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestTranslateEndpoint:
    """Tests for translation endpoint."""

    @patch("src.main.translator")
    def test_translate_success(self, mock_translator, client):
        """Test successful translation."""
        mock_job = TranslationJob(
            translated_content="1\n00:00:01,000 --> 00:00:04,000\nMerhaba",
            status=TranslationStatus.SUCCESS,
            stats=TranslationStats(
                total_sentences=1,
                translated_sentences=1,
                openai_calls=1,
                elapsed_seconds=1.0,
            ),
        )
        mock_translator.translate = AsyncMock(return_value=mock_job)

        response = client.post(
            "/subtitle-translate",
            json={
                "srt_content": "1\n00:00:01,000 --> 00:00:04,000\nHello",
                "source_language": "en",
                "target_language": "tr",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Merhaba" in data["translated_srt_content"]

    def test_translate_invalid_request(self, client):
        """Test validation error for invalid request."""
        response = client.post(
            "/subtitle-translate",
            json={
                "srt_content": "",  # Empty content should fail
                "source_language": "en",
                "target_language": "tr",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_translate_missing_fields(self, client):
        """Test error when required fields are missing."""
        response = client.post(
            "/subtitle-translate",
            json={"srt_content": "test"},  # Missing language fields
        )

        assert response.status_code == 422
