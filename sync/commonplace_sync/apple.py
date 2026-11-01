"""Call the on-device Apple helper (Vision text recognition, Apple's language model)."""
import json
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



def generate(system: str, prompt: str) -> str:
    """Apple's on-device language model (macOS 26+, Apple Intelligence on)."""
    h = helper()
    if not h:
        return ""
    payload = json.dumps({"system": system, "prompt": prompt})
    try:
        r = subprocess.run([str(h), "generate"], input=payload, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""
