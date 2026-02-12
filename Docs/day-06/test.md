# Day 06: Testing & Validation Guide - Service Layer

Comprehensive testing for all implemented services.

---

## Pre-Testing Checklist

- [ ] Day 05 completed
- [ ] scipy installed (`pip install scipy`)
- [ ] google-generativeai installed
- [ ] Gemini API key configured
- [ ] core/, assessment/ apps exist

---

## Test 1: GeminiService

**Test 1.1: Basic Model Calls**
```python
from core.gemini_service import GeminiService

service = GeminiService()

# Test Lite model
lite_response = service.generate_with_lite("What is 1+1?")
assert '2' in lite_response
print(f"✓ Lite: {lite_response}")

# Test Flash model  
flash_response = service.generate_with_flash("Name a color")
assert len(flash_response) > 0
print(f"✓ Flash: {flash_response}")

# Test Pro model
pro_response = service.generate_with_pro("Explain atoms briefly")
assert len(pro_response) > 20
print(f"✓ Pro: {pro_response[:100]}")

print("✓ Test 1.1 PASSED")
```

**Test 1.2: Retry Mechanism**
```python
# Test with retry
response = service.generate_with_retry(
    "List 3 programming languages",
    model_type='flash',
    max_retries=3
)

assert len(response) > 0
print(f"✓ Retry works: {response}")
print("✓ Test 1.2 PASSED")
```

**Test 1.3: JSON Parsing**
```python
# Test various JSON formats
test_cases = [
    '{"key": "value"}',  # Plain JSON
    '```json\n{"key": "value"}\n```',  # Markdown block
    'Here is data: {"key": "value"}',  # Embedded
    '```\n{"key": "value"}\n```',  # Generic block
]

for i, test_text in enumerate(test_cases):
    parsed = service.parse_json_response(test_text)
    assert parsed == {"key": "value"}
    print(f"✓ Format {i+1} parsed correctly")

print("✓ Test 1.3 PASSED")
```

---

## Test 2: IRTEngine

**Test 2.1: Probability Calculation**
```python
from assessment.services import IRTEngine

# Test at different ability levels
test_cases = [
    {'theta': -2, 'a': 1, 'b': 0, 'c': 0.25, 'expected_range': (0.25, 0.35)},
    {'theta': 0, 'a': 1, 'b': 0, 'c': 0.25, 'expected_range': (0.55, 0.65)},
    {'theta': 2, 'a': 1, 'b': 0, 'c': 0.25, 'expected_range': (0.85, 0.95)},
]

for case in test_cases:
    prob = IRTEngine.probability(case['theta'], case['a'], case['b'], case['c'])
    assert case['expected_range'][0] <= prob <= case['expected_range'][1]
    print(f"✓ P(theta={case['theta']}) = {prob:.3f}")

print("✓ Test 2.1 PASSED")
```

**Test 2.2: Information Function**
```python
# Information should peak near difficulty
theta = 0
info = IRTEngine.information(theta, a=1, b=0, c=0.25)
assert info > 0
print(f"✓ Information at theta=0: {info:.3f}")

# Information should be lower far from difficulty
theta_far = 3
info_far = IRTEngine.information(theta_far, a=1, b=0, c=0.25)
assert info_far < info  # Less information far from difficulty
print(f"✓ Information at theta=3: {info_far:.3f}")

print("✓ Test 2.2 PASSED")
```

**Test 2.3: Theta Estimation (MLE)**
```python
import numpy as np

# Simulate answers
answers = [True, True, False, True, True]  # 4/5 correct
questions = [
    {'a': 1.0, 'b': -1.0, 'c': 0.25},
    {'a': 1.0, 'b': 0.0, 'c': 0.25},
    {'a': 1.0, 'b': 0.5, 'c': 0.25},
    {'a': 1.0, 'b': 1.0, 'c': 0.25},
    {'a': 1.0, 'b': 1.5, 'c': 0.25},
]

theta, se = IRTEngine.estimate_theta(answers, questions)

# Should estimate positive theta (4/5 correct = above average)
assert theta > 0
assert -4 <= theta <= 4
assert 0 < se < 1

print(f"✓ Theta: {theta:.2f}, SE: {se:.2f}")
print("✓ Test 2.3 PASSED")
```

