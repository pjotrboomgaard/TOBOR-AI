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
from modules.module_messageQue import queue_message

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
character_config_manager = None

# === Helper Functions ===
def init_app():
    """
    Performs initial setup for the application
    """
    global CONFIG, character_config_manager
    
    queue_message(f"LOAD: Script running from: {BASE_DIR}")
    
    # Load the configuration
    CONFIG = load_config()
    
    # Initialize character configuration manager
    character_config_manager = CharacterConfigManager(CONFIG)
    character_config_manager.validate_character_files()
    
    # Check if we have the TTS configuration properly
    if hasattr(CONFIG, 'TTS') and hasattr(CONFIG.TTS, 'ttsoption'):
        if CONFIG.TTS.ttsoption == 'xttsv2':
            update_tts_settings(CONFIG.TTS.ttsurl)
    elif 'TTS' in CONFIG and CONFIG['TTS']['ttsoption'] == 'xttsv2':
        update_tts_settings(CONFIG['TTS']['ttsurl'])

def reload_character_for_wake_word(wake_word_text):
    """
    Reload CharacterManager and MemoryManager based on the detected wake word.
    This allows for hot-reloading of different character configurations.
    """
    global char_manager, memory_manager, character_loaded, CONFIG
    
    try:
        # Determine which character to load based on wake word
        character_key = character_config_manager.get_character_from_wake_word(wake_word_text)
        
        if character_key is None:
            queue_message("ERROR: No matching character found for wake word")
            return
        
        character_config = character_config_manager.get_character_config(character_key)
        character_name = character_config['name']
        
        # Skip reload if same character is already loaded
        if character_config_manager.is_same_character(character_key):
            queue_message(f"INFO: Character '{character_name}' is already active.")
            return
        
        queue_message(f"INFO: Loading character '{character_name}' from wake word: '{wake_word_text}'")
        
        # Update configuration for the new character
        if not character_config_manager.update_config_for_character(character_key):
            return
        
        # Reload the config to pick up any changes
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
        
        queue_message(f"INFO: Character '{character_name}' reload complete - ready for interaction!")
        
    except Exception as e:
        queue_message(f"ERROR: Failed to reload character: {e}")
        character_loaded = False

def custom_wake_word_callback(response_text):
    """
    Custom wake word callback that reloads character every time before processing.
    """
    # Always reload character on wake word detection
    reload_character_for_wake_word(response_text)
    
    # Call the original wake word callback
    wake_word_callback(response_text)

def start_discord_in_thread():
    """
    Start the Discord bot in a separate thread to prevent blocking.
    """
    discord_thread = threading.Thread(target=start_discord_bot, args=(process_discord_message_callback,), daemon=True)
    discord_thread.start()
    queue_message("INFO: Discord bot started in a separate thread.")

