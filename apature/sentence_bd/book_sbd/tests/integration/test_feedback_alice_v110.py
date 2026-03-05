"""Integration test: Alice v1.1.0 feedback requirements.

Validates that the pipeline output for Alice's Adventures in Wonderland
meets the v1.1.0 contract when run end-to-end.
"""

import sys, os, json, glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

EPUB_DIR = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "epubs_unpacked", "epubs"
))

ALICE_SLUG = "alices-adventures-in-wonderland"


def _find_alice():
    epub = os.path.join(EPUB_DIR, f"{ALICE_SLUG}.epub")
    meta = os.path.join(EPUB_DIR, f"{ALICE_SLUG}_meta.json")
    if os.path.exists(epub) and os.path.exists(meta):
        return epub, meta
    return None, None


@pytest.fixture(scope="module")
def alice_output():
    """Run the full pipeline on Alice and return the output dict."""
    epub, meta = _find_alice()
    if not epub:
        pytest.skip("Alice EPUB not found")

    from book_sbd.cli import process_book
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "output")
        book_data = process_book(epub, meta, output_dir=output_dir)

        out_path = os.path.join(output_dir, f"{ALICE_SLUG}.json")
        with open(out_path, encoding="utf-8") as f:
            return json.load(f)


class TestAliceV110:
    """v1.1.0 contract checks on Alice output."""

    def test_pipeline_version(self, alice_output):
        assert alice_output["pipeline_version"] == "1.1.0"

    def test_all_sentences_have_type(self, alice_output):
        for ch in alice_output["chapters"]:
            for s in ch["sentences"]:
                assert "type" in s, f"Ch{ch['number']} sent{s['number']}: missing type"
                assert s["type"] in ("prose", "verse"), (
                    f"Ch{ch['number']} sent{s['number']}: bad type {s['type']!r}"
                )

    def test_prose_sentences_no_newlines(self, alice_output):
        failures = []
        for ch in alice_output["chapters"]:
            for s in ch["sentences"]:
                if s["type"] == "prose" and "\n" in s["text"]:
                    failures.append(
                        f"Ch{ch['number']} sent{s['number']}: "
                        f"prose with newline: {s['text'][:60]!r}"
                    )
        assert not failures, (
            f"{len(failures)} prose sentences with newlines:\n"
            + "\n".join(failures[:10])
        )

    def test_verse_sentences_have_newlines(self, alice_output):
        """At least some verse sentences should exist and preserve newlines."""
        verse_sents = []
        for ch in alice_output["chapters"]:
            for s in ch["sentences"]:
                if s["type"] == "verse":
                    verse_sents.append(s)
        # Alice has poems/songs — expect some verse
        assert len(verse_sents) > 0, "Alice should have verse sentences"
        with_newlines = [s for s in verse_sents if "\n" in s["text"]]
        assert len(with_newlines) > 0, "Verse sentences should preserve newlines"

    def test_no_separator_sentences(self, alice_output):
        """No sentence should be a decorative asterisk separator."""
        import re
        sep_pattern = re.compile(r"^\s*(?:\*\s*){3,}\s*$")
        for ch in alice_output["chapters"]:
            for s in ch["sentences"]:
                assert not sep_pattern.match(s["text"]), (
                    f"Separator leaked: Ch{ch['number']} sent{s['number']}: {s['text']!r}"
                )

    def test_stats_consistency(self, alice_output):
        total = alice_output["stats"]["total_sentences"]
        chapter_sum = sum(ch["sentence_count"] for ch in alice_output["chapters"])
        assert total == chapter_sum

    def test_no_duplicate_stats_key(self, alice_output):
        assert "sentence_count" not in alice_output["stats"]

    def test_chapter_sentence_count_matches(self, alice_output):
        for ch in alice_output["chapters"]:
            assert ch["sentence_count"] == len(ch["sentences"]), (
                f"Ch{ch['number']}: sentence_count={ch['sentence_count']} "
                f"but has {len(ch['sentences'])} sentences"
            )
