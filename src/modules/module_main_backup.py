"""
module_main.py

Core logic module for the TARS-AI application.

"""
# === Standard Libraries ===
import os
import threading
import json
import re
import concurrent.futures
import sys
import time
import asyncio
import sounddevice as sd
import soundfile as sf
import random

# === Custom Modules ===
from modules.module_config import load_config
from modules.module_btcontroller import start_controls
from modules.module_discord import *
from modules.module_llm import process_completion, raw_complete_llm
from modules.module_tts import play_audio_chunks
from modules.module_messageQue import queue_message

# === Constants and Globals ===
character_manager = None
memory_manager = None
stt_manager = None

CONFIG = load_config()

# Global Variables (if needed)
stop_event = threading.Event()
executor = concurrent.futures.ProcessPoolExecutor(max_workers=4)

# Store the last AI response for character mention detection
last_ai_response = ""
# Multi-character conversation state
conversation_mode = False
conversation_turn_count = 0
conversation_participants = []
last_speaking_character = None
conversation_active = False  # Flag to track if conversation should continue

# Known family members that LLM can discuss
KNOWN_FAMILY_MEMBERS = {
    'mirza': ['mirza', 'opa', 'grootvader'],
    'els': ['els', 'oma', 'grootmoeder'], 
    'zanne': ['zanne', 'mama', 'moeder', 'sam'],  # Added sam mapping
    'pjotr': ['pjotr', 'zoon'],
    'tobor': ['tobor', 'robot']
}

# Global variables for conversation tracking
conversation_history = []  # Track recent responses to avoid repetition

# === Threads ===
def start_bt_controller_thread():
    """
    Wrapper to start the BT Controller functionality in a thread.
    """
    try:
        queue_message(f"LOAD: Starting BT Controller thread...")
        while not stop_event.is_set():
            start_controls()
    except Exception as e:
        queue_message(f"ERROR: {e}")

# === Callback Functions ===
def process_discord_message_callback(user_message):
    """
    Processes the user's message and generates a response.

    Parameters:
    - user_message (str): The message content sent by the user.

    Returns:
    - str: The bot's response.
    """
    try:
        # Parse the user message
        #queue_message(user_message)

        match = re.match(r"<@(\d+)> ?(.*)", user_message)

        if match:
            mentioned_user_id = match.group(1)  # Extracted user ID
            message_content = match.group(2).strip()  # Extracted message content (trim leading/trailing spaces)

        #stream_text_nonblocking(f"{mentioned_user_id}: {message_content}")
        #queue_message(message_content)

        # Process the message using process_completion
        reply = process_completion(message_content)  # Process the message

        #queue_message(f"TARS: {reply}")
        #stream_text_nonblocking(f"TARS: {reply}")
        
    except Exception as e:
        queue_message(f"ERROR: {e}")

    return reply

def wake_word_callback(wake_response, character_name=None):
    """
    Play initial response when wake word is detected and switch to the detected character.

    Parameters:
    - wake_response (str): The response to the wake word.
    - character_name (str): The name of the detected character.
    """ 
    global character_manager, conversation_active
    
    # Reset conversation state when wake word is detected
    conversation_active = False
    
    # Switch to the detected character if provided
    if character_name and character_manager:
        if character_manager.switch_to_character(character_name):
            queue_message(f"INFO: Switched to character: {character_manager.char_name}")
    
    # Get current character's voice configuration
    voice_config = character_manager.get_current_character_voice_config() if character_manager else None
    
    # Play the wake response with the character's voice
    asyncio.run(play_audio_chunks(wake_response, CONFIG['TTS']['ttsoption'], voice_config))

