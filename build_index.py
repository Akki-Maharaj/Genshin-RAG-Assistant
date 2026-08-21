
import json
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

CHUNKS_FILE = Path("chunks.jsonl")
INDEX_FILE = Path("faiss_index.bin")
STORE_FILE = Path("chunk_store.json")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 64

print("Loading chunks...")
chunks = []
with open(CHUNKS_FILE, encoding="utf-8") as f:
    for line in f:
        chunks.append(json.loads(line))

print(f"  {len(chunks)} chunks loaded")

print(f"\nLoading embedding model: {EMBEDDING_MODEL}")
model = SentenceTransformer(EMBEDDING_MODEL)

print("\nEmbedding chunks (this may take a minute)...")
texts = [c["text"] for c in chunks]
embeddings = model.encode(
    texts,
    batch_size=BATCH_SIZE,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True,
)

print(f"\nEmbedding shape: {embeddings.shape}")

dim = embeddings.shape[1]
index = faiss.IndexFlatIP(dim)
index.add(embeddings.astype(np.float32))

print(f"FAISS index built: {index.ntotal} vectors")

faiss.write_index(index, str(INDEX_FILE))
print(f"Index saved to {INDEX_FILE}")

store = [{"id": c["id"], "text": c["text"], "metadata": c["metadata"]} for c in chunks]
with open(STORE_FILE, "w", encoding="utf-8") as f:
    json.dump(store, f, ensure_ascii=False, indent=2)
print(f"Chunk store saved to {STORE_FILE}")

print("\nDone. Run rag.py to query.")