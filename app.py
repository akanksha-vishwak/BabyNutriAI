from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
import faiss
import numpy as np
import json
import os
import uuid
from database import init_db, save_memory, get_past_messages

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize FastAPI app
app = FastAPI(title="BabyNutri AI", description="AI-powered baby nutrition chatbot", version="1.0")

# Ensure FAISS index exists
FAISS_INDEX_PATH = "recipe_index.faiss"
if not os.path.exists(FAISS_INDEX_PATH):
    raise RuntimeError("FAISS index file is missing! Run `vector_store.py` first.")

index = faiss.read_index(FAISS_INDEX_PATH)

# Load recipe dataset
RECIPE_FILE_PATH = "recipes.json"
if not os.path.exists(RECIPE_FILE_PATH):
    raise RuntimeError("Recipes file is missing! Ensure `recipes.json` is in the project directory.")

with open(RECIPE_FILE_PATH, "r") as f:
    recipes = json.load(f)["recipes"]


# Request model for chatbot input
class ChatRequest(BaseModel):
    """Schema for chatbot request"""
    user_id: str  # Unique identifier for user
    user_message: str


# Extract structured data from user input
def extract_info(user_message: str) -> dict:
    """
    Extracts structured data from user message using OpenAI.
    
    Returns:
        dict: Extracted information with `age` and `ingredients` keys.
    """
    prompt = f"""
    Extract structured data from the following user message:
    "{user_message}"

    Strictly return a JSON object **only** in this format:
    {{
      "age": (integer or null),
      "ingredients": (list of strings)
    }}

    Do NOT include explanations or extra text, only return a valid JSON.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        raw_response = response.choices[0].message.content.strip()
        extracted_data = json.loads(raw_response)
        
        if not isinstance(extracted_data, dict):
            raise ValueError("Invalid JSON structure received.")

        return extracted_data

    except (json.JSONDecodeError, ValueError) as e:
        print(f"JSON Parsing Failed: {e}")
        return {"age": None, "ingredients": []}  # Return default empty structure


# Search for matching recipes in FAISS
def search_recipes(ingredients: list) -> list:
    """
    Searches FAISS index for recipes that match given ingredients.

    Args:
        ingredients (list): List of ingredient names.

    Returns:
        list: Top matching recipes.
    """
    if not ingredients:
        return []  # Return empty if no ingredients are provided

    try:
        query_embedding = np.array(client.embeddings.create(
            model="text-embedding-ada-002",
            input=", ".join(ingredients)
        ).data[0].embedding, dtype=np.float32).reshape(1, -1)

        _, indices = index.search(query_embedding, 2)  # Get top 2 matches
        return [recipes[i] for i in indices[0] if i < len(recipes)]

    except Exception as e:
        print(f"FAISS Search Error: {e}")
        return []  # Return empty if there's an error


# Chatbot endpoint
@app.post("/chat", summary="Get baby food recommendations")
def chat_with_bot(request: ChatRequest):
    """
    Handles chatbot requests and generates baby nutrition suggestions.

    Args:
        request (ChatRequest): Contains `user_id` and `user_message`.

    Returns:
        dict: AI-generated baby food recommendations.
    """
    try:
        user_id = request.user_id
        user_message = request.user_message

        # Retrieve past messages for memory
        past_messages = get_past_messages(user_id)
        print(f"Past Messages for {user_id}: {past_messages}")

        # Extract structured data (age & ingredients)
        extracted_data = extract_info(user_message)
        print(f"Extracted Data: {extracted_data}")

        # Validate extracted data
        if not isinstance(extracted_data, dict) or "age" not in extracted_data or "ingredients" not in extracted_data:
            raise ValueError("Extracted data format is invalid!")

        # Search for matching recipes
        matched_recipes = search_recipes(extracted_data.get("ingredients", []))
        print(f"Matched Recipes: {matched_recipes}")

        # Construct AI response prompt
        response_prompt = f"""
        Past Messages: {past_messages}

        User Message: "{user_message}"

        Based on ingredients {extracted_data.get('ingredients', [])} and matched recipes: {matched_recipes},
        suggest a nutritious meal for a baby aged {extracted_data.get('age', 'unknown')} months.
        Avoid repeating past recommendations.
        """

        # Generate AI response
        final_response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": "You are a baby nutrition expert."},
                      {"role": "user", "content": response_prompt}]
        )

        # Ensure valid OpenAI response
        if not final_response.choices:
            raise HTTPException(status_code=500, detail="Failed to generate a response. Please try again.")

        bot_reply = final_response.choices[0].message.content.strip()
        print(f"AI Response: {bot_reply}")

        # Save conversation to memory
        save_memory(user_id, user_message, bot_reply)

        return {"response": bot_reply}

    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# Health check endpoint
@app.get("/", summary="Health Check")
def home():
    return {"message": "BabyNutri AI is running!"}