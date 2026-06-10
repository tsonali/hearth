#!/bin/bash
# Double-click this on a Mac to start Hearth. First run installs everything (a few
# minutes + a one-time model download); after that it just starts and opens in your
# browser. Everything runs on THIS machine — nothing is uploaded.
cd "$(dirname "$0")" || exit 1

echo "──────────────────────────────────────────────"
echo "  Hearth — private AI that lives in your house"
echo "──────────────────────────────────────────────"

# 1. uv (the installer/runner) — install if missing
if ! command -v uv >/dev/null 2>&1; then
  echo "→ first-time setup: installing the package manager (uv)…"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

# 2. dependencies
if [ ! -d ".venv" ]; then
  echo "→ installing Hearth's dependencies (one time)…"
fi
uv sync || { echo "setup failed — see messages above"; read -r -p "Press return to close."; exit 1; }

# 3. model — predownload so the first session isn't a surprise wait
echo "→ checking the local model (one-time ~8 GB download on first run)…"
uv run python -c "from huggingface_hub import snapshot_download; snapshot_download('mlx-community/Qwen2.5-14B-Instruct-4bit')" || true

# 4. start the local server + open the browser
echo "→ starting Hearth at http://127.0.0.1:8765 …"
( sleep 6; open "http://127.0.0.1:8765" ) &
uv run python -m imagination_engine serve
