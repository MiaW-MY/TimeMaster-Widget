#!/usr/bin/env bash
# Build a read-only uncompressed DMG with Time Master.app and an Applications alias (Tier B UX).
set -euo pipefail
ROOT="$(cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

APP="$ROOT/dist/Time Master.app"
if [[ ! -d "$APP" ]]; then
  echo "Missing: $APP"
  echo "Running scripts/build_mac_app.sh first..."
  bash "$ROOT/scripts/build_mac_app.sh"
fi

VERSION="${VERSION:-}"
if [[ -z "$VERSION" ]]; then
  VERSION="$(git describe --tags --always 2>/dev/null || true)"
fi
if [[ -z "$VERSION" ]]; then
  VERSION="0.0.0"
fi
# Safe for filenames
VERSION="${VERSION//\//-}"

STAGE="$ROOT/build/dmg_stage"
OUT="$ROOT/dist/Time-Master-${VERSION}.dmg"

rm -rf "$STAGE"
mkdir -p "$STAGE"
ditto "$APP" "$STAGE/Time Master.app"
ln -sf /Applications "$STAGE/Applications"

mkdir -p "$ROOT/dist"
rm -f "$OUT"

hdiutil create \
  -volname "Time Master" \
  -srcfolder "$STAGE" \
  -ov \
  -format UDRO \
  "$OUT"

rm -rf "$STAGE"

echo
echo "DMG: $OUT"
echo "Upload this file to GitHub Releases (or share directly). Users open the DMG and drag Time Master.app to Applications."
