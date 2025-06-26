#!/usr/bin/env python3
"""
Debug script to test config loading
"""

import sys
import os

# Add the modules directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from modules.module_config import load_config

def debug_config():
    print("=== CONFIG DEBUG ===")
    
    # Load config
    config = load_config()
    
    print(f"Config type: {type(config)}")
    
    # Check if CHARACTERS section exists
    if hasattr(config, 'CHARACTERS'):
        print("✅ Found CHARACTERS as attribute")
        characters = config.CHARACTERS
        print(f"CHARACTERS type: {type(characters)}")
        
        if hasattr(characters, '__dict__'):
            print("CHARACTERS attributes:")
            for key, value in characters.__dict__.items():
                if not key.startswith('_'):
                    print(f"  {key}: {value}")
        else:
            print("CHARACTERS is not an object with __dict__")
            
    elif isinstance(config, dict) and 'CHARACTERS' in config:
        print("✅ Found CHARACTERS as dictionary key")
        characters = config['CHARACTERS']
        print(f"CHARACTERS type: {type(characters)}")
        print("CHARACTERS content:")
        for key, value in characters.items():
            print(f"  {key}: {value}")
    else:
        print("❌ CHARACTERS section not found")
        
        # Show all available sections
        print("\nAvailable sections:")
        if hasattr(config, '__dict__'):
            for key in config.__dict__.keys():
                if not key.startswith('_'):
                    print(f"  - {key}")
        elif isinstance(config, dict):
            for key in config.keys():
                print(f"  - {key}")
        else:
            print(f"Config is type {type(config)}, can't list sections")
    
    # Check specific sections
    print(f"\nSTT section exists: {hasattr(config, 'STT') or 'STT' in config}")
    print(f"TTS section exists: {hasattr(config, 'TTS') or 'TTS' in config}")
    print(f"CHAR section exists: {hasattr(config, 'CHAR') or 'CHAR' in config}")

if __name__ == "__main__":
    debug_config()
