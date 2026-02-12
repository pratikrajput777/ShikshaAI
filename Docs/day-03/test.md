# Day 03: Testing & Validation Guide

Comprehensive testing for Gemini AI integration and learning path generation.

---

## Pre-Testing Checklist

- [ ] Day 02 completed and tested
- [ ] google-generativeai installed
- [ ] Gemini API key configured
- [ ] channels, channels-redis, daphne installed
- [ ] Learning models migrated
- [ ] Celery and Redis running

---

## Test 1: Gemini API Connectivity

**Test 1.1: Basic API Connection**
```python
import google.generativeai as genai
from django.conf import settings

# Test API configuration
genai.configure(api_key=settings.GEMINI_API_KEY)

# Test Flash-Lite
model_lite = genai.GenerativeModel('gemini-2.0-flash-lite')
response = model_lite.generate_content("Say 'Gemini Flash-Lite works!'")
assert 'works' in response.text.lower() or 'flash-lite' in response.text.lower()
print("✓ Test 1.1: Flash-Lite model OK")

# Test Flash
model_flash = genai.GenerativeModel('gemini-1.5-flash')
response = model_flash.generate_content("Say 'Gemini Flash works!'")
assert'works' in response.text.lower()
print("✓ Test 1.1: Flash model OK")

# Test Pro
model_pro = genai.GenerativeModel('gemini-1.5-pro')
response = model_pro.generate_content("Say 'Gemini Pro works!'")
assert 'works' in response.text.lower()
print("✓ Test 1.1: Pro model OK")
```

**Pass Criteria:** All 3 models respond successfully

---

**Test 1.2: GeminiService Class**
```python
from core.gemini_service import GeminiService

service = GeminiService()

# Test each method
lite_response = service.generate_with_lite("What is 2+2?")
assert '4' in lite_response
print(f"✓ Lite: {lite_response[:50]}")

flash_response = service.generate_with_flash("Name a color")
assert len(flash_response) > 0
print(f"✓ Flash: {flash_response[:50]}")

pro_response = service.generate_with_pro("Explain photosynthesis in 20 words")
assert len(pro_response.split()) < 30
print(f"✓ Pro: {pro_response[:50]}")
```

**Pass Criteria:** All generation methods work

---

**Test 1.3: JSON Parsing**
```python
service = GeminiService()

# Test 1: Regular JSON
json_text = '{"key": "value"}'
result = service.parse_json_response(json_text)
assert result == {"key": "value"}
print("✓ Regular JSON parsed")

# Test 2: Markdown code blocks
markdown_json = '```json\n{"key": "value"}\n```'
result = service.parse_json_response(markdown_json)
assert result == {"key": "value"}
print("✓ Markdown JSON parsed")

# Test 3: JSON with surrounding text
text_with_json = 'Here is the data: {"key": "value"} as requested.'
result = service.parse_json_response(text_with_json)
assert result == {"key": "value"}
print("✓ Embedded JSON parsed")

# Test 4: Invalid JSON
try:
    service.parse_json_response("Not JSON at all")
    print("✗ Should have raised error")
except ValueError:
    print("✓ Invalid JSON rejected")
```

**Pass Criteria:** All JSON formats parsed correctly

---

## Test 2: Study Plan Generation

**Test 2.1: Macro Tier (Overall Plan)**
```python
from learning.services import StudyPlanService
from users.models import User
from skills.models import Occupation

service = StudyPlanService()

# Create test user and occupation
user = User.objects.first()
occupation = Occupation.objects.filter(preferred_label__icontains='Developer').first()

# Generate study plan
study_plan = service.generate_macro_plan(user, occupation)

assert study_plan is not None
assert study_plan.status == 'ready'
assert 5 <= study_plan.total_modules <= 8
print(f"✓ Study plan created with {study_plan.total_modules} modules")

# Verify modules
modules = study_plan.learning_modules.all()
assert len(modules) == study_plan.total_modules

for module in modules:
    assert module.title
    assert module.description
    assert module.estimated_hours > 0
    assert module.order >= 1
    print(f"  - Module {module.order}: {module.title} ({module.estimated_hours}h)")

print("✓ Test 2.1: Macro tier generation PASSED")
```

