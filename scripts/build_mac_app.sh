#!/usr/bin/env bash
# Build a double-clickable Time Master.app (bundles Python + PySide6; no system Python required).
set -euo pipefail
ROOT="$(cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export PYINSTALLER_CONFIG_DIR="${PYINSTALLER_CONFIG_DIR:-$ROOT/.cache/pyinstaller}"
mkdir -p "$PYINSTALLER_CONFIG_DIR"

if [[ -x "$ROOT/.venv/bin/python3" ]]; then
  PY="$ROOT/.venv/bin/python3"
else
  PY="${PYTHON:-python3}"
fi

"$PY" -m pip install -q -r requirements-dev.txt
"$PY" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "Time Master" \
  --osx-bundle-identifier "dev.timemaster.widget" \
  --icon "$ROOT/assets/AppIcon.icns" \
  --add-data "assets:assets" \
  "$ROOT/time_master.py"

# PyInstaller sometimes leaves the default windowed icon; always overlay our icns.
BUNDLE="$ROOT/dist/Time Master.app"
ICNS_DST="$BUNDLE/Contents/Resources/icon-windowed.icns"
if [[ -f "$ROOT/assets/AppIcon.icns" && -d "$BUNDLE" ]]; then
  cp "$ROOT/assets/AppIcon.icns" "$ICNS_DST"
  touch "$BUNDLE"
fi

echo
echo "Built: $BUNDLE"
echo "Drag it to Applications, or open it from dist/. Config and stats: ~/Library/Application Support/TimeMaster-Widget/"
echo "If the Dock/Finder still shows the old icon, remove the old app copy, rebuild, then re-copy; or run: touch \"$BUNDLE\" and relaunch Finder (icon cache)."
