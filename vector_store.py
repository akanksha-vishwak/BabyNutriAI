import json
import faiss
import os
from dotenv import load_dotenv
from openai import OpenAI
import numpy as np

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

with open("recipes.json", "r") as f:
      recipes = json.load(f)["recipes"]

#Convert each recipe into an embedding
def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32)

# Create a list of recipe embeddings
recipe_texts = [f"{r['name']} - {r['ingredients']} - {r['instructions']}" for r in recipes]
recipe_embeddings = np.array([get_embedding(text) for text in recipe_texts])

# Create a Faiss index
index = faiss.IndexFlatL2(recipe_embeddings.shape[1])
index.add(recipe_embeddings)

# Save the index
faiss.write_index(index, "recipe_index.faiss")