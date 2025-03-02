# 🍼 BabyNutriAI – AI-Powered Baby Nutrition Assistant  
**Personalized AI-driven baby food recommendations based on age, diet history, and nutritional guidelines.**  

## Overview  
NutriBabyAI is designed to help parents and caregivers make informed baby food choices using machine learning and AI. It leverages:  
- **LLMs (GPT-4)** for Natural Language Processing
- **Retrieval-Augmented Generation (RAG)** for factual recommendations  
- **FastAPI** for an interactive AI-powered chatbot
- **FAISS (vector search)** for efficient knowledge retrieval

This project is designed for **scalability** and can be integrated into mobile apps or parenting platforms.  

---

## How It Works  
1️. Parents enter **baby’s age & current diet**.  
2️. AI **retrieves real-world nutrition guidelines** and suggests meals.  
3️. The chatbot **remembers past meals** and adjusts future recommendations.  
4️. Data is **stored & analyzed** for personalized insights.  

---

## Tech Stack  
- **LLMs** – OpenAI API (GPT-4)  
- **Backend** – FastAPI  
- **Vector Search** – FAISS for RAG-based retrieval  
- **Database** – SQLite / Firebase (optional)  
- **Deployment** – Docker + Render  

---

## 📌 Getting Started  

### Clone the Repository  
```bash
git clone https://github.com/YOUR-USERNAME/NutriBabyAI.git
cd NutriBabyAI
pip install -r requirements.txt
uvicorn app:app --reload
```
API Endpoint:`http://127.0.0.1:8000/recommend`
