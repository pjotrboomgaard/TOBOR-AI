#!/usr/bin/env python3
"""
test_multi_agent_system.py

Test script for the TARS-AI Multi-Agent System
"""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.module_config import load_config
from modules.agent_base import AgentCommunicationBus, AgentMessage, MessageType
from modules.family_agents import ZanneAgent, ElsAgent, MirzaAgent, PjotrAgent
from modules.tobor_agent import ToborAgent

def print_status(message: str):
    """Print timestamped status messages"""
    from datetime import datetime
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}")

async def test_agent_creation():
    """Test creating agents"""
    print_status("🧪 Testing Agent Creation...")
    
    config = load_config()
    
    # Create sample character data
    char_data = {
        'char_name': 'TestCharacter',
        'personality': 'Test personality',
        'voice_id': 'test_voice',
        'tts_voice': 'test_tts'
    }
    
    # Test creating a Zanne agent
    try:
        zanne = ZanneAgent(char_data, config)
        print_status("✅ ZanneAgent created successfully")
    except Exception as e:
        print_status(f"❌ ZanneAgent creation failed: {e}")
        return False
    
    # Test creating Tobor agent
    try:
        tobor = ToborAgent(char_data, config)
        print_status("✅ ToborAgent created successfully")
    except Exception as e:
        print_status(f"❌ ToborAgent creation failed: {e}")
        return False
    
    return True

async def test_communication_bus():
    """Test the communication bus"""
    print_status("🧪 Testing Communication Bus...")
    
    # Create communication bus
    bus = AgentCommunicationBus()
    
    config = load_config()
    char_data = {
        'char_name': 'TestZanne',
        'personality': 'Test Zanne',
        'voice_id': 'test',
        'tts_voice': 'test'
    }
    
    # Create and register agents
    zanne = ZanneAgent(char_data, config)
    zanne.set_communication_bus(bus)
    
    char_data['char_name'] = 'TestTobor'
    tobor = ToborAgent(char_data, config)
    tobor.set_communication_bus(bus)
    
    # Activate agents
    zanne.activate()
    tobor.activate()
    
    print_status(f"✅ Communication bus created with {len(bus.agents)} agents")
    
    # Start bus in background
    bus_task = asyncio.create_task(bus.start())
    
    # Test sending a message
    test_message = AgentMessage.create(
        msg_type=MessageType.USER_INPUT,
        sender="user",
        content="Ik voel me niet begrepen"
    )
    
    print_status("📤 Sending test message...")
    await bus.send_message(test_message)
    
    # Wait for responses
    await asyncio.sleep(3)
    
    # Stop bus
    bus.stop()
    
    print_status("✅ Communication bus test completed")
    return True

async def test_agent_responses():
    """Test agent response generation"""
    print_status("🧪 Testing Agent Response Generation...")
    
    config = load_config()
    
    # Create test agents
    agents = []
    for name, agent_class in [('zanne', ZanneAgent), ('els', ElsAgent), ('pjotr', PjotrAgent)]:
        char_data = {
            'char_name': name.title(),
            'personality': f'{name.title()} family member',
            'voice_id': 'test',
            'tts_voice': 'test'
        }
        
        agent = agent_class(char_data, config)
        agents.append((name, agent))
    
    # Test response generation
    test_input = "Ik voel me niet begrepen in deze familie"
    
    for name, agent in agents:
        try:
            response = await agent.generate_response(test_input)
            print_status(f"✅ {name.title()}: {response}")
        except Exception as e:
            print_status(f"❌ {name.title()} response failed: {e}")
    
    return True

async def run_full_system_test():
    """Run a complete system test"""
    print_status("🧪 Running Full Multi-Agent System Test...")
    
    # Test 1: Agent Creation
    if not await test_agent_creation():
        print_status("❌ Agent creation test failed")
        return
    
    # Test 2: Communication Bus
    if not await test_communication_bus():
        print_status("❌ Communication bus test failed")
        return
    
    # Test 3: Agent Responses
    if not await test_agent_responses():
        print_status("❌ Agent response test failed")
        return
    
    print_status("✅ All tests passed!")

async def run_interactive_test():
    """Run interactive test with simulated therapy session"""
    print_status("🧪 Running Interactive Test Session...")
    
    config = load_config()
    bus = AgentCommunicationBus()
    
    # Create and register all agents
    agent_configs = {
        'zanne': ZanneAgent,
        'els': ElsAgent,
        'mirza': MirzaAgent,
        'pjotr': PjotrAgent,
        'tobor': ToborAgent
    }
    
    agents = {}
    for name, agent_class in agent_configs.items():
        char_data = {
            'char_name': name.title(),
            'personality': f'{name.title()} family member',
            'voice_id': 'test',
            'tts_voice': 'test'
        }
        
        agent = agent_class(char_data, config)
        agent.set_communication_bus(bus)
        agent.activate()
        agents[name] = agent
    
    # Start communication bus
    bus_task = asyncio.create_task(bus.start())
    
    # Start therapy session with Tobor
    print_status("🏥 Starting therapy session...")
    await agents['tobor'].start_therapy_session("Ik voel me niet begrepen")
    
    # Wait for family agents to respond
    await asyncio.sleep(5)
    
    # Send additional test inputs
    test_inputs = [
        "Niemand luistert naar me",
        "Ik probeer alleen maar te helpen",
        "Misschien moeten we meer mediteren"
    ]
    
    for test_input in test_inputs:
        print_status(f"👤 User input: {test_input}")
        
        message = AgentMessage.create(
            msg_type=MessageType.USER_INPUT,
            sender="user",
            content=test_input
        )
        
        await bus.send_message(message)
        await asyncio.sleep(4)  # Wait for responses
    
    # End session
    bus.stop()
    print_status("🏥 Interactive test session completed")

def main():
    """Main test runner"""
    print_status("=" * 60)
    print_status("🤖 TARS-AI Multi-Agent System Test Suite")
    print_status("=" * 60)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            asyncio.run(run_interactive_test())
        elif sys.argv[1] == "--agents":
            asyncio.run(test_agent_creation())
        elif sys.argv[1] == "--bus":
            asyncio.run(test_communication_bus())
        elif sys.argv[1] == "--responses":
            asyncio.run(test_agent_responses())
        else:
            print_status("Usage: python test_multi_agent_system.py [--interactive|--agents|--bus|--responses]")
    else:
        asyncio.run(run_full_system_test())

if __name__ == "__main__":
    main() 