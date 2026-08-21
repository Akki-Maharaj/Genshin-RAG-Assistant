import json
import re
import subprocess
import sys
import time
import numpy as np
import requests
from sentence_transformers import SentenceTransformer
from index_manager import load_index, load_manifest, print_status

import build_loader
from build_loader import (
    get_character_base_stats,
    get_weapon_atk_matched,
    get_character_rarity,
    find_dmg_param,
    build_character,
)

OLLAMA_MODEL = "qwen2.5:3b"
OLLAMA_URL = "http://localhost:11434"


def ensure_ollama_ready():
    try:
        subprocess.run(["ollama", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Ollama isn't installed or isn't on PATH. Install it from https://ollama.com "
              "and re-run this script.")
        sys.exit(1)

    server_up = False
    for attempt in range(3):
        try:
            requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
            server_up = True
            break
        except requests.exceptions.ConnectionError:
            if attempt == 0:
                print("Ollama server not responding -- attempting to start it...")
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            time.sleep(2)

    if not server_up:
        print("Could not reach the Ollama server after starting it. "
              "Try running 'ollama serve' manually in another terminal, then re-run this script.")
        sys.exit(1)

    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    installed_models = result.stdout

    if OLLAMA_MODEL not in installed_models:
        print(f"Model '{OLLAMA_MODEL}' not found locally -- downloading now "
              f"(this may take a while the first time)...")
        pull = subprocess.run(["ollama", "pull", OLLAMA_MODEL])
        if pull.returncode != 0:
            print(f"Failed to pull '{OLLAMA_MODEL}'. Check your internet connection and try again.")
            sys.exit(1)
        print(f"'{OLLAMA_MODEL}' downloaded successfully.")
    else:
        print(f"Ollama ready -- '{OLLAMA_MODEL}' is already downloaded.")


ensure_ollama_ready()
from damage_calculator import calculate_damage

print("Loading embedding model and index...")
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings, chunks = load_index()
print(f"Loaded {len(chunks)} chunks")
print_status()


_character_names = sorted(get_character_base_stats().keys(), key=len, reverse=True)
_weapon_names = sorted(get_weapon_atk_matched().keys(), key=len, reverse=True)

_UNVERIFIED_MECHANIC_CHARACTERS = {"Hu Tao"}

_character_rarity = get_character_rarity()


def _find_entity(query_lower, names):
    for name in names:
        if name.lower() in query_lower:
            return name
    return None


def _extract_level(query_lower, keyword_pattern, default):
    m = re.search(rf"{keyword_pattern}\s*(?:level|lv\.?|lvl)?\s*(\d{{1,3}})", query_lower)
    if m:
        lvl = int(m.group(1))
        if 1 <= lvl <= 90:
            return lvl
    return default


def _infer_talent_key(query_lower):
    if any(w in query_lower for w in ["burst", "ult"]):
        return "combat3", "burst"
    if any(w in query_lower for w in ["skill", "e ", " e)", "elemental skill"]):
        return "combat2", "skill"
    if any(w in query_lower for w in ["normal attack", "na ", "auto attack", "basic attack"]):
        return "combat1", "normal attack"
    return "combat3", "burst"



_CALC_KEYWORDS = [
    "damage", "dps", "how much dmg", "how much damage", "burst damage",
    "skill damage", "crit damage", "compare", "vs", "versus",
    "better weapon", "which weapon", "which does more"
]


def classify_intent(query):
    query_lower = query.lower()
    notes = []

    is_calc_shaped = any(kw in query_lower for kw in _CALC_KEYWORDS)
    if not is_calc_shaped:
        return "retrieval", notes

    character = _find_entity(query_lower, _character_names)
    if character is None:
        notes.append("Query looked damage/build-related but no known character name was found -- falling back to retrieval.")
        return "retrieval", notes

    weapons_found = [w for w in _weapon_names if w.lower() in query_lower]
    if not weapons_found:
        notes.append(f"Found character '{character}' but no known weapon name -- falling back to retrieval. "
                      f"Specify a weapon (e.g. 'Hu Tao with Staff of Homa') to use the calculator.")
        return "retrieval", notes

    return "calculator", notes



def _run_single_build(query_lower, character, weapon):
    if character in _UNVERIFIED_MECHANIC_CHARACTERS:
        return None, [f"{character} has a stat-conversion mechanic (HP/DEF -> ATK buff) this calculator "
                       f"doesn't model yet -- the ATK-only formula would give a misleadingly low number. "
                       f"Falling back to retrieval."]

    quality = _character_rarity.get(character)
    quality_note = None
    if quality is None:
        quality_note = f"No rarity found for '{character}' in character_rarity.json -- assumed 4-star."
        quality = 4

    char_level = _extract_level(query_lower, character.lower(), default=90)
    weapon_level = _extract_level(query_lower, weapon.lower(), default=90)
    talent_key, talent_label = _infer_talent_key(query_lower)

    if talent_key == "combat1":
        return None, ["Normal Attack damage isn't a single number (it's a multi-hit combo, "
                       "each hit scales differently) -- the calculator doesn't support this yet. "
                       "Falling back to retrieval."]

    talent_level_match = re.search(r"talent\s*(?:level|lv\.?|lvl)?\s*(\d{1,2})", query_lower)
    talent_level = int(talent_level_match.group(1)) if talent_level_match else 10
    talent_level = max(1, min(15, talent_level))

    param_key, is_ambiguous = find_dmg_param(character, talent_key)
    param_note = None
    if param_key is None:
        param_note = f"Could not identify a DMG% param label for {character}'s {talent_label} -- guessed 'param1'."
        param_key = "param1"
    elif is_ambiguous:
        param_note = (f"{character}'s {talent_label} has multiple valid DMG params (e.g. a hold/press "
                       f"skill with different variants) -- used the first match ('{param_key}'), "
                       f"which may not be the variant you meant.")

    try:
        build = build_character(
            character_name=character,
            character_level=char_level,
            character_quality=quality,
            weapon_name=weapon,
            weapon_level=weapon_level,
            talent_key=talent_key,
            talent_param_key=param_key,
            talent_level=talent_level,
            talent_scaling_stat="ATK",
        )
    except (KeyError, IndexError, FileNotFoundError) as e:
        return None, [f"Calculator lookup failed ({e}) -- falling back to retrieval."]

    notes = [f"Calculated: {character} Lv{char_level} ({talent_label}, talent Lv{talent_level}) "
              f"with {weapon} Lv{weapon_level}."]
    if quality_note:
        notes.append(quality_note)
    if param_note:
        notes.append(param_note)
    notes.append("Scaling stat assumed ATK (default) -- HP/DEF-scaling talents (e.g. Hu Tao's burst) "
                 "need talent_scaling_stat set manually; the number below may be wrong if this talent doesn't scale off ATK.")

    result = calculate_damage(build)
    return result, notes


def handle_calculator_query(query):
    query_lower = query.lower()
    character = _find_entity(query_lower, _character_names)
    weapons_found = [w for w in _weapon_names if w.lower() in query_lower]

    is_comparison = len(weapons_found) >= 2 or any(w in query_lower for w in [" vs ", " versus ", "compare"])

    if is_comparison and len(weapons_found) >= 2:
        print(f"\nComparing weapons for {character}: {weapons_found[0]} vs {weapons_found[1]}")
        outcomes = {}
        all_notes = []
        for weapon in weapons_found[:2]:
            result, notes = _run_single_build(query_lower, character, weapon)
            all_notes.extend(notes)
            if result is not None:
                outcomes[weapon] = result

        for n in all_notes:
            print(f"  note: {n}")

        if len(outcomes) < 2:
            print("Could not compute both builds -- falling back to retrieval for this query.")
            return None

        for weapon, result in outcomes.items():
            print(f"\n  {weapon}: expected {result['expected_damage']}, "
                  f"crit {result['crit_damage']}, non-crit {result['non_crit_damage']}")

        winner = max(outcomes.items(), key=lambda kv: kv[1]["expected_damage"])
        print(f"\n  -> {winner[0]} does more expected damage in this naked-artifact comparison "
              f"({winner[1]['expected_damage']} vs the other option).")
        return outcomes

    weapon = weapons_found[0]
    result, notes = _run_single_build(query_lower, character, weapon)
    for n in notes:
        print(f"  note: {n}")
    if result is None:
        return None

    print(f"\n  Expected damage: {result['expected_damage']}")
    print(f"  Crit damage: {result['crit_damage']}")
    print(f"  Non-crit damage: {result['non_crit_damage']}")
    print(f"  (naked build -- no artifacts/team buffs applied; add via build.add_source(...) for a real number)")
    return result



def retrieve(query, top_k=5):
    query_vec = model.encode([query])[0]
    norms = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_vec)
    similarities = np.dot(embeddings, query_vec) / (norms + 1e-10)

    query_lower = query.lower()
    is_general = any(w in query_lower for w in [
        "tell me about", "who is", "what is", "overview", "describe"
    ])
    is_constellation = any(w in query_lower for w in [
        "constellation", "c1", "c2", "c3", "c4", "c5", "c6"
    ])
    is_build = any(w in query_lower for w in [
        "weapon", "artifact", "build", "stats", "recommend"
    ])
    is_lore = any(w in query_lower for w in [
        "story", "lore", "background", "history", "past"
    ])
    is_relationship = any(w in query_lower for w in [
        "say about", "think about", "relationship", "opinion"
    ])
    is_mechanic = any(w in query_lower for w in [
        "how does", "mechanic", "work", "system", "explain",
        "ley line", "element", "reaction"
    ])

    type_boost = {}
    if is_general:
        type_boost = {
            "character": 0.15,
            "talent": 0.10,
            "playstyle": 0.08,
            "character_story": 0.05,
            "lore_intro": 0.05
        }
    elif is_constellation:
        type_boost = {"constellation": 0.20}
    elif is_build:
        type_boost = {
            "weapon": 0.15,
            "artifact": 0.15,
            "playstyle": 0.10
        }
    elif is_lore:
        type_boost = {
            "character_story": 0.15,
            "lore_intro": 0.10,
            "weapon_lore": 0.10,
            "quest_summary": 0.10,
            "npc_profile": 0.08
        }
    elif is_relationship:
        type_boost = {
            "voiceover_about_others": 0.20,
            "voiceover_personality": 0.10
        }
    elif is_mechanic:
        type_boost = {
            "world_mechanic": 0.20,
            "npc_profile": 0.05
        }

    boosted = similarities.copy()
    for i, chunk in enumerate(chunks):
        ctype = chunk.get("metadata", {}).get("type", chunk.get("topic", ""))
        if ctype in type_boost:
            boosted[i] += type_boost[ctype]

    top_indices = np.argsort(boosted)[::-1][:top_k]
    return [{
        "text": chunks[idx]["text"],
        "score": float(boosted[idx]),
        "type": chunks[idx].get("metadata", {}).get("type",
                chunks[idx].get("topic", "unknown")),
        "name": chunks[idx].get("metadata", {}).get("name",
                chunks[idx].get("character",
                chunks[idx].get("weapon", "unknown")))
    } for idx in top_indices]

