#!/usr/bin/env bash
# Launch script: ensure venv, find a free port, run Flask server, open browser

set -e
cd "$(dirname "$0")"

# Create venv if missing
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

# Activate and install deps
source venv/bin/activate
pip install -q -r requirements.txt

# Find first free port in 5000..5010
PORT=$(python3 -c "
import socket
for port in range(5000, 5010):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
            print(port)
            break
    except OSError:
        continue
else:
    print(5000)
")
export PORT
URL="http://localhost:${PORT}"

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
