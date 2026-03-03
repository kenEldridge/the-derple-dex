"""Integration tests: ingest -> canonicalize -> segment pipeline.

Gate 3 checks:
- Invariants hold for all segmented chapters
- Rerun produces identical spans (determinism)
"""

import sys, os, glob, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from book_sbd.pipeline import ingest_book
from book_sbd.canonicalize import canonicalize
from book_sbd.segment.punkt_backend import PunktSegmenter
from book_sbd.invariants import (
    check_spans_sorted_non_overlapping,
    check_no_empty_sentences,
)


EPUB_DIR = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "epubs_unpacked", "epubs"
))

# Test on a representative subset for speed
SAMPLE_SLUGS = [
    "pride-and-prejudice",
    "divine-comedy-dantes-inferno",
    "grimms-fairy-tales",
    "the-great-gatsby",
    "meditations",
]


@pytest.fixture(scope="module")
def segmenter():
    return PunktSegmenter()


@pytest.fixture(scope="module")
def sample_books():
    data = {}
    for slug in SAMPLE_SLUGS:
        epub_path = os.path.join(EPUB_DIR, f"{slug}.epub")
        meta_path = os.path.join(EPUB_DIR, f"{slug}_meta.json")
        if os.path.exists(epub_path):
            data[slug] = ingest_book(epub_path, meta_path)
    return data


class TestGate3:

    def test_invariants_after_segmentation(self, sample_books, segmenter):
        failures = []
        for slug, data in sample_books.items():
            for ch in data["chapters"]:
                ct = canonicalize(ch.text)
                spans = segmenter.segment(ct)
                # Build sentence dicts for invariant check
                sentences = []
                for i, (s, e) in enumerate(spans):
                    sentences.append({
                        "number": i + 1,
                        "start": s,
                        "end": e,
                        "text": ct[s:e],
                    })
                ch_dict = {"number": ch.number, "sentences": sentences}
                errors = check_spans_sorted_non_overlapping(ch_dict)
                errors += check_no_empty_sentences(ch_dict)
                if errors:
                    for err in errors:
                        failures.append(f"{slug}: {err}")
        assert not failures, "Invariant failures:\n" + "\n".join(failures[:20])

    def test_determinism(self, sample_books, segmenter):
        """Two segmentation runs produce identical spans."""
        for slug, data in sample_books.items():
            for ch in data["chapters"][:3]:  # first 3 chapters per book
                ct = canonicalize(ch.text)
                spans1 = segmenter.segment(ct)
                spans2 = segmenter.segment(ct)
                assert spans1 == spans2, (
                    f"{slug} ch{ch.number}: non-deterministic spans"
                )
