#!/usr/bin/env python3
"""
app_openai_multi_agent_therapy.py

Advanced Multi-Agent Family Therapy Application
============================================

This application provides a comprehensive family therapy system using:
- OpenAI-based LLM agents with individual psychology profiles
- Real-time conversation with dynamic character responses
- Tobor as therapeutic orchestrator
- Voice and text interaction modes
- Character-specific emotional triggers and responses

Usage:
    python app_openai_multi_agent_therapy.py --voice    # Voice mode
    python app_openai_multi_agent_therapy.py --text     # Text mode
    python app_openai_multi_agent_therapy.py --test     # Test mode
"""

import os
import sys
import time
import asyncio
import argparse
import threading
from datetime import datetime
from queue import Queue, Empty
from typing import Dict, List, Optional

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.module_config import load_config
from modules.module_messageQue import queue_message
from modules.openai_agent_system import FamilyAgentSystem
from modules.module_stt import STTManager
from modules.module_tts import generate_tts_audio


class OpenAIMultiAgentTherapyApp:
    """Advanced multi-agent family therapy application"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.family_system = FamilyAgentSystem(config)
        self.voice_input_queue = Queue()
        self.session_active = False
        self.voice_mode = False
        self.stt_manager = None
        self.tts_manager = None
        
        # Session flow control
        self.session_phase = "identify_user"  # identify_user, greetings, topic_discovery, therapy
        self.user_identity = None
        self.user_as_member = None  # Which family member the user is (if any)
        self.active_participants = ["Zanne", "Els", "Mirza", "Pjotr", "Tobor"]
        self.therapy_topic = None
        
        # Initialize voice systems if configured
        if config.get("STT", {}).get("enabled", False):
            self.stt_manager = STTManager(config)
        
        # Initialize TTS system
        self.tts_config = config.get("TTS", {})
        self.tts_enabled = not self.tts_config.test_mode if hasattr(self.tts_config, 'test_mode') else True
    
    def print_status(self, message: str, prefix: str = "💭"):
        """Print status message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Handle long messages by wrapping text
        import textwrap
        import sys
        
        # Get terminal width, default to 80 if not available
        try:
            terminal_width = os.get_terminal_size().columns
        except:
            terminal_width = 80
        
        # Calculate available width for message (accounting for prefix and timestamp)
        prefix_len = len(f"{prefix} [{timestamp}] ")
        available_width = max(40, terminal_width - prefix_len - 5)
        
        # Wrap long messages
        if len(message) > available_width:
            lines = textwrap.wrap(message, width=available_width)
            print(f"{prefix} [{timestamp}] {lines[0]}")
            for line in lines[1:]:
                print(f"{' ' * prefix_len}{line}")
        else:
        print(f"{prefix} [{timestamp}] {message}")
        
        # Flush output to ensure immediate display
        sys.stdout.flush()
        # Don't use queue_message here as it causes duplicate output
    
    def setup_voice_input(self):
        """Setup voice input callback"""
        if not self.stt_manager:
            return
        
        def voice_callback(json_result):
            try:
                import json
                result = json.loads(json_result)
                text = result.get("text", "").strip()
                if text:
                    self.voice_input_queue.put(text)
                    self.print_status(f"Voice detected: {text}", "🎤")
            except Exception as e:
                self.print_status(f"Voice callback error: {e}", "❌")
        
        self.stt_manager.set_utterance_callback(voice_callback)
        self.stt_manager.start()
        self.print_status("Voice input system activated", "🎤")
    
    async def speak_response(self, text: str, agent_name: str = "Tobor"):
        """Speak response using TTS"""
        if not self.tts_enabled:
            self.print_status(f"[TTS] {agent_name} would speak: {text[:100]}...", "🔊")
            return
        
        try:
            self.print_status(f"Speaking as {agent_name}: {text[:50]}...", "🔊")
            
            # Get character-specific voice configuration
            voice_config = self.get_voice_config_for_agent(agent_name)
            
            # Break long text into shorter chunks to avoid TTS truncation
            text_chunks = self._split_text_for_tts(text)
            
            for text_chunk in text_chunks:
                # Generate TTS audio for each chunk
                audio_chunks = []
                async for chunk in generate_tts_audio(
                    text=text_chunk,
                    ttsoption=self.tts_config.ttsoption,
                    voice_config=voice_config,
                    azure_api_key=self.tts_config.azure_api_key,
                    azure_region=self.tts_config.azure_region,
                    ttsurl=self.tts_config.ttsurl,
                    toggle_charvoice=self.tts_config.toggle_charvoice,
                    tts_voice=self.tts_config.tts_voice
                ):
                    audio_chunks.append(chunk)
                
                # Play audio chunks
                for chunk in audio_chunks:
                    try:
                        import sounddevice as sd
                        import soundfile as sf
                        
                        chunk.seek(0)
                        data, samplerate = sf.read(chunk)
                        sd.play(data, samplerate)
                        sd.wait()  # Wait until the audio is done playing
                    except Exception as e:
                        self.print_status(f"Audio playback error: {e}", "❌")
                
                # Small pause between chunks
                await asyncio.sleep(0.3)
            
        except Exception as e:
            self.print_status(f"TTS error: {e}", "❌")
    
    def _split_text_for_tts(self, text: str) -> list:
        """Split long text into TTS-friendly chunks"""
        # Split on sentence boundaries, keeping chunks under 200 characters
        import re
        
        # First split on sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would make chunk too long, start new chunk
            if len(current_chunk + sentence) > 200 and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def get_voice_config_for_agent(self, agent_name: str) -> dict:
        """Get voice configuration for a specific agent"""
        # Character-specific voice mapping
        voice_profiles = {
            "Tobor": {
                "voice_id": "SMfKQBd8dMBJVxRyV2OV",
                "tts_voice": "en-US-Steffan:DragonHDLatestNeural"
            },
            "Zanne": {
                "voice_id": "vPyUEx8yh5eRpulx9GVe",
                "tts_voice": "nl-NL-ColettaNeural"
            },
            "Els": {
                "voice_id": "RHk7amcwSyv2umxMHEJS",
                "tts_voice": "nl-NL-FennaNeural"
            },
            "Mirza": {
                "voice_id": "HFPhK8BTs1eEDhkawppF",
                "tts_voice": "nl-NL-MaartenNeural"
            },
            "Pjotr": {
                "voice_id": "5BEZKIGvByQrqSymXgwx",
                "tts_voice": "nl-NL-MaartenNeural"
            }
        }
        
        return voice_profiles.get(agent_name, voice_profiles["Tobor"])
    
    async def start_therapy_session(self):
        """Start a new therapy session with user identification"""
        self.session_active = True
        
        self.print_status("Starting family therapy session", "🎭")
        self.print_status("Available participants: Zanne, Els, Mirza, Pjotr, Tobor", "👥")
        
        # Phase 1: Tobor asks who they're talking to
        self.session_phase = "identify_user"
        opening_response = "Hallo! Ik ben Tobor, jullie familie therapeut. Met wie heb ik het genoegen te spreken vandaag?"
        
        self.print_status("Tobor: " + opening_response, "🤖")
        
        # Speak Tobor's opening if TTS is enabled
        if self.tts_enabled:
            await self.speak_response(opening_response, "Tobor")
        
        return opening_response
    
    async def process_input(self, user_input: str, target_agent: str = None):
        """Process user input and generate agent responses based on session phase"""
        
        self.print_status(f"Processing: {user_input}", "👤")
        
        # Handle different conversation phases
        if self.session_phase == "identify_user":
            return await self.handle_user_identification(user_input)
        elif self.session_phase == "greetings" or self.session_phase == "family_greeting":
            return await self.handle_greetings()
        elif self.session_phase == "orchestrated_therapy":
            return await self.handle_orchestrated_therapy(user_input)
        elif self.session_phase == "topic_discovery":
            return await self.handle_topic_discovery(user_input)
        elif self.session_phase == "therapy":
            return await self.handle_therapy_session(user_input, target_agent)
        
        return []
    
    async def handle_user_identification(self, user_input: str):
        """Handle user identification phase"""
        # Store user identity
        self.user_identity = user_input.strip().title()
        
        # Check if user is a family member
        family_members = ["Zanne", "Els", "Mirza", "Pjotr"]
        user_as_member = None
        
        for member in family_members:
            if member.lower() in user_input.lower():
                user_as_member = member
                break
        
        self.user_as_member = user_as_member  # Store as instance variable
        
        if self.user_as_member:
            # User is a family member - remove them from active participants
            if self.user_as_member in self.active_participants:
                self.active_participants.remove(self.user_as_member)
                self.print_status(f"{self.user_as_member} is now the user - removed from AI participants", "👤")
            
            # Update family system to exclude this member
            if self.user_as_member.lower() in self.family_system.agents:
                del self.family_system.agents[self.user_as_member.lower()]
                self.print_status(f"Removed {self.user_as_member} from AI agent system", "🔧")
                
            self.session_phase = "family_greeting"
            response_text = f"Ah, {self.user_as_member}! Welkom terug. Laat me de anderen even laten weten dat je er bent."
        else:
            # User is an outsider - formal introduction
            self.session_phase = "greetings"
            response_text = f"Aangenaam, {self.user_identity}! Ik ga je voorstellen aan de familie."
        
        self.print_status(f"Tobor: {response_text}", "🤖")
        
        if self.tts_enabled:
            await self.speak_response(response_text, "Tobor")
        
        return [{"agent": "Tobor", "response": response_text}]
    
    async def handle_greetings(self):
        """Handle greetings phase - characters greet based on whether user is family or outsider"""
        responses = []
        
        # Each active family member greets appropriately
        for member in self.active_participants:
            if member != "Tobor":
                if self.user_as_member:
                    greeting = await self.get_family_greeting(member, self.user_as_member)
                else:
                    greeting = await self.get_outsider_greeting(member)
                    
                responses.append({"agent": member, "response": greeting})
                
                agent_emoji = {
                    "Zanne": "🎨",
                    "Els": "👩‍⚕️", 
                    "Mirza": "🔧",
                    "Pjotr": "🎭"
                }.get(member, "💭")
                
                self.print_status(f"{member}: {greeting}", agent_emoji)
                
                if self.tts_enabled:
                    await self.speak_response(greeting, member)
        
        # Tobor starts topic discovery
        self.session_phase = "topic_discovery"
        
        if self.user_as_member:
            tobor_response = f"Nu we allemaal bij elkaar zijn, {self.user_as_member}, waar wil je het vandaag over hebben? Wat speelt er in de familie?"
        else:
            tobor_response = f"Dank je {self.user_identity}. Laat me beginnen met vragen wat er speelt in deze familie."
        
        responses.append({"agent": "Tobor", "response": tobor_response})
        self.print_status(f"Tobor: {tobor_response}", "🤖")
        
        if self.tts_enabled:
            await self.speak_response(tobor_response, "Tobor")
        
        return responses
    
    async def get_family_greeting(self, member: str, family_user: str):
        """Get greeting for when user is a family member"""
        family_greetings = {
            "Zanne": {
                "Pjotr": "Oh, Pjotr... weer tijd voor een familie bijeenkomst? Ik hoop dat je niet weer iedereen tevreden probeert te stellen.",
                "Els": "Zanne hier. Laten we hopen dat dit keer niemand mij de schuld geeft van alles.",
                "Mirza": "Zanne. Je bent er dus ook. Laten we proberen rustig te blijven deze keer."
            },
            "Els": {
                "Pjotr": "Pjotr! Fijn dat je er bent. Misschien kun je eindelijk eens uitleggen waarom iedereen zo dramatisch doet.",
                "Zanne": "Els hier. Ik hoop dat je open staat voor wat constructieve feedback vandaag.",
                "Mirza": "Mirza, goed je te zien. Ik heb wat ideeën over hoe we dit kunnen aanpakken."
            },
            "Mirza": {
                "Pjotr": "Pjotr. Goed dat je tijd hebt kunnen maken. Laten we praktisch blijven.",
                "Zanne": "Zanne. Ik hoop dat we vandaag wat verder komen dan de laatste keer.",
                "Els": "Els. Misschien kunnen we samen kijken naar wat echt werkt."
            },
            "Pjotr": {
                "Zanne": "Zanne! Lief dat je er bent. Ik hoop dat we vandaag wat begrip kunnen vinden.",
                "Els": "Els, fijn je te zien. Laten we proberen naar elkaar te luisteren vandaag.",
                "Mirza": "Mirza, welkom. Ik waardeer je nuchtere blik op onze familie situaties."
            }
        }
        
        return family_greetings.get(member, {}).get(family_user, f"Hallo {family_user}, fijn dat je er bent.")
    
    async def get_outsider_greeting(self, member: str):
        """Get greeting for when user is an outsider"""
        outsider_greetings = {
            "Zanne": "Hallo... een nieuwe persoon. Ik hoop dat je niet komt om mij te analyseren.",
            "Els": "Welkom! Fijn dat er iemand van buiten naar onze familie kijkt - misschien zie je wat ik bedoel.",
            "Mirza": "Hallo. Ik ben Mirza. Welkom bij onze familie gesprek.",
            "Pjotr": "Welkom! Ik ben Pjotr. Dank je dat je tijd maakt om naar onze familie dynamiek te luisteren."
        }
        return outsider_greetings.get(member, f"Hallo, ik ben {member}.")
    
    async def handle_orchestrated_therapy(self, user_input: str):
        """Handle orchestrated therapy where Tobor controls the conversation flow"""
        
        # Use the new orchestration-based family system
        responses = await self.family_system.process_user_input(user_input)
        
        # Display all responses
        for response in responses:
            agent_name = response["agent"]
            response_text = response["response"]
            
            # Display response
            agent_emoji = {
                "Zanne": "🎨",
                "Els": "👩‍⚕️", 
                "Mirza": "🔧",
                "Pjotr": "🎭",
                "Tobor": "🤖"
            }.get(agent_name, "💭")
            
            self.print_status(f"{agent_name}: {response_text}", agent_emoji)
            
            # Speak response if TTS is enabled
            if self.tts_enabled:
                await self.speak_response(response_text, agent_name)
        
        # Check if user input is requested
        user_input_requested = any(response.get("request_user_input", False) for response in responses)
        
        if not user_input_requested:
            # Continue orchestrated conversation without user input for 2-3 rounds
            for round_num in range(2):
                await asyncio.sleep(1)  # Brief pause
                
                # Tobor continues orchestrating agent conversations
                continuation_prompt = f"Continue the therapeutic conversation about '{self.therapy_topic}'. Let family members respond to each other naturally."
                
                continuation = await self.family_system.process_user_input(continuation_prompt)
                
                for response in continuation:
                    agent_name = response["agent"]
                    response_text = response["response"]
                    
                    agent_emoji = {
                        "Zanne": "🎨",
                        "Els": "👩‍⚕️", 
                        "Mirza": "🔧",
                        "Pjotr": "🎭",
                        "Tobor": "🤖"
                    }.get(agent_name, "💭")
                    
                    self.print_status(f"{agent_name}: {response_text}", agent_emoji)
                    
                    if self.tts_enabled:
                        await self.speak_response(response_text, agent_name)
                
                # Check if user involvement is now requested after agent conversations
                user_input_requested = any(response.get("request_user_input", False) for response in continuation)
                if user_input_requested:
                    break
        
        return responses
    
    async def handle_topic_discovery(self, user_input: str):
        """Handle topic discovery phase - Tobor asks for therapy topic"""
        
        # Check if user provided a therapy-relevant topic
        therapy_keywords = [
            "familie", "conflict", "ruzie", "probleem", "spanning", "communicatie",
            "begrip", "luisteren", "hulp", "relatie", "emotie", "gevoel",
            "misverstand", "boos", "kwaad", "verdriet", "zorgen", "stress"
        ]
        
        input_lower = user_input.lower()
        is_therapy_relevant = any(keyword in input_lower for keyword in therapy_keywords)
        
        if is_therapy_relevant:
            # User provided relevant topic - start orchestrated therapy
            self.therapy_topic = user_input
            self.session_phase = "orchestrated_therapy"
            
            response_text = f"Dank je. Ik hoor dat dit belangrijk is voor jullie. Laten we hier samen naar kijken."
            
            self.print_status(f"Tobor: {response_text}", "🤖")
            
            if self.tts_enabled:
                await self.speak_response(response_text, "Tobor")
            
            return [{"agent": "Tobor", "response": response_text}]
        
        else:
            # User didn't provide relevant topic - ask more specifically
            follow_up_questions = [
                "Wat vind je het moeilijkst in jullie familie?",
                "Waar loop je tegenaan in jullie familie communicatie?",
                "Wat zou je graag anders willen zien in jullie familie?",
                "Welke uitdagingen ervaar je met de familie?",
                "Wat zorgt voor spanning in jullie familie?"
            ]
            
            import random
            response_text = random.choice(follow_up_questions)
            
            self.print_status(f"Tobor: {response_text}", "🤖")
            
            if self.tts_enabled:
                await self.speak_response(response_text, "Tobor")
            
            return [{"agent": "Tobor", "response": response_text}]
    
    async def handle_therapy_session(self, user_input: str, target_agent: Optional[str] = None):
        """Handle orchestrated therapy where Tobor controls the conversation flow"""
        
        # This is now orchestrated therapy where agents converse with strategic user involvement
        responses = []
        
        # Tobor decides what to do based on conversation state
        orchestration_decision = await self.get_orchestration_decision(user_input)
        
        if orchestration_decision["action"] == "agent_conversation":
            # Let agents talk among themselves
            responses = await self.orchestrate_agent_conversation(orchestration_decision["focus"])
            
        elif orchestration_decision["action"] == "user_involvement":
            # Strategic user involvement
            responses = await self.handle_user_therapeutic_input(user_input)
            
        elif orchestration_decision["action"] == "redirect":
            # Tobor redirects conversation
            responses = await self.orchestrate_redirection(orchestration_decision["direction"])
        
        return responses
    
    async def get_orchestration_decision(self, user_input: str):
        """Tobor decides how to orchestrate the conversation"""
        
        # Analyze conversation state and decide next action
        conversation_history = getattr(self.family_system, 'conversation_context', None)
        recent_messages = []
        if conversation_history and hasattr(conversation_history, 'conversation_history'):
            recent_messages = conversation_history.conversation_history[-3:]
        
        # Simple orchestration logic (can be made more sophisticated)
        if len(recent_messages) < 2:
            # Start with agent conversation
            return {"action": "agent_conversation", "focus": "family_dynamics"}
        
        elif "conflict" in user_input.lower() or "ruzie" in user_input.lower():
            return {"action": "agent_conversation", "focus": "conflict_resolution"}
        
        elif any(agent in user_input.lower() for agent in ["zanne", "els", "mirza", "pjotr"]):
            return {"action": "user_involvement", "target": user_input}
            
        else:
            return {"action": "agent_conversation", "focus": "general_therapy"}
    
    async def orchestrate_agent_conversation(self, focus: str):
        """Orchestrate conversation between agents without user input"""
        
        # Tobor initiates agent discussion
        focus_prompts = {
            "family_dynamics": "Zanne, ik merk wat spanning. Kun je vertellen hoe je je voelt in deze familie?",
            "conflict_resolution": "Els, wat is volgens jou de kern van de problemen in jullie familie?", 
            "general_therapy": "Mirza, wat zie jij als belangrijkste uitdaging voor jullie als familie?"
        }
        
        tobor_prompt = focus_prompts.get(focus, "Laten we eens kijken wat er speelt in jullie familie.")
        
        responses = []
        
        # Tobor starts
        responses.append({"agent": "Tobor", "response": tobor_prompt})
        self.print_status(f"Tobor: {tobor_prompt}", "🤖")
        
        if self.tts_enabled:
            await self.speak_response(tobor_prompt, "Tobor")
        
        # Get agent responses through family system (but limited to 2-3 agents)
        agent_responses = await self.family_system.process_user_input(tobor_prompt, None)
        
        for response in agent_responses[:2]:  # Limit to first 2 responses
            responses.append(response)
            
            agent_emoji = {
                "Zanne": "🎨", "Els": "👩‍⚕️", "Mirza": "🔧", "Pjotr": "🎭", "Tobor": "🤖"
            }.get(response["agent"], "💭")
            
            self.print_status(f"{response['agent']}: {response['response']}", agent_emoji)
            
            if self.tts_enabled:
                await self.speak_response(response["response"], response["agent"])
        
        # Tobor decides if user input is needed
        needs_user_input = await self.should_involve_user()
        if needs_user_input:
            user_prompt = f"{self.user_identity}, wat denk jij hierover?"
            responses.append({"agent": "Tobor", "response": user_prompt, "request_user_input": True})
            self.print_status(f"Tobor: {user_prompt}", "🤖")
            
            if self.tts_enabled:
                await self.speak_response(user_prompt, "Tobor")
        
        return responses
    
    async def should_involve_user(self):
        """Decide if user input is strategically needed"""
        # Strategic logic based on conversation flow
        
        # Don't involve user too frequently
        if hasattr(self.family_system.tobor, 'conversation_turn_count'):
            turn_count = self.family_system.tobor.conversation_turn_count
            
            # Let agents establish conversation first
            if turn_count < 3:
                return False  
            
            # Only involve user every 4-5 turns at most
            if turn_count % 5 != 0:
                return False
        
        # Check if therapeutic intervention is needed from user
        if hasattr(self.family_system.tobor, 'conflict_areas'):
            if len(self.family_system.tobor.conflict_areas) > 2:
                return True  # User input might help resolve conflicts
        
        # Random strategic involvement (15% chance)
        import random
        return random.random() < 0.15
    
    async def handle_user_therapeutic_input(self, user_input: str):
        """Handle when user provides therapeutic input"""
        
        # Process user input therapeutically
        responses = await self.family_system.process_user_input(user_input, None)
        
        # Display responses
        for response in responses:
            agent_emoji = {
                "Zanne": "🎨", "Els": "👩‍⚕️", "Mirza": "🔧", "Pjotr": "🎭", "Tobor": "🤖"
            }.get(response["agent"], "💭")
            
            self.print_status(f"{response['agent']}: {response['response']}", agent_emoji)
            
            if self.tts_enabled:
                await self.speak_response(response["response"], response["agent"])
        
        return responses
    
    async def orchestrate_redirection(self, direction: str):
        """Tobor redirects conversation in therapeutic direction"""
        
        redirection_prompts = {
            "empathy": "Ik hoor pijn in jullie woorden. Kunnen we proberen elkaar te begrijpen?",
            "communication": "Laten we kijken hoe jullie met elkaar communiceren.",
            "solutions": "Wat kunnen jullie doen om deze situatie te verbeteren?"
        }
        
        prompt = redirection_prompts.get(direction, "Laten we een stap terug nemen.")
        
        response = {"agent": "Tobor", "response": prompt}
        self.print_status(f"Tobor: {prompt}", "🤖")
        
        if self.tts_enabled:
            await self.speak_response(prompt, "Tobor")
        
        return [response]
    
    async def run_voice_mode(self):
        """Run therapy session in voice mode"""
        self.voice_mode = True
        
        # Setup voice input
        self.setup_voice_input()
        
        # Start therapy session
        await self.start_therapy_session()
        
        self.print_status("Voice mode activated. Speak to interact with family members.", "🎤")
        self.print_status("Press Ctrl+C to end session", "ℹ️")
        
        try:
            while self.session_active:
                try:
                    # Check for voice input
                    voice_input = self.voice_input_queue.get(timeout=1.0)
                    
                    if voice_input:
                        # Process voice input
                        await self.process_input(voice_input)
                        
                        # Brief pause between interactions
                        await asyncio.sleep(2)
                    
                except Empty:
                    continue
                except KeyboardInterrupt:
                    break
                
        except KeyboardInterrupt:
            self.print_status("Session ended by user", "👋")
        finally:
            self.session_active = False
            if self.stt_manager:
                self.stt_manager.stop()
    
    async def run_text_mode(self):
        """Run therapy session in text mode"""
        self.voice_mode = False
        self.tts_enabled = False  # Disable TTS for text mode
        
        # Start therapy session
        await self.start_therapy_session()
        
        self.print_status("Text mode activated. Type to interact with family members.", "⌨️")
        self.print_status("Type 'quit' to end session", "ℹ️")
        
        try:
            while self.session_active:
                try:
                    # Get user input
                    user_input = input("\n👤 You: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'stop']:
                        break
                    
                    if user_input:
                        # Process text input
                        await self.process_input(user_input)
                        
                        # Brief pause between interactions
                        await asyncio.sleep(1)
                    
                except KeyboardInterrupt:
                    break
                except EOFError:
                    break
                
        except KeyboardInterrupt:
            self.print_status("Session ended by user", "👋")
        finally:
            self.session_active = False
    
    async def run_test_mode(self):
        """Run therapy session in test mode with predefined inputs"""
        self.voice_mode = False
        self.tts_enabled = False  # Disable TTS for test mode
        
        # Start therapy session
        await self.start_therapy_session()
        
        self.print_status("Test mode activated. Running predefined conversation.", "🧪")
        
        # Predefined test inputs designed to trigger different agents
        test_inputs = [
            "Waarom luistert niemand naar me? Ik voel me zo misverstand.",  # Should trigger Zanne + others
            "Ik probeer alleen maar te helpen en voor iedereen te zorgen.",  # Should trigger Els + others
            "Misschien kunnen we samen rustig mediteren over dit probleem.",  # Should trigger Mirza + others
            "Er is teveel conflict in deze familie. Ik ben moe van bemiddelen."  # Should trigger Pjotr + others
        ]
        
        for i, user_input in enumerate(test_inputs):
            self.print_status(f"Test input: {user_input}", "🧪")
            responses = await self.process_input(user_input)
            
            # Show which agents responded for testing purposes
            responding_agents = [r["agent"] for r in responses] if responses else ["None"]
            self.print_status(f"Responded: {', '.join(responding_agents)}", "📝")
            
            await asyncio.sleep(3)  # Pause between test inputs
        
        # Session summary
        summary = self.family_system.get_session_summary()
        self.print_status("Session Summary:", "📊")
        self.print_status(f"Session ID: {summary['session_id']}", "📊")
        self.print_status(f"Conversation length: {summary['conversation_length']} messages", "📊")
        self.print_status(f"Participants: {', '.join(summary['participants'])}", "📊")
        
        self.session_active = False
    
    def display_banner(self):
        """Display application banner"""
        print("\n" + "="*70)
        print("🎭 ADVANCED MULTI-AGENT FAMILY THERAPY SYSTEM 🎭")
        print("="*70)
        print("🤖 Powered by OpenAI GPT-4o with Character Psychology")
        print("👥 Family Members: Zanne, Els, Mirza, Pjotr")
        print("🎭 Therapist: Tobor")
        print("💭 Dynamic responses based on psychological profiles")
        print("="*70)
    
    def display_help(self):
        """Display help information"""
        print("\n📋 COMMANDS:")
        print("  --voice  : Start voice-based therapy session")
        print("  --text   : Start text-based therapy session")
        print("  --test   : Run automated test conversation")
        print("  --help   : Show this help message")
        print("\n🎭 FAMILY MEMBERS:")
        print("  🎨 Zanne : Defensive, creative, feels misunderstood")
        print("  👩‍⚕️ Els   : Controlling, anxious, practical caregiver")
        print("  🔧 Mirza : War survivor, emotionally distant")
        print("  🎭 Pjotr : Diplomatic, people-pleaser, mediator")
        print("  🤖 Tobor : AI therapist, orchestrates sessions")
        print("\n💡 Each family member has detailed psychology profiles")
        print("   and responds dynamically based on their character!")


async def main():
    """Main application entry point"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Advanced Multi-Agent Family Therapy System')
    parser.add_argument('--voice', action='store_true', help='Start voice-based therapy session')
    parser.add_argument('--text', action='store_true', help='Start text-based therapy session')
    parser.add_argument('--test', action='store_true', help='Run automated test conversation')
    parser.add_argument('--help-extended', action='store_true', help='Show extended help')
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        print("Please ensure config files are properly set up.")
        return
    
    # Create application instance
    app = OpenAIMultiAgentTherapyApp(config)
    
    # Display banner
    app.display_banner()
    
    # Handle command line arguments
    if args.help_extended:
        app.display_help()
        return
    
    elif args.voice:
        app.print_status("Starting voice mode therapy session", "🎤")
        await app.run_voice_mode()
    
    elif args.text:
        app.print_status("Starting text mode therapy session", "⌨️")
        await app.run_text_mode()
    
    elif args.test:
        app.print_status("Starting test mode therapy session", "🧪")
        await app.run_test_mode()
    
    else:
        # Default behavior - show help and start text mode
        app.display_help()
        print("\n🎭 Starting default text mode session...")
        await app.run_text_mode()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Thank you for using the Multi-Agent Family Therapy System!")
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        sys.exit(1)