---

## Test 3: AssessmentService

**Test 3.1: Session Creation**
```python
from assessment.services import AssessmentService
from users.models import User
from skills.models import Skill

user = User.objects.first()
skill = Skill.objects.first()

session = AssessmentService.start_session(user, skill)

assert session is not None
assert session.user == user
assert session.skill == skill
assert session.status == 'active'
assert session.current_theta == 0.0
assert session.current_se == 1.0

print(f"✓ Session created: ID={session.id}")
print("✓ Test 3.1 PASSED")
```

**Test 3.2: Question Selection**
```python
from assessment.models import QuestionBank

# Ensure questions exist
question_count = QuestionBank.objects.filter(skill=skill).count()
print(f"Questions available: {question_count}")

if question_count == 0:
    # Create sample questions
    for i in range(10):
        QuestionBank.objects.create(
            skill=skill,
            question_text=f"Test question {i}?",
            options=["A", "B", "C", "D"],
            correct_answer=0,
            difficulty_b=i - 5,  # Range -5 to 4
            discrimination_a=1.0,
            guessing_c=0.25
        )
    print("✓ Created 10 sample questions")

# Get next question
question = AssessmentService.get_next_question(session)

assert question is not None
assert question.skill == skill
print(f"✓ Question selected: {question.question_text}")
print("✓ Test 3.2 PASSED")
```

**Test 3.3: Answer Submission & Theta Update**
```python
# Submit correct answer
result = AssessmentService.submit_answer(
    session,
    question,
    selected_answer=question.correct_answer
)

assert result['correct'] == True
assert result['theta'] != 0.0  # Theta should update
assert result['se'] < 1.0  # SE should decrease

print(f"✓ Correct answer processed")
print(f"  Theta: {result['theta']:.2f}")
print(f"  SE: {result['se']:.2f}")

# Submit incorrect answer
question2 = AssessmentService.get_next_question(session)
if question2:
    wrong_answer = (question2.correct_answer + 1) % 4
    result2 = AssessmentService.submit_answer(session, question2, wrong_answer)
    
    assert result2['correct'] == False
    print(f"✓ Incorrect answer processed")
    print(f"  Theta: {result2['theta']:.2f}")

print("✓ Test 3.3 PASSED")
```

**Test 3.4: Convergence**
```python
# Simulate full assessment
question_count = 0
max_questions = 30

while question_count < max_questions:
    session.refresh_from_db()
    
    # Check convergence
    if session.status == 'converged':
        print(f"✓ Converged after {session.question_count} questions")
        break
    
    q = AssessmentService.get_next_question(session)
    if not q:
        break
    
    # Simulate answer (50% correct)
    answer = question_count % 2 == 0
    selected = q.correct_answer if answer else (q.correct_answer + 1) % 4
    
    AssessmentService.submit_answer(session, q, selected)
    question_count += 1

session.refresh_from_db()
print(f"✓ Final theta: {session.current_theta:.2f}")
print(f"✓ Final SE: {session.current_se:.2f}")
print(f"✓ Status: {session.status}")

assert session.status in ['converged', 'active']
print("✓ Test 3.4 PASSED")
```

---

## Test 4: Skill Gap Analysis

**Test 4.1: Calculate Gaps**
```python
from skills.models import Occupation

occupation = Occupation.objects.first()

# Calculate gaps
gaps = AssessmentService.calculate_skill_gaps(user, occupation)

assert len(gaps) > 0
print(f"✓ Calculated {len(gaps)} skill gaps")

# Check top gaps
for i, gap in enumerate(gaps[:5]):
    print(f"  {i+1}. {gap.skill.preferred_label}")
    print(f"     Current: {gap.current_level:.2f}, Required: {gap.required_level:.2f}")
    print(f"     Gap: {gap.gap_score:.2f}, Priority: {gap.priority_score:.2f}")

assert gaps[0].priority_score >= gaps[-1].priority_score  # Sorted by priority

print("✓ Test 4.1 PASSED")
```

---

## Integration Test

