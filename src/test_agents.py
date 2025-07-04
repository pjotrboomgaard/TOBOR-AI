#!/usr/bin/env python3
"""
test_agents.py - Test the multi-agent system
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_status(message: str):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}")

async def test_imports():
    """Test importing all agent modules"""
    print_status("Testing imports...")
    
    try:
        from modules.module_config import load_config
        print_status("✅ Config module imported")
        
        from modules.agent_base import AgentCommunicationBus, AgentMessage, MessageType
        print_status("✅ Agent base imported")
        
        from modules.family_agents import ZanneAgent, ElsAgent, MirzaAgent, PjotrAgent
        print_status("✅ Family agents imported")
        
        from modules.tobor_agent import ToborAgent
        print_status("✅ Tobor agent imported")
        
        return True, None
        
    except Exception as e:
        print_status(f"❌ Import failed: {e}")
        return False, e

async def test_agent_creation():
    """Test creating agents"""
    print_status("Testing agent creation...")
    
    try:
        from modules.module_config import load_config
        from modules.family_agents import ZanneAgent
        
        config = load_config()
        char_data = {
            'char_name': 'TestZanne',
            'personality': 'Test personality',
            'voice_id': 'test',
            'tts_voice': 'test'
        }
        
        agent = ZanneAgent(char_data, config)
        print_status("✅ Agent created successfully")
        return True, None
        
    except Exception as e:
        print_status(f"❌ Agent creation failed: {e}")
        return False, e

def main():
    print_status("🧪 TARS-AI Multi-Agent Test")
    print_status("=" * 40)
    
    # Test imports
    import_success, import_error = asyncio.run(test_imports())
    if not import_success:
        print_status(f"Import test failed: {import_error}")
        return
    
    # Test agent creation
    agent_success, agent_error = asyncio.run(test_agent_creation())
    if not agent_success:
        print_status(f"Agent creation failed: {agent_error}")
        return
    
    print_status("✅ All tests passed!")

if __name__ == "__main__":
    main() 