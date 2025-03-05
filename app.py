from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from openai import OpenAI
import faiss
import numpy as np
import json

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

# check if faiss index file exists
if not os.path.exists("recipe_index.faiss"):
    raise RuntimeError("FAISS index file is missing! Run `vector_store.py` first.")

# load faiss index
index = faiss.read_index("recipe_index.faiss")

# load recipe database
with open("recipes.json", "r") as f:
    recipes = json.load(f)["recipes"]

# Needed to parse the request body instead of a query parameter
class ChatRequest(BaseModel):
    user_message: str

# convert query to embedding
def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32)

# find closest recipe match in faiss
def search_recipes(query):
    query_embedding = get_embedding(query).reshape(1, -1) 
    _, indices = index.search(query_embedding, 2) # return 2 closest recipes
    return [recipes[i] for i in indices[0] if i < len(recipes)] 

@app.get("/")
def home():
    return{"message": "Welcome to BabyNutriAI!"}

@app.post("/chat")
def chat_with_bot(request: ChatRequest):
    """
    Accepts user input and generates baby food recommendations using GPT-4.
    """

    # Extract structured data from user message
    extraction_prompt = f"""
    Extract structured data from the following user message:
    "{request.user_message}"

    Return a JSON object with:
    - "age": Baby's age in months (if mentioned, otherwise null).
    - "ingredients": A list of food ingredients mentioned (if any, otherwise empty list).
    - "query_type": Either "meal_recommendation" (if the user wants a food suggestion) or "general_advice" (if they are asking about baby food guidelines).
    """

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Extract structured data from free-text input."},
            {"role": "user", "content": extraction_prompt}
        ]
    )   
    extracted_info = json.loads(response.choices[0].message.content.strip())

    #Search FAISS for relevant baby meals
    query = f"Baby {extracted_info['age']} months, ingredients: {extracted_info['ingredients']}"
    matched_recipes = search_recipes(query)

    # Step 3: Use retrieved recipes to generate response
    response_prompt = f"""
    Based on the retrieved recipes: {matched_recipes}
    Generate a helpful response for the parent.
    """

    final_response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a baby nutrition assistant."},
            {"role": "user", "content": response_prompt}
        ]
    )

    return {"response": final_response.choices[0].message.content}

