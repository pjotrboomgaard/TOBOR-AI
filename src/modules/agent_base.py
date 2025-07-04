"""
agent_base.py

Base Agent System for TARS-AI Multi-Agent Architecture
"""

import asyncio
import json
import uuid
import os
import glob
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from modules.module_llm import raw_complete_llm
from modules.module_messageQue import queue_message

class MessageType(Enum):
    USER_INPUT = "user_input"
    AGENT_RESPONSE = "agent_response"
    THERAPY_DIRECTIVE = "therapy_directive"
    CONVERSATION_START = "conversation_start"
    EMOTIONAL_STATE = "emotional_state"

@dataclass
class AgentMessage:
    id: str
    type: MessageType
    sender: str
    target: Optional[str]
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

class AgentCommunicationBus:
    """Central communication system for agents"""
    
    def __init__(self):
        self.agents: Dict[str, 'BaseAgent'] = {}
        self.message_history: List[AgentMessage] = []
        self.message_queue = asyncio.Queue()
        self.running = False
        
    def register_agent(self, agent: 'BaseAgent'):
        """Register an agent with the communication bus"""
        self.agents[agent.name] = agent
        queue_message(f"AGENT: Registered {agent.name}")
        
    async def send_message(self, message: AgentMessage):
        """Send message through the bus"""
        await self.message_queue.put(message)
        
    async def broadcast_message(self, message: AgentMessage):
        """Broadcast message to relevant agents"""
        self.message_history.append(message)
        
        if message.target and message.target in self.agents:
            # Direct message
            agent = self.agents[message.target]
            if agent.active:
                await agent.receive_message(message)
        else:
            # Broadcast to all active agents except sender
            for agent_name, agent in self.agents.items():
                if agent_name != message.sender and agent.active:
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
        
        # Character attributes
        self.char_name = character_data.get('char_name', name.title())
        self.personality = character_data.get('personality', '')
        self.voice_id = character_data.get('voice_id', '')
        self.tts_voice = character_data.get('tts_voice', '')
        
    def set_communication_bus(self, bus: AgentCommunicationBus):
        """Set the communication bus for this agent"""
        self.bus = bus
        bus.register_agent(self)
        
    def get_context_prompt(self, user_input: str = "") -> str:
        """Build context-aware prompt for this agent"""
        recent_context = "\n".join(self.context_memory[-5:]) if self.context_memory else "No recent conversation."
        
        prompt = f"""Je bent {self.char_name}, een lid van een Nederlandse familie in therapie.

Personality: {self.personality}
Recent Conversation:
{recent_context}

Reageer als {self.char_name} op: {user_input}

Houd je reactie kort en natuurlijk. Geen emoji's of acties.

{self.char_name}:"""
        
        return prompt
    
    async def generate_response(self, context: str) -> str:
        """Generate a response based on context"""
        try:
            prompt = self.get_context_prompt(context)
            response = raw_complete_llm(prompt, istext=True)
            
            if response:
                self.context_memory.append(f"{self.char_name}: {response}")
                if len(self.context_memory) > 15:
                    self.context_memory = self.context_memory[-10:]
                return response.strip()
            
        except Exception as e:
            queue_message(f"AGENT ERROR: {self.name} response failed: {e}")
            
        return "Ik kan nu niet reageren."
    
    async def receive_message(self, message: AgentMessage):
        """Process incoming messages"""
        self.context_memory.append(f"{message.sender}: {message.content}")
        
        if message.type == MessageType.USER_INPUT:
            await self.handle_user_input(message)
        elif message.type == MessageType.AGENT_RESPONSE:
            await self.handle_agent_response(message)
    
    async def handle_user_input(self, message: AgentMessage):
        """Handle user input - to be overridden by specific agents"""
        pass
    
    async def handle_agent_response(self, message: AgentMessage):
        """Handle agent responses - to be overridden by specific agents"""
        pass
    
    async def send_response(self, content: str, target: str = None):
        """Send a response through the communication bus"""
        if self.bus:
            message = AgentMessage.create(
                msg_type=MessageType.AGENT_RESPONSE,
                sender=self.name,
                content=content,
                target=target
            )
            await self.bus.send_message(message)
    
    def activate(self):
        """Activate this agent"""
        self.active = True
        queue_message(f"AGENT: {self.name} activated")
    
    def deactivate(self):
        """Deactivate this agent"""
        self.active = False 