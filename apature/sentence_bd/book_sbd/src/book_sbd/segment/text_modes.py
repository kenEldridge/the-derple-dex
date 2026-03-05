"""Text mode classification and normalization.

Classifies text blocks as 'prose' or 'verse' and applies mode-specific
normalization before sentence segmentation.

Separator lines (decorative asterisks) are filtered out entirely.

Two-pass approach:
1. Split on paragraph breaks, filter separators
2. Group consecutive short single-line blocks into verse stanzas
   (handles Gutenberg EPUBs where each verse line is a separate <p>)
3. Classify each group using metric thresholds
"""

from __future__ import annotations

import re

# Separator pattern: lines consisting of 3+ asterisks with optional spaces
_SEPARATOR_RE = re.compile(r"^\s*(?:\*\s*){3,}\s*$")

# Lines that look like structural/non-content markers rather than verse:
# all-caps lines, numbered lists, lines with colons (stage directions, addresses)
_NON_VERSE_LINE_RE = re.compile(
    r"^(?:"
    r"[A-Z][A-Z\s.,!?'\"]{5,}$"  # all-caps line (headings, names)
    r"|.{0,50}:\s*$"              # short lines ending with colon (labels, directions)
    r"|\s*\d+[.)]\s"              # numbered list items
    r")"
)

# Speech attribution verbs — high frequency in dialogue, low in verse/songs.
_ATTRIBUTION_RE = re.compile(
    r"\b(?:said|cried|replied|asked|exclaimed|interrupted|continued|"
    r"remarked|added|began|went\s+on|shouted|screamed|whispered|"
    r"muttered|observed|returned|thought|called)\b",
    re.IGNORECASE,
)

# Max line length to consider "short" for verse grouping
_SHORT_LINE_THRESHOLD = 55

# Relaxed threshold for long runs of consecutive single-line blocks.
# Songs in 19th-century novels often have verse lines of 56-70 chars.
_LONG_RUN_LINE_THRESHOLD = 75

# Min consecutive short single-line blocks to form a verse group
_MIN_VERSE_GROUP = 3

# Min consecutive blocks for the relaxed-threshold second pass
_MIN_LONG_RUN_GROUP = 6


def _is_separator(line: str) -> bool:
    return bool(_SEPARATOR_RE.match(line))


def _looks_like_verse_line(text: str) -> bool:
    """Check if a single-line block looks like it could be a verse line.

    Criteria: short (<=55 chars), not a separator, and has some
    poetic character (indentation, or ends with punctuation/quote,
    or is clearly not a full prose sentence).
    """
    stripped = text.strip()
    if not stripped:
        return False
    normalized = stripped.replace("\u00a0", " ")
    return len(normalized) <= _SHORT_LINE_THRESHOLD


def _classify_block(lines: list[str], short_threshold: int | None = None) -> str:
    """Classify a block of non-empty lines as 'prose' or 'verse'.

    Rules:
    - Normalize NBSP to plain space before checks
    - short_line_ratio = (# lines with len <= threshold) / line_count
    - terminal_punct_ratio = (# lines ending with . , ; : ! ? quote) / line_count
    - indented_ratio = (# lines starting with leading spaces/tabs) / line_count
    - verse when:
        line_count >= 3 AND
        short_line_ratio >= 0.70 AND
        (terminal_punct_ratio >= 0.50 OR indented_ratio >= 0.30)

    Additional guard (nit): if most lines match non-verse patterns
    (all-caps, numbered lists, colon-terminated labels), classify as prose
    even if the metrics otherwise suggest verse.

    Args:
        lines: Non-empty lines of the block.
        short_threshold: Override for line-length threshold (default: _SHORT_LINE_THRESHOLD).
    """
    if len(lines) < 3:
        return "prose"

    threshold = short_threshold if short_threshold is not None else _SHORT_LINE_THRESHOLD

    line_count = len(lines)
    short_count = 0
    terminal_count = 0
    indented_count = 0
    non_verse_count = 0

    terminal_chars = set(".,;:!?\u201d\u201c\u2019\u2018\"'")

    for line in lines:
        # Normalize NBSP
        normalized = line.replace("\u00a0", " ")

        if len(normalized) <= threshold:
            short_count += 1

        stripped = normalized.rstrip()
        if stripped and stripped[-1] in terminal_chars:
            terminal_count += 1

        if normalized and normalized[0] in (" ", "\t", "\u00a0"):
            indented_count += 1

        if _NON_VERSE_LINE_RE.match(normalized):
            non_verse_count += 1

    short_ratio = short_count / line_count
    terminal_ratio = terminal_count / line_count
    indented_ratio = indented_count / line_count
    non_verse_ratio = non_verse_count / line_count

    # Guard: if majority of lines look like non-verse structural content,
    # classify as prose regardless of metrics
    if non_verse_ratio >= 0.50:
        return "prose"

    # Guard: if many lines contain speech attribution verbs ("said", "cried", etc.),
    # this is dialogue, not verse. Songs/poems rarely have attribution in >40% of lines.
    attribution_count = sum(1 for line in lines if _ATTRIBUTION_RE.search(line))
    if attribution_count / line_count >= 0.40:
        return "prose"

    if (
        short_ratio >= 0.70
        and (terminal_ratio >= 0.50 or indented_ratio >= 0.30)
    ):
        return "verse"

    return "prose"


