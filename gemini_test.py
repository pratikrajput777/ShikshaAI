
import google.generativeai as genai
from django.conf import settings
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobreadiness.settings')
django.setup()

# Configure the generative AI client
genai.configure(api_key=settings.GEMINI_API_KEY)

# List available models
for model in genai.list_models():
    print(model.name)
