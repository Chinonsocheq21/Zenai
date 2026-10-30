#!/bin/zsh
# ZenAI class demo: double-click on presentation day.
#  1. makes a fresh class code
#  2. opens a secure https tunnel (Cloudflare, free), so phones on ANY network can
#     reach ZenAI and voice works (phones only allow the microphone over https)
#  3. starts ZenAI with the code required
#  4. posts the live link to the website's "Try ZenAI" button, signed with the code
#  5. opens the projector page with the QR code
# Close this window to stop everything. If the tunnel can't start, it falls back to Wi-Fi only.
ZEN="$HOME/Desktop/Project Folders/zenai"
GIST=527d48ca1398b4b96ae4ec5f685b0028
cd "$ZEN" || exit 1
if lsof -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Something is already running on port 8000. Close it (or the other ZenAI window) and try again."; read; exit 1
fi
CODE="ZEN-$(( RANDOM % 9000 + 1000 ))"
CF="$ZEN/tools/bin/cloudflared"
if [ ! -x "$CF" ]; then
  mkdir -p "$ZEN/tools/bin"; echo "Getting the tunnel tool (one time)..."
  curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz | tar xz -C "$ZEN/tools/bin" && chmod +x "$CF"
fi
URL=""
if [ -x "$CF" ]; then
  "$CF" tunnel --no-autoupdate --url http://localhost:8000 > /tmp/zenai-tunnel.log 2>&1 &
  TUN=$!
  trap 'kill $TUN 2>/dev/null' EXIT
  for i in {1..40}; do URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/zenai-tunnel.log | head -1); [ -n "$URL" ] && break; sleep 1; done
fi
echo ""
echo "  ZenAI class demo"
echo "  Class code:  $CODE"
if [ -n "$URL" ]; then
  echo "  Live link:   $URL/student/   (works on any network, voice included)"
  SIG=$(printf '%s|%s' "$CODE" "$URL" | shasum -a 256 | cut -d' ' -f1)
  if command -v gh >/dev/null && gh api -X PATCH "gists/$GIST" -f "files[live.json][content]={\"url\":\"$URL\",\"sig\":\"$SIG\",\"at\":\"$(date -u +%FT%TZ)\"}" >/dev/null 2>&1; then
    echo "  Website:     zenai.unv.run 'Try ZenAI' now opens it with the class code"
  fi
  HOST=127.0.0.1
else
  echo "  Tunnel didn't start: Wi-Fi only mode (phones on this laptop's Wi-Fi; no voice)"
  HOST=0.0.0.0
fi
echo "  The QR page opens in your browser in a few seconds. Close this window to stop."
echo ""
( sleep 6; open "http://127.0.0.1:8000/present/" ) &
ACCESS_CODE="$CODE" PUBLIC_URL="$URL" PYTHONPATH=src .venv/bin/uvicorn zenai.api.main:app --host $HOST --port 8000
