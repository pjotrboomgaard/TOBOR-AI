"""
tobor_agent.py

Tobor Orchestrator Agent - Therapy Flow Director
"""

import random
import asyncio
from typing import Dict, List, Set
from modules.agent_base import BaseAgent, AgentMessage, MessageType
from modules.module_messageQue import queue_message

class ToborAgent(BaseAgent):
    """Tobor - Therapeutic orchestrator"""
    
    def __init__(self, character_data: Dict, config: Dict):
        super().__init__("tobor", character_data, config)
        self.session_active = False
        self.session_turn = 0
        self.active_participants: Set[str] = set()
        
    async def start_therapy_session(self, user_input: str = None):
        """Start therapy session"""
        self.session_active = True
        self.session_turn = 1
        
        if user_input:
            opening = f"Ik hoor wat je zegt over: {user_input}. Laten we dit als familie bespreken."
        else:
            opening = "Welkom familie. Wat speelt er vandaag? Wie wil beginnen?"
        
        await self.send_response(opening)
        queue_message(f"Tobor: {opening}")
        
        # Activate family agents
        await self.activate_family_agents()
    
    async def activate_family_agents(self):
        """Gradually activate family agents"""
        family_order = ['pjotr', 'els', 'mirza', 'zanne']
        
        for agent_name in family_order:
            if agent_name in self.bus.agents:
                await asyncio.sleep(1)
                
                directive = f"Reageer op de therapie situatie als {agent_name.title()}"
                message = AgentMessage.create(
                    msg_type=MessageType.THERAPY_DIRECTIVE,
                    sender="tobor",
                    target=agent_name,
                    content=directive
                )
                
                await self.bus.send_message(message)
                self.bus.agents[agent_name].activate()
                self.active_participants.add(agent_name)
    
    async def handle_user_input(self, message: AgentMessage):
        """Handle user input therapeutically"""
        user_input = message.content
        
        # Generate therapeutic response
        prompt = f"""Je bent Tobor, therapeutische robot.
        
User zegt: "{user_input}"

Geef een korte therapeutische reactie die:
- Valideert het gevoel
- Stelt een open vraag
- Max 30 woorden

Tobor:"""
        
        response = await self.generate_response(prompt)
        await self.send_response(response)
        queue_message(f"Tobor: {response}")
        
        # Direct family to respond
        await self.direct_family_responses(user_input)
    
    async def direct_family_responses(self, user_input: str):
        """Direct family members to respond"""
        # Select 2-3 family members to respond
        available = [name for name in self.active_participants if name != "tobor"]
        respondents = random.sample(available, min(3, len(available)))
        
        for agent_name in respondents:
            directive = f"Reageer op gebruiker input: '{user_input}'"
            message = AgentMessage.create(
                msg_type=MessageType.THERAPY_DIRECTIVE,
                sender="tobor",
                target=agent_name,
                content=directive
            )
            
            await asyncio.sleep(1)
            await self.bus.send_message(message)
    
    async def handle_agent_response(self, message: AgentMessage):
        """Monitor family responses and provide guidance"""
        if random.random() < 0.3:  # 30% chance to intervene
            intervention = f"Ik zie een patroon in {message.sender}'s reactie. Laten we dit onderzoeken."
            await asyncio.sleep(2)
            await self.send_response(intervention)
            queue_message(f"Tobor: {intervention}") 