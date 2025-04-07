from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from utils.fact_extraction import extract_facts_from_text
from utils.database import init_db, update_fact, get_user_facts, save_memory
from scripts.answer_query import answer_query

import openai
from dotenv import load_dotenv
import os

# === LOAD ENV ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


# Init DB tables
init_db()

# FastAPI setup
app = FastAPI(title="BabyNutriAI Backend")

# Allow local frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:8501"] for Streamlit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def classify_intent(message: str) -> str:
    system_prompt = "You are a simple classifier for a baby nutrition assistant."
    user_prompt = f"""
Classify this user message into one of the following categories:
- greeting
- nutrition_query
- general_chat
- unclear

User message: "{message}"

Just return one word, no explanation.
"""

    result = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return result.choices[0].message.content.strip().lower()


# Request schema
class ChatRequest(BaseModel):
    user_id: str
    user_message: str

@app.post("/chat")
def chat(req: ChatRequest):
    user_id = req.user_id
    user_message = req.user_message
    intent = classify_intent(user_message)

    if intent == "greeting":
        return {"response": "Hi there! How can I help you today with baby nutrition or feeding questions?"}

    elif intent == "general_chat":
        return {"response": "I'm here to help with baby food, feeding, allergies, and nutrition questions. Ask me anything!"}

    elif intent == "unclear":
        return {"response": "Could you rephrase that? I'm not sure I understood your question about baby nutrition."}

    # Only if it's a nutrition query, continue
    # (your existing logic below)
    facts = extract_facts_from_text(user_message)
    existing_facts = get_user_facts(user_id)

    for key, value in facts.items():
        if value and (existing_facts.get(key) != value):
            update_fact(user_id, key, value)

    memory = get_user_facts(user_id)
    result, chunks = answer_query(user_message, memory)

    save_memory(user_id, user_message, result)

    return {"response": result}
