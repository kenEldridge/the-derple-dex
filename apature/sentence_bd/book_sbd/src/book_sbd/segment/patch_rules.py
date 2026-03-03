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


def apply_patch_rules(
    canonical_text: str,
    spans: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    """Apply all patch rules to baseline spans.

    Args:
        canonical_text: The canonical chapter text.
        spans: Baseline sentence spans from segmenter.

    Returns:
        Patched spans (sorted, non-overlapping).
    """
    spans = _merge_abbreviation_splits(canonical_text, spans)
    spans = _merge_closing_quotes(canonical_text, spans)
    spans = _merge_ellipsis_splits(canonical_text, spans)
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
