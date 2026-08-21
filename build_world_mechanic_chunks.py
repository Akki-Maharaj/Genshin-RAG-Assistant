
import json
import os
import glob
from index_manager import add_source

MECHANICS_DIR = "dataset/world_mechanics"
SOURCE_ID = "world_mechanics_v1"
MAX_CHARS = 1200

def chunk_text(name, text, max_chars=MAX_CHARS):
    if len(text) <= max_chars:
        return [text]

    parts = text.split("\n")
    chunks, current = [], ""
    for part in parts:
        if len(current) + len(part) + 1 > max_chars and current:
            chunks.append(current.strip())
            current = part
        else:
            current += "\n" + part
    if current.strip():
        chunks.append(current.strip())
    return chunks

def build_chunks():
    chunks = []
    for path in sorted(glob.glob(f"{MECHANICS_DIR}/*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        name = data.get("name")
        text = (data.get("text") or "").strip()
        if not name or not text:
            continue

        pieces = chunk_text(name, text)
        for i, piece in enumerate(pieces):
            suffix = f"_{i}" if len(pieces) > 1 else ""
            chunk_id = f"world_mechanic_{name.lower().replace(' ', '_').replace('-', '_')}{suffix}"
            chunks.append({
                "id": chunk_id,
                "text": f"{name}\n{piece}",
                "metadata": {
                    "type": "world_mechanic",
                    "name": name
                }
            })
    return chunks

if __name__ == "__main__":
    chunks = build_chunks()
    print(f"Built {len(chunks)} world_mechanic chunks from "
          f"{len(glob.glob(f'{MECHANICS_DIR}/*.json'))} source pages")

    if chunks:
        add_source(SOURCE_ID, chunks)
    else:
        print("No chunks to add.")