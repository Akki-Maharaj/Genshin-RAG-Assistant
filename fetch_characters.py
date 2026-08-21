import requests
import json
import os
import time

os.makedirs("dataset/characters", exist_ok=True)

BASE_URL = "https://genshin-db-api.vercel.app/api/v5/characters"

resp = requests.get(BASE_URL, params={"query": "names", "matchCategories": "true"})
names = resp.json()
print(f"Found {len(names)} characters")

for name in names:
    try:
        resp = requests.get(BASE_URL, params={
            "query": name,
            "dumpResult": "true"
        })
        data = resp.json()

        filename = name.lower().replace(" ", "_")
        with open(f"dataset/characters/{filename}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved {name}")
        time.sleep(0.3)
    except Exception as e:
        print(f"Failed {name}: {e}")