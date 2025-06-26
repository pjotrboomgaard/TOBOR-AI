"""
module_prompt.py – v4

Simplified prompt-builder that uses pre-loaded psychological profiles 
from CharacterManager instead of loading them on-demand.

🔄 **Wijziging in deze versie**
• Profielen worden nu geladen tijdens CharacterManager initialisatie
• Geen caching meer nodig - profielen zijn altijd beschikbaar via character_manager
• Veel eenvoudiger en consistenter met de rest van de applicatie
"""

from __future__ import annotations
from datetime import datetime
from modules.module_engine import check_for_module

# ────────────────────────────────────────────────────────────────────────────────
#  Hulp util's
# ────────────────────────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    return (
        text.replace("\\\\", "\\")
            .replace("\\n", "\n")
            .replace("\\'", "'")
            .replace('\\"', '"')
            .replace("<END>", "")
            .strip()
    )


def inject_dynamic_values(tmpl: str, user_name: str, char_name: str) -> str:
    return (
        tmpl.replace("{user}", user_name)
            .replace("{char}", char_name)
            .replace("'user_input'", user_name)
            .replace("'bot_response'", char_name)
    )

# ────────────────────────────────────────────────────────────────────────────────
#  Hoofdfunctie: build_prompt
# ────────────────────────────────────────────────────────────────────────────────

def build_prompt(user_prompt: str, character_manager, memory_manager, config: dict, debug: bool = False) -> str:
    now = datetime.now()
    dtg = f"Current Date: {now.strftime('%m/%d/%Y')}\nCurrent Time: {now.strftime('%H:%M:%S')}\n"

    user_name = config["CHAR"]["user_name"]
    char_name = character_manager.char_name
    functioncall = check_for_module(user_prompt)

    persona_traits = "\n".join(f"- {k}: {v}" for k, v in character_manager.traits.items())

    # ── statische blokken
    base = (
        f"System: {config['LLM']['systemprompt']}\n\n"
        f"### Instruction:\n{inject_dynamic_values(config['LLM']['instructionprompt'], user_name, char_name)}\n\n"
        f"### Interaction Context:\n---\nUser: {user_name}\nCharacter: {char_name}\n{dtg}---\n\n"
        f"### Character Details:\n---\n{character_manager.character_card}\n---\n\n"
        f"### {char_name} Settings:\n{persona_traits}\n---\n\n"
    )

    # ── dynamische blokken (nu veel eenvoudiger!)
    profile_context = clean_text(character_manager.get_profile_context(user_prompt))
    past_memory = clean_text(memory_manager.get_longterm_memory(user_prompt))

    draft = (
        f"{base}### Psychologische Profielen:\n---\n{profile_context}\n---\n\n"
        f"### Memory:\n---\nLong-Term Context:\n{past_memory}\n---\n"
    )

    context_size = int(config['LLM']['contextsize'])
    used = memory_manager.token_count(draft).get('length', 0)
    avail = max(0, context_size - used)

    short_term = ""
    if avail:
        short_term = memory_manager.get_shortterm_memories_tokenlimit(avail)
        avail -= memory_manager.token_count(short_term).get('length', 0)

    example_block = ""
    if avail and character_manager.example_dialogue:
        if memory_manager.token_count(character_manager.example_dialogue).get('length', 0) <= avail:
            example_block = f"### Example Dialog:\n{character_manager.example_dialogue}\n---\n"

    prompt = (
        f"{base}### Psychologische Profielen:\n---\n{profile_context}\n---\n\n"
        f"{example_block}"
        f"### Memory:\n---\nLong-Term Context:\n{past_memory}\n---\n"
        f"Recent Conversation:\n{short_term}\n---\n"
        f"### Interaction:\n{user_name}: {user_prompt}\n\n"
        f"### Function Calling Tool:\nResult: {functioncall}\n"
        f"### Response:\n{char_name}: "
    )

    prompt = inject_dynamic_values(prompt, user_name, char_name)
    cleaned = clean_text(prompt)
    
    if debug:
        from modules.module_messageQue import queue_message
        queue_message(f"DEBUG PROMPT:\n{cleaned}")
    
    return cleaned
