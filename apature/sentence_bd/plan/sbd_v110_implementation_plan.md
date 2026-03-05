# Sentence BD v1.1.0 Implementation Plan

Location: `apature/sentence_bd`
Date: 2026-03-05
Status: Ready for implementation

## 1) Executive Summary

This plan incorporates user feedback from `json improvements.eml` into a new pipeline release (`1.1.0`) without doing implementation work in this document.

The requested changes are not just schema tweaks. The core defect is that the pipeline treats all chapter text as one mode. It does not distinguish:
- wrapped prose line breaks (formatting noise)
- verse line breaks (semantic signal)
- decorative separators (non-content noise)

Because of that, the current system over-preserves newlines, mis-segments some boundaries, and leaks non-content lines as sentences.

## 2) Source Inputs and Evidence

Primary feedback:
- `json improvements.eml` with attached:
  - `alices-adventures-in-wonderland_start.json`
  - `alices-adventures-in-wonderland_end.json`

Current code and outputs:
- `book_sbd/src/book_sbd/*`
- `output/*.json`

Validated observations:
- Current output matches the feedback start file for Alice (`pipeline_version=1.0.0`, 967 sentences).
- Feedback end file expects `pipeline_version=1.1.0`, sentence `type`, prose newline stripping, revised segmentation, and separator removal.
- End file contains a bug-like inconsistency in stats (`total_sentences` vs `sentence_count`); do not replicate this.

## 3) True Root Cause (Not Just Symptom List)

Root issue: Missing text-mode layer before sentence segmentation.

Current behavior applies one canonicalization+segmentation path to all text blocks. This conflates:
- prose paragraphs where line-wrap newlines should be flattened
- verse blocks where line breaks are meaningful
- decorative separators that should be discarded

Secondary issue: span reconstruction in `punkt_backend.py` uses sentence string matching (`find`) which is brittle with repeated substrings and transformed whitespace.

## 4) Scope

### In Scope (v1.1.0)
1. Bump pipeline version to `1.1.0`.
2. Add sentence field `type` with exactly two values: `prose` or `verse`.
3. Strip/normalize newlines in prose sentence text (single-line prose output).
4. Preserve line breaks in verse sentence text.
5. Remove decorative asterisk separator lines from output.
6. Improve segmentation to better split over-merged spans and merge false splits.
7. Keep stats consistent with one authoritative sentence total.
8. Re-run all 19 inputs and regenerate outputs.

### Out of Scope (v1.1.0)
1. New output formats.
2. Model retraining or replacing Punkt backend.
3. Large chapter-extraction redesign.

## 5) Contract for v1.1.0 Output

Per sentence object, required fields:
- `number`
- `text`
- `start`
- `end`
- `char_len`
- `type` (`prose|verse`)

Global stats:
- Keep `stats.total_sentences` as the only authoritative total sentence count.
- If `chapter.sentence_count` exists, it must always equal `len(chapter.sentences)`.
- Do not emit duplicate global count keys (no conflicting `stats.sentence_count`).

## 6) Implementation Phases

## Phase 0 - Preflight and Safety

Goal: Lock baseline and add failing tests before touching pipeline logic.

Tasks:
1. Snapshot baseline hashes for current `output/*.json`.
2. Add targeted red tests for feedback requirements.
3. Confirm no implementation changes yet.

Files to add/update:
- `book_sbd/tests/unit/test_v110_contract.py` (new)
- `book_sbd/tests/integration/test_feedback_alice_v110.py` (new)

Acceptance gate:
- New tests fail on current code for the right reasons.

## Phase 1 - Text Mode Classification and Normalization

Goal: Introduce deterministic block-level mode handling (`prose` vs `verse`) before segmentation output is finalized.

