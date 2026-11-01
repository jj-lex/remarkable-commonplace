"""Write notecards and the generated Books / Topics / Recent pages into the vault."""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from .config import SYNC_MARKER


def safe(name: str, limit: int = 80) -> str:
    name = re.sub(r'[\\/:*?"<>|#^\[\]]', "", name).strip()
    name = re.sub(r"\s+", " ", name)
    return name[:limit].rstrip(" .") or "Untitled"


def fmt_time(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000).strftime("%-d %b %Y, %-I:%M %p").replace("AM", "am").replace("PM", "pm")


def note_name(card: dict) -> str:
    first = " ".join(card["passage"].split()[:6]) or "passage"
    return safe(f"{card['title']} p{card['page_label']} — {first}")


def existing_user_part(path: Path) -> str:
    if not path.exists():
        return "\n## My notes\n\n"
    s = path.read_text()
    return s.split(SYNC_MARKER, 1)[1] if SYNC_MARKER in s else "\n## My notes\n\n"


def existing_topics(path: Path) -> list[str] | None:
    """Topics already in the note's properties (yours or ours) — kept as they are."""
    if not path.exists():
        return None
    m = re.search(r"^topics:\s*(\[.*\])\s*$", path.read_text(), flags=re.M)
    if not m:
        return None
    try:
        return [str(t) for t in json.loads(m.group(1))]
    except json.JSONDecodeError:
        return None


def write_notecard(root: Path, card: dict) -> Path:
    path = root / "Notecards" / (card["note_name"] + ".md")
    path.parent.mkdir(parents=True, exist_ok=True)
    user = existing_user_part(path)
    src = card.get("source_file")
    page_link = f"[[_sources/{src}#page={card['page'] + 1}|Open the book at this page]]" if src else ""
    lines = [
        "---",
        "type: notecard",
        f'book: "[[Books/{safe(card["title"])}|{card["title"]}]]"',
        f'author: "{card["author"]}"' if card["author"] else "author: ",
        f"page: {card['page_label']}",
        *([f'printed_page: "{card["printed_page"]}"'] if card.get("printed_page") else []),
        f"captured: {datetime.fromtimestamp(card['time'] / 1000).strftime('%Y-%m-%dT%H:%M')}",
        f"topics: {json.dumps(card.get('topics', []), ensure_ascii=False)}",
        f"notecard_id: {card['id']}",
    ]
    if card.get("removed"):
        lines.append("removed: true")
    lines += ["---", ""]
    if card.get("removed"):
        lines += ["> [!warning] Removed from the tablet", "> You deleted this notecard in the Commonplace notebook. This note stays until you delete it.", ""]
    if card.get("clip"):
        lines += [f"![[_assets/{card['clip']}]]", ""]
    if card["passage"]:
        lines += ["> " + card["passage"], ""]
    else:
        lines += ["> [!note] Picture only", "> No text could be read from the book file for this passage.", ""]
    meta = f"**{card['title']}**" + (f" — {card['author']}" if card["author"] else "") + f" · p. {card['page_label']} · {fmt_time(card['time'])}"
    lines += [meta + (f" · {page_link}" if page_link else ""), ""]
    if card.get("context"):
        lines += ["> [!quote]- Around the passage", "> " + card["context"], ""]
    if card.get("handwriting") or card.get("note_text"):
        lines += ["## Note", ""]
        if card.get("handwriting"):
            lines += [f"![[_assets/{card['handwriting']}]]", ""]
        if card.get("note_text"):
            lines += ["> " + card["note_text"].replace("\n", "\n> "), ""]
    if card.get("topics"):
        lines += ["Topics: " + " · ".join(f"[[Topics/{safe(t)}|{t}]]" for t in card["topics"]), ""]
    path.write_text("\n".join(lines) + "\n" + SYNC_MARKER + user)
    return path


def _row(card: dict) -> str:
    first = " ".join(card["passage"].split()[:14]) or "(picture only)"
    return f"- [[Notecards/{card['note_name']}|p. {card['page_label']}]] — {first}…"


def write_generated(root: Path, cards: list[dict], recent_days: int) -> None:
    live = [c for c in cards if not c.get("removed")]
    books, topics = {}, {}
    for c in live:
        books.setdefault(c["title"], []).append(c)
        for t in c.get("topics", []):
            topics.setdefault(t, []).append(c)

    (root / "Books").mkdir(parents=True, exist_ok=True)
    for title, cs in books.items():
        cs.sort(key=lambda c: (c["page"], c["time"]))
        c0 = cs[0]
        info = [f"**Author:** {c0['author']}" if c0["author"] else "", f"**Published:** {c0['year']}" if c0.get("year") else "",
                f"**Publisher:** {c0['publisher']}" if c0.get("publisher") else "",
                f"**Source copy:** [[_sources/{c0['source_file']}]]" if c0.get("source_file") else ""]
        body = [f"# {title}", "", *[i for i in info if i], "", f"## Notecards ({len(cs)})", "", *[_row(c) for c in cs], ""]
        (root / "Books" / f"{safe(title)}.md").write_text("\n".join(body))

    (root / "Topics").mkdir(parents=True, exist_ok=True)
    for t, cs in topics.items():
        cs.sort(key=lambda c: -c["time"])
        body = [f"# {t}", "", f"{len(cs)} notecards from {len({c['title'] for c in cs})} books", ""]
        for c in cs:
            body.append(f"- [[Notecards/{c['note_name']}|{c['title']} p. {c['page_label']}]] — {' '.join(c['passage'].split()[:14])}…")
        (root / "Topics" / f"{safe(t)}.md").write_text("\n".join(body) + "\n")

    cutoff = (datetime.now() - timedelta(days=recent_days)).timestamp() * 1000
    recent = sorted([c for c in live if c["time"] >= cutoff], key=lambda c: -c["time"])
    body = ["# Recent", "", f"Notecards from the last {recent_days} days, newest first.", ""]
    body += [f"- {fmt_time(c['time'])} · **{c['title']}** · " + _row(c)[2:] for c in recent] or ["Nothing in the last two weeks."]
    (root / "Recent.md").write_text("\n".join(body) + "\n")

    body = ["# Commonplace", "", f"{len(live)} notecards from {len(books)} books.", "", "[[Recent]]", ""]
    for title in sorted(books):
        body += [f"## [[Books/{safe(title)}|{title}]]", "", *[_row(c) for c in sorted(books[title], key=lambda c: c["page"])], ""]
    if topics:
        body += ["## Topics", "", " · ".join(f"[[Topics/{safe(t)}|{t}]] ({len(cs)})" for t, cs in sorted(topics.items())), ""]
    (root / "Commonplace.md").write_text("\n".join(body))
