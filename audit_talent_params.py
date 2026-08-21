
import json
import glob
import re

DATA_DIR = "dataset"
TALENT_KEYS = ["combat1", "combat2", "combat3"]
CONDITIONAL_MARKERS = ["low hp", "per stack", "per ", "additional", "max hp", "cd", "cost"]

SAMPLE_CHARACTERS = ["hu_tao", "xiangling", "noelle", "bennett", "xingqiu"]


def analyze_talent(character_name, talent_key, talent):
    labels = talent.get("attributes", {}).get("labels", [])
    params = talent.get("attributes", {}).get("parameters", {})

    candidates = []
    for label in labels:
        m = re.search(r"\{(\w+):", label)
        if not m:
            continue
        param_key = m.group(1)
        if param_key not in params:
            continue
        if "dmg" in label.lower():
            candidates.append((label, param_key))

    if not candidates:
        return "NO_MATCH", None, []

    unconditional = [c for c in candidates
                      if not any(marker in c[0].lower() for marker in CONDITIONAL_MARKERS)]

    if unconditional:
        if len(unconditional) > 1:
            return "AMBIGUOUS", unconditional[0][1], unconditional
        return "OK", unconditional[0][1], unconditional
    else:
        return "FALLBACK_USED", candidates[0][1], candidates


def main():
    files = [f"{DATA_DIR}/talents/{name}.json" for name in SAMPLE_CHARACTERS]
    files = [f for f in files if __import__("os").path.exists(f)]
    print(f"Auditing {len(files)} talent files x {len(TALENT_KEYS)} talent slots...\n")

    counts = {"OK": 0, "NO_MATCH": 0, "AMBIGUOUS": 0, "FALLBACK_USED": 0}
    flagged = []

    for f in files:
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        result = data.get("result", data)
        name = result.get("name", f)

        for talent_key in TALENT_KEYS:
            talent = result.get(talent_key)
            if not talent:
                continue
            status, chosen_param, candidates = analyze_talent(name, talent_key, talent)
            counts[status] += 1
            if status != "OK":
                flagged.append((name, talent_key, status, chosen_param, candidates))

    print("Summary:")
    for status, count in counts.items():
        print(f"  {status}: {count}")

    print(f"\n{len(flagged)} flagged cases (not clean OK matches):\n")
    for name, talent_key, status, chosen_param, candidates in flagged:
        print(f"[{status}] {name} / {talent_key} -- would choose: {chosen_param}")
        for label, pkey in candidates:
            print(f"    candidate: {pkey} <- \"{label}\"")
        print()


if __name__ == "__main__":
    main()