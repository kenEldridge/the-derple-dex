"""Post-segmentation patch rules for improving sentence boundary detection.

Pipeline: baseline_spans -> apply_patch_rules(text, spans) -> final_spans

Each rule is applied in order. Rules must preserve sorted, non-overlapping
span invariant and not introduce empty sentences.
"""

from __future__ import annotations

import re


# Common abbreviations that should NOT trigger sentence breaks
ABBREVIATIONS = {
    "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Rev.", "Gen.", "Col.", "Sgt.",
    "St.", "Jr.", "Sr.", "Ltd.", "Inc.", "Corp.", "Co.", "vs.", "etc.",
    "Vol.", "No.", "Fig.", "Ch.", "Pt.", "Dept.", "Univ.",
    "Jan.", "Feb.", "Mar.", "Apr.", "Jun.", "Jul.", "Aug.",
    "Sep.", "Sept.", "Oct.", "Nov.", "Dec.",
    "Ave.", "Blvd.", "Rd.", "Mt.", "Ft.",
    "i.e.", "e.g.", "viz.", "cf.",
}

# Pre-compile for fast lookup
_ABBREV_LOWER = {a.lower() for a in ABBREVIATIONS}

# Smart quote characters
_OPEN_QUOTES = {"\u201c", "\u2018"}   # " '
_CLOSE_QUOTES = {"\u201d", "\u2019"}  # " '


def apply_patch_rules(
    canonical_text: str,
    spans: list[tuple[int, int]],
    block_metadata: list[dict] | None = None,
) -> list[tuple[int, int]]:
    """Apply all patch rules to baseline spans.

    Args:
        canonical_text: The canonical chapter text.
        spans: Baseline sentence spans from segmenter.
        block_metadata: Optional list of block dicts with 'type', 'start', 'end'
            from text mode classification. Used by quote-aware merge to skip
            verse blocks.

    Returns:
        Patched spans (sorted, non-overlapping).
    """
    spans = _merge_abbreviation_splits(canonical_text, spans)
    spans = _merge_closing_quotes(canonical_text, spans)
    spans = _merge_ellipsis_splits(canonical_text, spans)
    spans = _merge_exclamation_continuations(canonical_text, spans)
    spans = _merge_quoted_discourse(canonical_text, spans, block_metadata)
    spans = _consolidate_short_verse_blocks(canonical_text, spans, block_metadata)
    return spans