Tasks:
1. Add mode module to classify blocks and normalize text by mode.
2. Add separator-line filter (asterisk patterns) before sentence emission.
3. Implement deterministic classifier rules (explicit):
   - Split chapter text into blocks on double newlines (`\\n\\n`).
   - For each block, build `lines = non-empty stripped lines`.
   - Normalize NBSP to plain space before line checks.
   - If a line matches separator regex `^\\s*(?:\\*\\s*){3,}$`, drop it from content.
   - Compute:
     - `short_line_ratio = (# lines with len <= 55) / line_count`
     - `terminal_punct_ratio = (# lines ending with . , ; : ! ? quote) / line_count`
     - `indented_ratio = (# lines starting with leading spaces/tabs) / line_count`
   - Classify block as `verse` when:
     - `line_count >= 3` AND
     - `short_line_ratio >= 0.70` AND
     - (`terminal_punct_ratio >= 0.50` OR `indented_ratio >= 0.30`)
   - Otherwise classify as `prose`.
4. Apply normalization by type:
   - prose: convert single newlines to spaces inside each block, preserve paragraph breaks between blocks
   - verse: preserve line breaks as-is

Files to add/update:
- `book_sbd/src/book_sbd/segment/text_modes.py` (new)
- `book_sbd/src/book_sbd/cli.py` (wire mode handling)
- `book_sbd/src/book_sbd/canonicalize.py` (only if minimal helper needed)

Acceptance gate:
- Prose sentences contain no `\n` in output.
- Verse sentences retain line breaks.
- Asterisk-only lines are absent from output.

## Phase 2 - Segmentation Quality Repair

Goal: Address split/merge regressions noted in feedback while keeping deterministic spans.

Tasks:
1. Replace brittle sentence-to-span mapping with span-native tokenization in Punkt backend.
2. Pin exact implementation:
   - load tokenizer once with `nltk.data.load(\"tokenizers/punkt/english.pickle\")`
   - use `tokenizer.span_tokenize(chapter_text)` directly
   - remove string matching via `find` entirely
3. Keep existing merge patch rules.
4. Add one conservative split rule for obvious over-merged multi-paragraph spans.
5. Ensure split/merge rules never produce overlapping spans and preserve deterministic ordering.

Files to add/update:
- `book_sbd/src/book_sbd/segment/punkt_backend.py`
- `book_sbd/src/book_sbd/segment/patch_rules.py`
- `book_sbd/tests/unit/test_patch_rules.py` (extend)

Acceptance gate:
- Segmenter returns sorted, non-overlapping spans deterministically.
- Alice sample shows meaningful split/merge improvement against feedback checks.

## Phase 3 - Export Contract v1.1.0

Goal: Emit new fields and consistent stats.

Tasks:
1. Add sentence `type` in export.
2. Bump version in package constants and metadata.
3. Ensure stats consistency and remove duplicate global sentence counters.

Files to add/update:
- `book_sbd/src/book_sbd/export.py`
- `book_sbd/src/book_sbd/__init__.py` (`__version__ = "1.1.0"`)
- `book_sbd/pyproject.toml` (`version = "1.1.0"`)
- `apature/sentence_bd/output/README.md` (schema docs)

Acceptance gate:
- Output schema matches v1.1.0 contract exactly.
- No conflicting sentence total keys.

## Phase 4 - Invariants and Health Metrics Hardening

Goal: Catch hidden regressions beyond the explicit feedback bullets.

Tasks:
1. Add coverage invariant from spec with explicit scope:
   - invariant applies to `segmentation_input_text` only (post-boilerplate, post-heading-strip, post-separator-removal)
   - every non-whitespace char in this scoped text must belong to exactly one sentence span
   - excluded by design: front/back matter and dropped separator lines
2. Add mode-aware checks:
   - prose newline leakage ratio
   - verse presence sanity for books expected to contain verse
3. Add separator-leak metric (must be zero).

Files to add/update:
- `book_sbd/src/book_sbd/invariants.py`
- `book_sbd/tests/unit/test_invariants.py`
- `apature/sentence_bd/METRICS.md` (new post-run metrics section)

Acceptance gate:
- Invariants pass on batch output.

## Phase 5 - Full Corpus Re-run and Release Packaging

Goal: Regenerate all 19 books with v1.1.0 and verify deterministic output.

Tasks:
1. Run full test suite.
2. Run full batch pipeline on all EPUBs.
3. Run deterministic rerun hash check.
4. Produce delivery zip and update runbook notes.

