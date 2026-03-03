# Sentence Boundary Detection Batch Plan (Public-Domain EPUB Set)

This plan is updated in place for the provided batch at:
`C:/Users/eldri/projects/the-derple-dex/apature/sentence_bd/epubs_unpacked/epubs`

## Objective

Produce one JSON file per book in Bible-like structure:

- `title`, `author`, `slug`
- `chapters[]`
- each chapter has `number` and `sentences[]`
- each sentence has `number` and `text`

Target reference style: `BookName chapter:sentence` (for example, `Pride and Prejudice 3:12`).

## Input Reality (validated)

- 19 EPUB files + 19 companion `_meta.json` files
- Mixed structure patterns across books: `Chapter`, `Book`, `Part`, `Canto`, and story collections
- All books include Project Gutenberg header/footer/license boilerplate
- Spine doc counts vary widely (roughly 7 to 368 docs/book), so chapter boundaries cannot be inferred from file splits alone

This means chapter extraction and boilerplate removal are first-class upstream blockers.

---

## Tech choices (Python)

Baseline SBD backend:

- Option A (recommended first): NLTK Punkt
- Option B (later, optional): PyICU BreakIterator

Start with Punkt behind an interface so backend can be swapped.

Core design rule: operate on canonical chapter text and output character spans `(start, end)`.

---

## Repo structure (updated)

```
book_sbd/
  pyproject.toml
  src/book_sbd/
    __init__.py
    ingest/
      __init__.py
      epub_parser.py          # OPF/spine/nav extraction
      structure.py            # chapter unit detection/policy
      boilerplate.py          # Gutenberg boundary stripping
    canonicalize.py
    segment/
      __init__.py
      base.py
      punkt_backend.py
      icu_backend.py          # optional later
      patch_rules.py
    numbering.py              # chapter + sentence numbering
    export.py
    eval.py
    cli.py                  # Stage 6: single-book + batch entry points
  tests/
    unit/
      test_ingest_structure.py
      test_boilerplate.py
      test_canonicalize.py
      test_invariants.py
      test_patch_rules.py
    integration/
      test_pipeline_snapshots.py
      test_batch_19_books.py
    fixtures/
      raw/
      gold/
```

---

## Data contracts (freeze early)

### Input metadata (`*_meta.json`)

Keep and propagate source metadata:

- `title`
- `author`
- `slug`
- `gutenberg_id`
- `format`
- `source_url`

### Internal chapter unit

`ChapterUnit = { number, label, canonical_text, sentences }`

- `number` is contiguous `1..N`
- `label` is optional source label (`CHAPTER I`, `BOOK II`, `Canto V`, etc.)

### Sentence record

`Sentence = { number, start, end, text }`

- `start/end` index into chapter canonical text
- invariant: `text == canonical_text[start:end]`
- numbering is per chapter: `1..M`

### Final export record — strict mode

Strict mode outputs exactly the schema requested in the original spec.
Written to `output/strict/{slug}.json`.

```
{
  "title": "...",
  "author": "...",
  "slug": "...",
  "chapters": [
    {
      "number": 1,
      "sentences": [
        { "number": 1, "text": "..." }
      ]
    }
  ]
}
```

### Final export record — extended mode

Extended mode adds metadata and debug fields useful for evaluation and auditing.
Written to `output/extended/{slug}.json`.

```
{
  "title": "...",
  "author": "...",
  "slug": "...",
  "gutenberg_id": "...",
  "source_url": "...",
  "format": "...",
  "pipeline_version": "1.0.0",
  "chapters": [
    {
      "number": 1,
      "label": "CHAPTER I",
      "sentence_count": 42,
      "sentences": [
        { "number": 1, "text": "...", "start": 0, "end": 55, "char_len": 55 }
      ]
    }
  ],
  "stats": {
    "chapter_count": 61,
    "total_sentences": 4231,
    "total_chars": 682345
  }
}
```

---

## Stage 0 - Spec + harness (block downstream until green)

### Tasks

1. Write `SPEC.md` with:
   - chapter policy (what counts as chapter in mixed formats)
   - boilerplate policy (what must be excluded)
   - sentence definition and invariants
   - final JSON schema
2. Add pytest + CI (`pytest -q`).
3. Add invariant helpers:
   - chapter numbers contiguous
   - sentence numbers contiguous within chapter
   - spans sorted and non-overlapping
   - `text` matches slice
   - no empty/whitespace-only sentence unless explicitly allowed

### Gate 0 (hard)

