#!/bin/bash

# TARS-AI Conversation Test Launcher
# Quick access to conversation testing tools

echo "=========================================="
echo "🤖 TARS-AI Conversation Test Launcher"
echo "=========================================="
echo ""
echo "Choose a test mode:"
echo ""
echo "1) Text Only    - Ultra-fast, type to interact"
echo "2) Voice Input  - STT enabled, speak to interact"
echo "3) Full App     - Complete app with TTS"
echo ""
echo "q) Quit"
echo ""

read -p "Select option [1-3, q]: " choice

case $choice in
    1)
        echo ""
        echo "Starting Text-Only Conversation Test..."
        echo "=========================================="
        cd "$(dirname "$0")"
        source .venv/bin/activate
        python3 app_conversation_test_text.py
        ;;
    2)
        echo ""
        echo "Starting Voice Input Conversation Test..."
        echo "=========================================="
        cd "$(dirname "$0")"
        source .venv/bin/activate
        python3 app_conversation_test_voice.py
        ;;
    3)
        echo ""
        echo "Starting Full TARS-AI Application..."
        echo "=========================================="
        cd "$(dirname "$0")"
        bash App-Start.sh
        ;;
    q|Q)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid option. Please choose 1, 2, 3, or q."
        exit 1
        ;;
esac 