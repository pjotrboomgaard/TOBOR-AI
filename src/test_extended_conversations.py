#!/usr/bin/env python3
"""
test_extended_conversations.py

Extended test runner for family therapy conversations.
Runs for a fixed time period to test enhanced family dynamics.
"""

import time
import random
import threading
from datetime import datetime, timedelta
from modules.family_therapy_system import therapy_system

class ExtendedConversationTest:
    def __init__(self, duration_minutes=5):
        self.duration = timedelta(minutes=duration_minutes)
        self.start_time = datetime.now()
        self.end_time = self.start_time + self.duration
        self.running = True
        self.conversation_count = 0
        self.characters = ['tobor', 'zanne', 'els', 'mirza', 'pjotr']
        
    def run_test(self):
        """Run extended conversation test"""
        print(f"=== EXTENDED FAMILY THERAPY TEST ===")
        print(f"Start time: {self.start_time.strftime('%H:%M:%S')}")
        print(f"End time: {self.end_time.strftime('%H:%M:%S')}")
        print(f"Duration: {self.duration.total_seconds()/60:.1f} minutes")
        print("=" * 60)
        
        # Start conversation loop
        while self.running and datetime.now() < self.end_time:
            self.run_single_conversation()
            self.conversation_count += 1
            
            # Brief pause between conversations
            time.sleep(2)
            
            # Check if we should continue
            remaining = self.end_time - datetime.now()
            if remaining.total_seconds() <= 0:
                break
                
        self.print_summary()
        
    def run_single_conversation(self):
        """Run a single therapeutic conversation session"""
        print(f"\n{'='*20} CONVERSATION {self.conversation_count + 1} {'='*20}")
        print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        
        # Start with Tobor's therapeutic opening
        initiator = 'tobor'  # Always start with therapeutic framework
        opening = therapy_system.get_therapy_opening(initiator)
        
        print(f"\n{initiator.title()}: {opening}")
        
        # Initialize conversation state
        conversation_history = [f"{initiator}: {opening}"]
        active_characters = [initiator]
        turn_count = 1
        
        # Run conversation for 15-25 turns (authentic length)
        max_turns = random.randint(15, 25)
        
        while turn_count < max_turns and self.running:
            # Escalate tension as conversation progresses
            if turn_count % 3 == 0:
                therapy_system.escalate_tension()
            
            # Determine next speaker
            next_speaker = self.get_next_speaker(active_characters, turn_count)
            
            # Check for interruptions
            last_message = conversation_history[-1] if conversation_history else ""
            interruption = self.check_interruptions(last_message, next_speaker, active_characters)
            
            if interruption:
                print(f"{interruption['character'].title()}: {interruption['message']}")
                conversation_history.append(f"{interruption['character']}: {interruption['message']}")
                therapy_system.escalate_tension()
                time.sleep(0.5)  # Brief pause for dramatic effect
            
            # Generate response from next speaker
            context = " ".join(conversation_history[-3:])  # Last 3 exchanges for context
            target = self.get_target_character(next_speaker, active_characters)
            
            response = therapy_system.generate_character_response(
                next_speaker, target, context, turn_count
            )
            
            print(f"{next_speaker.title()}: {response}")
            conversation_history.append(f"{next_speaker}: {response}")
            
            # Add character to active list if not already there
            if next_speaker not in active_characters:
                active_characters.append(next_speaker)
                print(f"INFO: {next_speaker.title()} joins the conversation!")
            
            turn_count += 1
            
            # Variable delays for natural conversation flow
            delay = random.uniform(0.8, 2.5)  # Between 0.8-2.5 seconds
            time.sleep(delay)
            
            # Check if we should continue based on time
            if datetime.now() >= self.end_time:
                break
        
        # Conversation conclusion
        print(f"\nINFO: Conversation concluded after {turn_count} turns")
        print(f"Active characters: {', '.join(c.title() for c in active_characters)}")
        print(f"Emotional tension reached: {therapy_system.emotional_tension}/10")
        
        # Reset for next conversation
        therapy_system.emotional_tension = 3  # Reset but keep some base tension
        
    def get_next_speaker(self, active_characters, turn_count):
        """Determine who should speak next"""
        # Force characters to join early - more aggressive
        if turn_count < 8:
            if 'zanne' not in active_characters and turn_count >= 2:
                print(f"INFO: Zanne joins the conversation!")
                return 'zanne'
            elif 'els' not in active_characters and turn_count >= 4:
                print(f"INFO: Els joins the conversation!")
                return 'els'
            elif 'mirza' not in active_characters and turn_count >= 6:
                print(f"INFO: Mirza joins the conversation!")
                return 'mirza'
            elif 'pjotr' not in active_characters and turn_count >= 8:
                print(f"INFO: Pjotr joins the conversation!")
                return 'pjotr'
        
        # Later: focus on most reactive characters
        if turn_count > 8:
            weights = {
                'zanne': 0.35,  # High - most explosive
                'els': 0.25,    # Medium-high - corrective  
                'tobor': 0.2,   # Medium - therapeutic guidance
                'mirza': 0.15,  # Medium - solution-focused
                'pjotr': 0.05   # Low - mediator fatigue
            }
        else:
            weights = {
                'zanne': 0.3,
                'els': 0.25,
                'tobor': 0.25,
                'mirza': 0.15,
                'pjotr': 0.05
            }
        
        available = [c for c in active_characters if c in weights]
        if not available:
            return random.choice(active_characters)
            
        return random.choices(available, weights=[weights[c] for c in available])[0]
    
    def get_target_character(self, speaker, active_characters):
        """Get target character for response"""
        others = [c for c in active_characters if c != speaker]
        if not others:
            return 'familie'
        
        # Characters tend to address specific others based on relationships
        target_preferences = {
            'zanne': ['els', 'mirza', 'tobor', 'pjotr'],  # Addresses parents first
            'els': ['zanne', 'pjotr', 'mirza', 'tobor'],  # Addresses family
            'mirza': ['zanne', 'els', 'pjotr', 'tobor'],  # Addresses everyone
            'pjotr': ['zanne', 'els', 'mirza', 'tobor'],  # Diplomatic to all
            'tobor': ['zanne', 'els', 'mirza', 'pjotr']   # Therapeutic focus
        }
        
        preferences = target_preferences.get(speaker, others)
        available_targets = [t for t in preferences if t in others]
        
        return available_targets[0] if available_targets else random.choice(others)
    
    def check_interruptions(self, last_message, current_speaker, active_characters):
        """Check if anyone should interrupt based on triggers"""
        if not last_message:
            return None
            
        # Extract speaker and message from last_message
        if ': ' in last_message:
            last_speaker, message = last_message.split(': ', 1)
            last_speaker = last_speaker.lower()
        else:
            return None
        
        # Check each character for interruption potential
        potential_interrupters = [c for c in active_characters if c != last_speaker and c != current_speaker]
        
        for character in potential_interrupters:
            if therapy_system.should_interrupt(last_speaker, message, character):
                interruption_msg = therapy_system.generate_interruption(character, message)
                if interruption_msg:
                    return {
                        'character': character,
                        'message': interruption_msg
                    }
        
        return None
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print(f"TEST COMPLETED")
        print(f"Total runtime: {datetime.now() - self.start_time}")
        print(f"Conversations completed: {self.conversation_count}")
        print(f"Final emotional tension: {therapy_system.emotional_tension}/10")
        print(f"{'='*60}")

def main():
    """Run the extended conversation test"""
    print("Starting Extended Family Therapy Conversation Test...")
    print("This will run authentic family therapy sessions for 5 minutes.")
    print("Press Ctrl+C to stop early if needed.")
    
    try:
        test = ExtendedConversationTest(duration_minutes=5)
        test.run_test()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 