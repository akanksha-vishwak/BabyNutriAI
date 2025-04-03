import streamlit as st
import requests

# FastAPI backend URL
FASTAPI_URL = "http://127.0.0.1:8000/chat"  # Change this to your deployed API URL

st.title("BabyNutri AI 👶🍲🤖 - Smart Baby Nutrition Assistant")

st.write(
    "Welcome! Ask me about baby nutrition. Example: "
    "*'My baby is 8 months old. I have carrots and rice. What can I cook?'*"
)

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Ask a question about baby nutrition...")

if user_input:
    # Update session state before API call
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Make API request to FastAPI
    response = requests.post(FASTAPI_URL, json={"user_id": "user123", "user_message": user_input})

    if response.status_code == 200:
        bot_reply = response.json()["response"]
    else:
        bot_reply = "Error: Unable to get a response. Check FASTAPI backend URL"

    # Append bot response to session state
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    st.rerun()
