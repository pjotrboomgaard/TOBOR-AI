#!/usr/bin/env python3
"""
TARS-AI Conversation Test (Voice Input)
Fast testing of conversation logic without TTS overhead
"""

import os
import sys
import time
import threading
import signal
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

# Import required modules
from modules.module_config import load_config
from modules.module_character import CharacterManager
from modules.module_memory import MemoryManager
from modules.module_main import (
    start_auto_conversation,
    continue_multi_character_conversation,
    generate_single_character_question,
    conversation_mode,
    conversation_active,
    conversation_participants,
    conversation_history,
    current_character_name
)
from modules.module_stt import STTManager
from modules.module_messageQue import queue_message
from modules.module_llm import process_completion

# Global variables
CONFIG = None
char_manager = None
mem_manager = None
stt_manager = None
shutdown_event = threading.Event()

def print_message(text):
    """Print messages with timestamp"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {text}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print_message("Shutdown signal received...")
    shutdown_event.set()
    if stt_manager:
        stt_manager.stop()
    sys.exit(0)

def mock_tts_output(text, character_name):
    """Mock TTS - just print the output"""
    print_message(f"{character_name}: {text}")

def test_conversation_callback(user_input, detected_character=None):
    """Handle voice input from user"""
    global current_character_name, conversation_mode, conversation_active
    
    print_message(f"User said: '{user_input}'")
    
    # Switch character if detected
    if detected_character and char_manager:
        if char_manager.switch_to_character(detected_character):
            current_character_name = detected_character
            print_message(f"Switched to character: {detected_character}")
    
    # Get response from current character
    if char_manager and current_character_name:
        try:
            # Get character response
            response = process_completion(
                user_input, 
                char_manager, 
                mem_manager, 
                CONFIG
            )
            
            if response:
                # Mock TTS output
                mock_tts_output(response, current_character_name.title())
                
                # Add to conversation history
                conversation_history.append(f"User: {user_input}")
                conversation_history.append(f"{current_character_name}: {response}")
                
        except Exception as e:
            print_message(f"Error processing response: {e}")

def initialize_systems():
    """Initialize all required systems"""
    global CONFIG, char_manager, mem_manager, stt_manager, current_character_name
    
    print_message("Initializing TARS-AI Conversation Test...")
    
    # Load configuration
    CONFIG = load_config()
    print_message("Configuration loaded")
    
    # Initialize character manager
    char_manager = CharacterManager()
    available_chars = char_manager.get_character_names()
    print_message(f"Characters loaded: {', '.join(available_chars)}")
    
    # Set default character
    if available_chars:
        char_manager.switch_to_character(available_chars[0])
        current_character_name = available_chars[0]
        print_message(f"Default character: {current_character_name}")
    
    # Initialize memory manager
    try:
        mem_manager = MemoryManager(current_character_name, CONFIG)
        print_message("Memory system initialized")
    except Exception as e:
        print_message(f"Memory system error: {e}")
        mem_manager = None
    
    # Initialize STT manager
    try:
        stt_manager = STTManager(CONFIG, char_manager)
        stt_manager.set_callback(test_conversation_callback)
        print_message("STT Manager initialized")
    except Exception as e:
        print_message(f"STT initialization error: {e}")
        return False
    
    return True

def start_auto_conversation_test():
    """Start automatic conversation for testing"""
    import random
    
    global conversation_mode, conversation_active, conversation_participants
    
    print_message("Starting automatic conversation test...")
    time.sleep(2)
    
    if not char_manager:
        return
    
    available_characters = char_manager.get_character_names()
    if not available_characters:
        return
    
    # Pick random starting character
    starting_char = random.choice(available_characters)
    
    if char_manager.switch_to_character(starting_char):
        print_message(f"{starting_char.title()} initiating conversation session")
        
        # Set conversation state
        conversation_mode = True
        conversation_active = True
        conversation_participants = [starting_char]
        
        # Add another participant
        other_chars = [c for c in available_characters if c != starting_char]
        if other_chars:
            conversation_participants.append(random.choice(other_chars))
        
        # Generate opening message
        opening_messages = [
            "Systemen online. Ik heb familie-interactiepatronen geanalyseerd. We moeten een eerlijke dialoog faciliteren.",
            "Goed, laten we praten. Ik merk spanning in onze communicatie.",
            "Het is tijd voor een open gesprek. Iedereen mag zijn mening geven.",
            "Ik voel dat we als familie beter kunnen communiceren. Laten we beginnen."
        ]
        
        opening_message = random.choice(opening_messages)
        mock_tts_output(opening_message, starting_char.title())
        
        # Start multi-character conversation loop
        conversation_thread = threading.Thread(
            target=run_conversation_loop,
            daemon=True
        )
        conversation_thread.start()

def run_conversation_loop():
    """Run the multi-character conversation loop"""
    global conversation_active
    
    while conversation_active and not shutdown_event.is_set():
        try:
            time.sleep(5)  # Wait between responses
            
            if conversation_active and conversation_participants:
                # Continue conversation
                continue_multi_character_conversation(char_manager, mem_manager)
                
        except Exception as e:
            print_message(f"Conversation loop error: {e}")
            break
    
    print_message("Conversation loop ended")

def main():
    """Main function"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print_message("=== TARS-AI Conversation Test (Voice Input) ===")
    print_message("This test runs conversations without TTS but with voice input")
    print_message("Say character names to switch: mirza, els, zanne, pjotr, tobor")
    print_message("Press Ctrl+C to exit")
    print("")
    
    # Initialize systems
    if not initialize_systems():
        print_message("Failed to initialize systems")
        return 1
    
    # Start STT processing
    if stt_manager:
        stt_manager.start()
        print_message("Voice recognition started")
    
    # Start automatic conversation
    auto_thread = threading.Thread(target=start_auto_conversation_test, daemon=True)
    auto_thread.start()
    
    try:
        # Keep main thread alive
        while not shutdown_event.is_set():
            time.sleep(1)
            
    except KeyboardInterrupt:
        print_message("Keyboard interrupt received")
    
    finally:
        print_message("Shutting down...")
        shutdown_event.set()
        if stt_manager:
            stt_manager.stop()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 