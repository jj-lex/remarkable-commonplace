"""One sync pass: pull notecards from the tablet and write them into the vault."""
import hashlib
import json
import re
import shutil
import time
from datetime import datetime
from pathlib import Path

from . import ai, book, health, notecard, vault
from .config import CACHE, STATE, TABLET_DATA, XOCHITL, load
from .tablet import Tablet, Unreachable


def log(*a):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


def load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {"cards": {}}


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1))


def fingerprint(*paths: Path) -> str:
    h = hashlib.sha1()
    for p in paths:
        if p and p.exists():
            h.update(p.read_bytes())
    return h.hexdigest()


def enrich(card: dict, note_png: Path | None, existing: list[str] | None, known_topics: list[str]) -> None:
    """Handwriting as text and topics, via whichever providers are configured."""
    card["note_text"] = ai.read_handwriting(note_png, log) if note_png else ""
    if existing:                       # yours (or ours from an earlier run): keep as is
        card["topics"] = existing
    else:
        card["topics"] = ai.topics(card["passage"], card["note_text"], known_topics, log)
        known_topics.extend(t for t in card["topics"] if t not in known_topics)


YEAR_NAME = re.compile(r"^Commonplace (\d{4})$")


def yearly_notebooks(tab: Tablet, xo: Path) -> dict[int, str]:
    """{year: notebook id} for notebooks named 'Commonplace YYYY' inside a folder named 'Commonplace'."""
    meta_dir = xo / "_meta"
    shutil.rmtree(meta_dir, ignore_errors=True)
    r = tab.run(f"cd {XOCHITL} && grep -l -E '\"visibleName\": \"Commonplace( [0-9]{{4}})?\"' *.metadata 2>/dev/null")
    names = r.stdout.split()
    if not names:
        return {}
    tab.fetch(XOCHITL, names, meta_dir)
    metas = {f.name[:-9]: json.loads(f.read_text()) for f in meta_dir.glob("*.metadata")}
    folders = {u for u, m in metas.items() if m.get("type") == "CollectionType"
               and m.get("visibleName") == "Commonplace" and m.get("parent") != "trash"}
    years = {}
    for u, m in metas.items():
        hit = YEAR_NAME.match(m.get("visibleName", ""))
        if m.get("type") == "DocumentType" and hit and m.get("parent") in folders:
            years[int(hit.group(1))] = u
    return years


