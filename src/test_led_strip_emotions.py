#!/usr/bin/env python3
"""
Test script for TARS LED Strip Emotion Engine
Tests all emotion animations on the LED strip using Pi5Neo library
"""

import time
import random
import sys
import signal
from pi5neo import Pi5Neo

class ToborEmotionEngine:
    def __init__(self, spi_path="/dev/spidev10.0", num_leds=30, brightness=800):
        try:
            self.strip = Pi5Neo(spi_path, num_leds, brightness)
            self.num_leds = num_leds
            self.leds = list(range(num_leds))
            self.current_color = (10, 10, 10)
            print(f"LED Strip initialized: {num_leds} LEDs on {spi_path}")
        except Exception as e:
            print(f"ERROR: Failed to initialize LED strip: {e}")
            raise

    def cleanup(self):
        """Turn off all LEDs and cleanup"""
        try:
            print("Cleaning up LED strip...")
            for i in self.leds:
                self.strip.set_led_color(i, 0, 0, 0)
            self.strip.update_strip()
            print("LED strip cleaned up successfully")
        except Exception as e:
            print(f"ERROR during cleanup: {e}")

    def transition_to(self, new_color, steps=30, delay=0.02):
        print(f"Overgang van kleur: {self.current_color} naar {new_color}")
        start_r, start_g, start_b = self.current_color
        end_r, end_g, end_b = new_color
        for i in range(steps + 1):
            factor = i / steps
            r = max(1, int(start_r + (end_r - start_r) * factor))
            g = max(1, int(start_g + (end_g - start_g) * factor))
            b = max(1, int(start_b + (end_b - start_b) * factor))
            for j in self.leds:
                self.strip.set_led_color(j, r, g, b)
            self.strip.update_strip()
            time.sleep(delay)
        self.current_color = new_color

    def pulse(self, color, speed=0.01, steps=20):
        for i in range(steps):
            scale = i / steps
            r = max(1, int(color[0] * scale))
            g = max(1, int(color[1] * scale))
            b = max(1, int(color[2] * scale))
            for j in self.leds:
                self.strip.set_led_color(j, r, g, b)
            self.strip.update_strip()
            time.sleep(speed)
        for i in range(steps, -1, -1):
            scale = i / steps
            r = max(1, int(color[0] * scale))
            g = max(1, int(color[1] * scale))
            b = max(1, int(color[2] * scale))
            for j in self.leds:
                self.strip.set_led_color(j, r, g, b)
            self.strip.update_strip()
            time.sleep(speed)

    def sparkle_effect(self, base_color, sparkle_color=(255,192,203), sparkles=5, duration=1.5):
        start = time.time()
        while time.time() - start < duration:
            for i in self.leds:
                self.strip.set_led_color(i, *base_color)
            for _ in range(sparkles):
                idx = random.randint(0, self.num_leds - 1)
                self.strip.set_led_color(idx, *sparkle_color)
            self.strip.update_strip()
            time.sleep(0.1)

    def feel(self, emotion):
        print(f"Tobor voelt zich: {emotion} (begin)")
        method = getattr(self, f"feel_{emotion}", None)
        if method:
            method()
            print(f"Tobor voelt zich: {emotion} (overgang)")
        else:
            print(f"Emotie '{emotion}' niet gedefinieerd.")

    # Emotie-animaties hieronder:

    def feel_verliefd(self):
        pink1 = (180, 0, 180)  # puur magenta
        pink2 = (255, 0, 255)  # feller magenta
        pink_base = (100, 0, 100)  # donkerder magenta basis
        for wave in range(3):
            for i in range(self.num_leds):
                for j in range(self.num_leds):
                    if (i + wave) % self.num_leds == j:
                        self.strip.set_led_color(j, *pink2)
                    elif (i + wave - 1) % self.num_leds == j or (i + wave + 1) % self.num_leds == j:
                        self.strip.set_led_color(j, *pink1)
                    else:
                        self.strip.set_led_color(j, *pink_base)
                self.strip.update_strip()
                time.sleep(0.05)
        self.transition_to(pink2)
        self.sparkle_effect(pink2, sparkle_color=(255, 150, 255))
        self.pulse(pink1)

    def feel_blij(self):
        yellow = (255, 255, 100)  # heldere zonnige geel
        sparkle = (255, 255, 180)  # lichte fonkels
        for _ in range(15):
            for i in self.leds:
                self.strip.set_led_color(i, *yellow)
            for _ in range(4):
                idx = random.randint(0, self.num_leds - 1)
                self.strip.set_led_color(idx, *sparkle)
            self.strip.update_strip()
            time.sleep(0.1)
        self.transition_to(yellow)
        self.pulse(yellow, speed=0.02)

    def feel_bang(self):
        violet = (75, 0, 130)
        self.sparkle_effect(violet, sparkle_color=(255, 255, 255))
        self.transition_to(violet)
        self.pulse(violet)

    def feel_opgewonden(self):
        orange = (255, 80, 0)
        self.sparkle_effect(orange, sparkle_color=(255, 160, 60))
        self.transition_to(orange)
        self.pulse(orange)

    def feel_verward(self):
        for _ in range(15):
            for j in self.leds:
                color = (random.randint(30,255), random.randint(30,255), random.randint(30,255))
                self.strip.set_led_color(j, *color)
            self.strip.update_strip()
            time.sleep(0.1)
        self.transition_to((128, 0, 128), steps=5, delay=0.01)

    def feel_verdrietig(self):
        blue = (0, 0, 200)
        self.sparkle_effect(blue, sparkle_color=(0, 120, 255))
        self.transition_to(blue)
        self.pulse(blue, speed=0.02)

    def feel_kalm(self):
        mint = (100, 255, 180)
        self.sparkle_effect(mint, sparkle_color=(200, 255, 230))
        self.transition_to(mint)
        self.pulse(mint, speed=0.03)

    def feel_nieuwsgierig(self):
        gold = (255, 215, 0)
        self.sparkle_effect(gold, sparkle_color=(255, 255, 100))
        self.transition_to(gold)
        self.pulse(gold)

    def feel_geconcentreerd(self):
        cyan = (0, 255, 255)
        self.sparkle_effect(cyan, sparkle_color=(180, 255, 255))
        self.transition_to(cyan)
        self.pulse(cyan, speed=0.015)

    def feel_speels(self):
        rainbow = [(255,0,0), (255,127,0), (255,255,0), (0,255,0), (0,0,255), (75,0,130), (148,0,211)]
        for offset in range(20):
            for i in range(self.num_leds):
                color = rainbow[(i + offset) % len(rainbow)]
                self.strip.set_led_color(i, *color)
            self.strip.update_strip()
            time.sleep(0.1)

    def feel_eenzaam(self):
        darkblue = (0, 0, 100)
        self.sparkle_effect(darkblue, sparkle_color=(0, 50, 255))
        self.transition_to(darkblue)
        self.pulse(darkblue, speed=0.05)

    def feel_twijfel(self):
        yellow = (255, 255, 0)
        blue = (0, 0, 255)
        self.sparkle_effect((128, 128, 128), sparkle_color=(255, 255, 0))
        for _ in range(3):
            self.transition_to(yellow)
            self.transition_to(blue)
        self.transition_to((128, 128, 0), steps=5, delay=0.01)

    def feel_uitgeput(self):
        base = (40, 40, 60)
        flicker = (80, 80, 120)
        for _ in range(5):  # minder herhalingen
            for i in self.leds:
                color = base if random.random() > 0.3 else flicker
                self.strip.set_led_color(i, *color)
            self.strip.update_strip()
            time.sleep(0.1)
        for led in self.leds:
            for brightness in reversed(range(10)):  # minder stappen
                color = tuple(max(1, int(c * (brightness / 10))) for c in base)
                self.strip.set_led_color(led, *color)
                self.strip.update_strip()
                time.sleep(0.03)
        self.transition_to((0, 0, 0), steps=30, delay=0.03)  # snellere fade
        self.current_color = (10, 10, 10)

    def feel_boos(self):
        red = (255, 0, 0)
        for _ in range(6):
            for j in self.leds:
                self.strip.set_led_color(j, *(255, 0, 0))
            self.strip.update_strip()
            time.sleep(0.05)
            for j in self.leds:
                self.strip.set_led_color(j, *(180, 0, 0))
            self.strip.update_strip()
            time.sleep(0.05)
            for j in self.leds:
                self.strip.set_led_color(j, *(255, 255, 255))
            self.strip.update_strip()
            time.sleep(0.05)
        self.transition_to(red)
        self.pulse(red)


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\n\nInterrupt ontvangen! LED strip wordt uitgeschakeld...')
    if 'engine' in globals():
        engine.cleanup()
    sys.exit(0)


