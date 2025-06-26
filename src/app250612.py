"""
app.py

Main entry point for the TARS-AI application.

Initializes modules, loads configuration, and manages key threads for functionality such as:
- Speech-to-text (STT)
- Text-to-speech (TTS)
- Bluetooth control
- AI response generation

Run this script directly to start the application.
"""

# === Standard Libraries ===
import os
import sys
import threading
import time
from datetime import datetime

# === Custom Modules ===
from modules.module_config import load_config
from modules.module_character import CharacterManager
from modules.module_memory import MemoryManager
from modules.module_stt import STTManager
from modules.module_tts import update_tts_settings
from modules.module_btcontroller import *
from modules.module_main import initialize_managers, wake_word_callback, utterance_callback, post_utterance_callback, start_bt_controller_thread, start_discord_bot, process_discord_message_callback
from modules.module_vision import initialize_blip
from modules.module_llm import initialize_manager_llm
import modules.module_chatui

# === Constants and Globals ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)
sys.path.append(os.getcwd())

CONFIG = load_config()

# Global variables for character reloading
char_manager = None
memory_manager = None
character_loaded = False
stt_manager = None

# === Helper Functions ===
def init_app():
    """
    Performs initial setup for the application
    """
    
    queue_message(f"LOAD: Script running from: {BASE_DIR}")
    
    # Load the configuration
    CONFIG = load_config()
    if CONFIG['TTS']['ttsoption'] == 'xttsv2':
        update_tts_settings(CONFIG['TTS']['ttsurl'])

def reload_character_on_wake():
    """
    Reload CharacterManager and MemoryManager every time the wake word is detected.
    This allows for hot-reloading of character configurations.
    """
    global char_manager, memory_manager, character_loaded, CONFIG
    
    try:
        queue_message("INFO: Reloading character configuration...")
        
        # Reload the config first to pick up any changes
        CONFIG = load_config()
        queue_message("INFO: Configuration reloaded.")
        
        # Clean up existing managers if they exist
        if char_manager:
            queue_message("INFO: Cleaning up previous character instance...")
            del char_manager
        if memory_manager:
            queue_message("INFO: Cleaning up previous memory manager...")
            del memory_manager
        
        # Initialize fresh CharacterManager
        queue_message("INFO: Loading fresh character instance...")
        char_manager = CharacterManager(config=CONFIG)
        queue_message(f"INFO: Character '{char_manager.char_name}' reloaded successfully.")
        
        # Initialize fresh MemoryManager
        memory_manager = MemoryManager(
            config=CONFIG, 
            char_name=char_manager.char_name, 
            char_greeting=char_manager.char_greeting
        )
        queue_message("INFO: Memory manager reinitialized.")
        
        # Pass managers to main module
        initialize_managers(memory_manager, char_manager, stt_manager)
        initialize_manager_llm(memory_manager, char_manager)
        
        character_loaded = True
        queue_message("INFO: Character reload complete - ready for interaction!")
        
    except Exception as e:
        queue_message(f"ERROR: Failed to reload character: {e}")
        character_loaded = False

def custom_wake_word_callback(response_text):
    """
    Custom wake word callback that reloads character every time before processing.
    """
    # Always reload character on wake word detection
    reload_character_on_wake()
    
    # Call the original wake word callback
    wake_word_callback(response_text)

def start_discord_in_thread():
    """
    Start the Discord bot in a separate thread to prevent blocking.
    """
    discord_thread = threading.Thread(target=start_discord_bot, args=(process_discord_message_callback,), daemon=True)
    discord_thread.start()
    queue_message("INFO: Discord bot started in a separate thread.")

# === Main Application Logic ===
if __name__ == "__main__":
    # Perform initial setup
    init_app()

    # Create a shutdown event for global threads
    shutdown_event = threading.Event()

    # NOTE: CharacterManager and MemoryManager are reloaded on every wake word
    queue_message("INFO: Character will be reloaded fresh on every wake word detection.")
   
    # Initialize STTManager (this can start immediately)
    stt_manager = STTManager(config=CONFIG, shutdown_event=shutdown_event)
    stt_manager.set_wake_word_callback(custom_wake_word_callback)  # Use custom callback
    stt_manager.set_utterance_callback(utterance_callback)
    stt_manager.set_post_utterance_callback(post_utterance_callback)

    # DISCORD Callback
    if CONFIG['DISCORD']['enabled'] == 'True':
        start_discord_in_thread()

    # Start necessary threads
    if CONFIG['CONTROLS']['enabled'] == 'True':
        bt_controller_thread = threading.Thread(target=start_bt_controller_thread, name="BTControllerThread", daemon=True)
        bt_controller_thread.start()

    # Create a thread for the Flask app
    if CONFIG['CHATUI']['enabled'] == "True":
        queue_message(f"LOAD: ChatUI starting on port 5012...")
        flask_thread = threading.Thread(target=modules.module_chatui.start_flask_app, daemon=True)
        flask_thread.start()
    
    # Initialize BLIP to speed up initial image capture
    if CONFIG['VISION']['server_hosted'] != "True":
        initialize_blip()
    
    try:
        queue_message(f"LOAD: TARS-AI v1.03a running. Character will reload on each wake word...")
        # Start the STT thread
        stt_manager.start()

        while not shutdown_event.is_set():
            time.sleep(0.1) # Sleep to reduce CPU usage

    except KeyboardInterrupt:
        queue_message(f"INFO: Stopping all threads and shutting down executor...")
        shutdown_event.set()  # Signal global threads to shutdown
        # executor.shutdown(wait=True)

    finally:
        stt_manager.stop()
        if CONFIG['CONTROLS']['enabled'] == 'True':
            bt_controller_thread.join()
        queue_message(f"INFO: All threads and executor stopped gracefully.")
