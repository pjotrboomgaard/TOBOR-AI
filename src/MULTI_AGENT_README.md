# TARS-AI Multi-Agent Family Therapy System

## Overview

The TARS-AI Multi-Agent System represents a revolutionary approach to family therapy simulation, where each family member operates as an independent agent with their own context, memory, and behavioral patterns. Tobor acts as the orchestrating therapist who manages the therapy flow and directs agent interactions.

## Architecture

### Multi-Agent Components

1. **Individual Character Agents**
   - **ZanneAgent**: Defensive, explosive emotions, feels misunderstood
   - **ElsAgent**: Corrective, optimistic but intrusive, tries to fix everyone
   - **MirzaAgent**: Solution-focused, offers mindfulness, emotionally distant
   - **PjotrAgent**: Mediator, diplomatic, tired of being family translator

2. **Orchestrator Agent**
   - **ToborAgent**: Therapeutic AI that directs therapy flow and manages other agents

3. **Communication System**
   - **AgentCommunicationBus**: Central messaging system for inter-agent communication
   - **AgentMessage**: Structured message format with types and metadata

### Key Features

#### ✅ Independent Agent Operation
- Each character runs as a separate agent with unique context
- Individual memory and emotional state tracking
- Character-specific behavioral patterns and triggers
- Independent decision-making capabilities

#### ✅ Orchestrated Therapy Flow
- Tobor manages therapy session progression
- Strategic agent activation and engagement
- Therapeutic intervention and pattern recognition
- Session goal tracking and breakthrough facilitation

#### ✅ Voice Integration
- Individual voice configuration per character
- Synchronized TTS output preventing overlap
- Voice input detection and processing
- Character-specific voice personalities

#### ✅ Realistic Family Dynamics
- **Zanne**: Defensive triggers, explosive reactions, feeling misunderstood
- **Els**: Corrective urges, unsolicited advice, worry-driven responses
- **Mirza**: Mindfulness solutions, emotional distance, project focus
- **Pjotr**: Mediation fatigue, diplomatic bridge-building, breakthrough moments

## Usage

### Quick Start

1. **Test Mode** (No voice, text-only):
   ```bash
   ./Start-Multi-Agent-Therapy.sh --test
   ```

2. **Voice Mode** (Full interactive therapy):
   ```bash
   ./Start-Multi-Agent-Therapy.sh --voice
   ```

3. **Default Mode** (Voice interaction):
   ```bash
   ./Start-Multi-Agent-Therapy.sh
   ```

### Session Flow

1. **Initialization**: All agents are created with individual configurations
2. **Therapy Start**: Tobor opens the session with therapeutic greeting
3. **Agent Activation**: Family members are gradually brought into conversation
4. **User Interaction**: Voice input triggers agent responses
5. **Orchestrated Responses**: Tobor selects which agents should respond
6. **Therapeutic Guidance**: Tobor provides interventions and pattern analysis

## Technical Implementation

### Agent Base System (`agent_base.py`)
- **BaseAgent**: Core agent functionality with context memory
- **AgentCommunicationBus**: Message routing and broadcasting
- **AgentMessage**: Structured communication format
- **MessageType**: Enum for different message categories

### Character Agents (`family_agents.py`)
Each agent implements:
- `handle_user_input()`: Process and respond to user input
- `handle_agent_response()`: React to other family members
- Character-specific behavioral triggers and patterns
- Emotional state management and progression

### Orchestrator (`tobor_agent.py`)
Tobor provides:
- Therapy session management and flow control
- Strategic agent engagement and activation
- Therapeutic analysis and intervention
- Pattern recognition and breakthrough facilitation

### Multi-Agent App (`app_multi_agent_therapy.py`)
Complete application providing:
- Agent system initialization and configuration
- Voice input/output integration
- Communication bus management
- Session orchestration and flow control

## Behavioral Patterns

### Zanne (Defensive Agent)
- **Triggers**: Control words, criticism, structural demands
- **Responses**: Explosive defensiveness, feeling misunderstood
- **Pattern**: "Niemand van jullie VRAAGT wat ik eigenlijk nodig heb!"

### Els (Corrective Agent)
- **Triggers**: Problems, stress, family conflict
- **Responses**: Automatic corrections, unsolicited advice
- **Pattern**: "Je moet gewoon wat positiever denken."

### Mirza (Solution Agent)
- **Triggers**: Emotional distress, conflict situations
- **Responses**: Mindfulness solutions, meditation suggestions
- **Pattern**: "Misschien moeten we eerst een korte meditatie doen..."

### Pjotr (Mediator Agent)
- **Triggers**: Family conflicts, emotional outbursts
- **Responses**: Diplomatic mediation, eventual fatigue expression
- **Pattern**: "Misschien kunnen we dit rustig bespreken."

### Tobor (Orchestrator Agent)
- **Function**: Therapeutic guidance, session flow management
- **Capabilities**: Pattern recognition, intervention timing
- **Approach**: Clinical but warm, systematically therapeutic

## Configuration

### Character Setup
Each agent requires:
```python
char_data = {
    'char_name': 'CharacterName',
    'personality': 'Character description',
    'voice_id': 'elevenlabs_voice_id',
    'tts_voice': 'tts_system_voice'
}
```

### Voice Configuration
- Individual voice IDs for each character
- TTS system selection (ElevenLabs, Azure, Piper, etc.)
- Character-specific audio settings

## Testing

### Available Tests
1. **Import Test**: Verify all modules load correctly
2. **Agent Creation**: Test individual agent instantiation
3. **Communication Bus**: Verify message routing works
4. **Full System**: Complete multi-agent interaction test

### Running Tests
```bash
cd src
source venv/bin/activate
python test_agents.py
```

## Advantages Over Previous System

### ✅ True Multi-Agent Architecture
- Each character has independent context and memory
- No shared state between family members
- Realistic agent autonomy and decision-making

### ✅ Orchestrated Therapy Flow
- Tobor strategically manages conversation flow
- Therapeutic interventions at appropriate moments
- Pattern recognition and breakthrough facilitation

### ✅ Scalable and Modular
- Easy to add new family members or agents
- Configurable behavioral patterns and triggers
- Independent agent development and testing

### ✅ Enhanced Realism
- Character-specific behavioral triggers
- Emotional state progression and memory
- Natural family dynamic simulation

## Future Enhancements

### Planned Features
- **Memory Integration**: Character-specific long-term memory
- **Emotional Modeling**: Advanced emotional state tracking
- **Therapy Metrics**: Session progress and breakthrough analysis
- **Dynamic Personalities**: Adaptive character responses over time

### Extensibility
- Additional family members as new agents
- Specialized therapy scenarios and goals
- Integration with external psychology frameworks
- Advanced NLP for emotional analysis

## Getting Started

1. **Activate Environment**: `source venv/bin/activate`
2. **Run Test**: `python test_agents.py`
3. **Start Therapy**: `./Start-Multi-Agent-Therapy.sh --test`
4. **Voice Therapy**: `./Start-Multi-Agent-Therapy.sh --voice`

The system is ready for immediate use with full voice integration and therapeutic orchestration! 