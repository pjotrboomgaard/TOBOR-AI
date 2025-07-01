#!/usr/bin/env python3
"""
Simple LED Strip Test - Basic functionality to verify hardware
"""

import time
import random
from pi5neo import Pi5Neo

class ToborEmotionEngine:
    def __init__(self, spi_path="/dev/spidev10.0", num_leds=30, brightness=800):
        self.strip = Pi5Neo(spi_path, num_leds, brightness)
        self.num_leds = num_leds
        self.leds = list(range(num_leds))
        self.current_color = (10, 10, 10)

    def cleanup(self):
        """Turn off all LEDs"""
        for i in self.leds:
            self.strip.set_led_color(i, 0, 0, 0)
        self.strip.update_strip()

    def basic_test(self):
        """Basic LED test - light up all LEDs in different colors"""
        print("Testing basic LED functionality...")
        
        # Test 1: All red
        print("Setting all LEDs to RED...")
        for i in self.leds:
            self.strip.set_led_color(i, 255, 0, 0)
        self.strip.update_strip()
        time.sleep(2)
        
        # Test 2: All green
        print("Setting all LEDs to GREEN...")
        for i in self.leds:
            self.strip.set_led_color(i, 0, 255, 0)
        self.strip.update_strip()
        time.sleep(2)
        
        # Test 3: All blue
        print("Setting all LEDs to BLUE...")
        for i in self.leds:
            self.strip.set_led_color(i, 0, 0, 255)
        self.strip.update_strip()
        time.sleep(2)
        
        # Test 4: All white
        print("Setting all LEDs to WHITE...")
        for i in self.leds:
            self.strip.set_led_color(i, 255, 255, 255)
        self.strip.update_strip()
        time.sleep(2)
        
        # Test 5: Clear all
        print("Clearing all LEDs...")
        self.cleanup()
        time.sleep(1)

    def single_led_test(self):
        """Test individual LEDs one by one"""
        print("Testing individual LEDs...")
        
        for i in range(self.num_leds):
            print(f"Lighting LED {i+1}/{self.num_leds}")
            # Clear all first
            self.cleanup()
            # Light up current LED in red
            self.strip.set_led_color(i, 255, 0, 0)
            self.strip.update_strip()
            time.sleep(0.5)
        
        # Clear all at the end
        self.cleanup()

    def feel_blij(self):
        """Simple happy emotion - bright yellow"""
        print("Testing BLIJ emotion...")
        yellow = (255, 255, 0)  # Bright yellow
        
        for i in self.leds:
            self.strip.set_led_color(i, *yellow)
        self.strip.update_strip()
        time.sleep(3)
        
        self.cleanup()

if __name__ == "__main__":
    print("=== Simple LED Strip Test ===")
    
    try:
        engine = ToborEmotionEngine()
        print("LED strip initialized successfully!")
        
        # Run basic tests
        engine.basic_test()
        
        print("\nRunning single LED test...")
        engine.single_led_test()
        
        print("\nTesting emotion...")
        engine.feel_blij()
        
        print("\nTest completed!")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        try:
            engine.cleanup()
        except:
            pass 