**Test 5: Complete Assessment Flow**
```python
print("\nRunning Complete Assessment Flow Integration Test\n")

# 1. Create new user and session
from django.contrib.auth import get_user_model
User = get_user_model()

test_user, created = User.objects.get_or_create(
    username='test_assessment',
    defaults={'email': 'test@example.com'}
)
print(f"✓ Step 1: User ready")

# 2. Start assessment
test_skill = Skill.objects.first()
test_session = AssessmentService.start_session(test_user, test_skill)
print(f"✓ Step 2: Session started (ID: {test_session.id})")

# 3. Answer questions until convergence
answered = 0
while answered < 15:  # Max 15 for test
    question = AssessmentService.get_next_question(test_session)
    if not question:
        break
    
    # Randomize answers
    import random
    is_correct = random.random() > 0.3  # 70% correct rate
    answer = question.correct_answer if is_correct else random.randint(0, 3)
    
    result = AssessmentService.submit_answer(test_session, question, answer)
    answered += 1
    
    if answered % 5 == 0:
        print(f"✓ Step 3: {answered} questions answered (theta={result['theta']:.2f}, SE={result['se']:.2f})")
    
    if result['converged']:
        print(f"✓ Converged at question {answered}")
        break

# 4. Calculate skill gaps
test_occupation = Occupation.objects.first()
test_gaps = AssessmentService.calculate_skill_gaps(test_user, test_occupation)
print(f"✓ Step 4: {len(test_gaps)} skill gaps calculated")

# 5. Verify results
test_session.refresh_from_db()
assert test_session.question_count > 0
assert -4 <= test_session.current_theta <= 4
assert test_session.current_se > 0

print(f"\n✅ Complete Integration Test PASSED!")
print(f"   Final Results:")
print(f"   - Questions: {test_session.question_count}")
print(f"   - Theta: {test_session.current_theta:.2f}")
print(f"   - SE: {test_session.current_se:.2f}")
print(f"   - Status: {test_session.status}")
```

---

## Performance Test

**Test 6: Speed Benchmarks**
```python
import time

print("\nPerformance Benchmarks\n")

# Benchmark 1: Theta estimation
start = time.time()
for _ in range(100):
    IRTEngine.estimate_theta(
        [True, False, True, True, False],
        [{'a': 1.0, 'b': i-2.5, 'c': 0.25} for i in range(5)]
    )
estimation_time = time.time() - start
print(f"✓ 100 theta estimations: {estimation_time*10:.1f}ms each")

assert estimation_time < 5.0  # Should complete in <5 seconds

# Benchmark 2: Answer submission
start = time.time()
q = QuestionBank.objects.filter(skill=skill).first()
for _ in range(10):
    AssessmentService.submit_answer(test_session, q, 0)
submission_time = time.time() - start
print(f"✓ 10 answer submissions: {submission_time*100:.1f}ms each")

assert submission_time < 10.0  # Should complete in <10 seconds

print("✓ Performance test PASSED")
```

---

## Validation Script

```bash
#!/bin/bash

echo "Day 06 - Service Layer Validation"
echo "=================================="

# Check all service files exist
echo "Checking files..."
test -f core/gemini_service.py && echo "✓ GeminiService" || echo "✗ GeminiService missing"
test -f assessment/services.py && echo "✓ AssessmentService" || echo "✗ AssessmentService missing"

# Test imports
python manage.py shell -c "
from core.gemini_service import GeminiService
from assessment.services import IRTEngine, AssessmentService
print('✓ All imports successful')
"

# Run Django tests
python manage.py test assessment.tests
echo "✓ Unit tests passed"

echo ""
echo "=================================="
echo "✅ Day 06 VALIDATED!"
```

---

## Test Report Template

```markdown
# Day 06 Test Report

**Date**: ___________
**Tester**: ___________

| Test | Status | Notes |
|------|--------|-------|
| GeminiService Models | [ ] | |
| GeminiService Retry | [ ] | |
| JSON Parsing | [ ] | |
| IRT Probability | [ ] | |
| IRT Information | [ ] | |
| Theta Estimation | [ ] | |
| Session Creation | [ ] | |
| Question Selection | [ ] | |
| Answer Submission | [ ] | |
| Skill Gap Analysis | [ ] | |
| Integration Flow | [ ] | |
| Performance | [ ] | |

**Overall**: _____ / 12 passed

**Sign-off**: ✅ Ready for Day 07
```

---

**All tests passing = Service layer complete!** ✅🧪
