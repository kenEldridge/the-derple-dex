"""Tests for boilerplate detection and stripping."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from book_sbd.ingest.boilerplate import is_boilerplate_spine_doc, strip_gutenberg_text


def test_boilerplate_detection_pg_header():
    content = """<html><body>
    <h2>The Project Gutenberg eBook of Test</h2>
    <p>www.gutenberg.org</p>
    </body></html>"""
    assert is_boilerplate_spine_doc(content) is True


def test_boilerplate_detection_license():
    content = """<html><body>
    <h2>THE FULL PROJECT GUTENBERG LICENSE</h2>
    <p>Some license text here.</p>
    </body></html>"""
    assert is_boilerplate_spine_doc(content) is True


def test_boilerplate_detection_normal_content():
    content = """<html><body>
    <h2>Chapter I</h2>
    <p>It was a dark and stormy night.</p>
    </body></html>"""
    assert is_boilerplate_spine_doc(content) is False


def test_strip_gutenberg_text():
    text = """Some header text
*** START OF THE PROJECT GUTENBERG EBOOK TEST ***
Actual content here.
More content.
*** END OF THE PROJECT GUTENBERG EBOOK TEST ***
License footer text."""
    result = strip_gutenberg_text(text)
    assert "Actual content here." in result
    assert "More content." in result
    assert "Some header text" not in result
    assert "License footer text" not in result


def test_strip_gutenberg_no_markers():
    text = "Regular text without markers."
    result = strip_gutenberg_text(text)
    assert result == text
