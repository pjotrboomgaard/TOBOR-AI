# TARS-AI Conversation Testing Tools

This directory contains specialized testing tools for rapid development and debugging of conversation logic without the overhead of full TTS/STT systems.

## Quick Start

```bash
# From the src directory
./test_conversations_launcher.sh
```

## Available Test Tools

### 1. Text-Only Test (`app_conversation_test_text.py`)
**Best for:** Ultra-fast conversation logic testing

**Features:**
- Text input/output only - no audio processing
- Instant character responses
- Character switching by typing names
- Automatic multi-character conversations
- Minimal system overhead

**Usage:**
```bash
cd src
source .venv/bin/activate
python3 app_conversation_test_text.py
```

**Commands:**
- Type any message to interact with current character
- Include character names (`mirza`, `els`, `zanne`, `pjotr`, `tobor`) to switch
- Type `quit`, `exit`, or `q` to exit
- Press Ctrl+C to force quit

### 2. Voice Input Test (`app_conversation_test_voice.py`)
**Best for:** Testing voice recognition with conversation logic

**Features:**
- STT enabled for voice input
- Text output (no TTS overhead)
- Voice-activated character switching
- Real microphone interaction
- Automatic conversations continue in background

**Usage:**
```bash
cd src
source .venv/bin/activate
python3 app_conversation_test_voice.py
```

**Commands:**
- Speak to interact (say character names to switch)
- Press Ctrl+C to exit

### 3. Full Application (`App-Start.sh`)
**Best for:** Complete system testing with audio

**Features:**
- Full TTS + STT + conversation system
- Complete audio experience
- All production features enabled

## Development Workflow

1. **Rapid Logic Testing:** Use text-only test for quick iteration on conversation flows
2. **Voice Testing:** Use voice input test to verify STT integration  
3. **Full Integration:** Use full app for complete system validation

## Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'hyperdb'"**
- Make sure to activate the virtual environment: `source .venv/bin/activate`

**"STT initialization error"**
- Check microphone permissions
- Verify audio devices are available
- Run `alsamixer` to check audio levels

**Characters not responding**
- Check network connection (OpenAI API required)
- Verify configuration in `config.ini`
- Check character files in `../character/` directory

### Performance Tips

- Text-only test is ~10x faster than voice test
- Voice test is ~5x faster than full app
- Use text-only for rapid conversation logic development
- Use voice test for STT debugging
- Use full app only for final testing

## File Overview

- `app_conversation_test_text.py` - Text-only conversation testing
- `app_conversation_test_voice.py` - Voice input conversation testing  
- `test_conversations_launcher.sh` - Interactive launcher menu
- `CONVERSATION_TESTING.md` - This documentation file

## Character Switching

All test tools support character switching:

- **Mirza**: Sarcastic, confident, challenging
- **Els**: Supportive, empathetic, family-focused
- **Zanne**: Complex psychology, 15 behavioral sections
- **Pjotr**: Thoughtful, garden metaphors, philosophical
- **Tobor**: Technical, mechanical (note: corrupted psychology file)

Simply mention character names in your input to switch between them. 