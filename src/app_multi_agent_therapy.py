"""
app_multi_agent_therapy.py

Multi-Agent Voice Therapy Application for TARS-AI
=================================================

This application uses a multi-agent architecture where each family member
runs as an independent agent with Tobor as the orchestrating therapist.

Features:
- Individual agent context and memory for each character
- Voice input/output for each agent
- Tobor orchestrates therapy flow
- Agents can respond to each other independently
"""

import asyncio
import threading
import time
import queue
from datetime import datetime
from typing import Dict, List

# Core modules
from modules.module_config import load_config
from modules.module_character import CharacterManager
from modules.module_memory import MemoryManager
from modules.module_stt import STTManager
from modules.module_tts import play_audio_chunks
from modules.module_messageQue import queue_message

# Agent system
from modules.agent_base import AgentCommunicationBus, AgentMessage, MessageType
from modules.family_agents import ZanneAgent, ElsAgent, MirzaAgent, PjotrAgent
from modules.tobor_agent import ToborAgent

# === Configuration ===
CONFIG = load_config()

# === Global State ===
communication_bus = None
agents: Dict[str, object] = {}
session_active = False
voice_input_queue = queue.Queue()

def print_status(message: str):
    """Print timestamped status messages"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}")

async def initialize_agent_system():
    """Initialize the multi-agent system"""
    global communication_bus, agents
    
    print_status("🤖 Initializing Multi-Agent System...")
    
    # Create communication bus
    communication_bus = AgentCommunicationBus()
    
    # Load character configurations
    characters_config = CONFIG.get('CHARACTERS', {})
    
    # Create agents for each character
    agent_classes = {
        'zanne': ZanneAgent,
        'els': ElsAgent,
        'mirza': MirzaAgent,
        'pjotr': PjotrAgent,
        'tobor': ToborAgent
    }
    
    for char_name, agent_class in agent_classes.items():
        if char_name in characters_config or char_name == 'tobor':
            # Get character data
            if char_name == 'tobor':
                # Use CHAR section for Tobor
                char_data = {
                    'char_name': 'Tobor',
                    'personality': 'Therapeutic AI robot, clinical but warm',
                    'voice_id': CONFIG['TTS']['voice_id'],
                    'tts_voice': CONFIG['TTS']['tts_voice']
                }
            else:
                # Parse character config
                char_config = characters_config[char_name]
                config_parts = [part.strip() for part in char_config.split(',')]
                
                char_data = {
                    'char_name': char_name.title(),
                    'personality': f'{char_name.title()} family member',
                    'voice_id': config_parts[1] if len(config_parts) > 1 else '',
                    'tts_voice': config_parts[2] if len(config_parts) > 2 else ''
                }
            
            # Create agent
            agent = agent_class(char_data, CONFIG)
            agent.set_communication_bus(communication_bus)
            agents[char_name] = agent
            
            print_status(f"✅ Created {char_name.title()} agent")
    
    print_status(f"🤖 Agent system initialized with {len(agents)} agents")

async def start_voice_input_handler():
    """Handle voice input in a separate thread"""
    def voice_input_worker():
        print_status("🎤 Voice input handler started")
        
        # Initialize STT
        stt_manager = STTManager(CONFIG, None, None)
        
        def voice_callback(json_result):
            try:
                import json
                result = json.loads(json_result)
                text = result.get("text", "").strip()
                if text:
                    voice_input_queue.put(text)
                    print_status(f"🎤 Voice detected: {text}")
            except Exception as e:
                print_status(f"🎤 Voice callback error: {e}")
        
        stt_manager.set_utterance_callback(voice_callback)
        stt_manager.start()
        
        try:
            while session_active:
                time.sleep(0.1)
        finally:
            stt_manager.stop()
            print_status("🎤 Voice input handler stopped")
    
    voice_thread = threading.Thread(target=voice_input_worker, daemon=True)
    voice_thread.start()
    return voice_thread

async def play_agent_voice_response(agent_name: str, text: str):
    """Play voice response for specific agent"""
    try:
        if agent_name in agents:
            agent = agents[agent_name]
            
            # Get voice configuration for this agent
            voice_config = {
                'voice_id': agent.voice_id,
                'tts_voice': agent.tts_voice,
                'character_name': agent.char_name
            }
            
            print_status(f"🔊 {agent.char_name} speaking...")
            
            # Play TTS with character's voice
            await play_audio_chunks(text, CONFIG['TTS']['ttsoption'], voice_config)
            
            print_status(f"✅ {agent.char_name} finished speaking")
            
    except Exception as e:
        print_status(f"❌ Voice playback error for {agent_name}: {e}")

async def handle_agent_message(message: AgentMessage):
    """Handle agent messages and play voice responses"""
    if message.type == MessageType.AGENT_RESPONSE:
        # Play the agent's response with their voice
        await play_agent_voice_response(message.sender, message.content)
        
        print_status(f"💬 {message.sender.title()}: {message.content}")

async def start_therapy_session():
    """Start the multi-agent therapy session"""
    global session_active
    
    print_status("🏥 Starting Multi-Agent Family Therapy Session...")
    session_active = True
    
    # Start voice input handler
    voice_thread = await start_voice_input_handler()
    
    # Start communication bus
    bus_task = asyncio.create_task(communication_bus.start())
    
    # Start with Tobor's opening
    tobor_agent = agents.get('tobor')
    if tobor_agent:
        await tobor_agent.start_therapy_session()
        await play_agent_voice_response('tobor', "Welkom familie. Wat speelt er vandaag? Ik luister.")
    
    print_status("🎧 Listening for voice input... Say something to begin therapy.")
    
    # Main therapy loop
    try:
        while session_active:
            # Check for voice input
            try:
                user_input = voice_input_queue.get(timeout=1.0)
                
                print_status(f"👤 User: {user_input}")
                
                # Send user input to communication bus
                user_message = AgentMessage.create(
                    msg_type=MessageType.USER_INPUT,
                    sender="user",
                    content=user_input
                )
                
                await communication_bus.send_message(user_message)
                
                # Wait a bit for agent responses
                await asyncio.sleep(3)
                
            except queue.Empty:
                continue
            except Exception as e:
                print_status(f"❌ Error processing voice input: {e}")
                
    except KeyboardInterrupt:
        print_status("🛑 Session interrupted by user")
    
    finally:
        session_active = False
        communication_bus.stop()
        print_status("🏥 Therapy session ended")

async def run_interactive_therapy():
    """Run interactive therapy with voice input/output"""
    print_status("🚀 TARS-AI Multi-Agent Therapy System Starting...")
    
    try:
        # Initialize agent system
        await initialize_agent_system()
        
        # Override agent message handling to include voice
        original_broadcast = communication_bus.broadcast_message
        
        async def enhanced_broadcast(message):
            await original_broadcast(message)
            await handle_agent_message(message)
        
        communication_bus.broadcast_message = enhanced_broadcast
        
        # Start therapy session
        await start_therapy_session()
        
    except Exception as e:
        print_status(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()

async def run_test_mode():
    """Run test mode without voice input/output"""
    print_status("🧪 Running Multi-Agent Test Mode...")
    
    await initialize_agent_system()
    
    # Start communication bus
    bus_task = asyncio.create_task(communication_bus.start())
    
    # Test with Tobor starting session
    tobor_agent = agents.get('tobor')
    if tobor_agent:
        await tobor_agent.start_therapy_session("Ik voel me niet begrepen in deze familie")
    
    # Simulate some agent interactions
    test_inputs = [
        "Waarom luistert niemand naar me?",
        "Ik probeer alleen maar te helpen",
        "Misschien moeten we meer mediteren",
        "Ik ben moe van altijd de bemiddelaar te zijn"
    ]
    
    for test_input in test_inputs:
        print_status(f"👤 Test input: {test_input}")
        
        user_message = AgentMessage.create(
            msg_type=MessageType.USER_INPUT,
            sender="user",
            content=test_input
        )
        
        await communication_bus.send_message(user_message)
        await asyncio.sleep(5)  # Wait for responses
    
    communication_bus.stop()
    print_status("🧪 Test mode completed")

def main():
    """Main entry point"""
    print_status("=" * 60)
    print_status("🤖 TARS-AI Multi-Agent Family Therapy System")
    print_status("=" * 60)
    
    # Check if test mode
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        asyncio.run(run_test_mode())
    else:
        asyncio.run(run_interactive_therapy())

if __name__ == "__main__":
    main() 