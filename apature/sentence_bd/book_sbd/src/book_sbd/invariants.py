"""Invariant checks for chapter units and sentence spans."""

from __future__ import annotations
from typing import Any


def check_chapter_numbers_contiguous(chapters: list[dict]) -> list[str]:
    """Chapter numbers must be 1..N with no gaps."""
    errors = []
    expected = 1
    for ch in chapters:
        n = ch.get("number")
        if n != expected:
            errors.append(f"Chapter number gap: expected {expected}, got {n}")
        expected += 1
    if not chapters:
        errors.append("No chapters found")
    return errors


def check_sentence_numbers_contiguous(chapter: dict) -> list[str]:
    """Sentence numbers within a chapter must be 1..M with no gaps."""
    errors = []
    sentences = chapter.get("sentences", [])
    expected = 1
    for s in sentences:
        n = s.get("number")
        if n != expected:
            errors.append(
                f"Chapter {chapter.get('number')}: sentence number gap: "
                f"expected {expected}, got {n}"
            )
        expected += 1
    return errors


def check_spans_sorted_non_overlapping(chapter: dict) -> list[str]:
    """Spans must be strictly ordered and non-overlapping."""
    errors = []
    sentences = chapter.get("sentences", [])
    prev_end = -1
    for s in sentences:
        start = s.get("start", 0)
        end = s.get("end", 0)
        if start < prev_end:
            errors.append(
                f"Chapter {chapter.get('number')}, sentence {s.get('number')}: "
                f"span overlap: start={start} < prev_end={prev_end}"
            )
        if end <= start:
            errors.append(
                f"Chapter {chapter.get('number')}, sentence {s.get('number')}: "
                f"invalid span: start={start}, end={end}"
            )
        prev_end = end
    return errors


def check_text_matches_slice(chapter: dict, canonical_text: str) -> list[str]:
    """sentence.text must equal canonical_text[start:end]."""
    errors = []
    for s in chapter.get("sentences", []):
        start = s.get("start", 0)
        end = s.get("end", 0)
        expected = canonical_text[start:end]
        if s.get("text") != expected:
            errors.append(
                f"Chapter {chapter.get('number')}, sentence {s.get('number')}: "
                f"text mismatch at [{start}:{end}]"
            )
    return errors


def check_no_empty_sentences(chapter: dict) -> list[str]:
    """No sentence text may be empty or whitespace-only."""
    errors = []
    for s in chapter.get("sentences", []):
        text = s.get("text", "")
        if not text or not text.strip():
            errors.append(
                f"Chapter {chapter.get('number')}, sentence {s.get('number')}: "
                f"empty or whitespace-only sentence"
            )
    return errors


def validate_book(book: dict, canonical_texts: dict[int, str] | None = None) -> list[str]:
    """Run all invariant checks on a full book structure.

    Args:
        book: The book dict with 'chapters' list.
        canonical_texts: Optional mapping of chapter number -> canonical text
            for span/text validation.

    Returns:
        List of error strings. Empty list means all invariants pass.
    """
    errors = []
    chapters = book.get("chapters", [])
    errors.extend(check_chapter_numbers_contiguous(chapters))

    for ch in chapters:
        errors.extend(check_sentence_numbers_contiguous(ch))
        errors.extend(check_no_empty_sentences(ch))

        if canonical_texts and ch.get("number") in canonical_texts:
            ct = canonical_texts[ch["number"]]
            errors.extend(check_spans_sorted_non_overlapping(ch))
            errors.extend(check_text_matches_slice(ch, ct))

    return errors