- PASS: spec + invariants helper + CI test run exist
- FAIL: stop if missing

---

## Stage 1 - EPUB ingestion + structure extraction (new upstream blocker)

### Implement `ingest/epub_parser.py`

- Parse `META-INF/container.xml`, OPF manifest/spine, and NCX/nav labels
- Load reading-order XHTML/HTML content deterministically

### Implement `ingest/structure.py`

- Build chapter candidates from nav labels + heading heuristics
- Support variants: `Chapter`, `Book`, `Part`, `Canto`, story-title based units
- Normalize to a contiguous chapter list

### Implement `ingest/boilerplate.py`

- Remove Gutenberg header/footer/license regions and transcriber blocks
- Use explicit start/end marker detection and fallback heuristics

### Tests

- Unit tests on representative snippets for:
  - chapter label parsing
  - chapter boundary selection
  - boilerplate stripping
- Integration test on all 19 books:
  - parsed chapter units exist
  - no license text inside retained chapter bodies

### Deterministic artifact

Stage 1 produces a per-book intermediate file at `build/chapter_units/{slug}.json` containing:

```
{
  "slug": "...",
  "chapters": [
    { "number": 1, "label": "CHAPTER I", "text": "..." }
  ]
}
```

Written with `json.dumps(sort_keys=True, ensure_ascii=False, indent=2)` + trailing newline.
Determinism is verified by comparing SHA-256 of this file across two runs.

### Per-book chapter expectations

Maintain a reference table `EXPECTED_CHAPTERS` mapping each slug to an expected chapter
count and a tolerance band. The gate checks `abs(actual - expected) <= tolerance` per book.

| Slug | Expected | Tolerance | Structure type |
|------|----------|-----------|----------------|
| pride-and-prejudice | 61 | 0 | Chapter |
| crime-and-punishment | 37 | 2 | Part+Chapter |
| divine-comedy-dantes-inferno | 34 | 0 | Canto |
| don-quixote | 126 | 5 | Part+Chapter |
| dracula | 27 | 0 | Chapter (journal) |
| frankenstein-or-the-modern-prometheus | 24 | 1 | Letter+Chapter |
| grimms-fairy-tales | 62 | 0 | Story collection |
| meditations | 12 | 0 | Book |
| moby-dick-or-the-whale | 135 | 1 | Chapter (Etymology+Extracts+135) |
| the-adventures-of-sherlock-holmes | 12 | 0 | Story collection |
| the-art-of-war | 13 | 0 | Section |
| the-count-of-monte-cristo-illustrated | 117 | 2 | Chapter |
| the-great-gatsby | 9 | 0 | Chapter |
| the-iliad | 24 | 0 | Book |
| the-odyssey | 24 | 0 | Book |
| the-republic | 10 | 0 | Book |
| the-three-musketeers | 67 | 1 | Chapter |
| war-and-peace | 365 | 5 | Book+Part+Chapter |
| alices-adventures-in-wonderland | 12 | 0 | Chapter |

### Gate 1 (hard)

- PASS: all 19 books parse to >=1 chapter unit
- PASS: per-book chapter count within tolerance of expected (see table above)
- PASS: no chapter body contains known Gutenberg license marker strings
- PASS: no chapter has fewer than 20 characters of text (empty/stub detection)
- PASS: `build/chapter_units/{slug}.json` is byte-identical (SHA-256) across two runs
- FAIL: stop before canonicalization/SBD

---

## Stage 2 - Canonicalization (run per chapter unit)

### Implement `canonicalize.py`

Rules:

- Normalize newlines: `\r\n` / `\r` -> `\n`
- Remove BOM
- Unicode normalize (`NFC`)
- Trim trailing whitespace per line
- Collapse spaces/tabs within lines (preserve paragraph breaks)
- Normalize 3+ blank lines to 2

Apply canonicalization chapter-by-chapter.

### Tests

- Unit tests per rule
- Snapshot tests for chapter canonical text

### Gate 2 (hard)

- PASS: idempotence (`canon(canon(x)) == canon(x)`) on fixtures
- PASS: snapshots stable
- FAIL: stop before SBD

---

## Stage 3 - Baseline segmentation backend (no patch rules yet)

### Interface

`Segmenter.segment(canonical_text: str) -> list[(start, end)]`

### Backend A: Punkt

1. Train once on representative canonicalized book text
2. Serialize model artifact
3. Load artifact at runtime (no retraining in normal runs)
4. Segment chapter-by-chapter, preserving chapter boundaries

### Tests

