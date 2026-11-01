"""Talk to the reMarkable over SSH. Reads files; the only thing it ever runs is xovi's own start script."""
import io
import shlex
import subprocess
import tarfile
from pathlib import Path

SSH_OPTS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=6"]


class Unreachable(Exception):
    pass


class Tablet:
    def __init__(self, hosts: list[str]):
        self.host = None
        errors = []
        for h in hosts:
            r = subprocess.run(["ssh", *SSH_OPTS, h, "true"], capture_output=True, text=True)
            if r.returncode == 0:
                self.host = h
                break
            errors.append(f"{h}: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'exit ' + str(r.returncode)}")
        if not self.host:
            raise Unreachable("; ".join(errors))

    def run(self, cmd: str, timeout: int = 60) -> subprocess.CompletedProcess:
        return subprocess.run(["ssh", *SSH_OPTS, self.host, cmd], capture_output=True, text=True, timeout=timeout)

    def exists(self, path: str) -> bool:
        return self.run(f"test -e {shlex.quote(path)}").returncode == 0

    def fetch(self, base: str, names: list[str], dest: Path) -> list[str]:
        """Copy files/folders (relative to base) into dest. Missing names are skipped."""
        if not names:
            return []
        quoted = " ".join(shlex.quote(n) for n in names)
        cmd = f"cd {shlex.quote(base)} && for n in {quoted}; do [ -e \"$n\" ] && echo \"$n\"; done | tar -cf - -T - 2>/dev/null"
        r = subprocess.run(["ssh", *SSH_OPTS, self.host, cmd], capture_output=True, timeout=600)
        if not r.stdout:
            return []
        dest.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(r.stdout)) as t:
            members = t.getnames()
            t.extractall(dest, filter="data")
        return members

    def sizes(self, base: str, names: list[str]) -> dict[str, int]:
        quoted = " ".join(shlex.quote(n) for n in names)
        r = self.run(f"cd {shlex.quote(base)} && for n in {quoted}; do [ -f \"$n\" ] && echo \"$n $(wc -c < \"$n\")\"; done")
        out = {}
        for line in r.stdout.splitlines():
            n, s = line.rsplit(" ", 1)
            out[n] = int(s)
        return out
