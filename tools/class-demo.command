#!/bin/zsh
# ZenAI class demo: double-click on presentation day.
# Starts ZenAI for phones on the same Wi-Fi, with a fresh class code, and opens the QR page.
cd "$(dirname "$0")/.."
if lsof -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Something is already running on port 8000. Close it (or the other ZenAI window) and try again."; read; exit 1
fi
CODE="ZEN-$(( RANDOM % 9000 + 1000 ))"
echo ""
echo "  ZenAI class demo"
echo "  Class code: $CODE"
echo "  The QR page opens in your browser in a few seconds."
echo "  If macOS asks whether Python may accept incoming connections, click Allow."
echo "  Close this window to stop."
echo ""
( sleep 6; open "http://127.0.0.1:8000/present/" ) &
ACCESS_CODE="$CODE" PYTHONPATH=src exec .venv/bin/uvicorn zenai.api.main:app --host 0.0.0.0 --port 8000
