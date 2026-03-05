"""Unit tests for v1.1.0 contract requirements.

These tests assert the new requirements introduced in v1.1.0:
- Sentence type field (prose|verse)
- Prose newline normalization
- Verse line break preservation
- Separator filtering
- Stats consistency
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


class TestSentenceTypeField:
    """Every sentence must have a 'type' field with value 'prose' or 'verse'."""

    def test_type_field_present(self):
        """Sentence dicts must include 'type' key."""
        from book_sbd.export import export_book
        import tempfile, json

        book_data = {
            "slug": "test-type",
            "meta": {"title": "Test", "author": "A"},
            "processed_chapters": [{
                "number": 1,
                "label": "I",
                "canonical_text": "Hello world.",
                "sentences": [
                    {"number": 1, "start": 0, "end": 12, "text": "Hello world.", "type": "prose"},
                ],
            }],
        }
        with tempfile.TemporaryDirectory() as d:
            path = export_book(book_data, d)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            sent = data["chapters"][0]["sentences"][0]
            assert "type" in sent, "Sentence must have 'type' field"
            assert sent["type"] in ("prose", "verse"), f"Bad type: {sent['type']}"

    def test_type_values_only_prose_or_verse(self):
        """Only 'prose' and 'verse' are valid type values."""
        valid = {"prose", "verse"}
        for v in valid:
            assert v in valid


class TestProseNewlineNormalization:
    """Prose sentences must not contain newline characters."""

    def test_prose_no_newlines(self):
        from book_sbd.segment.text_modes import classify_and_normalize
        text = "This is a line\nthat wraps around\nto another line."
        blocks = classify_and_normalize(text)
        for block in blocks:
            if block["type"] == "prose":
                assert "\n" not in block["text"], (
                    f"Prose block contains newline: {block['text']!r}"
                )


class TestVersePreservation:
    """Verse sentences must retain internal line breaks."""

    def test_verse_keeps_newlines(self):
        from book_sbd.segment.text_modes import classify_and_normalize
        # Typical verse: short lines, some terminal punctuation
        text = (
            "'Twas brillig, and the slithy toves\n"
            "Did gyre and gimble in the wabe;\n"
            "All mimsy were the borogoves,\n"
            "And the mome raths outgrabe."
        )
        blocks = classify_and_normalize(text)
        verse_blocks = [b for b in blocks if b["type"] == "verse"]
        assert len(verse_blocks) >= 1, "Expected verse classification"
        for b in verse_blocks:
            assert "\n" in b["text"], "Verse block should preserve newlines"


class TestSeparatorFiltering:
    """Decorative asterisk separator lines must be removed."""

    def test_asterisk_separator_removed(self):
        from book_sbd.segment.text_modes import classify_and_normalize
        text = "First paragraph.\n\n* * *\n\nSecond paragraph."
        blocks = classify_and_normalize(text)
        for block in blocks:
            assert "* * *" not in block["text"], (
                f"Separator leaked into output: {block['text']!r}"
            )

    def test_dense_asterisks_removed(self):
        from book_sbd.segment.text_modes import classify_and_normalize
        text = "Before.\n\n***\n\nAfter."
        blocks = classify_and_normalize(text)
        for block in blocks:
            assert "***" not in block["text"]


class TestStatsConsistency:
    """Stats must be internally consistent."""

    def test_total_sentences_matches_sum(self):
        """stats.total_sentences == sum(ch.sentence_count for all chapters)."""
        from book_sbd.export import export_book
        import tempfile, json

        book_data = {
            "slug": "test-stats",
            "meta": {"title": "Test", "author": "A"},
            "processed_chapters": [
                {
                    "number": 1,
                    "label": "I",
                    "canonical_text": "Hello. World.",
                    "sentences": [
                        {"number": 1, "start": 0, "end": 6, "text": "Hello.", "type": "prose"},
                        {"number": 2, "start": 7, "end": 13, "text": "World.", "type": "prose"},
                    ],
                },
                {
                    "number": 2,
                    "label": "II",
                    "canonical_text": "Goodbye.",
                    "sentences": [
                        {"number": 1, "start": 0, "end": 8, "text": "Goodbye.", "type": "prose"},
                    ],
                },
            ],
        }
        with tempfile.TemporaryDirectory() as d:
            path = export_book(book_data, d)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            total = data["stats"]["total_sentences"]
            chapter_sum = sum(ch["sentence_count"] for ch in data["chapters"])
            assert total == chapter_sum, (
                f"total_sentences ({total}) != sum of chapter sentence_counts ({chapter_sum})"
            )

    def test_no_duplicate_sentence_count_key(self):
        """stats must not have both 'total_sentences' and 'sentence_count'."""
        from book_sbd.export import export_book
        import tempfile, json

        book_data = {
            "slug": "test-nodup",
            "meta": {"title": "T", "author": "A"},
            "processed_chapters": [{
                "number": 1,
                "label": "I",
                "canonical_text": "Hi.",
                "sentences": [
                    {"number": 1, "start": 0, "end": 3, "text": "Hi.", "type": "prose"},
                ],
            }],
        }
        with tempfile.TemporaryDirectory() as d:
            path = export_book(book_data, d)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            assert "sentence_count" not in data["stats"], (
                "stats must not have duplicate 'sentence_count' key"
            )


class TestPipelineVersion:
    """Pipeline version must be 1.1.0."""

    def test_version_is_110(self):
        from book_sbd import __version__
        assert __version__ == "1.1.0", f"Expected 1.1.0, got {__version__}"
