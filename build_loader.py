
import json
import os
import re
from damage_calculator import CharacterBuild

DATA_DIR = "dataset"


_character_base_stats = None
_level_multiplier_table = None
_weapon_atk_matched = None
_artifact_effects = None
_character_rarity = None

def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def get_character_base_stats():
    global _character_base_stats
    if _character_base_stats is None:
        _character_base_stats = _load_json(f"{DATA_DIR}/character_base_stats.json")
    return _character_base_stats

def get_level_multiplier_table():
    global _level_multiplier_table
    if _level_multiplier_table is None:
        raw = _load_json(f"{DATA_DIR}/level_multiplier_table.json")
        _level_multiplier_table = {int(k): v for k, v in raw.items()}
    return _level_multiplier_table

def get_weapon_atk_matched():
    global _weapon_atk_matched
    if _weapon_atk_matched is None:
        _weapon_atk_matched = _load_json(f"{DATA_DIR}/weapon_atk_matched.json")
    return _weapon_atk_matched

def get_artifact_effects():
    global _artifact_effects
    if _artifact_effects is None:
        _artifact_effects = _load_json(f"{DATA_DIR}/artifact_effects_parsed.json")
    return _artifact_effects

def get_character_rarity():
    global _character_rarity
    if _character_rarity is None:
        _character_rarity = _load_json(f"{DATA_DIR}/character_rarity.json")
    return _character_rarity



def character_stat_at_level(character_name, level, quality):
    stats = get_character_base_stats()
    mult_table = get_level_multiplier_table()

    if character_name not in stats:
        raise KeyError(f"No base stats found for character: {character_name}")

    c = stats[character_name]
    star_key = "5star" if quality == 5 else "4star"

    if level not in mult_table:
        raise KeyError(f"No level multiplier for level {level}")

    level_mult = mult_table[level][star_key]
    asc_progress = 1.0 if level > 20 else 0.0

    hp = c["base_hp"] * level_mult + c["asc_hp"] * asc_progress
    atk = c["base_atk"] * level_mult + c["asc_atk"] * asc_progress
    defense = c["base_def"] * level_mult + c["asc_def"] * asc_progress

    return {"hp": hp, "atk": atk, "def": defense}


def weapon_atk_at_level(weapon_name, level, ascended=True):
    matched = get_weapon_atk_matched()
    if weapon_name not in matched:
        raise KeyError(f"No ATK curve found for weapon: {weapon_name}")

    curve = matched[weapon_name]["curve"]
    suffix = "a" if ascended else "b"
    key = f"{level}{suffix}"

    if key not in curve or curve[key] is None:
        fallback_key = f"{level}b"
        if fallback_key in curve and curve[fallback_key] is not None:
            return curve[fallback_key]
        raise KeyError(f"No ATK value for {weapon_name} at level {key}")

    return curve[key]


def find_dmg_param(character_name, talent_key):
    fname = character_name.lower().replace(" ", "_").replace("'", "")
    path = f"{DATA_DIR}/talents/{fname}.json"
    if not os.path.exists(path):
        return None, False

    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    result = data.get("result", data)
    talent = result.get(talent_key)
    if not talent:
        return None, False

    labels = talent.get("attributes", {}).get("labels", [])
    params = talent.get("attributes", {}).get("parameters", {})

    conditional_markers = ["low hp", "per stack", "per ", "additional", "max hp", "cd", "cost"]
    excluded_terms = ["absorption", "shield"]

    candidates = []
    for label in labels:
        m = re.search(r"\{(\w+):", label)
        if not m:
            continue
        param_key = m.group(1)
        if param_key not in params:
            continue
        label_lower = label.lower()
        if "dmg" not in label_lower:
            continue
        if any(term in label_lower for term in excluded_terms):
            continue
        candidates.append((label, param_key))

    if not candidates:
        return None, False

    unconditional = [c for c in candidates
                      if not any(marker in c[0].lower() for marker in conditional_markers)]
    pool = unconditional if unconditional else candidates
    is_ambiguous = len(pool) > 1
    return pool[0][1], is_ambiguous


def get_talent_multiplier(character_name, talent_key, param_key, talent_level):
    fname = character_name.lower().replace(" ", "_").replace("'", "")
    path = f"{DATA_DIR}/talents/{fname}.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"No talent file for {character_name}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    result = data.get("result", data)

    talent = result.get(talent_key)
    if not talent:
        raise KeyError(f"No talent '{talent_key}' found for {character_name}")

    params = talent.get("attributes", {}).get("parameters", {})
    if param_key not in params:
        available = list(params.keys())
        raise KeyError(f"No param '{param_key}' for {character_name}'s {talent_key}. "
                        f"Available: {available}")

    values = params[param_key]
    idx = talent_level - 1
    if idx < 0 or idx >= len(values):
        raise IndexError(f"Talent level {talent_level} out of range (1-{len(values)})")

    return values[idx]



def build_character(character_name, character_level, character_quality,
                     weapon_name, weapon_level,
                     talent_key, talent_param_key, talent_level,
                     talent_scaling_stat="ATK"):
    char_stats = character_stat_at_level(character_name, character_level, character_quality)
    weapon_atk = weapon_atk_at_level(weapon_name, weapon_level)
    talent_mult = get_talent_multiplier(character_name, talent_key, talent_param_key, talent_level)

    return CharacterBuild(
        character_name=character_name,
        level=character_level,
        base_hp=char_stats["hp"],
        base_atk=char_stats["atk"],
        base_def=char_stats["def"],
        weapon_base_atk=weapon_atk,
        talent_multiplier=talent_mult,
        talent_scaling_stat=talent_scaling_stat,
    )


if __name__ == "__main__":
    try:
        stats = character_stat_at_level("Hu Tao", 90, quality=5)
        print("Hu Tao @ 90:", stats)
    except Exception as e:
        print("Character stat lookup failed:", e)

    try:
        atk = weapon_atk_at_level("Staff of Homa", 90)
        print("Staff of Homa ATK @ 90:", atk)
    except Exception as e:
        print("Weapon ATK lookup failed:", e)

    print("\n--- Full end-to-end test: Hu Tao Burst damage ---")
    try:
        build = build_character(
            character_name="Hu Tao",
            character_level=90,
            character_quality=5,
            weapon_name="Staff of Homa",
            weapon_level=90,
            talent_key="combat3",
            talent_param_key="param1",
            talent_level=10,
            talent_scaling_stat="HP",
        )
        print("Assembled build talent_multiplier (burst %):", build.talent_multiplier)

        from damage_calculator import calculate_damage
        result = calculate_damage(build)
        for k, v in result.items():
            print(f"  {k}: {v}")
    except Exception as e:
        print("End-to-end build/calc failed:", e)