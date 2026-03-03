"""Base interface for sentence segmentation backends."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Segmenter(ABC):
    """Abstract sentence segmenter.

    Implementations must produce character spans (start, end) into
    the canonical text.
    """

    @abstractmethod
    def segment(self, canonical_text: str) -> list[tuple[int, int]]:
        """Segment text into sentence spans.

        Args:
            canonical_text: Canonicalized chapter text.

        Returns:
            List of (start, end) tuples where text[start:end] is each sentence.
            Spans are sorted, non-overlapping, and cover all non-whitespace.
        """
        ...
