import os
import re
import concurrent.futures
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# The primary models from the list
models_to_test = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it",
]

print(f"{'Model':<25} | {'Status':<16} | {'Details'}", flush=True)
print("-" * 78, flush=True)

def test_model(m_name):
    return client.models.generate_content(
        model=m_name,
        contents="Say 'ready'",
    )

for model_id in models_to_test:
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(test_model, model_id)
        try:
            resp = future.result(timeout=6.0)
            text = (resp.text or "").strip().replace('\n', ' ')
            print(f"{model_id:<25} | {'RESPONDED':<16} | Output: {text[:40]}", flush=True)
        except concurrent.futures.TimeoutError:
            print(f"{model_id:<25} | {'TIMEOUT (>6s)':<16} | Endpoint did not respond within 6s", flush=True)
        except Exception as e:
            err = str(e)
            if "404" in err or "NOT_FOUND" in err:
                print(f"{model_id:<25} | {'404 NOT FOUND':<16} | Retired / unavailable", flush=True)
            elif "429" in err or "RESOURCE_EXHAUSTED" in err:
                info = "Quota exhausted"
                m = re.search(r"'quotaId': '([^']+)'", err)
                if m:
                    info += f" ({m.group(1)})"
                m_val = re.search(r"'quotaValue': '([^']+)'", err)
                if m_val:
                    info += f" limit={m_val.group(1)}/day"
                print(f"{model_id:<25} | {'429 EXHAUSTED':<16} | {info}", flush=True)
            elif "500" in err:
                print(f"{model_id:<25} | {'500 SERVER ERR':<16} | Internal error", flush=True)
            else:
                clean_err = err.replace('\n', ' ')[:45]
                print(f"{model_id:<25} | {'ERROR':<16} | {clean_err}", flush=True)
