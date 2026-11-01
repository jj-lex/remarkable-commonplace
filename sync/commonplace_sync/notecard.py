"""Read a notecard page from the Commonplace notebook: the clip image and your handwriting."""
import logging
from pathlib import Path

from PIL import Image, ImageDraw

logging.getLogger("rmscene").setLevel(logging.ERROR)
from rmscene import read_blocks  # noqa: E402
from rmscene.scene_stream import SceneLineItemBlock  # noqa: E402

PAGE_W, PAGE_H = 1404, 1872


def live_pages(content: dict) -> list[str]:
    pages = [p for p in content.get("cPages", {}).get("pages", []) if not p.get("deleted")]
    pages.sort(key=lambda p: p.get("idx", {}).get("value", ""))
    return [p["id"] for p in pages]


def clip_image(nb_folder: Path, page_id: str) -> Path | None:
    d = nb_folder / page_id
    pngs = sorted(d.glob("*.png"), key=lambda p: p.stat().st_size, reverse=True) if d.is_dir() else []
    return pngs[0] if pngs else None


def strokes(rm_file: Path) -> list[list[tuple[float, float]]]:
    if not rm_file.exists():
        return []
    out = []
    with open(rm_file, "rb") as f:
        try:
            for b in read_blocks(f):
                if isinstance(b, SceneLineItemBlock) and b.item.value is not None:
                    pts = [(p.x, p.y) for p in b.item.value.points]
                    if len(pts) > 1:
                        out.append(pts)
        except Exception:  # newer firmware blocks the reader doesn't know; keep what we got
            pass
    return out


def render_handwriting(lines: list, dest: Path, width: int = 4) -> bool:
    """Draw the strokes in black on white, cropped to the writing. Returns False if there's none."""
    if not lines:
        return False
    xs = [x for s in lines for x, _ in s]
    ys = [y for s in lines for _, y in s]
    pad = 24
    x0, y0, x1, y1 = min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad
    img = Image.new("RGB", (int(x1 - x0), int(y1 - y0)), "white")
    d = ImageDraw.Draw(img)
    for s in lines:
        d.line([(x - x0, y - y0) for x, y in s], fill="black", width=width, joint="curve")
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest)
    return True