def _merge_abbreviation_splits(
    text: str, spans: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    """Merge spans that were incorrectly split after abbreviations.

    If span N ends with a known abbreviation and span N+1 starts with
    a lowercase letter, merge them.
    """
    if len(spans) <= 1:
        return spans

    merged = [spans[0]]
    for i in range(1, len(spans)):
        prev_s, prev_e = merged[-1]
        curr_s, curr_e = spans[i]

        prev_text = text[prev_s:prev_e].rstrip()
        curr_text = text[curr_s:curr_e].lstrip()

        # Check if previous span ends with abbreviation
        should_merge = False
        for abbrev in _ABBREV_LOWER:
            if prev_text.lower().endswith(abbrev):
                # Only merge if next sentence starts with lowercase
                if curr_text and curr_text[0].islower():
                    should_merge = True
                break

        if should_merge:
            # Merge: extend previous span to cover current
            merged[-1] = (prev_s, curr_e)
        else:
            merged.append((curr_s, curr_e))

    return merged


def _merge_closing_quotes(
    text: str, spans: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    """Merge orphaned closing quotes/brackets with the previous sentence.

    If a span is very short (< 5 chars) and consists mostly of closing
    punctuation/quotes, merge it with the previous span.
    """
    if len(spans) <= 1:
        return spans

    closing_pattern = re.compile(r'^[\s\'""\u201c\u201d\u2018\u2019)\]}>.,;:!?\-]+$')

    merged = [spans[0]]
    for i in range(1, len(spans)):
        curr_s, curr_e = spans[i]
        curr_text = text[curr_s:curr_e]

        if len(curr_text.strip()) <= 4 and closing_pattern.match(curr_text.strip()):
            # Merge with previous
            prev_s, _ = merged[-1]
            merged[-1] = (prev_s, curr_e)
        else:
            merged.append((curr_s, curr_e))

    return merged


def _merge_ellipsis_splits(
    text: str, spans: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    """Merge spans split at ellipsis points (...) when they shouldn't be.

    If a span ends with '...' and the next begins with a lowercase letter,
    merge them as ellipsis usually indicates continuation.
    """
    if len(spans) <= 1:
        return spans

    merged = [spans[0]]
    for i in range(1, len(spans)):
        prev_s, prev_e = merged[-1]
        curr_s, curr_e = spans[i]

        prev_text = text[prev_s:prev_e].rstrip()
        curr_text = text[curr_s:curr_e].lstrip()

        if (prev_text.endswith("...") or prev_text.endswith("\u2026")) and \
           curr_text and curr_text[0].islower():
            merged[-1] = (prev_s, curr_e)
        else:
            merged.append((curr_s, curr_e))

    return merged


def _merge_exclamation_continuations(
    text: str, spans: list[tuple[int, int]]
) -> list[tuple[int, int]]:
    """Merge spans split at mid-sentence exclamation marks.

    If a span ends with '!' (but is not a complete quoted sentence) and
    the next span begins with a lowercase letter, merge them. Catches
    onomatopoeia and interjections like "thump!", "splash!", "Alas!".
    """
    if len(spans) <= 1:
        return spans

    merged = [spans[0]]
    for i in range(1, len(spans)):
        prev_s, prev_e = merged[-1]
        curr_s, curr_e = spans[i]

        prev_text = text[prev_s:prev_e].rstrip()
        curr_text = text[curr_s:curr_e].lstrip()

        if prev_text.endswith("!") and curr_text and curr_text[0].islower():
            merged[-1] = (prev_s, curr_e)
        else:
            merged.append((curr_s, curr_e))

    return merged


def _is_verse_span(start: int, end: int, block_metadata: list[dict] | None) -> bool:
    """Check if a span falls within a verse block."""
    if not block_metadata:
        return False
    midpoint = (start + end) // 2
    for meta in block_metadata:
        if meta["start"] <= midpoint < meta["end"]:
            return meta.get("type") == "verse"
    return False


def _local_quote_depth(text: str, span_start: int, span_end: int) -> int:
    """Compute quote depth from the start of the current paragraph to span_end.

    Counts open vs close smart double quotes within the current paragraph
    (delimited by \\n\\n). Returns the net open count.
    """
    # Find paragraph start: last \n\n before span_start
    para_break = text.rfind("\n\n", 0, span_start)
    para_start = para_break + 2 if para_break != -1 else 0

    local = text[para_start:span_end]
    return local.count("\u201c") - local.count("\u201d")


def _merge_quoted_discourse(
    text: str,
    spans: list[tuple[int, int]],
    block_metadata: list[dict] | None = None,
) -> list[tuple[int, int]]:
    """Merge spans that were split inside continuous quoted discourse.

    Punkt splits at ! ? . inside quotation marks, producing fragments
    like "Oh dear!" as separate sentences when they should remain part
    of the enclosing quoted passage.

    Algorithm:
    - For each pair of consecutive spans, compute the local double-quote
      depth (open minus close) from the current paragraph start to the
      end of span N.
    - If depth > 0 (we're inside an open quote), merge with span N+1.

    Guards (do NOT merge):
    - Paragraph break (\\n\\n) between spans.
    - Either span is classified as verse.
    """
    if len(spans) <= 1:
        return spans

    merged = [spans[0]]
    for i in range(1, len(spans)):
        prev_s, prev_e = merged[-1]
        curr_s, curr_e = spans[i]

        # Guard: paragraph break between spans
        gap = text[prev_e:curr_s]
        if "\n\n" in gap:
            merged.append((curr_s, curr_e))
            continue

        # Guard: verse spans
        if _is_verse_span(prev_s, prev_e, block_metadata) or \
           _is_verse_span(curr_s, curr_e, block_metadata):
            merged.append((curr_s, curr_e))
            continue

        # Check local quote depth at end of previous span
        depth = _local_quote_depth(text, prev_s, prev_e)

        if depth > 0:
            # Inside an open quote — merge
            merged[-1] = (prev_s, curr_e)
        else:
            merged.append((curr_s, curr_e))

    return merged


# Max verse-block line count eligible for whole-block consolidation.
# Blocks with <= this many lines become a single sentence.
# Above this threshold, internal sentence boundaries are preserved.
# Tuned to capture short songs/stanzas (Alice) without collapsing epic cantos (Iliad).
_SHORT_VERSE_MAX_LINES = 8


def _consolidate_short_verse_blocks(
    text: str,
    spans: list[tuple[int, int]],
    block_metadata: list[dict] | None = None,
) -> list[tuple[int, int]]:
    """Merge all sentence spans within short verse blocks into single spans.

    Short verse blocks (songs, stanzas, epigraphs with <= 8 lines) are treated
    as atomic sentence units. Longer verse blocks (epic cantos, long poems)
    keep their internal sentence boundaries.
    """
    if not block_metadata or len(spans) <= 1:
        return spans

    # Identify short verse blocks
    short_verse_ranges = []
    for meta in block_metadata:
        if meta.get("type") != "verse":
            continue
        block_text = text[meta["start"]:meta["end"]]
        line_count = block_text.count("\n") + 1
        if line_count <= _SHORT_VERSE_MAX_LINES:
            short_verse_ranges.append((meta["start"], meta["end"]))

    if not short_verse_ranges:
        return spans

    # Merge spans that fall within the same short verse block
    merged = []
    i = 0
    while i < len(spans):
        s, e = spans[i]
        mid = (s + e) // 2

        # Check if this span is in a short verse block
        in_block = None
        for block_start, block_end in short_verse_ranges:
            if block_start <= mid < block_end:
                in_block = (block_start, block_end)
                break

        if in_block is None:
            merged.append((s, e))
            i += 1
            continue

        # Absorb all consecutive spans within this same block
        block_start, block_end = in_block
        group_start = s
        group_end = e
        i += 1
        while i < len(spans):
            ns, ne = spans[i]
            nmid = (ns + ne) // 2
            if block_start <= nmid < block_end:
                group_end = ne
                i += 1
            else:
                break

        merged.append((group_start, group_end))

    return merged
