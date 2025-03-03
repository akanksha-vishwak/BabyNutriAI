from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

# Needed to parse the request body instead of a query parameter
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
    extracted_info = response.choices[0].message.content.strip()
    return {"structured_data": extracted_info}