# === Character Configuration Manager Class ===
class CharacterConfigManager:
    """
    Manages character configurations and provides utilities for character switching.
    """
    
    def __init__(self, config):
        self.config = config
        self.character_configs = {}
        self.current_character = None
        self.load_character_configs()
    
    def load_character_configs(self):
        """
        Load character configurations from the config file.
        """
        self.character_configs = {}
        
        # Handle both dictionary and object-style config access
        characters_section = None
        if hasattr(self.config, 'CHARACTERS'):
            characters_section = self.config.CHARACTERS
        elif isinstance(self.config, dict) and 'CHARACTERS' in self.config:
            characters_section = self.config['CHARACTERS']
        
        if characters_section:
            # Convert to dict if it's an object
            if hasattr(characters_section, '__dict__'):
                characters_dict = {k: v for k, v in characters_section.__dict__.items() if not k.startswith('_')}
            else:
                characters_dict = characters_section
            
            for char_name, char_data in characters_dict.items():
                try:
                    # Parse the character data: card_path, voice_id, tts_voice
                    parts = [part.strip() for part in char_data.split(',')]
                    if len(parts) == 3:
                        self.character_configs[char_name.lower()] = {
                            'name': char_name.title(),
                            'card_path': parts[0],
                            'voice_id': parts[1],
                            'tts_voice': parts[2]
                        }
                        queue_message(f"LOAD: Character config loaded: {char_name} -> {parts[0]}")
                    else:
                        queue_message(f"ERROR: Invalid character config format for {char_name}: {char_data}")
                        queue_message("Expected format: card_path, voice_id, tts_voice")
                except Exception as e:
                    queue_message(f"ERROR: Failed to parse character config for {char_name}: {e}")
        
        # Fallback to default configuration if no characters found
        if not self.character_configs:
            queue_message("WARN: No character configurations found in [CHARACTERS] section. Using default Tobor config.")
            
            # Handle both config formats
            char_path = None
            voice_id = None
            tts_voice = None
            
            if hasattr(self.config, 'CHAR'):
                char_path = self.config.CHAR.character_card_path
                voice_id = self.config.TTS.voice_id
                tts_voice = self.config.TTS.tts_voice
            elif 'CHAR' in self.config:
                char_path = self.config['CHAR']['character_card_path']
                voice_id = self.config['TTS']['voice_id']
                tts_voice = self.config['TTS']['tts_voice']
            
            self.character_configs['tobor'] = {
                'name': 'Tobor',
                'card_path': char_path,
                'voice_id': voice_id,
                'tts_voice': tts_voice
            }
    
    def get_character_from_wake_word(self, wake_word_text):
        """
        Extract character name from wake word detection text.
        Returns the character key if found, None otherwise.
        """
        wake_word_lower = wake_word_text.lower()
        
        # Check each character name in the wake word text
        for char_key in self.character_configs.keys():
            if char_key in wake_word_lower:
                queue_message(f"DEBUG: Found character '{char_key}' in wake word: '{wake_word_text}'")
                return char_key
        
        # Default fallback to first available character or tobor
        if 'tobor' in self.character_configs:
            queue_message(f"DEBUG: Defaulting to 'tobor' for wake word: '{wake_word_text}'")
            return 'tobor'
        elif self.character_configs:
            fallback = list(self.character_configs.keys())[0]
            queue_message(f"DEBUG: Defaulting to '{fallback}' for wake word: '{wake_word_text}'")
            return fallback
        
        return None
    
    def get_character_config(self, character_key):
        """
        Get configuration for a specific character.
        """
        return self.character_configs.get(character_key.lower())
    
    def update_config_for_character(self, character_key):
        """
        Update the global CONFIG with character-specific settings.
        """
        if character_key not in self.character_configs:
            queue_message(f"ERROR: Unknown character key: {character_key}")
            return False
        
        char_config = self.character_configs[character_key]
        
        try:
            # Handle both config formats - object style and dictionary style
            if hasattr(self.config, 'CHAR'):
                # Object-style config - update attributes directly
                self.config.CHAR.character_card_path = char_config['card_path']
                self.config.TTS.voice_id = char_config['voice_id']
                self.config.TTS.tts_voice = char_config['tts_voice']
            else:
                # Dictionary-style config - update dictionary values
                self.config['CHAR']['character_card_path'] = char_config['card_path']
                self.config['TTS']['voice_id'] = char_config['voice_id']
                self.config['TTS']['tts_voice'] = char_config['tts_voice']
            
            self.current_character = character_key
            queue_message(f"INFO: Config updated for character: {char_config['name']}")
            queue_message(f"INFO: Updated character card: {char_config['card_path']}")
            queue_message(f"INFO: Updated TTS voice: {char_config['tts_voice']}")
            queue_message(f"INFO: Updated voice ID: {char_config['voice_id']}")
            return True
            
        except Exception as e:
            queue_message(f"ERROR: Failed to update config for character {character_key}: {e}")
            import traceback
            queue_message(f"DEBUG: Traceback: {traceback.format_exc()}")
            return False
    
    def list_available_characters(self):
        """
        List all available characters for debugging.
        """
        queue_message("INFO: Available characters:")
        for char_key, char_config in self.character_configs.items():
            queue_message(f"  - {char_key}: {char_config['name']} ({char_config['card_path']})")
        return self.character_configs
    
    def get_wake_words(self):
        """
        Get list of all supported wake words.
        """
        return list(self.character_configs.keys())
    
    def is_same_character(self, character_key):
        """
        Check if the requested character is the same as the current one.
        """
        return self.current_character == character_key
    
    def validate_character_files(self):
        """
        Validate that all character card files exist.
        """
        missing_files = []
        for char_key, char_config in self.character_configs.items():
            card_path = os.path.join("..", char_config['card_path'])
            if not os.path.exists(card_path):
                missing_files.append(f"{char_key}: {card_path}")
                queue_message(f"WARN: Character card file not found: {card_path}")
        
        if missing_files:
            queue_message(f"ERROR: {len(missing_files)} character files are missing:")
            for missing in missing_files:
                queue_message(f"  - {missing}")
            return False
        else:
            queue_message("INFO: All character card files validated successfully.")
            return True

