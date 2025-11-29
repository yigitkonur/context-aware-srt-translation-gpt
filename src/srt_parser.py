"""SRT file parsing and reconstruction utilities."""

import re
from dataclasses import dataclass
from typing import Iterator

from .models import SubtitleEntry, TranslationChunk


@dataclass
class ParsedSubtitle:
    """Parsed SRT subtitle with metadata for reconstruction."""

    entries: list[SubtitleEntry]
    sentence_map: list[tuple[int, int]]  # (entry_index, line_index) for each sentence

    @property
    def sentences(self) -> list[str]:
        """Get flat list of all sentences."""
        result = []
        for entry in self.entries:
            result.extend(entry.text.split("\n"))
        return result


class SRTParser:
    """Parser for SRT subtitle files."""

    # Regex pattern for SRT timestamp
    TIMESTAMP_PATTERN = re.compile(
        r"(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})"
    )

    def parse(self, content: str) -> ParsedSubtitle:
        """
        Parse SRT content into structured subtitle entries.

        Args:
            content: Raw SRT file content

        Returns:
            ParsedSubtitle with entries and sentence mapping
        """
        entries = []
        sentence_map = []

        # Normalize line endings and split into blocks
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        blocks = re.split(r"\n\n+", content.strip())

        for block in blocks:
            entry = self._parse_block(block)
            if entry:
                entry_index = len(entries)
                entries.append(entry)

                # Map each line in the subtitle to its entry
                lines = entry.text.split("\n")
                for line_index in range(len(lines)):
                    sentence_map.append((entry_index, line_index))

        return ParsedSubtitle(entries=entries, sentence_map=sentence_map)

    def _parse_block(self, block: str) -> SubtitleEntry | None:
        """Parse a single subtitle block."""
        lines = block.strip().split("\n")
        if len(lines) < 3:
            return None

        # First line should be the index
        try:
            index = int(lines[0].strip())
        except ValueError:
            return None

        # Second line should be the timestamp
        timestamp_match = self.TIMESTAMP_PATTERN.match(lines[1].strip())
        if not timestamp_match:
            return None

        start_time = timestamp_match.group(1)
        end_time = timestamp_match.group(2)

        # Remaining lines are the text
        text = "\n".join(lines[2:]).strip()

        return SubtitleEntry(
            index=index,
            start_time=start_time,
            end_time=end_time,
            text=text,
        )

    def reconstruct(
        self,
        parsed: ParsedSubtitle,
        translated_sentences: list[str],
    ) -> str:
        """
        Reconstruct SRT content with translated sentences.

        Args:
            parsed: Original parsed subtitle
            translated_sentences: List of translated sentences matching sentence_map

        Returns:
            Reconstructed SRT content
        """
        # Group translated sentences back to entries
        entry_texts: dict[int, list[str]] = {}

        for i, (entry_idx, _) in enumerate(parsed.sentence_map):
            if i < len(translated_sentences):
                if entry_idx not in entry_texts:
                    entry_texts[entry_idx] = []
                entry_texts[entry_idx].append(translated_sentences[i])

        # Build output
        output_blocks = []
        for i, entry in enumerate(parsed.entries):
            if i in entry_texts:
                translated_text = "\n".join(entry_texts[i])
            else:
                translated_text = entry.text  # Keep original if no translation

            block = f"{entry.index}\n{entry.timestamp}\n{translated_text}"
            output_blocks.append(block)

        return "\n\n".join(output_blocks)


def create_chunks(
    sentences: list[str],
    chunk_size: int = 3,
) -> Iterator[TranslationChunk]:
    """Create translation chunks from sentences."""
    for i in range(0, len(sentences), chunk_size):
        yield TranslationChunk(sentences=sentences[i : i + chunk_size])
