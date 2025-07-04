"""
agent_system.py

Multi-Agent System for TARS-AI Family Therapy
=============================================

This module provides a multi-agent architecture where each family member
runs as an independent agent with their own context, memory, and personality.

Key Components:
- BaseAgent: Core agent functionality
- AgentCommunicationBus: Inter-agent messaging system
- Individual character agents: ElsAgent, ZanneAgent, MirzaAgent, PjotrAgent
- OrchestratorAgent (Tobor): Therapy flow director

Each agent maintains:
- Individual context and memory
- Character-specific personality and responses
- Voice configuration
- Psychology profiles
- Independent decision making
"""

import asyncio
import json
import uuid
import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from modules.module_config import load_config
from modules.module_llm import raw_complete_llm
from modules.module_messageQue import queue_message

# === Message Types ===
class MessageType(Enum):
    USER_INPUT = "user_input"
    AGENT_RESPONSE = "agent_response"
    THERAPY_DIRECTIVE = "therapy_directive"
    CONVERSATION_START = "conversation_start"
    CONVERSATION_END = "conversation_end"
    AGENT_JOIN = "agent_join"
    AGENT_LEAVE = "agent_leave"
    EMOTIONAL_STATE = "emotional_state"
    MEMORY_UPDATE = "memory_update"

@dataclass
class AgentMessage:
    """Message structure for inter-agent communication"""
    id: str
    type: MessageType
    sender: str
    target: Optional[str]  # None for broadcast
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    
    @classmethod
    def create(cls, msg_type: MessageType, sender: str, content: str, 
               target: str = None, **metadata):
        return cls(
            id=str(uuid.uuid4()),
            type=msg_type,
            sender=sender,
            target=target,
            content=content,
            metadata=metadata,
            timestamp=datetime.now()
        )

# === Agent Communication Bus ===
class AgentCommunicationBus:
    """Central communication system for agents"""
    
    def __init__(self):
        self.agents: Dict[str, 'BaseAgent'] = {}
        self.message_history: List[AgentMessage] = []
        self.subscribers: Dict[MessageType, List[str]] = {}
        self.running = False
        self.message_queue = asyncio.Queue()
        
    def register_agent(self, agent: 'BaseAgent'):
        """Register an agent with the communication bus"""
        self.agents[agent.name] = agent
        queue_message(f"AGENT: Registered {agent.name}")
        
    def unregister_agent(self, agent_name: str):
        """Unregister an agent"""
        if agent_name in self.agents:
            del self.agents[agent_name]
            queue_message(f"AGENT: Unregistered {agent_name}")
    
    def subscribe(self, agent_name: str, message_type: MessageType):
        """Subscribe agent to specific message types"""
        if message_type not in self.subscribers:
            self.subscribers[message_type] = []
        if agent_name not in self.subscribers[message_type]:
            self.subscribers[message_type].append(agent_name)
    
    async def send_message(self, message: AgentMessage):
        """Send message through the bus"""
        await self.message_queue.put(message)
        
    async def broadcast_message(self, message: AgentMessage):
        """Broadcast message to all relevant agents"""
        self.message_history.append(message)
        
        # Determine recipients
        recipients = []
        if message.target:
            # Direct message
            if message.target in self.agents:
                recipients = [message.target]
        else:
            # Broadcast to subscribers
            recipients = self.subscribers.get(message.type, [])
            
        # Deliver to recipients
        for agent_name in recipients:
            if agent_name in self.agents and agent_name != message.sender:
                agent = self.agents[agent_name]
                await agent.receive_message(message)
    
    async def start(self):
        """Start the communication bus"""
        self.running = True
        queue_message("AGENT: Communication bus started")
        
        while self.running:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self.broadcast_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                queue_message(f"AGENT ERROR: Bus error: {e}")
    
    def stop(self):
        """Stop the communication bus"""
        self.running = False
        queue_message("AGENT: Communication bus stopped")
    
    def get_recent_messages(self, count: int = 10) -> List[AgentMessage]:
        """Get recent messages for context"""
        return self.message_history[-count:]

