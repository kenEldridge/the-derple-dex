"""Gutenberg boilerplate detection and removal."""

from __future__ import annotations

import re

# Markers that indicate Gutenberg boilerplate (case-insensitive matching)
START_MARKERS = [
    "*** START OF THE PROJECT GUTENBERG EBOOK",
    "*** START OF THIS PROJECT GUTENBERG EBOOK",
    "***START OF THE PROJECT GUTENBERG EBOOK",
    "***START OF THIS PROJECT GUTENBERG EBOOK",
]

END_MARKERS = [
    "*** END OF THE PROJECT GUTENBERG EBOOK",
    "*** END OF THIS PROJECT GUTENBERG EBOOK",
    "***END OF THE PROJECT GUTENBERG EBOOK",
    "***END OF THIS PROJECT GUTENBERG EBOOK",
]

LICENSE_MARKERS = [
    "THE FULL PROJECT GUTENBERG LICENSE",
    "FULL LICENSE",
]

# Markers that indicate a spine doc is boilerplate
SPINE_BOILERPLATE_MARKERS = [
    "project gutenberg",
    "www.gutenberg.org",
    "gutenberg.org/license",
    "the full project gutenberg license",
    "start of the project gutenberg",
    "end of the project gutenberg",
]


def is_boilerplate_spine_doc(content: str) -> bool:
    """Check if a spine document is primarily Gutenberg boilerplate.

    Returns True for cover wrappers, PG headers, and PG license footers.
    """
    lower = content.lower()

    # Check for license/PG-heavy documents
    pg_marker_count = sum(1 for m in SPINE_BOILERPLATE_MARKERS if m in lower)
    if pg_marker_count >= 2:
        return True

    # Check for start/end markers
    for marker in START_MARKERS + END_MARKERS:
        if marker.lower() in lower:
            return True

    # Check for license page
    for marker in LICENSE_MARKERS:
        if marker.lower() in lower:
            return True

    return False


def strip_gutenberg_text(text: str) -> str:
    """Strip Gutenberg header and footer from text content.

    Removes everything before the START marker line and everything
    from the END marker line onward.
    """
    lines = text.split("\n")
    start_idx = 0
    end_idx = len(lines)

    # Find start marker
    for i, line in enumerate(lines):
        upper = line.strip().upper()
        for marker in START_MARKERS:
            if marker.upper() in upper:
                start_idx = i + 1
                break

    # Find end marker (search from end)
    for i in range(len(lines) - 1, -1, -1):
        upper = lines[i].strip().upper()
        for marker in END_MARKERS:
            if marker.upper() in upper:
                end_idx = i
                break

    result = "\n".join(lines[start_idx:end_idx])
    return result.strip()
