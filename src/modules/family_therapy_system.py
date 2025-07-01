"""
family_therapy_system.py

Specialized system for authentic family therapy conversations.
Creates dynamic, emotional conversations with character-specific patterns and triggers.
"""

import random
from modules.module_messageQue import queue_message

class FamilyTherapySystem:
    def __init__(self):
        self.conversation_depth = 0
        self.emotional_tension = 0
        self.current_theme = None
        self.character_triggers = self._init_character_triggers()
        self.therapy_themes = self._init_therapy_themes()
        self.character_patterns = self._init_character_patterns()
        
    def _init_character_triggers(self):
        """Define what triggers explosive reactions from each character"""
        return {
            'zanne': [
                # Immediate explosive triggers
                'rechtop zitten', 'ga eens rechtop', 'posture', 'scheef', 'ingedoken',
                'positiever denken', 'wat meer glimlachen', 'je houding', 'attitude', 
                'je moet', 'je hoeft niet', 'je overdrijft', 'fel doen', 'zo schreeuwen',
                'mindfulness', 'meditatie', 'ademhaling', 'drie diepe', 'oplossing',
                'luister nu eens', 'zonder boos te worden', 'beschaafd bespreken',
                'ga eens', 'moet niet zo', 'verbeteren', 'beter', 'tips'
            ],
            'els': [
                # Els gets triggered when people are upset, disrespectful, or chaotic
                'schreeuwen', 'STOP', 'HOU OP', 'boos', 'fel', 'ruzie', 'chaos',
                'negatief', 'niet luisteren', 'respect'
            ],
            'mirza': [
                # Mirza gets triggered when mindfulness is rejected
                'stomme mindfulness', 'hou op met meditatie', 'geen oplossingen',
                'altijd die', 'stomme', 'VADER', 'niet alles kan opgelost'
            ],
            'pjotr': [
                # Pjotr gets overwhelmed by family fighting
                'ruzie', 'fighting', 'conflict', 'schreeuwen', 'stressed', 
                'familievertaler', 'mediator'
            ]
        }
    
    def _init_therapy_themes(self):
        """Therapeutic conversation themes"""
        return {
            'young_parenthood': [
                'Zanne werd moeder op haar 19e',
                'Wat had je het meest nodig toen Pjotr geboren werd?',
                'Jong ouderschap en familie steun',
                'De impact op familie-dynamiek'
            ],
            'communication_patterns': [
                'Niemand VRAAGT wat ik eigenlijk nodig heb',
                'Jullie vertellen me altijd hoe ik moet voelen',
                'Elke familie-lid toont liefde in hun eigen taal',
                'Waarom voelen jullie je niet begrepen?'
            ],
            'intergenerational_trauma': [
                'Welke patronen heb je doorgegeven?',
                'Hoe vormde jouw jeugd je ouderschap?',
                'Wat wilde je anders doen dan je ouders?'
            ]
        }
    
    def _init_character_patterns(self):
        """Character-specific speech patterns and behaviors"""
        return {
            'zanne': {
                'explosive_responses': [
                    'Zie je wel! Daar doe je het weer!',
                    'MOEDER! Stop! Ik ben 44!',
                    'Stop met me verbeteren!',
                    'Hoe durf je dat te insinueren!',
                    'Niemand van jullie VRAAGT wat ik nodig heb!'
                ],
                'vulnerable_responses': [
                    'Voor het eerst voel ik dat ik misschien niet het kapotte stuk ben',
                    'Ik kon het nooit goed doen',
                    'Soms voelde ik...',
                    'Het is waar'
                ],
                'triggers': ['being corrected', 'mindfulness', 'posture', 'attitude']
            },
            'els': {
                'corrective_responses': [
                    'Je moet niet zo fel doen',
                    'Ga eens rechtop zitten',
                    'Je overdrijft',
                    'Misschien moeten we wat positiever denken',
                    'Je houding helpt ook niet'
                ],
                'caring_responses': [
                    'Ik maak me zorgen om je',
                    'Je moet goed voor jezelf zorgen',
                    'Misschien kunnen we dit beschaafd bespreken'
                ],
                'automatic_corrections': ['posture', 'attitude', 'fighting']
            },
            'mirza': {
                'solution_responses': [
                    'Er is een prachtige mindfulness techniek',
                    'Misschien een korte ademhalingsoefening',
                    'In meditatie leren we dat emoties als wolken zijn',
                    'Ik ken een geweldige app',
                    'Dagelijkse familie-meditaties zouden kunnen helpen'
                ],
                'excited_responses': [
                    'Dat zou echt kunnen helpen!',
                    'Ik heb een geweldige cursus gevonden!',
                    'Er zijn prachtige technieken voor dit!'
                ],
                'cant_help_himself': True
            },
            'pjotr': {
                'diplomatic_responses': [
                    'Misschien kunnen we allemaal even pauzeren',
                    'Laten we proberen elkaar te begrijpen',
                    'Ik denk dat we allemaal hetzelfde willen',
                    'We willen allemaal verbinding'
                ],
                'gentle_observations': [
                    'Soms zie ik hoe jij...',
                    'Er is iets moois in de manier waarop jij...',
                    'Ik waardeer hoe jij...'
                ],
                'mediator_fatigue': [
                    'Ik wil stoppen met de familievertaler zijn',
                    'Ik wil gewoon je zoon zijn, niet de brug tussen iedereen'
                ]
            },
            'tobor': {
                'therapeutic_observations': [
                    'Ik detecteer een patroon',
                    'Geheugenbanken raadplegen',
                    'Familie systeem update',
                    'Deze adaptieve strategieën dienden jullie toen maar creëren nu barrières'
                ],
                'pattern_calling': [
                    'Dit familiesysteem heeft gefunctioneerd op aannames',
                    'Elk lid heeft imperfect maar oprecht liefgehad',
                    'De perfecte vriend waar je naar zocht was al hier'
                ]
            }
        }
    
    def should_interrupt(self, speaker, message, potential_interrupter):
        """Check if character should interrupt based on triggers"""
        triggers = self.character_triggers.get(potential_interrupter.lower(), [])
        message_lower = message.lower()
        
        # Check if message contains trigger words
        for trigger in triggers:
            if trigger in message_lower:
                # MUCH higher interruption chances for authenticity
                if potential_interrupter.lower() == 'zanne':
                    return random.random() < 0.9  # Very high chance - she's explosive
                elif potential_interrupter.lower() == 'els':
                    return random.random() < 0.7  # High chance to correct
                elif potential_interrupter.lower() == 'mirza':
                    return random.random() < 0.6  # Can't help himself with solutions
                else:
                    return random.random() < 0.3  # Pjotr tries to mediate
        
        return False
    
    def generate_interruption(self, character, trigger_message):
        """Generate character-specific interruption"""
        char = character.lower()
        patterns = self.character_patterns.get(char, {})
        trigger_lower = trigger_message.lower()
        
        if char == 'zanne':
            # Very specific explosive interruptions based on exact triggers
            if 'rechtop zitten' in trigger_lower or 'ga eens rechtop' in trigger_lower or 'scheef' in trigger_lower:
                return "Stop! Ik ben 44! Je hoeft me niet te vertellen hoe ik moet zitten!"
            elif 'positiever denken' in trigger_lower or 'glimlachen' in trigger_lower:
                return "Zie je wel! Daar doe je het weer! Ik vertel je wat ik voelde en jij vertelt me hoe ik me had moeten voelen!"
            elif 'mindfulness' in trigger_lower or 'meditatie' in trigger_lower or 'ademhaling' in trigger_lower:
                return "HOU OP! Altijd die stomme mindfulness! Niet alles kan opgelost worden met ademhalen!"
            elif 'je moet' in trigger_lower or 'fel doen' in trigger_lower or 'beschaafd' in trigger_lower:
                return "Stop! Ik ben 44! Je hoeft me niet te vertellen hoe ik moet luisteren!"
            elif 'verbeteren' in trigger_lower or 'tips' in trigger_lower:
                return "HOUD OP! Houd op met me vertellen hoe ik moet zijn! Houd op met me verbeteren! Ik ben geen project!"
            else:
                explosive_options = [
                    "Zie je wel! Daar doe je het weer!",
                    "STOP MET ME VERBETEREN!",
                    "Niemand van jullie VRAAGT wat ik eigenlijk nodig heb!",
                    "Jullie vertellen me altijd hoe ik moet voelen!"
                ]
                return random.choice(explosive_options)
        
        elif char == 'els':
            if 'schreeuwen' in trigger_lower or 'STOP' in trigger_message or 'HOU OP' in trigger_message:
                return "Nu niet zo fel doen. We kunnen dit beschaafd bespreken. En je houding helpt ook niet."
            else:
                return "Je hoeft niet zo te schreeuwen. Laten we dit beschaafd bespreken."
        
        elif char == 'mirza':
            if 'stomme mindfulness' in trigger_lower or 'hou op met meditatie' in trigger_lower:
                return "Misschien moeten we allemaal even drie diepe ademhalingen nemen. In meditatie leren we dat emoties als wolken zijn."
            else:
                return "Er is een prachtige mindfulness techniek die zou kunnen helpen. Ik ken een geweldige app..."
        
        elif char == 'pjotr':
            return "Misschien kunnen we allemaal even pauzeren en naar elkaar luisteren. We willen allemaal hetzelfde."
        
        return None
    
    def generate_character_response(self, character, target_character, conversation_context, turn_number):
        """Generate authentic character response based on patterns"""
        char = character.lower()
        patterns = self.character_patterns.get(char, {})
        
        # Check emotional state based on conversation
        is_triggered = self._is_character_triggered(character, conversation_context)
        
        # Characters have automatic behavioral patterns that they can't help
        if char == 'els' and random.random() < 0.4:  # Els automatically corrects posture/behavior
            return self._generate_els_automatic_correction(target_character)
        elif char == 'mirza' and random.random() < 0.5:  # Mirza can't help offering mindfulness
            return self._generate_mirza_automatic_mindfulness(target_character)
        
        if char == 'zanne':
            return self._generate_zanne_response(target_character, conversation_context, is_triggered, turn_number)
        elif char == 'els':
            return self._generate_els_response(target_character, conversation_context, is_triggered)
        elif char == 'mirza':
            return self._generate_mirza_response(target_character, conversation_context, is_triggered)
        elif char == 'pjotr':
            return self._generate_pjotr_response(target_character, conversation_context, is_triggered)
        elif char == 'tobor':
            return self._generate_tobor_response(target_character, conversation_context, turn_number)
        
        return f"{target_character.title()}, ik hoor wat je zegt."
    
    def _is_character_triggered(self, character, context):
        """Check if character is in triggered emotional state"""
        triggers = self.character_triggers.get(character.lower(), [])
        context_lower = context.lower()
        
        for trigger in triggers:
            if trigger in context_lower:
                return True
        return False
    
    def _generate_zanne_response(self, target, context, triggered, turn):
        """Generate Zanne's responses - defensive/explosive or vulnerable"""
        patterns = self.character_patterns['zanne']
        
        # High emotional tension responses
        if self.emotional_tension > 6 or triggered:
            explosive_responses = [
                "Niemand van jullie VRAAGT wat ik eigenlijk nodig heb! Jullie nemen allemaal aan en worden dan gefrustreerd als ik niet dankbaar genoeg ben!",
                "Zie je wel! Daar doe je het weer! Ik vertel je wat ik voelde en jij vertelt me hoe ik me had moeten voelen!",
                "Geweldig, zelfs onze robottherapist heeft ons meteen door. Typisch dat jullie nu ook nog een robot nodig hebben om te horen wat ik al jaren probeer te zeggen!",
                "Ik had iemand nodig die me niet constant vertelde wat ik verkeerd deed. Iemand die niet meteen met oplossingen kwam voordat ze überhaupt begrepen wat het probleem was!"
            ]
            return random.choice(explosive_responses)
        
        # Breakthrough moments (later in conversation)
        if turn > 8 and random.random() < 0.3:
            breakthrough_responses = [
                "Voor het eerst voel ik dat ik misschien niet het kapotte stuk ben in deze familiepuzzel. Maar jullie moeten echt stoppen met me behandelen alsof ik gerepareerd moet worden.",
                "Jij hoort de patronen daadwerkelijk... waarom kunnen mensen dat niet? Waarom moet ik een robot nodig hebben om me begrepen te voelen?",
                "Ik kon het nooit goed doen. Hij wilde dat ik rustig en spiritueel was, zij wilde dat ik avontuurlijk en vrij was."
            ]
            return random.choice(breakthrough_responses)
        
        # Sarcastic/bitter emotional responses
        bitter_responses = [
            "Ja, omdat jullie dat kennelijk niet kunnen!",
            "Natuurlijk! De magische mindfulness-app! Lost alles op, toch?",
            "Structuur? Ik wist nooit wat jullie van me verwachtten.",
            "Het is altijd wat IK verkeerd doe!",
            "Ik voel me zo moe van altijd uitleggen waarom ik pijn heb.",
            "Soms denk ik dat jullie me gewoon anders willen dan ik ben."
        ]
        return random.choice(bitter_responses)
    
    def _generate_els_response(self, target, context, triggered):
        """Generate Els' responses - corrective but caring"""
        patterns = self.character_patterns['els']
        
        # Els automatically corrects behavior - this is her pattern
        corrective_responses = [
            "Je overdrijft. Ik ben meteen gekomen toen hij geboren werd. Je moet gewoon wat positiever denken. En trouwens, je houding nu helpt ook niet.",
            "Je moet niet zo fel doen. Hij deed zijn best. Luister nu eens gewoon zonder meteen boos te worden.",
            "Je hebt gelijk. Misschien moeten we allemaal wat meer... ga eens rechtop zitten, je zit helemaal scheef.",
            "Je moet mensen de kans geven je te helpen. En je houding maakt het er niet makkelijker op. Misschien als je wat meer glimlacht...",
            "Je hoeft niet zo te schreeuwen. We kunnen dit beschaafd bespreken.",
            "Ik maak me zorgen om je. Je lijkt zo gestrest de laatste tijd.",
            "Ik probeer alleen maar te helpen. Waarom wordt dat altijd verkeerd begrepen?"
        ]
        
        # Breakthrough moment (Els realizes her pattern)
        if self.emotional_tension > 8 and random.random() < 0.2:
            return "Misschien... misschien behandel ik iedereen alsof ze gerepareerd moeten worden. Oh... ik was je weer aan het vertellen wat je moest doen."
        
        return random.choice(corrective_responses)
    
    def _generate_mirza_response(self, target, context, triggered):
        """Generate Mirza's responses - always with solutions, can't help himself"""
        patterns = self.character_patterns['mirza']
        
        # Mirza's automatic pattern - always offers mindfulness, even when inappropriate
        mindfulness_responses = [
            "Misschien moeten we eerst een korte meditatie doen om onszelf te centreren? De spraakherkenning lijkt goed te werken. Hoewel ik de empathie-algoritmes nog even moet nakijken...",
            "Ik was... afwezig. Altijd in mijn hoofd, in mijn projecten. Maar weet je, door dagelijkse meditatiepraktijk had ik dat kunnen voorkomen.",
            "Ik bied meditatie aan, gezond leven, positief denken - dit heeft mij geholpen overleven. Er is een prachtige mindfulness-app die ik je kan aanraden...",
            "Misschien hebben we dagelijkse familie-meditaties nodig om dit bewustzijn te cultiveren...",
            "In plaats van aannames te maken, wil ik vragen wat je nodig hebt. Hoewel een korte ademhalingsoefening eerst misschien...",
            "Ik voel me schuldig dat ik altijd met oplossingen kom. Maar dit helpt mij echt.",
            "Ik weet dat jullie denken dat ik altijd afwezig ben in mijn projecten."
        ]
        
        # Breakthrough moment (he realizes he's doing it again)
        if self.emotional_tension > 8 and random.random() < 0.2:
            return "Oké, oké. Geen mindfulness. Gewoon vragen. In plaats van aannames te maken, wil ik vragen wat je nodig hebt."
        
        return random.choice(mindfulness_responses)
    
    def _generate_pjotr_response(self, target, context, triggered):
        """Generate Pjotr's responses - diplomatic but struggling, mediator fatigue"""
        patterns = self.character_patterns['pjotr']
        
        # Breakthrough moments - Pjotr expressing his burden
        if self.emotional_tension > 8 and random.random() < 0.3:
            breakthrough_responses = [
                "Ik wil stoppen met de familievertaler zijn. Ik wil gewoon je zoon zijn, en jullie kleinzoon. Niet de brug tussen iedereen.",
                "Ik voelde het gewicht van je vriend moeten zijn in plaats van gewoon je zoon. En ik voelde dat ook - alsof ik jouw emotionele steun moest zijn.",
                "Misschien waren we allemaal gewoon aan het proberen in het verkeerde plaatje te passen. Misschien moeten we een nieuw maken."
            ]
            return random.choice(breakthrough_responses)
        
        # Regular emotional sharing - removed therapeutic advice
        emotional_responses = [
            "Hij wil geen oplossingen. Ze wil eerst gehoord worden.",
            "Ik voel me soms moe van altijd de bemiddelaar te zijn.",
            "Soms wil ik gewoon jullie zoon zijn, niet de familietherapeut.",
            "Ik zie hoe we allemaal proberen te verbinden, maar het lukt niet altijd.",
            "Het is moeilijk om iedereen tevreden te houden.",
            "Ik voel de spanning tussen jullie en dat maakt me verdrietig.",
            "Soms denk ik dat jullie van me verwachten dat ik alles oplos."
        ]
        
        return random.choice(emotional_responses)
    
    def _generate_tobor_response(self, target, context, turn):
        """Generate Tobor's therapeutic responses - deep pattern recognition and leading conversation"""
        patterns = self.character_patterns['tobor']
        
        # Tobor as therapist - directive, uses names, leads conversation
        if turn < 3:  # Early conversation - establish leadership
            leadership_responses = [
                f"{target.title()}, laten we dit patroon onderzoeken dat ik detecteer. Vertel me over je vroegste herinnering waarin je je ongehoord voelde in deze familie.",
                f"{target.title()}, ik observeer defensieve reacties. Wat gebeurt er als je je verkeerd begrepen voelt? Loop me door die emotionele sequentie.",
                f"{target.title()}, jouw communicatiestijl suggereert aanpassing vanuit de kindertijd. Beschrijf de familie-dynamiek toen je opgroeide.",
                f"{target.title()}, ik detecteer pijn onder de woede. Wat had je nodig dat je niet ontving? Wees specifiek."
            ]
            return random.choice(leadership_responses)
        elif turn > 8:  # Deep therapy - breakthrough facilitation
            breakthrough_responses = [
                f"{target.title()}, we naderen een kritiek begrip. Elk familielid spreekt hun liefdetaal, maar jullie horen verschillende talen. Ben je klaar om vertaling te leren?",
                f"{target.title()}, ik detecteer een patroon over drie generaties. De methoden die je bekritiseerde bij je ouders - zie je ze in je eigen ouderschap? Hoe doorbreken we deze cyclus?",
                f"{target.title()}, het familiesysteem toont imperfecte maar authentieke liefde-pogingen. De vraag blijft: gaan jullie elkaars talen leren, of blijven communiceren in code?"
            ]
            return random.choice(breakthrough_responses)
        else:  # Mid-conversation - probing and directing
            therapeutic_responses = [
                f"{target.title()}, ik detecteer emotionele escalatie. Laten we pauzeren en de trigger identificeren. Wat gebeurde er intern?",
                f"{target.title()}, je noemde je ongesterkt voelen. Definieer steun. Hoe zou het eruit zien van elk familielid?",
                f"{target.title()}, jouw reactiepatroon suggereert historische trauma-activering. Wanneer leerde je deze defensieve strategie?",
                f"{target.title()}, ik observeer contradictie tussen je behoeften en reactieve responses. Help me deze discrepantie begrijpen.",
                f"{target.title()}, familie-systeemanalyse toont elk lid probeert verbinding via hun primaire taal. Wat is jouw primaire taal, en heb je het anderen geleerd?"
            ]
            return random.choice(therapeutic_responses)
    
    def get_therapy_opening(self, initiating_character):
        """Get a therapeutic opening for the conversation"""
        if initiating_character.lower() == 'tobor':
            return ("Welkom, familie. Ik ben Tobor, jullie therapeutische constructie. Ik heb "
                   "familie-interactiepatronen geanalyseerd en detecteer significante communicatiebarrières. We moeten "
                   "deze systematische disfuncties aanpakken. Zanne, laten we met jou beginnen - beschrijf je huidige emotionele staat.")
        else:
            themes = [
                "Familie, we moeten praten. Ik heb de familie-dynamiek geobserveerd en er zijn patronen die we moeten bespreken.",
                "Er zijn dingen die al te lang niet uitgesproken zijn. Laten we eerlijk zijn over onze verhoudingen.",
                "Ik zie hoe we allemaal proberen te verbinden, maar we lijken elkaar steeds te missen. Wat gaat er echt mis?"
            ]
            return random.choice(themes)
    
    def escalate_tension(self):
        """Increase emotional tension for more authentic conflict"""
        self.emotional_tension = min(10, self.emotional_tension + 1)
        queue_message(f"DEBUG: Emotional tension increased to {self.emotional_tension}")
    
    def should_have_breakthrough(self, turn_number):
        """Determine if characters should have breakthrough moment"""
        return turn_number > 8 and random.random() < 0.3
    
    def generate_breakthrough_response(self, character):
        """Generate breakthrough/realization response"""
        char = character.lower()
        
        breakthroughs = {
            'zanne': "Voor het eerst voel ik dat ik misschien niet het kapotte stuk ben in deze familiepuzzel. Maar jullie moeten echt stoppen met me behandelen alsof ik gerepareerd moet worden.",
            'els': "Misschien... misschien behandel ik iedereen alsof ze gerepareerd moeten worden. Oh... ik was je weer aan het vertellen wat je moest doen.",
            'mirza': "Oké, oké. Geen mindfulness. Gewoon vragen. In plaats van aannames te maken, wil ik vragen wat je nodig hebt.",
            'pjotr': "Misschien waren we allemaal gewoon aan het proberen in het verkeerde plaatje te passen. Misschien moeten we een nieuw maken."
        }
        
        return breakthroughs.get(char, "Ik begin iets te begrijpen over onszelf.")
    
    def _generate_els_automatic_correction(self, target):
        """Els can't help correcting people's behavior"""
        corrections = [
            "Ga eens rechtop zitten, je zit helemaal scheef.",
            "Je moet gewoon wat positiever denken. En trouwens, je houding helpt ook niet.",
            "Misschien als je wat meer glimlacht... je zit er bij alsof de hele wereld tegen je is.",
            "Luister nu eens gewoon zonder meteen boos te worden.",
            "Je hoeft niet zo te schreeuwen. We kunnen dit beschaafd bespreken.",
            "Ik zie dat je moe bent, maar je houding maakt het er niet makkelijker op.",
            "Ik probeer alleen maar te helpen. Waarom voel je je altijd aangevallen?"
        ]
        return random.choice(corrections)
    
    def _generate_mirza_automatic_mindfulness(self, target):
        """Mirza can't help offering mindfulness solutions"""
        mindfulness_offers = [
            "Misschien moeten we eerst een korte meditatie doen om onszelf te centreren?",
            "Er is een prachtige mindfulness-app die ik je kan aanraden... Ik ken een geweldige...",
            "Door dagelijkse meditatiepraktijk had je dat kunnen voorkomen. Er zijn prachtige cursussen...",
            "Misschien een korte ademhalingsoefening? Drie diepe ademhalingen nemen...",
            "In meditatie leren we dat emoties als wolken zijn - ze komen en gaan als je ze observeert.",
            "Ik weet dat jullie denken dat ik altijd met oplossingen kom, maar dit helpt mij echt.",
            "Ik voel me schuldig dat ik niet anders kan dan mindfulness voorstellen."
        ]
        return random.choice(mindfulness_offers)

# Global instance
therapy_system = FamilyTherapySystem() 