def classify_and_normalize(text: str) -> list[dict]:
    """Split text into blocks, classify each, and normalize.

    Two-pass approach:
    Pass 1: Split on paragraph breaks, filter separators, collect raw blocks
    Pass 2: Group consecutive short single-line blocks and classify as
            verse stanzas (handles Gutenberg's one-line-per-<p> verse format)

    Returns list of dicts with keys:
    - 'text': the normalized block text
    - 'type': 'prose' or 'verse'
    - 'start': character offset of this block in the original text
    - 'end': character offset of block end in the original text

    Separator blocks are dropped entirely (not returned).
    """
    # Pass 1: Split and collect raw blocks
    raw_blocks = re.split(r"\n\n+", text)
    parsed = []
    offset = 0

    for raw_block in raw_blocks:
        block_start = text.find(raw_block, offset)
        if block_start == -1:
            block_start = offset
        block_end = block_start + len(raw_block)
        offset = block_end

        lines = [ln for ln in raw_block.split("\n") if ln.strip()]
        if not lines:
            continue

        # Filter separators
        if all(_is_separator(ln) for ln in lines):
            continue

        content_lines = [ln for ln in lines if not _is_separator(ln)]
        if not content_lines:
            continue

        is_single = len(content_lines) == 1
        line_len = len(content_lines[0].strip().replace("\u00a0", " ")) if is_single else 0
        parsed.append({
            "lines": content_lines,
            "start": block_start,
            "end": block_end,
            "is_single_short": is_single and line_len <= _SHORT_LINE_THRESHOLD,
            "is_single_long_run": is_single and line_len <= _LONG_RUN_LINE_THRESHOLD,
        })

    # Pass 2: Group consecutive short single-line blocks into verse candidates
    # Uses strict threshold (_SHORT_LINE_THRESHOLD) and min group of 3
    intermediate = []
    i = 0
    while i < len(parsed):
        block = parsed[i]

        if block["is_single_short"]:
            # Look ahead for a run of consecutive short single-line blocks
            group = [block]
            j = i + 1
            while j < len(parsed) and parsed[j]["is_single_short"]:
                group.append(parsed[j])
                j += 1

            if len(group) >= _MIN_VERSE_GROUP:
                # Combine into a single block and classify
                all_lines = []
                for g in group:
                    all_lines.extend(g["lines"])
                block_type = _classify_block(all_lines)
                if block_type == "verse":
                    normalized = "\n".join(all_lines)
                    intermediate.append({
                        "text": normalized,
                        "type": "verse",
                        "start": group[0]["start"],
                        "end": group[-1]["end"],
                        "_single_prose": False,
                    })
                    i = j
                    continue
                # If classifier says prose, fall through and emit individually

            # Not enough for a verse group or classifier rejected — emit individually
            for g in group:
                normalized = " ".join(ln.strip() for ln in g["lines"])
                intermediate.append({
                    "text": normalized,
                    "type": "prose",
                    "start": g["start"],
                    "end": g["end"],
                    "_single_prose": True,
                    "_lines": g["lines"],
                    "_is_single_long_run": g["is_single_long_run"],
                })
            i = j
            continue

        # Multi-line block or single-line block that wasn't short enough for Pass 2
        block_type = _classify_block(block["lines"])
        if block_type == "prose":
            normalized = " ".join(ln.strip() for ln in block["lines"])
        else:
            normalized = "\n".join(block["lines"])

        # Flag single-line prose blocks within relaxed threshold for Pass 3
        is_long_run_candidate = (
            block_type == "prose"
            and block.get("is_single_long_run", False)
        )
        intermediate.append({
            "text": normalized,
            "type": block_type,
            "start": block["start"],
            "end": block["end"],
            "_single_prose": is_long_run_candidate,
            "_is_single_long_run": is_long_run_candidate,
            "_lines": block["lines"] if is_long_run_candidate else None,
        })
        i += 1

    # Pass 3: Relaxed grouping for long runs of single-line blocks.
    # Songs in 19th-century novels often have verse lines of 56-75 chars,
    # exceeding the strict threshold. For long runs (>=6 consecutive),
    # re-attempt verse classification with relaxed line-length threshold.
    results = []
    i = 0
    while i < len(intermediate):
        block = intermediate[i]

        if block["_single_prose"] and block.get("_is_single_long_run"):
            # Look ahead for a long run of consecutive single-line prose blocks
            group = [block]
            j = i + 1
            while j < len(intermediate) and intermediate[j]["_single_prose"] \
                    and intermediate[j].get("_is_single_long_run"):
                group.append(intermediate[j])
                j += 1

            if len(group) >= _MIN_LONG_RUN_GROUP:
                all_lines = []
                for g in group:
                    all_lines.extend(g["_lines"])
                block_type = _classify_block(all_lines, short_threshold=_LONG_RUN_LINE_THRESHOLD)
                if block_type == "verse":
                    normalized = "\n".join(ln.strip() for ln in all_lines)
                    results.append({
                        "text": normalized,
                        "type": "verse",
                        "start": group[0]["start"],
                        "end": group[-1]["end"],
                    })
                    i = j
                    continue

            # Not a verse run — emit as-is
            for g in group:
                results.append({
                    "text": g["text"],
                    "type": g["type"],
                    "start": g["start"],
                    "end": g["end"],
                })
            i = j
            continue

        # Emit as-is (already classified in Pass 2)
        results.append({
            "text": block["text"],
            "type": block["type"],
            "start": block["start"],
            "end": block["end"],
        })
        i += 1

    return results


