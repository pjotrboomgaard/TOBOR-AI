#!/bin/bash
# TARS-AI Simple Conversation Test Startup Script
# Runs the simplified conversation test in virtual environment

cd "$(dirname "$0")"

echo "🚀 Starting TARS-AI Simple Conversation Test..."

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "INFO: Activating virtual environment..."
    source .venv/bin/activate
else
    echo "ERROR: Virtual environment not found at .venv"
    echo "Please run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Run the simple conversation test
python app_simple.py 