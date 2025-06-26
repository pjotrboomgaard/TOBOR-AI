"""
module_tts.py

Text-to-Speech (TTS) module for TARS-AI.

Generates speech from text via multiple back-ends (Azure, ElevenLabs, Piper,
Silero, espeak-ng, AllTalk) and **optionally** pipes the audio through a light
real-time “robot” effect (telephone band-pass → 8-bit crush → 30 Hz
ring-modulation).

Enable or disable the effect in `config.ini`:

    [AUDIOFX]
    robot_fx        = true   ; enable / disable robot filter
    robot_fx_depth  = 1.0    ; wet/dry mix 0-1

This file now runs on Python 3.8+ (no `str | None` syntax) and keeps working
*even if SciPy is not installed*—it simply bypasses the robot filter and logs a
warning.
"""

# === Standard library ===
from __future__ import annotations

import asyncio
import os
import requests
from io import BytesIO
from datetime import datetime
from typing import Optional

# === Third-party ===
import numpy as np
import sounddevice as sd
import soundfile as sf

# --- SciPy is optional (used only for the band-pass) ---------
try:
    from scipy.signal import butter, lfilter  # type: ignore
    _scipy_available = True
except Exception:  # noqa: BLE001 (broad OK: import-time)
    _scipy_available = False

# === Local modules ===
from modules.module_piper import text_to_speech_with_pipelining_piper
from modules.module_silero import text_to_speech_with_pipelining_silero
from modules.module_espeak import text_to_speech_with_pipelining_espeak
from modules.module_alltalk import text_to_speech_with_pipelining_alltalk
from modules.module_elevenlabs import text_to_speech_with_pipelining_elevenlabs
from modules.module_azure import text_to_speech_with_pipelining_azure
from modules.module_messageQue import queue_message

# -----------------------------------------------------------
#  Helper: update remote TTS server settings
# -----------------------------------------------------------

def update_tts_settings(ttsurl: str) -> None:
    """POST a JSON blob to an external TTS server to update its settings."""
    url = f"{ttsurl}/set_tts_settings"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {
        "stream_chunk_size": 100,
        "temperature": 0.75,
        "speed": 1,
        "length_penalty": 1.0,
        "repetition_penalty": 5,
        "top_p": 0.85,
        "top_k": 50,
        "enable_text_splitting": True,
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            queue_message("LOAD: TTS settings updated successfully.")
        else:
            queue_message(
                f"ERROR: Failed to update TTS settings (status {resp.status_code})."
            )
            queue_message(f"INFO: Response: {resp.text}")
    except Exception as exc:  # noqa: BLE001
        queue_message(f"ERROR: TTS update failed: {exc}")

# -----------------------------------------------------------
#  Core: audio playback with optional robot FX
# -----------------------------------------------------------

def play_audio_stream(
    tts_stream,
    samplerate: int = 22050,
    channels: int = 1,
    gain: float = 1.0,
    normalize: bool = False,
    robot_fx: bool = False,
    fx_depth: float = 1.0,
) -> None:
    """Play a generator of raw 16-bit PCM chunks through the speakers."""
    try:
        with sd.OutputStream(
            samplerate=samplerate,
            channels=channels,
            dtype="int16",
            blocksize=4096,
        ) as stream:
            for chunk in tts_stream:
                if not chunk:
                    queue_message("ERROR: Received empty audio chunk.")
                    continue

                audio_f32 = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)

                # --- Normalise -------------------------------------------------
                if normalize:
                    peak = np.max(np.abs(audio_f32))
                    if peak > 0:
                        audio_f32 = audio_f32 / peak * 32767.0

                # --- Robot FX --------------------------------------------------
                if robot_fx:
                    audio_f32 = _robotize(audio_f32, samplerate, depth=fx_depth)

                # --- Gain + clamp ---------------------------------------------
                audio_i16 = np.clip(audio_f32 * gain, -32768, 32767).astype(np.int16)
                stream.write(audio_i16)
    except Exception as exc:  # noqa: BLE001
        queue_message(f"ERROR: Audio playback failed: {exc}")

