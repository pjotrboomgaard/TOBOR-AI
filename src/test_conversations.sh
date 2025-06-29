#!/bin/bash

echo "TARS-AI Conversation Test Environment"
echo "===================================="

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "WARNING: OPENAI_API_KEY environment variable not set"
    echo "Please set it with: export OPENAI_API_KEY=your_key_here"
    echo ""
fi

echo "Available test modes:"
echo "1. Automatic conversation test (default)"
echo "2. Interactive conversation test"
echo ""

read -p "Choose mode (1 or 2, press Enter for default): " mode

case $mode in
    2)
        echo "Starting interactive conversation test..."
        python app_conversation_test.py interactive
        ;;
    *)
        echo "Starting automatic conversation test..."
        python app_conversation_test.py
        ;;
esac 