"""Integration tests for the full 19-book batch.

Gate 1 checks:
- All 19 books parse to >=1 chapter unit
- Per-book chapter count within tolerance of expected
- No chapter body contains Gutenberg license markers
- No chapter has fewer than 20 characters
- Deterministic output (byte-identical JSON across two runs)
"""

import sys, os, glob, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from book_sbd.pipeline import (
    ingest_book,
    write_chapter_units_json,
    check_license_leakage,
    sha256_file,
    EXPECTED_CHAPTERS,
)

EPUB_DIR = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "epubs_unpacked", "epubs"
))
BUILD_DIR = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "build"
))


def _get_epub_paths():
    """Get all epub/meta path pairs."""
    epubs = sorted(glob.glob(os.path.join(EPUB_DIR, "*.epub")))
    result = []
    for epub_path in epubs:
        slug = os.path.basename(epub_path).replace(".epub", "")
        meta_path = os.path.join(EPUB_DIR, f"{slug}_meta.json")
        if os.path.exists(meta_path):
            result.append((slug, epub_path, meta_path))
    return result


ALL_BOOKS = _get_epub_paths()


@pytest.fixture(scope="module")
def all_book_data():
    """Ingest all 19 books once for the test module."""
    data = {}
    for slug, epub_path, meta_path in ALL_BOOKS:
        data[slug] = ingest_book(epub_path, meta_path)
    return data


class TestGate1:
    """Gate 1 integration tests."""

    def test_all_19_books_found(self):
        assert len(ALL_BOOKS) == 19, f"Expected 19 books, found {len(ALL_BOOKS)}"

    def test_all_books_have_chapters(self, all_book_data):
        for slug, data in all_book_data.items():
            assert len(data["chapters"]) >= 1, f"{slug}: no chapters extracted"

    def test_chapter_count_within_tolerance(self, all_book_data):
        failures = []
        for slug, data in all_book_data.items():
            actual = len(data["chapters"])
            if slug in EXPECTED_CHAPTERS:
                expected, tolerance = EXPECTED_CHAPTERS[slug]
                diff = abs(actual - expected)
                if diff > tolerance:
                    failures.append(
                        f"{slug}: expected {expected}±{tolerance}, got {actual} (diff={diff})"
                    )
        assert not failures, "Chapter count failures:\n" + "\n".join(failures)

    def test_no_license_leakage(self, all_book_data):
        failures = []
        for slug, data in all_book_data.items():
            issues = check_license_leakage(data["chapters"])
            if issues:
                failures.extend(f"{slug}: {issue}" for issue in issues)
        assert not failures, "License leakage:\n" + "\n".join(failures)

    def test_no_stub_chapters(self, all_book_data):
        failures = []
        for slug, data in all_book_data.items():
            for ch in data["chapters"]:
                if len(ch.text) < 20:
                    failures.append(
                        f"{slug} chapter {ch.number}: only {len(ch.text)} chars"
                    )
        assert not failures, "Stub chapters:\n" + "\n".join(failures)

    def test_deterministic_output(self, all_book_data):
        """Two runs of write_chapter_units_json produce byte-identical files."""
        import tempfile, shutil

        dir1 = os.path.join(BUILD_DIR, "_det_test_1")
        dir2 = os.path.join(BUILD_DIR, "_det_test_2")
        os.makedirs(dir1, exist_ok=True)
        os.makedirs(dir2, exist_ok=True)

        try:
            failures = []
            for slug, data in all_book_data.items():
                p1 = write_chapter_units_json(data, dir1)
                p2 = write_chapter_units_json(data, dir2)
                h1 = sha256_file(p1)
                h2 = sha256_file(p2)
                if h1 != h2:
                    failures.append(f"{slug}: SHA-256 mismatch {h1} != {h2}")
            assert not failures, "Determinism failures:\n" + "\n".join(failures)
        finally:
            shutil.rmtree(dir1, ignore_errors=True)
            shutil.rmtree(dir2, ignore_errors=True)
