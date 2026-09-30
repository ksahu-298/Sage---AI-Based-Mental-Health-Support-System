
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

key = (os.environ.get('GROQ_API_KEY') or '').strip()
if not key:
    print('SKIP: Set GROQ_API_KEY in backend/.env')
    raise SystemExit(0)

client = Groq(api_key=key)

try:
    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[{'role': 'user', 'content': 'Say hello in one word'}],
        temperature=0.7,
        max_tokens=50,
    )
    print('OK: Groq API responded.')
    print('Response:', response.choices[0].message.content)
except Exception as e:
    print('ERROR:', e)