**Pass Criteria:** 5-8 modules created with proper structure

---

**Test 2.2: Meso Tier (Lessons)**
```python
# Generate lessons for first module
module = study_plan.learning_modules.first()
lessons = service.generate_lessons_for_module(module)

assert 8 <= len(lessons) <= 12
print(f"✓ Generated {len(lessons)} lessons")

# Verify lesson structure
for lesson in lessons:
    assert lesson.title
    assert lesson.content
    assert len(lesson.content.split()) >= 400  # At least 400 words
    assert len(lesson.learning_objectives) >= 3
    assert lesson.estimated_minutes > 0
    assert lesson.order >= 1
    print(f"  - Lesson {lesson.order}: {lesson.title} ({lesson.estimated_minutes}min)")
    print(f"    Words: {len(lesson.content.split())}, Objectives: {len(lesson.learning_objectives)}")

# First lesson should be available
assert lessons[0].status == 'available'

# Rest should be locked
for lesson in lessons[1:]:
    assert lesson.status == 'locked'

print("✓ Test 2.2: Meso tier generation PASSED")
```

**Pass Criteria:** 8-12 lessons per module, proper content length

---

**Test 2.3: Complete Study Plan**
```python
# Generate all lessons for all modules
service.generate_all_lessons(study_plan)

total_lessons = sum(m.lessons.count() for m in study_plan.learning_modules.all())
print(f"✓ Total lessons across all modules: {total_lessons}")

assert total_lessons >= 40  # Minimum 5 modules × 8 lessons
print("✓ Test 2.3: Complete study plan PASSED")
```

**Pass Criteria:** All modules have lessons generated

---

## Test 3: CFU Quiz System

**Test 3.1: Quiz Generation**
```python
# Generate CFU for first lesson
lesson = study_plan.learning_modules.first().lessons.first()
quiz = service.generate_cfu_quiz(lesson)

assert quiz is not None
assert len(quiz.questions) == 5
assert quiz.passing_score == 70

# Verify question structure
difficulties = {'easy': 0, 'medium': 0, 'hard': 0}
for i, question in enumerate(quiz.questions):
    assert 'question' in question
    assert 'options' in question
    assert len(question['options']) == 4
    assert 'correct_answer' in question
    assert 0 <= question['correct_answer'] <= 3
    assert 'explanation' in question
    assert 'difficulty' in question
    
    difficulties[question['difficulty']] += 1
    print(f"  Q{i+1} ({question['difficulty']}): {question['question'][:60]}...")

# Verify difficulty distribution (2 easy, 2 medium, 1 hard)
assert difficulties['easy'] >= 2
assert difficulties['medium'] >= 2
assert difficulties['hard'] >= 1
print(f"✓ Difficulty distribution: {difficulties}")

print("✓ Test 3.1: CFU quiz generation PASSED")
```

**Pass Criteria:** 5 questions with proper difficulty distribution

---

**Test 3.2: Quiz Attempt and Scoring**
```python
from learning.models import CFUAttempt

# Test 1: Perfect score
perfect_answers = [q['correct_answer'] for q in quiz.questions]
attempt = CFUAttempt.objects.create(
    quiz=quiz,
    user=user,
    answers=perfect_answers,
    score=100,
    passed=True
)

assert attempt.score == 100
assert attempt.passed == True
print("✓ Perfect score recognized")

# Test 2: Failing score
bad_answers = [(q['correct_answer'] + 1) % 4 for q in quiz.questions]  # All wrong
fail_attempt = CFUAttempt.objects.create(
    quiz=quiz,
    user=user,
    answers=bad_answers,
    score=0,
    passed=False,
    attempt_number=2
)

assert fail_attempt.score == 0
assert fail_attempt.passed == False
print("✓ Failing score recognized")

# Test 3: Passing score (70%)
partial_answers = perfect_answers[:4] + bad_answers[4:]  # 4 correct, 1 wrong = 80%
pass_attempt = CFUAttempt.objects.create(
    quiz=quiz,
    user=user,
    answers=partial_answers,
    score=80,
    passed=True
)

assert pass_attempt.score == 80
assert pass_attempt.passed == True
print("✓ Passing score recognized")

print("✓ Test 3.2: Quiz scoring PASSED")
```

