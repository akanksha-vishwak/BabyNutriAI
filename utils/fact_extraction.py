import openai
from dotenv import load_dotenv
import os
import json

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_facts_from_text(user_message):
    system_prompt = """You are a helpful assistant. 
From the user's message, extract structured information in JSON format.

Supported fields:
- baby_age_months (integer)
- allergies (list of strings)
- baby_name (string, optional)

If no information is present, return an empty JSON object: {}

Only return the JSON. No other explanation.
"""

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.0
    )

    try:
        content = response.choices[0].message.content.strip()
        facts = json.loads(content)
        return facts if isinstance(facts, dict) else {}
    except Exception as e:
        print("Error extracting facts:", e)
        return {}

def should_answer_from_memory(user_query):
    system_prompt = """You are an assistant that decides if a user's question can be answered directly from stored profile information.

Supported fields:
- baby_age_months
- allergies
- baby_name

If the question is asking about any of these, return only the key(s) from this list.
If not, return an empty list.

Respond with a valid JSON array of strings. Example:
["baby_age_months", "allergies"]
"""

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        temperature=0.0
    )

    try:
        content = response.choices[0].message.content.strip()
        return json.loads(content)
    except Exception as e:
        print("Error deciding memory use:", e)
        return []
