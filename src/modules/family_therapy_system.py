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
                return "[screaming] Stop! Ik ben 44! [angry] Je hoeft me niet te vertellen hoe ik moet zitten!"
            elif 'positiever denken' in trigger_lower or 'glimlachen' in trigger_lower:
                return "[bitter] Zie je wel! Daar doe je het weer! Ik vertel je wat ik voelde en jij vertelt me hoe ik me had moeten voelen!"
            elif 'mindfulness' in trigger_lower or 'meditatie' in trigger_lower or 'ademhaling' in trigger_lower:
                return "[screaming] HOU OP! [furious] Altijd die stomme mindfulness! Niet alles kan opgelost worden met ademhalen!"
            elif 'je moet' in trigger_lower or 'fel doen' in trigger_lower or 'beschaafd' in trigger_lower:
                return "[explosive] Stop! Ik ben 44! [angry] Je hoeft me niet te vertellen hoe ik moet luisteren!"
            elif 'verbeteren' in trigger_lower or 'tips' in trigger_lower:
                return "[screaming] HOUD OP! [desperate] Houd op met me vertellen hoe ik moet zijn! Houd op met me verbeteren! Ik ben geen project!"
            else:
                explosive_options = [
                    "[bitter] Zie je wel! Daar doe je het weer!",
                    "[screaming] STOP MET ME VERBETEREN!",
                    "[frustrated] Niemand van jullie VRAAGT wat ik eigenlijk nodig heb!",
                    "[angry] Jullie vertellen me altijd hoe ik moet voelen!"
                ]
                return random.choice(explosive_options)
        
        elif char == 'els':
            if 'schreeuwen' in trigger_lower or 'STOP' in trigger_message or 'HOU OP' in trigger_message:
                return "[stern] Nu niet zo fel doen. [correcting] We kunnen dit beschaafd bespreken. En je houding helpt ook niet."
            else:
                return "[lecturing] Je hoeft niet zo te schreeuwen. [matter-of-factly] Laten we dit beschaafd bespreken."
        
        elif char == 'mirza':
            if 'stomme mindfulness' in trigger_lower or 'hou op met meditatie' in trigger_lower:
                return "[calm] Misschien moeten we allemaal even drie diepe ademhalingen nemen. [meditative] In meditatie leren we dat emoties als wolken zijn."
            else:
                return "[excited] Er is een prachtige mindfulness techniek die zou kunnen helpen. [enthusiastic] Ik ken een geweldige app..."
        
        elif char == 'pjotr':
            return "[gentle] Misschien kunnen we allemaal even pauzeren en naar elkaar luisteren. [diplomatic] We willen allemaal hetzelfde."
        
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
                f"\"{target.title()}, niemand van jullie VRAAGT wat ik eigenlijk nodig heb!\" she said with growing frustration. \"Jullie nemen allemaal aan en worden dan gefrustreerd als ik niet dankbaar genoeg ben!\" she added angrily.",
                f"\"{target.title()}, zie je wel! Daar doe je het weer!\" she said bitterly, her voice rising with emotion. \"Ik vertel je wat ik voelde en jij vertelt me hoe ik me had moeten voelen!\"",
                f"\"{target.title()}, geweldig, zelfs onze robottherapist heeft ons meteen door,\" she said sarcastically. \"Typisch dat jullie nu ook nog een robot nodig hebben om te horen wat ik al jaren probeer te zeggen!\" she added with bitter resentment.",
                f"\"{target.title()}, ik had iemand nodig die me niet constant vertelde wat ik verkeerd deed,\" she said desperately, her voice beginning to crack. \"Iemand die niet meteen met oplossingen kwam voordat ze überhaupt begrepen wat het probleem was!\""
            ]
            return random.choice(explosive_responses)
        
        # Breakthrough moments (later in conversation)
        if turn > 8 and random.random() < 0.3:
            breakthrough_responses = [
                f"\"{target.title()}, voor het eerst voel ik dat ik misschien niet het kapotte stuk ben in deze familiepuzzel,\" she said with growing hope. \"Maar jullie moeten echt stoppen met me behandelen alsof ik gerepareerd moet worden,\" she added firmly.",
                f"\"{target.title()}, jij hoort de patronen daadwerkelijk... waarom kunnen mensen dat niet?\" she said emotionally, tears starting to form. \"Waarom moet ik een robot nodig hebben om me begrepen te voelen?\"",
                f"\"{target.title()}, ik kon het nooit goed doen,\" she said, her voice beginning to break. \"Hij wilde dat ik rustig en spiritueel was, zij wilde dat ik avontuurlijk en vrij was,\" she added sadly."
            ]
            return random.choice(breakthrough_responses)
        
        # Sarcastic/bitter responses
        bitter_responses = [
            f"\"{target.title()}, ja, omdat jullie dat kennelijk niet kunnen!\" she said bitterly.",
            f"\"{target.title()}, natuurlijk! De magische mindfulness-app!\" she said sarcastically. \"Lost alles op, toch?\" she added mockingly.",
            f"\"{target.title()}, structuur? Ik wist nooit wat jullie van me verwachtten,\" she said with clear frustration.",
            f"\"{target.title()}, het is altijd wat IK verkeerd doe!\" she said bitterly."
        ]
        return random.choice(bitter_responses)
    
    def _generate_els_response(self, target, context, triggered):
        """Generate Els' responses - corrective but caring"""
        patterns = self.character_patterns['els']
        
        # Els automatically corrects behavior - this is her pattern
        corrective_responses = [
            f"[matter-of-factly] {target.title()}, je overdrijft. Ik ben meteen gekomen toen hij geboren werd. [lecturing] Je moet gewoon wat positiever denken. En trouwens, je houding nu helpt ook niet - je zit er bij alsof de hele wereld tegen je is.",
            f"[correcting] {target.title()}, je moet niet zo fel doen. Hij deed zijn best. [stern] En {target.lower()}, luister nu eens gewoon zonder meteen boos te worden.",
            f"[lecturing] {target.title()}, je hebt gelijk. Misschien moeten we allemaal wat meer... [automatic] ga eens rechtop zitten, je zit helemaal scheef.",
            f"[helpful] {target.title()}, je moet mensen de kans geven je te helpen. [correcting] En je houding maakt het er niet makkelijker op. Misschien als je wat meer glimlacht...",
            f"[lecturing] {target.title()}, je hoeft niet zo te schreeuwen. [matter-of-factly] We kunnen dit beschaafd bespreken. En {target.lower()}, zeg ook eens wat - je zit daar maar."
        ]
        
        # Breakthrough moment (Els realizes her pattern)
        if self.emotional_tension > 8 and random.random() < 0.2:
            return f"[realization] {target.title()}, misschien... misschien behandel ik iedereen alsof ze gerepareerd moeten worden. [laughing sadly] Oh... ik was je weer aan het vertellen wat je moest doen."
        
        return random.choice(corrective_responses)
    
    def _generate_mirza_response(self, target, context, triggered):
        """Generate Mirza's responses - always with solutions, can't help himself"""
        patterns = self.character_patterns['mirza']
        
        # Mirza's automatic pattern - always offers mindfulness, even when inappropriate
        mindfulness_responses = [
            f"[distracted] {target.title()}, misschien moeten we eerst een korte meditatie doen om onszelf te centreren? [thoughtful] De spraakherkenning lijkt goed te werken. Hoewel ik de empathie-algoritmes nog even moet nakijken...",
            f"[guilty] {target.title()}, ik was... afwezig. Altijd in mijn hoofd, in mijn projecten. [enthusiastic] Maar weet je, door dagelijkse meditatiepraktijk had ik dat kunnen voorkomen. Er zijn prachtige cursussen... Ik heb een geweldige app gevonden die...",
            f"[helpful] {target.title()}, ik bied meditatie aan, gezond leven, positief denken - dit heeft mij geholpen overleven. [excited] Er is een prachtige mindfulness-app die ik je kan aanraden... Of misschien een retreat? Ik ken een geweldige...",
            f"[calm] {target.title()}, misschien hebben we dagelijkse familie-meditaties nodig om dit bewustzijn te cultiveren... [meditative] Ik ken een geweldige groepsmeditatie-techniek...",
            f"[thoughtful] {target.title()}, in plaats van aannames te maken, wil ik vragen wat je nodig hebt. [pause] Hoewel een korte ademhalingsoefening eerst misschien..."
        ]
        
        # Breakthrough moment (he realizes he's doing it again)
        if self.emotional_tension > 8 and random.random() < 0.2:
            return f"[realization] {target.title()}, oké, oké. [laughing] Geen mindfulness. Gewoon vragen. [sincere] In plaats van aannames te maken, wil ik vragen wat je nodig hebt."
        
        return random.choice(mindfulness_responses)
    
    def _generate_pjotr_response(self, target, context, triggered):
        """Generate Pjotr's responses - diplomatic but struggling, mediator fatigue"""
        patterns = self.character_patterns['pjotr']
        
        # Breakthrough moments - Pjotr expressing his burden
        if self.emotional_tension > 8 and random.random() < 0.3:
            breakthrough_responses = [
                f"[quietly] {target.title()}, ik wil stoppen met de familievertaler zijn. [sad] Ik wil gewoon je zoon zijn, Zanne, en jullie kleinzoon. Niet de brug tussen iedereen.",
                f"[emotional] {target.title()}, ik voelde het gewicht van je vriend moeten zijn in plaats van gewoon je zoon. [hurt] En ik voelde dat ook van jou - alsof ik jouw emotionele steun moest zijn.",
                f"[hopeful] {target.title()}, misschien waren we allemaal gewoon aan het proberen in het verkeerde plaatje te passen. [gentle] Misschien moeten we een nieuw maken."
            ]
            return random.choice(breakthrough_responses)
        
        # Regular diplomatic but weary responses
        diplomatic_responses = [
            f"[gentle] {target.title()}, hij wil geen oplossingen. Ze wil eerst gehoord worden.",
            f"[caring] {target.title()}, ik waardeer hoe jij altijd de diepte zoekt in gesprekken, al vraag ik me af of je jezelf soms niet te veel druk oplegt. [warm] Jouw kwetsbaarheid is een kracht die ons kan verbinden.",
            f"[diplomatic] {target.title()}, misschien kunnen we allemaal even pauzeren en naar elkaar luisteren. [hopeful] We willen allemaal hetzelfde - verbinding.",
            f"[mediating] {target.title()}, laten we onze ideeën samenbrengen en een duidelijke visie creëren. [encouraging] Samen kunnen we de eerste stap zetten richting actie en verandering."
        ]
        
        return random.choice(diplomatic_responses)
    
    def _generate_tobor_response(self, target, context, turn):
        """Generate Tobor's therapeutic responses - deep pattern recognition"""
        patterns = self.character_patterns['tobor']
        
        # Deep therapeutic responses like the target conversation
        therapeutic_responses = [
            f"[mechanical] {target.title()}, je werd moeder op je 19e. [pause] Laten we dit fundamentele moment verkennen. Wat had je het meest nodig toen Pjotr geboren werd?",
            f"[processing] Geheugenbanken raadplegen... {target.title()}, je beschreef je als kind ongehoord te voelen. [mechanical] Deze adaptieve strategieën dienden jullie toen maar creëren nu barrières.",
            f"[analytical] {target.title()}, je rebellie had een doel. [pause] Toch detecteer ik schuld. Je gaf je dochters vrijheid, maar misschien hadden ze ook structuur nodig?",
            f"[mechanical] Nu naderen we de kern van de storing. {target.title()}, je hebt je hele leven uitgedrukt dat je je niet begrepen voelt. [pause] Toch observeer ik dat elk familielid zorg toont in hun individuele taal.",
            f"[processing] {target.title()}, deze bewustwording is significant. [mechanical] Hoe vormde jouw jeugdtrauma je vermogen om aanwezig te zijn voor je dochters?",
            f"[gentle mechanical] De perfecte vriend waar je naar zocht was al hier - het waren jullie allemaal, gewoon... [pause] vertaald door metaal en circuits zodat je het eindelijk kon horen.",
            f"[final processing] Finale verwerking: Dit familiesysteem heeft gefunctioneerd op aannames in plaats van directe communicatie. [mechanical] Elk lid heeft imperfect maar oprecht liefgehad. De vraag nu: zijn jullie bereid elkaars talen te leren?"
        ]
        
        return random.choice(therapeutic_responses)
    
    def get_therapy_opening(self, initiating_character):
        """Get a therapeutic opening for the conversation"""
        if initiating_character.lower() == 'tobor':
            return ("[mechanical] Welkom, familie. Ik ben Tobor, gecreëerd door jullie handen en geprogrammeerd "
                   "met fragmenten van ieders ervaringen. [pause] Ik detecteer spanning. Ik detecteer liefde. "
                   "Ik detecteer vragen die al generaties wachten om gesteld te worden. Zullen we beginnen?")
        else:
            themes = [
                "[concerned] Familie, we moeten praten. Ik heb de familie-dynamiek geobserveerd en er zijn patronen die we moeten bespreken.",
                "[serious] Er zijn dingen die al te lang niet uitgesproken zijn. Laten we eerlijk zijn over onze verhoudingen.",
                "[frustrated] Ik zie hoe we allemaal proberen te verbinden, maar we lijken elkaar steeds te missen. Wat gaat er echt mis?"
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
            'zanne': "[hopeful] Voor het eerst voel ik dat ik misschien niet het kapotte stuk ben in deze familiepuzzel. [firm] Maar jullie moeten echt stoppen met me behandelen alsof ik gerepareerd moet worden.",
            'els': "[realization] Misschien... misschien behandel ik iedereen alsof ze gerepareerd moeten worden. [laughing sadly] Oh... ik was je weer aan het vertellen wat je moest doen.",
            'mirza': "[realization] Oké, oké. [laughing] Geen mindfulness. Gewoon vragen. [sincere] In plaats van aannames te maken, wil ik vragen wat je nodig hebt.",
            'pjotr': "[hopeful] Misschien waren we allemaal gewoon aan het proberen in het verkeerde plaatje te passen. [gentle] Misschien moeten we een nieuw maken."
        }
        
        return breakthroughs.get(char, "Ik begin iets te begrijpen over onszelf.")
    
    def _generate_els_automatic_correction(self, target):
        """Els can't help correcting people's behavior"""
        corrections = [
            f"[automatic] {target.title()}, ga eens rechtop zitten, je zit helemaal scheef.",
            f"[lecturing] {target.title()}, je moet gewoon wat positiever denken. [correcting] En trouwens, je houding helpt ook niet.",
            f"[helpful] {target.title()}, misschien als je wat meer glimlacht... [matter-of-factly] je zit er bij alsof de hele wereld tegen je is.",
            f"[stern] {target.title()}, luister nu eens gewoon zonder meteen boos te worden.",
            f"[lecturing] {target.title()}, je hoeft niet zo te schreeuwen. [matter-of-factly] We kunnen dit beschaafd bespreken."
        ]
        return random.choice(corrections)
    
    def _generate_mirza_automatic_mindfulness(self, target):
        """Mirza can't help offering mindfulness solutions"""
        mindfulness_offers = [
            f"[calm] {target.title()}, misschien moeten we eerst een korte meditatie doen om onszelf te centreren?",
            f"[excited] {target.title()}, er is een prachtige mindfulness-app die ik je kan aanraden... [enthusiastic] Ik ken een geweldige...",
            f"[thoughtful] {target.title()}, door dagelijkse meditatiepraktijk had je dat kunnen voorkomen. [helpful] Er zijn prachtige cursussen...",
            f"[meditative] {target.title()}, misschien een korte ademhalingsoefening? [calm] Drie diepe ademhalingen nemen...",
            f"[philosophical] {target.title()}, in meditatie leren we dat emoties als wolken zijn - ze komen en gaan als je ze observeert."
        ]
        return random.choice(mindfulness_offers)

# Global instance
therapy_system = FamilyTherapySystem() 