- Integration pipeline test: ingest -> canonicalize -> segment
- Invariants check after each chapter segmentation
- Determinism check (same spans on rerun)

### Gate 3 (hard)

- PASS: invariants for all fixtures
- PASS: rerun produces byte-identical spans
- FAIL: stop before patch rules

---

## Stage 4 - Gold set + evaluation (sentence + chapter)

### Gold annotation scope

- Select 8-12 books spanning structure types
- Annotate:
  - chapter boundaries (or chapter unit labels/count expectations)
  - 200-500 sentence boundaries total

### `eval.py`

- Sentence boundary precision/recall/F1
- Chapter extraction checks:
  - chapter count delta
  - boundary alignment summary

### Gate 4 (hard)

- PASS: gold fixtures exist and eval is deterministic
- PASS: baseline metrics recorded in `METRICS.md`
- FAIL: no patch rules until this is in place

---

## Stage 5 - Patch rules layer (test-driven, surgical)

Pipeline:

`baseline_spans -> patch_rules.apply(chapter_text, spans) -> final_spans`

Initial rules:

1. Closing quote/bracket attachment
2. Abbreviation suppressions (`Mr.`, `Mrs.`, `Dr.`, `St.`, etc.)
3. Ellipsis handling
4. Heading/separator edge handling (if leaked into chapter text)

### Tests required per rule

- positive fix
- negative control
- edge case
- gold metrics non-regression

### Gate 5 (hard)

- PASS: per-rule unit tests and rationale docs
- PASS: no invariant violations after patching
- PASS: gold F1 non-regressing (prefer improvement)
- FAIL: remove/adjust any regressing rule

---

## Stage 6 - Numbering + export (deliverable stage)

### Implement `numbering.py`

- Chapter numbering: contiguous `1..N`
- Sentence numbering: contiguous `1..M` per chapter

### Implement `cli.py`

- `book-sbd run <epub>` — single-book pipeline (ingest through export)
- `book-sbd batch <dir>` — run all EPUBs in directory
- `book-sbd eval <gold-dir>` — run evaluation against gold fixtures

### Implement `export.py`

- One JSON per book slug, in two modes:
  - **Strict mode** → `output/strict/{slug}.json` — minimal schema (title, author, slug, chapters with number + sentences with number + text)
  - **Extended mode** → `output/extended/{slug}.json` — adds gutenberg_id, source_url, format, pipeline_version, chapter labels, sentence spans/char_len, and book-level stats
- Both modes written with `json.dumps(sort_keys=True, ensure_ascii=False, indent=2)` + trailing newline for determinism

### Gates 6 (hard)

- PASS: schema validation succeeds for all 19 outputs
- PASS: chapter and sentence numbering contiguous everywhere
- PASS: no sentence crosses chapter boundary
- PASS: two full runs are byte-identical

---

## Stage 7 - Corpus-scale acceptance run (all 19 books)

Collect health metrics:

- empty chapter count
- sentences < 3 chars (excluding configured cases)
- sentences > 1000 chars
- license leakage count in final output
- top longest sentences samples

### Gate 7 (hard)

- PASS: 0 crashes and 0 invalid spans
- PASS: license leakage count is 0
- PASS: short sentence ratio (< 3 chars) is <= 0.1% of total sentences corpus-wide
- PASS: long sentence count (> 1000 chars) is <= 0.05% of total sentences corpus-wide
- NOTE: documented exclusions for short sentences: standalone dialogue tags (e.g. `"No."`, `"Yes!"`), single-word exclamations, and Roman numeral section markers are expected and not counted as violations
- PASS: manual spot-check on at least 5 varied books

---

## Practical starting order (minimal path)

1. Stage 0 spec + invariants
2. Stage 1 ingest/structure/boilerplate (must be correct first)
3. Stage 2 canonicalization
4. Stage 3 baseline SBD
5. Stage 4 small gold + eval
6. Stage 5 only 1-2 high-value patch rules
7. Stage 6 numbering + final JSON export
8. Stage 7 full 19-book acceptance run

---

## Initial acceptance targets (adjust after first baseline)

- Sentence boundary F1 (gold): >= 0.97 baseline
- After patch rules: >= 0.985 with no gold regression
- License leakage in exported JSON: 0
- Empty chapters: 0
- Deterministic rerun diff: none

---

## Avoid early overbuild

- No heavy ML classifier before baseline + gold are stable
- No advanced chapter semantics beyond deterministic heuristics unless needed
- No extra output formats until JSON deliverable is validated