# === Main Application Logic ===
if __name__ == "__main__":
    # Perform initial setup
    init_app()

    # List available characters
    character_config_manager.list_available_characters()

    # Create a shutdown event for global threads
    shutdown_event = threading.Event()

    # NOTE: CharacterManager and MemoryManager are reloaded on every wake word
    queue_message("INFO: Characters will be reloaded fresh on every wake word detection.")
    wake_words = character_config_manager.get_wake_words()
    queue_message(f"INFO: Supported wake words: {', '.join(wake_words)}")
   
    # Initialize STTManager (this can start immediately)
    stt_manager = STTManager(config=CONFIG, shutdown_event=shutdown_event)
    stt_manager.set_wake_word_callback(custom_wake_word_callback)  # Use custom callback
    stt_manager.set_utterance_callback(utterance_callback)
    stt_manager.set_post_utterance_callback(post_utterance_callback)

    # DISCORD Callback
    discord_enabled = False
    if hasattr(CONFIG, 'DISCORD'):
        discord_enabled = getattr(CONFIG.DISCORD, 'enabled', False)
    elif 'DISCORD' in CONFIG:
        discord_enabled = CONFIG['DISCORD'].get('enabled') == 'True'
    
    if discord_enabled:
        start_discord_in_thread()

    # Start necessary threads
    controls_enabled = False
    if hasattr(CONFIG, 'CONTROLS'):
        controls_enabled = getattr(CONFIG.CONTROLS, 'enabled', False)
    elif 'CONTROLS' in CONFIG:
        controls_enabled = CONFIG['CONTROLS'].get('enabled') == 'True'
    
    if controls_enabled:
        bt_controller_thread = threading.Thread(target=start_bt_controller_thread, name="BTControllerThread", daemon=True)
        bt_controller_thread.start()

    # Create a thread for the Flask app
    chatui_enabled = False
    if hasattr(CONFIG, 'CHATUI'):
        chatui_enabled = getattr(CONFIG.CHATUI, 'enabled', False)
    elif 'CHATUI' in CONFIG:
        chatui_enabled = CONFIG['CHATUI'].get('enabled', "False") == "True"
    
    if chatui_enabled:
        queue_message(f"LOAD: ChatUI starting on port 5012...")
        flask_thread = threading.Thread(target=modules.module_chatui.start_flask_app, daemon=True)
        flask_thread.start()
    
    # Initialize BLIP to speed up initial image capture
    vision_server_hosted = False
    if hasattr(CONFIG, 'VISION'):
        vision_server_hosted = getattr(CONFIG.VISION, 'server_hosted', False)
    elif 'VISION' in CONFIG:
        vision_server_hosted = CONFIG['VISION'].get('server_hosted') == "True"
    
    if not vision_server_hosted:
        initialize_blip()
    
    try:
        queue_message(f"LOAD: TARS-AI v1.03a running with multi-character support. Characters will reload on each wake word...")
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
        if controls_enabled:
            bt_controller_thread.join()
        queue_message(f"INFO: All threads and executor stopped gracefully.")
