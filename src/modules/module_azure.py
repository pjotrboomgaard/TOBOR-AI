import io
import re
import asyncio
import azure.cognitiveservices.speech as speechsdk
from modules.module_config import load_config


CONFIG = load_config()

def init_speech_config(voice_config=None) -> speechsdk.SpeechConfig:
    """
    Initialize and return Azure speech configuration.
    
    Parameters:
        voice_config (dict): Dictionary containing voice settings like tts_voice
    
    Returns:
        speechsdk.SpeechConfig: Configured speech configuration object
        
    Raises:
        ValueError: If Azure API key or region is missing
    """
    if not CONFIG['TTS']['azure_api_key'] or not CONFIG['TTS']['azure_region']:
        raise ValueError("Azure API key and region must be provided for the 'azure' TTS option.")
    
    try:
        speech_config = speechsdk.SpeechConfig(
            subscription=CONFIG['TTS']['azure_api_key'],
            region=CONFIG['TTS']['azure_region']
        )
        
        # Use character-specific voice if provided, otherwise use default
        tts_voice = CONFIG['TTS']['tts_voice']
        if voice_config and 'tts_voice' in voice_config:
            tts_voice = voice_config['tts_voice']
            
        speech_config.speech_synthesis_voice_name = tts_voice
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
        )
        return speech_config
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Azure speech config: {str(e)}")

async def synthesize_azure(chunk: str, voice_config=None) -> io.BytesIO:
    """
    Synthesize a chunk of text into an audio buffer using Azure TTS.
    
    Parameters:
        chunk (str): The text chunk to synthesize
        voice_config (dict): Dictionary containing voice settings
    """
    try:
        speech_config = init_speech_config(voice_config)

        # Set audio_config to None to capture the audio data in result.audio_data
        audio_config = None
        # Create the Speech Synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        # Get the voice name (use character-specific if provided)
        tts_voice = CONFIG['TTS']['tts_voice']
        if voice_config and 'tts_voice' in voice_config:
            tts_voice = voice_config['tts_voice']

        # Build the SSML string using your original settings
        ssml = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis'
               xmlns:mstts='http://www.w3.org/2001/mstts' xml:lang='en-US'>
            <voice name='{tts_voice}'>
                <prosody rate="10%" pitch="5%" volume="default">
                    {chunk}
                </prosody>
            </voice>
        </speak>
        """

        # Run synthesis on a separate thread (since this call is blocking)
        result = await asyncio.to_thread(lambda: synthesizer.speak_ssml_async(ssml).get())
    
        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            cancellation_details = getattr(result, "cancellation_details", None)
            return None

        if not result.audio_data:
            return None

        audio_length = len(result.audio_data)

        # Wrap the resulting audio data in a BytesIO buffer
        audio_buffer = io.BytesIO(result.audio_data)
        audio_buffer.seek(0)
        return audio_buffer

    except Exception as e:
        return None

async def text_to_speech_with_pipelining_azure(text: str, voice_config=None):
    """
    Converts text to speech by splitting the text into chunks, synthesizing each chunk concurrently,
    and yielding audio buffers as soon as each is ready.
    
    Parameters:
        text (str): The text to convert to speech
        voice_config (dict): Dictionary containing voice settings
    """
    if not CONFIG['TTS']['azure_api_key'] or not CONFIG['TTS']['azure_region']:
        raise ValueError("Azure API key and region must be provided for the 'azure' TTS option.")

    # Split text into chunks based on sentence endings (adjust regex as needed)
    chunks = re.split(r'(?<=\.)\s', text)

    # Schedule synthesis for all non-empty chunks concurrently.
    tasks = []
    for index, chunk in enumerate(chunks):
        chunk = chunk.strip()
        if chunk:
            tasks.append(asyncio.create_task(synthesize_azure(chunk, voice_config)))

    # Now await and yield the results in the original order.
    for i, task in enumerate(tasks):
        audio_buffer = await task  # Each task is already running concurrently.
        if audio_buffer:
            yield audio_buffer