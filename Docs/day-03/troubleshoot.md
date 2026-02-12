# Day 03: Troubleshooting Guide

Solutions to common issues when implementing Gemini AI integration and learning path generation.

---

## Gemini API Issues

### ❌ Problem: API Key Authentication Failed

**Symptoms:**
```python
google.api_core.exceptions.InvalidArgument: 400 API key not valid
```

**Solution:**
```bash
# Verify API key in .env
echo $GEMINI_API_KEY

# Test key directly
python -c "
import google.generativeai as genai
genai.configure(api_key='YOUR_KEY_HERE')
model = genai.GenerativeModel('gemini-1.5-flash')
print(model.generate_content('test'))
"

# Regenerate key if needed at https://aistudio.google.com/app/apikey
```

---

### ❌ Problem: Rate Limiting (429 Error)

**Symptoms:**
```python
google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded
```

**Solution:**
```python
# Add exponential backoff with jitter
import time
import random

def generate_with_backoff(self, prompt, max_retries=5):
    for attempt in range(max_retries):
        try:
            return self.generate_with_flash(prompt)
        except google.api_core.exceptions.ResourceExhausted:
            if attempt == max_retries - 1:
                raise
            # Exponential backoff with jitter
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
```

---

### ❌ Problem: JSON Parsing Errors

**Symptoms:**
```python
json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Solution:**
```python
def parse_json_response(self, response_text):
    """Robust JSON parsing."""
    text = response_text.strip()
    
    # Remove markdown code blocks
    if '```json' in text:
        text = text.split('```json')[1].split('```')[0]
    elif '```' in text:
        text = text.split('```')[1].split('```')[0]
    
    text = text.strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON object/array
        import re
        # Find first { or [
        start = min([i for i, c in enumerate(text) if c in '{['] or [len(text)])
        # Find last } or ]
        end = max([i for i, c in enumerate(text) if c in '}]'] or [-1]) + 1
        
        if start < len(text) and end > 0:
            json_text = text[start:end]
            return json.loads(json_text)
        
        raise ValueError(f"No valid JSON found in response: {text[:200]}")
```

---

### ❌ Problem: Context Length Exceeded

**Symptoms:**
```python
google.api_core.exceptions.InvalidArgument: 400 Request payload size exceeds the limit
```

**Solution:**
```python
# Truncate long inputs
def create_macro_plan_prompt(self, user, occupation, skill_gaps):
    # Limit to top 10 gaps instead of all
    top_gaps = skill_gaps[:10]
    
    # Summarize instead of full text
    gaps_summary = "\n".join([
        f"- {gap.skill.preferred_label}: Gap {gap.gap_score:.1f}"
        for gap in top_gaps
    ])
    
    # Keep prompt focused and concise
    prompt = f"""Create study plan for {occupation.preferred_label}.
    
Top Skill Gaps:
{gaps_summary}

Output 5-8 modules as JSON..."""
    
    return prompt
```

---

## Model & Database Issues

### ❌ Problem: JSONField not recognized

**Symptoms:**
```python
django.core.exceptions.ImproperlyConfigured: 'JSONField' requires psycopg2 2.5.4 or higher
```

**Solution:**
```python
# Don't use django.contrib.postgres.fields.JSONField
# Use Django 3.1+ built-in JSONField

# Wrong:
from django.contrib.postgres.fields import JSONField

# Correct:
from django.db import models

class StudyPlan(models.Model):
    skill_gaps_snapshot = models.JSONField(default=dict)  # Built-in!
```

---

### ❌ Problem: Circular import between learning and assessment

**Symptoms:**
```python
ImportError: cannot import name 'AssessmentService'
```

**Solution:**
```python
# Import inside function, not at module level
def generate_macro_plan(self, user, occupation):
    # Import here to avoid circular dependency
    from assessment.services import AssessmentService
    
    skill_gaps = AssessmentService.calculate_skill_gaps(user, occupation)
    # ... rest of code
