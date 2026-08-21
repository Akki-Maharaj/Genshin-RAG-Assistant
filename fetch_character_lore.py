import requests
import re
import json
import os
import time

def get_wiki_content(title):
    url = "https://genshin-impact.fandom.com/api.php"
    params = {
        "action": "query",
        "titles": title,
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "format": "json",
        "formatversion": "2"
    }
    for attempt in range(5):
        try:
            resp = requests.get(url, params=params, timeout=15)
            page = resp.json()["query"]["pages"][0]
            if "missing" in page:
                return None
            return page["revisions"][0]["slots"]["main"]["content"]
        except Exception as e:
            print(f"  retry {attempt+1}: {e}")
            time.sleep(2 * (attempt + 1))
    return None

def clean_text(text):
    text = re.sub(r'<p>(.*?)</p>', r'\1 ', text, flags=re.DOTALL)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'<ref[^/]*/>', '', text)
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'\[\[(File|Image):[^\]]*\]\]', '', text)
    text = re.sub(r'\[\[[^\]|]*\|([^\]]*)\]\]', r'\1', text)
    text = re.sub(r'\[\[([^\]]*)\]\]', r'\1', text)
    text = re.sub(r'\{\{[^}]*\}\}', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&mdash;', '—', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_profile(content, char_name):
    chunks = []
    if not content:
        return chunks

    intro_match = re.search(r"\}\}\n'''[^']+'''.*?\n\n(.*?)(?:==|\Z)", content, re.DOTALL)
    if intro_match:
        intro = clean_text(intro_match.group(1))
        if intro:
            chunks.append({
                "character": char_name,
                "topic": "lore_intro",
                "text": f"{char_name} — Introduction: {intro}"
            })

    story_pattern = re.finditer(
        r'\|title\d+\s*=\s*(Character Story \d+|Character Details|Vision|[^|\n]+)'
        r'.*?\|text\d+\s*=(.*?)(?=\|title\d+|\}\})',
        content, re.DOTALL
    )
    for match in story_pattern:
        title = match.group(1).strip()
        text = clean_text(match.group(2))
        if text and len(text) > 50:
            chunks.append({
                "character": char_name,
                "topic": "character_story",
                "story_title": title,
                "text": f"{char_name} — {title}: {text}"
            })

    return chunks

def parse_voice_overs(content, char_name):
    chunks = []
    if not content:
        return chunks

    vo_pattern = re.finditer(
        r'\|vo_(\d+)_\d+_title\s*=\s*([^\n|]+).*?'
        r'\|vo_\1_\d+_tx\s*=\s*([^\n|]+(?:\n(?!\|)[^\n|]+)*)',
        content, re.DOTALL
    )

    for match in vo_pattern:
        section_num = int(match.group(1))
        title = match.group(2).strip()
        text = clean_text(match.group(3))

        if not text or len(text) < 10:
            continue

        if section_num == 5:
            topic = "voiceover_about_self"
        elif section_num == 6:
            topic = "voiceover_about_us"
        elif section_num == 7:
            topic = "voiceover_misc"
        elif section_num == 8:
            topic = "voiceover_about_others"
        elif section_num == 9:
            topic = "voiceover_personality"
        else:
            topic = "voiceover_other"

        title = title.replace("{character}", char_name)

        chunks.append({
            "character": char_name,
            "topic": topic,
            "vo_title": title,
            "text": f"{char_name} — {title}: {text}"
        })

    return chunks

with open("character_names.json", encoding="utf-8") as f:
    names = json.load(f)

os.makedirs("dataset/wiki_profile", exist_ok=True)
os.makedirs("dataset/wiki_voiceovers", exist_ok=True)

for name in names:
    fname = name.lower().replace(" ", "_")

    profile_path = f"dataset/wiki_profile/{fname}.json"
    if not os.path.exists(profile_path):
        content = get_wiki_content(f"{name}/Profile")
        if content and "#REDIRECT" in content:
            redirect = re.search(r'\[\[([^\]]+)\]\]', content)
            if redirect:
                content = get_wiki_content(redirect.group(1))
        profile_chunks = parse_profile(content, name)
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile_chunks, f, indent=2, ensure_ascii=False)
        print(f"Profile saved: {name} ({len(profile_chunks)} chunks)")
        time.sleep(0.5)

    vo_path = f"dataset/wiki_voiceovers/{fname}.json"
    if not os.path.exists(vo_path):
        content = get_wiki_content(f"{name}/Voice-Overs")
        vo_chunks = parse_voice_overs(content, name)
        with open(vo_path, "w", encoding="utf-8") as f:
            json.dump(vo_chunks, f, indent=2, ensure_ascii=False)
        print(f"Voice-overs saved: {name} ({len(vo_chunks)} chunks)")
        time.sleep(0.5)

print("Done.")