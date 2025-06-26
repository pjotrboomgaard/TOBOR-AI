#!/usr/bin/env python3
"""
Test script for LED Control Module

This script demonstrates the LED control functionality for TARS:
- Eye blinking while listening
- Mouth lights while talking
- Siren activation for intense emotions
- LED matrix emotion displays

Run this script to test the LED control system.
"""

import time
import sys
import os

# Add the modules directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.module_led_control import (
    test_led_controller,
    set_listening,
    set_talking,
    set_emotion,
    cleanup_leds,
    get_led_controller
)
from modules.module_messageQue import queue_message

def demo_led_functions():
    """Demonstrate all LED control functions"""
    print("\n=== TARS LED Control System Demo ===\n")
    
    controller = get_led_controller()
    
    # Test 1: Eye blinking (listening mode)
    print("Test 1: Eye blinking simulation (listening mode)")
    print("- Eyes should start blinking in a human-like pattern")
    set_listening(True)
    time.sleep(8)
    set_listening(False)
    print("- Eyes stopped blinking\n")
    
    # Test 2: Mouth lights (talking mode)
    print("Test 2: Mouth lights simulation (talking mode)")
    print("- Mouth lights should start rapid blinking")
    set_talking(True)
    time.sleep(5)
    set_talking(False)
    print("- Mouth lights stopped blinking\n")
    
    # Test 3: Combined listening and talking
    print("Test 3: Combined listening and talking")
    print("- Both eyes and mouth lights should be active")
    set_listening(True)
    time.sleep(2)
    set_talking(True)
    time.sleep(3)
    set_talking(False)
    time.sleep(2)
    set_listening(False)
    print("- All lights stopped\n")
    
    # Test 4: Emotion-based siren activation
    print("Test 4: Emotion-based responses")
    
    emotions_to_test = [
        ("happy", False),    # Should not trigger siren
        ("angry", True),     # Should trigger siren  
        ("scared", True),    # Should trigger siren
        ("calm", False),     # Should deactivate siren
    ]
    
    for emotion, should_trigger_siren in emotions_to_test:
        print(f"- Setting emotion: {emotion}")
        set_emotion(emotion, character_emotion=True)
        if should_trigger_siren:
            print(f"  → Siren should be {'ACTIVE' if should_trigger_siren else 'INACTIVE'}")
        time.sleep(3)
    
    print("\n- All emotion tests completed\n")
    
    # Test 5: LED Matrix emotions (if available)
    print("Test 5: LED Matrix emotion displays")
    matrix_emotions = ["blij", "verdrietig", "boos", "verrast", "verward"]
    
    for emotion in matrix_emotions:
        print(f"- Displaying emotion: {emotion}")
        set_emotion(emotion, character_emotion=True)
        time.sleep(2)
    
    print("- Matrix emotion tests completed\n")
    
    # Cleanup
    print("Test completed - cleaning up LED controller")
    cleanup_leds()
    print("Demo finished!\n")

def interactive_demo():
    """Interactive demo allowing user to control LEDs"""
    print("\n=== Interactive LED Control Demo ===")
    print("Commands:")
    print("  listen_on    - Start eye blinking")
    print("  listen_off   - Stop eye blinking") 
    print("  talk_on      - Start mouth lights")
    print("  talk_off     - Stop mouth lights")
    print("  emotion <name> - Set emotion (happy, angry, scared, etc.)")
    print("  test         - Run full test sequence")
    print("  quit         - Exit demo")
    print()
    
    try:
        while True:
            cmd = input("LED> ").strip().lower()
            
            if cmd == "quit":
                break
            elif cmd == "listen_on":
                set_listening(True)
                print("Eyes blinking started")
            elif cmd == "listen_off":
                set_listening(False)
                print("Eyes blinking stopped")
            elif cmd == "talk_on":
                set_talking(True)
                print("Mouth lights started")
            elif cmd == "talk_off":
                set_talking(False)
                print("Mouth lights stopped")
            elif cmd.startswith("emotion "):
                emotion = cmd.split(" ", 1)[1]
                set_emotion(emotion, character_emotion=True)
                print(f"Emotion set to: {emotion}")
            elif cmd == "test":
                demo_led_functions()
            elif cmd == "help":
                print("Available commands: listen_on, listen_off, talk_on, talk_off, emotion <name>, test, quit")
            else:
                print("Unknown command. Type 'help' for available commands.")
                
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        cleanup_leds()
        print("LED controller cleaned up")

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "interactive":
            interactive_demo()
        else:
            demo_led_functions()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
        cleanup_leds()
    except Exception as e:
        print(f"Error during demo: {e}")
        cleanup_leds() 