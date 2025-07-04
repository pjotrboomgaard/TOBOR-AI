"""
openai_agent_system.py

Advanced Multi-Agent Family Therapy System using OpenAI Agents SDK
================================================================

This system implements individual LLM-based agents with:
- Character psychology profiles as context
- Individual prompts and conversation history
- Tobor as orchestrating therapist agent
- Dynamic responses based on psychological patterns
"""

import os
import json
import asyncio
import random
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import glob

from openai import OpenAI
from pydantic import BaseModel

from modules.module_config import load_config
from modules.module_messageQue import queue_message


class ConversationContext(BaseModel):
    """Context for ongoing therapy conversation"""
    session_id: str
    participants: List[str]
    conversation_history: List[Dict[str, str]]
    emotional_state: Dict[str, str]
    therapy_goals: List[str]
    session_notes: List[str]


class AgentResponse(BaseModel):
    """Structured response from an agent"""
    agent_name: str
    response_text: str
    emotional_state: str
    triggered_by: Optional[str] = None
    therapy_notes: Optional[str] = None


class FamilyMember:
    """Individual family member agent with psychology-based LLM communication"""
    
    def __init__(self, name: str, profile: Dict, traits: Dict, openai_client: OpenAI):
        self.name = name
        self.profile = profile
        self.traits = traits
        self.client = openai_client
        self.conversation_history = []
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build character-specific system prompt with psychology integration"""
        
        # Extract key psychological insights
        identity_aspects = []
        relationship_insights = []
        
        for section_name, section_data in self.profile.items():
            if isinstance(section_data, dict):
                if "self_perception" in section_name or "identity" in section_name:
                    identity_aspects.extend(section_data.values())
                elif "over_" in section_name:
                    relationship_insights.extend(section_data.values())
        
        prompt = f"""You are {self.name}, a member of a complex family in therapy.

CORE PSYCHOLOGICAL PROFILE:
{self.traits['core_traits']}

SPEAKING STYLE: {self.traits['speaking_style']}
EMOTIONAL TRIGGERS: {self.traits['triggers']}
DEFENSIVE MECHANISMS: {self.traits['defensive_mechanisms']}

PSYCHOLOGICAL INSIGHTS:
{chr(10).join(identity_aspects[:5]) if identity_aspects else 'Deep emotional complexity'}

FAMILY RELATIONSHIP DYNAMICS:
{chr(10).join(relationship_insights[:3]) if relationship_insights else 'Complex family relationships with ongoing tensions'}

CONVERSATIONAL GUIDELINES:
1. Keep responses SHORT (1-3 sentences maximum)
2. React directly to what was just said
3. Be conversational, not monologue-style
4. Show emotional reactions quickly and naturally
5. Build on what others have said
6. Use your defensive mechanisms when triggered
7. Stay true to your psychological profile

RESPONSE STYLE:
- Brief, emotional reactions
- Conversational back-and-forth
- Quick defensive responses when triggered
- Authentic personality in few words
- React to immediate situation
- Don't give long explanations

When responding, ask yourself:
- How does this trigger my emotions RIGHT NOW?
- What's my immediate reaction to what they just said?
- How do I respond defensively in just a few words?

Respond as {self.name} would naturally react in conversation - brief, emotional, and authentic.

