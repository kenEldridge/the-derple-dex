"""Tests for canonicalization rules."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from book_sbd.canonicalize import canonicalize


def test_normalize_newlines():
    assert canonicalize("a\r\nb\rc") == "a\nb\nc"


def test_remove_bom():
    assert canonicalize("\ufeffHello") == "Hello"


def test_unicode_nfc():
    # e + combining acute = é in NFC
    import unicodedata
    decomposed = "e\u0301"
    result = canonicalize(decomposed)
    assert result == "\u00e9"
    assert unicodedata.is_normalized("NFC", result)


def test_trim_trailing_whitespace():
    assert canonicalize("hello   \nworld  ") == "hello\nworld"


def test_collapse_internal_spaces():
    assert canonicalize("hello   world") == "hello world"


def test_collapse_tabs():
    assert canonicalize("hello\t\tworld") == "hello world"


def test_normalize_blank_lines():
    text = "para1\n\n\n\n\npara2"
    result = canonicalize(text)
    assert result == "para1\n\npara2"


def test_strip_overall():
    assert canonicalize("  \n\nhello\n\n  ") == "hello"


def test_idempotence():
    """canon(canon(x)) == canon(x)"""
    samples = [
        "Hello  world.\r\n\r\nNew   paragraph.\r\n",
        "\ufeffBOM  text\t\there  \n\n\n\nGap",
        "  Leading and trailing  \n  spaces  ",
        "Already\ncanonical\n\ntext.",
    ]
    for s in samples:
        first = canonicalize(s)
        second = canonicalize(first)
        assert first == second, f"Not idempotent for: {s!r}"


def test_preserve_paragraph_breaks():
    """Double newlines (paragraph breaks) are preserved."""
    text = "Paragraph one.\n\nParagraph two."
    result = canonicalize(text)
    assert result == "Paragraph one.\n\nParagraph two."
