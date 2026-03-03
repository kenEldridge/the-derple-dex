"""EPUB parser: OPF/spine/nav extraction.

Supports both EPUB2 (toc.ncx) and EPUB3 (nav.xhtml) formats.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from xml.etree import ElementTree as ET


NS = {
    "container": "urn:oasis:names:tc:opendocument:xmlns:container",
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
    "ncx": "http://www.daisy.org/z3986/2005/ncx/",
    "xhtml": "http://www.w3.org/1999/xhtml",
    "epub": "http://www.idpf.org/2007/ops",
}


@dataclass
class NavEntry:
    """A single entry from the NCX/nav table of contents."""
    label: str
    href: str  # relative to OPF directory
    order: int = 0


@dataclass
class SpineItem:
    """A single spine item with its content."""
    idref: str
    href: str  # relative to OPF directory
    content: str = ""  # raw XHTML/HTML string


@dataclass
class EpubData:
    """Parsed EPUB data."""
    spine_items: list[SpineItem] = field(default_factory=list)
    nav_entries: list[NavEntry] = field(default_factory=list)
    opf_dir: str = ""


def parse_epub(epub_path: str) -> EpubData:
    """Parse an EPUB file and extract spine items and nav entries."""
    with zipfile.ZipFile(epub_path, "r") as zf:
        # Step 1: Find OPF path from container.xml
        container_xml = zf.read("META-INF/container.xml")
        container = ET.fromstring(container_xml)
        rootfile = container.find(
            ".//container:rootfile", NS
        )
        opf_path = rootfile.attrib["full-path"]
        opf_dir = str(PurePosixPath(opf_path).parent)
        if opf_dir == ".":
            opf_dir = ""

        # Step 2: Parse OPF
        opf_xml = zf.read(opf_path)
        opf = ET.fromstring(opf_xml)

        # Build manifest map: id -> href
        manifest = {}
        for item in opf.findall(".//opf:manifest/opf:item", NS):
            manifest[item.attrib["id"]] = item.attrib["href"]

        # Build manifest map by href for media-type lookup
        manifest_items = {}
        for item in opf.findall(".//opf:manifest/opf:item", NS):
            manifest_items[item.attrib["id"]] = {
                "href": item.attrib["href"],
                "media-type": item.attrib.get("media-type", ""),
                "properties": item.attrib.get("properties", ""),
            }

        # Step 3: Extract spine items
        spine_items = []
        for itemref in opf.findall(".//opf:spine/opf:itemref", NS):
            idref = itemref.attrib["idref"]
            if idref in manifest:
                href = manifest[idref]
                full_path = f"{opf_dir}/{href}" if opf_dir else href
                try:
                    content = zf.read(full_path).decode("utf-8", errors="replace")
                except KeyError:
                    content = ""
                spine_items.append(SpineItem(idref=idref, href=href, content=content))

        # Step 4: Extract nav entries (try NCX first, then EPUB3 nav)
        nav_entries = _parse_ncx(zf, opf, opf_dir, manifest_items)
        if not nav_entries:
            nav_entries = _parse_epub3_nav(zf, opf, opf_dir, manifest_items)

        return EpubData(
            spine_items=spine_items,
            nav_entries=nav_entries,
            opf_dir=opf_dir,
        )


def _parse_ncx(
    zf: zipfile.ZipFile,
    opf: ET.Element,
    opf_dir: str,
    manifest_items: dict,
) -> list[NavEntry]:
    """Parse NCX table of contents (EPUB2)."""
    # Find NCX file from spine toc attribute or manifest
    spine_el = opf.find(".//opf:spine", NS)
    toc_id = spine_el.attrib.get("toc", "") if spine_el is not None else ""

    ncx_href = None
    if toc_id and toc_id in manifest_items:
        ncx_href = manifest_items[toc_id]["href"]
    else:
        for mid, info in manifest_items.items():
            if info["media-type"] == "application/x-dtbncx+xml":
                ncx_href = info["href"]
                break

    if not ncx_href:
        return []

    ncx_path = f"{opf_dir}/{ncx_href}" if opf_dir else ncx_href
    try:
        ncx_xml = zf.read(ncx_path)
    except KeyError:
        return []

    ncx = ET.fromstring(ncx_xml)
    entries = []
    order = 0
    for navpoint in ncx.iter("{http://www.daisy.org/z3986/2005/ncx/}navPoint"):
        text_el = navpoint.find("ncx:navLabel/ncx:text", NS)
        content_el = navpoint.find("ncx:content", NS)
        if text_el is not None and content_el is not None:
            label = (text_el.text or "").strip()
            href = content_el.attrib.get("src", "")
            if label:
                entries.append(NavEntry(label=label, href=href, order=order))
                order += 1

    return entries


def _parse_epub3_nav(
    zf: zipfile.ZipFile,
    opf: ET.Element,
    opf_dir: str,
    manifest_items: dict,
) -> list[NavEntry]:
    """Parse EPUB3 nav document."""
    nav_href = None
    for mid, info in manifest_items.items():
        if "nav" in info.get("properties", ""):
            nav_href = info["href"]
            break

    if not nav_href:
        return []

    nav_path = f"{opf_dir}/{nav_href}" if opf_dir else nav_href
    try:
        nav_xml = zf.read(nav_path)
    except KeyError:
        return []

    nav = ET.fromstring(nav_xml)
    entries = []
    order = 0

    # Find the toc nav element
    for nav_el in nav.iter("{http://www.w3.org/1999/xhtml}nav"):
        epub_type = nav_el.attrib.get("{http://www.idpf.org/2007/ops}type", "")
        if epub_type == "toc":
            for li in nav_el.iter("{http://www.w3.org/1999/xhtml}li"):
                a = li.find("{http://www.w3.org/1999/xhtml}a")
                if a is not None:
                    label = "".join(a.itertext()).strip()
                    href = a.attrib.get("href", "")
                    if label:
                        entries.append(NavEntry(label=label, href=href, order=order))
                        order += 1

    return entries
