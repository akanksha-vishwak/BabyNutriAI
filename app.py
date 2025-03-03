from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

# Define a request model
class ChatRequest(BaseModel):
    user_message: str

@app.get("/")
def home():
    return{"message": "Welcome to BabyNutriAI!"}

@app.post("/chat")
def chat_with_bot(request: ChatRequest):
    """
    Accepts user input and generates baby food recommendations using GPT-4.
    """
    
    response = client.chat.completions.create(
        model="gpt-4-turbo",  # Use "gpt-3.5-turbo" if needed
        messages=[
            {"role": "system", "content": "You are a baby nutrition assistant. Provide healthy meal recommendations based on age and available ingredients."},
            {"role": "user", "content": request.user_message}
        ]
    )

    return {"response": response.choices[0].message.content}