```

---

## Content Generation Issues

### ❌ Problem: Study plan generation produces invalid module count

**Symptoms:**
```
Expected 5-8 modules, got 15
```

**Solution:**
```python
# Make requirements explicit in prompt
prompt = f"""...
**STRICT REQUIREMENTS**:
1. Generate EXACTLY 5-8 modules (not more, not less)
2. If more content needed, make modules broader
3. Each module should be 15-30 hours

Provide JSON with 5-8 modules only.
"""

# Validate and truncate if needed
plan_data = self.gemini.parse_json_response(response)
modules = plan_data['modules'][:8]  # Enforce maximum

if len(modules) < 5 or len(modules) > 8:
    raise ValueError(f"Invalid module count: {len(modules)}")
```

---

### ❌ Problem: Lesson content too short or poor quality

**Symptoms:**
```
Lesson content only 100 words instead of 500-800
```

**Solution:**
```python
# Be more specific in prompt
prompt = f"""...
**Content Requirements**:
1. Minimum 500 words, maximum 800 words
2. Include: Introduction, Main Concepts (3-4), Examples (2-3), Summary
3. Use analogies for complex topics
4. Provide code examples if applicable
5. Format with clear section headings

Do not provide brief summaries. Generate complete, detailed lessons.
"""

# Validate response
if len(lesson_data['content'].split()) < 400:
    # Retry with emphasis on length
    prompt += "\n\nIMPORTANT: Previous response was too brief. Provide detailed 600+ word content."
    response = self.gemini.generate_with_retry(prompt)
```

---

### ❌ Problem: CFU quiz questions too easy/hard

**Symptoms:**
```
All questions are trivial or all questions are impossible
```

**Solution:**
```python
# Specify difficulty distribution explicitly
prompt = f"""...
**Difficulty Requirements**:
- Question 1-2: Easy (recall, basic understanding)
- Question 3-4: Medium (application, analysis)
- Question 5: Hard (synthesis, evaluation)

**Easy Example**: "What is X?" or "Which statement is true?"
**Medium Example**: "How would you apply X to Y?"  
**Hard Example**: "Compare and contrast X and Y. Which is better for Z?"

Mark each question's difficulty in JSON.
"""

# Validate difficulty distribution
difficulties = [q['difficulty'] for q in quiz_data['questions']]
easy_count = difficulties.count('easy')
medium_count = difficulties.count('medium')
hard_count = difficulties.count('hard')

if not (easy_count >= 2 and medium_count >= 2 and hard_count >= 1):
    # Regenerate with feedback
    pass
```

---

## Celery & Async Issues

### ❌ Problem: Celery task not executing

**Symptoms:**
```
Task queued but never runs
```

**Solution:**
```bash
# Check Celery worker is running
celery -A jobreadiness inspect active

# Check task is registered
celery -A jobreadiness inspect registered

# Check Redis connection
redis-cli ping

# Restart worker with correct queue
celery -A jobreadiness worker -Q default,low_priority_batch -l info

# Check task status
from celery.result import AsyncResult
result = AsyncResult(task_id)
print(result.state)  # PENDING, STARTED, SUCCESS, FAILURE
```

---

### ❌ Problem: Batch task times out

**Symptoms:**
```
Task exceeded time limit and was terminated
```

**Solution:**
```python
# Increase task time limit in settings
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# Or in task decorator
@shared_task(bind=True, time_limit=1800, soft_time_limit=1700)
def generate_study_plan_batch_task(self, study_plan_id):
    # ... generation logic
    pass

# Add progress tracking
def generate_all_lessons(self, study_plan):
    modules = study_plan.learning_modules.all()
    total = len(modules)
    
    for i, module in enumerate(modules):
        self.generate_lessons_for_module(module)
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': i+1, 'total': total}
        )
```

---

## WebSocket Issues

### ❌ Problem: WebSocket connection refused

**Symptoms:**
```
WebSocket connection to 'ws://localhost:8000/ws/study-plan/progress/' failed
```

**Solution:**
```python
# Ensure Daphne is running (not just Django dev server)
# Start Daphne:
daphne -b 0.0.0.0 -p 8001 jobreadiness.asgi:application

