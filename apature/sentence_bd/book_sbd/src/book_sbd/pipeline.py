"""Full pipeline: ingest -> canonicalize -> segment -> number -> export.

Each stage can be run independently or as part of the full pipeline.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from .ingest.epub_parser import parse_epub
from .ingest.structure import extract_chapters, ChapterUnit


# Expected chapter counts (from plan, with actuals updated per-edition)
EXPECTED_CHAPTERS = {
    "alices-adventures-in-wonderland": (12, 0),
    "crime-and-punishment": (40, 3),
    "divine-comedy-dantes-inferno": (34, 0),
    "don-quixote": (126, 5),
    "dracula": (27, 0),
    "frankenstein-or-the-modern-prometheus": (28, 4),
    "grimms-fairy-tales": (62, 0),
    "meditations": (12, 0),
    "moby-dick-or-the-whale": (135, 1),
    "pride-and-prejudice": (59, 2),
    "the-adventures-of-sherlock-holmes": (12, 0),
    "the-art-of-war": (13, 0),
    "the-count-of-monte-cristo-illustrated": (117, 2),
    "the-great-gatsby": (9, 0),
    "the-iliad": (24, 0),
    "the-odyssey": (24, 0),
    "the-republic": (10, 0),
    "the-three-musketeers": (68, 1),
    "war-and-peace": (365, 5),
}

LICENSE_MARKERS = [
    "PROJECT GUTENBERG",
    "GUTENBERG LICENSE",
    "www.gutenberg.org",
    "gutenberg.org/license",
]


def ingest_book(epub_path: str, meta_path: str) -> dict:
    """Stage 1: Parse EPUB and extract chapter units.

    Returns dict with metadata and chapter units.
    """
    slug = os.path.basename(epub_path).replace(".epub", "")

    # Load metadata
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # Parse EPUB
    epub_data = parse_epub(epub_path)

    # Extract chapters
    chapters = extract_chapters(epub_data, slug=slug)

    return {
        "slug": slug,
        "meta": meta,
        "chapters": chapters,
    }


def write_chapter_units_json(book_data: dict, build_dir: str) -> str:
    """Write Stage 1 intermediate chapter units JSON.

    Returns the file path.
    """
    slug = book_data["slug"]
    chapters_json = {
        "slug": slug,
        "chapters": [
            {
                "number": ch.number,
                "label": ch.label,
                "text": ch.text,
            }
            for ch in book_data["chapters"]
        ],
    }

    out_dir = os.path.join(build_dir, "chapter_units")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{slug}.json")

    content = json.dumps(chapters_json, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    return out_path


def check_license_leakage(chapters: list[ChapterUnit]) -> list[str]:
    """Check for Gutenberg license text in chapter bodies."""
    issues = []
    for ch in chapters:
        upper = ch.text.upper()
        for marker in LICENSE_MARKERS:
            if marker in upper:
                issues.append(
                    f"Chapter {ch.number}: license marker '{marker}' found"
                )
                break
    return issues


def sha256_file(path: str) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
