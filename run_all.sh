#!/bin/bash
set -e

# Navigate to backend and run it in the background
cd ~/gesture-annotator-repo/backend

# Activate venv from project root
. ../venv/bin/activate

echo "Starting backend..."
python3 app.py &
BACKEND_PID=$!

# Navigate to frontend and run it
cd ../frontend
echo "Starting frontend..."
npm run dev -- --host 0.0.0.0 --port 5173

# When frontend exits, stop the backend
kill $BACKEND_PID
