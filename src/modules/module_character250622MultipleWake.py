"""
module_character.py
Character Management Module for TARS-AI Application.
This module manages character attributes and dynamic properties for the TARS-AI application.
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
        self.character_card_path = os.path.join("..", self.config['CHAR']['character_card_path'])
        self.character_card = None
        self.char_name = None
        self.description = None
        self.personality = None
        self.world_scenario = None
        self.char_greeting = None
        self.example_dialogue = None
        self.voice_only = config['TTS']['voice_only']
        
        # Profile-related attributes
        self.profiles = {}
        self.profile_dir = None
        
        # Load everything during initialization
        self.load_character_attributes()
        self.load_persona_traits()
        self.load_profiles()

    def load_character_attributes(self):
        """
        Load character attributes from the character card file specified in the config.
        """
        try:
            with open(self.character_card_path, "r") as file:
                data = json.load(file)
            self.char_name = data.get("char_name", "")
            self.description = data.get("description", "")
            self.personality = data.get("personality", "")
            self.scenario = data.get("scenario", "")
            self.char_greeting = data.get("first_mes", "")
            self.example_dialogue = data.get("mes_example", "")
            
            # Format the greeting with placeholders
            if self.char_greeting:
                self.char_greeting = self.char_greeting.replace("{{user}}", self.config['CHAR']['user_name'])
                self.char_greeting = self.char_greeting.replace("{{char}}", self.char_name)
                self.char_greeting = self.char_greeting.replace("{{time}}", datetime.now().strftime("%Y-%m-%d %H:%M"))
            
            self.character_card = f"\nDescription: {self.description}\n"\
                                  f"\nPersonality: {self.personality}\n"\
                                  f"\nWorld Scenario: {self.scenario}\n"
            
            queue_message(f"LOAD: Character loaded: {self.char_name}")
        except FileNotFoundError:
            queue_message(f"ERROR: Character file '{self.character_card_path}' not found.")
        except Exception as e:
            queue_message(f"ERROR: Error while loading character attributes: {e}")

    def load_persona_traits(self):
        """
        Load persona traits from the persona.ini file.
        """
        persona_path = os.path.join("..", 'character', self.char_name, 'persona.ini')
        config = configparser.ConfigParser()
        try:
            config.read(persona_path)
            if 'PERSONA' not in config:
                queue_message("ERROR: [PERSONA] section not found in persona.ini.")
                return
            self.traits = {key: int(value) for key, value in config['PERSONA'].items()}
        except Exception as e:
            queue_message(f"ERROR: Error while loading persona traits: {e}")

    def _derive_profile_dir(self) -> str:
        """
        Determine the directory that holds profile JSONs.
        Priority order:
        1. Explicit `[CHAR] profile_dir` in `config.ini`.
        2. Folder that *actually contains the active character card* plus `/profiles`.
        3. Fallback: global `profiles/` at project root.
        """
        # 1. explicit override
        explicit = self.config["CHAR"].get("profile_dir")
        if explicit:
            return explicit

        # 2. alongside active character card
        if self.character_card_path:
            base_dir = os.path.dirname(os.path.abspath(self.character_card_path))
            return os.path.join(base_dir, "profiles")

        # 3. final fallback
        return "profiles"

    def load_profiles(self):
        """
        Load all psychological profiles during character initialization.
        """
        self.profile_dir = self._derive_profile_dir()
        self.profiles = {}
        
        if not os.path.isdir(self.profile_dir):
            queue_message(f"WARN: profile directory '{self.profile_dir}' niet gevonden – profiles worden overgeslagen")
            return

        profile_count = 0
        for path in glob.glob(os.path.join(self.profile_dir, "*.json")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.profiles.update(data)
                    profile_count += len(data)
                    queue_message(f"LOAD: Loaded profile file: {os.path.basename(path)}")
            except Exception as exc:
                queue_message(f"ERROR: kon profielbestand {path} niet lezen: {exc}")

        queue_message(f"LOAD: {profile_count} profiel-secties geladen uit '{self.profile_dir}'")

    def _flatten_dict(self, section: dict) -> str:
        """
        Zet geneste dict om in key-value regels (eenvoudige flatten).
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

    def get_profile_context(self, user_prompt: str = "") -> str:
        """
        Get relevant profile data as formatted string.
        If user_prompt is provided, prioritize profiles that match names in the prompt.
        """
        if not self.profiles:
            return ""

        # Match op naamcomponent in user_prompt → preferential load
        if user_prompt:
            hits = [k for k in self.profiles if k.split("_")[-1].lower() in user_prompt.lower()]
            keys = hits or list(self.profiles.keys())
        else:
            keys = list(self.profiles.keys())

        blocks: List[str] = []
        for key in keys:
            blocks.append(f"######## {key.upper()} ########")
            blocks.append(self._flatten_dict(self.profiles[key]))
            blocks.append("")
        
        return "\n".join(blocks)