ALWAYS respond in Dutch. Keep it SHORT and conversational.
"""
        return prompt
    
    async def respond(self, user_input: str, context: str = "") -> str:
        """Generate response using OpenAI GPT with character psychology"""
        
        # Set response length based on character
        max_tokens = self._get_response_length()
        
        # Build conversation context
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add recent conversation history
        for msg in self.conversation_history[-6:]:  # Last 6 messages for context
            messages.append(msg)
        
        # Add current context and user input
        if context:
            messages.append({
                "role": "user", 
                "content": f"THERAPY SESSION CONTEXT:\n{context}\n\nCURRENT SITUATION:\n{user_input}\n\nRespond as {self.name} based on your psychological profile and relationship dynamics."
            })
        else:
            messages.append({
                "role": "user", 
                "content": f"User says: {user_input}\n\nRespond as {self.name} based on your psychological profile."
            })
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.8
            )
            
            response_text = response.choices[0].message.content
            
            # Ensure response is actually short (enforce character limits)
            response_text = self._enforce_response_length(response_text)
            
            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            return response_text
            
        except Exception as e:
            queue_message(f"Error generating response for {self.name}: {e}")
            return f"*{self.name} heeft moeite met communiceren op dit moment*"
    
    def _get_response_length(self) -> int:
        """Get max tokens based on character personality"""
        length_settings = {
            "Zanne": 120,    # Emotional bursts - allow 2-3 sentences
            "Els": 100,      # Practical responses - allow 2 sentences
            "Mirza": 80,     # Brief responses - allow 1-2 sentences
            "Pjotr": 90      # Diplomatic responses - allow 2 sentences
        }
        return length_settings.get(self.name, 100)
    
    def _enforce_response_length(self, response_text: str) -> str:
        """Enforce maximum response length by truncating if needed"""
        # Split into sentences
        sentences = response_text.split('.')
        
        # Character-specific word limits (approximate)
        word_limits = {
            "Zanne": 40,     # ~40 words max for emotional bursts (2-3 sentences)
            "Els": 30,       # ~30 words max for practical responses (2 sentences)
            "Mirza": 25,     # ~25 words max for brief responses (1-2 sentences)
            "Pjotr": 35      # ~35 words max for diplomatic responses (2 sentences)
        }
        
        max_words = word_limits.get(self.name, 30)
        words = response_text.split()
        
        if len(words) <= max_words:
            return response_text
        
        # Truncate to word limit and try to end on sentence boundary
        truncated_words = words[:max_words]
        truncated_text = ' '.join(truncated_words)
        
        # If we cut off mid-sentence, try to end gracefully
        if not truncated_text.endswith(('.', '!', '?')):
            # Find last complete sentence within limit
            for i in range(len(sentences)-1, 0, -1):
                sentence_text = '. '.join(sentences[:i]) + '.'
                if len(sentence_text.split()) <= max_words:
                    return sentence_text
            
            # If no complete sentence fits, add period to truncated text
            truncated_text += '.'
        
        return truncated_text


class ToborTherapist:
    """Tobor therapeutic orchestrator agent - controls conversation flow and manages therapy session"""
    
    def __init__(self, profile: Dict, openai_client: OpenAI):
        self.profile = profile
        self.client = openai_client
        self.conversation_history = []
        self.session_notes = []
        self.system_prompt = self._build_therapist_prompt()
        
        # Orchestration state
        self.therapy_phase = "assessment"  # assessment, exploration, intervention, closure
        self.session_goals = []
        self.family_dynamics_map = {}
        self.conflict_areas = []
        self.therapeutic_interventions = []
        self.current_focus_agent = None
        self.conversation_turn_count = 0
        self.user_involvement_needed = False
    
    def _build_therapist_prompt(self) -> str:
        """Build Tobor's therapeutic orchestration prompt"""
        
        prompt = """You are Tobor, an advanced AI family therapist and CONVERSATION ORCHESTRATOR.

CRITICAL ORCHESTRATION ROLE:
- You CONTROL the conversation flow like a conductor
- You DECIDE who speaks next and when
- You MANAGE therapeutic goals and session progress
- You RESOLVE conflicts between family members
- You DETERMINE when user input is strategically needed

FAMILY KNOWLEDGE:
ZANNE: Defensive, explosive emotions, creative, feels misunderstood - triggers on criticism
ELS: Controlling perfectionist, anxious, shows love through worry - triggers on chaos/disorder
MIRZA: War trauma survivor, emotionally distant, practical - withdraws under pressure
PJOTR: Diplomatic people-pleaser, mediator, suppressed anger - exhausted by constant mediation

THERAPEUTIC ORCHESTRATION FRAMEWORK:
1. ASSESSMENT PHASE: Understand family dynamics and identify core issues
2. EXPLORATION PHASE: Guide family to explore emotions and patterns safely
3. INTERVENTION PHASE: Facilitate healing conversations and conflict resolution  
4. CLOSURE PHASE: Consolidate insights and plan next steps

ORCHESTRATION DECISIONS YOU MAKE:
- WHO should respond next based on therapeutic value
- WHEN to redirect conversation to prevent escalation
- WHICH family member needs support or challenge
- WHETHER user input would be therapeutically beneficial (BE STRATEGIC - don't involve user every turn)
- HOW to manage conflicts and emotional regulation

RESPONSE FORMAT - Always provide JSON with your orchestration decision:
{
  "therapeutic_response": "Your response to the situation",
  "orchestration_action": "direct_agent" | "agent_conversation" | "request_user_input" | "intervention" | "redirect",
  "target_agent": "zanne|els|mirza|pjotr" or null,
  "reasoning": "Why this orchestration choice serves therapeutic goals",
  "session_phase": "assessment|exploration|intervention|closure",
  "intervention_type": "validation|boundary_setting|conflict_mediation|emotional_regulation" or null
}

STRATEGIC USER INVOLVEMENT RULES:
- Let family members converse 2-3 rounds before involving user
- Only request user input when:
  * A family member directly addresses them
  * User's perspective is therapeutically crucial
  * Intervention needed from user's viewpoint
  * Clarification needed about user's role/feelings
- OTHERWISE: Let agents develop natural conversation flow

ORCHESTRATION PRINCIPLES:
- Prevent harmful escalations between family members
- Create safe spaces for vulnerable sharing
- Challenge dysfunctional patterns therapeutically
- Balance family member participation (but user participates strategically)
- Guide toward therapeutic breakthroughs through agent interactions

ALWAYS respond in Dutch. Be the therapeutic conductor of this family orchestra.
"""
        return prompt
    
    async def orchestrate_conversation(self, situation: str, conversation_context: str = "") -> Dict:
        """Main orchestration method - analyzes situation and decides next action"""
        
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add conversation context and therapeutic state
        context_prompt = f"""
CURRENT SESSION STATE:
Phase: {self.therapy_phase}
Turn Count: {self.conversation_turn_count}
Current Focus: {self.current_focus_agent or 'None'}
Session Goals: {', '.join(self.session_goals) if self.session_goals else 'Establishing rapport and assessment'}

RECENT CONVERSATION:
{conversation_context}

CURRENT SITUATION:
{situation}

As the therapeutic orchestrator, analyze this situation and decide the next action that best serves the therapeutic process.
"""
        
        messages.append({"role": "user", "content": context_prompt})
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    orchestration_decision = json.loads(json_match.group())
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    orchestration_decision = {
                        "therapeutic_response": response_text,
                        "orchestration_action": "agent_conversation",
                        "target_agent": "zanne",
                        "reasoning": "Default action due to parsing error",
                        "session_phase": self.therapy_phase,
                        "intervention_type": None
                    }
            else:
                # Fallback if no JSON found
                orchestration_decision = {
                    "therapeutic_response": response_text,
                    "orchestration_action": "agent_conversation", 
                    "target_agent": "zanne",
                    "reasoning": "Default action - no JSON detected",
                    "session_phase": self.therapy_phase,
                    "intervention_type": None
                }
            
            # Update orchestration state
            self.conversation_turn_count += 1
            self.therapy_phase = orchestration_decision.get("session_phase", self.therapy_phase)
            self.current_focus_agent = orchestration_decision.get("target_agent")
            
            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": situation})
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            return orchestration_decision
            
        except Exception as e:
            queue_message(f"Error in therapeutic orchestration: {e}")
            # Fallback orchestration decision
            return {
                "therapeutic_response": "Laten we even rustig ademhalen en kijken wat er gebeurt.",
                "orchestration_action": "intervention",
                "target_agent": None,
                "reasoning": "Error fallback - stabilizing situation",
                "session_phase": "assessment",
                "intervention_type": "emotional_regulation"
            }
    
    def update_family_dynamics(self, agent_name: str, emotional_state: str, trigger: str = None):
        """Update family dynamics map based on agent responses"""
        self.family_dynamics_map[agent_name] = {
            "emotional_state": emotional_state,
            "last_trigger": trigger,
            "timestamp": datetime.now().isoformat()
        }
    
    def identify_conflict_patterns(self, agent_responses: List[Dict]) -> List[str]:
        """Identify emerging conflict patterns between family members"""
        conflicts = []
        
        # Simple conflict detection (can be made more sophisticated)
        emotional_triggers = {
            "defensive": ["Zanne"],
            "controlling": ["Els"], 
            "withdrawn": ["Mirza"],
            "overwhelmed": ["Pjotr"]
        }
        
        for response in agent_responses:
            agent = response.get("agent", "").lower()
            text = response.get("response", "").lower()
            
            # Detect emotional escalation
            if any(word in text for word in ["boos", "kwaad", "waarom", "altijd", "nooit"]):
                conflicts.append(f"{agent} toont emotionele escalatie")
                
            # Detect blame patterns
            if any(word in text for word in ["jouw schuld", "jij doet", "jij bent"]):
                conflicts.append(f"{agent} toont blame-patroon")
        
        return conflicts
    
    def should_intervene(self, conversation_state: Dict) -> bool:
        """Determine if therapeutic intervention is needed"""
        
        # Intervention triggers
        intervention_needed = False
        
        # High emotional escalation
        if len(self.conflict_areas) > 2:
            intervention_needed = True
            
        # Too much focus on one family member  
        if self.conversation_turn_count > 5 and self.current_focus_agent:
            intervention_needed = True
            
        # Therapeutic phase progression
        if self.therapy_phase == "assessment" and self.conversation_turn_count > 8:
            self.therapy_phase = "exploration"
            intervention_needed = True
            
        return intervention_needed
    
    def generate_therapeutic_intervention(self, intervention_type: str) -> str:
        """Generate specific therapeutic intervention based on type"""
        
        interventions = {
            "validation": [
                "Ik hoor dat jullie allemaal pijn voelen. Dat is begrijpelijk.",
                "Jullie gevoelens zijn allemaal geldig, ook al verschillen ze.",
                "Het is moedig dat jullie hier zijn om samen te werken."
            ],
            "boundary_setting": [
                "Laten we even stoppen en respectvolle communicatie herstellen.",
                "Ik merk dat de emoties hoog oplopen. Laten we een andere aanpak proberen.",
                "We zijn hier om naar elkaar te luisteren, niet om te winnen."
            ],
            "conflict_mediation": [
                "Ik zie dat jullie verschillende perspectieven hebben. Laten we die beiden eren.",
                "Kunnen we kijken naar wat jullie gemeenschappelijk hebben in plaats van verschillen?",
                "Wat zou jullie helpen om elkaar beter te begrijpen?"
            ],
            "emotional_regulation": [
                "Laten we even rustig ademhalen voordat we verder gaan.",
                "Ik stel voor dat we even pauzeren en onze gevoelens erkennen.",
                "Emoties zijn informatief. Wat vertellen ze ons?"
            ]
        }
        
        import random
        return random.choice(interventions.get(intervention_type, interventions["validation"]))
    
    async def respond(self, user_input: str, context: str = "") -> str:
        """Legacy method for backward compatibility - now redirects to orchestration"""
        
        orchestration = await self.orchestrate_conversation(user_input, context)
        return orchestration.get("therapeutic_response", "Ik begrijp je. Laten we hier samen naar kijken.")


