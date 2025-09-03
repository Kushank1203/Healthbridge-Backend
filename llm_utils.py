# import os
# import requests
# from dotenv import load_dotenv

# load_dotenv()

# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# GROQ_MODEL = "llama-3.3-70b-versatile"
# GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# if not GROQ_API_KEY:
#     raise EnvironmentError("GROQ_API_KEY not found in environment. Please check your .env file.")

# def query_llm(prompt: str):
#     headers = {
#         "Authorization": f"Bearer {GROQ_API_KEY}",
#         "Content-Type": "application/json"
#     }

#     payload = {
#         "model": GROQ_MODEL,
#         "messages": [{"role": "user", "content": prompt}],
#         "temperature": 0.3,
#         "max_tokens": 1024
#     }

#     try:
#         response = requests.post(GROQ_API_URL, headers=headers, json=payload)
#         if response.status_code != 200:
#             print("Groq API Error:", response.status_code, response.text)
#             response.raise_for_status()
#         return response.json()["choices"][0]["message"]["content"]

#     except requests.exceptions.HTTPError as http_err:
#         print(f"HTTP error occurred: {http_err}")
#         return "LLM API failed with HTTP error."
#     except Exception as err:
#         print(f"Other error occurred: {err}")
#         return "LLM API failed due to an unexpected error."


import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY not found in environment. Please check your .env file.")

def query_llm(prompt: str):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a careful insurance claim adjudicator. Always return strict JSON when asked."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 1200
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    except Exception as err:
        print(f"LLM error: {err}")
        return '{"status":"query","approved_amount":null,"covered_items":[],"excluded_items":[],"reasoning":"LLM API failed; manual review."}'
