#!/usr/bin/env python3
"""
TARS-AI Interactive Memory-Integrated Therapy App
Interactive therapy session with real voice input via STT
"""

import threading
import time
import json
import random
import signal
import sys
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# === Custom Modules ===
from modules.module_config import load_config
from modules.module_character import CharacterManager
from modules.module_memory import MemoryManager
from modules.module_stt import STTManager
from modules.module_tts import play_audio_chunks
from modules.module_memory_prompt import memory_prompt_system
from modules.module_chatui import start_flask_app

# Global variables
CONFIG = None
character_manager = None
memory_manager = None
stt_manager = None
# tts_manager = None  # Using direct TTS functions instead
conversation_history = []
therapy_session_active = False
waiting_for_user = False
user_question_count = 0
max_conversations_between_questions = 3
conversation_since_last_question = 0
shutdown_event = threading.Event()

def print_status(message):
    """Print timestamped status message"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def initialize_managers():
    """Initialize all system managers"""
    global CONFIG, character_manager, memory_manager, stt_manager
    
    try:
        print_status("Loading configuration...")
        CONFIG = load_config()
        
        print_status("Initializing managers...")
        
        # Initialize core managers
        character_manager = CharacterManager(CONFIG)
        memory_manager = MemoryManager(CONFIG, "Tobor", "Welkom bij de familiesessie.")
        
        # Initialize STT with voice detection
        stt_manager = STTManager(CONFIG, shutdown_event)
        stt_manager.set_utterance_callback(utterance_callback)
        
        # Start ChatUI in background if enabled
        if CONFIG.get("CHATUI", {}).get("enabled", False):
            start_flask_app()
            
        print_status("✅ All managers initialized successfully")
        return True
        
    except Exception as e:
        print_status(f"❌ Error initializing managers: {e}")
        return False

def clean_tts_text(text):
    """Clean text for TTS by removing behavioral tags and system elements"""
    import re
    
    # Remove behavioral tags like [frustrated], [automatic], etc.
    text = re.sub(r'\[[\w\s]+\]', '', text)
    
    # Remove action descriptions in parentheses
    text = re.sub(r'\([^)]*\)', '', text)
    
    # Remove system debug information
    text = re.sub(r'DEBUG:.*?(?=\n|$)', '', text)
    text = re.sub(r'INFO:.*?(?=\n|$)', '', text)
    
    # Remove think blocks
    text = re.sub(r'\*[^*]*\*', '', text)
    
    # Clean up multiple spaces and line breaks
    text = ' '.join(text.split())
    
    return text.strip()

async def play_tts_synchronized(character_name, text):
    """Play TTS with proper synchronization"""
    try:
        # Clean text for TTS
        clean_text = clean_tts_text(text)
        if not clean_text.strip():
            return
            
        # Print the character response
        print_status(f"🔊 {character_name}: {clean_text}")
        
        # Get character voice config
        if character_manager:
            character_manager.switch_to_character(character_name.lower())
            voice_config = character_manager.get_current_character_voice_config()
        else:
            voice_config = None
            
        # Play TTS and wait for completion
        await play_audio_chunks(clean_text, CONFIG['TTS']['ttsoption'], voice_config)
        
    except Exception as e:
        print_status(f"TTS Error: {e}")

def utterance_callback(message):
    """Process recognized speech from user (STT callback)"""
    try:
        # Parse the JSON message from STT
        data = json.loads(message)
        user_text = data.get("text", "").strip()
        
        if user_text and len(user_text) > 2:
            print_status(f"🎤 Recognized: {user_text}")
            handle_voice_input(user_text)
            
    except json.JSONDecodeError:
        print_status(f"Error parsing STT message: {message}")
    except Exception as e:
        print_status(f"Error in utterance callback: {e}")

def handle_voice_input(text):
    """Handle voice input from STT"""
    global waiting_for_user, conversation_history, therapy_session_active
    
    if not waiting_for_user or not therapy_session_active:
        print_status(f"Ignoring voice input - not waiting for user")
        return
        
    if text and len(text.strip()) > 2:
        print_status(f"👤 USER: {text}")
        conversation_history.append(f"user: {text}")
        waiting_for_user = False
        
        # Process user input and continue conversation
        threading.Thread(target=process_user_input_and_continue, args=(text,), daemon=True).start()

def process_user_input_and_continue(user_text):
    """Process user input and continue therapy conversation"""
    global conversation_history, conversation_since_last_question
    
    try:
        # Generate Tobor's therapeutic response to user
        tobor_response = memory_prompt_system.generate_tobor_therapeutic_response(
            user_text, conversation_history
        )
        
        if tobor_response:
            print_status(f"🤖 TOBOR: {tobor_response}")
            conversation_history.append(f"tobor: {tobor_response}")
            
            # Play Tobor's response
            asyncio.run(play_tts_synchronized("Tobor", tobor_response))
        
        # Allow family characters to respond to the user's topic
        time.sleep(2)
        characters_respond_to_topic(user_text)
        
        # Reset conversation counter
        conversation_since_last_question = 0
        
    except Exception as e:
        print_status(f"Error processing user input: {e}")

def characters_respond_to_topic(user_topic):
    """Let family characters respond to user's topic naturally"""
    global conversation_history, conversation_since_last_question
    
    try:
        # Select 2-3 characters to respond
        available_chars = ['els', 'mirza', 'zanne', 'pjotr']
        responding_chars = random.sample(available_chars, random.randint(2, 3))
        
        for i, char in enumerate(responding_chars):
            if conversation_since_last_question >= max_conversations_between_questions:
                break
                
            # Generate character response
            response = memory_prompt_system.generate_memory_integrated_response(
                char, 'user', user_topic, conversation_history
            )
            
            if response:
                print_status(f"👥 {char.upper()}: {response}")
                conversation_history.append(f"{char}: {response}")
                
                # Play character response
                asyncio.run(play_tts_synchronized(char.title(), response))
                
                conversation_since_last_question += 1
                
                # Small delay between character responses
                time.sleep(random.uniform(2, 4))
        
        # After characters respond, schedule next user interaction
        time.sleep(3)
        schedule_next_user_interaction()
        
    except Exception as e:
        print_status(f"Error in character responses: {e}")

