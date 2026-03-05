"""NLTK Punkt-based sentence segmenter.

Uses the pre-trained English Punkt model (punkt_tab) rather than
custom training to avoid overfitting to the 19-book corpus.

v1.1.0: Uses span_tokenize() directly instead of brittle str.find() mapping.
"""

from __future__ import annotations

import re

import nltk

from .base import Segmenter


# Ensure punkt_tab data is available
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)

# Load tokenizer once at module level
_tokenizer = nltk.data.load("tokenizers/punkt_tab/english.pickle")

# Pattern for splitting over-merged multi-paragraph spans
_PARA_BREAK_RE = re.compile(r"\n\n+")


class PunktSegmenter(Segmenter):
    """Sentence segmenter using NLTK's pre-trained Punkt model."""

    def __init__(self, language: str = "english"):
        self._language = language

    def segment(self, canonical_text: str) -> list[tuple[int, int]]:
        """Segment canonical text into sentence spans using Punkt.

        Uses span_tokenize() for direct character offsets — no string
        matching fallback needed.
        """
        if not canonical_text.strip():
            return []

        # Get spans directly from Punkt tokenizer
        raw_spans = list(_tokenizer.span_tokenize(canonical_text))

        # Apply conservative split for over-merged multi-paragraph spans
        spans = []
        for start, end in raw_spans:
            segment_text = canonical_text[start:end]
            sub_spans = self._split_paragraphs(segment_text, start)
            spans.extend(sub_spans)

        return spans

    def _split_paragraphs(
        self, text: str, offset: int
    ) -> list[tuple[int, int]]:
        """Split a span that contains paragraph breaks (\\n\\n+).

        Only splits at paragraph boundaries. Each resulting sub-span
        is trimmed of leading/trailing whitespace.
        """
        parts = _PARA_BREAK_RE.split(text)
        if len(parts) <= 1:
            return [(offset, offset + len(text))]

        spans = []
        search_pos = 0
        for part in parts:
            if not part.strip():
                continue
            # Find where this part starts in the original text
            part_start = text.find(part, search_pos)
            if part_start == -1:
                continue
            part_end = part_start + len(part)
            search_pos = part_end
            spans.append((offset + part_start, offset + part_end))

        return spans if spans else [(offset, offset + len(text))]
