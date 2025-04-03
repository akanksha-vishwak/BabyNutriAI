### Want to do:
improve the quality of input by reading NHS 
can read a text file?
response to simple "hi" is a big reply. handle greetings and questions 
If the user mentions different ages in multiple queries, the chatbot does not remember the last mentioned age.


### Things I learned:

1. Switched to Request Body instead of query parameter
    (I had to use `def chat_with_bot(request: ChatRequest):` instead of `def chat_with_bot(usert_message: str):`)
    - FastAPI allows data to be sent in two ways:
        1. Query Parameters (/chat?user_message=Hello)
        Passed directly in the URL.
        Good for short, simple inputs like filters or settings.

        2. Request Body (JSON: {"user_message": "Hello"})
        Passed inside the request payload (more structured).
        Good for complex inputs (like user messages, objects, multiple fields).

2. Extract the information so that GPT-4 sees a controlled version which improves response accuracy and also prepare for RAG

3. The langchain flow is updated recently so my old knowledge is not useful. I read the langgraph but will make a new project to implement this. Here I will fallback to the SQL database only. 

4. Created the docker image:
sha256:06be5c82c1e799c71adef670cf343ba82925c5c8cb9c980d0fd46ac9a00ae6d1
```
docker build -t babynutriai .     
docker run -p 8000:8000 -p 8501:8501 babynutriai
docker login
docker tag babynutriai aksvishwak/babynutriai
docker push aksvishwak/babynutriai 
```
docker login can be successful but can throw the error in pushing. Logout and login again.


Learnings from NHS Website Content Integration

## NHS Website Content Integration

### API Access vs. Public Website

- The NHS Website Content API provides structured health data (conditions, symptoms, etc.).
- Most endpoints are open-access.
- No API key is required for read-only access.
- JSON responses are identical with or without authentication.

### API Key and App Registration

- Successfully registered the BabyNutriAI app and received API key and secret.
- API key is not necessary for public content but may be needed for other restricted services in the future.

### Public Website Scraping

- Many baby-related articles (e.g., weaning, first foods) are available at `https://www.nhs.uk/conditions/...`
- These can be accessed using basic HTTP requests.
- Content can be parsed using tools like `BeautifulSoup` or `Trafilatura`.
