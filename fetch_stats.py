
import requests
import json
import os
import time

BASE = "https://genshin-db-api.vercel.app/api/v5/stats"

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

def fetch_stats_for_folder(folder, names_file, out_dir):
    with open(names_file, encoding="utf-8") as f:
        names = json.load(f)

    os.makedirs(out_dir, exist_ok=True)
    print(f"\nFetching {folder} stats for {len(names)} entries...")

    failed = []
    for name in names:
        fname = sanitize(name)
        path = f"{out_dir}/{fname}.json"
        if os.path.exists(path):
            continue

        resp = get_with_retry(BASE, {
            "folder": folder,
            "query": name,
            "dumpResult": "true"
        })

        if not resp:
            print(f"FAILED (no response): {name}")
            failed.append(name)
            continue

        try:
            data = resp.json()
        except ValueError:
            print(f"FAILED (bad JSON): {name}")
            failed.append(name)
            continue

        if not data or (isinstance(data, dict) and "result" in data and not data["result"]):
            print(f"FAILED (empty result): {name}")
            failed.append(name)
            continue

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved: {name}")
        time.sleep(0.5)

    print(f"\n{folder} done. Failed ({len(failed)}): {failed}")
    return failed

if __name__ == "__main__":
    char_failed = fetch_stats_for_folder(
        "characters", "character_names.json", "dataset/character_stats"
    )
    weapon_failed = fetch_stats_for_folder(
        "weapons", "weapon_names.json", "dataset/weapon_stats"
    )

    print("\n=== SUMMARY ===")
    print(f"Character stat fetch failures: {len(char_failed)} -> {char_failed}")
    print(f"Weapon stat fetch failures: {len(weapon_failed)} -> {weapon_failed}")
