import os
from dotenv import load_dotenv
import groq

# Load environment variables
load_dotenv()

def test_groq_key():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("❌ No GROQ_API_KEY found in .env file.")
        print("➡️  Make sure your .env file contains a line like:")
        print("   GROQ_API_KEY=your_actual_key_here")
        return

    print("🔑 Found GROQ_API_KEY in environment.")
    
    try:
        client = groq.Groq(api_key=api_key)
        models = client.models.list()
        print("✅ API key is valid. Connection to Groq successful!")
        print("Available models:")
        for model in models.data:
            print(" -", model.id)
    except Exception as e:
        print("❌ API key test failed.")
        print("Error details:", e)

if __name__ == "__main__":
    test_groq_key()
