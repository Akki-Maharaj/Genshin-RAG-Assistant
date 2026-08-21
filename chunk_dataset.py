
import json
import os
from pathlib import Path

DATASET_DIR = Path("dataset")
OUTPUT_FILE = Path("chunks.jsonl")

chunks = []


def add_chunk(chunk_id, text, metadata):
    chunks.append({
        "id": chunk_id,
        "text": text.strip(),
        "metadata": metadata
    })


char_dir = DATASET_DIR / "characters"
for filepath in sorted(char_dir.glob("*.json")):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    if "result" not in data:
        continue
    r = data["result"]
    if "name" not in r:
        continue
    name = r["name"]

    lines = [
        f"Character: {name}",
        f"Element: {r.get('elementText', 'N/A')}",
        f"Weapon Type: {r.get('weaponText', 'N/A')}",
        f"Rarity: {r.get('rarity', 'N/A')} star",
        f"Region: {r.get('region', 'N/A')}",
        f"Ascension Stat: {r.get('substatText', 'N/A')}",
    ]
    if r.get("description"):
        lines.append(f"Description: {r['description']}")

    add_chunk(
        chunk_id=f"character_{filepath.stem}",
        text="\n".join(lines),
        metadata={
            "type": "character",
            "name": name,
            "element": r.get("elementText"),
            "weapon_type": r.get("weaponText"),
            "rarity": r.get("rarity"),
            "region": r.get("region"),
            "substat": r.get("substatText"),
        }
    )

print(f"Characters: {len(chunks)} chunks")


talent_dir = DATASET_DIR / "talents"
talent_start = len(chunks)
for filepath in sorted(talent_dir.glob("*.json")):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    if "result" not in data:
        continue
    r = data["result"]
    if "name" not in r:
        continue

    talent_map = {
        "combat1": "Normal Attack",
        "combat2": "Elemental Skill",
        "combat3": "Elemental Burst",
        "passive1": "Passive 1",
        "passive2": "Passive 2",
        "passive3": "Passive 3",
    }

    for key, label in talent_map.items():
        talent = r.get(key)
        if not talent:
            continue
        text = (
            f"Character: {name}\n"
            f"Talent ({label}): {talent['name']}\n"
            f"{talent['description']}"
        )
        add_chunk(
            chunk_id=f"talent_{filepath.stem}_{key}",
            text=text,
            metadata={
                "type": "talent",
                "name": name,
                "talent_slot": label,
                "talent_name": talent["name"],
            }
        )

print(f"Talents: {len(chunks) - talent_start} chunks")


const_dir = DATASET_DIR / "constellations"
const_start = len(chunks)
for filepath in sorted(const_dir.glob("*.json")):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    if "result" not in data:
        continue
    r = data["result"]
    if "name" not in r:
        continue

    for level in ["c1", "c2", "c3", "c4", "c5", "c6"]:
        const = r.get(level)
        if not const:
            continue
        text = (
            f"Character: {name}\n"
            f"Constellation {level.upper()} — {const['name']}\n"
            f"{const['description']}"
        )
        add_chunk(
            chunk_id=f"constellation_{filepath.stem}_{level}",
            text=text,
            metadata={
                "type": "constellation",
                "name": name,
                "level": level.upper(),
                "constellation_name": const["name"],
            }
        )

print(f"Constellations: {len(chunks) - const_start} chunks")


playstyle_dir = DATASET_DIR / "playstyle"
playstyle_start = len(chunks)
for filepath in sorted(playstyle_dir.glob("*.json")):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    name = data.get("character", filepath.stem.replace("_", " ").title())
    roles = data.get("inferred_roles", [])
    reactions = data.get("reaction_tags", [])
    element = data.get("element", "")
    weapon = data.get("weapon_type", "")
    substat = data.get("substat", "")

    roles_str = ", ".join(roles) if roles else "Unknown"
    reactions_str = ", ".join(reactions) if reactions else "None"

    text = (
        f"Character: {name}\n"
        f"Element: {element} | Weapon: {weapon} | Ascension Stat: {substat}\n"
        f"Roles: {roles_str}\n"
        f"Elemental Reaction Synergies: {reactions_str}"
    )
    add_chunk(
        chunk_id=f"playstyle_{filepath.stem}",
        text=text,
        metadata={
            "type": "playstyle",
            "name": name,
            "element": element,
            "roles": roles,
            "reaction_tags": reactions,
        }
    )

print(f"Playstyle: {len(chunks) - playstyle_start} chunks")


weapon_dir = DATASET_DIR / "weapons"
weapon_start = len(chunks)

SKIP_WEAPON_FILES = {"costs", "mainstattype", "rarity", "range_gauge", "weapontype"}

for filepath in sorted(weapon_dir.glob("*.json")):
    if filepath.stem in SKIP_WEAPON_FILES:
        continue
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    if "result" not in data:
        continue
    r = data["result"]
    if "name" not in r:
        continue

    name = r["name"]
    weapon_type = r.get("weaponText", "N/A")
    rarity = r.get("rarity", "N/A")
    main_stat = r.get("mainStatText", "N/A")
    effect_name = r.get("effectName", "")

    r1_desc = r.get("r1", {}).get("description", "")
    r5_desc = r.get("r5", {}).get("description", "")

    lines = [
        f"Weapon: {name}",
        f"Type: {weapon_type} | Rarity: {rarity} star | Main Stat: {main_stat}",
    ]
    if effect_name:
        lines.append(f"Passive Effect ({effect_name}):")
    if r1_desc:
        lines.append(f"  R1: {r1_desc}")
    if r5_desc and r5_desc != r1_desc:
        lines.append(f"  R5: {r5_desc}")

    add_chunk(
        chunk_id=f"weapon_{filepath.stem}",
        text="\n".join(lines),
        metadata={
            "type": "weapon",
            "name": name,
            "weapon_type": weapon_type,
            "rarity": rarity,
            "main_stat": main_stat,
        }
    )

print(f"Weapons: {len(chunks) - weapon_start} chunks")


artifact_dir = DATASET_DIR / "artifacts"
artifact_start = len(chunks)
for filepath in sorted(artifact_dir.glob("*.json")):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    if "result" not in data:
        continue
    r = data["result"]
    if "name" not in r:
        continue

    name = r["name"]
    effect2 = r.get("effect2Pc", "")
    effect4 = r.get("effect4Pc", "")

    lines = [f"Artifact Set: {name}"]
    if effect2:
        lines.append(f"2-Piece Bonus: {effect2}")
    if effect4:
        lines.append(f"4-Piece Bonus: {effect4}")

    add_chunk(
        chunk_id=f"artifact_{filepath.stem}",
        text="\n".join(lines),
        metadata={
            "type": "artifact",
            "name": name,
        }
    )

print(f"Artifacts: {len(chunks) - artifact_start} chunks")


with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for chunk in chunks:
        f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

print(f"\nTotal chunks written: {len(chunks)}")
print(f"Output: {OUTPUT_FILE}")