#!/usr/bin/env bash
# Restart the autonomous worker daemon

# Kill existing worker
pkill -f "autonomous_worker.sh" || true

# Wait a moment
sleep 2

# Start new worker
cd "$(dirname "$0")"
nohup ./autonomous_worker.sh 5 > worker.log 2>&1 &

echo "Worker restarted. PID: $!"
echo "Monitor with: tail -f worker.log"
