"""The two AI jobs — topics and handwriting — with prompts and clean-up shared by every provider."""
import re

from .providers import NoProvider, ProviderError, make

TOPICS_SYSTEM = (
    "A reader saves excerpts from books. For each excerpt, name what it is about: the ideas, people, "
    "places or subjects in it. Answer with 1 to 3 lowercase subjects, one or two ordinary English words "
    "each, separated by commas. No other text."
)
HANDWRITING_PROMPT = (
    "This image is a short handwritten note a reader wrote next to a book excerpt. Transcribe the "
    "handwriting exactly as written. Reply with only the transcription. If you can't read it, reply with nothing."
)

# Words a model sometimes returns about the task itself rather than the excerpt.
NOT_TOPICS = {"passage", "passages", "excerpt", "theme", "themes", "topic", "topics", "subject", "subjects",
              "book", "books", "text", "quote", "quotation", "reader", "note", "chapter", "story", "literature",
              "writing", "narrative", "idea", "ideas", "none", "n/a"}

_providers = {}


def configure(cfg: dict, log) -> None:
    """Build the providers from config. A broken provider falls back to none (and says why)."""
    ai_cfg = cfg.get("ai", {})
    for job in ("topics", "handwriting"):
        try:
            _providers[job] = make(ai_cfg.get(job))
        except ProviderError as e:
            log(f"{job}: {e} — skipping {job} this run")
            _providers[job] = NoProvider()
    log("AI: topics via " + _providers["topics"].name + ", handwriting via " + _providers["handwriting"].name)


def _norm(t: str) -> str:
    t = re.sub(r"[^a-z0-9 &'-]", "", t.lower()).strip()
    return " ".join(t.split()[:3])


def topics(passage: str, note: str, existing: list[str], log) -> list[str]:
    if not (passage or note):
        return []
    existing = [e for e in existing if e not in NOT_TOPICS]
    system = TOPICS_SYSTEM
    if existing:
        system += " If one of these subjects fits, use it instead of a new one: " + ", ".join(existing[:200]) + "."
    prompt = passage[:3000] + (f"\n(The reader wrote: {note[:1000]})" if note else "")
    try:
        raw = _providers["topics"].complete(system, prompt, max_tokens=64)
    except ProviderError as e:
        log(f"topics: {e}")
        return []
    except Exception as e:  # never let a provider problem stop the sync
        log(f"topics: unexpected error from {_providers['topics'].name}: {e!r}")
        return []
    by_key = {}
    for e in existing:
        by_key.setdefault(e.lower().rstrip("s"), e)
    out = []
    for piece in raw.split(","):
        t = _norm(piece)
        if not t or len(t) < 3 or t in NOT_TOPICS:
            continue
        t = by_key.get(t.rstrip("s"), t)   # "habits" -> existing "habit"
        if t not in out:
            out.append(t)
    return out[:3]


def read_handwriting(png, log) -> str:
    try:
        return _providers["handwriting"].read_image(png, HANDWRITING_PROMPT).strip()
    except ProviderError as e:
        log(f"handwriting: {e}")
        return ""
    except Exception as e:  # never let a provider problem stop the sync
        log(f"handwriting: unexpected error from {_providers['handwriting'].name}: {e!r}")
        return ""