def schedule_next_user_interaction():
    """Schedule the next time Tobor asks the user a question"""
    global user_question_count, waiting_for_user, conversation_since_last_question
    
    # Check if we should ask user another question
    if (conversation_since_last_question >= max_conversations_between_questions or 
        random.random() < 0.3):  # 30% chance to involve user
        
        ask_user_question()
    else:
        # Let characters continue talking among themselves for a bit
        threading.Timer(random.uniform(3, 6), continue_family_conversation).start()

def ask_user_question():
    """Tobor asks user a therapeutic question and waits for voice input"""
    global waiting_for_user, user_question_count, conversation_history
    
    try:
        user_question_count += 1
        
        # Generate Tobor's therapeutic question based on conversation so far
        question = memory_prompt_system.generate_tobor_followup_question(
            conversation_history, user_question_count
        )
        
        if question:
            print_status(f"🤖 TOBOR ASKS: {question}")
            conversation_history.append(f"tobor: {question}")
            
            # Play Tobor's question
            asyncio.run(play_tts_synchronized("Tobor", question))
            
            # Wait for user voice input
            print_status("🎤 Waiting for your voice input... (speak into microphone)")
            waiting_for_user = True
            
            # STT manager is already listening for voice input
            
    except Exception as e:
        print_status(f"Error asking user question: {e}")

def continue_family_conversation():
    """Let family members continue conversation among themselves"""
    global conversation_history, conversation_since_last_question
    
    if waiting_for_user:
        return  # Don't interrupt if waiting for user
        
    try:
        # Pick a character to speak
        characters = ['els', 'mirza', 'zanne', 'pjotr']
        speaker = random.choice(characters)
        
        # Generate response based on recent conversation
        recent_context = ' | '.join(conversation_history[-3:]) if conversation_history else "family conversation"
        
        response = memory_prompt_system.generate_memory_integrated_response(
            speaker, 'family', recent_context, conversation_history
        )
        
        if response:
            print_status(f"👥 {speaker.upper()}: {response}")
            conversation_history.append(f"{speaker}: {response}")
            
            # Play response
            asyncio.run(play_tts_synchronized(speaker.title(), response))
            
            conversation_since_last_question += 1
            
            # Schedule next interaction
            time.sleep(2)
            schedule_next_user_interaction()
            
    except Exception as e:
        print_status(f"Error in family conversation: {e}")

def start_interactive_therapy_session():
    """Start the main interactive therapy session"""
    global therapy_session_active, conversation_history, user_question_count
    
    print_status("🎭 Starting Interactive Memory-Integrated Therapy Session")
    print_status("💡 This session uses real voice input - speak into your microphone when prompted")
    
    therapy_session_active = True
    conversation_history = []
    user_question_count = 0
    
    # Tobor opens the session
    opening = "Goedemorgen, ik ben Tobor, jullie therapeutische begeleider. Welkom bij onze familiesessie. We gaan vandaag diep in gesprek over jullie familiedynamiek. Vertel me eerst: wat houdt je vandaag het meest bezig in je familie?"
    
    print_status(f"🤖 TOBOR OPENS: {opening}")
    conversation_history.append(f"tobor: {opening}")
    
    # Play opening
    asyncio.run(play_tts_synchronized("Tobor", opening))
    
    # Wait for first user input
    print_status("🎤 Please speak your response into the microphone...")
    global waiting_for_user
    waiting_for_user = True
    
    # Start STT listening
    if stt_manager:
        stt_manager.start()

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    global therapy_session_active, shutdown_event
    print_status("🛑 Shutting down interactive therapy session...")
    therapy_session_active = False
    shutdown_event.set()
    
    if stt_manager:
        stt_manager.stop()
    
    sys.exit(0)

def main():
    """Main application entry point"""
    print_status("🎭 TARS-AI Interactive Memory-Integrated Therapy")
    print_status("=" * 50)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize all systems
    if not initialize_managers():
        print_status("❌ Failed to initialize systems")
        return
    
    print_status(f"📚 Memory system loaded: {len(memory_prompt_system.character_memories)} characters")
    
    # Start the interactive therapy session
    start_interactive_therapy_session()
    
    # Keep the main thread alive
    try:
        while therapy_session_active:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main() 