"""
module_tts.py

Text-to-Speech (TTS) module for TARS-AI application.

Handles TTS functionality to convert text into audio using:
- Azure Speech SDK
- Local tools (e.g., espeak-ng)
- Server-based TTS systems

"""

# === Standard Libraries ===
import requests
import os 
from datetime import datetime
import numpy as np
import sounddevice as sd
import soundfile as sf
from io import BytesIO
import asyncio
from scipy import signal
import configparser

from modules.module_piper import text_to_speech_with_pipelining_piper
from modules.module_silero import text_to_speech_with_pipelining_silero
from modules.module_espeak import text_to_speech_with_pipelining_espeak
from modules.module_alltalk import text_to_speech_with_pipelining_alltalk
from modules.module_elevenlabs import text_to_speech_with_pipelining_elevenlabs
from modules.module_azure import text_to_speech_with_pipelining_azure
from modules.module_messageQue import queue_message

def load_audio_fx_config():
    """Load audio effects configuration from config file."""
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    robot_fx_enabled = config.getboolean('AUDIOFX', 'robot_fx', fallback=True)
    robot_fx_depth = config.getfloat('AUDIOFX', 'robot_fx_depth', fallback=1.0)
    
    return robot_fx_enabled, robot_fx_depth

def apply_robot_fx(audio_data, sample_rate=22050, depth=1.0):
    """
    Apply robotization effects to audio data.
    
    Parameters:
    - audio_data: numpy array of audio samples
    - sample_rate: sample rate of the audio
    - depth: effect intensity (0.0 = no effect, 1.0 = full effect)
    
    Returns:
    - processed audio data as numpy array
    """
    if depth <= 0:
        return audio_data
    
    try:
        # Convert to float for processing
        audio = audio_data.astype(np.float32)
        original_audio = audio.copy()
        
        # 1. Bit crushing effect (reduces bit depth for digital distortion)
        bit_depth = max(2, int(16 * (1 - depth * 0.7)))  # Reduce bit depth based on intensity
        max_val = 2 ** (bit_depth - 1)
        audio = np.round(audio / 32768 * max_val) / max_val * 32768
        
        # 2. Ring modulation (classic robot voice effect)
        mod_freq = 30 + (depth * 20)  # Modulation frequency between 30-50 Hz
        t = np.arange(len(audio)) / sample_rate
        ring_mod = np.sin(2 * np.pi * mod_freq * t)
        audio = audio * (0.7 + 0.3 * ring_mod * depth)
        
        # 3. Formant shifting (changes vocal characteristics)
        # Simple pitch shifting using resampling
        shift_factor = 1.0 + (depth * 0.15)  # Slight pitch shift
        indices = np.arange(0, len(audio), shift_factor)
        indices = indices[indices < len(audio)].astype(int)
        if len(indices) > 0:
            shifted_audio = audio[indices]
            # Pad or truncate to original length
            if len(shifted_audio) < len(audio):
                shifted_audio = np.pad(shifted_audio, (0, len(audio) - len(shifted_audio)), 'constant')
            else:
                shifted_audio = shifted_audio[:len(audio)]
            audio = shifted_audio
        
        # 4. High-pass filter (removes some low frequencies for metallic sound)
        nyquist = sample_rate * 0.5
        high_cutoff = 200 + (depth * 300)  # Cutoff between 200-500 Hz
        if high_cutoff < nyquist:
            b, a = signal.butter(2, high_cutoff / nyquist, btype='high')
            audio = signal.filtfilt(b, a, audio)
        
        # 5. Add slight distortion
        drive = 1.0 + (depth * 2.0)
        audio = np.tanh(audio * drive / 32768) * 32768
        
        # 6. Mix with original based on depth
        audio = original_audio * (1 - depth) + audio * depth
        
        # Normalize and convert back to int16
        audio = np.clip(audio, -32768, 32767).astype(np.int16)
        
        return audio
        
    except Exception as e:
        queue_message(f"ERROR: Robot FX processing failed: {e}")
        return audio_data.astype(np.int16)

