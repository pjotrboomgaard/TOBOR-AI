#!/usr/bin/env python3
"""
Simple Interactive Therapy Session Test
Tests the memory-integrated therapy system with simulated voice input
"""

import sys
import os
import time
import random

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.module_memory_prompt import memory_prompt_system

# Global session state
conversation_history = []
user_question_count = 0
max_user_questions = 5

def simulate_tobor_question():
    """Simulate Tobor asking a therapeutic question"""
    global user_question_count, conversation_history
    
    if user_question_count == 0:
        # Opening question
        question = "Goedemorgen, familie. Ik ben Tobor, jullie therapeutische begeleider. Welkom bij onze familiesessie. Vertel me, waar wil je vandaag over praten? Wat houdt je bezig?"
    else:
        # Follow-up questions
        followup_questions = [
            "Vertel me meer over wat je net zei. Hoe voelt dat precies?",
            "Wat gebeurt er in je lichaam als je daaraan denkt?",
            "Wanneer voelde je dit voor het eerst in je leven?",
            "Wat zou je tegen je 8-jarige zelf willen zeggen over dit onderwerp?",
            "Welke familielid begrijpt dit het beste? En wie begrijpt het niet?",
            "Als deze pijn een kleur had, welke zou het zijn? En waarom?",
            "Wat heb je nodig van deze familie dat je nog niet krijgt?"
        ]
        question = random.choice(followup_questions)
    
    print(f"\n🤖 TOBOR: {question}")
    conversation_history.append(f"tobor: {question}")
    user_question_count += 1
    
    return question

def simulate_user_response():
    """Simulate user voice input with realistic therapy responses"""
    responses = [
        "ik voel me vaak alleen in deze familie",
        "niemand begrijpt mijn creativiteit hier",
        "ik voel me verantwoordelijk voor ieders geluk",
        "soms denk ik dat ik niet thuishoor",
        "jullie proberen me altijd te veranderen",
        "ik mis de tijd toen we nog echt praatten",
        "waarom wordt mijn mening nooit gehoord",
        "ik ben moe van altijd sterk moeten zijn"
    ]
    
    user_input = random.choice(responses)
    print(f"\n👤 USER: {user_input}")
    conversation_history.append(f"user: {user_input}")
    
    return user_input

def generate_family_responses(user_context):
    """Generate family member responses with memory integration"""
    family_members = ['els', 'zanne', 'mirza', 'pjotr']
    responding_characters = random.sample(family_members, random.randint(2, 3))
    
    print(f"\n💬 FAMILY RESPONSES:")
    
    for char_name in responding_characters:
        # Generate memory-integrated response
        response = memory_prompt_system.generate_memory_integrated_response(
            char_name, 
            'user',  # target
            user_context,
            conversation_history
        )
        
        response = response.replace('\\n\\n', ' ').strip()
        print(f"   {char_name.upper()}: {response}")
        conversation_history.append(f"{char_name}: {response}")

def generate_tobor_therapeutic_response(user_message):
    """Generate Tobor's therapeutic analysis"""
    response = memory_prompt_system.generate_tobor_therapeutic_response(
        user_message, 
        conversation_history
    )
    
    print(f"\n🔍 TOBOR ANALYSIS: {response}")
    conversation_history.append(f"tobor: {response}")
    
    return response

def main():
    """Run interactive therapy session test"""
    print("=" * 60)
    print("🧠 INTERACTIVE MEMORY-INTEGRATED THERAPY SESSION TEST")
    print("=" * 60)
    
    print(f"\n📊 MEMORY SYSTEM STATUS:")
    for char in ['els', 'zanne', 'mirza', 'pjotr']:
        memories = memory_prompt_system.character_memories.get(char, {})
        print(f"   {char.upper()}: {len(memories)} memory categories loaded")
    
    print(f"\n🎭 STARTING THERAPY SESSION...")
    print(f"📝 Session will include {max_user_questions} user interactions")
    
    # Run therapy session simulation
    for session_turn in range(max_user_questions):
        print(f"\n" + "=" * 40)
        print(f"   SESSION TURN {session_turn + 1}")
        print(f"=" * 40)
        
        # 1. Tobor asks question
        tobor_question = simulate_tobor_question()
        time.sleep(1)
        
        # 2. User responds (simulated voice input)
        user_response = simulate_user_response()
        time.sleep(1)
        
        # 3. Tobor provides therapeutic analysis
        tobor_analysis = generate_tobor_therapeutic_response(user_response)
        time.sleep(1)
        
        # 4. Family members respond with memory integration
        generate_family_responses(user_response)
        time.sleep(2)
        
        print(f"\n⏸️  [Pause between turns...]")
        time.sleep(1)
    
    print(f"\n" + "=" * 60)
    print(f"✅ THERAPY SESSION COMPLETED!")
    print(f"📊 CONVERSATION SUMMARY:")
    print(f"   - Total turns: {len(conversation_history)}")
    print(f"   - User responses: {user_question_count}")
    print(f"   - Memory integrations triggered throughout session")
    print(f"=" * 60)

if __name__ == "__main__":
    main() 