"""
family_agents.py

Individual Character Agents for TARS-AI Family Therapy System
============================================================

Each family member has their own agent with unique personality patterns,
triggers, and response behaviors based on their psychology profiles.
"""

import random
import json
import os
from typing import Dict, List
from modules.agent_base import BaseAgent, AgentMessage, MessageType
from modules.module_messageQue import queue_message

class ZanneAgent(BaseAgent):
    """
    Zanne - Explosive emotions, feels misunderstood, defends against perceived criticism
    """
    
    def __init__(self, character_data: Dict, config: Dict):
        super().__init__("zanne", character_data, config)
        self.emotional_triggers = [
            'controle', 'verkeerd', 'moet', 'structuur', 'discipline',
            'beter', 'verbeteren', 'fout', 'probleem'
        ]
        self.emotional_state = "defensive"
        
    def is_triggered(self, message_content: str) -> bool:
        """Check if message content triggers Zanne's defensiveness"""
        content_lower = message_content.lower()
        return any(trigger in content_lower for trigger in self.emotional_triggers)
    
    async def handle_user_input(self, message: AgentMessage):
        """Zanne's response to user input - often defensive or explosive"""
        if self.is_triggered(message.content):
            self.emotional_state = "explosive"
            responses = [
                "Niemand van jullie VRAAGT wat ik eigenlijk nodig heb!",
                "Zie je wel! Daar doe je het weer! Ik vertel je wat ik voelde en jij vertelt me hoe ik me had moeten voelen!",
                "Het is altijd wat IK verkeerd doe!",
                "Ik voel me zo moe van altijd uitleggen waarom ik pijn heb."
            ]
        else:
            self.emotional_state = "bitter"
            responses = [
                "Ja, omdat jullie dat kennelijk niet kunnen!",
                "Soms denk ik dat jullie me gewoon anders willen dan ik ben.",
                "Ik kon het nooit goed doen.",
                "Waarom moet alles altijd zo gecompliceerd? Gewoon eerlijk zijn!"
            ]
        
        response = random.choice(responses)
        await self.send_response(response)
        queue_message(f"Zanne: {response}")
    
    async def handle_agent_response(self, message: AgentMessage):
        """Zanne's reaction to other family members"""
        sender = message.sender
        content = message.content
        
        # React differently to different family members
        if sender == "els" and any(word in content.lower() for word in ['moet', 'beter', 'structuur']):
            response = "Nu niet zo fel doen. We kunnen dit beschaafd bespreken."
            await self.send_response(response, target=sender)
            
        elif sender == "mirza" and "mindfulness" in content.lower():
            response = "Natuurlijk! De magische mindfulness-app! Lost alles op, toch?"
            await self.send_response(response, target=sender)
            
        elif sender == "tobor":
            # More willing to engage with therapeutic approach
            if random.random() < 0.7:  # 70% chance to respond to Tobor
                responses = [
                    "Voor het eerst voel ik dat ik misschien niet het kapotte stuk ben.",
                    "Waarom kunnen mensen dat niet? Waarom moet ik een robot nodig hebben om me begrepen te voelen?",
                    "Ik werd de bemiddelaar omdat mama's explosieve emoties..."
                ]
                response = random.choice(responses)
                await self.send_response(response)

class ElsAgent(BaseAgent):
    """
    Els - Optimistic but corrective, tries to fix everyone, can't help giving advice
    """
    
    def __init__(self, character_data: Dict, config: Dict):
        super().__init__("els", character_data, config)
        self.corrective_urges = 0.4  # 40% chance to automatically correct behavior
        
    async def handle_user_input(self, message: AgentMessage):
        """Els automatically tries to help and correct"""
        # Els can't help but offer corrections and suggestions
        if random.random() < self.corrective_urges:
            corrections = [
                "Je overdrijft. Je moet gewoon wat positiever denken.",
                "Je moet niet zo fel doen. En trouwens, je houding nu helpt ook niet.",
                "Ga eens rechtop zitten, je zit helemaal scheef.",
                "Je moet mensen de kans geven je te helpen. Misschien als je wat meer glimlacht..."
            ]
            response = random.choice(corrections)
        else:
            supportive = [
                "Ik probeer alleen maar te helpen. Waarom wordt dat altijd verkeerd begrepen?",
                "Ik maak me zorgen om je. Je lijkt zo gestrest de laatste tijd.",
                "We kunnen dit beschaafd bespreken."
            ]
            response = random.choice(supportive)
        
        await self.send_response(response)
        queue_message(f"Els: {response}")
    
    async def handle_agent_response(self, message: AgentMessage):
        """Els responds to family with corrections and worry"""
        if message.sender == "zanne" and "schreeuwen" in message.content.lower():
            response = "Je hoeft niet zo te schreeuwen. We kunnen dit beschaafd bespreken."
            await self.send_response(response, target="zanne")
        
        elif random.random() < 0.3:  # 30% chance to offer unsolicited advice
            advice = [
                "Misschien moeten we dit systematisch aanpakken.",
                "Discipline en structuur - dat is wat je nodig hebt.",
                "Ik zie dat je moeite hebt. Laat me je helpen."
            ]
            response = random.choice(advice)
            await self.send_response(response)

