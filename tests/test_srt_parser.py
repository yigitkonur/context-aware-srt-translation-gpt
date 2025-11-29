"""Tests for SRT parser."""

import pytest
from src.srt_parser import SRTParser, create_chunks


class TestSRTParser:
    """Tests for the SRTParser class."""

    def setup_method(self):
        self.parser = SRTParser()

    def test_parse_simple_srt(self):
        """Test parsing a simple SRT file."""
        content = """1
00:00:01,000 --> 00:00:04,000
Hello, world!

2
00:00:05,000 --> 00:00:08,000
How are you?"""

        result = self.parser.parse(content)

        assert len(result.entries) == 2
        assert result.entries[0].index == 1
        assert result.entries[0].text == "Hello, world!"
        assert result.entries[0].start_time == "00:00:01,000"
        assert result.entries[0].end_time == "00:00:04,000"

        assert result.entries[1].index == 2
        assert result.entries[1].text == "How are you?"

    def test_parse_multiline_subtitle(self):
        """Test parsing subtitles with multiple lines."""
        content = """1
00:00:01,000 --> 00:00:04,000
First line
Second line

2
00:00:05,000 --> 00:00:08,000
Single line"""

        result = self.parser.parse(content)

        assert len(result.entries) == 2
        assert result.entries[0].text == "First line\nSecond line"
        assert len(result.sentences) == 3

    def test_parse_handles_different_line_endings(self):
        """Test that parser handles different line ending formats."""
        content = "1\r\n00:00:01,000 --> 00:00:04,000\r\nHello\r\n\r\n2\r\n00:00:05,000 --> 00:00:08,000\r\nWorld"

        result = self.parser.parse(content)

        assert len(result.entries) == 2
        assert result.entries[0].text == "Hello"
        assert result.entries[1].text == "World"

    def test_reconstruct_srt(self):
        """Test reconstructing SRT from parsed data and translations."""
        content = """1
00:00:01,000 --> 00:00:04,000
Hello

2
00:00:05,000 --> 00:00:08,000
World"""

        parsed = self.parser.parse(content)
        translated = ["Merhaba", "Dünya"]

        result = self.parser.reconstruct(parsed, translated)

        assert "Merhaba" in result
        assert "Dünya" in result
        assert "00:00:01,000 --> 00:00:04,000" in result

    def test_sentence_map(self):
        """Test that sentence map correctly tracks entries."""
        content = """1
00:00:01,000 --> 00:00:04,000
Line A
Line B

2
00:00:05,000 --> 00:00:08,000
Line C"""

        result = self.parser.parse(content)

        # Should have 3 sentences mapped
        assert len(result.sentence_map) == 3
        assert result.sentence_map[0] == (0, 0)  # "Line A" -> entry 0, line 0
        assert result.sentence_map[1] == (0, 1)  # "Line B" -> entry 0, line 1
        assert result.sentence_map[2] == (1, 0)  # "Line C" -> entry 1, line 0


class TestCreateChunks:
    """Tests for the create_chunks function."""

    def test_create_chunks_exact_fit(self):
        """Test chunking when sentences fit exactly."""
        sentences = ["A", "B", "C", "D", "E", "F"]
        chunks = list(create_chunks(sentences, chunk_size=3))

        assert len(chunks) == 2
        assert chunks[0].sentences == ["A", "B", "C"]
        assert chunks[1].sentences == ["D", "E", "F"]

    def test_create_chunks_with_remainder(self):
        """Test chunking when there's a remainder."""
        sentences = ["A", "B", "C", "D", "E"]
        chunks = list(create_chunks(sentences, chunk_size=3))

        assert len(chunks) == 2
        assert chunks[0].sentences == ["A", "B", "C"]
        assert chunks[1].sentences == ["D", "E"]

    def test_create_chunks_empty_input(self):
        """Test chunking with empty input."""
        sentences = []
        chunks = list(create_chunks(sentences, chunk_size=3))

        assert len(chunks) == 0

    def test_create_chunks_single_item(self):
        """Test chunking with single item."""
        sentences = ["A"]
        chunks = list(create_chunks(sentences, chunk_size=3))

        assert len(chunks) == 1
        assert chunks[0].sentences == ["A"]
