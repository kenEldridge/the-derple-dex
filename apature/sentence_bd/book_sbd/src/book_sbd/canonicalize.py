"""Text canonicalization for chapter units.

Rules (applied in order):
1. Normalize newlines: \\r\\n and \\r -> \\n
2. Remove BOM (U+FEFF)
3. Unicode normalize to NFC
4. Trim trailing whitespace per line
5. Collapse runs of spaces/tabs within lines to single space
6. Normalize 3+ consecutive blank lines to exactly 2
7. Strip leading/trailing whitespace from overall text

Canonicalization is idempotent: canon(canon(x)) == canon(x).
"""

from __future__ import annotations

import re
import unicodedata


def canonicalize(text: str) -> str:
    """Apply all canonicalization rules to text."""
    # 1. Normalize newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Remove BOM
    text = text.replace("\ufeff", "")

    # 3. Unicode NFC normalization
    text = unicodedata.normalize("NFC", text)

    # 4+5. Per-line: trim trailing whitespace, collapse internal spaces/tabs
    lines = text.split("\n")
    processed = []
    for line in lines:
        # Collapse internal whitespace runs to single space
        line = re.sub(r"[ \t]+", " ", line)
        # Trim trailing whitespace (and leading for consistency)
        line = line.rstrip()
        processed.append(line)
    text = "\n".join(processed)

    # 6. Normalize 3+ consecutive blank lines to exactly 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 7. Strip leading/trailing whitespace from overall text
    text = text.strip()

    return text
