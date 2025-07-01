#!/usr/bin/env python3
"""
TARS-AI Simple Conversation Test
Simplified version of main app for testing conversations only
"""

import os
import sys
import time
import json
import signal
import threading
from pathlib import Path

# Add the src directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class SimpleCharacterManager:
    def __init__(self):
        self.characters = {}
        self.current_character = 'tobor'
        self.load_characters()
        
    def load_characters(self):
        """Load character data from JSON files"""
        character_dirs = [
            '../character/Tobor',
            '../character/Mirza', 
            '../character/Els',
            '../character/Pjotr',
            '../character/Zanne'
        ]
        
        for char_dir in character_dirs:
            if os.path.exists(char_dir):
                char_name = os.path.basename(char_dir).lower()
                json_file = os.path.join(char_dir, f"{os.path.basename(char_dir)}.json")
                
                if os.path.exists(json_file):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            char_data = json.load(f)
                            self.characters[char_name] = char_data
                            print(f"LOAD: Character loaded: {char_name}")
                    except Exception as e:
                        print(f"ERROR: Could not load {char_name}: {e}")
                        # Create basic character data
                        self.characters[char_name] = {
                            "name": char_name.title(),
                            "personality": f"I am {char_name.title()}"
                        }
                        
        if not self.characters:
            # Fallback characters
            self.characters = {
                'tobor': {"name": "Tobor", "personality": "Logical robot"},
                'mirza': {"name": "Mirza", "personality": "Sarcastic character"},
                'els': {"name": "Els", "personality": "Caring family member"},
                'pjotr': {"name": "Pjotr", "personality": "Philosophical poet"},
                'zanne': {"name": "Zanne", "personality": "Complex character"}
            }
            
    def switch_character(self, name):
        name = name.lower()
        if name in self.characters:
            self.current_character = name
            return True
        return False
        
    def get_current_character(self):
        return self.characters.get(self.current_character, {}).get('name', self.current_character.title())

class SimpleSTTManager:
    def __init__(self):
        self.is_listening = False
        self.stop_flag = threading.Event()
        
        # Try to load STT, but don't fail if unavailable
        try:
            import vosk
            import pyaudio
            
            # Find available model
            model_path = None
            possible_paths = [
                "stt/vosk-model-small-nl-0.22",
                "stt/vosk-model-small-en-us-0.15"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
                    
            if model_path:
                self.model = vosk.Model(model_path)
                self.rec = vosk.KaldiRecognizer(self.model, 16000)
                self.audio = pyaudio.PyAudio()
                self.stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=8000
                )
                self.stt_available = True
                print(f"INFO: STT initialized with model: {model_path}")
            else:
                self.stt_available = False
                print("INFO: No STT model found - using text input mode")
                
        except Exception as e:
            self.stt_available = False
            print(f"INFO: STT not available ({e}) - using text input mode")
            
    def listen_once(self):
        """Listen for one input (voice or text)"""
        if self.stt_available:
            return self._listen_voice()
        else:
            return self._listen_text()
            
    def _listen_voice(self):
        """Listen for voice input"""
        try:
            print("🎤 Listening... (speak now)")
            timeout = 100  # 10 seconds
            while timeout > 0:
                data = self.stream.read(4000, exception_on_overflow=False)
                if self.rec.AcceptWaveform(data):
                    result = json.loads(self.rec.Result())
                    text = result.get('text', '').strip()
                    if text:
                        return text
                timeout -= 1
            return None
        except Exception as e:
            print(f"❌ Voice input error: {e}")
            return None
            
    def _listen_text(self):
        """Listen for text input"""
        try:
            print("📝 Type your message (or character name to switch):")
            text = input("> ").strip()
            return text if text else None
        except (EOFError, KeyboardInterrupt):
            return None
            
    def cleanup(self):
        if hasattr(self, 'stream') and self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'audio') and self.audio:
            self.audio.terminate()

