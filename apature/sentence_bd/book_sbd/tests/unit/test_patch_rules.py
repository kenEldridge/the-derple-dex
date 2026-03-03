"""Tests for patch rules: positive fix, negative control, edge case per rule."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from book_sbd.segment.patch_rules import (
    apply_patch_rules,
    _merge_abbreviation_splits,
    _merge_closing_quotes,
    _merge_ellipsis_splits,
)


class TestAbbreviationRule:
    """Merge splits after abbreviations like Mr., Mrs., Dr."""

    def test_positive_fix(self):
        # "etc." followed by lowercase continuation — should merge
        text = "Items etc. and more things here."
        # Split: "Items etc." + "and more things here."
        spans = [(0, 10), (11, 31)]
        result = _merge_abbreviation_splits(text, spans)
        assert len(result) == 1
        assert result[0] == (0, 31)

    def test_negative_control(self):
        """Don't merge when next sentence starts with uppercase (real boundary)."""
        text = "He left early. She stayed late."
        spans = [(0, 14), (15, 31)]
        result = _merge_abbreviation_splits(text, spans)
        assert len(result) == 2

    def test_edge_case_end_of_text(self):
        text = "Just Dr."
        spans = [(0, 8)]
        result = _merge_abbreviation_splits(text, spans)
        assert len(result) == 1


class TestClosingQuoteRule:
    """Merge orphaned closing quotes/brackets."""

    def test_positive_fix(self):
        text = 'She said, "Hello." "'
        spans = [(0, 18), (19, 20)]  # Orphaned closing quote
        result = _merge_closing_quotes(text, spans)
        assert len(result) == 1

    def test_negative_control(self):
        """Don't merge a real short sentence."""
        text = "He ran. No! She screamed."
        spans = [(0, 7), (8, 11), (12, 25)]
        result = _merge_closing_quotes(text, spans)
        # "No!" is 3 chars but contains a letter, not just punctuation
        assert len(result) == 3

    def test_edge_case_only_punctuation(self):
        text = 'He said something). End.'
        spans = [(0, 18), (18, 20), (21, 25)]
        result = _merge_closing_quotes(text, spans)
        # ")." merges into previous sentence
        assert len(result) == 2
        assert result[0] == (0, 20)


class TestEllipsisRule:
    """Merge splits at ellipsis when continuation follows."""

    def test_positive_fix(self):
        text = "He thought... and then decided."
        spans = [(0, 13), (14, 31)]  # "He thought..." + "and then decided."
        result = _merge_ellipsis_splits(text, spans)
        assert len(result) == 1

    def test_negative_control(self):
        """Don't merge when next starts with uppercase (new sentence)."""
        text = "He stopped... The next day arrived."
        spans = [(0, 13), (14, 35)]
        result = _merge_ellipsis_splits(text, spans)
        assert len(result) == 2

    def test_edge_case_unicode_ellipsis(self):
        text = "He thought\u2026 and then decided."
        spans = [(0, 11), (12, 30)]
        result = _merge_ellipsis_splits(text, spans)
        assert len(result) == 1


class TestApplyAll:
    """Integration: all patch rules applied together."""

    def test_combined_rules(self):
        text = 'Mr. smith said "hello..." and left.'
        # Baseline might split at "Mr." and "hello..."
        spans = [(0, 3), (4, 28), (29, 35)]
        result = apply_patch_rules(text, spans)
        # Should merge Mr. split (lowercase follows) and ... split (lowercase follows)
        assert len(result) <= 2

    def test_no_change_needed(self):
        text = "Hello world. Goodbye world."
        spans = [(0, 12), (13, 27)]
        result = apply_patch_rules(text, spans)
        assert result == spans
