"""
module_led_control.py

LED Control module for TARS-AI application.

Handles different types of lighting:
- Eyes: Blinking while listening and not talking (human-like behavior)
- Mouth lights: Blinking while talking
- Siren: Activated for angry, scared, or wary emotions
- Emotion display: MAX7219 LED Matrix for emotional expressions

For now, it only prints terminal messages since no actual lights are connected yet.
"""

import time
import random
import threading
import asyncio
from typing import Optional, Dict, Any
from modules.module_messageQue import queue_message

# Import the emotion animation module
try:
    from modules.tobor_emoties import speel_emotie, init_display as init_emotion_display
    EMOTION_DISPLAY_AVAILABLE = True
except ImportError:
    EMOTION_DISPLAY_AVAILABLE = False
    queue_message("WARN: Emotion display module not available")

class LEDController:
    """Main LED controller for TARS lighting system"""
    
    def __init__(self):
        self.is_listening = False
        self.is_talking = False
        self.current_emotion = "neutral"
        self.siren_active = False
        self.eye_blink_thread = None
        self.mouth_blink_thread = None
        self.siren_thread = None
        self.stop_threads = False
        
        # Emotion mapping for siren activation
        self.siren_emotions = ["angry", "scared", "fear", "wary", "anxious", "boos", "bang"]
        
        # Initialize emotion display if available
        if EMOTION_DISPLAY_AVAILABLE:
            try:
                init_emotion_display()
                queue_message("INFO: LED Matrix emotion display initialized")
            except Exception as e:
                queue_message(f"WARN: Failed to initialize emotion display: {e}")
        
        queue_message("INFO: LED Controller initialized")
    
    def set_listening_state(self, listening: bool):
        """Set whether the system is listening (affects eye blinking)"""
        self.is_listening = listening
        if listening:
            self._start_eye_blinking()
            queue_message("LED: Eyes - Started blinking (listening mode)")
        else:
            self._stop_eye_blinking()
            queue_message("LED: Eyes - Stopped blinking")
    
    def set_talking_state(self, talking: bool):
        """Set whether the system is talking (affects mouth lights)"""
        self.is_talking = talking
        if talking:
            self._start_mouth_blinking()
            queue_message("LED: Mouth lights - Started blinking (talking mode)")
        else:
            self._stop_mouth_blinking()
            queue_message("LED: Mouth lights - Stopped blinking")
    
    def set_emotion(self, emotion: str, character_emotion: bool = False):
        """
        Set current emotion and trigger appropriate responses
        
        Args:
            emotion: The detected emotion
            character_emotion: If True, this is Tobor's emotion, if False it's user's emotion
        """
        self.current_emotion = emotion.lower()
        
        # Check if siren should be activated
        should_activate_siren = self.current_emotion in self.siren_emotions
        
        if should_activate_siren and not self.siren_active:
            self._activate_siren()
            emotion_source = "character Tobor" if character_emotion else "user"
            queue_message(f"LED: Siren activated due to {emotion_source} emotion: {emotion}")
        elif not should_activate_siren and self.siren_active:
            self._deactivate_siren()
            queue_message("LED: Siren deactivated")
        
        # Display emotion on LED matrix if available
        if EMOTION_DISPLAY_AVAILABLE and character_emotion:
            self._display_emotion(emotion)
    
    def _display_emotion(self, emotion: str):
        """Display emotion on LED matrix"""
        # Map common emotion names to our animation functions
        emotion_mapping = {
            "happy": "blij",
            "joy": "blij", 
            "sad": "verdrietig",
            "angry": "boos",
            "fear": "bang",
            "scared": "bang",
            "surprised": "verrast",
            "confused": "verward",
            "love": "verliefd",
            "tired": "slaperig",
            "annoyed": "geirriteerd",
            "irritated": "geirriteerd",
            "enough": "genoeg",
            "refusal": "weigering",
            "addiction": "verslaving"
        }
        
        animation_name = emotion_mapping.get(emotion.lower(), emotion.lower())
        
        try:
            threading.Thread(target=speel_emotie, args=(animation_name,), daemon=True).start()
            queue_message(f"LED: Displaying emotion animation: {animation_name}")
        except Exception as e:
            queue_message(f"WARN: Failed to display emotion {animation_name}: {e}")
    
    def _start_eye_blinking(self):
        """Start eye blinking pattern (human-like)"""
        if self.eye_blink_thread and self.eye_blink_thread.is_alive():
            return
        
        self.stop_threads = False
        self.eye_blink_thread = threading.Thread(target=self._eye_blink_pattern, daemon=True)
        self.eye_blink_thread.start()
    
    def _stop_eye_blinking(self):
        """Stop eye blinking"""
        self.stop_threads = True
        if self.eye_blink_thread:
            self.eye_blink_thread.join(timeout=1)
    
    def _eye_blink_pattern(self):
        """Human-like eye blinking pattern while listening"""
        while not self.stop_threads and self.is_listening:
            # Human blink pattern: 15-20 blinks per minute
            # That's roughly every 3-4 seconds
            blink_interval = random.uniform(2.5, 4.5)
            
            # Blink duration: 100-400ms
            blink_duration = random.uniform(0.1, 0.4)
            
            # Turn on eyes
            self._control_eyes(True)
            
            # Wait for blink interval
            time.sleep(blink_interval)
            
            if self.stop_threads or not self.is_listening:
                break
            
            # Blink (turn off briefly)
            self._control_eyes(False)
            time.sleep(blink_duration)
            
            # Occasional double blink (10% chance)
            if random.random() < 0.1:
                time.sleep(0.1)
                self._control_eyes(True)
                time.sleep(0.05)
                self._control_eyes(False)
                time.sleep(blink_duration)
    
    def _start_mouth_blinking(self):
        """Start mouth light blinking while talking"""
        if self.mouth_blink_thread and self.mouth_blink_thread.is_alive():
            return
        
        self.stop_threads = False
        self.mouth_blink_thread = threading.Thread(target=self._mouth_blink_pattern, daemon=True)
        self.mouth_blink_thread.start()
    
    def _stop_mouth_blinking(self):
        """Stop mouth light blinking"""
        self.stop_threads = True
        if self.mouth_blink_thread:
            self.mouth_blink_thread.join(timeout=1)
    
    def _mouth_blink_pattern(self):
        """Mouth light blinking pattern while talking"""
        while not self.stop_threads and self.is_talking:
            # Fast blinking to simulate speech
            blink_speed = random.uniform(0.05, 0.15)
            
            self._control_mouth_lights(True)
            time.sleep(blink_speed)
            
            if self.stop_threads or not self.is_talking:
                break
                
            self._control_mouth_lights(False) 
            time.sleep(blink_speed * 0.5)  # Shorter off period
    
    def _activate_siren(self):
        """Activate siren for intense emotions"""
        if self.siren_active:
            return
            
        self.siren_active = True
        self.siren_thread = threading.Thread(target=self._siren_pattern, daemon=True)
        self.siren_thread.start()
    
    def _deactivate_siren(self):
        """Deactivate siren"""
        self.siren_active = False
        if self.siren_thread:
            self.siren_thread.join(timeout=1)
        self._control_siren(False)
    
    def _siren_pattern(self):
        """Siren blinking pattern"""
        while self.siren_active:
            # Rapid alternating pattern
            self._control_siren(True)
            time.sleep(0.2)
            if not self.siren_active:
                break
            self._control_siren(False)
            time.sleep(0.2)
    
    def _control_eyes(self, state: bool):
        """Control eye lights (placeholder for actual hardware control)"""
        action = "ON" if state else "OFF"
        print(f"LED_CONTROL: Eyes {action}")
    
    def _control_mouth_lights(self, state: bool):
        """Control mouth lights (placeholder for actual hardware control)"""
        action = "ON" if state else "OFF"
        print(f"LED_CONTROL: Mouth lights {action}")
    
    def _control_siren(self, state: bool):
        """Control siren lights (placeholder for actual hardware control)"""
        action = "ON" if state else "OFF"
        print(f"LED_CONTROL: Siren {action}")
    
    def emergency_stop(self):
        """Emergency stop all LED functions"""
        self.stop_threads = True
        self.siren_active = False
        self.is_listening = False
        self.is_talking = False
        
        # Turn off all lights
        self._control_eyes(False)
        self._control_mouth_lights(False)
        self._control_siren(False)
        
        queue_message("LED: Emergency stop - all lights off")
    
    def cleanup(self):
        """Clean up all LED controller resources"""
        self.emergency_stop()
        
        # Wait for threads to finish
        if self.eye_blink_thread:
            self.eye_blink_thread.join(timeout=2)
        if self.mouth_blink_thread:
            self.mouth_blink_thread.join(timeout=2)
        if self.siren_thread:
            self.siren_thread.join(timeout=2)
        
        queue_message("LED: Controller cleaned up")

