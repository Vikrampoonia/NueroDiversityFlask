# check_models.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

# --- Initialization ---
# This part is the same as your ai_service.py
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("API Key not found. Please check your .env file.")
else:
    try:
        genai.configure(api_key=api_key)

        print("Available models that support the 'generateContent' method:")
        print("-" * 60)

        # Loop through all available models
        for m in genai.list_models():
            # Check if the model supports the method your code uses ('generateContent')
            if 'generateContent' in m.supported_generation_methods:
                # Print the exact name you need to use in your code
                print(m.name)
        
        print("-" * 60)

    except Exception as e:
        print(f"An error occurred: {e}")