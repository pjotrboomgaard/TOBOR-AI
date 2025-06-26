"""
module_character.py

Character Management Module for TARS-AI Application.

This module manages character attributes and dynamic properties for the TARS-AI application.

MULTI-CHARACTER SYSTEM:
======================

The CharacterManager now supports multiple characters that can be switched dynamically
based on wake word detection. Here's how it works:

1. CONFIGURATION:
   Add a [CHARACTERS] section to your config.ini with the format:
   character_name = card_path, voice_id, tts_voice
   
   Example:
   [CHARACTERS]
   mirza = character/Mirza/Mirza.json, vPyUEx8yh5eRpulx9GVe, en-US-Steffan:DragonHDLatestNeural
   els = character/Els/Els.json, 5BEZKIGvByQrqSymXgwx, nl-NL-MaartenNeural

2. WAKE WORD DETECTION:
   The STT module detects wake words like "mirza", "els", "zanne", "pjotr", "tobor"
   and automatically switches the active character.

3. CHARACTER-SPECIFIC FEATURES:
   - Each character has their own voice (voice_id for ElevenLabs, tts_voice for Azure)
   - Each character has their own personality, greeting, and psychology profiles
   - Memory is shared across characters but responses are character-specific

4. FALLBACK MODE:
   If no [CHARACTERS] section exists, the system falls back to single-character mode
   using the traditional [CHAR] section configuration.

USAGE:
======
- Say any character's wake word to activate them
- The system will switch to that character and use their voice
- All subsequent interactions will be with that character until another wake word is detected
"""

# === Standard Libraries ===
import json
import glob
import os
from datetime import datetime
import configparser
from typing import Dict, List

from modules.module_messageQue import queue_message