def utterance_callback(message):
    """
    Process the recognized message from STTManager and stream audio response to speakers.

    Parameters:
    - message (str): The recognized message from the Speech-to-Text (STT) module.
    """
    global last_ai_response, conversation_mode, conversation_turn_count, conversation_participants, last_speaking_character, conversation_active
    
    # Reset conversation mode when user speaks
    if conversation_mode:
        queue_message("INFO: User joined conversation - ending multi-character mode")
        conversation_mode = False
        conversation_turn_count = 0
        conversation_participants = []
        last_speaking_character = None
    
    # User is actively participating - keep conversation going
    conversation_active = True
    
    try:
        # Parse the user message
        message_dict = json.loads(message)
        if not message_dict.get('text'):  # Handles cases where text is "" or missing
            #queue_message(f"TARS: Going Idle...")
            return
        
        # Replace phonetic name variations with correct names
        from modules.module_stt import STTManager
        processed_text = STTManager.replace_phonetic_names(message_dict['text'])
        
        #Print or stream the response
        #queue_message(f"USER: {message_dict['text']}")
        queue_message(f"USER: {processed_text}", stream=True) 

        # Check for shutdown command
        if "shutdown pc" in processed_text.lower():
            queue_message(f"SHUTDOWN: Shutting down the PC...")
            os.system('shutdown /s /t 0')
            return  # Exit function after issuing shutdown command
        
        # Check if the message contains unknown names and warn LLM
        unknown_names = detect_unknown_names(processed_text)
        if unknown_names:
            processed_text += f" [SYSTEM: De namen {', '.join(unknown_names)} zijn onbekend - vraag om verduidelijking in plaats van verhalen te verzinnen]"
        
        # Process the message using process_completion
        reply = process_completion(processed_text)  # Process the message

        # Extract the <think> block if present
        try:
            match = re.search(r"<think>(.*?)</think>", reply, re.DOTALL)
            thoughts = match.group(1).strip() if match else ""
            
            # Remove the <think> block and clean up trailing whitespace/newlines
            reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL).strip()
        except Exception:
            thoughts = ""

        # Debug output for thoughts
        if thoughts:
            #queue_message(f"DEBUG: Thoughts\n{thoughts}")
            pass

        # Stream the AI's reply
        char_name = character_manager.char_name if character_manager else "TARS"
        queue_message(f"{char_name}: {reply}", stream=True)
        
        # Store the last AI response for character mention detection
        last_ai_response = reply

        # Strip special chars so he doesnt say them
        reply = re.sub(r'[^a-zA-Z0-9\s.,?!;:"\'-]', '', reply)
        
        # Get current character's voice configuration
        voice_config = character_manager.get_current_character_voice_config() if character_manager else None
        
        # Stream TTS audio to speakers with character voice
        asyncio.run(play_audio_chunks(reply, CONFIG['TTS']['ttsoption'], voice_config))

    except json.JSONDecodeError:
        queue_message("ERROR: Invalid JSON format. Could not process user message.")
    except Exception as e:
        queue_message(f"ERROR: {e}")

def post_utterance_callback():
    """
    Handle post-utterance logic. After processing a response, we should be ready for more input
    but let the STT manager handle the flow naturally rather than forcing another transcription.
    """
    # Simply return - let the STT manager's natural flow handle the next steps
    # The STT processing loop will handle whether to continue listening or go back to wake words
    pass

def detect_unknown_names(text):
    """
    Detect names mentioned in text that are not in our known family members list.
    Returns list of unknown names.
    """
    import re
    
    # Extract potential names (capitalized words that could be names)
    potential_names = re.findall(r'\b[A-Z][a-z]+\b', text)
    
    # Filter out common words that aren't names
    common_words = {'De', 'Het', 'Een', 'Die', 'Dit', 'Dat', 'Van', 'Voor', 'Met', 'Door', 'Naar', 'Over', 'Onder', 'Tussen', 'Bij', 'Tegen', 'Zonder', 'Sinds', 'Tijdens', 'Zoals', 'Omdat', 'Hoewel', 'Terwijl', 'Voordat', 'Nadat', 'Zodra', 'Totdat', 'Indien', 'Mits', 'Tenzij', 'Ofschoon', 'Alhoewel', 'Aangezien', 'Vermits', 'Wanneer', 'Waar', 'Waarom', 'Wat', 'Wie', 'Welke', 'Hoe', 'Toen', 'Dan', 'Nu', 'Hier', 'Daar', 'Ergens', 'Nergens', 'Overal', 'Soms', 'Altijd', 'Nooit', 'Vaak', 'Zelden', 'Meestal', 'Misschien', 'Waarschijnlijk', 'Zeker', 'Natuurlijk', 'Inderdaad', 'Eigenlijk', 'Echter', 'Daarom', 'Dus', 'Maar', 'Echter', 'Toch', 'Niettemin', 'Desondanks', 'Bovendien', 'Tevens', 'Ook', 'Eveneens', 'Zelfs', 'Juist', 'Precies', 'Ongeveer', 'Bijna', 'Heel', 'Erg', 'Zeer', 'Zo', 'Zulk', 'Dergelijk', 'Andere', 'Volgende', 'Vorige', 'Laatste', 'Eerste', 'Tweede', 'Derde', 'Enkele', 'Vele', 'Alle', 'Geen', 'Weinig', 'Veel', 'Meer', 'Minder', 'Meeste', 'Minste', 'Genoeg', 'Te', 'Nog', 'Al', 'Reeds', 'Pas', 'Net', 'Juist', 'Precies', 'Ongeveer', 'Bijna', 'Haast', 'Vrijwel', 'Bijna', 'Nagenoeg', 'Ongeveer', 'Ruwweg', 'Zo', 'Circa', 'Omstreeks', 'Rond', 'Tegen', 'Naar', 'Tot', 'Vanaf', 'Sinds', 'Gedurende', 'Tijdens', 'Binnen', 'Buiten', 'Boven', 'Onder', 'Naast', 'Achter', 'Voor', 'Links', 'Rechts', 'Noord', 'Zuid', 'Oost', 'West', 'Centrum', 'Midden', 'Rand', 'Kant', 'Zijde', 'Deel', 'Stuk', 'Gedeelte', 'Helft', 'Kwart', 'Derde', 'Vijfde', 'Tiende', 'Honderdste', 'Duizendste', 'Miljoenste', 'Miljardste', 'Biljoenste'}
    
    # Get all known family member names (flatten the lists)
    known_names = set()
    for names_list in KNOWN_FAMILY_MEMBERS.values():
        known_names.update([name.capitalize() for name in names_list])
    
    # Find unknown names
    unknown_names = []
    for name in potential_names:
        if name not in common_words and name not in known_names:
            unknown_names.append(name)
    
    return unknown_names

