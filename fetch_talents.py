import requests
import json
import os
import time

def get_with_retry(url, params=None, retries=5, timeout=15):
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            if resp.status_code == 200 and resp.text.strip():
                return resp
        except requests.exceptions.RequestException as e:
            print(f"  retry {attempt+1}: {e}")
        time.sleep(2 * (attempt + 1))
    return None

with open("character_names.json", encoding="utf-8") as f:
    names = json.load(f)

os.makedirs("dataset/talents", exist_ok=True)

BASE = "https://genshin-db-api.vercel.app/api/v5"

for name in names:
    fname = name.lower().replace(" ", "_")
    path = f"dataset/talents/{fname}.json"
    if os.path.exists(path):
        continue

    resp = get_with_retry(f"{BASE}/talents", {"query": name, "dumpResult": "true"})
    if resp:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(resp.json(), f, indent=2, ensure_ascii=False)
        print(f"Saved talents: {name}")
    else:
        print(f"FAILED talents: {name}")
    time.sleep(1)

print("Done.")