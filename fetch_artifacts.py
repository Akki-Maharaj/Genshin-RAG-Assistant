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

def sanitize(name):
    fname = name.lower()
    for ch in [" ", "'", ",", "-", '"', ":", "!", "?", "(", ")"]:
        fname = fname.replace(ch, "_" if ch == " " else "")
    return fname

with open("artifact_names.json", encoding="utf-8") as f:
    names = json.load(f)

os.makedirs("dataset/artifacts", exist_ok=True)
BASE = "https://genshin-db-api.vercel.app/api/v5"

for name in names:
    fname = sanitize(name)
    path = f"dataset/artifacts/{fname}.json"
    if os.path.exists(path):
        continue

    resp = get_with_retry(f"{BASE}/artifacts", {"query": name, "dumpResult": "true"})
    if resp:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(resp.json(), f, indent=2, ensure_ascii=False)
        print(f"Saved: {name}")
    else:
        print(f"FAILED: {name}")
    time.sleep(1)

print("Done.")