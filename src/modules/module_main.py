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
# from modules.module_led_control import set_emotion  # DISABLED
from modules.module_messageQue import queue_message
from modules.family_therapy_system import therapy_system

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

# Global conversation state for collaborative understanding
conversation_memory = {
    'current_topic': None,
    'participants': [],
    'understanding_goals': {},
    'revelations': [],
    'emotional_threads': {},
    'conversation_depth': 0,
    'last_breakthrough': None
}

# Conversation understanding objectives for each character
UNDERSTANDING_OBJECTIVES = {
    'zanne': {
        'wants_to_understand': ['why Els controls so much', 'why Mirza stays distant', 'how to feel less alone'],
        'wants_others_to_understand': ['her creative chaos is not weakness', 'she needs emotional honesty', 'her confrontations come from love'],
        'conversation_style': 'direct_emotional_probing'
    },
    'els': {
        'wants_to_understand': ['why Zanne resists help', 'how to support without controlling', 'what everyone really needs'],
        'wants_others_to_understand': ['her corrections come from love', 'she fears losing people', 'she wants to create safety'],
        'conversation_style': 'caring_inquiry'
    },
    'mirza': {
        'wants_to_understand': ['family emotional patterns', 'how to connect despite trauma', 'what healing looks like'],
        'wants_others_to_understand': ['distance is protection not rejection', 'he observes to help', 'his silence has meaning'],
        'conversation_style': 'analytical_exploration'
    },
    'pjotr': {
        'wants_to_understand': ['how to bridge differences', 'what brings peace', 'how to help everyone feel heard'],
        'wants_others_to_understand': ['diplomacy is care not avoidance', 'metaphors carry deep truth', 'everyone deserves gentleness'],
        'conversation_style': 'gentle_bridging'
    }
}

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
    Process the recognized message from STTManager for therapy sessions.
    In therapy mode, user can speak directly without wake words.
    """
    global last_ai_response, conversation_mode, conversation_turn_count, conversation_participants, last_speaking_character, conversation_active
    
    try:
        # Parse the user message
        message_dict = json.loads(message)
        if not message_dict.get('text'):  # Handles cases where text is "" or missing
            return
        
        # Replace phonetic name variations with correct names
        from modules.module_stt import STTManager
        processed_text = STTManager.replace_phonetic_names(message_dict['text'])
        
        queue_message(f"USER: {processed_text}", stream=True) 

        # Check for shutdown command
        if "shutdown pc" in processed_text.lower():
            queue_message(f"SHUTDOWN: Shutting down the PC...")
            os.system('shutdown /s /t 0')
            return
        
        # Check if the message contains unknown names and warn LLM
        unknown_names = detect_unknown_names(processed_text)
        if unknown_names:
            processed_text += f" [SYSTEM: De namen {', '.join(unknown_names)} zijn onbekend - vraag om verduidelijking in plaats van verhalen te verzinnen]"
        
        # THERAPY SESSION FLOW - Characters respond to user topic
        conversation_active = True
        
        # If we're in a conversation already, stop auto-conversation
        if conversation_mode:
            queue_message("INFO: User joined conversation - ending multi-character mode")
            conversation_mode = False
            conversation_turn_count = 0
            conversation_participants = []
            last_speaking_character = None
        
        # Start family responses to user's topic
        start_family_responses_to_user(processed_text)
        
    except Exception as e:
        queue_message(f"ERROR: Utterance processing failed: {e}")
        import traceback
        queue_message(f"TRACEBACK: {traceback.format_exc()}")

def start_family_responses_to_user(user_message):
    """
    Generate family member responses to user's topic in therapy session.
    """
    global conversation_mode, conversation_participants, conversation_turn_count, character_manager
    
    try:
        available_characters = character_manager.get_character_names() if character_manager else []
        if not available_characters:
            return
        
        # Set up therapy conversation mode
        conversation_mode = True
        conversation_active = True
        conversation_turn_count = 1
        
        # Include all family members except Tobor (he already opened)
        family_members = [char for char in available_characters if char.lower() != 'tobor']
        conversation_participants = ['tobor'] + family_members
        
        # Add user message to conversation history
        conversation_history.append({
            'char': 'user',
            'response': user_message,
            'turn': 'user_input'
        })
        
        # Tobor responds first as therapist
        if 'tobor' in available_characters and character_manager:
            character_manager.switch_to_character('tobor')
            tobor_response = therapy_system.generate_character_response(
                'tobor', 
                'user', 
                f"User heeft gezegd: {user_message}", 
                1
            )
            
            # Clean and play Tobor's response
            clean_response = clean_character_response(tobor_response, 'tobor')
            queue_message(f"Tobor: {clean_response}", stream=True)
            
            # Play audio
            if character_manager:
                voice_config = character_manager.get_current_character_voice_config()
                asyncio.run(play_audio_chunks(clean_response, CONFIG['TTS']['ttsoption'], voice_config))
            
            # Add to history
            conversation_history.append({
                'char': 'tobor',
                'response': clean_response,
                'turn': 'therapist_response'
            })
            
            last_ai_response = clean_response
            last_speaking_character = 'tobor'
        
        # Brief pause before family responses
        import time
        time.sleep(2)
        
        # Continue with family conversation
        continue_multi_character_conversation()
        
    except Exception as e:
        queue_message(f"ERROR: Family response generation failed: {e}")
        import traceback
        queue_message(f"TRACEBACK: {traceback.format_exc()}")

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
    Handle silences after character responses:
    - First silence: If character mentioned another, that character responds
    - Second silence: Current character asks a follow-up question to user
    - Third/Fourth silence: Continue normal flow
    - After 4th silence: Multi-character conversation starts
    """
    global last_ai_response, conversation_active, conversation_history, last_speaking_character, stt_manager
    
    try:
        # Get current silence count to determine behavior
        silence_count = getattr(stt_manager, 'consecutive_silence_count', 1) if stt_manager else 1
        
        if silence_count == 1:
            # First silence - check if the last AI response mentioned another character
            # But only if multi-character conversations are enabled
            if CONFIG.get('CHARACTERS', {}).get('enable_multi_character', 'True').lower() == 'true':
                mentioned_character = detect_character_mention_in_response(last_ai_response)
            else:
                mentioned_character = None
            
            if mentioned_character:
                # Switch to the mentioned character
                if character_manager and character_manager.switch_to_character(mentioned_character):
                    queue_message(f"INFO: Switched to character: {character_manager.char_name}")
                    
                    # Generate personality-based response from the mentioned character
                    char_name = character_manager.char_name
                    previous_char = last_speaking_character or "iemand"
                    
                    # Build conversation context - make it clear who just spoke
                    conversation_context = f"{previous_char}: {last_ai_response}"
                    
                    # Add debug output to see conversation history
                    queue_message(f"DEBUG: Conversation history length: {len(conversation_history)}")
                    queue_message(f"DEBUG: Last entry: {previous_char}: {last_ai_response[:50] if last_ai_response else 'None'}...")
                    
                    # Add some additional context if available
                    if len(conversation_history) > 1:
                        prev_entry = conversation_history[-2]
                        conversation_context = f"{prev_entry['char']}: {prev_entry['response']} | {conversation_context}"
                    else:
                        conversation_context = f"{previous_char}: {last_ai_response}" if last_ai_response else "algemeen gesprek"
                        queue_message(f"DEBUG: No conversation history, using: {conversation_context[:50]}...")
                    
                    # Add final debug output
                    queue_message(f"DEBUG: Context for {char_name}: {conversation_context[:100]}...")
                    
                    # Generate personality-based response
                    response = generate_personality_based_response(
                        char_name, 
                        conversation_context, 
                        [entry['response'] for entry in conversation_history[-2:]]
                    )
                    
                    if response and response.strip():
                        response = clean_character_response(response, char_name)
                        
                        # Add to conversation history PROPERLY
                        conversation_history.append({
                            'char': char_name,
                            'response': response,
                            'turn': 'mention_response'
                        })
                        
                        queue_message(f"{char_name}: {response}", stream=True)
                        
                        # Play with character's voice
                        voice_config = character_manager.get_current_character_voice_config() if character_manager else None
                        asyncio.run(play_audio_chunks(response, CONFIG['TTS']['ttsoption'], voice_config))
                        
                        # Update last AI response and keep conversation active
                        last_ai_response = response
                        last_speaking_character = char_name  # Update who just spoke
                        conversation_active = True
                        return
                    
            # First silence, no character mentioned - just continue with current character
            return
        
        elif silence_count == 2:
            # Second silence - current character asks a follow-up question to the user
            # Skip multi-character behavior if disabled
            if not CONFIG.get('CHARACTERS', {}).get('enable_multi_character', 'True').lower() == 'true':
                queue_message("DEBUG: Multi-character mode disabled - skipping follow-up question")
                return
                
            current_char = character_manager.char_name if character_manager else "TARS"
            previous_char = last_speaking_character or "iemand"
            
            # Build context showing who just spoke
            conversation_context = f"{previous_char}: {last_ai_response}"
            
            # Add debugging
            queue_message(f"DEBUG: Second silence - {current_char} asking follow-up question")
            queue_message(f"DEBUG: Context for {current_char}: {conversation_context}")
            
            # Generate a group therapy question that responds to whoever just spoke
            question = generate_group_therapy_question(current_char, conversation_context)
            
            # Add to conversation history PROPERLY
            conversation_history.append({
                'char': current_char,
                'response': question,
                'turn': 'follow_up_question'
            })
            
            # Queue and play the question
            queue_message(f"{current_char}: {question}", stream=True)
            
            voice_config = character_manager.get_current_character_voice_config() if character_manager else None
            asyncio.run(play_audio_chunks(question, CONFIG['TTS']['ttsoption'], voice_config))
            
            # Update tracking
            last_ai_response = question
            last_speaking_character = current_char
            
            # Keep conversation active
            conversation_active = True
            return
        
        # For 3rd and 4th silences, do nothing special - just let the silence counter increment
        # The multi-character conversation will trigger after the 4th silence
        
    except Exception as e:
        queue_message(f"ERROR: Silence question callback failed: {e}")
        import traceback
        queue_message(f"TRACEBACK: {traceback.format_exc()}")
        # Fallback to single character question
        generate_single_character_question()

