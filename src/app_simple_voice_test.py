#!/usr/bin/env python3
"""
TARS-AI Simple Voice Conversation Test
- STT enabled for voice input
- Text output only (no TTS)
- Minimal dependencies
- Auto-runs in virtual environment
"""

import os
import sys
import time
import threading
import signal
from pathlib import Path

# Add the src directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Simple character manager without heavy dependencies
class SimpleCharacterManager:
    def __init__(self):
        self.characters = {
            'tobor': 'Tobor - The logical robot',
            'mirza': 'Mirza - The sarcastic one', 
            'els': 'Els - The caring family member',
            'pjotr': 'Pjotr - The philosophical poet',
            'zanne': 'Zanne - The complex character'
        }
        self.current_character = 'tobor'
        
    def switch_character(self, name):
        name = name.lower()
        if name in self.characters:
            self.current_character = name
            return True
        return False
        
    def get_current_character(self):
        return self.current_character.title()

# Simple STT manager without LED dependencies
class SimpleSTTManager:
    def __init__(self):
        self.is_listening = False
        self.thread = None
        self.stop_flag = threading.Event()
        
        try:
            import vosk
            import pyaudio
            import json
            
                         # Find available Dutch model
             model_path = None
             possible_paths = [
                 "stt/vosk-model-nl-spraakherkenning-0.6-lgraph",
                 "stt/vosk-model-small-nl-0.22",
                 "stt/vosk-model-small-en-us-0.15"
             ]
             
             for path in possible_paths:
                 if os.path.exists(path):
                     model_path = path
                     break
                     
                          if not model_path:
                 print("❌ No STT model found. Available models:")
                 print("   - Install Dutch model with: bash Install.sh")
                 print("   - Continuing with mock STT responses")
                 self.model = None
                 self.rec = None
                 self.audio = None
                 self.stream = None
                 return
                 
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
             
             print(f"🎤 STT initialized successfully with model: {model_path}")
            
        except Exception as e:
            print(f"❌ STT initialization failed: {e}")
            sys.exit(1)
    
    def start_listening(self):
        if not self.is_listening:
            self.is_listening = True
            self.stop_flag.clear()
            self.thread = threading.Thread(target=self._listen_loop)
            self.thread.start()
            
    def stop_listening(self):
        if self.is_listening:
            self.is_listening = False
            self.stop_flag.set()
            if self.thread:
                self.thread.join()
                
    def _listen_loop(self):
        if not self.model:
            print("🎧 STT not available - using mock input mode")
            print("📝 Type messages instead of speaking (press Enter to send)")
            while not self.stop_flag.is_set():
                try:
                    import select
                    import sys
                    if select.select([sys.stdin], [], [], 1.0)[0]:
                        text = input().strip()
                        if text:
                            yield text
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"❌ Input error: {e}")
                    break
            return
            
        print("🎧 Listening... (say character names: mirza, els, pjotr, tobor, zanne)")
        
        while not self.stop_flag.is_set():
            try:
                data = self.stream.read(4000, exception_on_overflow=False)
                if self.rec.AcceptWaveform(data):
                    result = json.loads(self.rec.Result())
                    text = result.get('text', '').strip()
                    if text:
                        yield text
                        
            except Exception as e:
                print(f"❌ STT error: {e}")
                break
                
    def cleanup(self):
        self.stop_listening()
        if hasattr(self, 'stream') and self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'audio') and self.audio:
            self.audio.terminate()

# Simple LLM manager without complex dependencies
class SimpleLLMManager:
    def __init__(self):
        self.api_key = None
        self.load_config()
        
    def load_config(self):
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read('config.ini')
            self.api_key = config.get('openai', 'api_key', fallback=None)
        except:
            print("⚠️ No OpenAI API key found - using mock responses")
            
    def generate_response(self, character, user_input):
        if not self.api_key:
            # Mock responses for testing
            responses = {
                'tobor': f"Tobor here. I processed your input: '{user_input}'. Logic circuits engaged.",
                'mirza': f"Mirza: Oh great, another '{user_input}'. How... fascinating.",
                'els': f"Els: I hear you saying '{user_input}'. Let's talk about this together.",
                'pjotr': f"Pjotr: Your words '{user_input}' remind me of a garden in spring...",
                'zanne': f"Zanne: About '{user_input}'... it's complicated, but I understand."
            }
            return responses.get(character, f"{character}: I heard '{user_input}'")
            
        # Real OpenAI API call (if configured)
        try:
            import openai
            openai.api_key = self.api_key
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are {character}. Respond briefly in character."},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=100,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ LLM error: {e}")
            return f"{character}: I'm having trouble thinking right now. Try again?"

class SimpleVoiceTest:
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
        print("\n" + "="*50)
        print("🤖 TARS-AI Simple Voice Conversation Test")
        print("="*50)
        print("📢 VOICE COMMANDS:")
        print("   - Say 'mirza', 'els', 'pjotr', 'tobor', 'zanne' to switch")
        print("   - Speak naturally to have conversations")
        print("   - Press Ctrl+C to quit")
        print("="*50)
        
    def run(self):
        self.print_help()
        
        current_character = self.character_manager.get_current_character()
        print(f"\n💬 Current character: {current_character}")
        print("🎤 Start speaking...")
        
        try:
            self.stt_manager.start_listening()
            
            for text in self.stt_manager._listen_loop():
                if not self.running:
                    break
                    
                print(f"\n🎧 Heard: '{text}'")
                
                # Check for character switching
                text_lower = text.lower()
                switched = False
                for char_name in self.character_manager.characters.keys():
                    if char_name in text_lower:
                        if self.character_manager.switch_character(char_name):
                            current_character = self.character_manager.get_current_character()
                            print(f"🔄 Switched to: {current_character}")
                            switched = True
                            break
                
                if not switched and text.strip():
                    # Generate response
                    response = self.llm_manager.generate_response(
                        self.character_manager.current_character, 
                        text
                    )
                    print(f"💭 {current_character}: {response}")
                
                print("🎤 Listening...")
                
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.stt_manager.cleanup()

def main():
    # Ensure we're in virtual environment
    if not os.environ.get('VIRTUAL_ENV') and not sys.prefix != sys.base_prefix:
        print("🔧 Starting virtual environment...")
        venv_python = os.path.join(os.path.dirname(__file__), '.venv', 'bin', 'python')
        if os.path.exists(venv_python):
            os.execv(venv_python, [venv_python] + sys.argv)
        else:
            print("❌ Virtual environment not found. Please run: python -m venv .venv")
            sys.exit(1)
    
    print("🚀 Starting Simple Voice Conversation Test...")
    
    # Change to src directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    app = SimpleVoiceTest()
    app.run()

if __name__ == "__main__":
    main() 