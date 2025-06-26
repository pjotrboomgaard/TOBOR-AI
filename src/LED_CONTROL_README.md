# TARS LED Control System

This document describes the LED control system implemented for TARS-AI, providing lighting effects for different states and emotions.

## Overview

The LED control system consists of three main components:

1. **Eye Lights** - Blink in a human-like pattern while listening
2. **Mouth Lights** - Rapid blinking while talking/speaking
3. **Siren Lights** - Activated during intense emotions (angry, scared, fearful)
4. **LED Matrix Display** - Shows emotional animations using MAX7219 controller

## Files Created

### `modules/module_led_control.py`
Main LED controller module that handles all lighting functions:
- Eye blinking patterns (human-like timing)
- Mouth light control during speech
- Siren activation for intense emotions
- Integration with emotion detection
- Thread management for concurrent light patterns

### `modules/tobor_emoties.py`
LED Matrix emotion animation module with Dutch emotion animations:
- `verliefd` (in love) - Heart animation
- `blij` (happy) - Expanding circles with sparkles
- `verdrietig` (sad) - Falling tear drops
- `boos` (angry) - Explosive burst pattern
- `bang` (scared/afraid) - Chaotic flashing with stabilizing
- `verward` (confused) - Rotating patterns with question marks
- `slaperig` (sleepy) - Slow pulsing pattern
- And many more emotional expressions

### `test_led_control.py`
Test script to demonstrate LED functionality:
- Automated demo of all LED functions
- Interactive mode for manual control
- Emotion testing capabilities

## Integration Points

The LED control system is integrated into existing TARS modules:

### Speech-to-Text (STT) Integration
- **File**: `module_stt.py`
- **Function**: Eyes start blinking when listening for wake words or user input
- **Trigger**: `set_listening(True)` when actively listening
- **Stop**: `set_listening(False)` when speech detected or timeout

### Text-to-Speech (TTS) Integration  
- **File**: `module_tts.py`
- **Function**: Mouth lights blink rapidly during speech output
- **Trigger**: `set_talking(True)` when TTS audio starts
- **Stop**: `set_talking(False)` when TTS audio ends

### Emotion Detection Integration
- **File**: `module_llm.py`
- **Function**: LED matrix displays character emotions, siren for intense emotions
- **Trigger**: `set_emotion(emotion, character_emotion=True)` after emotion detection
- **Emotions**: Maps detected emotions to appropriate LED matrix animations

## LED Control Functions

### Basic Control
```python
from modules.module_led_control import set_listening, set_talking, set_emotion

# Eye blinking control
set_listening(True)   # Start human-like eye blinking
set_listening(False)  # Stop eye blinking

# Mouth light control  
set_talking(True)     # Start rapid mouth light blinking
set_talking(False)    # Stop mouth light blinking

# Emotion control
set_emotion("happy", character_emotion=True)   # Display happy emotion + no siren
set_emotion("angry", character_emotion=True)   # Display angry emotion + activate siren
```

### Advanced Control
```python
from modules.module_led_control import get_led_controller, cleanup_leds

# Get controller instance for advanced control
controller = get_led_controller()

# Emergency stop all LEDs
controller.emergency_stop()

# Clean up when shutting down
cleanup_leds()
```

## Hardware Placeholder

Currently, all LED control functions print terminal messages since no actual hardware is connected:

```
LED_CONTROL: Eyes ON
LED_CONTROL: Eyes OFF
LED_CONTROL: Mouth lights ON
LED_CONTROL: Mouth lights OFF  
LED_CONTROL: Siren ON
LED_CONTROL: Siren OFF
```

When hardware is connected, these placeholder functions can be replaced with actual GPIO/relay control code.

## Emotion Mapping

The system maps common English emotions to Dutch LED matrix animations:

| English | Dutch | Animation Description |
|---------|-------|----------------------|
| happy/joy | blij | Expanding circles with sparkles |
| sad | verdrietig | Falling tear drops |
| angry | boos | Explosive burst pattern |
| fear/scared | bang | Chaotic flashing to stable |
| surprised | verrast | Random dots to organized pattern |
| confused | verward | Rotating with question marks |
| love | verliefd | Scrolling heart animation |
| tired | slaperig | Slow pulsing pattern |
| annoyed | geirriteerd | Rapid scanning lines |

## Siren Activation

The siren is automatically activated for these intense emotions:
- angry, scared, fear, wary, anxious, boos, bang

It can be triggered by either:
- Character emotions (Tobor's emotional state)
- User emotions (if user emotion detection is enabled)

## Testing

Run the test script to verify LED functionality:

```bash
# Automated demo
python3 src/test_led_control.py

# Interactive mode
python3 src/test_led_control.py interactive
```

## Configuration

The LED system uses the existing TARS configuration for:
- Emotion detection enabled/disabled
- Character settings
- Message queue integration

## Thread Safety

The LED controller uses proper thread management:
- Daemon threads for non-blocking operation
- Thread synchronization for state changes
- Proper cleanup on shutdown
- Timeout handling for thread joins

## Future Hardware Integration

When connecting actual hardware:

1. Replace placeholder functions in `module_led_control.py`:
   - `_control_eyes(state)` - Connect to eye LED GPIO pins
   - `_control_mouth_lights(state)` - Connect to mouth LED GPIO pins  
   - `_control_siren(state)` - Connect to siren/warning light relay

2. Update `tobor_emoties.py` for actual MAX7219 LED matrix:
   - SPI connection should work as-is
   - Verify GPIO pin assignments
   - Test matrix display initialization

3. Add hardware-specific error handling and fallbacks

## Troubleshooting

Common issues and solutions:

1. **Import Error for tobor_emoties**:
   - LED matrix emotions will be disabled
   - Other LED functions continue to work
   - Check SPI/hardware dependencies

2. **Thread Not Stopping**:
   - Use `emergency_stop()` function
   - Check for proper cleanup calls
   - Verify timeout settings

3. **No LED Response**:
   - Check terminal output for placeholder messages
   - Verify hardware connections (when applicable)
   - Test with `test_led_control.py` script

## Performance

The LED system is designed for minimal impact:
- Lightweight threading
- Efficient pattern algorithms
- Non-blocking operations
- Automatic cleanup 