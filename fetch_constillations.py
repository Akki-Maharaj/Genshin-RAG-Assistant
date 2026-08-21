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

os.makedirs("dataset/characters", exist_ok=True)
os.makedirs("dataset/constellations", exist_ok=True)

BASE = "https://genshin-db-api.vercel.app/api/v5"

for name in names:
    fname = name.lower().replace(" ", "_")

    char_path = f"dataset/characters/{fname}.json"
    if not os.path.exists(char_path):
        resp = get_with_retry(f"{BASE}/characters", {"query": name, "dumpResult": "true"})
        if resp:
            with open(char_path, "w", encoding="utf-8") as f:
                json.dump(resp.json(), f, indent=2, ensure_ascii=False)
            print(f"Saved character: {name}")
        else:
            print(f"FAILED character: {name}")
        time.sleep(1)

    const_path = f"dataset/constellations/{fname}.json"
    if not os.path.exists(const_path):
        resp = get_with_retry(f"{BASE}/constellations", {"query": name, "dumpResult": "true"})
        if resp:
            with open(const_path, "w", encoding="utf-8") as f:
                json.dump(resp.json(), f, indent=2, ensure_ascii=False)
            print(f"Saved constellations: {name}")
        else:
            print(f"FAILED constellations: {name}")
        time.sleep(1)

print("Done.")