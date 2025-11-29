"""Pytest configuration and fixtures."""

import pytest
import os

# Set test environment variables
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("DEEPL_API_KEY", "test-key")
os.environ.setdefault("LOG_LEVEL", "DEBUG")


@pytest.fixture
def sample_srt():
    """Sample SRT content for testing."""
    return """1
00:00:01,000 --> 00:00:04,000
Hello, how are you?

2
00:00:05,000 --> 00:00:08,000
I'm doing great, thank you!

3
00:00:09,000 --> 00:00:12,000
That's wonderful to hear."""


@pytest.fixture
def sample_multiline_srt():
    """Sample SRT with multiline subtitles."""
    return """1
00:00:01,000 --> 00:00:04,000
First line of dialogue
Second line continues

2
00:00:05,000 --> 00:00:08,000
Another subtitle here"""