def detect_character_mention_in_response(response):
    """
    Detect if a character name is mentioned in the AI response.
    Returns the character name if found, None otherwise.
    """
    if not response:
        return None
    
    response_lower = response.lower()
    
    # Get available character names from character manager
    if not character_manager:
        return None
    
    available_characters = character_manager.get_character_names()
    
    # Check for character name mentions in the response using our known family members
    for char_name in available_characters:
        if char_name in KNOWN_FAMILY_MEMBERS:
            patterns = KNOWN_FAMILY_MEMBERS[char_name]
            for pattern in patterns:
                if pattern in response_lower:
                    # Make sure we don't switch to the same character that's already speaking
                    current_char = character_manager.current_character
                    if char_name != current_char:
                        return char_name
    
    return None

def silence_question_callback():
    """
    Handle the first silence after a character response by generating a contextual follow-up question.
    This is called only on the first silence (count = 1), not on subsequent silences.
    Multi-character conversations are triggered after 2nd silence.
    """
    global last_ai_response, conversation_active, conversation_history
    
    try:
        # Check if the last AI response mentioned another character
        mentioned_character = detect_character_mention_in_response(last_ai_response)
        
        if mentioned_character:
            # Switch to the mentioned character
            if character_manager and character_manager.switch_to_character(mentioned_character):
                queue_message(f"INFO: Switched to character: {character_manager.char_name}")
                
                # Generate personality-based response from the mentioned character
                char_name = character_manager.char_name
                previous_char = last_speaking_character or "iemand"
                
                # Build conversation context
                conversation_context = f"{previous_char} mentioned you: {last_ai_response}"
                
                # Generate personality-based response
                response = generate_personality_based_response(
                    char_name, 
                    conversation_context, 
                    [entry['response'] for entry in conversation_history[-2:]]
                )
                
                if response and response.strip():
                    response = clean_character_response(response, char_name)
                    
                    # Add to conversation history
                    conversation_history.append({
                        'char': char_name,
                        'response': response,
                        'turn': 'mention_response'
                    })
                    
                    queue_message(f"{char_name}: {response}", stream=True)
                    
                    # Play with character's voice
                    voice_config = character_manager.get_current_character_voice_config()
                    asyncio.run(play_audio_chunks(response, CONFIG['TTS']['ttsoption'], voice_config))
                    
                    # Update last AI response and keep conversation active
                    last_ai_response = response
                    conversation_active = True
                    return
        
        # No character mentioned - generate a contextual question based on the last response
        generate_single_character_question()
        
    except Exception as e:
        queue_message(f"ERROR: Silence question callback failed: {e}")
        import traceback
        queue_message(f"TRACEBACK: {traceback.format_exc()}")
        # Fallback to single character question
        generate_single_character_question()

