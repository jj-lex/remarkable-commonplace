"""Book details and passage text, read from the files the tablet keeps for each book."""
import json
import re
import unicodedata
import zipfile
from pathlib import Path

import pymupdf

TABLET_PAGE_W = 1404  # tablet scene units; x runs from -702 to 702, y from 0 down


def clean_title(name: str) -> str:
    if " -- " in name:
        name = name.split(" -- ")[0]
    name = re.sub(r"\.(pdf|epub)$", "", name, flags=re.I)
    name = re.sub(r"\s*\(.*?\)\s*$", "", name).strip()
    return name.split(": ")[0].strip() or "Untitled"


def details(folder: Path, book_id: str, visible_name: str, logged_author: str = "") -> dict:
    """Title, author, publisher, year from the tablet's metadata and the EPUB itself."""
    title, authors, publisher, year = "", [], "", ""
    content = folder / f"{book_id}.content"
    if content.exists():
        try:
            dm = json.loads(content.read_text()).get("documentMetadata") or {}
            title = dm.get("title", "") or ""
            authors = [a for a in (dm.get("authors") or []) if a]
            publisher = dm.get("publisher", "") or ""
            year = (dm.get("publicationDate", "") or "")[:4]
        except (json.JSONDecodeError, OSError):
            pass
    epub = folder / f"{book_id}.epub"
    if epub.exists() and (not title or not authors):
        try:
            z = zipfile.ZipFile(epub)
            opf = next(n for n in z.namelist() if n.endswith(".opf"))
            x = z.read(opf).decode("utf8", "ignore")
            title = title or (re.findall(r"<dc:title[^>]*>([^<]+)", x) or [""])[0]
            authors = authors or re.findall(r"<dc:creator[^>]*>([^<]+)", x)
        except (StopIteration, zipfile.BadZipFile, OSError):
            pass
    if not authors and " -- " in visible_name:
        authors = [visible_name.split(" -- ")[1]]
    if not authors and logged_author:
        authors = [logged_author]
    author = _display_author(authors[0]) if authors else ""
    if len(authors) > 1:
        author += " et al."
    return {
        "title": clean_title(title or visible_name),
        "author": author,
        "publisher": publisher.strip(),
        "year": year if year.isdigit() else "",
    }


def _display_author(a: str) -> str:
    a = re.sub(r"\[.*$", "", a).split(";")[0].strip()
    # "Surname, First" -> "First Surname"; "Surname, 1926-1977" -> "Surname"
    if "," in a:
        last, rest = [p.strip() for p in a.split(",", 1)]
        rest = rest.split(",")[0].strip()
        return last if (not rest or re.match(r"^\d", rest)) else f"{rest} {last}"
    return a


def book_pdf(folder: Path, book_id: str) -> Path | None:
    p = folder / f"{book_id}.pdf"
    return p if p.exists() else None


def passage(pdf: Path, page: int, rect: dict) -> dict:
    """Whole words whose centre is inside the capture area, plus the text around it."""
    doc = pymupdf.open(pdf)
    if page < 0 or page >= doc.page_count:
        return {"text": "", "context": "", "label": ""}
    p = doc[page]
    s = p.rect.width / TABLET_PAGE_W
    x0, y0 = (rect["x"] + TABLET_PAGE_W / 2) * s, rect["y"] * s
    x1, y1 = x0 + rect["w"] * s, y0 + rect["h"] * s
    words = p.get_text("words", sort=True)
    inside = [w for w in words if x0 <= (w[0] + w[2]) / 2 <= x1 and y0 <= (w[1] + w[3]) / 2 <= y1]
    norm = lambda x: unicodedata.normalize("NFKC", x)
    words = [(*w[:4], norm(w[4]), *w[5:]) for w in words]
    inside = [(*w[:4], norm(w[4]), *w[5:]) for w in inside]
    text = " ".join(w[4] for w in inside)
    context = ""
    if inside:
        all_text = [w[4] for w in words]
        i0, i1 = words.index(inside[0]), words.index(inside[-1])
        before = " ".join(all_text[max(0, i0 - 40):i0])
        after = " ".join(all_text[i1 + 1:i1 + 41])
        context = (("…" + before + " ") if before else "") + "==" + text + "==" + ((" " + after + "…") if after else "")
    return {"text": text, "context": context, "label": p.get_label() or ""}
