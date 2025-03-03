from fastapi import FastAPI
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to BabyNutriAI!"}

@app.post("/recommend")
def recommend_nutrition(data: dict):
    baby_age = data.get("age", "unknown")
    baby_diet = data.get("diet", "unknown")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a baby nutrition assistant."},
            {"role": "user", "content": f"My baby is {baby_age} months old and eats {baby_diet}. What should I feed next?"}
        ]
    )

    # Convert response to dictionary
    response_dict = response.model_dump()

    return {
        "age": baby_age,
        "current diet": baby_diet,
        "recommendation": response_dict["choices"][0]["message"]["content"]
        }