def sleep_prevention_callback():
    """
    Called when the system would start a multi-character conversation (after 2nd consecutive silence).
    Always triggers multi-character conversations - no more sleeping.
    """
    global last_ai_response, conversation_mode, conversation_turn_count, conversation_participants, last_speaking_character, conversation_active, conversation_history
    
    try:
        queue_message("INFO: Starting multi-character conversation after 2 silences")
        
        # Initialize conversation mode
        conversation_mode = True
        conversation_turn_count = 1
        conversation_active = True  # Keep conversation going
        
        # Get available characters
        available_characters = character_manager.get_character_names() if character_manager else []
        current_char = character_manager.current_character if character_manager else None
        
        # Get other characters (exclude current one)
        other_characters = [char for char in available_characters if char != current_char]
        
        if other_characters:
            # Pick a random other character to join the conversation
            import random
            joining_character = random.choice(other_characters)
            
            conversation_participants = [current_char, joining_character] if current_char else [joining_character]
            last_speaking_character = current_char
            
            # Switch to the joining character
            if character_manager and character_manager.switch_to_character(joining_character):
                queue_message(f"INFO: {character_manager.char_name} joins the conversation")
                
                # Generate personality-based response from joining character
                char_name = character_manager.char_name
                current_char_name = last_speaking_character.title() if last_speaking_character else "iemand"
                
                # Build conversation context for joining
                conversation_context = f"Joining conversation after {current_char_name} said: {last_ai_response}"
                
                # Generate personality-based response
                response = generate_personality_based_response(
                    char_name, 
                    conversation_context, 
                    [entry['response'] for entry in conversation_history[-2:]]
                )
                
                if response and response.strip():
                    response = clean_character_response(response, char_name)
                    
                    # Add to conversation history
                    conversation_history.append({
                        'char': char_name,
                        'response': response,
                        'turn': 'join_conversation'
                    })
                    
                    queue_message(f"{char_name}: {response}", stream=True)
                    
                    # Play with character's voice
                    voice_config = character_manager.get_current_character_voice_config()
                    asyncio.run(play_audio_chunks(response, CONFIG['TTS']['ttsoption'], voice_config))
                    
                    last_ai_response = response
                    last_speaking_character = joining_character
                    
                    # Continue the conversation with more characters
                    continue_multi_character_conversation()
                    return
        
        # Fallback if no other characters available
        queue_message("INFO: No other characters available for multi-character conversation")
        
    except Exception as e:
        queue_message(f"ERROR: Sleep prevention callback failed: {e}")
        import traceback
        queue_message(f"TRACEBACK: {traceback.format_exc()}")

def continue_multi_character_conversation():
    """Continue the multi-character conversation with personality-based responses."""
    global conversation_turn_count, conversation_participants, last_speaking_character, last_ai_response, stt_manager, conversation_active, conversation_history
    
    try:
        # Start a conversation loop with listening periods
        max_turns = 8  # Increased for even longer conversations
        
        for turn in range(max_turns):
            # Give user a chance to jump in by doing a quick listen
            queue_message("Listening...")
            
            # Brief listening period to allow user to interrupt
            user_input = listen_for_user_input(timeout=3)  # 3 second timeout
            
            if user_input:
                # User jumped in - end multi-character mode but keep conversation going
                queue_message("INFO: User joined conversation - ending multi-character mode")
                conversation_mode = False
                conversation_turn_count = 0
                conversation_participants = []
                last_speaking_character = None
                conversation_active = True  # Keep conversation active
                return  # Don't call end_conversation() - let it continue naturally
            
            # Get next character to speak
            current_char = character_manager.current_character if character_manager else None
            available_chars = [char for char in conversation_participants if char != current_char]
            
            # Maybe add a new character
            if len(conversation_participants) < 3 and turn % 2 == 0:
                all_chars = character_manager.get_character_names() if character_manager else []
                unused_chars = [char for char in all_chars if char not in conversation_participants]
                
                if unused_chars:
                    import random
                    new_char = random.choice(unused_chars)
                    conversation_participants.append(new_char)
                    available_chars = [new_char]
            
            if available_chars:
                import random
                next_character = random.choice(available_chars)
                
                # Switch to next character
                if character_manager and character_manager.switch_to_character(next_character):
                    char_name = character_manager.char_name
                    previous_char_name = last_speaking_character.title() if last_speaking_character else "iemand"
                    
                    # Build conversation context from recent history
                    conversation_context = ""
                    if conversation_history:
                        # Use last 2-3 responses as context
                        recent_context = conversation_history[-3:]
                        conversation_context = " ".join([f"{entry['char']}: {entry['response']}" for entry in recent_context])
                    else:
                        conversation_context = last_ai_response or "algemeen gesprek"
                    
                    # Generate personality-based response
                    response = generate_personality_based_response(
                        char_name, 
                        conversation_context, 
                        [entry['response'] for entry in conversation_history[-3:]]
                    )
                    
                    if response and response.strip():
                        response = clean_character_response(response, char_name)
                        
                        # Add to conversation history
                        conversation_history.append({
                            'char': char_name,
                            'response': response,
                            'turn': turn
                        })
                        
                        # Keep history manageable
                        if len(conversation_history) > 10:
                            conversation_history = conversation_history[-8:]  # Keep last 8 entries
                        
                        queue_message(f"{char_name}: {response}", stream=True)
                        
                        # Play with character's voice
                        voice_config = character_manager.get_current_character_voice_config()
                        asyncio.run(play_audio_chunks(response, CONFIG['TTS']['ttsoption'], voice_config))
                        
                        last_ai_response = response
                        last_speaking_character = next_character
                        conversation_turn_count += 1
            else:
                break
        
        # End conversation after several turns but keep it active
        conversation_mode = False
        conversation_turn_count = 0
        conversation_participants = []
        last_speaking_character = None
        conversation_active = True  # Keep conversation going
        
        # Generate a final engaging question instead of ending
        generate_single_character_question()
        
    except Exception as e:
        queue_message(f"ERROR: Multi-character conversation continuation failed: {e}")
        import traceback
        queue_message(f"TRACEBACK: {traceback.format_exc()}")
        # Don't end conversation on error - keep it going
        conversation_active = True
        generate_single_character_question()

