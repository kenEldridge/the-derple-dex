"""NLTK Punkt-based sentence segmenter.

Uses the pre-trained English Punkt model (punkt_tab) rather than
custom training to avoid overfitting to the 19-book corpus.
"""

from __future__ import annotations

import nltk
from nltk.tokenize import sent_tokenize

from .base import Segmenter


# Ensure punkt_tab data is available
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)


class PunktSegmenter(Segmenter):
    """Sentence segmenter using NLTK's pre-trained Punkt model."""

    def __init__(self, language: str = "english"):
        self._language = language

    def segment(self, canonical_text: str) -> list[tuple[int, int]]:
        """Segment canonical text into sentence spans using Punkt."""
        if not canonical_text.strip():
            return []

        # Use NLTK sent_tokenize to get sentence strings
        sentences = sent_tokenize(canonical_text, language=self._language)

        # Map sentence strings back to character spans in the original text
        spans = []
        search_start = 0

        for sent in sentences:
            # Find this sentence in the canonical text
            idx = canonical_text.find(sent, search_start)
            if idx == -1:
                # Fallback: try stripped version
                stripped = sent.strip()
                idx = canonical_text.find(stripped, search_start)
                if idx == -1:
                    continue
                sent = stripped

            spans.append((idx, idx + len(sent)))
            search_start = idx + len(sent)

        return spans
