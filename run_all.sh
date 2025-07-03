#!/bin/bash
set -e

echo "Stopping any existing node and python processes..."
pkill -f "python3 app.py" || true
pkill -f "npm run dev" || true

# Start backend
echo "Starting backend..."
cd ~/gesture-annotator-repo/backend
. ../venv/bin/activate
nohup python3 app.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend running with PID $BACKEND_PID"

# Start report_backend
echo "Starting report backend..."
cd ~/gesture-annotator-repo/report_backend
. ../venv/bin/activate
nohup python3 app.py > report_backend.log 2>&1 &
REPORT_BACKEND_PID=$!
echo "Report backend running with PID $REPORT_BACKEND_PID"

# Start frontend
echo "Starting frontend..."
cd ~/gesture-annotator-repo/frontend
nohup npm run dev -- --host 0.0.0.0 --port 5173 > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend running with PID $FRONTEND_PID"

# Start report_frontend
echo "Starting report frontend..."
cd ~/gesture-annotator-repo/report_frontend
nohup npm run dev -- --host 0.0.0.0 --port 5174 > report_frontend.log 2>&1 &
REPORT_FRONTEND_PID=$!
echo "Report frontend running with PID $REPORT_FRONTEND_PID"

echo "All services started."
echo "Press Ctrl+C to stop all services."

# Wait to keep script running and allow Ctrl+C
trap "echo 'Stopping all services...'; kill $BACKEND_PID $REPORT_BACKEND_PID $FRONTEND_PID $REPORT_FRONTEND_PID; exit 0" SIGINT SIGTERM

# Keep the script alive
while true; do sleep 10; done