Files to add/update:
- `apature/sentence_bd/output/*.json` (regenerated)
- `apature/sentence_bd/sbd_output_YYYY-MM-DD.zip` (new release artifact)
- `apature/sentence_bd/RUNBOOK.md` (commands + v1.1.0 notes)

Acceptance gate:
- All tests pass.
- Re-run hashes stable.
- All 19 outputs generated.

## 7) Test Plan (Explicit)

### Unit tests to add
1. Sentence type validity: every sentence has `type in {prose, verse}`.
2. Prose newline normalization: no `\n` in prose sentence text.
3. Verse preservation: verse sentence text keeps internal newlines.
4. Separator filtering: asterisk-only blocks never emitted.
5. Stats consistency: `stats.total_sentences == sum(len(ch.sentences))`.
6. No duplicate conflicting global sentence count key.

### Integration tests to add
1. Alice v1.1.0 regression test from feedback criteria.
2. Batch-level check that separator leakage count is zero.
3. Batch-level check that prose newline leakage is below target threshold.

### Existing tests to keep green
- all current unit and integration tests in `book_sbd/tests/`

## 8) Rerun Procedure (After Implementation)

From `apature/sentence_bd/book_sbd`:

1. `python -m pytest -q`
2. `set PYTHONPATH=src && python -m book_sbd.cli batch "..\\epubs_unpacked\\epubs" --output-dir ".."`
3. `set PYTHONPATH=src && python -m book_sbd.cli eval "tests/fixtures/gold" --epub-dir "..\\epubs_unpacked\\epubs"`
4. deterministic hash check on `..\\output\\*.json` across two batch runs
5. package output zip

## 9) Risks and Mitigations

Risk 1: Verse classifier false positives on wrapped prose.
- Mitigation: deterministic conservative rules + tests on known verse sections.

Risk 2: Span drift from new segmentation logic.
- Mitigation: strengthen invariants and run full integration suite.

Risk 3: Breaking downstream consumers expecting v1.0.0 sentence schema.
- Mitigation: document schema bump and version in README/RUNBOOK.

Risk 4: Overfitting to Alice sample.
- Mitigation: validate across all 19 books and track corpus metrics.

## 10) Rollout and Rollback Strategy

1. Do not overwrite `output/*.json` during first v1.1.0 run.
2. Write candidate outputs to `output_v110_candidate/`.
3. Compare candidate vs current output with:
   - schema checks
   - determinism hashes
   - key corpus metrics (newline leakage, separator leakage, sentence totals)
4. Promote candidate to `output/` only after review pass.
5. Keep previous release zip (`sbd_output_2026-03-03.zip`) as rollback artifact.
6. If regression found after promotion, restore from prior zip and rerun v1.0.0 path.

## 11) Definition of Done

All conditions must be true:
1. `pipeline_version == 1.1.0` in every output JSON.
2. Every sentence has `type` and valid value.
3. Prose newline leakage is near zero; verse line breaks preserved.
4. Decorative asterisk separator sentences are zero.
5. Stats are internally consistent with one authoritative global total sentence field.
6. Full 19-book run succeeds and is deterministic.
7. Test suite passes.

## 12) Execution Checklist (Simpler LLM Operator)

Phase 0 checklist:
1. Add red tests (`test_v110_contract.py`, `test_feedback_alice_v110.py`).
2. Run `python -m pytest -q` and confirm expected failures for v1.1.0 requirements.

Phase 1 checklist:
1. Implement `segment/text_modes.py`.
2. Wire mode handling in `cli.py`.
3. Add/extend unit tests for mode classification and separator filtering.

Phase 2 checklist:
1. Update `punkt_backend.py` to span-native tokenization.
2. Extend `patch_rules.py` with conservative split rule.
3. Re-run tests and confirm span invariants.

Phase 3 checklist:
1. Add sentence `type` in export.
2. Bump versions in `__init__.py` and `pyproject.toml`.
3. Verify stats keys and totals are consistent.

Phase 4 checklist:
1. Add coverage invariant with explicit scope.
2. Add mode-aware metric checks and tests.

Phase 5 checklist:
1. Run full tests.
2. Batch run to `output_v110_candidate/`.
3. Determinism rerun hash check.
4. Promote candidate output after review.
5. Package release zip.
