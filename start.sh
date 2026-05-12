#!/bin/bash
echo "============================================"
echo "  HVAC Complaint Analysis System"
echo "============================================"

export PYTHONUTF8=1

if [ ! -f "backend/data/complaints.db" ]; then
    echo "[WARN] No database found. Running setup..."
    bash setup.sh
fi

echo "Starting server at http://localhost:8000"
echo "Press Ctrl+C to stop."
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
