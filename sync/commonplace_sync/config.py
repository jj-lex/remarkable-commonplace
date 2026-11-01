"""Settings live outside the repo, in ~/Library/Application Support/Commonplace/config.json."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

APP = Path.home() / "Library" / "Application Support" / "Commonplace"
CONFIG = APP / "config.json"
STATE = APP / "state.json"
CACHE = APP / "cache"

DEFAULTS = {
    # Folder in your vault where notecards, books and topics are written. Required.
    "vault_dir": "",
    # SSH hosts from ~/.ssh/config, tried in order.
    "hosts": ["remarkable-wifi", "remarkable"],
    # Host used to check that Wi-Fi SSH still refuses passwords (empty to skip).
    "wifi_host": "remarkable-wifi",
    # IANA time zone for capture times, e.g. "America/New_York". Empty = this Mac's time zone.
    "timezone": "",
    "recent_days": 14,
    # Alert if the tablet hasn't been reachable for this many days.
    "unreachable_alert_days": 3,
}

XOCHITL = "/home/root/.local/share/remarkable/xochitl"
TABLET_DATA = "/home/root/commonplace"
MOD_FILE = "/home/root/xovi/exthome/qt-resource-rebuilder/commonplace.qmd"
XOVI_MARKER = "/etc/systemd/system/xochitl.service.d/00-xovi.conf"
SYNC_MARKER = "%% Everything above this line is updated by Commonplace sync. Write below it. %%"


def load() -> dict:
    cfg = dict(DEFAULTS)
    if CONFIG.exists():
        cfg.update(json.loads(CONFIG.read_text()))
    if not cfg["vault_dir"]:
        raise SystemExit(f"Set vault_dir in {CONFIG}")
    cfg["vault_dir"] = Path(cfg["vault_dir"]).expanduser()
    cfg["tz"] = ZoneInfo(cfg["timezone"]) if cfg["timezone"] else datetime.now().astimezone().tzinfo
    return cfg
