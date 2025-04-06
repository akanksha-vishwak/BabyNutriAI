import os
os.environ["OMP_NUM_THREADS"] = "1" # Limit OpenMP threads to avoid performance issues
os.environ["TOKENIZERS_PARALLELISM"] = "false" # Disable parallelism for tokenizers to avoid warnings
import json
import numpy as np
import faiss
import argparse
from sentence_transformers import SentenceTransformer
import openai
from dotenv import load_dotenv

# === CONFIG ===
DATA_DIR = "data/combined"
INDEX_PATH = os.path.join(DATA_DIR, "faiss_index.index")
METADATA_PATH = os.path.join(DATA_DIR, "chunk_metadata.json")
EMBEDDINGS_DIM = 384  # for MiniLM
TOP_K = 6

# === LOAD ENV ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# === LOAD MODEL & INDEX ===
model = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")
index = faiss.read_index(INDEX_PATH)

with open(METADATA_PATH, "r", encoding="utf-8") as f:
    chunk_metadata = json.load(f)

# === FILTERING ===

def filter_chunks_by_allergens(chunks, allergens):
    def contains_allergen(chunk):
        text = chunk.get("chunk", "").lower()
        ingredients = " ".join(chunk.get("ingredients", [])).lower() if "ingredients" in chunk else ""
        return any(allergen.lower() in text or allergen.lower() in ingredients for allergen in allergens)
    
    return [chunk for chunk in chunks if not contains_allergen(chunk)]

# === PROMPT BUILDING ===

def build_prompt(user_query, nhs_chunks, recipe_chunks):
    for chunk in recipe_chunks:
        chunk["chunk"] = f"Recipe: {chunk['title']}\n{chunk['chunk']}"
    
    context_chunks = nhs_chunks[:3] + recipe_chunks[:2]
    context = "\n\n".join(chunk["chunk"] for chunk in context_chunks)

    prompt = f"""You are a helpful baby nutrition assistant.

Answer the user's question using only the information in the context below.
If the context contains any named recipes, write one full recipe and explain why they are appropriate.
Only if the question has no age mentioned, clearly state that solids are typically introduced at 6 months of age.
If the context includes allergens that must be avoided, do not mention those foods and suggest safe alternatives.

User question:
{user_query}

Context:
{context}
"""
    return prompt, context_chunks

# === MAIN FUNCTION ===

def answer_query(user_query, allergens=None):
    # 1. Embed and normalize query
    query_vector = model.encode([user_query], convert_to_numpy=True)
    # query_vector = query_vector / np.linalg.norm(query_vector, axis=1, keepdims=True)

    # 2. Search FAISS
    D, I = index.search(query_vector, k=TOP_K)
    retrieved_chunks = [chunk_metadata[i] for i in I[0]]

    # 3. Apply allergen filter
    if allergens:
        retrieved_chunks = filter_chunks_by_allergens(retrieved_chunks, allergens)

    # 4. Separate sources
    nhs_chunks = [c for c in retrieved_chunks if c.get("source_type") == "nhs"]
    recipe_chunks = [c for c in retrieved_chunks if c.get("source_type") == "recipe"]

    # 5. Build prompt
    prompt, used_chunks = build_prompt(user_query, nhs_chunks, recipe_chunks)

    # 6. Call OpenAI
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful baby nutrition assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    final_answer = response.choices[0].message.content
    return final_answer, used_chunks

# === CLI ===

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True, help="The user query to answer")
    parser.add_argument("--allergens", nargs="*", default=[], help="List of allergens to avoid (e.g. egg milk)")
    args = parser.parse_args()

    result, chunks = answer_query(args.query, args.allergens)
    print("\n=== Answer ===\n")
    print(result)
    print("\n=== Chunks Used ===\n")
    for c in chunks:
        print(f"- {c.get('title')} ({c.get('source_type')}): {c.get('source_url')}")
