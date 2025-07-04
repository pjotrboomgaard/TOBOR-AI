# 🤖 TARS-AI Multi-Agent Family Therapy System

## System Overview

Successfully implemented a revolutionary multi-agent architecture where each family member operates as an independent agent with Tobor as the orchestrating therapist.

## ✅ What's Working

### Individual Character Agents
- **ZanneAgent**: Defensive, explosive emotions ("Niemand van jullie VRAAGT wat ik eigenlijk nodig heb!")
- **ElsAgent**: Corrective, tries to fix everyone ("Je moet gewoon wat positiever denken")
- **MirzaAgent**: Solution-focused mindfulness ("Er is een prachtige mindfulness-app...")
- **PjotrAgent**: Diplomatic mediator ("Misschien kunnen we dit rustig bespreken")

### Orchestrator System
- **ToborAgent**: Directs therapy flow, activates agents strategically
- **Communication Bus**: Routes messages between agents
- **Voice Integration**: Each agent has unique voice configuration

## 🚀 How to Use

### Test Mode (Text Only)
```bash
cd src
source venv/bin/activate
./Start-Multi-Agent-Therapy.sh --test
```

### Voice Mode (Full Interaction)
```bash
./Start-Multi-Agent-Therapy.sh --voice
```

## 🏗️ Architecture

### Files Created
- `modules/agent_base.py` - Core agent system
- `modules/family_agents.py` - Individual character agents  
- `modules/tobor_agent.py` - Orchestrator agent
- `app_multi_agent_therapy.py` - Main application
- `test_agents.py` - Test suite
- `Start-Multi-Agent-Therapy.sh` - Launch script

### Key Features
✅ Independent agent context and memory  
✅ Unique behavioral patterns per character  
✅ Therapeutic orchestration by Tobor  
✅ Voice input/output integration  
✅ Real-time agent communication  
✅ Pattern recognition and intervention  

## 🎭 Character Behaviors

Each agent has distinct personality triggers and response patterns that create realistic family dynamics during therapy sessions.

Ready for immediate use! 