def run() -> int:
    cfg = load()
    state = load_state()
    vault.TZ = cfg["tz"]
    ai.configure(cfg, log)
    root: Path = cfg["vault_dir"]

    try:
        tab = Tablet(cfg["hosts"])
    except Unreachable as e:
        log("tablet not reachable — nothing to do (" + str(e) + ")")
        health.check_unreachable(state, cfg["unreachable_alert_days"], log)
        save_state(state)
        return 0
    state["last_seen"] = time.time()
    state.pop("alerted_unreachable", None)
    log("connected via", tab.host)
    health.ensure_mod_running(tab, log)
    health.check_wifi_passwords(cfg["wifi_host"], state, log)

    # 1. notecard logs written by the mod
    logs_dir = CACHE / "logs"
    shutil.rmtree(logs_dir, ignore_errors=True)
    tab.fetch(TABLET_DATA, ["."], logs_dir)
    cfg_file = logs_dir / "config.json"
    if not cfg_file.exists():
        log("no config.json on the tablet — run scripts/install.sh first")
        return 1
    tablet_cfg = json.loads(cfg_file.read_text())
    xo = CACHE / "xochitl"
    changed = []
    # one notebook per year: point the mod at this year's "Commonplace YYYY" notebook
    years = yearly_notebooks(tab, xo)
    if years:
        this_year = datetime.now(cfg["tz"]).year
        target = years.get(this_year) or years[max(years)]
        if tablet_cfg.get("notebookId") != target:
            tablet_cfg["notebookId"] = target
            changed.append("notebook")
        if this_year not in years and state.get("reminded_year") != this_year:
            health.notify(f"Create a notebook named 'Commonplace {this_year}' in your Commonplace folder. "
                          f"Until then, notecards go into Commonplace {max(years)}.")
            state["reminded_year"] = this_year
    nb_id = tablet_cfg["notebookId"]
    # keep the tablet's label times in the reader's time zone (handles daylight saving)
    offset = int(datetime.now(cfg["tz"]).utcoffset().total_seconds() // 60)
    if tablet_cfg.get("utcOffsetMinutes") != offset:
        tablet_cfg["utcOffsetMinutes"] = offset
        changed.append("time zone")
    if changed and tab.write_text(f"{TABLET_DATA}/config.json", json.dumps(tablet_cfg)):
        log("updated tablet settings:", ", ".join(changed))
    card_logs = []
    for f in sorted(logs_dir.glob("*.json")):
        if f.name in ("config.json", "index.json"):
            continue
        c = json.loads(f.read_text())
        if isinstance(c.get("id"), str) and c.get("cardPageId"):
            card_logs.append(c)

    # 2. the notebooks the notecards live in (small) and the books they came from (cached)
    nb_ids = sorted({lg.get("notebookId") or nb_id for lg in card_logs} | {nb_id})
    for n in nb_ids:
        shutil.rmtree(xo / n, ignore_errors=True)
    tab.fetch(XOCHITL, [x for n in nb_ids for x in (f"{n}.content", n)], xo)
    live = set()
    for n in nb_ids:
        if (xo / f"{n}.content").exists():
            live |= set(notecard.live_pages(json.loads((xo / f"{n}.content").read_text())))

    book_ids = sorted({c["id"] for c in card_logs})
    names = [f"{b}.{ext}" for b in book_ids for ext in ("pdf", "epub", "content", "metadata")]
    remote = tab.sizes(XOCHITL, names)
    stale = [n for n, size in remote.items() if not (xo / n).exists() or (xo / n).stat().st_size != size]
    if stale:
        log("fetching book files:", len(stale))
        tab.fetch(XOCHITL, stale, xo)

    sources = root / "_sources"
    assets = root / "_assets"
    known_topics = sorted({t for c in state["cards"].values() for t in c.get("topics", [])})
    cards = []

    for lg in card_logs:
        cid = lg["cardPageId"]
        prev = state["cards"].get(cid, {})
        nb_folder = xo / (lg.get("notebookId") or nb_id)
        rm = nb_folder / f"{cid}.rm"
        clip_src = notecard.clip_image(nb_folder, cid)
        removed = cid not in live
        if removed and cid not in state["cards"]:
            continue  # deleted on the tablet before it was ever synced
        fp = fingerprint(rm, clip_src) + json.dumps(lg, sort_keys=True) + str(removed)

        meta = book.details(xo, lg["id"], lg.get("name", ""), lg.get("author", ""))
        pdf = book.book_pdf(xo, lg["id"])
        psg = book.passage(pdf, lg["page"], lg["rect"]) if pdf else {"text": "", "context": "", "label": ""}
        card = {
            "id": cid, "book_id": lg["id"], "page": lg["page"], "time": lg["time"],
            "page_label": str(lg["page"] + 1),
            "printed_page": psg["label"] if psg["label"] and psg["label"] != str(lg["page"] + 1) else "",
            "passage": psg["text"], "context": psg["context"], "removed": removed, **meta,
        }
        if prev.get("note_name"):
            card["note_name"] = prev["note_name"]
        else:
            name = vault.note_name(card)
            taken = {c.get("note_name") for k, c in state["cards"].items() if k != cid} | {c["note_name"] for c in cards}
            card["note_name"] = name if name not in taken else f"{name} · {cid[:4]}"
        note_path = root / "Notecards" / (card["note_name"] + ".md")

        if prev.get("fp") == fp and note_path.exists():
            cards.append({**card, **{k: prev[k] for k in ("topics", "clip", "handwriting", "source_file", "note_text") if k in prev}})
            continue

        # book copy, once per book
        if pdf:
            src_name = vault.safe(meta["title"]) + ".pdf"
            if not (sources / src_name).exists():
                sources.mkdir(parents=True, exist_ok=True)
                shutil.copy2(pdf, sources / src_name)
                epub = xo / f"{lg['id']}.epub"
                if epub.exists():
                    shutil.copy2(epub, sources / (vault.safe(meta["title"]) + ".epub"))
                log("saved source copy:", src_name)
            card["source_file"] = src_name

        if clip_src:
            assets.mkdir(parents=True, exist_ok=True)
            shutil.copy2(clip_src, assets / f"{cid}-clip.png")
            card["clip"] = f"{cid}-clip.png"
        note_png = assets / f"{cid}-note.png"
        if notecard.render_handwriting(notecard.strokes(rm), note_png):
            card["handwriting"] = note_png.name
        else:
            note_png = None

        enrich(card, note_png, vault.existing_topics(note_path), known_topics)
        vault.write_notecard(root, card)
        state["cards"][cid] = {k: card[k] for k in ("note_name", "topics", "clip", "handwriting", "source_file", "note_text") if k in card}
        state["cards"][cid]["fp"] = fp
        log("wrote notecard:", card["note_name"])
        cards.append(card)

    vault.write_generated(root, cards, cfg["recent_days"])
    save_state(state)
    log(f"done: {len(cards)} notecards")
    return 0
