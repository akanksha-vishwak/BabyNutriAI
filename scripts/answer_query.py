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

from utils.fact_extraction import extract_facts_from_text, should_answer_from_memory
from utils.database import update_fact
from utils.database import init_facts_table
init_facts_table()
from utils.database import get_user_facts


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
        return any(allergen in text or allergen in ingredients for allergen in allergens)
    
    return [chunk for chunk in chunks if not contains_allergen(chunk)]

# === PROMPT BUILDING ===

def build_prompt(user_query, nhs_chunks, recipe_chunks, user_memory):
    memory_lines = []

    for chunk in recipe_chunks:
        chunk["chunk"] = f"Recipe: {chunk['title']}\n{chunk['chunk']}"
    
    if user_memory:
        if "baby_name" in user_memory:
            memory_lines.append(f'Baby name: {user_memory["baby_name"]}')
        if "baby_age_months" in user_memory:
            memory_lines.append(f'Baby age: {user_memory["baby_age_months"]} months')
        if "allergies" in user_memory and user_memory["allergies"]:
            memory_lines.append("Allergies: " + ", ".join(user_memory["allergies"]))

    memory_context = "\n".join(memory_lines) if memory_lines else ""

    context_chunks = nhs_chunks[:2] + recipe_chunks[:3]
    context = "\n\n".join(chunk["chunk"] for chunk in context_chunks)

    prompt = f"""You are a helpful baby nutrition assistant.
Answer the user's question using only the information in the context below and the stored information about the user.

- If the context contains any named recipes, write one full recipe and explain why it's appropriate.
- If the user clearly asked for meal suggestions, give a direct suggestion that avoids allergens.
- If the user only shared an allergy or fact but did not request anything, acknowledge it and ask if they want suggestions.
- Do not suggest foods that include the allergens stored for the user.
- Only mention 6-month solids introduction if relevant and not already stated.

            User question:
            {user_query}

            Stored user info:
            {memory_context}

            Context:
            {context}
            """
    return prompt, context_chunks

# === MAIN FUNCTION ===

def answer_query(user_query, user_memory=None):

    memory_keys = should_answer_from_memory(user_query)

    if memory_keys:
        missing = [k for k in memory_keys if k not in user_memory]
        if not missing:
            age = user_memory.get("baby_age_months")
            allergies = user_memory.get("allergies")
            parts = []

            if age:
                parts.append(f"{age} months old")
            if allergies:
                parts.append(f"allergic to {allergies}")

            fact_summary = " and ".join(parts)
            follow_up = "Would you like some meal ideas or guidance based on this?"

            return f"Thanks for sharing! I've saved that your baby is {fact_summary}. {follow_up}", []
        else:
            return "I don't have that info saved yet. Please tell me again.", []

    allergens = []
    if user_memory and "allergies" in user_memory:
        allergens = [a.lower() for a in user_memory["allergies"]]

    # 1. Embed and normalize query
    query_vector = model.encode([user_query], convert_to_numpy=True)

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
    prompt, used_chunks = build_prompt(user_query, nhs_chunks, recipe_chunks, user_memory)

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
    parser.add_argument("--user", required=True, help="User ID for memory")
    args = parser.parse_args()

    user_id = args.user
    user_query = args.query

    # 1. Extract facts from this query and store them
    facts = extract_facts_from_text(user_query)
    for key, value in facts.items():
        update_fact(user_id, key, value)

    # 2. Get stored memory (baby age, allergies, name)
    user_memory = get_user_facts(user_id)
    print("[DEBUG] User memory loaded:", user_memory)


    result, chunks = answer_query(args.query, user_memory)
    print("\n=== Answer ===\n")
    print(result)
    print("\n=== Chunks Used ===\n")
    for c in chunks:
        print(f"- {c.get('title')} ({c.get('source_type')}): {c.get('source_url')}")
