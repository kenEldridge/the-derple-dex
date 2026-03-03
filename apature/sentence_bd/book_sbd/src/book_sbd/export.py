"""Export pipeline results to JSON.

Single output mode with metadata, chapter labels, sentence spans, and stats.
"""

from __future__ import annotations

import json
import os

from . import __version__


def export_book(book_data: dict, output_dir: str) -> str:
    """Export book to JSON.

    Schema:
    {
      "title": str,
      "author": str,
      "slug": str,
      "gutenberg_id": str,
      "source_url": str,
      "format": str,
      "pipeline_version": str,
      "chapters": [
        {
          "number": int,
          "label": str | null,
          "sentence_count": int,
          "sentences": [
            {"number": int, "text": str, "start": int, "end": int, "char_len": int}
          ]
        }
      ],
      "stats": {
        "chapter_count": int,
        "total_sentences": int,
        "total_chars": int
      }
    }
    """
    slug = book_data["slug"]
    meta = book_data["meta"]

    total_sentences = 0
    total_chars = 0

    chapters_out = []
    for ch in book_data["processed_chapters"]:
        sentences_out = []
        for s in ch["sentences"]:
            sentences_out.append({
                "char_len": s["end"] - s["start"],
                "end": s["end"],
                "number": s["number"],
                "start": s["start"],
                "text": s["text"],
            })
        total_sentences += len(sentences_out)
        total_chars += sum(s["char_len"] for s in sentences_out)

        chapters_out.append({
            "label": ch.get("label"),
            "number": ch["number"],
            "sentence_count": len(sentences_out),
            "sentences": sentences_out,
        })

    output = {
        "author": meta.get("author", ""),
        "chapters": chapters_out,
        "format": meta.get("format", ""),
        "gutenberg_id": meta.get("gutenberg_id", ""),
        "pipeline_version": __version__,
        "slug": slug,
        "source_url": meta.get("source_url", ""),
        "stats": {
            "chapter_count": len(chapters_out),
            "total_chars": total_chars,
            "total_sentences": total_sentences,
        },
        "title": meta.get("title", ""),
    }

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{slug}.json")

    content = json.dumps(output, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    return out_path
