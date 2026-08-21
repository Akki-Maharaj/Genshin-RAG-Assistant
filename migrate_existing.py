import json
from index_manager import add_source
from sentence_transformers import SentenceTransformer

print("Migrating existing chunks into managed index...")

chunks = []
with open("chunks.jsonl", encoding="utf-8") as f:
    for line in f:
        chunks.append(json.loads(line))

print(f"Found {len(chunks)} existing chunks")

model = SentenceTransformer("all-MiniLM-L6-v2")

import numpy as np
import os
if os.path.exists("index/embeddings.npy"):
    existing = np.load("index/embeddings.npy")
    if len(existing) == len(chunks):
        print("Embeddings already exist and match chunk count.")
        print("Registering in manifest without re-embedding...")
        from index_manager import load_manifest, save_manifest, save_index
        import datetime
        embeddings = existing
        manifest = load_manifest()
        manifest["indexed_sources"]["core_dataset_v1"] = {
            "chunk_count": len(chunks),
            "added": datetime.datetime.now().isoformat(),
            "start_idx": 0
        }
        manifest["total_chunks"] = len(chunks)
        manifest["last_updated"] = datetime.datetime.now().isoformat()
        save_manifest(manifest)
        save_index(embeddings, chunks)
        print("Done. No re-embedding needed.")
    else:
        print("Chunk count mismatch — re-embedding...")
        add_source("core_dataset_v1", chunks, model=model)
else:
    print("No existing embeddings — embedding now...")
    add_source("core_dataset_v1", chunks, model=model)

print("Migration complete.")