#!/bin/bash

# Start-Multi-Agent-Therapy.sh
# Launch script for TARS-AI Multi-Agent Family Therapy System

echo "=================================================="
echo "🤖 TARS-AI Multi-Agent Family Therapy System"
echo "=================================================="
echo ""

# Check if we're in the src directory
if [ ! -f "app_multi_agent_therapy.py" ]; then
    cd src
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️  No virtual environment found. Running in system Python..."
fi

echo ""
echo "Starting Multi-Agent Therapy System..."
echo "Each family member runs as an independent agent:"
echo "  👥 Zanne - Defensive, feels misunderstood"
echo "  👥 Els - Corrective, tries to fix everyone"
echo "  👥 Mirza - Solution-focused, offers mindfulness"
echo "  👥 Pjotr - Mediator, diplomatic but tired"
echo "  🤖 Tobor - Orchestrating therapist"
echo ""
echo "🎤 Voice input will be active - speak into microphone"
echo "🔊 Each character will respond with their unique voice"
echo "🏥 Tobor will orchestrate the therapy session"
echo ""
echo "Press Ctrl+C to stop the session"
echo ""

# Check command line arguments
if [ "$1" = "--test" ]; then
    echo "🧪 Running in TEST MODE (no voice input/output)"
    python app_multi_agent_therapy.py --test
elif [ "$1" = "--voice" ]; then
    echo "🎤 Running with VOICE interaction"
    python app_multi_agent_therapy.py
else
    echo "Available modes:"
    echo "  ./Start-Multi-Agent-Therapy.sh --voice   (Full voice interaction)"
    echo "  ./Start-Multi-Agent-Therapy.sh --test    (Text-only test mode)"
    echo ""
    echo "🎤 Starting VOICE mode by default..."
    python app_multi_agent_therapy.py
fi