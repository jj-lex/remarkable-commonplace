"""Call the on-device Apple helper (Vision text recognition, Apple's language model)."""
import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HELPER = REPO / "build" / "commonplace-helper"
SOURCE = REPO / "helper" / "CommonplaceHelper.swift"


def helper() -> Path | None:
    if not HELPER.exists() or (SOURCE.exists() and SOURCE.stat().st_mtime > HELPER.stat().st_mtime):
        HELPER.parent.mkdir(exist_ok=True)
        r = subprocess.run(["swiftc", "-O", "-o", str(HELPER), str(SOURCE)], capture_output=True, text=True)
        if r.returncode != 0:
            print("could not build the Apple helper:", r.stderr.strip()[:300])
            return None
    return HELPER


def read_handwriting(png: Path) -> str:
    h = helper()
    if not h:
        return ""
    r = subprocess.run([str(h), "ocr", str(png)], capture_output=True, text=True, timeout=60)
    return r.stdout.strip() if r.returncode == 0 else ""


# words the model sometimes returns about the task itself rather than the excerpt
NOT_TOPICS = {"passage", "passages", "excerpt", "theme", "themes", "topic", "topics", "subject", "subjects",
              "book", "books", "text", "quote", "quotation", "reader", "note", "chapter", "story", "literature",
              "writing", "narrative", "idea", "ideas", "none", "n/a"}


def _norm(t: str) -> str:
    t = re.sub(r"[^a-z0-9 &'-]", "", t.lower()).strip()
    return " ".join(t.split()[:3])


def topics(passage: str, note: str, existing: list[str]) -> list[str]:
    """1-3 topics from Apple's on-device model; reuses existing topics when they match."""
    h = helper()
    if not h or not (passage or note):
        return []
    existing = [e for e in existing if e not in NOT_TOPICS]
    payload = json.dumps({"passage": passage[:3000], "note": note[:1000], "existing": existing[:200]})
    try:
        r = subprocess.run([str(h), "topics"], input=payload, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return []
    if r.returncode != 0:
        return []
    by_key = {}
    for e in existing:
        by_key.setdefault(e.lower().rstrip("s"), e)
    out = []
    for raw in r.stdout.split(","):
        t = _norm(raw)
        if not t or len(t) < 3 or t in NOT_TOPICS:
            continue
        t = by_key.get(t.rstrip("s"), t)   # "habits" -> existing "habit"
        if t not in out:
            out.append(t)
    return out[:3]
