"""Chapter and sentence numbering.

Ensures contiguous 1..N chapter numbers and 1..M sentence numbers per chapter.
"""

from __future__ import annotations


def number_chapters(chapters: list[dict]) -> list[dict]:
    """Assign contiguous chapter numbers 1..N."""
    for i, ch in enumerate(chapters):
        ch["number"] = i + 1
    return chapters


def number_sentences(sentences: list[dict]) -> list[dict]:
    """Assign contiguous sentence numbers 1..M within a chapter."""
    for i, s in enumerate(sentences):
        s["number"] = i + 1
    return sentences