def build_prompt(query, retrieved_chunks):
    context = "\n\n".join([
        f"[{c['type']}] {c['text'][:400]}"
        for c in retrieved_chunks
    ])
    return f"""You are a Genshin Impact wiki assistant. You have deep knowledge of Genshin Impact's lore, characters, world mechanics, quests, and game systems. Answer ONLY using the provided context. Do NOT invent information. If the context is insufficient, say so honestly.

Context:
{context}

Question: {query}

Answer:"""

def ask_ollama(prompt):
    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 512,
                "temperature": 0.7
            }
        },
        timeout=300
    )
    return resp.json()["response"]

def ask_retrieval(query):
    retrieved = retrieve(query, top_k=5)
    print("Top chunks:")
    for r in retrieved:
        print(f"  [{r['type']}] {r['name']} (score: {r['score']:.3f})")
    prompt = build_prompt(query, retrieved)
    print("Generating answer...")
    answer = ask_ollama(prompt)
    print(f"\nAnswer:\n{answer}")
    return answer



def ask(query):
    print(f"\nQuestion: {query}")
    intent, notes = classify_intent(query)
    for n in notes:
        print(f"  note: {n}")

    if intent == "calculator":
        print("[routed: calculator]")
        result = handle_calculator_query(query)
        if result is not None:
            return result
        print("[calculator path failed -- falling back to retrieval]")

    print("[routed: retrieval]")
    return ask_retrieval(query)


if __name__ == "__main__":
    print("\nGenshin Impact Wiki Assistant")
    print("Type 'quit' to exit\n")
    while True:
        query = input("Ask about Genshin: ").strip()
        if not query:
            continue
        if query.lower() == "quit":
            break
        ask(query)