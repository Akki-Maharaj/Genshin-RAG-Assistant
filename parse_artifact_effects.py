
import json
import re
import glob
import os

ARTIFACT_DIR = "dataset/artifacts"
OUT_FILE = "dataset/artifact_effects_parsed.json"

ELEMENTS = ["Pyro", "Hydro", "Cryo", "Electro", "Anemo", "Geo", "Dendro", "Physical"]

SIMPLE_PATTERNS = [
    (re.compile(r"^(ATK|DEF|HP|Elemental Mastery|Energy Recharge|CRIT Rate|CRIT DMG|Healing Bonus) \+([\d.]+)%\.?$", re.IGNORECASE),
     lambda m: {"stat": f"{m.group(1)}%", "value": float(m.group(2))}),

    (re.compile(r"^Max (HP|ATK|DEF) increased by ([\d,]+)\.?$", re.IGNORECASE),
     lambda m: {"stat": f"{m.group(1)}_flat", "value": float(m.group(2).replace(",", ""))}),

    (re.compile(r"(\d+(?:\.\d+)?)% (Pyro|Hydro|Cryo|Electro|Anemo|Geo|Dendro|Physical) DMG Bonus", re.IGNORECASE),
     lambda m: {"stat": f"{m.group(2).title()}_DMG%", "value": float(m.group(1))}),

    (re.compile(r"^Elemental Mastery \+(\d+)\.?$", re.IGNORECASE),
     lambda m: {"stat": "Elemental_Mastery_flat", "value": float(m.group(1))}),

    (re.compile(r"^CRIT (Rate|DMG) \+([\d.]+)%\.?$", re.IGNORECASE),
     lambda m: {"stat": f"CRIT_{m.group(1)}%", "value": float(m.group(2))}),

    (re.compile(r"^Energy Recharge increased by ([\d.]+)%\.?$", re.IGNORECASE),
     lambda m: {"stat": "Energy_Recharge%", "value": float(m.group(1))}),
]

def try_parse_simple(text):
    text = text.strip()
    for pattern, extractor in SIMPLE_PATTERNS:
        m = pattern.search(text)
        if m:
            return extractor(m)
    return None

def parse_effect(text):
    if not text:
        return None
    parsed = try_parse_simple(text)
    if parsed:
        parsed["raw"] = text
        parsed["conditional"] = False
        return parsed
    else:
        return {"conditional": True, "raw": text}

def build():
    results = {}
    for path in sorted(glob.glob(f"{ARTIFACT_DIR}/*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        result = data.get("result", data)
        name = result.get("name")
        if not name:
            continue

        effect_2pc_raw = result.get("effect2Pc")
        effect_4pc_raw = result.get("effect4Pc")

        results[name] = {
            "effect2Pc": parse_effect(effect_2pc_raw),
            "effect4Pc": parse_effect(effect_4pc_raw),
        }

    return results

if __name__ == "__main__":
    results = build()

    clean_2pc = sum(1 for v in results.values() if v["effect2Pc"] and not v["effect2Pc"]["conditional"])
    clean_4pc = sum(1 for v in results.values() if v["effect4Pc"] and not v["effect4Pc"]["conditional"])
    cond_2pc = sum(1 for v in results.values() if v["effect2Pc"] and v["effect2Pc"]["conditional"])
    cond_4pc = sum(1 for v in results.values() if v["effect4Pc"] and v["effect4Pc"]["conditional"])

    print(f"Parsed {len(results)} artifact sets")
    print(f"  2pc: {clean_2pc} clean / {cond_2pc} conditional (need manual encoding)")
    print(f"  4pc: {clean_4pc} clean / {cond_4pc} conditional (need manual encoding)")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {OUT_FILE}")

    print("\nSample conditional (4pc) entries needing manual encoding:")
    shown = 0
    for name, v in results.items():
        if v["effect4Pc"] and v["effect4Pc"]["conditional"] and shown < 5:
            print(f"  - {name}: {v['effect4Pc']['raw'][:100]}...")
            shown += 1
