# Sentence Boundary Detection — Specification

## Chapter Policy

A "chapter" is the primary structural division of a book. The mapping depends on
the book's structure type:

| Structure type | What counts as a chapter |
|---------------|-------------------------|
| Chapter       | Each numbered chapter (CHAPTER I, CHAPTER II, ...) |
| Part+Chapter  | Each chapter within a part (parts are not separate chapters) |
| Book          | Each numbered book (BOOK I, THE FIRST BOOK, ...) |
| Canto         | Each canto (Canto I, Canto II, ...) |
| Story collection | Each individual story/tale |
| Section       | Each numbered or titled section |
| Letter+Chapter | Each letter or chapter as a separate unit |
| Journal       | Each dated journal entry or chapter |

### Rules

1. Chapters are numbered contiguously 1..N regardless of source labeling.
2. Front matter (title pages, tables of contents, dedications) is excluded.
3. Back matter (appendices, glossaries, notes, indices) is excluded.
4. Gutenberg boilerplate is always excluded (see Boilerplate Policy).
5. If a book has no detectable chapter divisions, the entire text body is
   treated as a single chapter (number=1).
6. Nested structures (Part > Chapter) flatten to chapters only.
7. The NCX/nav table of contents is the primary source for chapter boundaries.
   Heading-tag heuristics are used as fallback when NCX entries are too coarse.

## Boilerplate Policy

The following must be stripped before any text enters the pipeline:

1. **Gutenberg header block** — from start of text to the line matching
   `*** START OF THE PROJECT GUTENBERG EBOOK` (or close variants).
2. **Gutenberg footer/license block** — from the line matching
   `*** END OF THE PROJECT GUTENBERG EBOOK` (or close variants) to end of text.
3. **Transcriber notes** — blocks starting with "Transcriber's Note" or similar.
4. **Cover page wrapper** — the first spine document if it contains only a
   cover image or Project Gutenberg metadata.
5. **License footer spine document** — the last spine document if it contains
   the "FULL PROJECT GUTENBERG LICENSE" text.

Detection uses literal string matching on known marker phrases. No regex
heuristics beyond the marker set.

### Known marker strings (case-insensitive)

- `*** START OF THE PROJECT GUTENBERG EBOOK`
- `*** END OF THE PROJECT GUTENBERG EBOOK`
- `*** START OF THIS PROJECT GUTENBERG EBOOK`
- `*** END OF THIS PROJECT GUTENBERG EBOOK`
- `THE FULL PROJECT GUTENBERG LICENSE`
- `PROJECT GUTENBERG`
- `www.gutenberg.org`
- `gutenberg.org/license`

## Sentence Definition

A sentence is a contiguous span of text within a chapter's canonical text that
represents a single grammatical sentence.

### Invariants

1. **Contiguous numbering**: sentence numbers within a chapter form 1..M with
   no gaps.
2. **Span validity**: each sentence has `start` and `end` character offsets into
   the chapter's canonical text such that `text == canonical_text[start:end]`.
3. **Sorted and non-overlapping**: spans are strictly ordered
   (`spans[i].end <= spans[i+1].start`).
4. **No empty sentences**: no sentence text is empty or whitespace-only.
5. **Full coverage**: every non-whitespace character in the canonical text
   belongs to exactly one sentence span.

## Output Schemas

### Strict mode

```json
{
  "title": "string",
  "author": "string",
  "slug": "string",
  "chapters": [
    {
      "number": "integer (1-based)",
      "sentences": [
        {
          "number": "integer (1-based, per-chapter)",
          "text": "string (non-empty)"
        }
      ]
    }
  ]
}
```

No additional fields are permitted in strict mode.

### Extended mode

```json
{
  "title": "string",
  "author": "string",
  "slug": "string",
  "gutenberg_id": "string",
  "source_url": "string",
  "format": "string",
  "pipeline_version": "string",
  "chapters": [
    {
      "number": "integer",
      "label": "string or null",
      "sentence_count": "integer",
      "sentences": [
        {
          "number": "integer",
          "text": "string",
          "start": "integer",
          "end": "integer",
          "char_len": "integer"
        }
      ]
    }
  ],
  "stats": {
    "chapter_count": "integer",
    "total_sentences": "integer",
    "total_chars": "integer"
  }
}
```

## Canonicalization Rules (applied per chapter)

1. Normalize newlines: `\r\n` and `\r` → `\n`
2. Remove BOM (U+FEFF)
3. Unicode normalize to NFC
4. Trim trailing whitespace per line
5. Collapse runs of spaces/tabs within lines to single space
6. Normalize 3+ consecutive blank lines to exactly 2
7. Strip leading/trailing whitespace from overall text

Canonicalization is idempotent: `canon(canon(x)) == canon(x)`.
