
import requests
import json
import os
import time

API_URL = "https://genshin-impact.fandom.com/api.php"
OUT_DIR = "dataset/world_mechanics"
HEADERS = {"User-Agent": "genshin-rag-project/1.0 (personal research project)"}

def sanitize(name):
    fname = name.lower()
    for ch in [" ", "'", ",", "-", '"', ":", "!", "?", "(", ")", "/"]:
        fname = fname.replace(ch, "_" if ch in (" ", "/") else "")
    return fname

def get_with_retry(params, retries=3, timeout=15):
    for attempt in range(retries):
        try:
            resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=timeout)
            print(f"    [debug] status={resp.status_code} url={resp.url}")
            if resp.status_code == 200:
                try:
                    return resp.json()
                except ValueError:
                    print(f"    [debug] non-JSON response, first 300 chars: {resp.text[:300]}")
                    return None
            else:
                print(f"    [debug] body preview: {resp.text[:300]}")
        except requests.exceptions.RequestException as e:
            print(f"  retry {attempt+1}: {e}")
        time.sleep(2 * (attempt + 1))
    return None

def search_page_title(query):
    data = get_with_retry({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": 1
    })
    if not data:
        return None
    results = data.get("query", {}).get("search", [])
    return results[0]["title"] if results else None

import re

def strip_wikitext(raw):
    text = raw

    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)

    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^>]*/>", "", text)

    text = re.sub(r"<[^>]+>", "", text)

    text = re.sub(r"\[\[(File|Image):[^\]]*\]\]", "", text, flags=re.IGNORECASE)

    text = re.sub(r"\[\[([^\|\]]*)\|([^\]]*)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]*)\]\]", r"\1", text)

    text = re.sub(r"\[https?://\S+\s+([^\]]*)\]", r"\1", text)
    text = re.sub(r"\[https?://\S+\]", "", text)

    text = text.replace("'''", "").replace("''", "")

    text = re.sub(r"={2,6}\s*(.*?)\s*={2,6}", r"\n## \1\n", text)

    text = re.sub(r"^\{\|.*?\|\}$", "", text, flags=re.DOTALL | re.MULTILINE)
    text = re.sub(r"\[\[Category:[^\]]*\]\]", "", text, flags=re.IGNORECASE)

    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [ln.strip() for ln in text.split("\n")]
    text = "\n".join(ln for ln in lines if ln)

    return text.strip()

def fetch_extract(title):
    data = get_with_retry({
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "redirects": "1",
        "titles": title,
        "format": "json"
    })
    if not data:
        return None
    pages = data.get("query", {}).get("pages", {})
    for page_id, page in pages.items():
        if page_id == "-1" or "missing" in page:
            return None
        revisions = page.get("revisions", [])
        if not revisions:
            return None
        raw = revisions[0].get("slots", {}).get("main", {}).get("*", "")
        if not raw:
            raw = revisions[0].get("*", "")
        return strip_wikitext(raw)
    return None

PAGES = [
    ("Elemental Reaction", "Elemental Reaction"),
    ("Vaporize", "Vaporize"),
    ("Melt", "Melt"),
    ("Overloaded", "Overloaded"),
    ("Superconduct", "Superconduct"),
    ("Electro-Charged", "Electro-Charged"),
    ("Swirl", "Swirl"),
    ("Crystallize", "Crystallize"),
    ("Bloom", "Bloom"),
    ("Burgeon", "Burgeon"),
    ("Hyperbloom", "Hyperbloom"),
    ("Quicken", "Quicken"),
    ("Aggravate", "Aggravate"),
    ("Spread", "Spread"),
    ("Burning", "Burning"),
    ("Catalyze", "Catalyze"),
    ("Frozen", "Frozen"),
    ("Elemental Mastery", "Elemental Mastery"),
    ("CRIT", "CRIT"),
    ("Elemental Resonance", "Elemental Resonance"),
    ("Stamina", "Stamina"),
    ("Adventure Rank", "Adventure Rank"),
    ("Domains", "Domain"),
    ("Spiral Abyss", "Spiral Abyss"),
    ("Ley Lines", "Ley Line"),
    ("Archon", "Archon"),
    ("Gnosis", "Gnosis"),
    ("Vision", "Vision"),
]

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    failed = []

    for name, guess_title in PAGES:
        fname = sanitize(name)
        path = f"{OUT_DIR}/{fname}.json"
        if os.path.exists(path):
            print(f"Skip (exists): {name}")
            continue

        print(f"  Trying title: {guess_title}")
        extract = fetch_extract(guess_title)

        if not extract:
            print(f"  Guess failed, searching for real title...")
            real_title = search_page_title(name)
            print(f"  Search found: {real_title}")
            if real_title:
                extract = fetch_extract(real_title)

        if not extract or len(extract) < 50:
            print(f"FAILED: {name}")
            failed.append(name)
            continue

        with open(path, "w", encoding="utf-8") as f:
            json.dump({"name": name, "title": guess_title, "text": extract},
                       f, indent=2, ensure_ascii=False)
        print(f"Saved: {name} ({len(extract)} chars)")
        time.sleep(0.5)

    print("\nDone.")
    if failed:
        print(f"Failed ({len(failed)}): {failed}")

if __name__ == "__main__":
    main()
