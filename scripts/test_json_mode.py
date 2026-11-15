import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

test_models = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3-flash-preview"]
for m in test_models:
    try:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0,
            max_output_tokens=100
        )
        res = client.models.generate_content(
            model=m,
            contents='Return a JSON object with a single key "status" and value "ok"',
            config=config
        )
        print(f"{m} JSON MODE SUCCESS: {res.text.strip()}", flush=True)
    except Exception as e:
        print(f"{m} JSON MODE FAILED: {str(e)[:150]}", flush=True)
