import os
import re
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Get all models that support generateContent
available_models = []
try:
    for m in client.models.list():
        actions = getattr(m, 'supported_actions', []) or []
        if 'generateContent' in actions:
            clean_name = m.name.replace('models/', '')
            # Filter for text models, exclude vision/audio/tts/image-specific
            if not any(x in clean_name for x in ['image', 'tts', 'transcribe', 'live', 'native-audio', 'computer-use', 'robotics', 'banana', 'embedding']):
                available_models.append(clean_name)
except Exception as e:
    print(f"Error listing models: {e}", flush=True)

print(f"Discovered candidate text models: {available_models}", flush=True)
print(f"\n{'Model':<30} | {'Status':<15} | {'Details'}", flush=True)
print("-" * 80, flush=True)

for model_id in available_models:
    try:
        resp = client.models.generate_content(
            model=model_id,
            contents="Say 'ready'",
        )
        text = (resp.text or "").strip()
        print(f"{model_id:<30} | {'RESPONDED':<15} | Output: {text[:40]}", flush=True)
    except Exception as e:
        err = str(e)
        if "404" in err or "NOT_FOUND" in err:
            print(f"{model_id:<30} | {'404 NOT FOUND':<15} | Retired / unavailable", flush=True)
        elif "429" in err or "RESOURCE_EXHAUSTED" in err:
            info = "Quota exhausted"
            m = re.search(r"'quotaId': '([^']+)'", err)
            if m:
                info += f" ({m.group(1)})"
            m_val = re.search(r"'quotaValue': '([^']+)'", err)
            if m_val:
                info += f" limit={m_val.group(1)}/day"
            print(f"{model_id:<30} | {'429 EXHAUSTED':<15} | {info}", flush=True)
        else:
            print(f"{model_id:<30} | {'ERROR':<15} | {err[:50]}", flush=True)