# Update asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import learning.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobreadiness.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            learning.routing.websocket_urlpatterns
        )
    ),
})

# Install channels and daphne
pip install channels channels-redis daphne

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    ...
    'channels',
]

# Configure channel layers in settings
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}
```

---

### ❌ Problem: WebSocket messages not received

**Symptoms:**
```
Celery task sends messages but frontend doesn't receive
```

**Solution:**
```python
# Verify channel layer configured
python manage.py shell
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()
print(channel_layer)  # Should not be None

# Test message sending
from asgiref.sync import async_to_sync
async_to_sync(channel_layer.group_send)(
    'study_plan_1',
    {
        'type': 'study_plan_update',
        'message': 'test'
    }
)

# Ensure consumer method name matches 'type'
# If type='study_plan_update', method must be study_plan_update()

# Check Redis
redis-cli
KEYS *  # Should see channel layer keys
```

---

## Performance Issues

### ❌ Problem: Study plan generation too slow

**Symptoms:**
```
Takes 5+ minutes to generate study plan
```

**Solution:**
```python
# Parallelize lesson generation
from celery import group

def generate_all_lessons_parallel(self, study_plan):
    modules = study_plan.learning_modules.all()
    
    # Create group of tasks
    job = group(
        generate_lessons_for_module_task.s(module.id)
        for module in modules
    )
    
    # Execute in parallel
    result = job.apply_async()
    result.join()  # Wait for all to complete
    
    return study_plan

# Separate task for each module
@shared_task
def generate_lessons_for_module_task(module_id):
    module = LearningModule.objects.get(id=module_id)
    service = StudyPlanService()
    return service.generate_lessons_for_module(module)
```

---

### ❌ Problem: Too many Gemini API calls (high cost)

**Symptoms:**
```
$100 API bill for 100 users
```

**Solution:**
```python
# 1. Batch generation instead of real-time
# Queue non-urgent generation
@shared_task
def batch_generate_study_plans():
    pending_plans = StudyPlan.objects.filter(status='pending')
    for plan in pending_plans:
        generate_study_plan_batch_task.delay(plan.id)

# 2. Cache generated content
from django.core.cache import cache

def generate_lessons_for_module(self, module):
    cache_key = f'lessons_{module.id}'
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Generate...
    lessons = ...
    
    cache.set(cache_key, lessons, timeout=86400)  # 24 hours
    return lessons

# 3. Share content between similar modules
# Detect duplicate topics and reuse generation

# 4. Use cheaper models
# Flash-Lite for simple content, Pro only for complex planning
```

---

## Complete System Test

```python
# Run end-to-end test
from learning.services import StudyPlanService
from users.models import User
from skills.models import Occupation

service = StudyPlanService()

# 1. Generate study plan
user = User.objects.first()
occupation = Occupation.objects.filter(preferred_label__icontains='Developer').first()
study_plan = service.generate_macro_plan(user, occupation)

print(f"✓ Study plan created: {study_plan.total_modules} modules")

# 2. Generate lessons
service.generate_all_lessons(study_plan)
lesson_count = sum(m.lessons.count() for m in study_plan.learning_modules.all())
print(f"✓ Lessons created: {lesson_count} total")

# 3. Generate CFU quiz
first_lesson = study_plan.learning_modules.first().lessons.first()
quiz = service.generate_cfu_quiz(first_lesson)
print(f"✓ CFU quiz created: {len(quiz.questions)} questions")

# 4. Simulate quiz attempt (fail)
from learning.models import CFUAttempt
attempt = CFUAttempt.objects.create(
    quiz=quiz,
    user=user,
    answers=[1, 1, 1, 1, 1],  # All wrong
    score=0,
    passed=False
)

# 5. Generate remediation
remediation = service.generate_remediation(attempt)
print(f"✓ Remediation created: {remediation.misconception}")

print("\n✅ Complete system test PASSED!")
```

---

**If all else fails**: Clear study plans, regenerate with fresh prompts, check Gemini API dashboard for quota/errors!
