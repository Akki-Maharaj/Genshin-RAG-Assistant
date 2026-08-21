# Genshin RAG Assistant

A local Genshin Impact assistant I built to answer both lore questions and actual damage-number questions, fully offline.

It does two things:
- Answers lore/mechanics/general questions using RAG (retrieval + a local LLM)
- Answers "how much damage does X do with weapon Y" questions using an actual damage calculator I wrote from the game's real formula, not the LLM guessing numbers

I split it this way because I quickly learned LLMs are bad at math and at remembering exact game numbers, but they're good at writing an answer once you hand them the right text. So the numeric stuff goes through real code, everything else goes through retrieval + the LLM.

Runs 100% locally. Uses Ollama for the LLM and sentence-transformers for embeddings, no external API calls when you're actually using it.

---

## Running it

```bash
pip install -r requirements.txt
python run.py
```

`run.py` checks if Ollama is installed/running and pulls the model itself if it's missing, so you don't have to mess with `ollama serve`/`ollama pull` manually.

---

## How it's put together

```
fetch_*.py  →  dataset/  →  ┬─ chunking + embedding →  index/  ─┐
                            └─ build_loader.py → damage calc   ─┤
                                                                ↓
                                                              run.py (router) → answer
```

1. **fetch_*.py** — one-time scripts, pull raw character/weapon/talent/artifact/lore data from the genshin-db API + Fandom wiki. Only need to rerun these after a new patch.
2. **dataset/** — where all that raw data lives, plus a couple derived files (character_rarity.json, artifact_effects_parsed.json) built from it.
3. **index/** — lore/mechanics text chunked and embedded (all-MiniLM-L6-v2), stored as plain numpy vectors + a jsonl file. No vector DB — didn't need one at this scale, plain cosine similarity with numpy is enough and way simpler to reason about.
4. **build_loader.py + damage_calculator.py** — my actual damage formula implementation, built from the real stat curves in the dataset. If it can't verify something (multi-hit normal attacks, characters with weird stat-conversion mechanics like Hu Tao) it says so and falls back to retrieval instead of just making up a number.
5. **run.py** — decides per question whether to hit the calculator or retrieval, based on keywords + whether it recognizes a character/weapon name in the question.

I wrote up the full architecture + how I debugged some annoying data-format issues along the way in `project_report.docx` if you want the long version.

---

## What each file actually does

| File | What it does |
|---|---|
| `run.py` | entry point — loads everything, routes each question, handles Ollama setup automatically |
| `build_loader.py` | turns raw dataset json into stuff the calculator can use — character stats at a given level, weapon ATK at a given level, and `find_dmg_param()` which figures out the right damage number from a talent's label text instead of assuming it's always in the same spot |
| `damage_calculator.py` | the actual math — Genshin's real damage formula, no LLM anywhere near it |
| `index_manager.py` | handles the retrieval index — embedding chunks, saving/loading, adding new sources without rebuilding everything |
| `chunk_dataset.py` / `build_world_mechanic_chunks.py` / `build_artifact_lore_chunks.py` | turn raw lore/mechanics/artifact data into chunks ready to embed |
| `extract_rarity.py` | one-time script, pulls each character's star rarity out of the raw data |
| `fetch_*.py` | one-time scripts that populate dataset/ from the APIs |
| `master_name.py` | the character roster list the fetch scripts use — update this when new characters release |
| `audit_talent_params.py` / `inspect_character_stats.py` / `inspect_talent_data.py` | scripts I used to sanity-check the data while building this — not needed to actually run the project |

---

## Stuff that doesn't work yet / known issues

- No build/team recommendation data is indexed yet, so "what's the best weapon for X" currently just pulls whatever lore text is thematically similar, not an actual answer. Don't trust that one.
- The calculator assumes talents scale off ATK. A handful of characters convert one stat into another (Hu Tao's Skill turns HP into ATK, for example) and I haven't modeled that yet — those characters are listed explicitly in run.py and fall back to retrieval instead of giving a wrong number.
- Normal Attack damage isn't supported — it's a multi-hit combo, there's no single "the damage" number to give.

---

## Where the data comes from

Pulled from the genshin-db API and the Genshin Impact Fandom wiki (community-run). All Genshin Impact content/names belong to HoYoverse — this is just a personal tool for querying publicly available data, not something I'm claiming ownership of or redistributing as my own dataset.

---

## Requirements

- Python 3.12+
- Ollama installed (the script handles pulling the model itself)
- requests, numpy, sentence-transformers