class CharacterManager:
    """
    Manages character attributes and dynamic properties for TARS-AI.
    """
    def __init__(self, config):
        self.config = config
        self.characters = {}  # Dictionary to store all characters
        self.current_character = None  # Currently active character
        self.voice_only = config['TTS']['voice_only']
        
        # Initialize default attributes
        self.char_name = None
        self.description = None
        self.personality = None
        self.scenario = None
        self.char_greeting = None
        self.example_dialogue = None
        self.character_card = None
        self.traits = {}
        self.psychology_cache = None
        
        # Load all characters if CHARACTERS section exists
        if 'CHARACTERS' in config:
            self.load_all_characters()
        else:
            # Fallback to single character mode
            self.load_single_character()
    
    def load_all_characters(self):
        """
        Load all characters from the CHARACTERS section in config.
        """
        try:
            characters_config = self.config['CHARACTERS']
            
            for char_name, char_config in characters_config.items():
                # Skip configuration settings that aren't character definitions
                if char_name in ['enable_multi_character']:
                    continue
                    
                # Parse character config: card_path, voice_id, tts_voice
                config_parts = [part.strip() for part in char_config.split(',')]
                if len(config_parts) >= 3:
                    card_path = config_parts[0]
                    voice_id = config_parts[1]
                    tts_voice = config_parts[2]
                    
                    # Load character data
                    character_data = self.load_character_data(card_path, char_name, voice_id, tts_voice)
                    if character_data:
                        self.characters[char_name.lower()] = character_data
                        queue_message(f"LOAD: Character loaded: {character_data['char_name']} ({char_name})")
                else:
                    queue_message(f"ERROR: Invalid character config for {char_name}: {char_config}")
            
            # Set the first character as default
            if self.characters:
                first_char = next(iter(self.characters.values()))
                self.switch_to_character(list(self.characters.keys())[0])
                queue_message(f"LOAD: Default character set to: {first_char['char_name']}")
            else:
                queue_message("ERROR: No characters loaded successfully")
                
        except Exception as e:
            queue_message(f"ERROR: Failed to load characters: {e}")
            # Fallback to single character mode
            self.load_single_character()
    
    def load_single_character(self):
        """
        Load a single character (legacy mode).
        """
        try:
            character_card_path = os.path.join("..", self.config['CHAR']['character_card_path'])
            char_name = os.path.basename(character_card_path).replace('.json', '')
            
            # Handle TTS config properly - it's a dataclass, not a dict
            tts_config = self.config['TTS']
            voice_id = getattr(tts_config, 'voice_id', '')
            tts_voice = getattr(tts_config, 'tts_voice', '')
            
            character_data = self.load_character_data(
                character_card_path, 
                char_name,
                voice_id,
                tts_voice
            )
            
            if character_data:
                self.characters[char_name.lower()] = character_data
                self.switch_to_character(char_name.lower())
                queue_message(f"LOAD: Single character loaded: {character_data['char_name']}")
            
        except Exception as e:
            queue_message(f"ERROR: Failed to load single character: {e}")
    
    def load_character_data(self, card_path, char_name, voice_id, tts_voice):
        """
        Load character data from a character card file.
        """
        try:
            # Handle path resolution more robustly
            if os.path.isabs(card_path):
                full_path = card_path
            else:
                # Try multiple path combinations to find the file
                possible_paths = [
                    os.path.join("..", card_path),  # Original logic
                    card_path,  # Direct path
                    os.path.join("character", char_name, f"{char_name}.json"),  # Construct from char_name
                    os.path.join("..", "character", char_name, f"{char_name}.json")  # Full construct
                ]
                
                full_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        full_path = path
                        break
                
                if not full_path:
                    queue_message(f"ERROR: Character file not found. Tried paths: {possible_paths}")
                    return None
            
            with open(full_path, "r") as file:
                data = json.load(file)

            char_data = {
                'char_name': char_name.title(),  # Use the actual character name from config, not from JSON
                'description': data.get("description", ""),
                'personality': data.get("personality", ""),
                'scenario': data.get("scenario", ""),
                'char_greeting': data.get("first_mes", ""),
                'example_dialogue': data.get("mes_example", ""),
                'voice_id': voice_id,
                'tts_voice': tts_voice,
                'card_path': card_path,
                'psychology_cache': None
            }

            # Format the greeting with placeholders
            if char_data['char_greeting']:
                char_data['char_greeting'] = char_data['char_greeting'].replace("{{user}}", self.config['CHAR']['user_name'])
                char_data['char_greeting'] = char_data['char_greeting'].replace("{{char}}", char_data['char_name'])
                char_data['char_greeting'] = char_data['char_greeting'].replace("{{time}}", datetime.now().strftime("%Y-%m-%d %H:%M"))

            char_data['character_card'] = f"\nDescription: {char_data['description']}\n"\
                                         f"\nPersonality: {char_data['personality']}\n"\
                                         f"\nWorld Scenario: {char_data['scenario']}\n"

            # Load persona traits for this character
            char_data['traits'] = self.load_persona_traits(char_name)
            
            # Load character psychology for this character
            char_data['psychology_cache'] = self.load_character_psychology(char_name)

            return char_data
            
        except FileNotFoundError:
            queue_message(f"ERROR: Character file '{card_path}' not found.")
            return None
        except Exception as e:
            queue_message(f"ERROR: Error while loading character {char_name}: {e}")
            return None
    
    def switch_to_character(self, character_name):
        """
        Switch to a specific character by name.
        """
        character_name = character_name.lower()
        if character_name in self.characters:
            self.current_character = character_name
            char_data = self.characters[character_name]
            
            # Update current character properties for compatibility
            self.char_name = char_data['char_name']
            self.description = char_data['description']
            self.personality = char_data['personality']
            self.scenario = char_data['scenario']
            self.char_greeting = char_data['char_greeting']
            self.example_dialogue = char_data['example_dialogue']
            self.character_card = char_data['character_card']
            self.traits = char_data['traits']
            self.psychology_cache = char_data['psychology_cache']
            
            return True
        else:
            queue_message(f"ERROR: Character '{character_name}' not found")
            return False

    def get_current_character_voice_config(self):
        """
        Get the voice configuration for the current character.
        """
        if self.current_character and self.current_character in self.characters:
            char_data = self.characters[self.current_character]
            return {
                'voice_id': char_data['voice_id'],
                'tts_voice': char_data['tts_voice']
            }
        return None
    
    def get_character_names(self):
        """
        Get list of all available character names.
        """
        return list(self.characters.keys())

    def load_character_attributes(self):
        """
        Load character attributes from the character card file specified in the config.
        DEPRECATED: Use load_character_data instead.
        """
        pass

    def load_persona_traits(self, char_name):
        """
        Load persona traits from the persona.ini file for a specific character.
        """
        persona_path = os.path.join("..", 'character', char_name, 'persona.ini')
        config = configparser.ConfigParser()

        try:
            config.read(persona_path)
            if 'PERSONA' not in config:
                return {}

            return {key: int(value) for key, value in config['PERSONA'].items()}
        except Exception as e:
            queue_message(f"ERROR: Error while loading persona traits for {char_name}: {e}")
            return {}

    def _derive_characterpsychology_dir(self, char_name) -> str:
        """
        Determine the directory that holds character psychology JSONs for a specific character.
        """
        # Explicit override
        explicit = self.config["CHAR"].get("characterpsychology_dir")
        if explicit:
            return explicit

        # Character-specific directory - try multiple path variations with different capitalizations
        possible_paths = [
            # Try with original case
            os.path.join("..", "character", char_name, "characterpsychology"),
            os.path.join("character", char_name, "characterpsychology"),
            os.path.join("..", "..", "character", char_name, "characterpsychology"),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "character", char_name, "characterpsychology")),
            # Try with title case (first letter capitalized)
            os.path.join("..", "character", char_name.title(), "characterpsychology"),
            os.path.join("character", char_name.title(), "characterpsychology"),
            os.path.join("..", "..", "character", char_name.title(), "characterpsychology"),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "character", char_name.title(), "characterpsychology")),
            # Try with uppercase
            os.path.join("..", "character", char_name.upper(), "characterpsychology"),
            os.path.join("character", char_name.upper(), "characterpsychology"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
                
        # Return the most likely path even if it doesn't exist
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "character", char_name, "characterpsychology"))

    def _load_character_psychology(self, psychology_dir: str) -> Dict[str, dict]:
        """
        Load all `*.json` files in the character psychology directory.
        """
        psychology_data: Dict[str, dict] = {}
        
        queue_message(f"DEBUG: Attempting to load psychology from: {psychology_dir}")
        queue_message(f"DEBUG: Directory exists: {os.path.isdir(psychology_dir)}")
        
        if not os.path.isdir(psychology_dir):
            queue_message(f"DEBUG: Psychology directory not found: {psychology_dir}")
            return {}

        json_files = glob.glob(os.path.join(psychology_dir, "*.json"))
        queue_message(f"DEBUG: Found JSON files: {json_files}")

        for path in json_files:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    psychology_data.update(data)
                    queue_message(f"DEBUG: Loaded {len(data)} sections from {path}")
            except Exception as exc:
                queue_message(f"ERROR: Could not read character psychology file {path}: {exc}")

        if psychology_data:
            queue_message(f"INFO: {len(psychology_data)} character psychology sections loaded for character")
        else:
            queue_message(f"WARNING: No psychology data loaded from {psychology_dir}")
        return psychology_data

    def load_character_psychology(self, char_name):
        """
        Initialize character psychology data for a specific character.
        """
        psychology_dir = self._derive_characterpsychology_dir(char_name)
        return self._load_character_psychology(psychology_dir)

    def _flatten_dict(self, section: dict) -> str:
        """
        Convert nested dictionary to key-value lines (simple flatten).
        """
        lines: List[str] = []

        def walk(prefix: str, obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    walk(f"{prefix}{k}.", v)
            elif isinstance(obj, list):
                for i, itm in enumerate(obj, 1):
                    walk(f"{prefix}{i}.", itm)
            else:
                lines.append(f"{prefix[:-1]}: {obj}")

        walk("", section)
        return "\n".join(lines)

    def get_psychology_context(self, user_prompt: str) -> str:
        """
        Export relevant character psychology data as string for current character.
        
        Parameters:
        - user_prompt (str): The user's input to match against psychology profiles
        
        Returns:
        - str: Formatted psychology context for the prompt
        """
        if not self.psychology_cache:
            return ""

        user_prompt_lower = user_prompt.lower()
        relevant_keys = []
        
        # Enhanced matching logic for specific topics and names
        name_mappings = {
            'els': ['els', 'grandmother', 'oma'],
            'mama': ['mama', 'mother', 'moeder'],
            'mirza': ['mirza', 'grandfather', 'opa'],
            'pjotr': ['pjotr', 'son', 'zoon'],
            'tobor': ['tobor', 'robot']
        }
        
        topic_mappings = {
            'memories': ['herinnering', 'memory', 'memories', 'verhaal', 'gebeurtenis', 'specifiek'],
            'core_identity': ['identiteit', 'identity', 'wie ben', 'persoonlijkheid'],
            'wereldbeeld': ['wereldbeeld', 'worldview', 'denk over', 'geloof', 'filosofie']
        }
        
        # Check for specific person mentions
        for person, keywords in name_mappings.items():
            if any(keyword in user_prompt_lower for keyword in keywords):
                # Add sections about this person
                person_keys = [k for k in self.psychology_cache.keys() if f"_{person}" in k.lower()]
                relevant_keys.extend(person_keys)
                
                # If asking for memories specifically, prioritize memory sections
                if any(mem_word in user_prompt_lower for mem_word in topic_mappings['memories']):
                    memory_keys = [k for k in person_keys if 'memories' in k.lower()]
                    if memory_keys:
                        relevant_keys = memory_keys  # Only show memories for this person
                        break
        
        # Check for topic-specific requests
        for topic, keywords in topic_mappings.items():
            if any(keyword in user_prompt_lower for keyword in keywords):
                topic_keys = [k for k in self.psychology_cache.keys() if topic in k.lower()]
                relevant_keys.extend(topic_keys)
        
        # If no specific matches, use original logic but limit to most relevant
        if not relevant_keys:
            hits = [k for k in self.psychology_cache if k.split("_")[-1].lower() in user_prompt_lower]
            relevant_keys = hits[:3] if hits else list(self.psychology_cache.keys())[:3]  # Limit to 3 sections
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keys = []
        for key in relevant_keys:
            if key not in seen:
                seen.add(key)
                unique_keys.append(key)
        
        # Build the context blocks
        blocks: List[str] = []
        for key in unique_keys[:5]:  # Limit to 5 most relevant sections
            blocks.append(f"######## {key.upper()} ########")
            blocks.append(self._flatten_dict(self.psychology_cache[key]))
            blocks.append("")
        
        # If we have memory-specific content, add a strong instruction
        if any('memories' in key.lower() for key in unique_keys):
            instruction = "INSTRUCTIE: Gebruik ALLEEN de bovenstaande specifieke herinneringen. Verzin geen nieuwe gebeurtenissen of details die niet expliciet vermeld staan."
            blocks.insert(0, instruction)
            blocks.insert(1, "")
        
        return "\n".join(blocks)