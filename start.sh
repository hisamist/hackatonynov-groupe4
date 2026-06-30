#!/usr/bin/env bash
#
# Launch the TechCorp AI stack and auto-open the chat + demo pages in a browser.
#
# A container cannot open a browser on the host, so this thin wrapper runs
# docker compose, waits for the web service to respond, then opens the URLs.
# Plain `docker compose up` still works — you just don't get the auto-open.
#
set -euo pipefail
cd "$(dirname "$0")"

WEB_PORT="${WEB_PORT:-5050}"
BASE="http://localhost:${WEB_PORT}"
CHAT_URL="${BASE}/"
DEMO_URL="${BASE}/demo"

# Pick the compose command (plugin form first, then legacy).
if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  echo "ERROR: docker compose is not available." >&2
  exit 1
fi

echo "▶ Building and starting the stack..."
$COMPOSE up -d --build

# Pick a browser opener for the host OS.
open_url() {
  if command -v xdg-open >/dev/null 2>&1; then xdg-open "$1" >/dev/null 2>&1 &
  elif command -v open    >/dev/null 2>&1; then open "$1"     >/dev/null 2>&1 &   # macOS
  elif command -v wslview >/dev/null 2>&1; then wslview "$1"  >/dev/null 2>&1 &   # WSL
  else return 1; fi
}

# Wait for the web service to come up (Flask serves /models even before Ollama).
echo "▶ Waiting for the web service at ${BASE} ..."
for i in $(seq 1 60); do
  if curl -sf -o /dev/null "${BASE}/models" 2>/dev/null \
     || curl -sf -o /dev/null "${CHAT_URL}" 2>/dev/null; then
    echo "✔ Web service is up."
    break
  fi
  sleep 2
  if [ "$i" -eq 60 ]; then
    echo "⚠ Web service did not respond in time; opening pages anyway."
  fi
done

echo "▶ Opening pages:"
echo "    Chat : ${CHAT_URL}"
echo "    Demo : ${DEMO_URL}"
if ! open_url "${CHAT_URL}"; then
  echo "⚠ No browser opener found (xdg-open/open/wslview). Open these URLs manually:"
  echo "    ${CHAT_URL}"
  echo "    ${DEMO_URL}"
  exit 0
fi
sleep 1
open_url "${DEMO_URL}" || true

echo "✔ Done. Use 'make down' (or '${COMPOSE} down') to stop."
