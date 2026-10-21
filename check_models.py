from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("No GEMINI_API_KEY found in environment or .env")
    print("Please set GEMINI_API_KEY in .env file.")
else:
    print(f"Using API Key: {api_key[:5]}...")
    try:
        client = genai.Client(api_key=api_key)
        print("Successfully configured Gemini client with google-genai")
        print("Available models via google-genai SDK:")
        for model in client.models.list():
            if 'generateContent' in getattr(model, 'supported_generation_methods', []):
                print(f"- {model.name}")
    except Exception as e:
        print(f"Error: {e}")
