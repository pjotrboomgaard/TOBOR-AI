#!/usr/bin/env python3
"""
TARS-AI Voice Therapy App - Working Version
Based on the earlier version that successfully captured voice input
"""

import threading
import time
import json
import signal
import sys
import os
import asyncio

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# === Custom Modules ===
from modules.module_config import load_config
from modules.module_character import CharacterManager
from modules.module_memory import MemoryManager
from modules.module_stt import STTManager
from modules.module_tts import play_audio_chunks
from modules.module_memory_prompt import memory_prompt_system

# Global variables
CONFIG = None
character_manager = None
memory_manager = None
stt_manager = None
conversation_history = []
therapy_session_active = False
waiting_for_user = False
user_question_count = 0
shutdown_event = threading.Event()

def print_status(message):
    """Print timestamped status message"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def clean_tts_text(text):
    """Clean text for TTS output"""
    if not text:
        return ""
    
    import re
    text = re.sub(r'\[[\w\s,]+\]', '', text)
    text = re.sub(r'\*[^*]*\*', '', text)
    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'\{[^}]*\}', '', text)
    text = ' '.join(text.split())
    return text.strip()

def display_therapy_response(character_name, text):
    """Display character response (simplified without TTS for now)"""
    clean_text = clean_tts_text(text)
    if clean_text:
        print_status(f"🔊 {character_name.upper()}: {clean_text}")
    else:
        print_status(f"⚠️ {character_name}: [empty response]")

def voice_input_callback(message):
    """Handle real voice input from STT"""
    global waiting_for_user, conversation_history
    
    try:
        # Parse the JSON message from STT
        data = json.loads(message)
        user_text = data.get("text", "").strip()
        
        if user_text and len(user_text) > 2 and waiting_for_user:
            print_status(f"🎤 USER: {user_text}")
            conversation_history.append(f"user: {user_text}")
            waiting_for_user = False
            
            # Process user input
            threading.Thread(target=process_user_therapy_input, args=(user_text,), daemon=True).start()
            
    except json.JSONDecodeError:
        print_status(f"DEBUG: Non-JSON STT message: {message}")
    except Exception as e:
        print_status(f"ERROR in voice callback: {e}")

def process_user_therapy_input(user_text):
    """Process user input and generate character responses"""
    global conversation_history, user_question_count
    
    try:
        print_status("💭 Processing your input...")
        
        # Phase 1: Tobor's therapeutic response
        tobor_response = memory_prompt_system.generate_tobor_therapeutic_response(
            user_text, conversation_history[-10:]
        )
        
        if tobor_response:
            display_therapy_response("Tobor", tobor_response)
            conversation_history.append(f"tobor: {tobor_response}")
            time.sleep(2)
        
        # Phase 2: Family member responses
        family_members = ['zanne', 'els', 'mirza', 'pjotr']
        import random
        responding_members = random.sample(family_members, random.randint(2, 3))
        
        for member in responding_members:
            member_response = memory_prompt_system.generate_memory_integrated_response(
                member, 'user', user_text, conversation_history[-5:]
            )
            
            if member_response:
                display_therapy_response(member.title(), member_response)
                conversation_history.append(f"{member}: {member_response}")
                time.sleep(1.5)
        
        # Phase 3: Characters discuss among themselves
        print_status("💬 Characters discussing among themselves...")
        character_conversation_phase()
        
        # Phase 4: Tobor asks follow-up question
        user_question_count += 1
        time.sleep(2)
        
        followup_question = memory_prompt_system.generate_tobor_followup_question(
            conversation_history, user_question_count
        )
        
        if followup_question:
            display_therapy_response("Tobor", followup_question)
            conversation_history.append(f"tobor: {followup_question}")
            time.sleep(1)
            wait_for_user_input()
        
    except Exception as e:
        print_status(f"ERROR processing user input: {e}")
        wait_for_user_input()

def character_conversation_phase():
    """Characters have a brief conversation among themselves"""
    global conversation_history
    
    try:
        family_members = ['zanne', 'els', 'mirza', 'pjotr']
        import random
        
        # 2-3 exchanges between characters
        for turn in range(random.randint(2, 3)):
            speaking_chars = random.sample(family_members, 2)
            
            for char in speaking_chars:
                context = conversation_history[-8:] if conversation_history else []
                char_response = memory_prompt_system.generate_memory_integrated_response(
                    char, 'family', ' '.join([msg.split(': ', 1)[1] if ': ' in msg else msg for msg in context[-3:]]), context
                )
                
                if char_response:
                    display_therapy_response(char.title(), char_response)
                    conversation_history.append(f"{char}: {char_response}")
                    time.sleep(1)
        
        print_status("🔄 Characters finished discussing - returning to therapy session")
        
    except Exception as e:
        print_status(f"ERROR in character conversation: {e}")

def wait_for_user_input():
    """Set up system to wait for user voice input"""
    global waiting_for_user
    
    waiting_for_user = True
    print_status("🎤 Speak into your microphone now...")
    print_status("   (The system is listening for your voice)")

def bypass_wake_word_detection():
    """Start STT in a mode that bypasses wake word detection"""
    global stt_manager, therapy_session_active
    
    def therapy_stt_loop():
        """Custom STT loop that bypasses wake words and directly listens"""
        print_status("INFO: Starting therapy voice input mode")
        
        while therapy_session_active and not shutdown_event.is_set():
            if waiting_for_user:
                # Direct transcription without wake word detection
                try:
                    result = stt_manager._transcribe_utterance()
                    if result:
                        # Voice input was captured and processed by callback
                        time.sleep(0.5)
                    else:
                        time.sleep(0.1)
                except Exception as e:
                    print_status(f"ERROR in STT transcription: {e}")
                    time.sleep(1)
            else:
                # Not waiting for input, just pause briefly
                time.sleep(0.5)
    
    # Start the therapy STT loop
    threading.Thread(target=therapy_stt_loop, daemon=True).start()

def start_therapy_session():
    """Start the interactive therapy session"""
    global therapy_session_active
    
    therapy_session_active = True
    print_status("🎭 Starting Interactive Voice Therapy Session")
    print_status("=" * 60)
    
    # Tobor's opening
    opening_message = "Goedemorgen. Ik ben Tobor, jullie therapeutische begeleider. Welkom bij onze familiesessie. Vertel me, waar wil je vandaag over praten? Wat houdt je bezig?"
    display_therapy_response("Tobor", opening_message)
    conversation_history.append(f"tobor: {opening_message}")
    
    # Wait for user to respond
    time.sleep(2)
    wait_for_user_input()

def initialize_therapy_system():
    """Initialize all therapy system components"""
    global CONFIG, character_manager, memory_manager, stt_manager
    
    try:
        print_status("Loading configuration...")
        CONFIG = load_config()
        
        print_status("Initializing managers...")
        
        # Initialize core managers
        character_manager = CharacterManager(CONFIG)
        memory_manager = MemoryManager(CONFIG, "Tobor", "Welkom bij de familiesessie.")
        
        # Initialize STT for voice input
        stt_manager = STTManager(CONFIG, shutdown_event)
        stt_manager.set_utterance_callback(voice_input_callback)
        
        print_status("✅ All therapy systems initialized successfully")
        return True
        
    except Exception as e:
        print_status(f"❌ Failed to initialize therapy system: {e}")
        return False

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    global therapy_session_active
    print_status("🛑 Shutting down voice therapy session...")
    therapy_session_active = False
    shutdown_event.set()
    
    if stt_manager:
        try:
            stt_manager.stop()
        except AttributeError:
            pass
    
    sys.exit(0)

def main():
    """Main therapy application"""
    print_status("🎭 TARS-AI Voice-Interactive Therapy Session - Working Version")
    print_status("=" * 60)
    
    # Set up signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize all systems
    if not initialize_therapy_system():
        print_status("❌ Failed to initialize therapy systems")
        return
    
    # Check memory system status
    print_status(f"Memory system loaded: {len(memory_prompt_system.character_memories)} characters")
    
    # Start voice input bypass
    bypass_wake_word_detection()
    
    # Start the interactive therapy session
    start_therapy_session()
    
    # Keep the main thread alive
    try:
        while therapy_session_active:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main() 