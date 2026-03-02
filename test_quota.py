import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found in .env")
    exit(1)

client = genai.Client(api_key=api_key)

models_to_test = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite"
]

print("Starting Quota Test...")
for m_id in models_to_test:
    print(f"\nTesting Model: {m_id} ...")
    try:
        response = client.models.generate_content(
            model=m_id,
            contents="Say hi!"
        )
        print(f"✅ Success! Response: {response.text.strip()}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    time.sleep(1) # Rate limit 방지
