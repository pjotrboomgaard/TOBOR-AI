"""
module_voice_switcher.py

Dynamic voice switching module for TARS-AI that changes TTS voice
based on which psychological profile is most relevant to the response.
Shares profile cache with module_prompt.py to avoid duplicate loading.
"""

import re
import json
import os
import glob
from typing import Dict, Tuple, Optional, List
from modules.module_messageQue import queue_message

# Try to import the profile cache from module_prompt if it exists
try:
    from modules.module_prompt import _PROFILE_CACHE, _load_profiles
    SHARE_PROFILE_CACHE = True
except ImportError:
    SHARE_PROFILE_CACHE = False
    _PROFILE_CACHE = None

class VoiceSwitcher:
    def __init__(self, config: dict, character_manager=None):
        self.config = config
        self.character_manager = character_manager
        self._profile_cache = {}  # Initialize as empty dict, not None
        self._profile_patterns = {}
        
        # Voice configuration for each persona
        self.voice_profiles = {
            'persoon_zoon': {  # Pjotr
                'name': 'Pjotr',
                'elevenlabs_voice_id': '5BEZKIGvByQrqSymXgwx',
                'azure_voice': 'nl-NL-MaartenNeural',
                'alltalk_voice': 'pjotr_voice',
                'piper_voice': 'nl_NL_male_medium',
                'espeak_voice': 'nl+m3',
                'silero_voice': 'eugene'
            },
            'persoon_moeder': {  # Zanne
                'name': 'Zanne',
                'elevenlabs_voice_id': 'vPyUEx8yh5eRpulx9GVe',
                'azure_voice': 'nl-NL-ColettaNeural',
                'alltalk_voice': 'zanne_voice',
                'piper_voice': 'nl_NL_female_medium',
                'espeak_voice': 'nl+f3',
                'silero_voice': 'xenia'
            },
            'persoon_els': {  # Els
                'name': 'Els',
                'elevenlabs_voice_id': 'RHk7amcwSyv2umxMHEJS',
                'azure_voice': 'nl-NL-FennaNeural',
                'alltalk_voice': 'els_voice',
                'piper_voice': 'nl_NL_female_medium',
                'espeak_voice': 'nl+f5',
                'silero_voice': 'xenia'
            },
            'persoon_mirza': {  # Mirza
                'name': 'Mirza',
                'elevenlabs_voice_id': 'HFPhK8BTs1eEDhkawppF',
                'azure_voice': 'nl-NL-MaartenNeural',
                'alltalk_voice': 'mirza_voice',
                'piper_voice': 'nl_NL_male_x_low',
                'espeak_voice': 'nl+m5',
                'silero_voice': 'random'
            },
            'tobor': {  # Default Tobor
                'name': 'Tobor',
                'elevenlabs_voice_id': 'ZEcx3Wdpj4EvM8PltzHY',
                'azure_voice': 'en-US-Steffan:DragonHDLatestNeural',
                'alltalk_voice': 'tobor_voice',
                'piper_voice': 'en_US_male_medium',
                'espeak_voice': 'en+m3',
                'silero_voice': 'random'
            }
        }
        
        # Load profiles and build patterns immediately during initialization
        queue_message("VOICE: Loading psychological profiles for voice switching...")
        self._load_profiles_and_patterns()
        
        # Default to Tobor
        self.current_persona = 'tobor'
    
    def _derive_profile_dir(self) -> str:
        """Get the profile directory path (same logic as module_prompt.py)."""
        # Check for explicit override
        explicit = self.config["CHAR"].get("profile_dir")
        if explicit:
            return explicit
        
        # Use character card path
        card_path = None
        if self.character_manager and hasattr(self.character_manager, "character_card_path"):
            card_path = self.character_manager.character_card_path
        else:
            raw_cfg_path = self.config["CHAR"].get("character_card_path", "")
            if raw_cfg_path:
                card_path = os.path.join("..", raw_cfg_path)
        
        if card_path:
            base_dir = os.path.dirname(os.path.abspath(card_path))
            return os.path.join(base_dir, "profiles")
        
        return "profiles"
    
    def _load_profiles_and_patterns(self):
        """Load psychological profiles and extract key patterns for matching."""
        profile_dir = self._derive_profile_dir()
        
        # Check if we can use the shared cache from module_prompt
        if SHARE_PROFILE_CACHE and _PROFILE_CACHE is not None:
            queue_message("VOICE: Using shared profile cache from module_prompt")
            self._profile_cache = _PROFILE_CACHE
        else:
            # Load profiles ourselves
            if not os.path.isdir(profile_dir):
                queue_message(f"WARN: Voice switcher - profile directory '{profile_dir}' not found")
                self._profile_cache = {}
                return
            
            # Load all JSON files from the profile directory
            json_files = glob.glob(os.path.join(profile_dir, "*.json"))
            queue_message(f"VOICE: Found {len(json_files)} profile files in '{profile_dir}'")
            
            profiles = {}
            for path in json_files:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        profiles.update(data)
                        queue_message(f"VOICE: Loaded profiles from {os.path.basename(path)}")
                except Exception as exc:
                    queue_message(f"ERROR: Voice switcher - could not read profile {path}: {exc}")
            
            self._profile_cache = profiles
            
            # Update the global cache if module_prompt is available
            if SHARE_PROFILE_CACHE:
                import modules.module_prompt
                modules.module_prompt._PROFILE_CACHE = profiles
        
        # Extract patterns from each profile
        for profile_key, profile_data in self._profile_cache.items():
            patterns = self._extract_patterns_from_profile(profile_key, profile_data)
            self._profile_patterns[profile_key] = patterns
            queue_message(f"VOICE: Extracted {len(patterns)} patterns for {profile_key}")
        
        queue_message(f"INFO: Voice switcher initialized with {len(self._profile_cache)} profiles and {sum(len(p) for p in self._profile_patterns.values())} total patterns")
    
    def _extract_patterns_from_profile(self, profile_key: str, profile_data: dict) -> List[str]:
        """Extract unique patterns from a psychological profile."""
        patterns = []
        
        # Helper to extract text values from nested structures
        def extract_values(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    extract_values(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for item in obj:
                    extract_values(item, path)
            elif isinstance(obj, str) and len(obj) > 3:  # Only meaningful strings
                # Clean and add to patterns
                clean_val = obj.lower().strip()
                if clean_val and not clean_val.isdigit():
                    patterns.append(clean_val)
        
        extract_values(profile_data)
        
        # Add specific identifiers
        if 'identificatie' in profile_data:
            ident = profile_data['identificatie']
            if 'voornaam' in ident:
                patterns.append(ident['voornaam'].lower())
            if 'werk' in ident:
                patterns.append(ident['werk'].lower())
            if 'opleiding' in ident:
                patterns.append(ident['opleiding'].lower())
        
        # Add key psychological terms
        if 'persoonlijkheidsprofiel' in profile_data:
            prof = profile_data['persoonlijkheidsprofiel']
            if 'coping_primary' in prof:
                patterns.extend([c.lower() for c in prof['coping_primary']])
            if 'hechtingsstijl' in prof:
                patterns.append(prof['hechtingsstijl'].lower())
            if 'schema_domeinen' in prof:
                patterns.extend([s.lower() for s in prof['schema_domeinen']])
        
        # Add event descriptions
        if 'gebeurtenissen' in profile_data:
            for event in profile_data['gebeurtenissen']:
                if 'titel' in event:
                    patterns.append(event['titel'].lower())
                if 'omschrijving' in event:
                    patterns.append(event['omschrijving'].lower())
        
        # Add therapy goals and complaints
        if 'therapiedoelen' in profile_data:
            patterns.extend([g.lower() for g in profile_data['therapiedoelen']])
        
        if 'huidige_klachten' in profile_data:
            klachten = profile_data['huidige_klachten']
            if 'klachtenlijst' in klachten:
                patterns.extend([k.lower() for k in klachten['klachtenlijst']])
        
        # Remove duplicates
        return list(set(patterns))
    
    def detect_persona_from_content(self, text: str) -> str:
        """
        Detect which persona's profile is most relevant to the text content.
        Returns the detected persona key or 'tobor' as default.
        """
        if not self._profile_patterns:
            return 'tobor'
        
        text_lower = text.lower()
        
        # Score each profile based on pattern matches
        profile_scores = {}
        
        for profile_key, patterns in self._profile_patterns.items():
            score = 0
            matched_patterns = []
            
            for pattern in patterns:
                # Check for substring matches (more flexible than exact word matching)
                if len(pattern) > 10:  # Longer patterns - look for partial matches
                    if pattern in text_lower or any(word in pattern for word in text_lower.split() if len(word) > 4):
                        score += 2
                        matched_patterns.append(pattern[:30] + "...")
                elif pattern in text_lower:  # Shorter patterns - exact match
                    score += 1
                    matched_patterns.append(pattern)
            
            # Bonus points for specific persona names
            persona_names = {
                'persoon_zoon': ['pjotr', 'zoon'],
                'persoon_moeder': ['zanne', 'moeder', 'mama'],
                'persoon_els': ['els', 'oma', 'grootmoeder'],
                'persoon_mirza': ['mirza', 'opa', 'grootvader']
            }
            
            if profile_key in persona_names:
                for name in persona_names[profile_key]:
                    if name in text_lower:
                        score += 5  # Strong weight for direct name reference
                        matched_patterns.append(f"NAME: {name}")
            
            if score > 0:
                profile_scores[profile_key] = (score, matched_patterns)
        
        # If no matches found, return current persona
        if not profile_scores:
            return self.current_persona
        
        # Return persona with highest score
        best_match = max(profile_scores.items(), key=lambda x: x[1][0])
        detected_persona = best_match[0]
        score, patterns = best_match[1]
        
        # Log the detection with matched patterns for debugging
        queue_message(f"VOICE: Detected persona '{detected_persona}' (score: {score})")
        if len(patterns) <= 3:
            queue_message(f"VOICE: Matched patterns: {patterns}")
        else:
            queue_message(f"VOICE: Matched {len(patterns)} patterns including: {patterns[:3]}")
        
        return detected_persona
    
    def get_voice_config(self, persona_key: str, tts_option: str) -> Tuple[str, Dict[str, str]]:
        """
        Get the voice configuration for the detected persona and TTS option.
        Returns (persona_name, voice_config_dict)
        """
        # Map profile keys to voice profiles
        profile_mapping = {
            'persoon_zoon': 'persoon_zoon',
            'persoon_moeder': 'persoon_moeder',
            'persoon_els': 'persoon_els',
            'persoon_mirza': 'persoon_mirza'
        }
        
        voice_key = profile_mapping.get(persona_key, 'tobor')
        
        if voice_key not in self.voice_profiles:
            voice_key = 'tobor'
        
        profile = self.voice_profiles[voice_key]
        voice_config = {}
        
        # Map TTS option to appropriate voice setting
        if tts_option == 'elevenlabs':
            voice_config['voice_id'] = profile['elevenlabs_voice_id']
            voice_config['model_id'] = self.config['TTS'].get('model_id', 'eleven_multilingual_v2')
        elif tts_option == 'azure':
            voice_config['tts_voice'] = profile['azure_voice']
        elif tts_option == 'alltalk':
            voice_config['tts_voice'] = profile['alltalk_voice']
        elif tts_option == 'piper':
            voice_config['tts_voice'] = profile['piper_voice']
        elif tts_option == 'espeak':
            voice_config['tts_voice'] = profile['espeak_voice']
        elif tts_option == 'silero':
            voice_config['tts_voice'] = profile['silero_voice']
        
        return profile['name'], voice_config
    
    def analyze_and_switch(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Analyze text and return appropriate voice configuration.
        Returns (persona_name, voice_config)
        """
        # Detect persona from text content
        detected_persona = self.detect_persona_from_content(text)
        
        # Update current persona
        self.current_persona = detected_persona
        
        # Get voice configuration
        tts_option = self.config['TTS'].get('ttsoption', 'elevenlabs')
        persona_name, voice_config = self.get_voice_config(detected_persona, tts_option)
        
        # Log the switch
        queue_message(f"VOICE: Switching to {persona_name}'s voice profile")
        
        return persona_name, voice_config
    
    def should_switch_voice(self, text: str) -> bool:
        """
        Determine if voice should be switched based on text content.
        """
        detected_persona = self.detect_persona_from_content(text)
        return detected_persona != self.current_persona


# Enhanced TTS module integration
async def generate_tts_audio_with_voice_switch(text, voice_switcher, config):
    """
    Enhanced TTS generation that switches voice based on persona detection.
    """
    from modules.module_tts import generate_tts_audio
    
    # Analyze text and get voice configuration
    persona_name, voice_config = voice_switcher.analyze_and_switch(text)
    
    # Update config with new voice settings
    ttsoption = config['TTS']['ttsoption']
    
    # Temporarily update the config with detected voice
    original_values = {}
    for key, value in voice_config.items():
        if key in config['TTS']:
            original_values[key] = config['TTS'][key]
            config['TTS'][key] = value
    
    try:
        # Generate TTS with switched voice
        async for chunk in generate_tts_audio(
            text=text,
            ttsoption=ttsoption,
            azure_api_key=config['TTS'].get('azure_api_key'),
            azure_region=config['TTS'].get('azure_region'),
            ttsurl=config['TTS'].get('ttsurl'),
            toggle_charvoice=True,
            tts_voice=voice_config.get('tts_voice', config['TTS'].get('tts_voice'))
        ):
            yield chunk
    finally:
        # Restore original config values
        for key, value in original_values.items():
            config['TTS'][key] = value


# Integration helper for module_main.py
def integrate_voice_switcher(memory_manager, character_manager, config):
    """
    Helper function to integrate voice switcher into the main module.
    This should be called from module_main.py after managers are initialized.
    """
    # Create voice switcher instance
    voice_switcher = VoiceSwitcher(config, character_manager)
    
    # Store it in a global or pass it to relevant modules
    return voice_switcher