def test_single_emotion(engine, emotion):
    """Test a single emotion"""
    print(f"\n=== Testing emotion: {emotion} ===")
    try:
        engine.feel(emotion)
        print(f"✓ Emotion '{emotion}' completed successfully")
        time.sleep(2)  # Pause between emotions
    except Exception as e:
        print(f"✗ Error testing emotion '{emotion}': {e}")


def test_all_emotions(engine):
    """Test all available emotions sequentially"""
    emotions = [
        "verliefd", "blij", "bang", "opgewonden", "verward", "verdrietig",
        "kalm", "nieuwsgierig", "geconcentreerd", "speels", "eenzaam",
        "twijfel", "uitgeput", "boos"
    ]
    
    print(f"\n=== Testing all {len(emotions)} emotions ===")
    print("Press Ctrl+C to stop at any time")
    
    for i, emotion in enumerate(emotions, 1):
        print(f"\n[{i}/{len(emotions)}] Testing: {emotion}")
        try:
            engine.feel(emotion)
            print(f"✓ Completed: {emotion}")
            time.sleep(2)  # Pause between emotions
        except KeyboardInterrupt:
            print(f"\nTest interrupted at emotion: {emotion}")
            break
        except Exception as e:
            print(f"✗ Error with emotion '{emotion}': {e}")
            continue


