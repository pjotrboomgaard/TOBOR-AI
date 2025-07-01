#!/usr/bin/env python3
"""
Test script for Memory-Integrated Conversation System
Tests the new memory-integrated prompting for realistic family therapy
"""

import threading
import time
import json
import sys
import os
from datetime import datetime

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.module_config import load_config
from modules.module_character import CharacterManager
from modules.module_memory import MemoryManager
from modules.module_memory_prompt import memory_prompt_system

def print_status(message, char="SYSTEM"):
    """Print timestamped status message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{char}] {message}")

def test_memory_loading():
    """Test memory loading from character psychology profiles"""
    print_status("Testing memory system loading...")
    
    print_status(f"Character memories loaded: {list(memory_prompt_system.character_memories.keys())}")
    
    for char, memories in memory_prompt_system.character_memories.items():
        print_status(f"{char.title()}: {len(memories)} memory categories")
        for category in list(memories.keys())[:3]:  # Show first 3 categories
            print_status(f"  - {category}: {len(memories[category])} memories", char.upper())

def test_memory_integration():
    """Test memory integration in responses"""
    print_status("Testing memory integration...")
    
    test_contexts = [
        "ik voel me alleen in deze familie",
        "niemand begrijpt mijn creativiteit", 
        "ik weet niet wat ik wil met mijn carrière",
        "jullie waren er nooit voor me",
        "ik probeer alleen maar te helpen"
    ]
    
    characters = ['els', 'zanne', 'mirza', 'pjotr']
    
    for context in test_contexts:
        print_status(f"Context: {context}")
        
        for char in characters:
            response = memory_prompt_system.generate_memory_integrated_response(
                char, 'user', context, []
            )
            print_status(f"{response}", char.upper())
        
        print_status("---")

def test_conversation_flow():
    """Test complete conversation flow"""
    print_status("Testing conversation flow...")
    
    conversation_history = []
    
    # Tobor opening
    tobor_opening = "Goedemorgen, familie. Welkom bij onze familiesessie. Vertel me, waar wil je vandaag over praten?"
    conversation_history.append(f"tobor: {tobor_opening}")
    print_status(tobor_opening, "TOBOR")
    
    # User input
    user_message = "ik wil praten over familie relaties en hoe niemand me begrijpt"
    conversation_history.append(f"user: {user_message}")
    print_status(f"USER: {user_message}")
    
    # Tobor response
    tobor_response = memory_prompt_system.generate_tobor_therapeutic_response(
        user_message, conversation_history
    )
    conversation_history.append(f"tobor: {tobor_response}")
    print_status(tobor_response, "TOBOR")
    
    # Family responses
    family_members = ['els', 'zanne', 'mirza', 'pjotr']
    
    for char in family_members:
        response = memory_prompt_system.generate_memory_integrated_response(
            char, 'user', user_message, conversation_history
        )
        conversation_history.append(f"{char}: {response}")
        print_status(response, char.upper())
        
        # Small delay to simulate natural conversation
        time.sleep(0.5)

def interactive_memory_test():
    """Interactive test where you can input messages"""
    print_status("=== Interactive Memory Conversation Test ===")
    print("Type messages to test the memory system. Type 'quit' to exit.")
    
    conversation_history = []
    
    # Tobor opening
    tobor_opening = "Goedemorgen, familie. Welkom bij onze familiesessie. Vertel me, waar wil je vandaag over praten?"
    conversation_history.append(f"tobor: {tobor_opening}")
    print_status(tobor_opening, "TOBOR")
    
    try:
        while True:
            user_input = input("\n[USER]> ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'stop']:
                break
                
            if not user_input:
                continue
            
            # Add user input to history
            conversation_history.append(f"user: {user_input}")
            print_status(f"USER: {user_input}")
            
            # Tobor response
            tobor_response = memory_prompt_system.generate_tobor_therapeutic_response(
                user_input, conversation_history
            )
            conversation_history.append(f"tobor: {tobor_response}")
            print_status(tobor_response, "TOBOR")
            
            # Random family member responds
            import random
            responding_char = random.choice(['els', 'zanne', 'mirza', 'pjotr'])
            
            family_response = memory_prompt_system.generate_memory_integrated_response(
                responding_char, 'user', user_input, conversation_history
            )
            conversation_history.append(f"{responding_char}: {family_response}")
            print_status(family_response, responding_char.upper())
            
    except KeyboardInterrupt:
        print_status("Test interrupted by user")

def extended_conversation_test():
    """Extended conversation test with multiple exchanges"""
    print_status("=== Extended Memory Conversation Test ===")
    
    conversation_history = []
    
    # Conversation simulation
    exchanges = [
        ("ik voel me alleen in deze familie", "USER"),
        ("niemand begrijpt echt wie ik ben", "USER"), 
        ("jullie proberen me altijd te veranderen", "USER"),
        ("ik wil gewoon geaccepteerd worden", "USER")
    ]
    
    # Tobor opening
    tobor_opening = "Goedemorgen, familie. Welkom bij onze familiesessie. Vertel me, waar wil je vandaag over praten?"
    conversation_history.append(f"tobor: {tobor_opening}")
    print_status(tobor_opening, "TOBOR")
    
    for user_message, speaker in exchanges:
        print_status("---")
        
        # User message
        conversation_history.append(f"user: {user_message}")
        print_status(f"USER: {user_message}")
        
        # Tobor therapeutic response
        tobor_response = memory_prompt_system.generate_tobor_therapeutic_response(
            user_message, conversation_history
        )
        conversation_history.append(f"tobor: {tobor_response}")
        print_status(tobor_response, "TOBOR")
        
        # 2-3 family member responses
        import random
        responding_chars = random.sample(['els', 'zanne', 'mirza', 'pjotr'], random.randint(2, 3))
        
        for char in responding_chars:
            response = memory_prompt_system.generate_memory_integrated_response(
                char, 'user', user_message, conversation_history
            )
            conversation_history.append(f"{char}: {response}")
            print_status(response, char.upper())
            
            time.sleep(0.3)  # Natural flow
        
        time.sleep(1)  # Pause between exchanges

def main():
    """Main test function"""
    print_status("TARS-AI Memory-Integrated Conversation Test")
    print_status("=========================================")
    
    try:
        # Load configuration
        CONFIG = load_config()
        if not CONFIG:
            print_status("ERROR: Failed to load configuration")
            return
        
        # Initialize managers (needed for character loading)
        character_manager = CharacterManager(CONFIG)
        memory_manager = MemoryManager(CONFIG)
        
        print_status("Managers initialized for memory testing")
        
        # Test menu
        print("\\nTest Options:")
        print("1. Test memory loading")
        print("2. Test memory integration")
        print("3. Test conversation flow")
        print("4. Interactive test")
        print("5. Extended conversation test")
        
        choice = input("\\nSelect test (1-5): ").strip()
        
        if choice == '1':
            test_memory_loading()
        elif choice == '2':
            test_memory_integration()
        elif choice == '3':
            test_conversation_flow()
        elif choice == '4':
            interactive_memory_test()
        elif choice == '5':
            extended_conversation_test()
        else:
            print_status("Running all tests...")
            test_memory_loading()
            time.sleep(2)
            test_memory_integration()
            time.sleep(2)
            test_conversation_flow()
        
        print_status("Testing completed!")
        
    except Exception as e:
        print_status(f"ERROR: {e}")

if __name__ == "__main__":
    main() 