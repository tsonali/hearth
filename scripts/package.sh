#!/usr/bin/env bash
# Build a clean, distributable Hearth bundle: the code + the double-click app, with all
# private/heavy/generated material stripped (corpus, voice clips, checkpoints, model
# adapter, internal docs, venv, git). Produces dist/hearth-<version>.zip — the thing a
# person downloads, unzips, and double-clicks. (The model itself downloads on first run.)
set -euo pipefail
cd "$(dirname "$0")/.." || exit 1
VER=$(grep -m1 CFBundleShortVersionString -A1 "Hearth.app/Contents/Info.plist" | grep -oE '[0-9.]+' | head -1 || echo "0.2")
OUT="dist"; STAGE="$OUT/hearth"
rm -rf "$STAGE"; mkdir -p "$STAGE"

# copy tracked files only (git is the source of truth for "clean"), + the app bundle
git archive --format=tar HEAD | tar -x -C "$STAGE"
cp -R "Hearth.app" "$STAGE/" 2>/dev/null || true
cp -R "Start Hearth.command" "$STAGE/" 2>/dev/null || true

# belt-and-suspenders: ensure nothing private/heavy slipped in
rm -rf "$STAGE/data/corpus" "$STAGE/data/dataset" "$STAGE/data/recordings" \
       "$STAGE/data/model" "$STAGE/ckpts" "$STAGE/docs/internal" \
       "$STAGE/data/system_voices"/*.wav "$STAGE/.venv" 2>/dev/null || true
find "$STAGE" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find "$STAGE" -name '*.safetensors' -delete 2>/dev/null || true
find "$STAGE" -name '*.wav' -delete 2>/dev/null || true

# audit: fail loudly if anything risky remains
RISK=$(find "$STAGE" \( -name '*.safetensors' -o -name '*.wav' -o -name '*.pt' -o -name '*.gguf' \) 2>/dev/null | head)
if [ -n "$RISK" ]; then echo "ABORT — risky files in bundle:"; echo "$RISK"; exit 1; fi

ZIP="$OUT/hearth-$VER.zip"
( cd "$OUT" && zip -rqX "hearth-$VER.zip" "hearth" )
echo "built $ZIP ($(du -h "$ZIP" | cut -f1))"
echo "contents (top level):"; unzip -Z1 "$ZIP" | sed 's#^hearth/##' | awk -F/ '{print $1}' | sort -u | head -25