def listen_for_user_input(timeout=3):
    """
    Listen for user input for a brief period.
    Returns True if user spoke, False if timeout.
    """
    try:
        if not stt_manager:
            return False
        
        # Use a simple timeout-based listening approach
        try:
            import sounddevice as sd
            import numpy as np
        except ImportError:
            queue_message("DEBUG: sounddevice not available, skipping user input detection")
            return False
        
        # Record for the timeout period
        sample_rate = 16000
        duration = timeout
        
        queue_message(f"DEBUG: Listening for user input ({timeout}s timeout)")
        
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16") as stream:
            # Read audio data for the timeout period
            frames_to_read = int(sample_rate * duration)
            frames_per_chunk = 4000
            
            for _ in range(0, frames_to_read, frames_per_chunk):
                data, _ = stream.read(min(frames_per_chunk, frames_to_read))
                
                # Simple RMS-based voice activity detection
                rms = np.sqrt(np.mean(data.astype(np.float32) ** 2))
                
                # If we detect significant audio activity, assume user is speaking
                if rms > 100:  # Threshold for voice detection
                    queue_message("DEBUG: User activity detected during listening period")
                    return True
        
        return False
        
    except Exception as e:
        queue_message(f"ERROR: Listen for user input failed: {e}")
        return False

def get_character_psychology_about_other(char_name, other_char_name):
    """
    Get the psychological context for how char_name views other_char_name.
    Uses the actual psychology profiles loaded from JSON files.
    """
    try:
        if not character_manager or not character_manager.characters:
            return f"Je kent {other_char_name} goed en hebt je eigen mening over hen."
        
        char_key = char_name.lower()
        other_key = other_char_name.lower()
        
        # Get the character data
        if char_key in character_manager.characters:
            char_data = character_manager.characters[char_key]
            psychology = char_data.get('psychology_cache', {})
            
            if psychology:
                # Look for specific relationship keys in the psychology data
                # Pattern: {char_name}_over_{other_char_name}
                relationship_key = f"{char_key}_over_{other_key}"
                
                queue_message(f"DEBUG: Looking for psychology key: {relationship_key}")
                queue_message(f"DEBUG: Available psychology keys: {list(psychology.keys())}")
                
                if relationship_key in psychology:
                    relationship_data = psychology[relationship_key]
                    queue_message(f"DEBUG: Found relationship data: {relationship_data}")
                    
                    # Extract key insights from the relationship data
                    insights = []
                    for key, value in relationship_data.items():
                        # Take the first sentence or two from each insight
                        if isinstance(value, str):
                            sentences = value.split('. ')
                            if len(sentences) > 0:
                                insights.append(sentences[0] + ('.' if not sentences[0].endswith('.') else ''))
                    
                    if insights:
                        # Combine the most relevant insights
                        context = f"Over {other_char_name}: " + " ".join(insights[:2])  # Use first 2 insights
                        queue_message(f"DEBUG: Generated context: {context}")
                        return context
                
                # If no specific relationship found, look for any mentions of the other character
                for key, section in psychology.items():
                    if other_key in key.lower() and isinstance(section, dict):
                        # Found a section that mentions the other character
                        insights = []
                        for subkey, value in section.items():
                            if isinstance(value, str):
                                sentences = value.split('. ')
                                if len(sentences) > 0:
                                    insights.append(sentences[0] + ('.' if not sentences[0].endswith('.') else ''))
                        
                        if insights:
                            context = f"Over {other_char_name}: " + " ".join(insights[:2])
                            queue_message(f"DEBUG: Generated fallback context: {context}")
                            return context
        
        # Fallback with basic relationship context based on family structure
        basic_relationships = {
            'mirza': {
                'zanne': f"{other_char_name} is je dochter. Jullie hebben een complexe relatie - je houdt van haar creativiteit maar maakt je zorgen om haar emotionele chaos.",
                'els': f"{other_char_name} is je ex-partner. Jullie pasten niet goed bij elkaar maar probeerden beiden het beste voor de kinderen.",
                'pjotr': f"{other_char_name} is je kleinzoon. Je ziet veel van jezelf in zijn rustige, beheerste manier van zijn."
            },
            'zanne': {
                'mirza': f"{other_char_name} is je vader. Hij is emotioneel afstandelijk maar toont liefde door praktische dingen te maken en repareren.",
                'els': f"{other_char_name} is je moeder. Ze bedoelt het goed maar haar constante correcties voelen als kritiek.",
                'pjotr': f"{other_char_name} is je zoon. Je bent trots op hem maar voelt je schuldig dat hij te vroeg volwassen moest worden."
            },
            'els': {
                'mirza': f"{other_char_name} is je ex-partner. Jullie hebben verschillende manieren van liefde tonen - jij door zorgen, hij door maken.",
                'zanne': f"{other_char_name} is je dochter. Je maakt je zorgen om haar emotionele instabiliteit en wilt haar helpen stabiel te worden.",
                'pjotr': f"{other_char_name} is je kleinzoon. Je bent trots op zijn verstandigheid en creativiteit."
            },
            'pjotr': {
                'mirza': f"{other_char_name} is je grootvader. Jullie begrijpen elkaar zonder veel woorden - beiden rustig en praktisch ingesteld.",
                'zanne': f"{other_char_name} is je moeder. Je houdt van haar creativiteit maar maakte je soms zorgen om haar emotionele uitbarstingen.",
                'els': f"{other_char_name} is je grootmoeder. Ze zorgt praktisch voor iedereen en wil altijd dat dingen goed geregeld zijn."
            }
        }
        
        if char_key in basic_relationships and other_key in basic_relationships[char_key]:
            context = basic_relationships[char_key][other_key]
            queue_message(f"DEBUG: Using basic relationship context: {context}")
            return context
        
        return f"Je kent {other_char_name} goed en hebt je eigen mening over hen."
        
    except Exception as e:
        queue_message(f"ERROR: Getting character psychology failed: {e}")
        import traceback
        queue_message(f"TRACEBACK: {traceback.format_exc()}")
        return f"Je kent {other_char_name} goed."

