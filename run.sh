#!/usr/bin/env bash
# Launch script: ensure venv, run Flask server, open browser to localhost:5000

set -e
cd "$(dirname "$0")"
PORT=5000
URL="http://localhost:${PORT}"

# Create venv if missing
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

# Activate and install deps
source venv/bin/activate
pip install -q -r requirements.txt

# Start server in background
echo "Starting server at ${URL} ..."
(cd src && python app.py) &
SERVER_PID=$!

# Wait for server to bind then open browser
sleep 2
if command -v open &>/dev/null; then
  open "${URL}"
elif command -v xdg-open &>/dev/null; then
  xdg-open "${URL}"
else
  echo "Open ${URL} in your browser"
fi

wait $SERVER_PID
