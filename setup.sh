#!/bin/bash
echo "============================================"
echo "  HVAC Complaint Analysis System - Setup"
echo "============================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed."
    exit 1
fi

echo "[1/3] Installing Python dependencies..."
pip3 install -r requirements.txt

echo ""
echo "[2/3] Generating synthetic complaint data..."
cd backend
PYTHONUTF8=1 python3 generate_data.py

echo ""
echo "[3/3] Running ML analysis pipeline..."
PYTHONUTF8=1 python3 run_pipeline.py

cd ..
echo ""
echo "============================================"
echo "  Setup Complete! Run: ./start.sh"
echo "============================================"
