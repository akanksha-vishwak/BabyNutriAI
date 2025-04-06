import os
os.environ["OMP_NUM_THREADS"] = "1"
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# === SETTINGS ===
DATA_DIR = "data/combined"
#input
CHUNKS_PATH = os.path.join(DATA_DIR, "all_chunks.json")
#output
INDEX_PATH = os.path.join(DATA_DIR, "faiss_index.index")
METADATA_OUTPUT_PATH = os.path.join(DATA_DIR, "chunk_metadata.json")
EMBEDDINGS_OUTPUT_PATH = os.path.join(DATA_DIR, "embeddings.npy")
os.makedirs(DATA_DIR, exist_ok=True)

# === LOAD MODEL ===
print("Loading embedding model...")
model = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")

# === LOAD CHUNKS ===
print(f"Loading chunks from {CHUNKS_PATH}")
with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)

texts = [chunk["chunk"] for chunk in chunks]

# === EMBED & NORMALIZE ===
print(f"Embedding {len(texts)} chunks...")
embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

# Normalize to unit vectors (for cosine similarity)
# print("Normalizing vectors...")
# embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

# Save raw embeddings (could be used for tuning)
print(f"Saving raw embeddings to {EMBEDDINGS_OUTPUT_PATH}")
np.save(EMBEDDINGS_OUTPUT_PATH, embeddings)

# === BUILD FAISS INDEX ===
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# === SAVE INDEX ===
print(f"Saving FAISS index to {INDEX_PATH}")
faiss.write_index(index, INDEX_PATH)

# Save metadata
print(f"Saving chunk metadata to {METADATA_OUTPUT_PATH}")
with open(METADATA_OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(chunks, f, indent=2, ensure_ascii=False)

print(f"Done. Indexed {len(texts)} chunks with dimension {dimension}.")
