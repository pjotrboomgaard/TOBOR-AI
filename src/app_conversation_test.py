"""
app_conversation_test.py

Minimal test environment for TARS-AI multi-character conversations.
Only loads essential modules for conversation testing.
"""

# === Standard Libraries ===
import os
import sys
import threading
import time
from datetime import datetime

# === Custom Modules ===
from modules.module_config import load_config
import configparser
from modules.module_character import CharacterManager
from modules.module_memory import MemoryManager
from modules.module_llm import initialize_manager_llm
from modules.module_main import (
    initialize_managers, 
    start_auto_conversation, 
    conversation_mode,
    conversation_active,
    last_ai_response,
    conversation_participants,
    continue_multi_character_conversation
)

# === Constants and Globals ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)
sys.path.append(os.getcwd())

def print_status(message):
    """Print timestamped status messages"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}")

def initialize_test_managers(mem_manager, char_manager):
    """
    Initialize managers for testing without STT manager
    """
    # Import and set up global references
    import modules.module_main as main_module
    
    main_module.memory_manager = mem_manager
    main_module.character_manager = char_manager
    main_module.stt_manager = None  # No STT manager for testing
    
    # Import CONFIG for global access
    from modules.module_config import load_config
    main_module.CONFIG = load_config()
    
    print_status("Managers initialized for testing")

# Load test configuration
def load_test_config():
    """Load minimal configuration for testing"""
    config = configparser.ConfigParser()
    config_path = os.path.join(BASE_DIR, 'config_conversation_test.ini')
    
    if os.path.exists(config_path):
        print_status(f"Loading test config from: {config_path}")
        # Create a simple load_config-like function for our test config
        os.environ.setdefault('OPENAI_API_KEY', 'your_api_key_here')  # You'll need to set this
        
        # Import the regular config loader and modify it
        sys.path.insert(0, os.path.join(BASE_DIR, 'modules'))
        
        # Use the existing config loading mechanism but with our test file
        original_config = load_config()
        
        # Override with test-specific settings
        config.read(config_path)
        if 'TTS' in config:
            original_config['TTS'].test_mode = True
            original_config['TTS'].auto_start_conversations = True
        
        return original_config
    else:
        print_status("Test config not found, using regular config")
        return load_config()

CONFIG = load_test_config()

def simulate_conversation_test():
    """
    Simulate conversation testing without hardware dependencies
    """
    global conversation_mode, conversation_active
    
    print_status("=== TARS-AI Conversation Test Environment ===")
    print_status("Testing multi-character conversations...")
    
    try:
        # Initialize managers
        char_manager = CharacterManager(config=CONFIG)
        memory_manager = MemoryManager(config=CONFIG, char_name=char_manager.char_name, char_greeting=char_manager.char_greeting)
        
        # Initialize managers for testing (without STT manager)
        initialize_test_managers(memory_manager, char_manager)
        initialize_manager_llm(memory_manager, char_manager)
        
        print_status(f"Available characters: {char_manager.get_character_names()}")
        print_status("Starting auto-conversation test...")
        
        # Start auto conversation in a thread
        auto_conversation_thread = threading.Thread(
            target=start_auto_conversation, 
            args=(char_manager, memory_manager), 
            daemon=True
        )
        auto_conversation_thread.start()
        
        # Monitor conversation for testing
        print_status("Monitoring conversation activity...")
        
        # Let the conversation run for a while
        test_duration = 120  # 2 minutes
        start_time = time.time()
        
        while time.time() - start_time < test_duration:
            if conversation_active:
                status = f"Conversation active - Mode: {conversation_mode}, Participants: {len(conversation_participants) if conversation_participants else 0}"
                print_status(status)
            else:
                print_status("Conversation inactive")
            
            time.sleep(10)  # Check every 10 seconds
        
        print_status("Test completed successfully!")
        
        # Manually trigger another conversation for testing
        print_status("Triggering manual conversation test...")
        
        # Test character switching
        test_characters = ['zanne', 'mirza', 'els', 'pjotr']
        for char in test_characters:
            if char_manager.switch_to_character(char):
                print_status(f"✓ Successfully switched to {char}")
                
                # Test a quick conversation starter
                starter = f"Hallo familie, ik ben {char.title()}. Laten we even praten over onze verhoudingen."
                print_status(f"{char.title()}: {starter}")
                
                time.sleep(2)  # Brief pause between characters
            else:
                print_status(f"✗ Failed to switch to {char}")
        
    except KeyboardInterrupt:
        print_status("Test interrupted by user")
    except Exception as e:
        print_status(f"ERROR: {e}")
        import traceback
        print_status(f"TRACEBACK: {traceback.format_exc()}")

def interactive_conversation_test():
    """
    Interactive conversation testing mode
    """
    print_status("=== Interactive Conversation Test ===")
    print("Commands:")
    print("  start - Start auto conversation")
    print("  switch <character> - Switch to character")
    print("  say <message> - Make current character say something")
    print("  status - Show conversation status")
    print("  quit - Exit test")
    
    try:
        # Initialize managers
        char_manager = CharacterManager(config=CONFIG)
        memory_manager = MemoryManager(config=CONFIG, char_name=char_manager.char_name, char_greeting=char_manager.char_greeting)
        
        initialize_test_managers(memory_manager, char_manager)
        initialize_manager_llm(memory_manager, char_manager)
        
        while True:
            try:
                command = input(f"\n[{char_manager.char_name}]> ").strip().lower()
                
                if command == "quit":
                    break
                elif command == "start":
                    print_status("Starting auto conversation...")
                    auto_thread = threading.Thread(
                        target=start_auto_conversation, 
                        args=(char_manager, memory_manager), 
                        daemon=True
                    )
                    auto_thread.start()
                elif command.startswith("switch "):
                    char_name = command.split(" ", 1)[1]
                    if char_manager.switch_to_character(char_name):
                        print_status(f"Switched to {char_manager.char_name}")
                    else:
                        print_status(f"Failed to switch to {char_name}")
                elif command.startswith("say "):
                    message = command.split(" ", 1)[1]
                    char_name = char_manager.char_name
                    print_status(f"{char_name}: {message}")
                elif command == "status":
                    print_status(f"Current character: {char_manager.char_name}")
                    print_status(f"Conversation active: {conversation_active}")
                    print_status(f"Conversation mode: {conversation_mode}")
                    print_status(f"Participants: {conversation_participants}")
                    print_status(f"Available characters: {char_manager.get_character_names()}")
                elif command == "help":
                    print("Commands: start, switch <char>, say <msg>, status, quit")
                else:
                    print("Unknown command. Type 'help' for commands.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print_status(f"ERROR: {e}")
                
    except Exception as e:
        print_status(f"SETUP ERROR: {e}")

if __name__ == "__main__":
    print_status("TARS-AI Conversation Test Environment")
    
    # Check if user wants interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_conversation_test()
    else:
        simulate_conversation_test() 