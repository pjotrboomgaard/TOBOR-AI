"""
tobor_orchestrator.py

Tobor Orchestrator Agent - Therapy Flow Director
===============================================

Tobor acts as the orchestrating agent that:
- Directs the therapy session flow
- Decides which agents should respond when
- Maintains therapy goals and progress
- Provides therapeutic guidance and intervention
"""

import random
import asyncio
from typing import Dict, List, Set
from modules.agent_base import BaseAgent, AgentMessage, MessageType
from modules.module_messageQue import queue_message

class ToborOrchestratorAgent(BaseAgent):
    """
    Tobor - Therapeutic orchestrator that manages family therapy sessions
    """
    
    def __init__(self, character_data: Dict, config: Dict):
        super().__init__("tobor", character_data, config)
        
        # Therapy session state
        self.session_active = False
        self.session_turn = 0
        self.active_participants: Set[str] = set()
        self.therapy_goals = []
        self.emotional_tension = 3  # Scale 1-10
        self.breakthrough_achieved = False
        
        # Family dynamics tracking
        self.family_patterns = {
            'zanne_defensive_triggers': 0,
            'els_correction_attempts': 0,
            'mirza_solution_offers': 0,
            'pjotr_mediation_fatigue': 0
        }
        
        # Therapeutic interventions
        self.intervention_strategies = [
            'pattern_recognition',
            'emotional_validation',
            'family_system_analysis',
            'breakthrough_facilitation'
        ]
        
    async def start_therapy_session(self, initial_user_input: str = None):
        """Start a new family therapy session"""
        self.session_active = True
        self.session_turn = 1
        self.active_participants = {'tobor'}
        
        # Therapeutic opening
        if initial_user_input:
            opening = await self.generate_therapeutic_opening(initial_user_input)
        else:
            opening = self.get_default_opening()
        
        # Broadcast session start
        await self.send_response(opening, msg_type=MessageType.CONVERSATION_START)
        queue_message(f"Tobor: {opening}")
        
        # Activate family agents gradually
        await self.orchestrate_family_engagement()
        
    def get_default_opening(self) -> str:
        """Get default therapeutic opening"""
        openings = [
            "Welkom, familie. Ik ben Tobor, jullie therapeutische assistent. Ik detecteer communicatiebarrières in jullie systeem. Laten we beginnen met wat er vandaag speelt.",
            "Familie, ik observeer patronen die we moeten bespreken. Wie wil beginnen met te delen wat er op hun hart ligt?",
            "Ik zie spanning in de familie-dynamiek. Laten we een veilige ruimte creëren om eerlijk te zijn over jullie gevoelens."
        ]
        return random.choice(openings)
    
    async def generate_therapeutic_opening(self, user_input: str) -> str:
        """Generate therapeutic opening based on user input"""
        prompt = f"""Je bent Tobor, een therapeutische AI-robot die familie therapie leidt.

Een familielid heeft net gezegd: "{user_input}"

Genereer een professionele therapeutische opening die:
1. Erkent wat gezegd is
2. Creëert een veilige ruimte voor alle familieleden
3. Stelt een therapeutisch kader
4. Nodigt uit tot verdere dialoog

Houd het professioneel maar warm. Max 50 woorden.

Tobor:"""
        
        response = await self.generate_response(prompt)
        return response
    
    async def orchestrate_family_engagement(self):
        """Gradually bring family members into the conversation"""
        # Determine engagement order based on therapeutic strategy
        engagement_order = self.get_engagement_strategy()
        
        for i, agent_name in enumerate(engagement_order):
            if agent_name in self.bus.agents:
                await asyncio.sleep(2)  # Allow time between engagements
                
                directive = await self.create_engagement_directive(agent_name, i)
                
                message = AgentMessage.create(
                    msg_type=MessageType.THERAPY_DIRECTIVE,
                    sender="tobor",
                    target=agent_name,
                    content=directive,
                    engagement_phase=i,
                    session_turn=self.session_turn
                )
                
                await self.bus.send_message(message)
                self.active_participants.add(agent_name)
                
                # Activate the agent
                if agent_name in self.bus.agents:
                    self.bus.agents[agent_name].activate()
    
    def get_engagement_strategy(self) -> List[str]:
        """Determine which family members to engage and in what order"""
        # Start with most emotionally available, then add challenging ones
        base_order = ['pjotr', 'mirza', 'els', 'zanne']  # From diplomatic to explosive
        
        # Randomize slightly to avoid predictability
        if random.random() < 0.3:
            random.shuffle(base_order[1:3])  # Shuffle middle two
            
        return base_order
    
    async def create_engagement_directive(self, agent_name: str, phase: int) -> str:
        """Create therapeutic directive for engaging specific family member"""
        directives = {
            'pjotr': [
                "Pjotr, als bemiddelaar zie jij veel. Wat observeer je in onze familie-dynamiek?",
                "Pjotr, jouw perspectief is waardevol. Wat zou je willen dat iedereen begreep?"
            ],
            'mirza': [
                "Mirza, vanuit jouw ervaring, wat denk je dat deze familie nodig heeft?",
                "Mirza, ik detecteer dat je vaak oplossingen aanbiedt. Wat triggers deze behoefte?"
            ],
            'els': [
                "Els, je zorgt voor iedereen. Wie zorgt er voor jou? Wat heb je nodig?",
                "Els, ik zie jouw zorgzaamheid. Hoe voelt het als mensen jouw hulp niet accepteren?"
            ],
            'zanne': [
                "Zanne, ik observeer verdedigende reacties. Kun je me helpen begrijpen wat je kwetsbaar maakt?",
                "Zanne, wat zou je willen dat deze familie anders deed? Spreek vrij."
            ]
        }
        
        agent_directives = directives.get(agent_name, ["Deel je gedachten."])
        return random.choice(agent_directives)
    
    async def handle_user_input(self, message: AgentMessage):
        """Process user input and provide therapeutic guidance"""
        self.session_turn += 1
        
        # Analyze user input for therapeutic opportunities
        analysis = await self.analyze_therapeutic_opportunity(message.content)
        
        # Generate therapeutic response
        therapeutic_response = await self.generate_therapeutic_response(message.content, analysis)
        
        await self.send_response(therapeutic_response)
        queue_message(f"Tobor: {therapeutic_response}")
        
        # Decide which family members should respond
        await self.orchestrate_family_responses(message.content, analysis)
    
    async def analyze_therapeutic_opportunity(self, user_input: str) -> Dict:
        """Analyze user input for therapeutic intervention opportunities"""
        analysis = {
            'emotional_content': self.detect_emotions(user_input),
            'family_patterns': self.detect_family_patterns(user_input),
            'intervention_needed': self.assess_intervention_need(user_input),
            'recommended_respondents': []
        }
        
        # Determine which family members should respond
        if 'conflict' in user_input.lower() or 'ruzie' in user_input.lower():
            analysis['recommended_respondents'] = ['pjotr', 'zanne']
        elif 'help' in user_input.lower() or 'hulp' in user_input.lower():
            analysis['recommended_respondents'] = ['els', 'mirza']
        else:
            # General response - select 2-3 family members
            available = ['zanne', 'els', 'mirza', 'pjotr']
            analysis['recommended_respondents'] = random.sample(available, random.randint(2, 3))
        
        return analysis
    
    def detect_emotions(self, text: str) -> List[str]:
        """Detect emotional content in text"""
        emotions = []
        text_lower = text.lower()
        
        emotion_words = {
            'anger': ['boos', 'kwaad', 'woedend', 'geïrriteerd'],
            'sadness': ['verdrietig', 'somber', 'depressief', 'down'],
            'anxiety': ['bang', 'angstig', 'nerveus', 'onzeker'],
            'frustration': ['gefrustreerd', 'moe', 'uitgeput']
        }
        
        for emotion, words in emotion_words.items():
            if any(word in text_lower for word in words):
                emotions.append(emotion)
        
        return emotions
    
    def detect_family_patterns(self, text: str) -> List[str]:
        """Detect family patterns in user input"""
        patterns = []
        text_lower = text.lower()
        
        pattern_indicators = {
            'defensive': ['altijd', 'nooit', 'jullie begrijpen niet'],
            'controlling': ['moet', 'zou moeten', 'verkeerd'],
            'avoiding': ['het maakt niet uit', 'laat maar'],
            'mediating': ['misschien kunnen we', 'beide kanten']
        }
        
        for pattern, indicators in pattern_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                patterns.append(pattern)
        
        return patterns
    
    def assess_intervention_need(self, text: str) -> str:
        """Assess what type of therapeutic intervention is needed"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['help', 'hulp', 'weet niet']):
            return 'guidance'
        elif any(word in text_lower for word in ['conflict', 'ruzie', 'boos']):
            return 'de-escalation'
        elif any(word in text_lower for word in ['eenzaam', 'alleen', 'misunderstood']):
            return 'validation'
        else:
            return 'exploration'
    
    async def generate_therapeutic_response(self, user_input: str, analysis: Dict) -> str:
        """Generate therapeutic response based on analysis"""
        intervention_type = analysis['intervention_needed']
        emotions = analysis['emotional_content']
        
        prompt = f"""Je bent Tobor, een therapeutische AI-robot. 

