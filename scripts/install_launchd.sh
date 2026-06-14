#!/bin/zsh
# Install the wkpool run as a macOS launchd agent. Runs twice a day by
# default (morning + afternoon) so late-arriving upstream results get picked
# up the same day.
# Usage: scripts/install_launchd.sh ["H:M H:M ..."]   default: "9:15 15:15"
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
TIMES="${1:-9:15 15:15}"
LABEL="nl.wkpool.daily"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

# Build one <dict> per run time inside StartCalendarInterval.
INTERVALS=""
for t in ${(s: :)TIMES}; do
    H="${t%%:*}"; M="${t##*:}"
    INTERVALS+="        <dict><key>Hour</key><integer>$H</integer><key>Minute</key><integer>$M</integer></dict>
"
done

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
    <array>
$INTERVALS    </array>
    <key>StandardOutPath</key><string>$REPO/output/launchd.log</string>
    <key>StandardErrorPath</key><string>$REPO/output/launchd.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "geïnstalleerd: $LABEL draait dagelijks om: $TIMES"
echo "handmatig testen: launchctl start $LABEL"
echo "verwijderen:      launchctl unload $PLIST && rm $PLIST"
