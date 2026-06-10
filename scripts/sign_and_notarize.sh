#!/usr/bin/env bash
# Sign + notarize the Hearth distribution so macOS opens it without the
# right-click-to-Open dance. Run AFTER scripts/package.sh.
#
# Team: Sonali Maitra (individual), Team ID U3MBG724WA — enrolled 2026-06-10.
#
# One-time setup (the ONE thing only Sonali does):
#   App Store Connect -> Users and Access -> Integrations -> App Store Connect
#   API -> "+" -> name "hearth", role Admin -> download the AuthKey_<KEYID>.p8.
#   Claude takes it from there: scripts/apple_setup.py creates the Developer ID
#   certificate via the ASC API from a locally-generated CSR, installs it in
#   the keychain, and stores notarytool credentials from the same key.
# After that, this script is fully automatic every release.
TEAM_ID="U3MBG724WA"
set -euo pipefail
cd "$(dirname "$0")/.." || exit 1

IDENTITY=$(security find-identity -v -p codesigning | grep "Developer ID Application" | head -1 | sed 's/.*"\(.*\)"/\1/') || true
if [ -z "${IDENTITY:-}" ]; then
  echo "No 'Developer ID Application' certificate in the keychain yet."
  echo "Generate a CSR for the portal? (creates hearth-csr.pem on your Desktop)"
  read -r -p "[y/N] " yn
  if [ "${yn:-n}" = "y" ]; then
    openssl req -new -newkey rsa:2048 -nodes \
      -keyout "$HOME/Desktop/hearth-private.key" \
      -out "$HOME/Desktop/hearth-csr.pem" \
      -subj "/emailAddress=hello@sonalimaitra.com/CN=Sonali Maitra/C=US"
    echo "Upload ~/Desktop/hearth-csr.pem at developer.apple.com -> Certificates."
  fi
  exit 1
fi
echo "Signing as: $IDENTITY"

ZIP=$(ls -t dist/hearth-*.zip | head -1)
STAGE="dist/hearth"
[ -d "$STAGE" ] || { echo "run scripts/package.sh first"; exit 1; }

# Sign the app bundle (hardened runtime, required for notarization)
codesign --force --deep --options runtime --timestamp \
  --sign "$IDENTITY" "$STAGE/Hearth.app"
codesign --verify --strict "$STAGE/Hearth.app" && echo "signature verifies"

# Re-zip signed bundle, submit for notarization, wait, staple.
SIGNED="dist/$(basename "$ZIP" .zip)-signed.zip"
( cd dist && zip -rqX "$(basename "$SIGNED")" "hearth" )
xcrun notarytool submit "$SIGNED" --keychain-profile hearth-notary --wait
xcrun stapler staple "$STAGE/Hearth.app"
( cd dist && rm -f "$(basename "$SIGNED")" && zip -rqX "$(basename "$SIGNED")" "hearth" )
echo "DONE: $SIGNED is signed, notarized, stapled — no scary dialog."
