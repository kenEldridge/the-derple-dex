"""Tests for patch rules: positive fix, negative control, edge case per rule."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from book_sbd.segment.patch_rules import (
    apply_patch_rules,
    _merge_abbreviation_splits,
    _merge_closing_quotes,
    _merge_ellipsis_splits,
    _merge_exclamation_continuations,
    _merge_quoted_discourse,
    _consolidate_short_verse_blocks,
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


class TestExclamationRule:
    """Merge mid-sentence exclamation splits with lowercase continuation."""

    def test_positive_onomatopoeia(self):
        """'thump!' + lowercase continuation should merge."""
        text = "thump! down she came upon a heap of sticks."
        spans = [(0, 6), (7, 44)]
        result = _merge_exclamation_continuations(text, spans)
        assert len(result) == 1
        assert result[0] == (0, 44)

    def test_positive_splash(self):
        """'splash!' + lowercase continuation should merge."""
        text = "and in another moment, splash! she was up to her chin."
        spans = [(0, 30), (31, 54)]
        result = _merge_exclamation_continuations(text, spans)
        assert len(result) == 1

    def test_positive_alas(self):
        """'Alas!' + lowercase continuation should merge."""
        text = "Alas! it was too late to wish that!"
        spans = [(0, 5), (6, 34)]
        result = _merge_exclamation_continuations(text, spans)
        assert len(result) == 1

    def test_negative_uppercase_continuation(self):
        """Don't merge when next sentence starts with uppercase."""
        text = "Stop! The train is coming."
        spans = [(0, 5), (6, 25)]
        result = _merge_exclamation_continuations(text, spans)
        assert len(result) == 2

    def test_negative_real_sentence_boundary(self):
        """Don't merge two independent sentences."""
        text = "She screamed! He ran away."
        spans = [(0, 13), (14, 25)]
        result = _merge_exclamation_continuations(text, spans)
        assert len(result) == 2

    def test_edge_case_single_span(self):
        text = "Help!"
        spans = [(0, 5)]
        result = _merge_exclamation_continuations(text, spans)
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


class TestQuotedDiscourseRule:
    """Merge splits inside continuous quoted speech/thought."""

    def test_positive_exclamation_in_quote(self):
        """Exclamation inside open quote should merge."""
        # \u201c = " and \u201d = "
        text = "the Rabbit said, \u201cOh dear! Oh dear! I shall be late!\u201d"
        # Punkt splits at each "!"
        spans = [(0, 27), (28, 37), (38, 55)]
        result = _merge_quoted_discourse(text, spans)
        assert len(result) == 1
        assert result[0] == (0, 55)

    def test_positive_question_in_quote(self):
        """Question inside open quote should merge."""
        text = "Alice thought, \u201cWhere am I? What is this place?\u201d"
        spans = [(0, 25), (26, 49)]
        result = _merge_quoted_discourse(text, spans)
        assert len(result) == 1

    def test_negative_separate_sentences_no_quote(self):
        """Normal sentences outside quotes should not merge."""
        text = "She ran away. He stayed behind."
        spans = [(0, 13), (14, 31)]
        result = _merge_quoted_discourse(text, spans)
        assert len(result) == 2

    def test_negative_paragraph_break(self):
        """Never merge across paragraph breaks, even inside a quote."""
        text = "\u201cFirst paragraph.\n\nSecond paragraph.\u201d"
        # "First paragraph." ends at pos 17, \n\n at 17-18, "Second" at 19
        spans = [(0, 17), (19, 37)]
        result = _merge_quoted_discourse(text, spans)
        assert len(result) == 2

    def test_negative_verse_not_merged(self):
        """Verse spans should not be merged even if inside a quote."""
        text = "\u201cHow doth the crocodile! Improve his shining tail!\u201d"
        spans = [(0, 23), (24, 52)]
        block_meta = [{"type": "verse", "start": 0, "end": 52}]
        result = _merge_quoted_discourse(text, spans, block_meta)
        assert len(result) == 2

    def test_closed_quote_not_merged(self):
        """If quote is closed (depth 0), don't merge."""
        text = "\u201cHello.\u201d She left."
        spans = [(0, 9), (10, 19)]
        result = _merge_quoted_discourse(text, spans)
        assert len(result) == 2

    def test_chained_merges(self):
        """Multiple consecutive fragments inside one quote should all merge."""
        text = "She said, \u201cOne! Two! Three! Four!\u201d"
        spans = [(0, 15), (16, 20), (21, 27), (28, 34)]
        result = _merge_quoted_discourse(text, spans)
        assert len(result) == 1

    def test_nested_quotes(self):
        """Inner quote within outer quote should still merge."""
        text = "Alice said, \u201cHe told me \u2018Go away!\u2019 How rude!\u201d"
        spans = [(0, 34), (35, 47)]
        result = _merge_quoted_discourse(text, spans)
        assert len(result) == 1


class TestShortVerseConsolidation:
    """Short verse blocks (<=8 lines) become single sentences."""

    def test_positive_short_stanza(self):
        """A 4-line verse block with 2 sentence spans should consolidate."""
        text = "Twinkle, twinkle, little bat!\nHow I wonder what you\u2019re at!\nUp above the world you fly,\nLike a tea-tray in the sky."
        # Punkt might split at "!" boundary
        spans = [(0, 58), (59, 112)]
        block_meta = [{"type": "verse", "start": 0, "end": 112}]
        result = _consolidate_short_verse_blocks(text, spans, block_meta)
        assert len(result) == 1
        assert result[0] == (0, 112)

    def test_negative_long_canto(self):
        """A verse block with >8 lines should keep internal boundaries."""
        # Simulate a 10-line verse block
        lines = [f"Line {i} of the epic poem here." for i in range(10)]
        text = "\n".join(lines)
        # Two sentence spans within it
        mid = text.index("\n", len(text) // 2)
        spans = [(0, mid), (mid + 1, len(text))]
        block_meta = [{"type": "verse", "start": 0, "end": len(text)}]
        result = _consolidate_short_verse_blocks(text, spans, block_meta)
        assert len(result) == 2

    def test_mixed_prose_and_verse(self):
        """Prose spans before/after a short verse block are untouched."""
        text = "She began to sing.\nTwinkle twinkle!\nLittle bat!\nThen she stopped."
        # Prose span, then 2 verse spans, then prose span
        spans = [(0, 18), (19, 35), (36, 47), (48, 64)]
        block_meta = [
            {"type": "prose", "start": 0, "end": 18},
            {"type": "verse", "start": 19, "end": 47},
            {"type": "prose", "start": 48, "end": 64},
        ]
        result = _consolidate_short_verse_blocks(text, spans, block_meta)
        assert len(result) == 3
        assert result[0] == (0, 18)    # prose unchanged
        assert result[1] == (19, 47)   # verse consolidated
        assert result[2] == (48, 64)   # prose unchanged

    def test_no_metadata(self):
        """Without block metadata, spans are returned unchanged."""
        text = "Hello! World!"
        spans = [(0, 6), (7, 13)]
        result = _consolidate_short_verse_blocks(text, spans, None)
        assert result == spans

    def test_single_sentence_verse_unchanged(self):
        """A verse block with only 1 sentence span needs no consolidation."""
        text = "A single verse line."
        spans = [(0, 20)]
        block_meta = [{"type": "verse", "start": 0, "end": 20}]
        result = _consolidate_short_verse_blocks(text, spans, block_meta)
        assert len(result) == 1
