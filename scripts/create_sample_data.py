import os
import sys
import django

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # scripts folder
sys.path.append(os.path.dirname(BASE_DIR))  # add ShikshAAI folder

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobreadiness.tech.settings")  # replace 'core.settings' with your settings path if needed
django.setup()

# Import models
from users.models import User
from skills.models import Skill, Occupation

# Create sample occupation
occ, _ = Occupation.objects.get_or_create(
    onet_code="15-1252.00",
    defaults={
        "preferred_label": "Software Developer",
        "description": "Develop software applications"
    }
)

# Create sample skill
skill1, _ = Skill.objects.get_or_create(
    preferred_label="Python Programming",
    defaults={
        "skill_type": "technical",
        "description": "Programming language"
    }
)

print("Sample data created successfully")