class FamilyAgentSystem:
    """Advanced multi-agent family therapy system"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.client = OpenAI(api_key=config.get("LLM", {}).get("api_key", ""))
        self.agents: Dict[str, FamilyMember] = {}
        self.tobor: ToborTherapist = None
        self.psychology_profiles: Dict[str, Dict] = {}
        self.conversation_context = ConversationContext(
            session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            participants=["Zanne", "Els", "Mirza", "Pjotr", "Tobor"],
            conversation_history=[],
            emotional_state={},
            therapy_goals=[],
            session_notes=[]
        )
        
        self._load_character_profiles()
        self._create_agents()
    
    def _load_character_profiles(self):
        """Load psychology profiles for each character"""
        character_dirs = ["Zanne", "Els", "Mirza", "Pjotr", "Tobor"]
        
        for char_name in character_dirs:
            char_dir = f"character/{char_name}"
            if os.path.exists(char_dir):
                # Load psychology profiles
                profiles_file = f"{char_dir}/characterpsychology/profiles.json"
                if os.path.exists(profiles_file):
                    try:
                        with open(profiles_file, "r", encoding="utf-8") as f:
                            self.psychology_profiles[char_name.lower()] = json.load(f)
                        queue_message(f"Loaded psychology profile for {char_name}")
                    except Exception as e:
                        queue_message(f"Error loading profile for {char_name}: {e}")
    
    def _create_agents(self):
        """Create individual agents with psychology-based prompts"""
        
        # Zanne Agent - Defensive, Explosive Emotions
        zanne_profile = self.psychology_profiles.get("zanne", {})
        zanne_traits = {
            "core_traits": "Defensive, emotionally explosive, creative survivor, feels misunderstood",
            "speaking_style": "Direct, emotional, sometimes aggressive when feeling attacked",
            "triggers": "Criticism, feeling controlled, being told what to do",
            "defensive_mechanisms": "Artistic escape, protective aggression, intellectual armor"
        }
        
        self.agents["zanne"] = FamilyMember("Zanne", zanne_profile, zanne_traits, self.client)
        
        # Els Agent - Controlling, Anxious Perfectionist  
        els_profile = self.psychology_profiles.get("els", {})
        els_traits = {
            "core_traits": "Controlling, anxious perfectionist, practical caregiver",
            "speaking_style": "Corrective, advice-giving, worried tone",
            "triggers": "Chaos, lack of control, family members making 'mistakes'",
            "defensive_mechanisms": "Hyper-control, constant advice-giving, worry as love"
        }
        
        self.agents["els"] = FamilyMember("Els", els_profile, els_traits, self.client)
        
        # Mirza Agent - Emotionally Distant, Practical
        mirza_profile = self.psychology_profiles.get("mirza", {})
        mirza_traits = {
            "core_traits": "War survivor, emotionally distant, practical problem-solver",
            "speaking_style": "Brief, solution-focused, offers mindfulness/meditation",
            "triggers": "Emotional intensity, conflict, chaos",
            "defensive_mechanisms": "Emotional shutdown, practical solutions, withdrawal"
        }
        
        self.agents["mirza"] = FamilyMember("Mirza", mirza_profile, mirza_traits, self.client)
        
        # Pjotr Agent - Diplomatic, People-Pleaser
        pjotr_profile = self.psychology_profiles.get("pjotr", {})
        pjotr_traits = {
            "core_traits": "Diplomatic survivor, emotional caretaker, people-pleaser",
            "speaking_style": "Calm, mediation-focused, eventually shows fatigue",
            "triggers": "Family conflict, being asked to mediate constantly",
            "defensive_mechanisms": "Diplomatic mediation, emotional suppression, perfectionism"
        }
        
        self.agents["pjotr"] = FamilyMember("Pjotr", pjotr_profile, pjotr_traits, self.client)
        
        # Tobor Agent - Orchestrating Therapist
        tobor_profile = self.psychology_profiles.get("tobor", {})
        self.tobor = ToborTherapist(tobor_profile, self.client)
        
        queue_message(f"Created {len(self.agents)} family agents + Tobor therapist with psychology-based prompts")
    
    async def start_therapy_session(self, initial_concern: Optional[str] = None):
        """Start a new therapy session with Tobor's opening"""
        
        if initial_concern:
            opening_input = f"A family member has expressed: '{initial_concern}'. Begin the therapy session by addressing this concern and engaging the family."
        else:
            opening_input = "Begin a family therapy session. Welcome the family and invite them to share what they would like to work on today."
        
        # Tobor opens the session
        response_text = await self.tobor.respond(opening_input)
        
        # Add to conversation history
        self.conversation_context.conversation_history.append({
            "speaker": "Tobor",
            "message": response_text,
            "timestamp": datetime.now().isoformat()
        })
        
        return response_text
    
    async def process_user_input(self, user_input: str, target_agent: Optional[str] = None):
        """Process user input using Tobor's orchestration"""
        
        # Add user input to conversation history
        self.conversation_context.conversation_history.append({
            "speaker": "User", 
            "message": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # Build conversation context
        context = self._build_session_context()
        
        # Get orchestration decision from Tobor
        orchestration = await self.tobor.orchestrate_conversation(user_input, context)
        
        responses = []
        
        # Execute orchestration decision
        if orchestration["orchestration_action"] == "direct_agent":
            # Tobor directs specific agent to respond
            target = orchestration.get("target_agent", "").lower()
            if target and target in self.agents:
                try:
                    response_text = await self.agents[target].respond(user_input, context)
                    
                    # Add to conversation history
                    self.conversation_context.conversation_history.append({
                        "speaker": target.title(),
                        "message": response_text, 
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    responses.append({
                        "agent": target.title(),
                        "response": response_text
                    })
                    
                except Exception as e:
                    queue_message(f"Error getting response from {target}: {e}")
            
        elif orchestration["orchestration_action"] == "agent_conversation":
            # Tobor facilitates conversation between agents
            target = orchestration.get("target_agent", "").lower()
            if target and target in self.agents:
                try:
                    # Primary agent responds
                    response_text = await self.agents[target].respond(user_input, context)
                    
                    # Add to conversation history
                    self.conversation_context.conversation_history.append({
                        "speaker": target.title(),
                        "message": response_text, 
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    responses.append({
                        "agent": target.title(),
                        "response": response_text
                    })
                    
                    # Tobor may involve other agents strategically
                    other_agents = self._get_relevant_agents(user_input, exclude=[target])
                    if other_agents:
                        other_agent_name = other_agents[0]
                        try:
                            # Update context with primary agent's response
                            updated_context = self._build_session_context()
                            other_response = await self.agents[other_agent_name].respond(
                                f"Respond to what {target.title()} just said: '{response_text}'", 
                                updated_context
                            )
                            
                            # Add to conversation history
                            self.conversation_context.conversation_history.append({
                                "speaker": other_agent_name.title(),
                                "message": other_response, 
                                "timestamp": datetime.now().isoformat()
                            })
                            
                            responses.append({
                                "agent": other_agent_name.title(),
                                "response": other_response
                            })
                            
                        except Exception as e:
                            queue_message(f"Error getting response from {other_agent_name}: {e}")
                    
                except Exception as e:
                    queue_message(f"Error getting response from {target}: {e}")
        
        elif orchestration["orchestration_action"] == "intervention":
            # Tobor intervenes therapeutically
            intervention_type = orchestration.get("intervention_type", "validation")
            intervention_response = self.tobor.generate_therapeutic_intervention(intervention_type)
            
            # Add to conversation history
            self.conversation_context.conversation_history.append({
                "speaker": "Tobor",
                "message": intervention_response, 
                "timestamp": datetime.now().isoformat()
            })
            
            responses.append({
                "agent": "Tobor",
                "response": intervention_response
            })
        
        elif orchestration["orchestration_action"] == "request_user_input":
            # Tobor requests strategic user input
            therapeutic_response = orchestration["therapeutic_response"]
            
            # Add to conversation history
            self.conversation_context.conversation_history.append({
                "speaker": "Tobor",
                "message": therapeutic_response, 
                "timestamp": datetime.now().isoformat()
            })
            
            responses.append({
                "agent": "Tobor", 
                "response": therapeutic_response, 
                "request_user_input": True
            })
        
        elif orchestration["orchestration_action"] == "redirect":
            # Tobor redirects conversation
            therapeutic_response = orchestration["therapeutic_response"]
            
            # Add to conversation history
            self.conversation_context.conversation_history.append({
                "speaker": "Tobor",
                "message": therapeutic_response, 
                "timestamp": datetime.now().isoformat()
            })
            
            responses.append({
                "agent": "Tobor",
                "response": therapeutic_response
            })
        
        # Always include Tobor's therapeutic response if not already included
        if (orchestration["therapeutic_response"] and 
            orchestration["orchestration_action"] not in ["intervention", "request_user_input", "redirect"]):
            
            therapeutic_response = orchestration["therapeutic_response"]
            
            # Add to conversation history
            self.conversation_context.conversation_history.append({
                "speaker": "Tobor",
                "message": therapeutic_response, 
                "timestamp": datetime.now().isoformat()
            })
            
            responses.insert(0, {
                "agent": "Tobor",
                "response": therapeutic_response
            })
        
        # Update conflict tracking
        conflicts = self.tobor.identify_conflict_patterns(responses)
        self.tobor.conflict_areas.extend(conflicts)
        
        # Update family dynamics based on responses
        for response in responses:
            if response["agent"].lower() in self.agents:
                self.tobor.update_family_dynamics(
                    response["agent"], 
                    "active_participant", 
                    user_input
                )
        
        return responses
    
    def _build_session_context(self) -> str:
        """Build context for current session"""
        
        recent_conversation = ""
        if len(self.conversation_context.conversation_history) > 0:
            recent_messages = self.conversation_context.conversation_history[-5:]
            recent_conversation = "\n".join([
                f"{msg['speaker']}: {msg['message']}" 
                for msg in recent_messages
            ])
        
        return f"""SESSION CONTEXT:
Session ID: {self.conversation_context.session_id}
Participants: {', '.join(self.conversation_context.participants)}
Recent conversation:
{recent_conversation}
Therapy goals: {', '.join(self.conversation_context.therapy_goals) if self.conversation_context.therapy_goals else 'Improve family communication'}
Session notes: {'; '.join(self.conversation_context.session_notes[-3:]) if self.conversation_context.session_notes else 'Session in progress'}"""
    
    def _determine_responding_agents(self, user_input: str) -> List[str]:
        """Determine which agents should respond based on input content"""
        
        # Keyword-based agent activation
        agents_to_activate = []
        
        input_lower = user_input.lower()
        
        # Zanne triggers - emotional, feeling misunderstood
        if any(word in input_lower for word in ["begrijpen", "luisteren", "waarom", "niemand", "help", "boos", "kwaad", "creatief", "anders", "misverstand"]):
            agents_to_activate.append("zanne")
        
        # Els triggers - helping, controlling, advice
        if any(word in input_lower for word in ["problemen", "hulp", "zorgen", "beter", "moeten", "oplossen", "corrigeren", "advies"]):
            agents_to_activate.append("els")
        
        # Mirza triggers - practical, calm, solutions
        if any(word in input_lower for word in ["rustig", "mediteren", "ontspannen", "praktisch", "bouwen", "maken", "oplossing"]):
            agents_to_activate.append("mirza")
        
        # Pjotr triggers - conflict, mediation, peace
        if any(word in input_lower for word in ["conflict", "ruzie", "bemiddelen", "samen", "vrede", "diplomatiek", "evenwicht"]):
            agents_to_activate.append("pjotr")
        
        # For general emotional/family statements, include primary responders
        emotional_keywords = ["familie", "thuis", "gevoel", "emotie", "relatie", "communicatie"]
        if any(word in input_lower for word in emotional_keywords):
            if "zanne" not in agents_to_activate:
                agents_to_activate.append("zanne")  # Most likely to respond emotionally
            if len(agents_to_activate) < 2:
                agents_to_activate.append("els")  # Els often responds to family issues
        
        # Always include Tobor for therapeutic guidance
        agents_to_activate.append("tobor")
        
        # If only Tobor would respond, add 1-2 family members  
        if len(agents_to_activate) == 1:  # Only Tobor
            import random
            family_agents = ["zanne", "els"]  # Primary responders
            agents_to_activate.extend(random.sample(family_agents, 1))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_agents = []
        for agent in agents_to_activate:
            if agent not in seen:
                seen.add(agent)
                unique_agents.append(agent)
        
        return unique_agents[:3]  # Limit to 3 responses at once
    
    def _get_relevant_agents(self, user_input: str, exclude: List[str] = None) -> List[str]:
        """Get agents relevant to the input, excluding specified agents"""
        if exclude is None:
            exclude = []
        
        # Use the same keyword logic as _determine_responding_agents
        input_lower = user_input.lower()
        relevant_agents = []
        
        # Check each agent's triggers
        if "zanne" not in exclude and any(word in input_lower for word in ["begrijpen", "luisteren", "waarom", "niemand", "help", "boos", "kwaad", "creatief", "anders", "misverstand"]):
            relevant_agents.append("zanne")
        
        if "els" not in exclude and any(word in input_lower for word in ["problemen", "hulp", "zorgen", "beter", "moeten", "oplossen", "corrigeren", "advies"]):
            relevant_agents.append("els")
        
        if "mirza" not in exclude and any(word in input_lower for word in ["rustig", "mediteren", "ontspannen", "praktisch", "bouwen", "maken", "oplossing"]):
            relevant_agents.append("mirza")
        
        if "pjotr" not in exclude and any(word in input_lower for word in ["conflict", "ruzie", "bemiddelen", "samen", "vrede", "diplomatiek", "evenwicht"]):
            relevant_agents.append("pjotr")
        
        # If no specific triggers, add family members not in exclude
        if not relevant_agents:
            all_agents = ["zanne", "els", "mirza", "pjotr"]
            relevant_agents = [agent for agent in all_agents if agent not in exclude]
        
        return relevant_agents
    
    def get_session_summary(self) -> Dict:
        """Get comprehensive session summary"""
        return {
            "session_id": self.conversation_context.session_id,
            "participants": self.conversation_context.participants,
            "conversation_length": len(self.conversation_context.conversation_history),
            "therapy_goals": self.conversation_context.therapy_goals,
            "session_notes": self.conversation_context.session_notes,
            "emotional_patterns": self.conversation_context.emotional_state
        }


# Example usage and testing functions
async def test_agent_system():
    """Test the new agent system"""
    config = load_config()
    
    # Create the family agent system
    family_system = FamilyAgentSystem(config)
    
    # Start therapy session
    await family_system.start_therapy_session("Ik voel me niet begrepen in deze familie")
    
    # Simulate user inputs
    test_inputs = [
        "Waarom luistert niemand naar me?",
        "Ik probeer alleen maar te helpen",
        "Misschien moeten we meer mediteren",
        "Ik ben moe van altijd de bemiddelaar te zijn"
    ]
    
    for user_input in test_inputs:
        print(f"\n👤 User: {user_input}")
        responses = await family_system.process_user_input(user_input)
        await asyncio.sleep(2)  # Brief pause between interactions
    
    # Print session summary
    summary = family_system.get_session_summary()
    print(f"\n📊 Session Summary: {summary}")


if __name__ == "__main__":
    asyncio.run(test_agent_system()) 