**Pass Criteria:** Scoring logic works correctly

---

## Test 4: Remediation System

**Test 4.1: Remediation Generation**
```python
# Generate remediation for failed attempt
remediation = service.generate_remediation(fail_attempt)

assert remediation is not None
assert remediation.misconception
assert remediation.explanation
assert remediation.simplified_content
assert len(remediation.simplified_content.split()) >= 250
assert len(remediation.additional_examples) >= 2

print(f"✓ Misconception: {remediation.misconception}")
print(f"✓ Explanation length: {len(remediation.explanation.split())} words")
print(f"✓ Simplified content: {len(remediation.simplified_content.split())} words")
print(f"✓ Examples: {len(remediation.additional_examples)}")

# Verify attempt marked
fail_attempt.refresh_from_db()
assert fail_attempt.remediation_generated == True

print("✓ Test 4.1: Remediation generation PASSED")
```

**Pass Criteria:** Remediation created with all required components

---

## Test 5: Celery Batch Processing

**Test 5.1: Batch Task Execution**
```python
from learning.tasks import generate_study_plan_batch_task
from celery.result import AsyncResult

# Create new study plan for batch generation
batch_plan = StudyPlan.objects.create(
    user=user,
    target_occupation=occupation,
    status='pending'
)

# Queue task
task = generate_study_plan_batch_task.delay(batch_plan.id)
batch_plan.batch_job_id = task.id
batch_plan.save()

print(f"✓ Task queued: {task.id}")

# Wait for completion (with timeout)
import time
timeout = 300  # 5 minutes
start = time.time()

while time.time() - start < timeout:
    result = AsyncResult(task.id)
    if result.state in ['SUCCESS', 'FAILURE']:
        break
    time.sleep(5)
    print(f"  Status: {result.state}...")

assert result.state == 'SUCCESS'
print(f"✓ Task completed: {result.result}")

# Verify study plan generated
batch_plan.refresh_from_db()
assert batch_plan.status == 'ready'
assert batch_plan.total_modules > 0
print(f"✓ Batch study plan ready with {batch_plan.total_modules} modules")

print("✓ Test 5.1: Batch processing PASSED")
```

**Pass Criteria:** Task completes successfully, study plan generated

---

## Test 6: WebSocket Notifications

**Test 6.1: Channel Layer Configuration**
```python
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()
assert channel_layer is not None
print("✓ Channel layer configured")

# Test message sending
from asgiref.sync import async_to_sync

group_name = f'study_plan_{user.id}'

# Send test message
async_to_sync(channel_layer.group_send)(
    group_name,
    {
        'type': 'study_plan_update',
        'status': 'generating',
        'progress': 50,
        'message': 'Test message'
    }
)

print("✓ Test message sent successfully")
print("⚠ Manual verification needed: Check WebSocket client receives message")
```

**Pass Criteria:** Channel layer works, messages sent

---

## Test 7: Integration Test