# Global LED controller instance
led_controller = None

def initialize_led_controller():
    """Initialize the global LED controller"""
    global led_controller
    if led_controller is None:
        led_controller = LEDController()
    return led_controller

def get_led_controller():
    """Get the global LED controller instance"""
    global led_controller
    if led_controller is None:
        led_controller = initialize_led_controller()
    return led_controller

# Convenience functions for easy integration
def set_listening(listening: bool):
    """Set listening state for eye blinking"""
    controller = get_led_controller()
    controller.set_listening_state(listening)

def set_talking(talking: bool):
    """Set talking state for mouth lights"""
    controller = get_led_controller()
    controller.set_talking_state(talking)

def set_emotion(emotion: str, character_emotion: bool = False):
    """Set emotion for appropriate LED responses"""
    controller = get_led_controller()
    controller.set_emotion(emotion, character_emotion)

def emergency_stop():
    """Emergency stop all LED functions"""
    controller = get_led_controller()
    controller.emergency_stop()

def cleanup_leds():
    """Clean up LED controller"""
    global led_controller
    if led_controller:
        led_controller.cleanup()
        led_controller = None

# Test function
def test_led_controller():
    """Test function to demonstrate LED controller functionality"""
    controller = get_led_controller()
    
    queue_message("LED: Starting test sequence...")
    
    # Test eye blinking
    queue_message("LED: Testing eye blinking (5 seconds)")
    controller.set_listening_state(True)
    time.sleep(5)
    controller.set_listening_state(False)
    
    # Test mouth lights
    queue_message("LED: Testing mouth lights (3 seconds)")
    controller.set_talking_state(True)
    time.sleep(3)
    controller.set_talking_state(False)
    
    # Test emotions and siren
    queue_message("LED: Testing siren with angry emotion")
    controller.set_emotion("angry", character_emotion=True)
    time.sleep(3)
    controller.set_emotion("happy", character_emotion=True)
    
    queue_message("LED: Test sequence completed")

if __name__ == "__main__":
    # Run test if module is executed directly
    test_led_controller()
    cleanup_leds() 