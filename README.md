# 🍼 BabyNutriAI – AI-Powered Baby Nutrition Assistant  
**Personalized AI-driven baby food recommendations based on age, diet history, and nutritional guidelines.**  

🔗 **Live Demo (Coming Soon)** | 📖 **[Project Documentation](#)** | ⭐ *Give a Star if you like this project!*  

---

## 🌟 Features  
✅ **Smart Baby Food Recommendations** – AI suggests the best foods based on age & diet.  
✅ **Retrieval-Augmented Generation (RAG)** – Fetches **real nutrition facts** instead of hallucinating answers.  
✅ **FastAPI-Powered Chatbot** – Get instant, AI-driven nutrition advice.  
✅ **Memory & History Tracking** – Remembers past food intake to avoid repetition.  
✅ **Embeddings & Vector Search** – Uses FAISS for knowledge retrieval.  
✅ **Deployable API** – Can be integrated into mobile apps or parenting platforms.  

---

## 🚀 How It Works  
1️⃣ Parents enter **baby’s age & current diet**.  
2️⃣ AI **retrieves real-world nutrition guidelines** and suggests meals.  
3️⃣ The chatbot **remembers past meals** and adjusts future recommendations.  
4️⃣ Data is **stored & analyzed** for personalized insights.  

---

## 🔧 Tech Stack  
- **LLMs** – OpenAI API (GPT-4)  
- **Backend** – FastAPI  
- **Vector Search** – FAISS for RAG-based retrieval  
- **Database** – SQLite / Firebase (optional)  
- **Deployment** – Docker + Render  

---

## 📌 Getting Started  

### 1️⃣ Clone the Repository  
```bash
git clone https://github.com/YOUR-USERNAME/NutriBabyAI.git
cd NutriBabyAI
pip install -r requirements.txt
uvicorn app:app --reload
```
API Endpoint:`http://127.0.0.1:8000/recommend`