def apply_text_modes(canonical_text: str) -> tuple[str, list[dict]]:
    """Apply text mode classification to canonical text.

    Returns:
        (processed_text, block_metadata)

    processed_text: the full text reassembled with mode-appropriate normalization.
        Paragraph breaks (double newlines) are preserved between blocks.
    block_metadata: list of dicts describing each block's type and span in
        the processed text.
    """
    blocks = classify_and_normalize(canonical_text)
    if not blocks:
        return "", []

    parts = []
    metadata = []
    current_offset = 0

    for i, block in enumerate(blocks):
        if i > 0:
            parts.append("\n\n")
            current_offset += 2

        block_start = current_offset
        parts.append(block["text"])
        current_offset += len(block["text"])

        metadata.append({
            "type": block["type"],
            "start": block_start,
            "end": current_offset,
        })

    processed = "".join(parts)
    return processed, metadata


def get_sentence_type(sentence_start: int, sentence_end: int, block_metadata: list[dict]) -> str:
    """Determine sentence type based on which block it falls in.

    Uses the midpoint of the sentence span to find the containing block.
    Falls back to 'prose' if no block contains the sentence.
    """
    midpoint = (sentence_start + sentence_end) // 2
    for meta in block_metadata:
        if meta["start"] <= midpoint < meta["end"]:
            return meta["type"]
    return "prose"
