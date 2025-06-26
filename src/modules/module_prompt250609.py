"""
module_prompt.py – v3

Prompt‑builder met automatische in‑line laad­functionaliteit voor
**psychologische profiel‑JSON’s**.

🔄 **Wijziging in deze versie**
• Profielen worden nu standaard gezocht in een submap **profiles/**
  binnen de map waar de actieve `character‑card staat.
  (bv. `character/Tobor/profiles/…`)
• Config‑override blijft mogelijk met `[CHAR] profile_dir = …`.
"""

from __future__ import annotations

import json
import os
import glob
from datetime import datetime
from typing import Dict, List

from modules.module_engine import check_for_module
from modules.module_messageQue import queue_message

# ────────────────────────────────────────────────────────────────────────────────
#  Helper‑functies voor profielen
# ────────────────────────────────────────────────────────────────────────────────
_PROFILE_CACHE: Dict[str, dict] | None = None


def _derive_profile_dir(config: dict, character_manager=None) -> str:
    """Determine the directory that holds profile JSONs.

    Priority order:
    1. Explicit `[CHAR] profile_dir` in `config.ini`.
    2. Folder that *actually contains the active character card* plus `/profiles`.
       We mimic exactly the same path logic as `CharacterManager`, i.e. we prefix
       the config‑path with `".."` because modules live in `src/modules/`.
    3. Fallback: global `profiles/` at project root.
    """

    # 1. explicit override
    explicit = config["CHAR"].get("profile_dir")
    if explicit:
        return explicit

    # 2. alongside active character card --------------------------------------
    card_path: str | None = None

    # Preferred: ask the live CharacterManager (already contains correct ".." prefix)
    if character_manager and hasattr(character_manager, "character_card_path"):
        card_path = character_manager.character_card_path
    else:
        # Re‑construct path exactly as CharacterManager does
        raw_cfg_path = config["CHAR"].get("character_card_path", "")
        if raw_cfg_path:
            card_path = os.path.join("..", raw_cfg_path)

    if card_path:
        base_dir = os.path.dirname(os.path.abspath(card_path))
        return os.path.join(base_dir, "profiles")

    # 3. final fallback
    return "profiles"


def _load_profiles(profile_dir: str) -> Dict[str, dict]:
    """Lees alle `*.json` in *profile_dir* (één keer) en cache."""
    global _PROFILE_CACHE
    if _PROFILE_CACHE is not None:
        return _PROFILE_CACHE

    profiles: Dict[str, dict] = {}
    if not os.path.isdir(profile_dir):
        queue_message(f"WARN: profile directory '{profile_dir}' niet gevonden – profiles worden overgeslagen")
        _PROFILE_CACHE = {}
        return _PROFILE_CACHE

    for path in glob.glob(os.path.join(profile_dir, "*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                profiles.update(data)
        except Exception as exc:
            queue_message(f"ERROR: kon profielbestand {path} niet lezen: {exc}")

    queue_message(f"INFO: {len(profiles)} profiel‑secties geladen uit '{profile_dir}'")
    _PROFILE_CACHE = profiles
    return _PROFILE_CACHE


def _flatten_dict(section: dict) -> str:
    """Zet geneste dict om in key‑value regels (eenvoudige flatten)."""
    lines: List[str] = []

    def walk(prefix: str, obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(f"{prefix}{k}.", v)
        elif isinstance(obj, list):
            for i, itm in enumerate(obj, 1):
                walk(f"{prefix}{i}.", itm)
        else:
            lines.append(f"{prefix[:-1]}: {obj}")

    walk("", section)
    return "\n".join(lines)


def _get_profile_context(user_prompt: str, config: dict) -> str:
    """Exporteer relevante profieldata als string."""
    profile_dir = _derive_profile_dir(config)
    profiles = _load_profiles(profile_dir)

    # Match op naamcomponent in user_prompt → preferential load
    hits = [k for k in profiles if k.split("_")[-1].lower() in user_prompt.lower()]
    keys = hits or list(profiles.keys())

    blocks: List[str] = []
    for key in keys:
        blocks.append(f"######## {key.upper()} ########")
        blocks.append(_flatten_dict(profiles[key]))
        blocks.append("")
    return "\n".join(blocks)

# ────────────────────────────────────────────────────────────────────────────────
#  Hulp util’s uit het origineel
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

    # ── dynamische blokken
    profile_context = clean_text(_get_profile_context(user_prompt, config))
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
        queue_message(f"DEBUG PROMPT:\n{cleaned}")
    return cleaned
