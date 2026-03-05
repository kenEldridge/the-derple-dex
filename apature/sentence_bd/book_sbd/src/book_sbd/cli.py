"""CLI entry points for book-sbd.

Commands:
  book-sbd run <epub> [--meta <meta.json>] [--output-dir <dir>]
  book-sbd batch <epub-dir> [--output-dir <dir>]
  book-sbd eval <gold-dir> [--epub-dir <dir>]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time

from .canonicalize import canonicalize
from .export import export_book
from .ingest.epub_parser import parse_epub
from .ingest.structure import extract_chapters
from .invariants import validate_book
from .numbering import number_chapters, number_sentences
from .pipeline import ingest_book, write_chapter_units_json, check_license_leakage
from .segment.punkt_backend import PunktSegmenter
from .segment.patch_rules import apply_patch_rules
from .segment.text_modes import apply_text_modes, get_sentence_type


def process_book(
    epub_path: str,
    meta_path: str,
    build_dir: str | None = None,
    output_dir: str | None = None,
    verbose: bool = False,
) -> dict:
    """Run the full pipeline on a single book.

    Returns the processed book data dict.
    """
    slug = os.path.basename(epub_path).replace(".epub", "")
    if verbose:
        print(f"Processing: {slug}")

    # Stage 1: Ingest
    book_data = ingest_book(epub_path, meta_path)
    chapters = book_data["chapters"]

    if verbose:
        print(f"  Chapters: {len(chapters)}")

    # Write Stage 1 intermediate
    if build_dir:
        write_chapter_units_json(book_data, build_dir)

    # Stage 2+3+5: Canonicalize -> Segment -> Patch
    segmenter = PunktSegmenter()
    processed_chapters = []

    for ch in chapters:
        canonical = canonicalize(ch.text)

        # Apply text mode classification and normalization
        processed_text, block_metadata = apply_text_modes(canonical)

        # Segment the mode-normalized text
        spans = segmenter.segment(processed_text)
        spans = apply_patch_rules(processed_text, spans, block_metadata)

        sentences = []
        for i, (start, end) in enumerate(spans):
            sent_type = get_sentence_type(start, end, block_metadata)
            sentences.append({
                "number": i + 1,
                "start": start,
                "end": end,
                "text": processed_text[start:end],
                "type": sent_type,
            })

        processed_chapters.append({
            "number": ch.number,
            "label": ch.label,
            "canonical_text": processed_text,
            "sentences": sentences,
        })

    # Stage 6: Number
    number_chapters(processed_chapters)
    for ch in processed_chapters:
        number_sentences(ch["sentences"])

    book_data["processed_chapters"] = processed_chapters

    # Export
    if output_dir:
        export_book(book_data, output_dir)

    if verbose:
        total_sents = sum(len(ch["sentences"]) for ch in processed_chapters)
        print(f"  Sentences: {total_sents}")

    return book_data


def cmd_run(args):
    """Run pipeline on a single book."""
    epub_path = args.epub
    meta_path = args.meta
    if not meta_path:
        meta_path = epub_path.replace(".epub", "_meta.json")

    base_dir = args.output_dir or os.path.dirname(epub_path)
    build_dir = os.path.join(base_dir, "build")
    output_dir = os.path.join(base_dir, "output")

    process_book(
        epub_path, meta_path,
        build_dir=build_dir,
        output_dir=output_dir,
        verbose=True,
    )


def cmd_batch(args):
    """Run pipeline on all EPUBs in a directory."""
    epub_dir = args.epub_dir
    base_dir = args.output_dir or os.path.dirname(epub_dir)
    build_dir = os.path.join(base_dir, "build")
    output_dir = os.path.join(base_dir, "output")

    epubs = sorted(glob.glob(os.path.join(epub_dir, "*.epub")))
    print(f"Found {len(epubs)} EPUBs")

    start = time.time()
    for epub_path in epubs:
        slug = os.path.basename(epub_path).replace(".epub", "")
        meta_path = os.path.join(epub_dir, f"{slug}_meta.json")
        if not os.path.exists(meta_path):
            print(f"  SKIP {slug}: no meta.json")
            continue

        process_book(
            epub_path, meta_path,
            build_dir=build_dir,
            output_dir=output_dir,
            verbose=True,
        )

    elapsed = time.time() - start
    print(f"\nBatch complete: {len(epubs)} books in {elapsed:.1f}s")


def cmd_eval(args):
    """Run evaluation against gold fixtures."""
    from .eval import evaluate_book, load_gold

    gold_dir = args.gold_dir
    epub_dir = args.epub_dir

    segmenter = PunktSegmenter()
    gold_files = sorted(glob.glob(os.path.join(gold_dir, "*.json")))

    print(f"Evaluating against {len(gold_files)} gold files\n")

    for gold_path in gold_files:
        gold = load_gold(gold_path)
        slug = gold["slug"]
        epub_path = os.path.join(epub_dir, f"{slug}.epub")
        meta_path = os.path.join(epub_dir, f"{slug}_meta.json")

        if not os.path.exists(epub_path):
            print(f"  SKIP {slug}: epub not found")
            continue

        book_data = ingest_book(epub_path, meta_path)

        pred_spans = {}
        for ch in book_data["chapters"]:
            ct = canonicalize(ch.text)
            processed_text, _ = apply_text_modes(ct)
            spans = segmenter.segment(processed_text)
            spans = apply_patch_rules(processed_text, spans)
            pred_spans[ch.number] = spans

        result = evaluate_book(pred_spans, gold)
        agg = result["aggregate"]
        print(
            f"{slug:45s}  P={agg.precision:.4f}  R={agg.recall:.4f}  "
            f"F1={agg.f1:.4f}"
        )


def main():
    parser = argparse.ArgumentParser(prog="book-sbd", description="Sentence Boundary Detection for books")
    subparsers = parser.add_subparsers(dest="command")

    # run
    p_run = subparsers.add_parser("run", help="Process a single EPUB")
    p_run.add_argument("epub", help="Path to EPUB file")
    p_run.add_argument("--meta", help="Path to meta.json (default: {epub}_meta.json)")
    p_run.add_argument("--output-dir", help="Output directory")

    # batch
    p_batch = subparsers.add_parser("batch", help="Process all EPUBs in a directory")
    p_batch.add_argument("epub_dir", help="Directory containing EPUB files")
    p_batch.add_argument("--output-dir", help="Output directory")

    # eval
    p_eval = subparsers.add_parser("eval", help="Evaluate against gold annotations")
    p_eval.add_argument("gold_dir", help="Directory with gold JSON files")
    p_eval.add_argument("--epub-dir", required=True, help="Directory with EPUB files")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "batch":
        cmd_batch(args)
    elif args.command == "eval":
        cmd_eval(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