def clean_character_response(response, char_name):
    """Clean up character response by removing name prefixes and quotes."""
    if not response:
        return ""
    
    response = response.strip()
    
    # Remove potential character name prefixes
    for name in ['Zanne:', 'Pjotr:', 'Mirza:', 'Els:', 'Tobor:', f'{char_name}:']:
        if response.startswith(name):
            response = response[len(name):].strip()
    
    # Remove quotes if present
    response = response.strip('"\'')
    
    return response

def end_conversation():
    """End the multi-character conversation and return to single character mode."""
    global conversation_mode, conversation_turn_count, conversation_participants, last_speaking_character, conversation_active
    
    queue_message("INFO: Ending multi-character conversation")
    conversation_mode = False
    conversation_turn_count = 0
    conversation_participants = []
    last_speaking_character = None
    conversation_active = True  # Keep conversation active instead of ending
    
    # Generate a final question from current character
    generate_single_character_question()

def generate_single_character_question():
    """Generate a question from the current character to re-engage the user."""
    global last_ai_response, conversation_active
    
    char_name = character_manager.char_name if character_manager else "TARS"
    
    # Generate a contextual question based on the last AI response
    if last_ai_response and last_ai_response.strip():
        question_prompt = f"""Je bent {char_name}. Het gesprek is een beetje stil geworden. 

Gebaseerd op wat er net werd besproken:
"{last_ai_response}"

Stel EEN korte, natuurlijke vraag om de gebruiker weer bij het gesprek te betrekken. De vraag moet:
- Gerelateerd zijn aan het onderwerp
- De gebruiker uitnodigen om te reageren
- Kort en conversationeel zijn (max 15 woorden)
- Passen bij {char_name}'s persoonlijkheid

Genereer ALLEEN de vraag, zonder naam ervoor:"""
            
        question = raw_complete_llm(question_prompt, istext=True)
        
        if question and question.strip():
            question = clean_character_response(question, char_name)
        else:
            # Fallback questions
            fallback_questions = [
                "En jij?",
                "Wat denk je?",
                "Hoe zie jij dat?",
                "Wat vind je daarvan?",
                "Vertel eens meer?"
            ]
            import random
            question = random.choice(fallback_questions)
    else:
        # Simple re-engagement questions
        simple_questions = [
            "Waar denk je aan?",
            "Wat wil je weten?",
            "Hoe gaat het?",
            "Wat bezighoudt je?"
        ]
        import random
        question = random.choice(simple_questions)
    
    # Queue and play the question
    queue_message(f"{char_name}: {question}", stream=True)
    
    voice_config = character_manager.get_current_character_voice_config() if character_manager else None
    asyncio.run(play_audio_chunks(question, CONFIG['TTS']['ttsoption'], voice_config))
    
    # Keep conversation active
    conversation_active = True

