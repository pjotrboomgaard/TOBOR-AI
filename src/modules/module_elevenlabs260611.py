"""
module_elevenlabs.py

ElevenLabs TTS module with dynamic voice switching support.
"""

import io
import re
import asyncio
import wave
from modules.module_config import load_config
from elevenlabs.client import ElevenLabs
from modules.module_messageQue import queue_message

CONFIG = load_config()

# ✅ Initialize ElevenLabs client globally
elevenlabs_client = ElevenLabs(api_key=CONFIG['TTS']['elevenlabs_api_key'])

async def synthesize_elevenlabs(chunk, voice_id=None):
    """
    Synthesize a chunk of text into an AudioSegment using ElevenLabs API with dynamic voice support.
    
    Parameters:
    - chunk (str): A single sentence or phrase.
    - voice_id (str): ElevenLabs voice ID (overrides config if provided).
    
    Returns:
    - BytesIO: A buffer containing the generated audio.
    """
    try:
        # Use provided voice_id or fall back to config default
        if voice_id is None:
            voice_id = CONFIG['TTS']['voice_id']
        
        model_id = CONFIG['TTS']['model_id']
        
        queue_message(f"INFO: Synthesizing with ElevenLabs voice ID: {voice_id}")
        
        # ✅ Generate audio using ElevenLabs API
        audio_generator = elevenlabs_client.text_to_speech.convert(
            text=chunk,
            voice_id=voice_id,
            model_id=model_id,
            output_format="mp3_44100_128",
        )
        
        # ✅ Join the generator output into a single byte object
        audio_bytes = b"".join(audio_generator)
        
        if not audio_bytes:  # ✅ Ensure the API response is valid
            queue_message(f"ERROR: ElevenLabs returned an empty response for chunk: {chunk}")
            return None
        
        # Convert raw audio bytes to BytesIO buffer
        audio_buffer = io.BytesIO(audio_bytes)
        audio_buffer.seek(0)  # Reset buffer position
        
        return audio_buffer  # ✅ Return the processed audio buffer
        
    except Exception as e:
        queue_message(f"ERROR: ElevenLabs TTS synthesis failed: {e}")
        return None


async def text_to_speech_with_pipelining_elevenlabs(text, voice_id=None):
    """
    Converts text to speech using the ElevenLabs API with dynamic voice switching 
    and streams audio as it's generated.
    
    Parameters:
    - text (str): The text to convert to speech
    - voice_id (str): Optional voice ID to use (overrides config if provided)
    
    Yields:
    - BytesIO: Processed audio chunks as they're generated.
    """
    try:
        # Use provided voice_id or fall back to config default
        if voice_id is None:
            voice_id = CONFIG['TTS']['voice_id']
        
        queue_message(f"INFO: Starting ElevenLabs TTS with voice ID: {voice_id}")
        
        # ✅ Split text into sentences before sending to ElevenLabs
        chunks = re.split(r'(?<=\.)\s', text)  # Split at sentence boundaries
        
        # ✅ Process each sentence separately
        for chunk in chunks:
            if chunk.strip():  # ✅ Ignore empty chunks
                wav_buffer = await synthesize_elevenlabs(chunk.strip(), voice_id)  # ✅ Generate audio
                if wav_buffer:
                    yield wav_buffer  # ✅ Stream audio chunks dynamically
                    
    except Exception as e:
        queue_message(f"ERROR: ElevenLabs pipelined TTS failed: {e}")


async def get_available_voices():
    """
    Get list of available voices from ElevenLabs API.
    
    Returns:
    - list: List of available voices with their IDs and names
    """
    try:
        voices = elevenlabs_client.voices.get_all()
        voice_list = []
        
        for voice in voices.voices:
            voice_info = {
                'voice_id': voice.voice_id,
                'name': voice.name,
                'category': voice.category,
                'settings': voice.settings
            }
            voice_list.append(voice_info)
            
        queue_message(f"INFO: Retrieved {len(voice_list)} voices from ElevenLabs")
        return voice_list
        
    except Exception as e:
        queue_message(f"ERROR: Failed to get ElevenLabs voices: {e}")
        return []


async def validate_voice_id(voice_id):
    """
    Validate if a voice ID exists in ElevenLabs.
    
    Parameters:
    - voice_id (str): Voice ID to validate
    
    Returns:
    - bool: True if voice exists, False otherwise
    """
    try:
        voices = await get_available_voices()
        valid_ids = [voice['voice_id'] for voice in voices]
        
        is_valid = voice_id in valid_ids
        if not is_valid:
            queue_message(f"WARN: Voice ID {voice_id} not found in available voices")
        
        return is_valid
        
    except Exception as e:
        queue_message(f"ERROR: Voice validation failed: {e}")
        return False


# Voice mapping for character personas
VOICE_MAP = {
    "zanne": "vPyUEx8yh5eRpulx9GVe",    # Zanne's voice ID
    "pjotr": "5BEZKIGvByQrqSymXgwx",    # Pjotr's voice ID  
    "els": "RHk7amcwSyv2umxMHEJS",      # Els's voice ID
    "mirza": "HFPhK8BTs1eEDhkawppF"     # Mirza's voice ID
}


def get_voice_for_character(character_name):
    """
    Get the voice ID for a specific character.
    
    Parameters:
    - character_name (str): Name of the character
    
    Returns:
    - str: Voice ID for the character, or default if not found
    """
    character_lower = character_name.lower()
    voice_id = VOICE_MAP.get(character_lower)
    
    if voice_id:
        queue_message(f"INFO: Found voice for character '{character_name}': {voice_id}")
        return voice_id
    else:
        default_voice = CONFIG['TTS']['voice_id']
        queue_message(f"WARN: No specific voice for character '{character_name}', using default: {default_voice}")
        return default_voice


async def test_voice_synthesis(test_text="Hello, this is a test.", voice_id=None):
    """
    Test voice synthesis with a given voice ID.
    
    Parameters:
    - test_text (str): Text to synthesize for testing
    - voice_id (str): Voice ID to test (optional)
    
    Returns:
    - bool: True if synthesis successful, False otherwise
    """
    try:
        if voice_id is None:
            voice_id = CONFIG['TTS']['voice_id']
        
        queue_message(f"INFO: Testing voice synthesis with ID: {voice_id}")
        
        async for chunk in text_to_speech_with_pipelining_elevenlabs(test_text, voice_id):
            if chunk:
                queue_message(f"INFO: Voice test successful for ID: {voice_id}")
                return True
        
        queue_message(f"WARN: Voice test failed - no audio generated for ID: {voice_id}")
        return False
        
    except Exception as e:
        queue_message(f"ERROR: Voice test failed for ID {voice_id}: {e}")
        return False