def main():
    global engine
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=== TARS LED Strip Emotion Test ===")
    print("Initializing LED strip...")
    
    try:
        # Initialize the emotion engine
        engine = ToborEmotionEngine()
        
        # Available emotions
        emotions = [
            "verliefd", "blij", "bang", "opgewonden", "verward", "verdrietig",
            "kalm", "nieuwsgierig", "geconcentreerd", "speels", "eenzaam",
            "twijfel", "uitgeput", "boos"
        ]
        
        # Check command line arguments
        if len(sys.argv) > 1:
            emotion = sys.argv[1].lower()
            if emotion in emotions:
                test_single_emotion(engine, emotion)
            elif emotion == "all":
                test_all_emotions(engine)
            else:
                print(f"Unknown emotion: {emotion}")
                print(f"Available emotions: {', '.join(emotions)}")
                print("Or use 'all' to test all emotions")
        else:
            # Interactive mode
            print("\nAvailable emotions:")
            for i, emotion in enumerate(emotions, 1):
                print(f"  {i:2d}. {emotion}")
            print(f"  {len(emotions)+1:2d}. all (test all emotions)")
            
            while True:
                try:
                    choice = input(f"\nSelect emotion (1-{len(emotions)+1}) or 'q' to quit: ").strip()
                    
                    if choice.lower() == 'q':
                        break
                    elif choice == str(len(emotions)+1) or choice.lower() == 'all':
                        test_all_emotions(engine)
                    elif choice.isdigit() and 1 <= int(choice) <= len(emotions):
                        emotion = emotions[int(choice)-1]
                        test_single_emotion(engine, emotion)
                    else:
                        print("Invalid choice. Please try again.")
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error: {e}")
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        return 1
    
    finally:
        # Cleanup
        if 'engine' in locals():
            engine.cleanup()
        print("Test completed!")
    
    return 0


if __name__ == "__main__":
    exit(main()) 