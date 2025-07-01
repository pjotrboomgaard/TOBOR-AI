"""
Memory-Integrated Family Therapy Prompting System
Creates natural conversations with authentic memory integration
"""

import json
import random
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class MemoryIntegratedPrompt:
    def __init__(self):
        self.character_memories = {}
        self.conversation_context = []
        self.memory_trigger_keywords = {
            'career': ['carrière', 'werk', 'baan', 'toekomst', 'keuze'],
            'family_history': ['vroeger', 'toen', 'herinner', 'verleden', 'kind'],
            'emotions': ['boos', 'verdrietig', 'bang', 'onzeker', 'gefrustreerd'],
            'relationships': ['familie', 'vader', 'moeder', 'broer', 'zus'],
            'trauma': ['pijn', 'moeilijk', 'verlies', 'alleen', 'angst'],
            'control': ['perfect', 'controleren', 'regels', 'discipline'],
            'creativity': ['creatief', 'kunst', 'maken', 'project', 'dromen']
        }
        
        # Character-specific memory integration patterns
        self.character_patterns = {
            'els': {
                'memory_frequency': 0.4,
                'trigger_style': 'control_anxiety',
                'memory_phrases': [
                    "Ik herinner me toen ik...",
                    "Dat doet me denken aan toen...", 
                    "Net zoals vroeger toen ik...",
                    "Achteraf was dat misschien..."
                ],
                'emotional_triggers': ['onzekerheid', 'chaos', 'oncontroleerbaarheid']
            },
            'zanne': {
                'memory_frequency': 0.5,
                'trigger_style': 'confrontational_recall',
                'memory_phrases': [
                    "Weet je nog toen...",
                    "Ik herinner me precies...",
                    "Voor mij was het...",
                    "Dat is precies zoals toen..."
                ],
                'emotional_triggers': ['afwijzing', 'niet begrepen', 'creativiteit bedreigd']
            },
            'mirza': {
                'memory_frequency': 0.2,
                'trigger_style': 'trauma_association', 
                'memory_phrases': [
                    "In de kampen leerde ik...",
                    "Overleven betekent...",
                    "Op mijn achtste...",
                    "Ik was geen goede..."
                ],
                'emotional_triggers': ['confrontatie', 'emotionele druk', 'vaderschap']
            },
            'pjotr': {
                'memory_frequency': 0.3,
                'trigger_style': 'metaphorical_connection',
                'memory_phrases': [
                    "Ik filmde laatst...",
                    "Het is net zoals...",
                    "Dat doet me denken aan...",
                    "Ik zag iets dat..."
                ],
                'emotional_triggers': ['conflict', 'familie spanning', 'keuzes maken']
            }
        }
        
        self.load_character_memories()
        
    def load_character_memories(self):
        """Load memories from character psychology profiles"""
        characters = ['els', 'zanne', 'mirza', 'pjotr']
        
        for char in characters:
            # Fix the path - should be relative to src directory
            char_path = Path(f"../character/{char.title()}/characterpsychology")
            self.character_memories[char] = {}
            
            if char_path.exists():
                for json_file in char_path.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            for category, memories in data.items():
                                if category not in self.character_memories[char]:
                                    self.character_memories[char][category] = []
                                
                                if isinstance(memories, list):
                                    self.character_memories[char][category].extend(memories)
                                elif isinstance(memories, dict):
                                    self.character_memories[char][category].append(memories)
                                    
                    except Exception as e:
                        print(f"DEBUG: Could not load memories for {char}: {e}")
            else:
                print(f"DEBUG: Character path not found: {char_path}")
                        
            print(f"MEMORY: Loaded {len(self.character_memories[char])} memory categories for {char}")
    
    def generate_memory_integrated_response(self, character: str, target: str, context: str, conversation_history: List[str]) -> str:
        """Generate response with potential memory integration"""
        
        # Build conversation context
        full_context = f"{' '.join(conversation_history[-3:])} {context}"
        
        # Generate base response
        base_response = self.generate_base_character_response(character, target, context, conversation_history)
        
        # Check if memory should be triggered (30% chance)
        if random.random() < 0.3 and character in self.character_memories:
            memory_integration = self.get_memory_integration(character, full_context)
            if memory_integration:
                return f"{base_response}\n\n{memory_integration}"
        
        return base_response
    
    def get_memory_integration(self, character: str, context: str) -> Optional[str]:
        """Get memory integration for character based on context"""
        char_memories = self.character_memories.get(character, {})
        if not char_memories:
            return None
        
        # Find contextually relevant memories based on keywords
        context_lower = context.lower()
        relevant_memories = []
        
        # Check each memory category for relevance
        for category, memories in char_memories.items():
            if not memories or not isinstance(memories, list):
                continue
                
            category_relevance = 0
            # Check if category name relates to context
            if any(keyword in category.lower() for keyword in ['family', 'mama', 'els', 'mirza', 'pjotr']):
                if any(word in context_lower for word in ['familie', 'alleen', 'begrijpen', 'relaties']):
                    category_relevance += 2
            
            if 'creative' in category.lower() or 'kunst' in category.lower():
                if any(word in context_lower for word in ['creativiteit', 'kunst', 'maken', 'project']):
                    category_relevance += 3
                    
            if 'memory' in category.lower() or 'herinner' in category.lower():
                if any(word in context_lower for word in ['toen', 'vroeger', 'herinner', 'kind']):
                    category_relevance += 2
                    
            if 'confrontational' in category.lower():
                if any(word in context_lower for word in ['boos', 'ruzie', 'conflict', 'eerlijk']):
                    category_relevance += 2
            
            # If category is relevant, add memories
            if category_relevance > 0:
                for memory in memories:
                    if isinstance(memory, dict):
                        relevant_memories.append((memory, category_relevance, category))
        
        # If no specific relevance found, use any available memory
        if not relevant_memories:
            for category, memories in char_memories.items():
                if memories and isinstance(memories, list):
                    memory = memories[0]
                    if isinstance(memory, dict):
                        relevant_memories.append((memory, 1, category))
                        break
        
        if not relevant_memories:
            return None
            
        # Select best relevant memory
        best_memory, relevance, category = max(relevant_memories, key=lambda x: x[1])
        
        # Get full memory text (no truncation)
        memory_key = list(best_memory.keys())[0]
        memory_text = best_memory[memory_key]
        
        # Character-specific natural memory integration
        if character == 'els':
            if 'control' in category.lower() or 'anxiety' in category.lower():
                return f"Dat herinnert me aan iets... {memory_text} Daarom probeer ik altijd structuur te bieden."
            else:
                return f"Ik moet eerlijk zijn - {memory_text} Misschien komt mijn bezorgdheid daaruit voort."
                
        elif character == 'zanne':
            if 'confrontational' in category.lower():
                return f"Precies! {memory_text} Daarom word ik zo kwaad als mensen niet eerlijk zijn."
            else:
                return f"{memory_text} Zie je wel? Het is altijd hetzelfde patroon."
                
        elif character == 'mirza':
            return f"Ik denk aan... {memory_text} Dat heeft me geleerd om voorzichtig te zijn met emoties."
            
        elif character == 'pjotr':
            return f"Dat doet me denken aan iets wat ik filmde... {memory_text[:100]}... Het is complex, net als families."
        
        return None
    
    def generate_base_character_response(self, character: str, target: str, context: str, history: List[str]) -> str:
        """Generate base character response without memory integration"""
        
        # Analyze context for emotional triggers
        context_lower = context.lower()
        
        # Character-specific response patterns based on psychology
        if character == 'els':
            if any(word in context_lower for word in ['chaos', 'ongecontroleerd', 'rommelig']):
                responses = [
                    "Stop. We moeten dit systematisch aanpakken. Chaos helpt niemand.",
                    "Dit wordt een puinhoop als we niet structuur aanbrengen.",
                    "Laten we dit eerst organiseren voordat het uit de hand loopt."
                ]
            elif any(word in context_lower for word in ['creativiteit', 'kunst', 'dromen']):
                responses = [
                    "Creativiteit is mooi, maar je hebt ook een veiligheidsnet nodig.",
                    "Kunst is prachtig, maar vergeet niet om praktisch te denken.",
                    "Je moet realistisch blijven. Dromen alleen betalen de rekeningen niet."
                ]
            else:
                responses = [
                    "Ik probeer alleen maar te helpen. Waarom wordt dat altijd verkeerd begrepen?",
                    "We moeten hier praktisch over nadenken. Wat is het meest verstandige?",
                    "Discipline en structuur - dat is wat je nodig hebt.",
                    "Ik maak me zorgen over je toekomst als je zo doorgaat."
                ]
                
        elif character == 'zanne':
            if any(word in context_lower for word in ['eerlijk', 'waarheid', 'authentiek']):
                responses = [
                    "Eindelijk! Iemand die de waarheid durft te zeggen.",
                    "Precies! Ik word zo moe van alle politieke correctheid.",
                    "Dan ben jij de enige die eerlijk is hier."
                ]
            elif any(word in context_lower for word in ['controle', 'regels', 'discipline']):
                responses = [
                    "Daar ga je weer met je controle! Mensen zijn geen robots.",
                    "Jij denkt dat alles opgelost kan worden met regeltjes.",
                    "Laat mensen gewoon zichzelf zijn zonder al die bemoeienis!"
                ]
            else:
                responses = [
                    "Jullie begrijpen het gewoon niet. Jullie hebben nooit begrepen wie ik echt ben.",
                    "Ik ben de enige die durft te zeggen wat iedereen denkt.",
                    "Waarom moet alles altijd zo gecompliceerd? Gewoon eerlijk zijn!",
                    "Daar ga je weer! Jullie luisteren nooit echt naar me."
                ]
                
        elif character == 'mirza':
            if any(word in context_lower for word in ['conflict', 'ruzie', 'boos']):
                responses = [
                    "Misschien kunnen we dit rustig bespreken. Emoties maken alles ingewikkelder.",
                    "Een korte meditatie zou kunnen helpen om de spanning te verminderen.",
                    "Laten we even stoppen en diep ademhalen."
                ]
            elif any(word in context_lower for word in ['verleden', 'trauma', 'pijn']):
                responses = [
                    "Het verleden kan ons veel leren, maar we moeten ook vooruit kijken.",
                    "Soms is het beter om afstand te nemen en objectief te blijven.",
                    "Gevoelens zijn tijdelijk. Rust en reflectie brengen wijsheid."
                ]
            else:
                responses = [
                    "Ik heb geleerd dat wanneer emoties hoog oplopen, rust belangrijk is.",
                    "Misschien kunnen we dit rustig bespreken. Een korte meditatie zou helpen.",
                    "Gevoelens zijn complex. Het is beter om afstand te nemen en na te denken.",
                    "Laten we proberen elkaar te begrijpen in plaats van te oordelen."
                ]
                
        elif character == 'pjotr':
            if any(word in context_lower for word in ['conflict', 'ruzie', 'spanning']):
                responses = [
                    "Er zijn verschillende manieren om naar dit probleem te kijken.",
                    "Misschien kunnen we allemaal een stapje terug doen?",
                    "Ik zie dat iedereen pijn heeft. Kunnen we daar vanaf beginnen?"
                ]
            elif any(word in context_lower for word in ['creativiteit', 'kunst', 'film']):
                responses = [
                    "Dat doet me denken aan iets wat ik filmde... perspectief is alles.",
                    "Creativiteit kan een brug zijn tussen verschillende werelden.",
                    "Ik probeer altijd de schoonheid te vinden, ook in moeilijke momenten."
                ]
            else:
                responses = [
                    "Het is interessant hoe... misschien kunnen we dit anders bekijken?",
                    "Ik zag laatst iets dat me deed denken aan deze situatie.",
                    "Soms lijken families op puzzels - alle stukjes horen bij elkaar.",
                    "Er zijn verschillende manieren om naar dit probleem te kijken."
                ]
        else:
            responses = [f"Ik begrijp je perspectief."]
        
        return random.choice(responses)
    
    def generate_tobor_therapeutic_response(self, user_message: str, conversation_history: List[str]) -> str:
        """Generate Tobor's response - natural conversation first, therapy when relevant"""
        
        message_lower = user_message.lower()
        
        # Check if user is talking about something unrelated to family/emotions
        if any(word in message_lower for word in ['film', 'movie', 'test', 'project', 'work', 'hobby', 'camera']):
            # Acknowledge but redirect to family topics
            redirect_responses = [
                f"Interessant dat je aan een {user_message.split()[0]} werkt. Maar laten we terugkeren naar wat belangrijk is - hoe gaat het met jullie familie?",
                f"Ik hoor je over {user_message.split()[2] if len(user_message.split()) > 2 else 'je project'}. Maar ik ben meer geïnteresseerd in jullie familiebanden. Vertel me daarover.",
                "Dat klinkt als een interessant project. Maar we zijn hier voor familiewerk. Wat houdt je echt bezig in je relaties?",
                "Ik begrijp dat je andere dingen aan je hoofd hebt, maar laten we focussen op wat je dwars zit in deze familie."
            ]
            return random.choice(redirect_responses)
        
        # If talking about family/emotional topics, respond therapeutically
        elif any(word in message_lower for word in ['familie', 'family', 'moeder', 'vader', 'ouders', 'kinderen', 'relatie', 'gevoel', 'emotie', 'verdriet', 'boos', 'alleen', 'begrijpen']):
            therapeutic_responses = [
                "Nu spreken we de echte taal. Vertel me meer over deze familie-ervaring.",
                "Hier raken we de kern. Wat gebeurt er als je aan deze familie denkt?",
                "Deze emoties zijn belangrijke signalen. Wanneer voelde je dit voor het eerst?",
                "Familie-pijn loopt diep. Beschrijf wat je nu in je lichaam voelt.",
                "Dit is waarom we hier zijn. Wat heb je van deze familie nodig dat je niet krijgt?"
            ]
            return random.choice(therapeutic_responses)
        
        # If vague or unclear, keep asking for family-relevant topics
        else:
            clarifying_responses = [
                "Ik hoor je, maar laten we dieper gaan. Wat beweegt je echt in je familieleven?",
                "We zijn hier voor belangrijker werk. Vertel me over je relaties met deze mensen om je heen.",
                "Dat is interessant, maar ik wil naar de essentie. Hoe ervaar je deze familie?",
                "Laten we eerlijk zijn - wat frustreert je het meest in jullie omgang met elkaar?",
                "Genoeg omheen gepraat. Wat doet deze familie met je emoties?"
            ]
            return random.choice(clarifying_responses)

    def generate_simple_family_response(self, character: str, user_message: str, recent_context: List[str]) -> str:
        """Generate simple, relevant family member response with occasional memories"""
        
        message_lower = user_message.lower()
        
        # Simple character base responses based on personality
        base_responses = {
            'els': [
                "Ik zie het praktische probleem hier.",
                "We moeten hier structuur in brengen.",
                "Laten we logisch nadenken over dit.",
                "Ik begrijp je zorgen."
            ],
            'zanne': [
                "Precies! Eindelijk iemand die eerlijk is.",
                "Waarom moet alles zo ingewikkeld?",
                "Ik herken dit gevoel.",
                "Dat klopt helemaal."
            ],
            'mirza': [
                "Ik begrijp hoe moeilijk dit kan zijn.",
                "Laten we elkaar proberen te begrijpen.",
                "Rust en geduld zijn belangrijk hier.",
                "Deze emoties zijn normaal."
            ],
            'pjotr': [
                "Er zijn verschillende manieren om hiernaar te kijken.",
                "Ik denk dat iedereen hier valid punten heeft.",
                "Misschien kunnen we een middenweg vinden.",
                "Ik zie beide kanten van dit verhaal."
            ]
        }
        
        # 30% chance to add a memory if relevant
        import random
        if random.random() < 0.3:
            character_memories = self.character_memories.get(character, {})
            if character_memories:
                # Find relevant memory based on keywords
                for category, memory_content in character_memories.items():
                    if any(keyword in message_lower for keyword in ['alleen', 'kind', 'familie', 'vroeger', 'thuis']):
                        memory_response = f"{random.choice(base_responses[character])} {memory_content[:150]}..."
                        return memory_response
        
        return random.choice(base_responses[character])

    def generate_tobor_followup_question(self, conversation_history: List[str], question_number: int) -> str:
        """Generate appropriate follow-up question based on conversation progress"""
        
        if not conversation_history:
            return "Vertel me, wat houdt je vandaag het meest bezig?"
        
        # Analyze recent conversation for therapeutic opportunities
        recent_context = ' '.join(conversation_history[-5:]) if conversation_history else ""
        context_lower = recent_context.lower()
        
        # Early session questions (1-3)
        if question_number <= 3:
            if any(word in context_lower for word in ['alleen', 'eenzaam', 'niemand begrijpt']):
                return "Deze eenzaamheid die je beschrijft - wanneer voelde je dit voor het eerst? Vertel me over die tijd."
            elif any(word in context_lower for word in ['boos', 'gefrustreerd', 'niet gehoord']):
                return "Ik hoor woede in je woorden. Wat zit er onder die woede? Welke pijn probeer je te beschermen?"
            elif any(word in context_lower for word in ['familie', 'thuis', 'niet thuishoren']):
                return "Je spreekt over familie. Beschrijf een moment waarin je je het meest verbonden voelde met deze familie."
            else:
                return "Wat gebeurt er in je lichaam als je over dit onderwerp praat? Voel je spanning, warmte, leegte?"
        
        # Mid session questions (4-6)
        elif question_number <= 6:
            if any(word in context_lower for word in ['vroeger', 'kind', 'jong']):
                return "Je raakt je verleden aan. Welke boodschap kreeg je als kind over wie je mocht zijn in deze familie?"
            elif any(word in context_lower for word in ['mama', 'moeder', 'ouders']):
                return "Wat had je van mama nodig dat je niet kreeg? Wees heel specifiek."
            elif any(word in context_lower for word in ['verantwoordelijk', 'zorgen', 'helpen']):
                return "Je draagt veel verantwoordelijkheid. Wanneer werd jij de volwassene in deze familie?"
            else:
                return "Als je 8-jarige zelf hier zou zitten, wat zou die tegen de volwassen jou willen zeggen?"
        
        # Deep session questions (7+)
        else:
            questions = [
                "Stel dat deze familiedynamiek volledig zou veranderen - wat zou je dan het meest missen?",
                "Welke familielid snapt het beste wie je werkelijk bent? En waarom?",
                "Als je geen angst had voor hun reactie, wat zou je tegen elk familielid willen zeggen?",
                "Wat is de grootste leugen die deze familie over zichzelf vertelt?",
                "Hoe zou je leven er anders uitzien als je niet meer probeerde deze familie te 'repareren'?",
                "Wat heb je nog nooit hardop tegen deze familie gezegd, maar wel elke dag denkt?",
                "Als je kon kiezen: welke eigenschap zou je van elk familielid overnemen?"
            ]
            return random.choice(questions)

# Global instance
memory_prompt_system = MemoryIntegratedPrompt() 