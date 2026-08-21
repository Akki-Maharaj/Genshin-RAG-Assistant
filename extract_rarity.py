
import json
import glob

CHAR_DIR = "dataset/characters"
OUT_PATH = "dataset/character_rarity.json"

def main():
    files = sorted(glob.glob(f"{CHAR_DIR}/*.json"))
    rarity_map = {}
    missing = []

    for f in files:
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        result = data.get("result", data)
        name = result.get("name")
        rarity = result.get("rarity")
        if name is None or rarity is None:
            missing.append(f)
            continue
        rarity_map[name] = rarity

    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(rarity_map, fh, indent=2, ensure_ascii=False)

    print(f"Wrote {len(rarity_map)} entries to {OUT_PATH}")
    if missing:
        print(f"WARNING: {len(missing)} files missing name/rarity field:")
        for m in missing:
            print(f"  {m}")

    checks = {"Hu Tao": 5, "Zhongli": 5, "Xiangling": 4, "Bennett": 4}
    print("\nSanity check:")
    for name, expected in checks.items():
        actual = rarity_map.get(name)
        status = "OK" if actual == expected else "MISMATCH"
        print(f"  {name}: expected {expected}, got {actual} [{status}]")

if __name__ == "__main__":
    main()