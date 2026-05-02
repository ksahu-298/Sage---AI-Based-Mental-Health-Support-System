from google import genai

print("Testing Gemini API...")

try:
    client = genai.Client(api_key="AIzaSyDMszmPKL99FpSVYcBmHU4SLZybC5LGm3E")
    print("✅ Client created successfully")
    
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents="Say 'Hello, I am working!'"
    )
    print(f"✅ SUCCESS! Response: {response.text}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")