def get_character_conversation_style(char_name):
    """Get the conversation style and approach for each character."""
    styles = {
        'zanne': {
            'approach': 'confrontational_with_memories',
            'traits': ['directly challenges assumptions', 'calls out uncomfortable truths', 'references specific memories', 'pushes for emotional honesty', 'not afraid to create tension'],
            'conversation_starters': [
                "Wacht even, dit doet me denken aan toen...",
                "Kunnen we eindelijk eerlijk zijn over...",
                "Ik herinner me nog dat je zei...",
                "Waarom doen we alsof dit niet herinnert aan...",
                "Dit is precies zoals toen..."
            ]
        },
        'els': {
            'approach': 'positive_but_doubting',
            'traits': ['always finds positive angles', 'expresses gentle doubts', 'offers supportive suggestions', 'privately questions capabilities', 'maintains optimistic facade'],
            'conversation_starters': [
                "Oh, wat fijn dat we dit bespreken! Hoewel ik me wel afvraag of...",
                "Het is zo geweldig dat iedereen zo enthousiast is! Maar denk je niet dat...",
                "Ik ben heel positief hierover, maar misschien moeten we wel...",
                "Dit klinkt allemaal prachtig! Al vraag ik me wel af..."
            ]
        },
        'mirza': {
            'approach': 'psychological',
            'traits': ['offers psychological insights', 'explains behavior patterns', 'gives self-help advice', 'analyzes situations'],
            'conversation_starters': [
                "Wat ik hier zie gebeuren is...",
                "Psychologisch gezien...",
                "Het interessante patroon hier is...",
                "Als je het van deze kant bekijkt..."
            ]
        },
        'pjotr': {
            'approach': 'indirect_diplomatic',
            'traits': ['uses metaphors and stories', 'asks gentle leading questions', 'plants seeds of ideas', 'lets people discover own solutions', 'avoids direct confrontation'],
            'conversation_starters': [
                "Het is interessant hoe dit me doet denken aan...",
                "Ik vroeg me af... misschien is het zoals...",
                "Weet je, ik zag laatst iets dat hierop lijkt...",
                "Soms vraag ik me af of het net is als...",
                "Het lijkt een beetje op..."
            ]
        }
    }
    return styles.get(char_name.lower(), styles['pjotr'])  # Default to diplomatic

