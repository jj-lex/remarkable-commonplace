#!/usr/bin/env bash
# Stop the background sync. Your notes, settings and the tablet are left as they are.
set -euo pipefail
LABEL="com.github.commonplace.sync"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/$LABEL.plist"
echo "Background sync stopped. Notes in your vault and ~/Library/Application Support/Commonplace are untouched."
