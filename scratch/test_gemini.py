import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

for m in ["gemini-2.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-latest"]:
    try:
        r = client.models.generate_content(model=m, contents="Respond with JSON: {\"status\": \"ok\"}")
        print(f"{m}: SUCCESS -> {r.text[:30]}")
    except Exception as e:
        print(f"{m}: FAILED -> {str(e)[:60]}")
