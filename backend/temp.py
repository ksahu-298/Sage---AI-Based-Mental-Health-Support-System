import os
from dotenv import load_dotenv

load_dotenv()

print("Testing Gemini API Setup...")
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ℹ️ Set GEMINI_API_KEY in your .env file to run tests.")
else:
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        print("✅ Client created successfully")
    except Exception as e:
        print(f"❌ ERROR: {e}")