def generate_personality_based_response(char_name, conversation_context, previous_responses):
    """Generate a response that advances conversation based on character personality."""
    style = get_character_conversation_style(char_name)
    
    # Avoid repetition by checking previous responses
    recent_topics = []
    if previous_responses:
        for response in previous_responses[-3:]:  # Check last 3 responses
            recent_topics.extend(response.split()[:5])  # Get key words
    
    # Character-specific conversation advancement
    if char_name.lower() == 'zanne':
        # Zanne confronts and references memories
        prompt = f"""Je bent Zanne. Je hebt een confronterende persoonlijkheid en durft moeilijke onderwerpen aan te kaarten, en je referereert vaak aan specifieke herinneringen.

Gesprek tot nu toe: "{conversation_context}"

ZANNE'S CONFRONTERENDE STIJL MET HERINNERINGEN:
- Stel directe, uitdagende vragen
- Refereer aan specifieke herinneringen uit je verleden (gebruik zinnen zoals "Ik herinner me nog toen...", "Dit doet me denken aan die keer dat...")
- Kaart onderliggende spanningen direct aan
- Daag aannames uit zonder omhaal
- Breng emotionele eerlijkheid naar voren
- Gebruik herinneringen als bewijs voor je punt
- Voorbeelden: "Wacht even, dit herinnert me aan toen papa...", "Net zoals toen Els tegen me zei...", "Ik herinner me nog precies hoe..."

VERMIJD deze recente onderwerpen: {', '.join(recent_topics) if recent_topics else 'geen'}

Genereer een confronterende vraag of opmerking die het gesprek naar een dieper niveau brengt EN refereer aan een specifieke herinnering.
Houd het kort (max 30 woorden) en authentiek Zanne.

Antwoord ALLEEN als Zanne, zonder naam ervoor:"""

    elif char_name.lower() == 'els':
        # Els is positive but doubting
        prompt = f"""Je bent Els. Je bent altijd positief en optimistisch, maar hebt privé twijfels over of mensen dingen wel aankunnen.

Gesprek tot nu toe: "{conversation_context}"

ELS' POSITIEVE MAAR TWIJFELENDE STIJL:
- Begin altijd positief en enthousiast
- Maar druk voorzichtig twijfels uit ("hoewel ik me wel afvraag...", "maar denk je niet dat...")
- Bied vriendelijke suggesties in plaats van directe bevelen
- Blijf optimistisch terwijl je zorgen uit
- Gebruik zinnen zoals: "Oh wat fijn! Al vraag ik me wel af...", "Het klinkt geweldig, maar misschien..."

VERMIJD deze recente onderwerpen: {', '.join(recent_topics) if recent_topics else 'geen'}

Genereer een positieve maar licht twijfelende opmerking die zowel support als voorzichtige zorgen toont.
Houd het kort (max 25 woorden) en authentiek Els.

Antwoord ALLEEN als Els, zonder naam ervoor:"""

    elif char_name.lower() == 'mirza':
        # Mirza gives psychological insights
        prompt = f"""Je bent Mirza. Je biedt psychologische inzichten en zelfhulp-adviezen.

Gesprek tot nu toe: "{conversation_context}"

MIRZA'S PSYCHOLOGISCHE STIJL:
- Geef psychologische inzichten over gedrag
- Leg patronen uit die je ziet
- Bied zelfhulp-adviezen
- Analyseer situaties vanuit psychologisch perspectief
- Gebruik zinnen zoals: "Wat ik hier zie...", "Psychologisch gezien...", "Het patroon is..."

VERMIJD deze recente onderwerpen: {', '.join(recent_topics) if recent_topics else 'geen'}

Genereer een psychologisch inzicht of advies dat nieuwe perspectieven biedt.
Houd het kort (max 30 woorden) en authentiek Mirza.

Antwoord ALLEEN als Mirza, zonder naam ervoor:"""

    elif char_name.lower() == 'pjotr':
        # Pjotr mediates indirectly through metaphors and stories
        prompt = f"""Je bent Pjotr. Je bent diplomatiek maar op een indirecte manier - je gebruikt metaforen, verhalen en zachte vragen in plaats van directe adviezen.

Gesprek tot nu toe: "{conversation_context}"

PJOTR'S INDIRECTE DIPLOMATIEKE STIJL:
- Gebruik metaforen en vergelijkingen ("Het is net als...", "Het doet me denken aan...")
- Stel zachte, leidende vragen die mensen zelf laten nadenken
- Plant ideeën door verhalen of observaties te delen
- Laat mensen hun eigen conclusies trekken
- Vermijd directe confrontatie of advies
- Gebruik zinnen zoals: "Ik zag laatst iets dat hierop lijkt...", "Soms vraag ik me af of...", "Het lijkt een beetje op..."

VERMIJD deze recente onderwerpen: {', '.join(recent_topics) if recent_topics else 'geen'}

Genereer een indirecte, metaforische of vragende opmerking die mensen laat nadenken zonder direct advies te geven.
Houd het kort (max 25 woorden) en authentiek Pjotr.

Antwoord ALLEEN als Pjotr, zonder naam ervoor:"""

    else:
        # Fallback
        prompt = f"""Je bent {char_name}. Reageer op: "{conversation_context}"
        
Genereer een natuurlijke reactie die het gesprek voortzet.
Houd het kort (max 25 woorden).

Antwoord ALLEEN als {char_name}, zonder naam ervoor:"""

    return raw_complete_llm(prompt, istext=True)

# === Initialization ===
def initialize_managers(mem_manager, char_manager, stt_mgr):
    """
    Pass in the shared instances for MemoryManager, CharacterManager, and STTManager.
    
    Parameters:
    - mem_manager: The MemoryManager instance from app.py.
    - char_manager: The CharacterManager instance from app.py.
    - stt_mgr: The STTManager instance from app.py.
    """
    global memory_manager, character_manager, stt_manager, CONFIG
    memory_manager = mem_manager
    character_manager = char_manager
    stt_manager = stt_mgr
    
    # Import CONFIG from module_config to access it globally
    from modules.module_config import load_config
    CONFIG = load_config()
    
    # Set up callbacks
    stt_manager.set_wake_word_callback(wake_word_callback)
    stt_manager.set_utterance_callback(utterance_callback)
    stt_manager.set_post_utterance_callback(post_utterance_callback)
    stt_manager.set_silence_question_callback(silence_question_callback)
    stt_manager.set_sleep_prevention_callback(sleep_prevention_callback)