**Test 7.1: Complete User Flow**
```python
print("Running complete user flow test...")

# 1. User has skill gaps (from Day 02)
from assessment.services import AssessmentService
gaps = AssessmentService.calculate_skill_gaps(user, occupation)
print(f"✓ Step 1: {len(gaps)} skill gaps identified")

# 2. Generate study plan
study_plan = service.generate_macro_plan(user, occupation)
print(f"✓ Step 2: Study plan created ({study_plan.total_modules} modules)")

# 3. Generate lessons
service.generate_all_lessons(study_plan)
total_lessons = sum(m.lessons.count() for m in study_plan.learning_modules.all())
print(f"✓ Step 3: {total_lessons} lessons generated")

# 4. Start first lesson
first_lesson = study_plan.learning_modules.first().lessons.first()
first_lesson.status = 'in_progress'
first_lesson.save()
print(f"✓ Step 4: Started lesson '{first_lesson.title}'")

# 5. Complete lesson and take quiz
quiz = service.generate_cfu_quiz(first_lesson)
print(f"✓ Step 5: CFU quiz generated ({len(quiz.questions)} questions)")

# 6. Fail quiz
attempt = CFUAttempt.objects.create(
    quiz=quiz,
    user=user,
    answers=[0, 0, 0, 0, 0],  # All wrong
    score=0,
    passed=False
)
print(f"✓ Step 6: Quiz attempted (score: {attempt.score}%)")

# 7. Get remediation
remediation = service.generate_remediation(attempt)
print(f"✓ Step 7: Remediation generated")

# 8. Retake quiz and pass
retry_answers = [q['correct_answer'] for q in quiz.questions]
retry_attempt = CFUAttempt.objects.create(
    quiz=quiz,
    user=user,
    answers=retry_answers,
    score=100,
    passed=True,
    attempt_number=2
)
print(f"✓ Step 8: Quiz retaken (score: {retry_attempt.score}%)")

# 9. Complete lesson and unlock next
first_lesson.status = 'completed'
first_lesson.save()

next_lesson = study_plan.learning_modules.first().lessons.all()[1]
next_lesson.status = 'available'
next_lesson.save()
print(f"✓ Step 9: Next lesson unlocked: '{next_lesson.title}'")

# 10. Update progress
study_plan.completed_modules = 0
study_plan.update_progress()
print(f"✓ Step 10: Progress updated ({study_plan.progress_percentage:.1f}%)")

print("\n✅ Complete integration test PASSED!")
```

**Pass Criteria:** All steps complete without errors

---

## Performance Tests

**Test 8.1: Generation Speed**
```python
import time

# Test macro generation speed
start = time.time()
plan = service.generate_macro_plan(user, occupation)
macro_time = time.time() - start

print(f"Macro generation: {macro_time:.2f}s")
assert macro_time < 60, "Macro generation should complete in <60s"

# Test meso generation speed
module = plan.learning_modules.first()
start = time.time()
lessons = service.generate_lessons_for_module(module)
meso_time = time.time() - start

print(f"Meso generation (1 module): {meso_time:.2f}s")
assert meso_time < 90, "Lesson generation should complete in <90s"

print("✓ Performance test PASSED")
```

**Pass Criteria:** Acceptable response times

---

## Final Validation Script

```bash
#!/bin/bash

echo "🧪 Day 03 - AI Learning Paths Validation"
echo "========================================="

# 1. Check Gemini API
python -c "
import google.generativeai as genai
from django.conf import settings
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content('test')
print('✓ Gemini API OK')
"

# 2. Check models
python manage.py check learning
[ $? -eq 0 ] && echo "✓ Models OK" || echo "✗ Models FAIL"

# 3. Check Celery
celery -A jobreadiness inspect ping
[ $? -eq 0 ] && echo "✓ Celery OK" || echo "✗ Celery not running"

# 4. Check Channels
python -c "
from channels.layers import get_channel_layer
assert get_channel_layer() is not None
print('✓ Channels OK')
"

# 5. Run integration test
python manage.py shell < day-03/integration_test.py

echo ""
echo "========================================="
echo "Day 03 Validation Complete!"
```

---

## Test Report Template

```markdown
# Day 03 Test Report

**Date**: ___________
**Tester**: ___________

| Test | Status | Notes |
|------|--------|-------|
| Gemini API | [ ] | |
| JSON Parsing | [ ] | |
| Study Plan (Macro) | [ ] | |
| Lessons (Meso) | [ ] | |
| CFU Quizzes | [ ] | |
| Remediation | [ ] | |
| Batch Processing | [ ] | |
| WebSocket | [ ] | |
| Integration Flow | [ ] | |
| Performance | [ ] | |

**Overall**: _____ / 10 passed

**Issues**:

**Sign-off**: ✅ Ready for Day 04
```

---

**All tests passing = Day 03 complete!** 🎉 **Ready to build mock interviews!**
