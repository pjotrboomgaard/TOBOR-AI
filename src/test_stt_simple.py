#!/usr/bin/env python3
"""
Simple STT Test - Test if voice input is being captured properly
"""

import sys
import os
import time
import threading
import json

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.module_config import load_config
from modules.module_stt import STTManager

# Global variables
CONFIG = None
stt_manager = None
shutdown_event = threading.Event()
voice_detected = False

def utterance_callback(message):
    """Handle STT voice recognition"""
    global voice_detected
    try:
        print(f"[STT RAW] {message}")
        
        # Parse JSON message
        data = json.loads(message)
        text = data.get("text", "").strip()
        
        if text and len(text) > 2:
            print(f"[VOICE DETECTED] '{text}'")
            voice_detected = True
            
            # Test response
            if "stop" in text.lower() or "quit" in text.lower():
                print("[STOPPING] Voice command received")
                shutdown_event.set()
            
    except json.JSONDecodeError:
        print(f"[ERROR] Could not parse: {message}")
    except Exception as e:
        print(f"[ERROR] Callback error: {e}")

def main():
    """Simple STT test"""
    global CONFIG, stt_manager, voice_detected
    
    print("=== Simple STT Test ===")
    print("Speak into your microphone. Say 'stop' or 'quit' to end.")
    
    try:
        # Load config
        CONFIG = load_config()
        
        # Initialize STT
        stt_manager = STTManager(CONFIG, shutdown_event)
        stt_manager.set_utterance_callback(utterance_callback)
        
        print("Starting STT system...")
        stt_manager.start()
        
        print("🎤 Listening for voice input... (speak now)")
        
        # Listen for 30 seconds or until voice detected
        for i in range(60):  # 60 seconds total
            if shutdown_event.is_set():
                break
            if voice_detected:
                print(f"✅ Voice input detected successfully!")
                voice_detected = False  # Reset for next detection
            
            print(f"Listening... {i+1}/60", end='\r')
            time.sleep(1)
        
        print("\nStopping STT system...")
        stt_manager.stop()
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        if stt_manager:
            stt_manager.stop()
    except Exception as e:
        print(f"Error: {e}")
        if stt_manager:
            stt_manager.stop()

if __name__ == "__main__":
    main() 