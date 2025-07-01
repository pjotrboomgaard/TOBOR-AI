#!/usr/bin/env python3
"""
LED Emotion Test Script

Tests all available emotions on the MAX7219 LED Matrix using the tobor_emoties library.
This script cycles through all emotions with delays between them for testing.
"""

import time
import sys
import os

# Add the current directory to the path to import tobor_emoties
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from modules.tobor_emoties import speel_emotie, init_display, clear_display
    EMOTIONS_AVAILABLE = True
    print("✅ tobor_emoties library loaded successfully")
except ImportError as e:
    print(f"❌ Failed to import tobor_emoties: {e}")
    EMOTIONS_AVAILABLE = False

# List of all available emotions
EMOTIONS = [
    ("verrast", "Surprised - chaos to insight pattern"),
    ("weigering", "Refusal - alternating rejection patterns"),  
    ("verward", "Confused - ripples, rotation, question marks"),
    ("bang", "Scared - flashing, trembling, panic patterns"),
    ("slaperig", "Sleepy - slow pulsing patterns"),
    ("verdrietig", "Sad - falling tear drops"),
    ("geirriteerd", "Irritated - rapid scanning patterns"),
    ("boos", "Angry - explosive burst patterns"),
    ("verslaving", "Addiction - snake eating food"),
    ("genoeg", "Enough - breathing circle patterns"),
    ("blij", "Happy - expanding circles with sparkles"),
    ("verliefd", "In love - heart animations")
]

def test_single_emotion(emotion_name, description):
    """Test a single emotion"""
    print(f"\n🎭 Testing: {emotion_name} ({description})")
    print("   Starting in 2 seconds...")
    time.sleep(2)
    
    try:
        speel_emotie(emotion_name)
        print(f"   ✅ {emotion_name} completed successfully")
    except Exception as e:
        print(f"   ❌ Error with {emotion_name}: {e}")
    
    print("   Waiting 3 seconds before next emotion...")
    time.sleep(3)

def test_all_emotions():
    """Test all emotions in sequence"""
    if not EMOTIONS_AVAILABLE:
        print("❌ Cannot test emotions - tobor_emoties library not available")
        return
    
    print("=" * 60)
    print("🎭 LED MATRIX EMOTION TEST SCRIPT")
    print("=" * 60)
    print(f"Testing {len(EMOTIONS)} emotions on MAX7219 LED Matrix")
    print("Each emotion will play with 3-second breaks between them")
    print("Press Ctrl+C to stop at any time")
    print("=" * 60)
    
    try:
        # Initialize the display
        print("\n🔧 Initializing LED Matrix...")
        init_display()
        clear_display()
        print("   ✅ LED Matrix initialized")
        
        # Test each emotion
        for i, (emotion_name, description) in enumerate(EMOTIONS, 1):
            print(f"\n[{i}/{len(EMOTIONS)}]", end="")
            test_single_emotion(emotion_name, description)
        
        # Final cleanup
        print("\n🎉 All emotions tested successfully!")
        print("🔧 Clearing display...")
        clear_display()
        print("   ✅ Display cleared")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        print("🔧 Clearing display...")
        try:
            clear_display()
            print("   ✅ Display cleared")
        except:
            print("   ❌ Could not clear display")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        try:
            clear_display()
        except:
            pass

def test_specific_emotion(emotion_name):
    """Test a specific emotion by name"""
    if not EMOTIONS_AVAILABLE:
        print("❌ Cannot test emotions - tobor_emoties library not available")
        return
    
    # Find the emotion in our list
    emotion_found = False
    for name, description in EMOTIONS:
        if name.lower() == emotion_name.lower():
            emotion_found = True
            print(f"🎭 Testing specific emotion: {name}")
            print(f"   Description: {description}")
            
            try:
                init_display()
                clear_display()
                time.sleep(1)
                speel_emotie(name)
                print(f"   ✅ {name} completed successfully")
                time.sleep(2)
                clear_display()
            except Exception as e:
                print(f"   ❌ Error with {name}: {e}")
            break
    
    if not emotion_found:
        print(f"❌ Emotion '{emotion_name}' not found")
        print("Available emotions:")
        for name, description in EMOTIONS:
            print(f"   - {name}: {description}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Test specific emotion
        emotion_name = sys.argv[1]
        test_specific_emotion(emotion_name)
    else:
        # Test all emotions
        test_all_emotions()

if __name__ == "__main__":
    main() 