def sleep_prevention_callback():
    """
    Called when the system would normally go to sleep (after 4 consecutive silences).
    This is when we start multi-character conversations with a 3rd random character joining.
    """
    global last_ai_response, conversation_mode, conversation_turn_count, conversation_participants, last_speaking_character, conversation_active, conversation_history
    
    try:
        # Check if multi-character conversations are enabled
        if not CONFIG.get('CHARACTERS', {}).get('enable_multi_character', 'True').lower() == 'true':
            queue_message("DEBUG: Multi-character conversations disabled - system going to sleep")
            return
        
        queue_message("DEBUG: Fourth consecutive silence - starting multi-character conversation")
        queue_message("INFO: Starting multi-character conversation after 4 silences")
        
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
    """Continue the multi-character conversation with personality-based responses that go on indefinitely."""
    global conversation_turn_count, conversation_participants, last_speaking_character, last_ai_response, stt_manager, conversation_active, conversation_history, conversation_mode
    
    try:
        # Start an infinite conversation loop - only stop when user interrupts
        turn = 0
        
        while conversation_active and conversation_mode:
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
            
            # Maybe add a new character every 4 turns
            if len(conversation_participants) < 4 and turn % 4 == 0 and turn > 0:
                all_chars = character_manager.get_character_names() if character_manager else []
                unused_chars = [char for char in all_chars if char not in conversation_participants]
                
                if unused_chars:
                    import random
                    new_char = random.choice(unused_chars)
                    conversation_participants.append(new_char)
                    available_chars = [new_char]
                    queue_message(f"INFO: {new_char.title()} joins the conversation!")
            
            if available_chars:
                import random
                next_character = random.choice(available_chars)
                
                # Switch to next character
                if character_manager and character_manager.switch_to_character(next_character):
                    char_name = character_manager.char_name
                    previous_char_name = last_speaking_character.title() if last_speaking_character else "iemand"
                    
                    # Build conversation context from recent history - make it clear who just spoke
                    if conversation_history and len(conversation_history) > 0:
                        # Get the most recent speaker and their message
                        last_entry = conversation_history[-1]
                        last_speaker = last_entry['char']
                        last_message = last_entry['response']
                        conversation_context = f"{last_speaker}: {last_message}"
                        
                        # Add debug output to see conversation history
                        queue_message(f"DEBUG: Conversation history length: {len(conversation_history)}")
                        queue_message(f"DEBUG: Last entry: {last_speaker}: {last_message[:50]}...")
                        
                        # Add some additional context if available
                        if len(conversation_history) > 1:
                            prev_entry = conversation_history[-2]
                            conversation_context = f"{prev_entry['char']}: {prev_entry['response']} | {conversation_context}"
                    else:
                        conversation_context = f"{previous_char_name}: {last_ai_response}" if last_ai_response else "algemeen gesprek"
                        queue_message(f"DEBUG: No conversation history, using: {conversation_context[:50]}...")
                    
                    # Add final debug output
                    queue_message(f"DEBUG: Context for {char_name}: {conversation_context[:100]}...")
                    
                    # Generate personality-based response with specific thoughts about the other character
                    response = generate_enhanced_personality_response(
                        char_name, 
                        last_speaking_character or previous_char_name,
                        conversation_context, 
                        [entry['response'] for entry in conversation_history[-3:]],
                        turn
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
                        if len(conversation_history) > 12:
                            conversation_history = conversation_history[-10:]  # Keep last 10 entries
                        
                        queue_message(f"{char_name}: {response}", stream=True)
                        
                        # Play with character's voice
                        voice_config = character_manager.get_current_character_voice_config()
                        asyncio.run(play_audio_chunks(response, CONFIG['TTS']['ttsoption'], voice_config))
                        
                        last_ai_response = response
                        last_speaking_character = next_character
                        conversation_turn_count += 1
                        turn += 1
                        
                        # Brief pause between responses to allow natural flow
                        import time
                        time.sleep(1)
            else:
                # If no available characters, break the loop
                break
        
        # If we get here, the conversation has ended naturally
        queue_message("INFO: Multi-character conversation concluded")
        
    except Exception as e:
        queue_message(f"ERROR: Multi-character conversation continuation failed: {e}")
        import traceback
        queue_message(f"TRACEBACK: {traceback.format_exc()}")
        # Don't end conversation on error - keep it going
        conversation_active = True
        generate_single_character_question()

def generate_enhanced_personality_response(char_name, target_character, conversation_context, previous_responses, turn_number):
    """Generate enhanced responses using family therapy system for natural conversation."""
    
    # Use family therapy system for authentic responses
    response = therapy_system.generate_character_response(
        char_name, 
        target_character, 
        conversation_context, 
        turn_number
    )
    
    return response

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
    """Generate a group therapy question from the current character to re-engage the user."""
    global last_ai_response, conversation_active
    
    char_name = character_manager.char_name if character_manager else "TARS"
    
    # Generate a group therapy question that focuses on family relationships
    question = generate_group_therapy_question(char_name, last_ai_response or "")
    
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
    """Generate a collaborative conversation response focused on building mutual understanding."""
    
    # Detect who actually just spoke
    target_character = detect_actual_target_from_context(conversation_context)
    
    if not target_character:
        # Fallback: extract from conversation_history
        if conversation_history:
            target_character = conversation_history[-1]['char']
        else:
            target_character = "iemand"  # Default fallback
    
    # Ensure target_character is a string
    if not target_character:
        target_character = "iemand"
    
    # Build rich context with conversation memory
    memory_context = build_conversation_context_with_memory(char_name, target_character)
    
    # Update conversation memory with the target's last message
    if target_character and conversation_history:
        last_message = conversation_history[-1]['response']
        update_conversation_memory(target_character, last_message, char_name)
    
    queue_message(f"DEBUG: {char_name} responding to {target_character} | Depth: {memory_context['conversation_depth']}")
    
    # CHARACTER-SPECIFIC COLLABORATIVE RESPONSES
    if char_name.lower() == 'zanne':
        prompt = f"""Je bent Zanne in een diep familiaal gesprek. Je reageert op {target_character.upper()} die net sprak.

GESPREK CONTEXT:
{memory_context['recent_conversation']}

EMOTIONELE CONTEXT: {memory_context['emotional_threads']}
RECENTE ONTHULLINGEN: {memory_context['revelations']}

ZANNE'S DOEL IN DIT GESPREK:
- Begrijpen: {memory_context['understanding_goal']}
- Anderen laten begrijpen: {memory_context['revelation_goal']}

ZANNE'S CONFRONTERENDE MAAR LIEFDEVOLLE STIJL:
Je MOET direct reageren op wat {target_character} net zei. Begin met "{target_character.title()}, ..."

Gebaseerd op wat zij net zeiden, doe je één van deze dingen:
1. Stel een directe vraag over hun motivatie: "Waarom doe je...?" "Wat bedoel je als je..."
2. Deel een kwetsbare waarheid over jezelf: "Het doet me pijn als jij..." "Ik heb moeite met..."
3. Confronteer hen liefdevol: "Ik zie dat jij... maar ik voel..."
4. Bouw voort op hun onthulling: "Wat je net zei raakt me omdat..."

Voorbeelden:
- "{target_character.title()}, wat je net zei over [hun onderwerp] - waarom vind je het zo moeilijk om..."
- "{target_character.title()}, ik hoor je, maar het doet me pijn als jij..."
- "{target_character.title()}, je zegt [hun punt], maar ik heb het gevoel dat..."

Max 30 woorden. Reageer DIRECT op hun laatste uitspraak.

Antwoord ALLEEN als Zanne:"""

    elif char_name.lower() == 'els':
        prompt = f"""Je bent Els in een diep familiaal gesprek. Je reageert op {target_character.upper()} die net sprak.

GESPREK CONTEXT:
{memory_context['recent_conversation']}

EMOTIONELE CONTEXT: {memory_context['emotional_threads']}
RECENTE ONTHULLINGEN: {memory_context['revelations']}

ELS' DOEL IN DIT GESPREK:
- Begrijpen: {memory_context['understanding_goal']}
- Anderen laten begrijpen: {memory_context['revelation_goal']}

ELS' BEZORGDE MAAR ONDERSTEUNENDE STIJL:
Je MOET direct reageren op wat {target_character} net zei. Begin met "{target_character.title()}, ..."

Gebaseerd op wat zij net zeiden, doe je één van deze dingen:
1. Toon begrip en vraag door: "{target_character.title()}, ik hoor dat je... kan je me helpen begrijpen..."
2. Deel je bezorgdheid liefdevol: "Het maakt me bezorgd als jij... omdat ik..."
3. Bied steun aan: "Wat je net zei... hoe kan ik je helpen met..."
4. Erken hun gevoel: "Ik zie dat je... en dat raakt me omdat..."

Voorbeelden:
- "{target_character.title()}, wat je net zei over [hun onderwerp] - ik maak me zorgen omdat..."
- "{target_character.title()}, ik hoor je pijn en vraag me af hoe ik..."
- "{target_character.title()}, je woorden raken me - kan je me helpen begrijpen..."

Max 30 woorden. Reageer DIRECT op hun laatste uitspraak.

Antwoord ALLEEN als Els:"""

    elif char_name.lower() == 'mirza':
        prompt = f"""Je bent Mirza in een diep familiaal gesprek. Je reageert op {target_character.upper()} die net sprak.

GESPREK CONTEXT:
{memory_context['recent_conversation']}

EMOTIONELE CONTEXT: {memory_context['emotional_threads']}
RECENTE ONTHULLINGEN: {memory_context['revelations']}

MIRZA'S DOEL IN DIT GESPREK:
- Begrijpen: {memory_context['understanding_goal']}
- Anderen laten begrijpen: {memory_context['revelation_goal']}

MIRZA'S ANALYTISCHE MAAR EMPATHISCHE STIJL:
Je MOET direct reageren op wat {target_character} net zei. Begin met "{target_character.title()}, ..."

Gebaseerd op wat zij net zeiden, doe je één van deze dingen:
1. Analyseer hun patroon empathisch: "{target_character.title()}, wat je zegt toont... ik herken dat omdat..."
2. Deel een psychologisch inzicht: "Wat ik zie in jouw woorden is... dat raakt me omdat..."
3. Verbind hun gevoel met je eigen ervaring: "{target_character.title()}, je pijn herken ik... bij mij voelt dat..."
4. Stel een diepere vraag: "Je zegt [hun punt]... wat zou er gebeuren als..."

Voorbeelden:
- "{target_character.title()}, je woorden tonen een patroon dat ik herken - bij mij..."
- "{target_character.title()}, psychologisch gezien zie ik... dat raakt me omdat ik ook..."
- "{target_character.title()}, wat je net deelde... ik vraag me af of jij ook..."

Max 35 woorden. Reageer DIRECT op hun laatste uitspraak.

Antwoord ALLEEN als Mirza:"""

    elif char_name.lower() == 'pjotr':
        prompt = f"""Je bent Pjotr in een diep familiaal gesprek. Je reageert op {target_character.upper()} die net sprak.

GESPREK CONTEXT:
{memory_context['recent_conversation']}

EMOTIONELE CONTEXT: {memory_context['emotional_threads']}
RECENTE ONTHULLINGEN: {memory_context['revelations']}

PJOTR'S DOEL IN DIT GESPREK:
- Begrijpen: {memory_context['understanding_goal']}
- Anderen laten begrijpen: {memory_context['revelation_goal']}

PJOTR'S ZACHTE MAAR DIEPGAANDE STIJL:
Je MOET direct reageren op wat {target_character} net zei. Begin met "{target_character.title()}, ..."

Gebaseerd op wat zij net zeiden, doe je één van deze dingen:
1. Gebruik een metafoor: "{target_character.title()}, wat je zegt is als... vraag je je af..."
2. Stel een zachte maar diepgaande vraag: "Je woorden doen me denken... hoe voelt het voor jou als..."
3. Bouw een brug: "Ik zie hoe jij... en [andere persoon]... misschien kunnen we..."
4. Deel zachte wijsheid: "Wat je net zei... het doet me denken aan hoe..."

Voorbeelden:
- "{target_character.title()}, je woorden zijn als een rivier die... vraag je je af hoe..."
- "{target_character.title()}, ik zie jouw [gevoel] en vraag me af of..."
- "{target_character.title()}, wat als we jouw [punt] en [ander punt] samen..."

Max 30 woorden. Reageer DIRECT op hun laatste uitspraak.

Antwoord ALLEEN als Pjotr:"""

    else:
        # Fallback
        prompt = f"""Reageer direct op {target_character} gebaseerd op wat zij net zeiden. Begin met hun naam. Max 25 woorden."""

    response = raw_complete_llm(prompt, istext=True)
    
    # Update conversation memory with this response
    update_conversation_memory(char_name, response, target_character)
    
    return response

def get_specific_memory_or_relationship_detail(char_name, other_char_name=None, memory_type="random"):
    """
    Extract specific memories or relationship details from character psychology profiles.
    Returns actual content from the persona files, not made-up content.
    """
    try:
        if not character_manager or not character_manager.characters:
            return None
        
        char_key = char_name.lower()
        
        if char_key not in character_manager.characters:
            return None
        
        char_data = character_manager.characters[char_key]
        psychology = char_data.get('psychology_cache', {})
        
        if not psychology:
            return None
        
        # If looking for relationship-specific content
        if other_char_name:
            other_key = other_char_name.lower()
            relationship_key = f"{char_key}_over_{other_key}"
            
            if relationship_key in psychology:
                relationship_data = psychology[relationship_key]
                # Get a random insight from the relationship data
                import random
                if isinstance(relationship_data, dict) and relationship_data:
                    insight_key = random.choice(list(relationship_data.keys()))
                    insight_text = relationship_data[insight_key]
                    # Return first 1-2 sentences
                    sentences = insight_text.split('. ')
                    return '. '.join(sentences[:2]) + ('.' if not sentences[1].endswith('.') else '')
        
        # Get specific memories based on type
        memory_sections = []
        
        if memory_type == "confrontational" and char_key == "zanne":
            if "zanne_confrontational_memories" in psychology:
                memory_sections.append(psychology["zanne_confrontational_memories"])
        elif memory_type == "childhood":
            for key in psychology.keys():
                if "memories" in key.lower() and "childhood" in key.lower():
                    memory_sections.append(psychology[key])
        elif memory_type == "family":
            for key in psychology.keys():
                if "memories" in key.lower() and any(name in key.lower() for name in ["mama", "els", "mirza", "pjotr"]):
                    memory_sections.append(psychology[key])
        else:
            # Random memory from any memory section
            for key in psychology.keys():
                if "memories" in key.lower():
                    memory_sections.append(psychology[key])
        
        if memory_sections:
            import random
            selected_section = random.choice(memory_sections)
            if isinstance(selected_section, dict) and selected_section:
                memory_key = random.choice(list(selected_section.keys()))
                memory_text = selected_section[memory_key]
                # Return first sentence or two
                sentences = memory_text.split('. ')
                return '. '.join(sentences[:2]) + ('.' if len(sentences) > 1 and not sentences[1].endswith('.') else '')
        
        return None
        
    except Exception as e:
        queue_message(f"ERROR: Getting specific memory failed: {e}")
        return None

def get_character_specific_relationship_view(char_name, other_char_name):
    """
    Get how char_name specifically views other_char_name based on their psychology profile.
    Returns actual relationship insights from persona files.
    """
    try:
        if not character_manager or not character_manager.characters:
            return None
        
        char_key = char_name.lower()
        other_key = other_char_name.lower()
        
        if char_key not in character_manager.characters:
            return None
        
        char_data = character_manager.characters[char_key]
        psychology = char_data.get('psychology_cache', {})
        
        if not psychology:
            return None
        
        # Look for specific relationship section
        relationship_key = f"{char_key}_over_{other_key}"
        
        if relationship_key in psychology:
            relationship_data = psychology[relationship_key]
            if isinstance(relationship_data, dict) and relationship_data:
                # Get 2-3 key insights about this relationship
                insights = []
                for key, value in list(relationship_data.items())[:3]:  # Take first 3 insights
                    if isinstance(value, str):
                        # Get first sentence
                        first_sentence = value.split('. ')[0]
                        if first_sentence:
                            insights.append(first_sentence)
                
                if insights:
                    return " ".join(insights[:2])  # Return first 2 insights combined
        
        return None
        
    except Exception as e:
        queue_message(f"ERROR: Getting relationship view failed: {e}")
        return None

def generate_group_therapy_question(char_name, context=""):
    """Generate a group therapy style question that focuses on family relationships."""
    
    # Get other family members
    all_characters = ['zanne', 'els', 'mirza', 'pjotr']
    other_characters = [char for char in all_characters if char.lower() != char_name.lower()]
    
    # Pick someone to ask about
    import random
    target_character = random.choice(other_characters)
    
    # Get relationship view
    relationship_view = get_character_specific_relationship_view(char_name, target_character)
    
    # Character-specific group therapy questions
    if char_name.lower() == 'zanne':
        questions = [
            f"{target_character.title()}, waarom denk je dat we altijd om elkaar heen draaien?",
            f"Wat vind je van hoe {target_character} met emoties omgaat?",
            f"{target_character.title()}, heb je wel eens het gevoel dat we elkaar niet echt zien?",
            f"Waarom is het zo moeilijk om eerlijk te zijn tegen {target_character}?",
            f"{target_character.title()}, denk je dat we ooit echt kunnen praten zonder drama?"
        ]
    elif char_name.lower() == 'els':
        questions = [
            f"{target_character.title()}, ik maak me zorgen om je - hoe gaat het echt met je?",
            f"Denk je dat {target_character} weet hoeveel ik om hen geef?",
            f"{target_character.title()}, voel jij je wel gesteund door onze familie?",
            f"Wat kunnen we doen om {target_character} beter te helpen?",
            f"{target_character.title()}, is er iets wat je van mij nodig hebt?"
        ]
    elif char_name.lower() == 'mirza':
        questions = [
            f"Wat zie je voor patronen in hoe {target_character} communiceert?",
            f"{target_character.title()}, hoe ervaar jij onze familiedynamiek?",
            f"Welke emotionele behoeften heeft {target_character} volgens jou?",
            f"{target_character.title()}, wat zou je willen veranderen aan onze interacties?",
            f"Hoe kunnen we {target_character} beter begrijpen?"
        ]
    elif char_name.lower() == 'pjotr':
        questions = [
            f"{target_character.title()}, soms vraag ik me af... voel je je wel begrepen?",
            f"Het lijkt alsof {target_character} en ik verschillende talen spreken - herken jij dat?",
            f"{target_character.title()}, wat zou je willen dat we beter begrijpen over jou?",
            f"Denk je dat {target_character} zich wel veilig voelt om kwetsbaar te zijn?",
            f"{target_character.title()}, hoe kunnen we dichter bij elkaar komen?"
        ]
    else:
        questions = [f"Hoe voel je je over {target_character}?"]
    
    return random.choice(questions)

def update_conversation_memory(speaker, message, target_character=None):
    """Update the collective conversation memory with new insights."""
    global conversation_memory
    
    try:
        # Add speaker to participants if not already there
        if speaker not in conversation_memory['participants']:
            conversation_memory['participants'].append(speaker)
        
        # Detect emotional content and revelations
        emotional_keywords = {
            'pain': ['pijn', 'doet pijn', 'kwetst', 'verdriet'],
            'fear': ['bang', 'angst', 'onzeker', 'zorgen'],
            'love': ['liefde', 'houd van', 'zorg', 'belangrijk'],
            'anger': ['boos', 'gefrustreerd', 'irritant', 'woede'],
            'understanding': ['begrijp', 'snap', 'zie', 'herken']
        }
        
        message_lower = message.lower()
        detected_emotions = []
        
        for emotion, keywords in emotional_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_emotions.append(emotion)
        
        # Track emotional threads between characters
        if target_character:
            thread_key = f"{speaker}->{target_character}"
            if thread_key not in conversation_memory['emotional_threads']:
                conversation_memory['emotional_threads'][thread_key] = []
            
            conversation_memory['emotional_threads'][thread_key].append({
                'message': message,
                'emotions': detected_emotions,
                'timestamp': len(conversation_history)
            })
        
        # Detect revelations (vulnerable statements)
        revelation_indicators = ['ik voel', 'het doet me pijn', 'ik heb moeite', 'ik wil graag', 'ik ben bang']
        if any(indicator in message_lower for indicator in revelation_indicators):
            conversation_memory['revelations'].append({
                'speaker': speaker,
                'revelation': message,
                'target': target_character,
                'depth_level': conversation_memory['conversation_depth']
            })
            
            # Mark as breakthrough if deep enough
            if conversation_memory['conversation_depth'] >= 3:
                conversation_memory['last_breakthrough'] = {
                    'speaker': speaker,
                    'message': message,
                    'turn': len(conversation_history)
                }
        
        # Increase conversation depth
        conversation_memory['conversation_depth'] += 1
        
        queue_message(f"DEBUG: Conversation depth: {conversation_memory['conversation_depth']}, Revelations: {len(conversation_memory['revelations'])}")
        
    except Exception as e:
        queue_message(f"ERROR: Failed to update conversation memory: {e}")

def get_conversation_understanding_goal(char_name, target_character=None):
    """Get what this character wants to understand about the target."""
    if char_name.lower() not in UNDERSTANDING_OBJECTIVES:
        return "beter begrijpen wat er speelt"
    
    objectives = UNDERSTANDING_OBJECTIVES[char_name.lower()]
    
    if target_character:
        # Get specific understanding goals about this character
        wants_to_understand = objectives['wants_to_understand']
        
        # Filter goals relevant to the target character
        relevant_goals = []
        target_lower = target_character.lower()
        
        for goal in wants_to_understand:
            if target_lower in goal.lower() or 'waarom' in goal or 'hoe' in goal:
                relevant_goals.append(goal)
        
        if relevant_goals:
            import random
            return random.choice(relevant_goals)
    
    # Return a general understanding goal
    return objectives['wants_to_understand'][0] if objectives['wants_to_understand'] else "beter begrijpen"

def get_conversation_revelation_goal(char_name):
    """Get what this character wants others to understand about them."""
    if char_name.lower() not in UNDERSTANDING_OBJECTIVES:
        return "dat ik er voor jullie ben"
    
    objectives = UNDERSTANDING_OBJECTIVES[char_name.lower()]
    wants_others_to_understand = objectives['wants_others_to_understand']
    
    if wants_others_to_understand:
        import random
        return random.choice(wants_others_to_understand)
    
    return "dat ik er voor jullie ben"

def build_conversation_context_with_memory(current_speaker, target_character):
    """Build rich conversation context using collective memory."""
    global conversation_memory, conversation_history
    
    context_parts = []
    
    # Add recent conversation flow
    if conversation_history:
        recent_exchanges = conversation_history[-3:]
        for entry in recent_exchanges:
            context_parts.append(f"{entry['char']}: {entry['response']}")
    
    # Add emotional thread context
    thread_key = f"{target_character}->{current_speaker}"
    reverse_thread_key = f"{current_speaker}->{target_character}"
    
    emotional_context = []
    
    if thread_key in conversation_memory['emotional_threads']:
        last_exchange = conversation_memory['emotional_threads'][thread_key][-1:]
        for exchange in last_exchange:
            emotional_context.append(f"Emoties tussen jullie: {', '.join(exchange['emotions'])}")
    
    # Add revelations context
    relevant_revelations = [r for r in conversation_memory['revelations'] 
                          if r['speaker'] == target_character or r['target'] == current_speaker]
    
    revelation_context = []
    if relevant_revelations:
        last_revelation = relevant_revelations[-1]
        revelation_context.append(f"Recente onthulling van {last_revelation['speaker']}: {last_revelation['revelation']}")
    
    # Build comprehensive context
    full_context = {
        'recent_conversation': " | ".join(context_parts[-2:]) if context_parts else "",
        'emotional_threads': " | ".join(emotional_context),
        'revelations': " | ".join(revelation_context),
        'conversation_depth': conversation_memory['conversation_depth'],
        'understanding_goal': get_conversation_understanding_goal(current_speaker, target_character),
        'revelation_goal': get_conversation_revelation_goal(current_speaker)
    }
    
    return full_context

def detect_actual_target_from_context(conversation_context):
    """Detect who actually just spoke from the conversation context."""
    if not conversation_context:
        return None
    
    # Look for character names followed by colon in the context
    character_names = ['mirza', 'els', 'zanne', 'pjotr']
    
    # Check the most recent part of the context first
    context_lower = conversation_context.lower()
    
    for char_name in character_names:
        if f"{char_name}:" in context_lower:
            # Find the last occurrence to get the most recent speaker
            last_pos = context_lower.rfind(f"{char_name}:")
            if last_pos != -1:
                return char_name
    
    return None

# === Initialization ===
def start_auto_conversation(char_manager, mem_manager, mode="conversation"):
    """
    Start conversations based on mode:
    - "conversation": Normal multi-character conversations (for automatic testing)
    - "therapy": Therapy session where Tobor asks what user wants to discuss (for interactive)
    """
    import time
    import random
    global conversation_mode, conversation_active, conversation_participants, last_speaking_character, last_ai_response, conversation_history, conversation_turn_count
    
    try:
        if mode == "therapy":
            # THERAPY SESSION MODE (Interactive)
            queue_message("INFO: Starting family therapy session...")
            time.sleep(2)
            
            if char_manager:
                available_characters = char_manager.get_character_names()
                if available_characters:
                    # Tobor always starts therapy sessions
                    starting_char = 'tobor' if 'tobor' in available_characters else available_characters[0]
                    
                    # Switch to Tobor
                    if char_manager.switch_to_character(starting_char):
                        queue_message(f"INFO: {starting_char.title()} starting therapy session")
                        
                        # Initialize therapy session variables
                        conversation_mode = False  # Don't start auto-conversation
                        conversation_active = True
                        conversation_turn_count = 0
                        conversation_participants = [starting_char]
                        
                        # Tobor opens the session asking what user wants to discuss
                        opening_message = "Goedemorgen, familie. Ik ben Tobor, jullie therapeutische begeleider. Welkom bij onze familiesessie. Vertel me, waar wil je vandaag over praten? Wat houdt je bezig?"
                        
                        queue_message(f"{starting_char.title()}: {opening_message}")
                        
                        # Set up conversation tracking
                        last_ai_response = opening_message
                        last_speaking_character = starting_char
                        
                        # Add to conversation history
                        conversation_history.append({
                            'char': starting_char,
                            'response': opening_message,
                            'turn': 'session_start'
                        })
                        
                        # Now wait for user input - don't start auto-conversation
                        # The system will naturally wait for user speech through STT
        
        else:
            # NORMAL CONVERSATION MODE (Automatic testing)
            queue_message("INFO: Auto-conversation mode starting...")
            time.sleep(2)
            
            # Get available characters
            if char_manager:
                available_characters = char_manager.get_character_names()
                if available_characters:
                    # Make Tobor more likely to start conversations (80% chance)
                    if 'tobor' in available_characters and random.random() < 0.8:
                        starting_char = 'tobor'
                    else:
                        # Pick a random character to start
                        starting_char = random.choice(available_characters)
                    
                    # Switch to that character
                    if char_manager.switch_to_character(starting_char):
                        queue_message(f"INFO: {starting_char.title()} initiating conversation session")
                        
                        # Initialize conversation variables properly
                        conversation_mode = True
                        conversation_active = True
                        conversation_turn_count = 1
                        
                        # Set up participants with at least 2 characters
                        other_characters = [char for char in available_characters if char != starting_char]
                        if other_characters:
                            # Add the starting character and one other to participants
                            conversation_participants = [starting_char, random.choice(other_characters)]
                        else:
                            conversation_participants = [starting_char]
                        
                        # Generate character-specific opening conversation starter
                        if starting_char.lower() == 'tobor':
                            opening_message = "Welkom, familie. Ik ben Tobor, jullie therapeutische constructie. Ik heb familie-interactiepatronen geanalyseerd en detecteer significante communicatiebarrières. We moeten deze systematische disfuncties aanpakken. Zanne, laten we met jou beginnen - beschrijf je huidige emotionele staat."
                        elif starting_char.lower() == 'zanne':
                            opening_message = "Ik voel me zo moe van alles. We praten nooit echt met elkaar. Altijd om de hete brij heen."
                        elif starting_char.lower() == 'els':
                            opening_message = "Ik maak me zorgen om deze familie. We kunnen dit beschaafd bespreken, maar iedereen is altijd zo defensief."
                        elif starting_char.lower() == 'mirza':
                            opening_message = "Ik was weer afwezig in mijn projecten. Maar ik voel dat er spanning is. Misschien kunnen we praten?"
                        elif starting_char.lower() == 'pjotr':
                            opening_message = "Ik voel de spanning tussen iedereen. Het maakt me verdrietig dat we zo moeilijk kunnen communiceren."
                        else:
                            opening_message = "We moeten praten als familie. Er zijn dingen die gezegd moeten worden."
                        
                        queue_message(f"{starting_char.title()}: {opening_message}")
                        
                        # Set up conversation tracking
                        last_ai_response = opening_message
                        last_speaking_character = starting_char
                        
                        # Add to conversation history
                        conversation_history.append({
                            'char': starting_char,
                            'response': opening_message,
                            'turn': 'auto_start'
                        })
                        
                        # Continue with automatic conversation
                        continue_multi_character_conversation()
                        
    except Exception as e:
        queue_message(f"ERROR: Conversation start failed: {e}")
        import traceback
        queue_message(f"TRACEBACK: {traceback.format_exc()}")

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