"""Keep the mod running and tell you (once) when something needs you."""
import subprocess
import time

from .config import MOD_FILE, XOVI_MARKER
from .tablet import SSH_OPTS, Tablet


def notify(message: str) -> None:
    script = f'display notification "{message.replace(chr(34), chr(39))}" with title "Commonplace"'
    subprocess.run(["osascript", "-e", script], capture_output=True)


def ensure_mod_running(tab: Tablet, log) -> None:
    """After a full restart the tablet comes back stock; start xovi again if the mod is installed."""
    if not tab.exists(MOD_FILE) or tab.exists(XOVI_MARKER):
        return
    log("tablet restarted since the mod was last running — starting xovi")
    r = tab.run("/home/root/xovi/start >/dev/null 2>&1; sleep 10; systemctl is-active xochitl", timeout=90)
    if r.stdout.strip() == "active" and tab.exists(XOVI_MARKER):
        notify("The tablet had restarted, so Commonplace was switched back on.")
    else:
        notify("Commonplace couldn't switch itself back on after the tablet restarted. Run /home/root/xovi/start.")


def check_wifi_passwords(host: str, state: dict, log) -> None:
    """A firmware update silently brings back password login over Wi-Fi. Warn once until it's fixed."""
    if not host:
        return
    r = subprocess.run(["ssh", *SSH_OPTS, "-o", "PreferredAuthentications=password", "-o", "PubkeyAuthentication=no",
                        host, "true"], capture_output=True, text=True)
    err = r.stderr
    if "Permission denied" not in err:
        return  # unreachable or unexpected: say nothing
    allowed = "password" in err.split("Permission denied", 1)[1]
    if allowed and not state.get("alerted_wifi_passwords"):
        log("Wi-Fi SSH accepts passwords again (firmware update?)")
        notify("Your tablet accepts passwords over Wi-Fi again, probably after an update. Ask Claude to re-apply key-only login.")
        state["alerted_wifi_passwords"] = True
    elif not allowed:
        state.pop("alerted_wifi_passwords", None)


def check_unreachable(state: dict, days: int, log) -> None:
    last = state.get("last_seen")
    if last and time.time() - last > days * 86400 and not state.get("alerted_unreachable"):
        log(f"tablet not reachable for over {days} days")
        notify(f"Haven't been able to reach your reMarkable for {days} days. Is Wi-Fi on?")
        state["alerted_unreachable"] = True
