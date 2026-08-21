import json
import glob

candidates = sorted(glob.glob("dataset/talents/*.json"))
path = None
for c in candidates:
    with open(c, encoding="utf-8") as f:
        d = json.load(f)
    if "result" in d and d["result"]:
        path = c
        break

if not path:
    print("No talent file with a valid 'result' found!")
else:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    result = data.get("result", data)
    print("File:", path)
    print("Top-level keys:", list(result.keys()) if isinstance(result, dict) else type(result))
    print()
    print(json.dumps(result, indent=2, ensure_ascii=False)[:4000])