def update_tts_settings(ttsurl):
    """
    Updates TTS settings using a POST request to the specified server.

    Parameters:
    - ttsurl: The URL of the TTS server.
    """

    url = f"{ttsurl}/set_tts_settings"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    payload = {
        "stream_chunk_size": 100,
        "temperature": 0.75,
        "speed": 1,
        "length_penalty": 1.0,
        "repetition_penalty": 5,
        "top_p": 0.85,
        "top_k": 50,
        "enable_text_splitting": True
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            queue_message(f"LOAD: TTS Settings updated successfully.")
        else:
            queue_message(f"ERROR: Failed to update TTS settings. Status code: {response.status_code}")
            queue_message(f"INFO: Response: {response.text}")
    except Exception as e:
        queue_message(f"ERROR: TTS update failed: {e}")

def play_audio_stream(tts_stream, samplerate=22050, channels=1, gain=1.0, normalize=False, apply_robot_effects=False):
    """
    Play the audio stream through speakers using SoundDevice with volume/gain adjustment and optional robot effects.
    
    Parameters:
    - tts_stream: Stream of audio data in chunks.
    - samplerate: The sample rate of the audio data.
    - channels: The number of audio channels (e.g., 1 for mono, 2 for stereo).
    - gain: A multiplier for adjusting the volume. Default is 1.0 (no change).
    - normalize: Whether to normalize the audio to use the full dynamic range.
    - apply_robot_effects: Whether to apply robotization effects.
    """
    try:
        # Load robot FX settings if needed
        robot_fx_enabled, robot_fx_depth = False, 1.0
        if apply_robot_effects:
            robot_fx_enabled, robot_fx_depth = load_audio_fx_config()
        
        with sd.OutputStream(samplerate=samplerate, channels=channels, dtype='int16', blocksize=4096) as stream:
            for chunk in tts_stream:
                if chunk:
                    # Convert bytes to int16 using numpy
                    audio_data = np.frombuffer(chunk, dtype='int16')
                    
                    # Apply robot effects if enabled
                    if apply_robot_effects and robot_fx_enabled:
                        audio_data = apply_robot_fx(audio_data, samplerate, robot_fx_depth)
                    
                    # Normalize the audio (if enabled)
                    if normalize:
                        max_value = np.max(np.abs(audio_data))
                        if max_value > 0:
                            audio_data = audio_data / max_value * 32767
                    
                    # Apply gain adjustment
                    audio_data = np.clip(audio_data * gain, -32768, 32767).astype('int16')

                    # Write the adjusted audio data to the stream
                    stream.write(audio_data)
                else:
                    queue_message(f"ERROR: Received empty chunk.")
    except Exception as e:
        queue_message(f"ERROR: Error during audio playback: {e}")


async def generate_tts_audio(text, ttsoption, azure_api_key=None, azure_region=None, ttsurl=None, toggle_charvoice=True, tts_voice=None):
    """
    Generate TTS audio for the given text using the specified TTS system with optional robot effects.

    Parameters:
    - text (str): The text to convert into speech.
    - ttsoption (str): The TTS system to use (Azure, server-based, or local).
    - ttsurl (str): The base URL of the TTS server (for server-based TTS).
    - toggle_charvoice (bool): Flag indicating whether to use character voice for TTS.
    - tts_voice (str): The TTS speaker/voice configuration.
    """
    try:
        # Load robot FX settings
        robot_fx_enabled, robot_fx_depth = load_audio_fx_config()
        apply_effects = robot_fx_enabled and ttsoption == "elevenlabs"
        
        # Azure TTS generation
        if ttsoption == "azure":
           async for chunk in text_to_speech_with_pipelining_azure(text):
                yield chunk

        # Local TTS generation using `espeak-ng`
        elif ttsoption == "espeak":
            async for chunk in text_to_speech_with_pipelining_espeak(text):
                yield chunk

        elif ttsoption == "alltalk":
            async for chunk in text_to_speech_with_pipelining_alltalk(text):
                yield chunk
                
        # Local TTS generation using local onboard PIPER TTS
        elif ttsoption == "piper":
            async for chunk in text_to_speech_with_pipelining_piper(text):
                yield chunk  

        elif ttsoption == "elevenlabs":
            async for chunk in text_to_speech_with_pipelining_elevenlabs(text):
                # Apply robot effects to ElevenLabs audio if enabled
                if apply_effects:
                    try:
                        # Read the audio chunk
                        chunk.seek(0)  # Reset BytesIO position
                        audio_data, sample_rate = sf.read(chunk, dtype='int16')
                        
                        # Apply robot effects
                        processed_audio = apply_robot_fx(audio_data, sample_rate, robot_fx_depth)
                        
                        # Convert back to BytesIO
                        output_buffer = BytesIO()
                        sf.write(output_buffer, processed_audio, sample_rate, format='WAV')
                        output_buffer.seek(0)
                        
                        yield output_buffer
                    except Exception as e:
                        queue_message(f"ERROR: Failed to apply robot effects to ElevenLabs audio: {e}")
                        yield chunk
                else:
                    yield chunk

        elif ttsoption == "silero":
            async for chunk in text_to_speech_with_pipelining_silero(text):
                yield chunk 

        else:
            raise ValueError(f"ERROR: Invalid TTS option.")

    except Exception as e:
        queue_message(f"ERROR: Text-to-speech generation failed: {e}")

async def play_audio_chunks(text, config):
    """
    Plays audio chunks sequentially from the generate_tts_audio function.
    """
    async for audio_chunk in generate_tts_audio(text, config):
        try:
            # Read the audio chunk into a format playable by sounddevice
            data, samplerate = sf.read(audio_chunk, dtype='float32')
            sd.play(data, samplerate)
            await asyncio.sleep(len(data) / samplerate)  # Wait for playback to finish
        except Exception as e:
            queue_message(f"ERROR: Failed to play audio chunk: {e}")
