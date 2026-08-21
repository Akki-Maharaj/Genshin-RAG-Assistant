import json
import numpy as np
import os
from sentence_transformers import SentenceTransformer
from datetime import datetime

INDEX_DIR = "index"
MANIFEST_PATH = f"{INDEX_DIR}/manifest.json"
EMBEDDINGS_PATH = f"{INDEX_DIR}/embeddings.npy"
CHUNKS_PATH = f"{INDEX_DIR}/chunks_meta.jsonl"

def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"indexed_sources": {}, "total_chunks": 0, "last_updated": None}

def save_manifest(manifest):
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def load_index():
    if not os.path.exists(EMBEDDINGS_PATH):
        return np.array([]), []
    embeddings = np.load(EMBEDDINGS_PATH)
    chunks = []
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    return embeddings, chunks

def save_index(embeddings, chunks):
    os.makedirs(INDEX_DIR, exist_ok=True)
    np.save(EMBEDDINGS_PATH, embeddings)
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

def embed_chunks(model, new_chunks, batch_size=64):
    texts = [c["text"] for c in new_chunks]
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        embeddings = model.encode(batch, show_progress_bar=False)
        all_embeddings.append(embeddings)
        print(f"  Embedded {min(i + batch_size, len(texts))}/{len(texts)}")
    return np.vstack(all_embeddings)

def add_source(source_id, new_chunks, model=None):
    manifest = load_manifest()

    if source_id in manifest["indexed_sources"]:
        print(f"Source '{source_id}' already indexed. Use update_source() to update it.")
        return

    if model is None:
        print("Loading embedding model...")
        model = SentenceTransformer("all-MiniLM-L6-v2")

    print(f"Embedding {len(new_chunks)} chunks for source '{source_id}'...")
    new_embeddings = embed_chunks(model, new_chunks)

    existing_embeddings, existing_chunks = load_index()

    if len(existing_embeddings) == 0:
        combined_embeddings = new_embeddings
        combined_chunks = new_chunks
    else:
        combined_embeddings = np.vstack([existing_embeddings, new_embeddings])
        combined_chunks = existing_chunks + new_chunks

    save_index(combined_embeddings, combined_chunks)

    manifest["indexed_sources"][source_id] = {
        "chunk_count": len(new_chunks),
        "added": datetime.now().isoformat(),
        "start_idx": len(existing_chunks)
    }
    manifest["total_chunks"] = len(combined_chunks)
    manifest["last_updated"] = datetime.now().isoformat()
    save_manifest(manifest)

    print(f"Done. Index now has {len(combined_chunks)} total chunks.")
    return model

def update_source(source_id, new_chunks, model=None):
    manifest = load_manifest()

    if source_id not in manifest["indexed_sources"]:
        print(f"Source '{source_id}' not found. Use add_source() instead.")
        return

    if model is None:
        print("Loading embedding model...")
        model = SentenceTransformer("all-MiniLM-L6-v2")

    print(f"Updating source '{source_id}' with {len(new_chunks)} new chunks...")

    existing_embeddings, existing_chunks = load_index()

    old_start = manifest["indexed_sources"][source_id]["start_idx"]
    old_count = manifest["indexed_sources"][source_id]["chunk_count"]

    keep_chunks = [c for i, c in enumerate(existing_chunks)
                   if not (old_start <= i < old_start + old_count)]
    keep_embeddings = np.delete(existing_embeddings,
                                range(old_start, old_start + old_count), axis=0)

    new_embeddings = embed_chunks(model, new_chunks)

    combined_embeddings = np.vstack([keep_embeddings, new_embeddings])
    combined_chunks = keep_chunks + new_chunks

    save_index(combined_embeddings, combined_chunks)

    manifest["indexed_sources"][source_id] = {
        "chunk_count": len(new_chunks),
        "updated": datetime.now().isoformat(),
        "start_idx": len(keep_chunks)
    }
    manifest["total_chunks"] = len(combined_chunks)
    manifest["last_updated"] = datetime.now().isoformat()
    save_manifest(manifest)

    print(f"Done. Index now has {len(combined_chunks)} total chunks.")
    return model

def print_status():
    manifest = load_manifest()
    print(f"\nIndex Status:")
    print(f"  Total chunks: {manifest['total_chunks']}")
    print(f"  Last updated: {manifest['last_updated']}")
    print(f"\n  Sources:")
    for src_id, info in manifest["indexed_sources"].items():
        action = "updated" if "updated" in info else "added"
        date = info.get("updated", info.get("added", "unknown"))
        print(f"    {src_id}: {info['chunk_count']} chunks ({action}: {date[:10]})")