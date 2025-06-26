"""
module_prompt.py – v4

Prompt‑builder met automatische in‑line laad­functionaliteit voor
**psychologische profiel‑JSON's**.

🔄 **Wijziging in deze versie**
• Profielen zijn verplaatst naar CharacterManager en hernoemd naar 'characterpsychology'
• Profielen worden nu geladen tijdens character initialisatie in plaats van tijdens prompt building
"""

from __future__ import annotations

from datetime import datetime

from modules.module_engine import check_for_module
from modules.module_messageQue import queue_message

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

    # ── dynamische blokken - nu via character_manager
    psychology_context = clean_text(character_manager.get_psychology_context(user_prompt))
    
    # Check if this is a memory-specific question - if so, disable memory retrieval to prevent conflicts
    memory_keywords = ['herinnering', 'memory', 'memories', 'verhaal', 'gebeurtenis', 'specifiek']
    is_memory_question = any(keyword in user_prompt.lower() for keyword in memory_keywords)
    
    if is_memory_question and 'memories' in psychology_context.lower():
        # For memory questions, don't retrieve past memory to avoid conflicts
        past_memory = "Memory retrieval disabled for memory-specific questions to ensure accuracy."
    else:
        past_memory = clean_text(memory_manager.get_longterm_memory(user_prompt))

    draft = (
        f"{base}### Character Psychology:\n---\n{psychology_context}\n---\n\n"
        f"### Memory:\n---\nLong-Term Context:\n{past_memory}\n---\n"
    )

    context_size = int(config['LLM']['contextsize'])
    used = memory_manager.token_count(draft).get('length', 0)
    avail = max(0, context_size - used)

    short_term = ""
    if avail:
        # For memory questions, limit short-term memory to avoid fictional content
        if is_memory_question and 'memories' in psychology_context.lower():
            short_term = "Short-term memory limited for memory-specific questions."
        else:
            short_term = memory_manager.get_shortterm_memories_tokenlimit(avail)
            avail -= memory_manager.token_count(short_term).get('length', 0)

    example_block = ""
    if avail and character_manager.example_dialogue:
        if memory_manager.token_count(character_manager.example_dialogue).get('length', 0) <= avail:
            example_block = f"### Example Dialog:\n{character_manager.example_dialogue}\n---\n"

    # Add strong instruction when memory content exists but psychology context is about memories
    memory_override_instruction = ""
    if 'memories' in psychology_context.lower() and (past_memory or short_term):
        memory_override_instruction = (
            "### CRITICAL INSTRUCTION:\n"
            "When answering questions about memories, relationships, or personal history, "
            "you MUST ONLY use information from the Character Psychology section above. "
            "IGNORE any conflicting information in the Memory sections below. "
            "The Character Psychology contains the ONLY VALID memories and facts.\n"
            "---\n\n"
        )

    prompt = (
        f"{base}### Character Psychology:\n---\n{psychology_context}\n---\n\n"
        f"{memory_override_instruction}"
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
        queue_message(f"DEBUG PROMPT:\n{cleaned}")
    return cleaned
