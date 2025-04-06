## Data Collection

### From NHS website

#### API Key

- The NHS Website Content API provides structured health data (conditions, symptoms, etc.).
- Most endpoints are open-access. No API key is required for read-only access.
- JSON responses are identical with or without authentication.
- I still registered the BabyNutriAI app and received API key and secret. Didn't use it though.

#### Scraping
Extract the urls from "https://www.nhs.uk/conditions/baby/weaning-and-feeding/":
- `trafilatura` didn't work so fallback to `bs4`

### Fixing SentenceTransformer + Transformers Error on macOS

#### Problem on Jupyter
When trying to use `SentenceTransformer`, an error occurs:
RuntimeError: Failed to import transformers.integrations.integration_utils... Your currently installed version of Keras is Keras 3, but this is not yet supported in Transformers.

This is caused by an incompatibility between:
- `transformers` (used by `sentence-transformers`)
- `Keras 3` (installed by default)
- Mac systems (especially with Python 3.11 or M1/M2 chips)

#### Solution

**Install tf-keras shim**

```bash
pip uninstall keras -y
pip install tf-keras
```

#### Problem and solution on Terminal 
- There were multiple errors with the version and what not
- final solution was to install these 
```bash

python3.11 -m pip install "sentence-transformers==2.2.2" "transformers==4.30.2" "huggingface_hub==0.14.1"
```

#### Retrieving
- In 1st attempt the answer for "meal option for 10 months with egg allergy" contained egg in the recipe
- Used LLM to generate answer from the chunks and it did a good job but did not pick up the answer from my data of recipes
- So, I chose to add fiters based on the age, allergy from ingredients 
- After this the answer was from my data but too much from nhs guideline no recipe
- Then I picked up 3 chunks from nhs and 3 from recipe making sure of the allergy and age
- This worked very well but needed to refine the prompt to actually write the recipe not just mention the name
- Answers look pretty good so far, tested for variety of questions. 
- All the tests can be referred in the 03... notebook







#### Want to do:
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