class SimpleLLMManager:
    def __init__(self):
        self.responses = {
            'tobor': [
                "Tobor here. Processing your input with logical precision.",
                "Logic circuits engaged. How may I assist with computational efficiency?",
                "Analyzing data patterns. Your request is being processed systematically."
            ],
            'mirza': [
                "Oh great, another conversation. How... delightful.",
                "Mirza here, with all the enthusiasm I can muster. Which isn't much.",
                "Sure, let's chat. Because I have nothing better to do with my existence."
            ],
            'els': [
                "Els here! I'm so glad we can talk together.",
                "That's really interesting. Tell me more about how you're feeling.",
                "I want to understand you better. Family connections matter so much."
            ],
            'pjotr': [
                "Pjotr here, contemplating the poetry of your words...",
                "Your thoughts remind me of autumn leaves dancing in philosophical winds.",
                "In the garden of conversation, every word is a seed of deeper meaning."
            ],
            'zanne': [
                "Zanne speaking. It's... complicated, but I'm listening.",
                "There's so much beneath the surface. Do you really want to understand?",
                "I appreciate you reaching out, even when things feel overwhelming."
            ]
        }
        self.response_index = {char: 0 for char in self.responses.keys()}
        
    def generate_response(self, character, user_input):
        """Generate a simple response for the character"""
        if character not in self.responses:
            return f"{character.title()}: I heard '{user_input}' but I'm not sure how to respond."
            
        responses = self.responses[character]
        index = self.response_index[character]
        response = responses[index % len(responses)]
        self.response_index[character] = (index + 1) % len(responses)
        
        # Add some context if user mentions specific things
        if 'family' in user_input.lower():
            response += " Family dynamics are indeed complex."
        elif 'help' in user_input.lower():
            response += " I'm here to help however I can."
        elif any(name in user_input.lower() for name in ['tobor', 'mirza', 'els', 'pjotr', 'zanne']):
            response += " Yes, we're all connected in this family system."
            
        return response

class SimpleConversationApp:
    def __init__(self):
        self.character_manager = SimpleCharacterManager()
        self.stt_manager = SimpleSTTManager()
        self.llm_manager = SimpleLLMManager()
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        print("\n🛑 Shutting down...")
        self.running = False
        self.stt_manager.cleanup()
        sys.exit(0)
        
    def print_help(self):
        print("\n" + "="*60)
        print("🤖 TARS-AI Simple Conversation Test")
        print("="*60)
        print("📢 Available characters:", ", ".join(self.character_manager.characters.keys()))
        print("💬 Commands:")
        print("   - Say/type character names to switch (tobor, mirza, els, pjotr, zanne)")
        print("   - Say/type anything else to chat with current character")
        print("   - Press Ctrl+C to quit")
        print("="*60)
        
    def run(self):
        self.print_help()
        
        current_character = self.character_manager.get_current_character()
        print(f"\n💬 Current character: {current_character}")
        print("🚀 Starting conversation loop...")
        
        try:
            while self.running:
                user_input = self.stt_manager.listen_once()
                
                if not user_input:
                    continue
                    
                print(f"\n👤 You: {user_input}")
                
                # Check for character switching
                user_input_lower = user_input.lower()
                switched = False
                
                for char_name in self.character_manager.characters.keys():
                    if char_name in user_input_lower:
                        if self.character_manager.switch_character(char_name):
                            current_character = self.character_manager.get_current_character()
                            print(f"🔄 Switched to: {current_character}")
                            switched = True
                            break
                
                if not switched:
                    # Generate response from current character
                    response = self.llm_manager.generate_response(
                        self.character_manager.current_character, 
                        user_input
                    )
                    print(f"🤖 {current_character}: {response}")
                
                print()  # Empty line for readability
                
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.stt_manager.cleanup()

def main():
    print("🚀 TARS-AI Simple Conversation Test")
    print("INFO: Loading simplified conversation system...")
    
    # Change to src directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    app = SimpleConversationApp()
    app.run()

if __name__ == "__main__":
    main() 