# === Base Agent Class ===
class BaseAgent:
    """Base class for all agents in the system"""
    
    def __init__(self, name: str, character_data: Dict, config: Dict):
        self.name = name
        self.character_data = character_data
        self.config = config
        self.bus: Optional[AgentCommunicationBus] = None
        
        # Agent state
        self.active = False
        self.context_memory: List[str] = []
        self.emotional_state = "neutral"
        self.conversation_turn_count = 0
        
        # Character attributes
        self.char_name = character_data.get('char_name', name.title())
        self.personality = character_data.get('personality', '')
        self.psychology_profiles = {}
        
        # Voice configuration
        self.voice_id = character_data.get('voice_id', '')
        self.tts_voice = character_data.get('tts_voice', '')
        
        # Load psychology profiles
        self.load_psychology_profiles()
        
    def set_communication_bus(self, bus: AgentCommunicationBus):
        """Set the communication bus for this agent"""
        self.bus = bus
        bus.register_agent(self)
        
        # Subscribe to relevant message types
        self.bus.subscribe(self.name, MessageType.USER_INPUT)
        self.bus.subscribe(self.name, MessageType.AGENT_RESPONSE)
        self.bus.subscribe(self.name, MessageType.THERAPY_DIRECTIVE)
        
    def load_psychology_profiles(self):
        """Load character-specific psychology profiles"""
        try:
            psychology_dir = f"character/{self.name.title()}/characterpsychology"
            if os.path.exists(psychology_dir):
                for file_path in glob.glob(os.path.join(psychology_dir, "*.json")):
                    with open(file_path, 'r') as f:
                        profile_data = json.load(f)
                        profile_name = os.path.basename(file_path).replace('.json', '')
                        self.psychology_profiles[profile_name] = profile_data
                        
            queue_message(f"AGENT: {self.name} loaded {len(self.psychology_profiles)} psychology profiles")
        except Exception as e:
            queue_message(f"AGENT ERROR: Failed to load psychology for {self.name}: {e}")
    
    def get_context_prompt(self, user_input: str = "") -> str:
        """Build context-aware prompt for this agent"""
        now = datetime.now()
        dtg = f"Current Date: {now.strftime('%m/%d/%Y')}\nCurrent Time: {now.strftime('%H:%M:%S')}\n"
        
        # Recent conversation context
        recent_context = "\n".join(self.context_memory[-5:]) if self.context_memory else "No recent conversation."
        
        # Psychology context
        psychology_context = ""
        if self.psychology_profiles:
            psychology_context = f"### {self.char_name} Psychology:\n"
            for profile_name, profile_data in self.psychology_profiles.items():
                psychology_context += f"**{profile_name}**: {json.dumps(profile_data, indent=2)}\n"
        
        prompt = f"""System: Je bent {self.char_name}, een lid van een Nederlandse familie in therapie.

### Character Information:
Name: {self.char_name}
Personality: {self.personality}
Current Emotional State: {self.emotional_state}

{psychology_context}

### Context:
{dtg}
Recent Conversation:
{recent_context}

### Instruction:
Reageer als {self.char_name} op de volgende situatie. Blijf in karakter en gebruik je unieke persoonlijkheid en achtergrond. 
Houd je reactie kort en natuurlijk. Gebruik geen emoji's of acties tussen sterretjes.

Input: {user_input}

Response ({self.char_name}):"""
        
        return prompt
    
    async def generate_response(self, context: str, target_agent: str = None) -> str:
        """Generate a response based on context"""
        try:
            prompt = self.get_context_prompt(context)
            response = raw_complete_llm(prompt, istext=True)
            
            if response:
                # Update context memory
                self.context_memory.append(f"{self.char_name}: {response}")
                self.conversation_turn_count += 1
                
                # Keep memory manageable
                if len(self.context_memory) > 20:
                    self.context_memory = self.context_memory[-15:]
                
                return response.strip()
            
        except Exception as e:
            queue_message(f"AGENT ERROR: {self.name} response generation failed: {e}")
            
        return f"Ik heb moeite met reageren op dit moment."
    
    async def receive_message(self, message: AgentMessage):
        """Process incoming messages"""
        try:
            # Add to context memory
            self.context_memory.append(f"{message.sender}: {message.content}")
            
            # Process based on message type
            if message.type == MessageType.USER_INPUT:
                await self.handle_user_input(message)
            elif message.type == MessageType.AGENT_RESPONSE:
                await self.handle_agent_response(message)
            elif message.type == MessageType.THERAPY_DIRECTIVE:
                await self.handle_therapy_directive(message)
                
        except Exception as e:
            queue_message(f"AGENT ERROR: {self.name} message processing failed: {e}")
    
    async def handle_user_input(self, message: AgentMessage):
        """Handle user input messages"""
        # Default behavior - can be overridden by specific agents
        pass
    
    async def handle_agent_response(self, message: AgentMessage):
        """Handle responses from other agents"""
        # Default behavior - can be overridden by specific agents
        pass
    
    async def handle_therapy_directive(self, message: AgentMessage):
        """Handle therapy directives from orchestrator"""
        # Default behavior - can be overridden by specific agents
        pass
    
    async def send_response(self, content: str, target: str = None, msg_type: MessageType = MessageType.AGENT_RESPONSE):
        """Send a response through the communication bus"""
        if self.bus:
            message = AgentMessage.create(
                msg_type=msg_type,
                sender=self.name,
                content=content,
                target=target,
                emotional_state=self.emotional_state,
                turn_count=self.conversation_turn_count
            )
            await self.bus.send_message(message)
    
    def activate(self):
        """Activate this agent"""
        self.active = True
        queue_message(f"AGENT: {self.name} activated")
    
    def deactivate(self):
        """Deactivate this agent"""
        self.active = False
        queue_message(f"AGENT: {self.name} deactivated")
    
    def get_voice_config(self) -> Dict:
        """Get voice configuration for TTS"""
        return {
            'voice_id': self.voice_id,
            'tts_voice': self.tts_voice,
            'character_name': self.char_name
        }

# === Global Communication Bus Instance ===
communication_bus = AgentCommunicationBus() 