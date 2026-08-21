
import json
import os
import glob
from index_manager import add_source

ARTIFACT_DIR = "dataset/artifacts"
SOURCE_ID = "artifact_lore_v1"

def extract_pieces(result):
    pieces_out = []
    for piece_key in ("flower", "plume", "sands", "goblet", "circlet"):
        piece_data = result.get(piece_key)
        if not isinstance(piece_data, dict):
            continue
        piece_name = piece_data.get("name", piece_key)
        story = (piece_data.get("story") or "").strip()
        description = (piece_data.get("description") or "").strip()
        lore_text = story if story else description
        if lore_text:
            pieces_out.append((piece_key, piece_name, lore_text))
    return pieces_out

def build_chunks():
    chunks = []
    skipped = []

    for path in sorted(glob.glob(f"{ARTIFACT_DIR}/*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        result = data.get("result", data)
        set_name = result.get("name")
        pieces = extract_pieces(result)

        if not set_name or not pieces:
            skipped.append(os.path.basename(path))
            continue

        for piece_key, piece_name, lore_text in pieces:
            chunk_id = f"artifact_lore_{set_name.lower().replace(' ', '_')}_{piece_key}"
            chunks.append({
                "id": chunk_id,
                "text": f"Artifact Lore: {piece_name} ({set_name} — {piece_key})\n{lore_text}",
                "metadata": {
                    "type": "artifact_lore",
                    "name": set_name,
                    "piece": piece_key,
                    "piece_name": piece_name
                }
            })

    return chunks, skipped

if __name__ == "__main__":
    total_files = len(glob.glob(f"{ARTIFACT_DIR}/*.json"))
    chunks, skipped = build_chunks()

    print(f"Scanned {total_files} artifact files")
    print(f"Built {len(chunks)} artifact_lore chunks")

    if len(chunks) == 0:
        print("\nNo lore text found in any artifact file under any known field name.")
        print("This means artifact lore is NOT sitting unused in your existing data —")
        print("unlike weapons, it genuinely needs a Fandom wiki scrape. Sample keys")
        print("from the first file, to help figure out the real field names:")
        first = sorted(glob.glob(f"{ARTIFACT_DIR}/*.json"))
        if first:
            with open(first[0], encoding="utf-8") as f:
                d = json.load(f)
            print(list((d.get("result", d)).keys()))
    else:
        if skipped:
            print(f"Skipped {len(skipped)} files with no lore found: {skipped[:10]}"
                  f"{' ...' if len(skipped) > 10 else ''}")
        add_source(SOURCE_ID, chunks)