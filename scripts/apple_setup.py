#!/usr/bin/env python3
"""One-time Apple signing setup, fully automated from a single ASC API key.

Sonali's part (once): App Store Connect -> Users and Access -> Integrations ->
App Store Connect API -> "+" (name: hearth, role: Admin) -> download
AuthKey_<KEYID>.p8 (lands in ~/Downloads) and note the Issuer ID shown on
that page.

Then:  .venv/bin/python scripts/apple_setup.py --issuer <ISSUER-UUID>
       (key file + key id are auto-discovered from ~/Downloads)

What it does, all locally except the one Apple API call the portal would have
made anyway:
  1. generates a P-256-equivalent RSA private key + CSR (Developer ID wants RSA)
  2. mints an ES256 JWT from the .p8 and POSTs the CSR to
     /v1/certificates {type: DEVELOPER_ID_APPLICATION}  (the documented API)
  3. installs the returned certificate + private key into the login keychain
  4. stores notarytool credentials from the same API key (profile: hearth-notary)
After this, scripts/sign_and_notarize.sh is fully automatic every release.
"""
import argparse
import base64
import glob
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

TEAM_ID = "U3MBG724WA"
API = "https://api.appstoreconnect.apple.com/v1"


def b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def make_jwt(key_path: Path, key_id: str, issuer: str) -> str:
    """ES256 JWT for the ASC API — signed with `cryptography` directly."""
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec, utils

    priv = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    header = {"alg": "ES256", "kid": key_id, "typ": "JWT"}
    now = int(time.time())
    payload = {"iss": issuer, "iat": now, "exp": now + 900,
               "aud": "appstoreconnect-v1"}
    signing_input = (b64url(json.dumps(header).encode()) + "." +
                     b64url(json.dumps(payload).encode()))
    der_sig = priv.sign(signing_input.encode(), ec.ECDSA(hashes.SHA256()))
    r, s = utils.decode_dss_signature(der_sig)
    raw = r.to_bytes(32, "big") + s.to_bytes(32, "big")  # JOSE wants raw r||s
    return signing_input + "." + b64url(raw)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issuer", required=True, help="Issuer ID (UUID) from the Integrations page")
    ap.add_argument("--key", help="path to AuthKey_<KEYID>.p8 (default: newest in ~/Downloads)")
    args = ap.parse_args()

    key_path = Path(args.key) if args.key else None
    if key_path is None:
        candidates = sorted(glob.glob(os.path.expanduser("~/Downloads/AuthKey_*.p8")),
                            key=os.path.getmtime)
        if not candidates:
            print("No AuthKey_*.p8 in ~/Downloads — download it from App Store Connect first.")
            return 1
        key_path = Path(candidates[-1])
    key_id = key_path.stem.replace("AuthKey_", "")
    print(f"using {key_path.name} (key id {key_id}, team {TEAM_ID})")

    # Move the key somewhere deliberate (and out of Downloads).
    keys_dir = Path.home() / ".appstoreconnect" / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)
    stored = keys_dir / key_path.name
    if not stored.exists():
        stored.write_bytes(key_path.read_bytes())
        os.chmod(stored, 0o600)
        print(f"key stored at {stored}")

    # 1. local private key + CSR (RSA-2048 — what Developer ID certs use)
    work = Path.home() / ".appstoreconnect" / "devid"
    work.mkdir(parents=True, exist_ok=True)
    priv = work / "developer_id_private.key"
    csr = work / "developer_id.csr"
    if not priv.exists():
        subprocess.run(["openssl", "req", "-new", "-newkey", "rsa:2048", "-nodes",
                        "-keyout", str(priv), "-out", str(csr),
                        "-subj", "/CN=Sonali Maitra/C=US"], check=True)
        os.chmod(priv, 0o600)
        print("CSR generated")

    # 2. create the Developer ID Application certificate via the API
    token = make_jwt(stored, key_id, args.issuer)
    body = json.dumps({"data": {"type": "certificates", "attributes": {
        "certificateType": "DEVELOPER_ID_APPLICATION",
        "csrContent": csr.read_text()}}}).encode()
    req = urllib.request.Request(f"{API}/certificates", data=body, method="POST",
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"Apple said {e.code}: {e.read().decode()[:500]}")
        return 1
    cert_b64 = data["data"]["attributes"]["certificateContent"]
    cer = work / "developer_id.cer"
    cer.write_bytes(base64.b64decode(cert_b64))
    print(f"certificate created: {data['data']['attributes'].get('name')} "
          f"(expires {data['data']['attributes'].get('expirationDate')})")

    # 3. into the keychain (cert + matching private key)
    subprocess.run(["security", "import", str(cer), "-k",
                    os.path.expanduser("~/Library/Keychains/login.keychain-db")], check=True)
    subprocess.run(["security", "import", str(priv), "-k",
                    os.path.expanduser("~/Library/Keychains/login.keychain-db"),
                    "-T", "/usr/bin/codesign"], check=True)
    ok = subprocess.run(["security", "find-identity", "-v", "-p", "codesigning"],
                        capture_output=True, text=True)
    print(ok.stdout.strip())
    if "Developer ID Application" not in ok.stdout:
        print("WARNING: identity not visible yet — may need Apple's intermediate "
              "(Developer ID G2 CA) — fetch from https://www.apple.com/certificateauthority/")

    # 4. notarytool credentials from the same API key
    subprocess.run(["xcrun", "notarytool", "store-credentials", "hearth-notary",
                    "--key", str(stored), "--key-id", key_id,
                    "--issuer", args.issuer], check=True)
    print("\nDONE — scripts/sign_and_notarize.sh is now fully automatic.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
