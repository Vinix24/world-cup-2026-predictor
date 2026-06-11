#!/bin/zsh
# Install the daily wkpool run as a macOS launchd agent (08:15 local time).
# Usage: scripts/install_launchd.sh [HOUR] [MINUTE]
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
HOUR="${1:-8}"
MINUTE="${2:-15}"
LABEL="nl.wkpool.daily"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$REPO/scripts/daily_local.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key><integer>$HOUR</integer>
        <key>Minute</key><integer>$MINUTE</integer>
    </dict>
    <key>StandardOutPath</key><string>$REPO/output/launchd.log</string>
    <key>StandardErrorPath</key><string>$REPO/output/launchd.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "geïnstalleerd: $LABEL draait dagelijks om $(printf '%02d:%02d' "$HOUR" "$MINUTE")"
echo "handmatig testen: launchctl start $LABEL"
echo "verwijderen:      launchctl unload $PLIST && rm $PLIST"
