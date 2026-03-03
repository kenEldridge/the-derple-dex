"""Tests for structure extraction."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from book_sbd.ingest.structure import html_to_text, _is_skip_entry, _looks_like_title_entry


def test_html_to_text_basic():
    html = "<p>Hello</p><p>World</p>"
    text = html_to_text(html)
    assert "Hello" in text
    assert "World" in text


def test_html_to_text_strips_scripts():
    html = "<p>Visible</p><script>hidden</script><p>Also visible</p>"
    text = html_to_text(html)
    assert "Visible" in text
    assert "hidden" not in text
    assert "Also visible" in text


def test_html_to_text_br():
    html = "Line one<br/>Line two"
    text = html_to_text(html)
    assert "Line one" in text
    assert "Line two" in text
    # br produces at least one newline between them
    assert text.index("Line two") > text.index("Line one")


def test_skip_entry_contents():
    assert _is_skip_entry("Contents") is True
    assert _is_skip_entry("TABLE OF CONTENTS") is True


def test_skip_entry_gutenberg():
    assert _is_skip_entry("THE FULL PROJECT GUTENBERG LICENSE") is True


def test_skip_entry_normal():
    assert _is_skip_entry("CHAPTER I") is False
    assert _is_skip_entry("The Golden Bird") is False


def test_skip_entry_footnotes():
    assert _is_skip_entry("Footnotes:") is True
    assert _is_skip_entry("FOOTNOTES") is True


def test_looks_like_title_entry():
    assert _looks_like_title_entry("Pride and Prejudice") is True
    assert _looks_like_title_entry("CHAPTER I") is False
    assert _looks_like_title_entry("Book I") is False
    assert _looks_like_title_entry("I. A SCANDAL IN BOHEMIA") is False
