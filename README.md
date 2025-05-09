# BabyNutriAI – AI-Powered Baby Nutrition Assistant  
**Personalized AI-driven baby food recommendations based on age, diet history, and nutritional guidelines.**  

## Overview  
BabyNutriAI is designed to help parents and caregivers make informed baby food choices using machine learning and AI. It leverages:  
- LLMs (GPT-4) for Natural Language Processing
- Retrieval-Augmented Generation (RAG) for factual recommendations  
- FastAPI for an interactive AI-powered chatbot
- FAISS (vector search) for efficient knowledge retrieval

---

## How It Works  
1. Parents enter baby’s age & current diet.  
2. AI retrieves real-world nutrition guidelines and suggests meals.  
3. The chatbot remembers past meals and adjusts future recommendations.  
4. Data is stored & analyzed for personalized insights.  

---

## Tech Stack  
- **LLMs** – OpenAI API (GPT-4)  
- **Backend** – FastAPI  
- **Vector Search** – FAISS for RAG-based retrieval  
- **Database** – SQLite 
- **Deployment** – Docker

---

## Getting Started  

### Clone the Repository  
```bash
git clone https://github.com/akanksha-vishwak/BabyNutriAI.git
cd BabyNutriAI
pip install -r requirements.txt
uvicorn app:app --reload
```

