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
    
import google.generativeai as genai
import json
import time
from typing import Dict, List, Optional
  
class GeminiService:
      """Service for interacting with Google Gemini API."""
      
      def __init__(self):
          genai.configure(api_key=settings.GEMINI_API_KEY)
      
      def generate_with_lite(self, prompt: str, **kwargs) -> str:
          """Generate content using Flash-Lite (cheapest, fastest)."""
          model = genai.GenerativeModel(settings.GEMINI_MODEL_LITE)
          response = model.generate_content(prompt, **kwargs)
          return response.text
      
      def generate_with_flash(self, prompt: str, **kwargs) -> str:
          """Generate content using Flash (balanced)."""
          model = genai.GenerativeModel(settings.GEMINI_MODEL_FLASH)
          response = model.generate_content(prompt, **kwargs)
          return response.text
      
      def generate_with_pro(self, prompt: str, **kwargs) -> str:
          """Generate content using Pro (most capable)."""
          model = genai.GenerativeModel(settings.GEMINI_MODEL_PRO)
          response = model.generate_content(prompt, **kwargs)
          return response.text
      
def generate_with_retry(self, prompt: str, model_type='flash', 
                         max_retries=3, **kwargs) -> str:
      """Generate with automatic retry on failure."""
      for attempt in range(max_retries):
          try:
              if model_type == 'lite':
                  return self.generate_with_lite(prompt, **kwargs)
              elif model_type == 'flash':
                  return self.generate_with_flash(prompt, **kwargs)
              elif model_type == 'pro':
                  return self.generate_with_pro(prompt, **kwargs)
          except Exception as e:
              if attempt == max_retries - 1:
                  raise
              wait_time = 2 ** attempt  # Exponential backoff
              time.sleep(wait_time)
      
      raise Exception("Failed after max retries")

def parse_json_response(self, response_text: str) -> Dict:
      """Parse JSON from Gemini response, handling code blocks."""
      # Remove markdown code blocks if present
      text = response_text.strip()
      if text.startswith('```json'):
          text = text[7:]  # Remove ```json
      if text.startswith('```'):
          text = text[3:]  # Remove ```
      if text.endswith('```'):
          text = text[:-3]  # Remove closing ```
      
      text = text.strip()
      
      try:
          return json.loads(text)
      except json.JSONDecodeError as e:
          # Try to extract JSON from text
          import re
          json_match = re.search(r'\{.*\}', text, re.DOTALL)
          if json_match:
              return json.loads(json_match.group())
          raise ValueError(f"Could not parse JSON: {e}")