# -----------------------------------------------------------
#  DSP: cheap robot filter (telephone BP + crush + ring-mod)
# -----------------------------------------------------------

def _robotize(sig: np.ndarray, sr: int, depth: float = 1.0) -> np.ndarray:
    """Return *sig* with a band-pass, 8-bit crush and 30 Hz ring-mod.

    Falls back to a simple 8-bit crush if SciPy (for the band-pass) is absent.
    """
    if depth <= 0.0:
        return sig

    # --- 1. Telephone band-pass (if SciPy available) -------------------------
    processed = sig
    if _scipy_available:
        lo, hi = 300.0, 3400.0
        b, a = butter(2, [lo / (sr * 0.5), hi / (sr * 0.5)], btype="band")
        processed = lfilter(b, a, processed)  # type: ignore[arg-type]
    else:
        queue_message("WARN: SciPy not found — skipping band-pass stage.")

    # --- 2. 8-bit crush -------------------------------------------------------
    step = 256.0  # 16-bit / 256 ≈ 8-bit levels
    processed = np.round(processed / step) * step

    # --- 3. Ring modulation (30 Hz) ------------------------------------------
    t = np.arange(len(processed), dtype=np.float32) / sr
    ring = np.sin(2.0 * np.pi * 30.0 * t)
    processed *= ring

    # --- 4. Wet/dry mix -------------------------------------------------------
    return (1.0 - depth) * sig + depth * processed

# -----------------------------------------------------------
#  Text-to-speech back-end switchboard
# -----------------------------------------------------------

async def generate_tts_audio(
    text: str,
    ttsoption: str,
    azure_api_key: Optional[str] = None,
    azure_region: Optional[str] = None,
    ttsurl: Optional[str] = None,
    toggle_charvoice: bool = True,
    tts_voice: Optional[str] = None,
):
    """Yield raw PCM chunks for the given *text* via the chosen *ttsoption*."""
    try:
        if ttsoption == "azure":
            async for chunk in text_to_speech_with_pipelining_azure(text):
                yield chunk
        elif ttsoption == "espeak":
            async for chunk in text_to_speech_with_pipelining_espeak(text):
                yield chunk
        elif ttsoption == "alltalk":
            async for chunk in text_to_speech_with_pipelining_alltalk(text):
                yield chunk
        elif ttsoption == "piper":
            async for chunk in text_to_speech_with_pipelining_piper(text):
                yield chunk
        elif ttsoption == "elevenlabs":
            async for chunk in text_to_speech_with_pipelining_elevenlabs(text):
                yield chunk
        elif ttsoption == "silero":
            async for chunk in text_to_speech_with_pipelining_silero(text):
                yield chunk
        else:
            raise ValueError(f"Invalid TTS option: {ttsoption}")
    except Exception as exc:  # noqa: BLE001
        queue_message(f"ERROR: Text-to-speech generation failed: {exc}")

# -----------------------------------------------------------
#  Convenience: play a whole text right away
# -----------------------------------------------------------

async def play_audio_chunks(
    text: str,
    ttsoption: str,
    samplerate: int = 22050,
    robot_fx: bool = False,
    fx_depth: float = 1.0,
) -> None:
    """Generate TTS for *text* and play it immediately with optional robot FX."""
    async for audio_chunk in generate_tts_audio(text, ttsoption):
        try:
            data, sr = sf.read(BytesIO(audio_chunk), dtype="float32")
            if robot_fx:
                data = _robotize(data * 32767.0, sr, depth=fx_depth) / 32767.0
            sd.play(data, sr)
            await asyncio.sleep(len(data) / sr)
        except Exception as exc:  # noqa: BLE001
            queue_message(f"ERROR: Failed to play audio chunk: {exc}")
