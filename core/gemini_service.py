from google import genai
from django.conf import settings

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate(self, prompt: str):
        response = self.client.models.generate_content(
            model="models/gemini-1.5-flash",  # ✅ THIS IS THE FIX
            contents=prompt,
        )
        return response.text
