"""Chapter unit detection and extraction from parsed EPUB data.

Uses NCX/nav TOC as primary source, with heading heuristics as fallback
for books where multiple chapters share a single spine document.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urldefrag

from .epub_parser import EpubData, NavEntry, SpineItem
from .boilerplate import is_boilerplate_spine_doc, strip_gutenberg_text


@dataclass
class ChapterUnit:
    """A chapter unit with its extracted text."""
    number: int
    label: str | None
    text: str


class _TextExtractor(HTMLParser):
    """Extract visible text from HTML, stripping tags."""

    def __init__(self):
        super().__init__()
        self._pieces: list[str] = []
        self._skip_depth = 0
        self._skip_tags = {"script", "style", "head"}
        self._block_tags = {
            "p", "div", "h1", "h2", "h3", "h4", "h5", "h6",
            "blockquote", "pre", "li", "tr", "br", "hr",
        }

    def handle_starttag(self, tag: str, attrs: list) -> None:
        tag = tag.lower()
        if tag in self._skip_tags:
            self._skip_depth += 1
        if tag in self._block_tags and self._pieces and self._pieces[-1] != "\n":
            self._pieces.append("\n")
        if tag == "br":
            self._pieces.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self._skip_tags:
            self._skip_depth = max(0, self._skip_depth - 1)
        if tag in self._block_tags and self._pieces and self._pieces[-1] != "\n":
            self._pieces.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._pieces.append(data)

    def get_text(self) -> str:
        return "".join(self._pieces)


def html_to_text(html: str) -> str:
    """Convert HTML to plain text, preserving paragraph structure."""
    extractor = _TextExtractor()
    extractor.feed(html)
    return extractor.get_text()


# Patterns for entries to always SKIP (front/back matter, non-content)
_SKIP_PATTERNS = [
    re.compile(r"(?i)^\s*contents?\s*$"),
    re.compile(r"(?i)^\s*table\s+of\s+contents?\s*$"),
    re.compile(r"(?i)(?:full\s+)?project\s+gutenberg"),
    re.compile(r"(?i)^\s*cover\s*$"),
    re.compile(r"(?i)^\s*title\s*page\s*$"),
    re.compile(r"(?i)^\s*copyright\s*"),
    re.compile(r"(?i)^\s*appendix\b"),
    re.compile(r"(?i)^\s*glossary\s*$"),
    re.compile(r"(?i)^\s*notes?\s*$"),
    re.compile(r"(?i)^\s*index\s*$"),
    re.compile(r"(?i)^\s*pages?\s*$"),
    re.compile(r"(?i)^\s*paragraphs?\s+with\s+first\s+lines?"),
    re.compile(r"(?i)^\s*footnotes?\s*:?\s*$"),
    re.compile(r"(?i)^\s*illustrations?\s*$"),
    re.compile(r"(?i)^\s*list\s+of\s+illustrations"),
    re.compile(r"(?i)^\s*preface\s+to\s+(the\s+)?project\s+gutenberg"),
    re.compile(r"(?i)^\s*dedication\s*$"),
    re.compile(r"(?i)^\s*colophon\s*$"),
    re.compile(r"(?i)^\s*errata\s*$"),
]

# Per-book configuration for tricky structures.
# Each entry specifies how to select chapters from nav entries.
# "pattern": regex that chapter labels must match to be included
# "skip_pattern": regex for entries to exclude even if they match
# "include_prefixes": if set, only include entries starting with these
BOOK_OVERRIDES: dict[str, dict] = {
    "pride-and-prejudice": {
        # NCX labels embed illustration text; match "Chapter" anywhere in label
        "pattern": r"(?i)CHAPTER\s+[IVXLCDM]+",
    },
    "crime-and-punishment": {
        # Keep only "PART ... CHAPTER" entries, not bare Part headers
        "pattern": r"(?i)(?:CHAPTER|EPILOGUE)",
    },
    "don-quixote": {
        # Keep numbered chapters, skip CONTENTS, VOLUME headers
        "pattern": r"(?i)^CHAPTER\s+[IVXLCDM]+",
    },
    "the-adventures-of-sherlock-holmes": {
        # Keep the 12 story entries (I. through XII.), not their sub-sections
        "pattern": r"^[IVXLCDM]+\.\s+[A-Z]",
    },
    "the-art-of-war": {
        # Keep "Chapter I" through "Chapter XIII" only
        "pattern": r"(?i)^Chapter\s+[IVXLCDM]+",
    },
    "the-great-gatsby": {
        # Chapters are Roman numerals: I through IX
        "pattern": r"^[IVXLCDM]+$",
    },
    "the-iliad": {
        # Keep "BOOK I" through "BOOK XXIV"
        "pattern": r"(?i)^BOOK\s+[IVXLCDM]+",
    },
    "the-odyssey": {
        # Keep "Book I" through "Book XXIV"
        "pattern": r"(?i)^Book\s+[IVXLCDM]+",
    },
    "the-republic": {
        # Keep "BOOK I." through "BOOK X."
        "pattern": r"(?i)^BOOK\s+[IVXLCDM]+",
    },
    "the-count-of-monte-cristo-illustrated": {
        # Keep numbered chapters, skip VOLUME headers and FOOTNOTES
        "pattern": r"(?i)^Chapter\s+\d+",
    },
    "meditations": {
        # Keep "THE FIRST BOOK" through "THE TWELFTH BOOK"
        "pattern": r"(?i)^THE\s+\w+\s+BOOK$",
    },
    "the-three-musketeers": {
        # Keep "Chapter N." entries and EPILOGUE
        "pattern": r"(?i)^(?:Chapter\s+[IVXLCDM]+|EPILOGUE)",
    },
    "war-and-peace": {
        # Keep "CHAPTER" entries only, skip BOOK/PART headers and EPILOGUE headers
        "pattern": r"(?i)^CHAPTER\s+[IVXLCDM]+",
    },
    "moby-dick-or-the-whale": {
        # Keep "CHAPTER" entries only
        "pattern": r"(?i)^CHAPTER\s+\d+",
    },
    "divine-comedy-dantes-inferno": {
        # Keep Canto entries only
        "pattern": r"(?i)Canto\s+[IVXLCDM]+",
    },
    "frankenstein-or-the-modern-prometheus": {
        # Keep Letters and Chapters
        "pattern": r"(?i)^(?:Letter\s+\d+|Chapter\s+\d+)$",
    },
    "dracula": {
        # Keep "CHAPTER" entries only
        "pattern": r"(?i)^CHAPTER\s+[IVXLCDM]+",
    },
    "grimms-fairy-tales": {
        # Keep everything except the title entry and "THE BROTHERS GRIMM FAIRY TALES"
        "skip_pattern": r"(?i)^(?:Grimms|THE\s+BROTHERS\s+GRIMM)",
    },
    "alices-adventures-in-wonderland": {
        "pattern": r"(?i)^CHAPTER\s+[IVXLCDM]+",
    },
}


def _is_skip_entry(label: str) -> bool:
    """Check if a nav label should be skipped (not a content chapter)."""
    for pat in _SKIP_PATTERNS:
        if pat.search(label):
            return True
    return False


def _get_spine_href_map(epub_data: EpubData) -> dict[str, int]:
    """Map base hrefs (without fragments) to spine item indices."""
    href_map = {}
    for i, item in enumerate(epub_data.spine_items):
        href_map[item.href] = i
    return href_map


def extract_chapters(epub_data: EpubData, slug: str = "") -> list[ChapterUnit]:
    """Extract chapter units from parsed EPUB data.

    Args:
        epub_data: Parsed EPUB data.
        slug: Book slug for per-book overrides.
    """
    href_map = _get_spine_href_map(epub_data)
    content_entries = _filter_content_entries(epub_data.nav_entries, slug)

    if not content_entries:
        return _fallback_spine_chapters(epub_data)

    chapters = _nav_to_chapters(content_entries, epub_data, href_map)

    for i, ch in enumerate(chapters):
        ch.number = i + 1

    return chapters


def _filter_content_entries(entries: list[NavEntry], slug: str) -> list[NavEntry]:
    """Filter nav entries to only content chapters."""
    override = BOOK_OVERRIDES.get(slug)

    if override and "pattern" in override:
        # Use explicit pattern matching
        pat = re.compile(override["pattern"])
        filtered = [e for e in entries if pat.search(e.label)]
    elif override and "skip_pattern" in override:
        # Skip matching entries, keep the rest (minus standard skips)
        skip_pat = re.compile(override["skip_pattern"])
        filtered = [
            e for e in entries
            if not _is_skip_entry(e.label) and not skip_pat.search(e.label)
        ]
    else:
        # General filtering: remove standard skips
        filtered = [e for e in entries if not _is_skip_entry(e.label)]
        # Remove title-like first entry if it doesn't look like a chapter
        if filtered and _looks_like_title_entry(filtered[0].label):
            filtered = filtered[1:]

    return filtered


def _looks_like_title_entry(label: str) -> bool:
    """Check if a nav label looks like a book title, not a chapter."""
    lower = label.lower().strip()
    chapter_indicators = [
        "chapter", "book ", "canto", "part ", "letter",
        "act ", "scene", "section",
    ]
    for ind in chapter_indicators:
        if ind in lower:
            return False
    # Numbered entries are chapters
    if re.match(r"^[IVXLCDM]+\.?\s", label):
        return False
    if re.match(r"^\d+\.?\s", label):
        return False
    return True


def _nav_to_chapters(
    entries: list[NavEntry],
    epub_data: EpubData,
    href_map: dict[str, int],
) -> list[ChapterUnit]:
    """Convert nav entries to chapter units with extracted text."""
    chapters = []
    spine_items = epub_data.spine_items

    for i, entry in enumerate(entries):
        base_href, fragment = urldefrag(entry.href)
        spine_idx = href_map.get(base_href)

        if spine_idx is None:
            continue

        item = spine_items[spine_idx]

        # Don't skip entire spine docs as boilerplate when we have a fragment —
        # the doc may contain both PG boilerplate and real chapter content.
        # Instead we extract by fragment and strip inline boilerplate later.
        if is_boilerplate_spine_doc(item.content) and not fragment:
            continue

        next_entry = entries[i + 1] if i + 1 < len(entries) else None
        next_base_href = urldefrag(next_entry.href)[0] if next_entry else None
        same_file_next = next_base_href == base_href if next_base_href else False

        if fragment and same_file_next:
            next_fragment = urldefrag(next_entry.href)[1]
            text = _extract_between_fragments(item.content, fragment, next_fragment)
        elif fragment:
            text = _extract_from_fragment(item.content, fragment)
        else:
            if same_file_next:
                next_fragment = urldefrag(next_entry.href)[1]
                if next_fragment:
                    text = _extract_until_fragment(item.content, next_fragment)
                else:
                    text = html_to_text(item.content)
            else:
                text = html_to_text(item.content)

        # Always strip gutenberg markers if present
        if _has_gutenberg_markers(text):
            text = strip_gutenberg_text(text)

        # Strip chapter heading from body text
        label = entry.label.strip() if entry.label else None
        text = _strip_heading_from_text(text, label)
        text = text.strip()

        if text and len(text) >= 10:
            chapters.append(ChapterUnit(
                number=0,
                label=label,
                text=text,
            ))

    return chapters


def _strip_heading_from_text(text: str, label: str | None) -> str:
    """Strip the chapter heading from the beginning of body text.

    The heading may appear as:
    - The full label on one line
    - Parts of the label on separate lines (e.g. "CHAPTER I" then "Down the Rabbit-Hole")
    - A shortened version of the label

    We strip lines from the start that match components of the label,
    then strip any remaining leading blank lines.
    """
    if not label or not text:
        return text

    # Normalize for comparison
    label_clean = re.sub(r"\s+", " ", label).strip()
    label_words = set(label_clean.upper().split())

    lines = text.split("\n")
    strip_until = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            # Blank line — keep scanning past blanks between heading parts
            continue

        stripped_upper = stripped.upper()
        stripped_words = set(re.sub(r"\s+", " ", stripped_upper).split())

        # Check if this line is part of the heading:
        # 1. Line matches or is contained in the label
        if stripped_upper in label_clean.upper():
            strip_until = i + 1
            continue

        # 2. Label contains this line's words (for multi-line headings)
        if stripped_words and stripped_words.issubset(label_words):
            strip_until = i + 1
            continue

        # 3. Line is a common heading pattern that appeared before content
        #    (e.g. bare roman numerals, "CHAPTER X", section markers)
        if re.match(r"^(?:CHAPTER|BOOK|CANTO|PART|LETTER)\s+[IVXLCDM\d]+\.?$",
                     stripped_upper):
            strip_until = i + 1
            continue
        if re.match(r"^[IVXLCDM]+\.?$", stripped):
            strip_until = i + 1
            continue

        # Not a heading line — stop scanning
        break

    if strip_until > 0:
        text = "\n".join(lines[strip_until:])

    return text


def _has_gutenberg_markers(text: str) -> bool:
    upper = text.upper()
    return (
        "*** START OF" in upper
        or "*** END OF" in upper
        or "PROJECT GUTENBERG" in upper
    )


def _extract_between_fragments(html: str, frag_start: str, frag_end: str) -> str:
    start_pos = _find_fragment_pos(html, frag_start)
    end_pos = _find_fragment_pos(html, frag_end)
    if start_pos is None:
        return ""
    if end_pos is None:
        return html_to_text(html[start_pos:])
    return html_to_text(html[start_pos:end_pos])


def _extract_from_fragment(html: str, fragment: str) -> str:
    pos = _find_fragment_pos(html, fragment)
    if pos is None:
        return html_to_text(html)
    return html_to_text(html[pos:])


def _extract_until_fragment(html: str, fragment: str) -> str:
    pos = _find_fragment_pos(html, fragment)
    if pos is None:
        return html_to_text(html)
    return html_to_text(html[:pos])


def _find_fragment_pos(html: str, fragment: str) -> int | None:
    if not fragment:
        return None
    patterns = [
        rf'id\s*=\s*"{re.escape(fragment)}"',
        rf"id\s*=\s*'{re.escape(fragment)}'",
        rf'name\s*=\s*"{re.escape(fragment)}"',
        rf"name\s*=\s*'{re.escape(fragment)}'",
    ]
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            tag_start = html.rfind("<", 0, m.start())
            return tag_start if tag_start >= 0 else m.start()
    return None


def _fallback_spine_chapters(epub_data: EpubData) -> list[ChapterUnit]:
    """Fallback: use non-boilerplate spine docs as chapters."""
    chapters = []
    num = 1
    for item in epub_data.spine_items:
        if is_boilerplate_spine_doc(item.content):
            continue
        text = html_to_text(item.content)
        text = strip_gutenberg_text(text) if _has_gutenberg_markers(text) else text
        text = text.strip()
        if text and len(text) >= 10:
            chapters.append(ChapterUnit(number=num, label=None, text=text))
            num += 1
    return chapters