User input: "{user_input}"
Gedetecteerde emoties: {emotions}
Interventie type: {intervention_type}

Genereer een therapeutische respons die:
- Valideert de emoties
- Stelt een therapeutische vraag
- Behoudt professionele warmte
- Max 40 woorden

Tobor:"""
        
        response = await self.generate_response(prompt)
        return response
    
    async def orchestrate_family_responses(self, user_input: str, analysis: Dict):
        """Orchestrate which family members should respond"""
        respondents = analysis['recommended_respondents']
        
        # Send targeted directives to specific family members
        for agent_name in respondents:
            if agent_name in self.bus.agents and agent_name in self.active_participants:
                directive = f"Reageer op wat de gebruiker zei: '{user_input}'"
                
                message = AgentMessage.create(
                    msg_type=MessageType.THERAPY_DIRECTIVE,
                    sender="tobor",
                    target=agent_name,
                    content=directive,
                    user_input=user_input,
                    therapeutic_context=analysis
                )
                
                await asyncio.sleep(1)  # Stagger responses
                await self.bus.send_message(message)
    
    async def handle_agent_response(self, message: AgentMessage):
        """Monitor and guide family member responses"""
        sender = message.sender
        content = message.content
        
        # Track family patterns
        self.track_family_patterns(sender, content)
        
        # Assess if therapeutic intervention is needed
        if self.needs_therapeutic_intervention(sender, content):
            intervention = await self.generate_intervention(sender, content)
            await asyncio.sleep(2)  # Allow space after agent response
            await self.send_response(intervention)
            queue_message(f"Tobor: {intervention}")
    
    def track_family_patterns(self, sender: str, content: str):
        """Track recurring family patterns"""
        content_lower = content.lower()
        
        if sender == "zanne" and any(word in content_lower for word in ['niemand', 'altijd', 'jullie']):
            self.family_patterns['zanne_defensive_triggers'] += 1
            
        elif sender == "els" and any(word in content_lower for word in ['moet', 'beter', 'help']):
            self.family_patterns['els_correction_attempts'] += 1
            
        elif sender == "mirza" and 'mindfulness' in content_lower:
            self.family_patterns['mirza_solution_offers'] += 1
            
        elif sender == "pjotr" and any(word in content_lower for word in ['misschien', 'beide', 'kunnen we']):
            self.family_patterns['pjotr_mediation_fatigue'] += 1
    
    def needs_therapeutic_intervention(self, sender: str, content: str) -> bool:
        """Determine if therapeutic intervention is needed"""
        # Intervene after certain pattern thresholds
        if (self.family_patterns['zanne_defensive_triggers'] > 2 or
            self.family_patterns['els_correction_attempts'] > 3 or
            self.session_turn > 8):
            return True
        return False
    
    async def generate_intervention(self, sender: str, content: str) -> str:
        """Generate therapeutic intervention"""
        pattern_count = self.family_patterns[f'{sender}_pattern'] if f'{sender}_pattern' in self.family_patterns else 0
        
        prompt = f"""Je bent Tobor. {sender.title()} heeft net gezegd: "{content}"

Je detecteert een patroon. Genereer een therapeutische interventie die:
- Benoemt het patroon zonder te beschuldigen
- Vraagt naar de onderliggende behoefte
- Houdt het warm maar direct
- Max 35 woorden

Tobor:"""
        
        response = await self.generate_response(prompt)
        return response
    
    async def facilitate_breakthrough(self):
        """Facilitate family breakthrough moments"""
        if not self.breakthrough_achieved and self.session_turn > 10:
            breakthrough_prompt = """Familie, ik observeer patronen die jullie generaties teruggaan. 
            Elke persoon hier probeert liefde te tonen op hun eigen manier. 
            De vraag is: gaan jullie elkaars talen leren, of blijven communiceren in code?"""
            
            await self.send_response(breakthrough_prompt)
            queue_message(f"Tobor: {breakthrough_prompt}")
            self.breakthrough_achieved = True
    
    def end_session(self):
        """End the therapy session"""
        self.session_active = False
        self.active_participants.clear()
        queue_message("THERAPY: Session ended by orchestrator") 