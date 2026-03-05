"""Tests for invariant helpers."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from book_sbd.invariants import (
    check_chapter_numbers_contiguous,
    check_sentence_numbers_contiguous,
    check_spans_sorted_non_overlapping,
    check_text_matches_slice,
    check_no_empty_sentences,
    check_sentence_types,
    check_prose_no_newlines,
    check_no_separator_sentences,
    check_coverage,
    validate_book,
)


def test_chapter_numbers_contiguous_pass():
    chapters = [{"number": 1}, {"number": 2}, {"number": 3}]
    assert check_chapter_numbers_contiguous(chapters) == []


def test_chapter_numbers_contiguous_gap():
    chapters = [{"number": 1}, {"number": 3}]
    errors = check_chapter_numbers_contiguous(chapters)
    assert len(errors) == 1
    assert "expected 2" in errors[0]


def test_chapter_numbers_empty():
    assert len(check_chapter_numbers_contiguous([])) == 1


def test_sentence_numbers_contiguous_pass():
    ch = {"number": 1, "sentences": [{"number": 1}, {"number": 2}]}
    assert check_sentence_numbers_contiguous(ch) == []


def test_sentence_numbers_contiguous_gap():
    ch = {"number": 1, "sentences": [{"number": 1}, {"number": 5}]}
    errors = check_sentence_numbers_contiguous(ch)
    assert len(errors) == 1


def test_spans_sorted_pass():
    ch = {
        "number": 1,
        "sentences": [
            {"number": 1, "start": 0, "end": 10},
            {"number": 2, "start": 11, "end": 20},
        ],
    }
    assert check_spans_sorted_non_overlapping(ch) == []


def test_spans_overlap():
    ch = {
        "number": 1,
        "sentences": [
            {"number": 1, "start": 0, "end": 10},
            {"number": 2, "start": 5, "end": 15},
        ],
    }
    errors = check_spans_sorted_non_overlapping(ch)
    assert len(errors) == 1
    assert "overlap" in errors[0]


def test_text_matches_slice_pass():
    text = "Hello world. Goodbye world."
    ch = {
        "number": 1,
        "sentences": [
            {"number": 1, "start": 0, "end": 12, "text": "Hello world."},
            {"number": 2, "start": 13, "end": 27, "text": "Goodbye world."},
        ],
    }
    assert check_text_matches_slice(ch, text) == []


def test_text_matches_slice_mismatch():
    text = "Hello world."
    ch = {
        "number": 1,
        "sentences": [{"number": 1, "start": 0, "end": 5, "text": "WRONG"}],
    }
    errors = check_text_matches_slice(ch, text)
    assert len(errors) == 1


def test_no_empty_sentences_pass():
    ch = {"number": 1, "sentences": [{"number": 1, "text": "Hello."}]}
    assert check_no_empty_sentences(ch) == []


def test_no_empty_sentences_fail():
    ch = {"number": 1, "sentences": [{"number": 1, "text": "  "}]}
    errors = check_no_empty_sentences(ch)
    assert len(errors) == 1


def test_validate_book_full_pass():
    book = {
        "chapters": [
            {
                "number": 1,
                "sentences": [
                    {"number": 1, "text": "Hello.", "start": 0, "end": 6, "type": "prose"},
                    {"number": 2, "text": "World.", "start": 7, "end": 13, "type": "prose"},
                ],
            }
        ]
    }
    canonical = {1: "Hello. World."}
    assert validate_book(book, canonical) == []


# --- v1.1.0 invariant tests ---


def test_sentence_types_pass():
    ch = {"number": 1, "sentences": [
        {"number": 1, "type": "prose"},
        {"number": 2, "type": "verse"},
    ]}
    assert check_sentence_types(ch) == []


def test_sentence_types_missing():
    ch = {"number": 1, "sentences": [{"number": 1}]}
    errors = check_sentence_types(ch)
    assert len(errors) == 1
    assert "missing type" in errors[0]


def test_sentence_types_invalid():
    ch = {"number": 1, "sentences": [{"number": 1, "type": "dialog"}]}
    errors = check_sentence_types(ch)
    assert len(errors) == 1


def test_prose_no_newlines_pass():
    ch = {"number": 1, "sentences": [
        {"number": 1, "type": "prose", "text": "No newlines here."},
    ]}
    assert check_prose_no_newlines(ch) == []


def test_prose_no_newlines_fail():
    ch = {"number": 1, "sentences": [
        {"number": 1, "type": "prose", "text": "Has\nnewline."},
    ]}
    errors = check_prose_no_newlines(ch)
    assert len(errors) == 1


def test_prose_newline_ok_in_verse():
    ch = {"number": 1, "sentences": [
        {"number": 1, "type": "verse", "text": "Line one\nLine two"},
    ]}
    assert check_prose_no_newlines(ch) == []


def test_no_separator_sentences_pass():
    ch = {"number": 1, "sentences": [
        {"number": 1, "text": "Normal text."},
    ]}
    assert check_no_separator_sentences(ch) == []


def test_no_separator_sentences_fail():
    ch = {"number": 1, "sentences": [
        {"number": 1, "text": "* * *"},
    ]}
    errors = check_no_separator_sentences(ch)
    assert len(errors) == 1
    assert "separator" in errors[0]


def test_coverage_pass():
    text = "Hello. World."
    ch = {"number": 1, "sentences": [
        {"number": 1, "start": 0, "end": 6},
        {"number": 2, "start": 7, "end": 13},
    ]}
    assert check_coverage(ch, text) == []


def test_coverage_fail_gap():
    text = "Hello. World."
    ch = {"number": 1, "sentences": [
        {"number": 1, "start": 0, "end": 6},
        # gap: "World." at 7-13 is missing
    ]}
    errors = check_coverage(ch, text)
    assert len(errors) == 1
    assert "uncovered" in errors[0]
