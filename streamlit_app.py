import streamlit as st
import requests

# === Config ===
FASTAPI_URL = "http://127.0.0.1:8000/chat"

# === Page settings ===
st.set_page_config(page_title="BabyNutriAI")
st.title("BabyNutriAI - Baby Nutrition Assistant")

# === User ID input ===
user_id = st.text_input("Enter your name or ID", value="guest")

# === Session state setup ===
if "messages" not in st.session_state:
    st.session_state.messages = []

if "intent" not in st.session_state:
    st.session_state.intent = {}

# === Display chat history ===
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# === Chat input ===
user_input = st.chat_input("Ask something about baby feeding, allergies, or meal ideas...")

if user_input:
    # Pre-process input for follow-up handling
    cleaned = user_input.strip().lower()
    intent = st.session_state.get("intent", {})

    if cleaned in {"yes", "ok", "okay", "sure"} and intent.get("next_expected_action") == "suggest_safe_meal":
        allergen = intent.get("based_on_allergen", "some allergens")
        user_input = f"My baby is allergic to {allergen}. Can you suggest a safe meal?"
        st.session_state.intent = {}

    # Save user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Call FastAPI backend
    try:
        response = requests.post(
            FASTAPI_URL,
            json={"user_id": user_id, "user_message": user_input}
        )

        if response.status_code == 200:
            bot_reply = response.json()["response"]

            # Detect intent follow-ups from response
            if "would you like" in bot_reply.lower() and "allergic to" in bot_reply.lower():
                # Try to extract allergen mentioned earlier from user input
                if "allergic to" in user_input.lower():
                    allergen = user_input.lower().split("allergic to")[-1].split()[0]
                else:
                    allergen = "certain ingredients"

                st.session_state.intent = {
                    "next_expected_action": "suggest_safe_meal",
                    "based_on_allergen": allergen
                }

        else:
            bot_reply = f"Server error: {response.status_code}"

    except Exception as e:
        bot_reply = "Connection error. Make sure the FastAPI server is running."

    # Save assistant response
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    # Refresh to re-render chat
    st.rerun()
