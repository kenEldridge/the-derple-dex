# Quote-Aware Segmentation and Span-Basis Alignment Plan (v1.1.x)

Location: `apature/sentence_bd`
Date: 2026-03-05
Status: Ready for implementation

## Objective

Implement the conclusion from diff analysis:
1. Reduce systematic over-splitting in quoted discourse.
2. Align span offsets by using a single authoritative normalized text basis.
3. Apply changes generically across all 19 books (no Alice-only tuning).

## Problem Statement

From analysis against the reference output:
1. We over-split many quoted monologue regions (Punkt boundary behavior around `! ? .` inside quotes).
2. We have span drift caused by mismatched text normalization basis between segmentation and export.
3. This creates mismatch categories such as over-split, under-split, and positional drift.

## Core Architecture Decisions (Locked)

1. Authoritative span basis is `normalized_text` per chapter.
2. `canonical_text` remains for diagnostics only, not exported span indexing.
3. Export invariant: `sentence.text == normalized_text[start:end]`.
4. Global sentence total key is `stats.total_sentences` only.

## Normalization Contract

Normalization must be deterministic and applied before segmentation.

1. Remove decorative separators matching:
   - `^\s*(?:\*\s*){3,}$`
2. Split chapter text into blocks on paragraph boundaries.
3. Classify each block as `prose` or `verse`.
4. For prose blocks:
   - convert line-wrap newlines to spaces
   - keep paragraph boundaries as `\n\n`
5. For verse blocks:
   - preserve internal newlines
6. Construct a single `normalized_text` chapter string from classified blocks.

## Quote-Aware Segmentation Rules

Baseline:
1. Run Punkt on `normalized_text` to get candidate spans.

Patch layer (new):
1. Merge boundaries that split continuous quoted monologue in the same paragraph.
2. Primary trigger patterns:
   - punctuation split inside an open quote where subsequent fragment is same discourse unit
   - repeated exclamations/questions within one quoted thought/speech unit
3. Non-merge guards:
   - paragraph break between candidates
   - strong speaker-turn indicators
   - clear attribution boundary indicating a new sentence unit
4. Maintain deterministic ordering and non-overlap invariants after merges.

## Implementation Work Packages

1. `book_sbd/src/book_sbd/segment/text_modes.py` (new)
   - block classification
   - normalization functions
   - separator filtering helpers

2. `book_sbd/src/book_sbd/segment/punkt_backend.py`
   - ensure segmentation returns spans on `normalized_text`
   - remove brittle string-search span reconstruction

3. `book_sbd/src/book_sbd/segment/patch_rules.py`
   - add quote-aware merge rule
   - add strict non-merge guard conditions

4. `book_sbd/src/book_sbd/cli.py`
   - wire normalization -> segmentation -> patching -> sentence typing

5. `book_sbd/src/book_sbd/export.py`
   - include sentence `type`
   - enforce single authoritative sentence total key

6. Versioning
   - `book_sbd/src/book_sbd/__init__.py`
   - `book_sbd/pyproject.toml`

7. Invariants
   - `book_sbd/src/book_sbd/invariants.py`
   - add full non-whitespace coverage check on `normalized_text`

## Test Plan

## Unit tests

1. Normalization:
   - prose newline stripping
   - verse newline preservation
   - separator removal

2. Quote-aware merge:
   - positive cases (monologue continuation)
   - negative cases (true sentence boundary)
   - edge cases (quotes + attribution + punctuation)

3. Span invariants:
   - sorted
   - non-overlapping
   - full non-whitespace coverage on `normalized_text`

4. Schema/stats:
   - every sentence has valid `type`
   - no duplicate global sentence total keys

## Integration tests

1. Reference regression test (Alice feedback pair):
   - over-split count reduced materially
   - offset drift reduced or eliminated under normalized basis

2. Full corpus checks:
   - no separator leakage
   - prose newline leakage near-zero
   - deterministic rerun hashes stable

## Acceptance Gates

1. All tests pass.
2. `stats.total_sentences == sum(len(ch.sentences))` in every output.
3. Sentence `type` present and valid for all sentences.
4. No decorative separator sentences.
5. Deterministic reruns are byte-identical for regenerated outputs.
6. Quality gate: over-split category count decreases vs current baseline.

## Rollout and Rollback

1. First write to `output_v11_candidate/`.
2. Run all validation gates there.
3. Compare candidate vs current outputs on metrics and hashes.
4. Promote candidate to `output/` only after review sign-off.
5. Preserve previous zip artifact for rollback.

## Execution Sequence (Strict Order)

1. Add failing tests for normalization/type/quote-merge expectations.
2. Implement normalization contract and sentence typing pipeline.
3. Implement quote-aware merge with guard rules.
4. Update export and versioning.
5. Add/upgrade invariants and integration checks.
6. Run full 19-book batch to candidate output.
7. Validate, then promote.

## Definition of Done

All conditions must be true:
1. v1.1.x output generated for all 19 books.
2. Span indexing is consistent with `normalized_text` basis.
3. Quoted monologue over-splitting is materially reduced.
4. No conflicting sentence totals in stats.
5. Full deterministic and quality gates pass.
