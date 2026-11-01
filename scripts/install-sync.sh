#!/usr/bin/env bash
# Set up the Mac sync and run it every 15 minutes in the background (macOS).
# Usage: ./scripts/install-sync.sh "/path/to/your/vault/Books & Reading/Commonplace"
#        TIMEZONE="Europe/London" ./scripts/install-sync.sh "..."   (default: your Mac's time zone)
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
APP="$HOME/Library/Application Support/Commonplace"
LOGS="$HOME/Library/Logs/Commonplace"
LABEL="com.github.commonplace.sync"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

say() { printf '\n==> %s\n' "$*"; }

say "Python environment"
[ -d "$REPO/.venv" ] || python3 -m venv "$REPO/.venv"
"$REPO/.venv/bin/pip" -q install -r "$REPO/sync/requirements.txt"

say "Apple helper (text recognition + topics, on device)"
mkdir -p "$REPO/build"
swiftc -O -o "$REPO/build/commonplace-helper" "$REPO/helper/CommonplaceHelper.swift"

say "Settings"
mkdir -p "$APP" "$LOGS"
if [ ! -f "$APP/config.json" ]; then
  VAULT_DIR="${1:-}"
  if [ -z "$VAULT_DIR" ]; then
    echo "Pass the vault folder to write into, e.g.:"
    echo "  ./scripts/install-sync.sh \"\$HOME/Notes/Books/Commonplace\""
    exit 1
  fi
  TZ_NAME="${TIMEZONE:-$(readlink /etc/localtime | sed 's#.*/zoneinfo/##')}"
  python3 - "$APP/config.json" "$VAULT_DIR" "$TZ_NAME" <<'EOF'
import json, sys
json.dump({"vault_dir": sys.argv[2], "timezone": sys.argv[3],
           "hosts": ["remarkable-wifi", "remarkable"], "wifi_host": "remarkable-wifi",
           "ai": {"topics": {"provider": "apple"}, "handwriting": {"provider": "apple"}}},
          open(sys.argv[1], "w"), indent=2)
EOF
  echo "Wrote $APP/config.json"
  echo "Time zone: $TZ_NAME  <- check this. Notecard times use it (the tablet's own clock is UTC)."
  echo "           To change it, edit \"timezone\" in that file, e.g. \"Europe/London\"."
else
  echo "Keeping existing $APP/config.json"
fi

say "Background job (every 15 minutes)"
mkdir -p "$(dirname "$PLIST")"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$REPO/.venv/bin/python</string>
    <string>-m</string>
    <string>commonplace_sync</string>
  </array>
  <key>WorkingDirectory</key><string>$REPO/sync</string>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/opt/homebrew/bin</string></dict>
  <key>StartInterval</key><integer>900</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$LOGS/sync.log</string>
  <key>StandardErrorPath</key><string>$LOGS/sync.log</string>
</dict>
</plist>
EOF
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"

say "Done. It runs now and every 15 minutes while your Mac is awake."
echo "Log: $LOGS/sync.log"
echo "Run once by hand: (cd \"$REPO/sync\" && ../.venv/bin/python -m commonplace_sync)"
