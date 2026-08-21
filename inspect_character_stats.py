import json
import glob

candidates = sorted(glob.glob("dataset/characters/*.json"))
path = None
for c in candidates:
    with open(c, encoding="utf-8") as f:
        d = json.load(f)
    if "result" in d and d["result"]:
        path = c
        break

if not path:
    print("No character file with a valid 'result' found!")
else:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    result = data.get("result", data)
    print("File:", path)
    print("Top-level keys:", list(result.keys()) if isinstance(result, dict) else type(result))
    print()

    for key in result.keys():
        if isinstance(result, dict):
            key_lower = key.lower()
            if any(term in key_lower for term in
                   ["stat", "level", "ascend", "curve", "base", "growth", "hp", "atk", "def"]):
                print(f"--- {key} ---")
                print(json.dumps(result[key], indent=2, ensure_ascii=False)[:1500])
                print()