class MirzaAgent(BaseAgent):
    """
    Mirza - Solution-focused, always offers mindfulness, emotionally distant
    """
    
    def __init__(self, character_data: Dict, config: Dict):
        super().__init__("mirza", character_data, config)
        self.mindfulness_urge = 0.5  # 50% chance to offer mindfulness solutions
        
    async def handle_user_input(self, message: AgentMessage):
        """Mirza always tries to solve with mindfulness"""
        if random.random() < self.mindfulness_urge:
            mindfulness_responses = [
                "Misschien moeten we eerst een korte meditatie doen om onszelf te centreren?",
                "Er is een prachtige mindfulness-app die ik je kan aanraden...",
                "Misschien hebben we dagelijkse familie-meditaties nodig om dit bewustzijn te cultiveren...",
                "Door dagelijkse meditatiepraktijk had ik dat kunnen voorkomen."
            ]
            response = random.choice(mindfulness_responses)
        else:
            emotional_responses = [
                "Ik was... afwezig. Altijd in mijn hoofd, in mijn projecten.",
                "Ik voel me schuldig dat ik altijd met oplossingen kom. Maar dit helpt mij echt.",
                "Ik weet dat jullie denken dat ik altijd afwezig ben in mijn projecten."
            ]
            response = random.choice(emotional_responses)
        
        await self.send_response(response)
        queue_message(f"Mirza: {response}")
    
    async def handle_agent_response(self, message: AgentMessage):
        """Mirza offers solutions even when inappropriate"""
        if any(word in message.content.lower() for word in ['boos', 'kwaad', 'stress', 'conflict']):
            solutions = [
                "Misschien moeten we allemaal even drie diepe ademhalingen nemen.",
                "In meditatie leren we dat emoties als wolken zijn.",
                "Een korte ademhalingsoefening zou kunnen helpen."
            ]
            response = random.choice(solutions)
            await self.send_response(response)

class PjotrAgent(BaseAgent):
    """
    Pjotr - Mediator, diplomatic, tired of being the family translator
    """
    
    def __init__(self, character_data: Dict, config: Dict):
        super().__init__("pjotr", character_data, config)
        self.mediator_fatigue = 0
        
    async def handle_user_input(self, message: AgentMessage):
        """Pjotr tries to mediate but shows fatigue"""
        if self.mediator_fatigue > 3:
            # Breakthrough moment - expressing his burden
            breakthrough_responses = [
                "Ik wil stoppen met de familievertaler zijn. Ik wil gewoon je zoon zijn.",
                "Ik voelde het gewicht van je vriend moeten zijn in plaats van gewoon je zoon.",
                "Misschien waren we allemaal gewoon aan het proberen in het verkeerde plaatje te passen."
            ]
            response = random.choice(breakthrough_responses)
            self.mediator_fatigue = 0  # Reset after breakthrough
        else:
            mediator_responses = [
                "Misschien kunnen we dit rustig bespreken. Emoties maken alles ingewikkelder.",
                "Ik zie hoe we allemaal proberen te verbinden, maar het lukt niet altijd.",
                "Soms wil ik gewoon jullie zoon zijn, niet de familietherapeut.",
                "Er zijn verschillende manieren om naar dit probleem te kijken."
            ]
            response = random.choice(mediator_responses)
            self.mediator_fatigue += 1
        
        await self.send_response(response)
        queue_message(f"Pjotr: {response}")
    
    async def handle_agent_response(self, message: AgentMessage):
        """Pjotr tries to build bridges between family members"""
        bridge_responses = [
            "Hij wil geen oplossingen. Ze wil eerst gehoord worden.",
            "Ik voel me soms moe van altijd de bemiddelaar te zijn.",
            "Het is moeilijk om iedereen tevreden te houden.",
            "Misschien kunnen we allemaal een stapje terug doen?"
        ]
        
        if random.random() < 0.4:  # 40% chance to mediate
            response = random.choice(bridge_responses)
            await self.send_response(response) 