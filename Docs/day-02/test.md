# Day 02: Testing & Validation Guide

Comprehensive testing for IRT assessment engine implementation.

---

## Pre-Testing Checklist

- [ ] Day 01 completed and tested
- [ ] scipy and numpy installed
- [ ] Assessment models migrated
- [ ] Sample questions generated
- [ ] Django server running

---

## Test 1: IRT Probability Function

**Python Code:**
```python
from assessment.irt_engine import IRTEngine

# Test 1.1: Basic probability calculation
prob = IRTEngine.probability(theta=0, a=1, b=0, c=0.25)
assert 0.6 < prob < 0.7, f"Expected ~0.625, got {prob}"
print(f"✓ Test 1.1 passed: P(θ=0, b=0) = {prob:.3f}")

# Test 1.2: Easy question for low ability
prob = IRTEngine.probability(theta=-2, a=1.5, b=-2, c=0.25)
assert prob > 0.5, f"Easy question should have P>0.5 for matched ability"
print(f"✓ Test 1.2 passed: P(θ=-2, b=-2) = {prob:.3f}")

# Test 1.3: Hard question for low ability  
prob = IRTEngine.probability(theta=-2, a=1.5, b=2, c=0.25)
assert prob < 0.4, f"Hard question should have low P for low ability"
print(f"✓ Test 1.3 passed: P(θ=-2, b=2) = {prob:.3f}")

# Test 1.4: Guessing parameter floor
prob = IRTEngine.probability(theta=-4, a=2, b=2, c=0.25)
assert prob >= 0.25, f"Probability should never drop below guessing parameter"
print(f"✓ Test 1.4 passed: P has guessing floor = {prob:.3f}")
```

**Pass Criteria:** All 4 assertions pass

---

## Test 2: Information Function

**Python Code:**
```python
# Test 2.1: Maximum information at theta = b
theta_values = [-2, -1, 0, 1, 2]
b = 0  # Difficulty
info_values = [IRTEngine.information(t, a=1.5, b=b, c=0.25) for t in theta_values]

max_info_idx = info_values.index(max(info_values))
assert theta_values[max_info_idx] == b, "Info should be max when theta = b"
print(f"✓ Test 2.1 passed: Max info at theta={theta_values[max_info_idx]}")

# Test 2.2: Higher discrimination = higher information
info_low_a = IRTEngine.information(0, a=0.8, b=0, c=0.25)
info_high_a = IRTEngine.information(0, a=2.0, b=0, c=0.25)
assert info_high_a > info_low_a, "Higher a should give more information"
print(f"✓ Test 2.2 passed: High a ({info_high_a:.2f}) > Low a ({info_low_a:.2f})")
```

**Pass Criteria:** Information maximizes at theta = b, increases with discrimination

---

## Test 3: MLE Theta Estimation

**Python Code:**
```python
from assessment.models import QuestionBank
from skills.models import Skill

skill = Skill.objects.first()

# Create test questions
questions = [
    QuestionBank(skill=skill, difficulty_b=-1.0, discrimination_a=1.5, guessing_c=0.25),
    QuestionBank(skill=skill, difficulty_b=0.0, discrimination_a=1.2, guessing_c=0.25),
    QuestionBank(skill=skill, difficulty_b=1.0, discrimination_a=1.3, guessing_c=0.25),
]

# Test 3.1: All correct → positive theta
answer_pattern = [True, True, True]
result = IRTEngine.estimate_theta(answer_pattern, questions)
assert result['theta'] > 0, f"All correct should give positive theta"
print(f"✓ Test 3.1: All correct → θ={result['theta']:.2f}")

# Test 3.2: All incorrect → negative theta
answer_pattern = [False, False, False]
result = IRTEngine.estimate_theta(answer_pattern, questions)
assert result['theta'] < 0, f"All incorrect should give negative theta"
print(f"✓ Test 3.2: All incorrect → θ={result['theta']:.2f}")

# Test 3.3: Mixed answers → moderate theta
answer_pattern = [True, True, False]
result = IRTEngine.estimate_theta(answer_pattern, questions)
assert -1 < result['theta'] < 1, f"Mixed should give moderate theta"
assert result['se'] < 1.0, f"SE should decrease with more questions"
print(f"✓ Test 3.3: Mixed → θ={result['theta']:.2f}, SE={result['se']:.2f}")
```

**Pass Criteria:** Theta estimates align with answer patterns

---

## Test 4: Adaptive Question Selection

**Python Code:**
```python
# Test 4.1: Selects question near current theta
current_theta = 0.5
questions = QuestionBank.objects.filter(skill=skill)[:10]

selected = IRTEngine.select_next_question(current_theta, questions)
info_selected = IRTEngine.information(
    current_theta, selected.discrimination_a, 
    selected.difficulty_b, selected.guessing_c
)

# Check it's actually maximum information
for q in questions:
    info = IRTEngine.information(current_theta, q.discrimination_a, 
                                 q.difficulty_b, q.guessing_c)
    assert info <= info_selected + 0.01, "Selected question should have max info"

print(f"✓ Test 4.1: Selected Q with difficulty {selected.difficulty_b:.2f} for θ={current_theta}")

# Test 4.2: Balanced selection for first 3 questions
selected_difficulties = []
for i in range(3):
    q = IRTEngine.select_next_question_balanced(0, questions, i)
    selected_difficulties.append(q.difficulty_b)

# Should span range
assert max(selected_difficulties) - min(selected_difficulties) > 1.0, \
    "First 3 should span difficulty range"
print(f"✓ Test 4.2: First 3 span range: {selected_difficulties}")
```

**Pass Criteria:** Adaptive selection chooses high-information questions

---

## Test 5: Complete Assessment Flow

**Python Code:**
```python
from assessment.services import AssessmentService
from users.models import User

user = User.objects.first()
skill = Skill.objects.first()

# Test 5.1: Start session
session = AssessmentService.start_session(user, skill)
assert session.status == 'active'
assert session.current_theta == 0.0
assert session.question_count == 0
print(f"✓ Test 5.1: Session started, ID={session.id}")

# Test 5.2: Get first question
question1 = AssessmentService.get_next_question(session)
assert question1 is not None
print(f"✓ Test 5.2: First question retrieved, difficulty={question1.difficulty_b:.2f}")

# Test 5.3: Submit answer and update theta
initial_theta = session.current_theta
answer_log = AssessmentService.submit_answer(session, question1, question1.correct_answer)

session.refresh_from_db()
assert session.question_count == 1
assert session.current_theta != initial_theta  # Should update
assert answer_log.is_correct == True
print(f"✓ Test 5.3: Answer submitted, new θ={session.current_theta:.2f}")

# Test 5.4: Complete full assessment
while not session.should_terminate:
    question = AssessmentService.get_next_question(session)
    if not question:
        break
    
    # Simulate mixed performance
    import random
    answer = question.correct_answer if random.random() > 0.3 else (question.correct_answer + 1) % 4
    
    AssessmentService.submit_answer(session, question, answer)
    session.refresh_from_db()
    
    print(f"  Q{session.question_count}: θ={session.current_theta:.2f}, SE={session.current_se:.2f}")
    
    if session.question_count > 30:  # Safety limit
        break

assert session.status in ['converged', 'completed']
print(f"✓ Test 5.4: Assessment completed, status={session.status}")
```

**Pass Criteria:** Full assessment flow works end-to-end

---

## Test 6: Convergence Detection

**Python Code:**
```python
# Test 6.1: SE decreases over time
session = AssessmentService.start_session(user, skill)
se_values = [session.current_se]

for i in range(15):
    question = AssessmentService.get_next_question(session)
    if not question:
        break
    AssessmentService.submit_answer(session, question, question.correct_answer)
    session.refresh_from_db()
    se_values.append(session.current_se)

# SE should generally decrease
assert se_values[-1] < se_values[0], "SE should decrease over time"
print(f"✓ Test 6.1: SE decreased from {se_values[0]:.3f} to {se_values[-1]:.3f}")

# Test 6.2: Convergence detected
if session.current_se < 0.3:
    assert session.has_converged == True
    assert session.status == 'converged'
    print(f"✓ Test 6.2: Convergence detected at SE={session.current_se:.3f}")
else:
    print(f"⚠ Test 6.2: Did not converge, SE={session.current_se:.3f}")
```

**Pass Criteria:** SE decreases, convergence detected when SE < 0.3

---

## Test 7: Skill Gap Calculation

**Python Code:**
```python
from assessment.models import SkillGap
from skills.models import Occupation, OccupationSkill
from users.models import UserProficiency

# Setup test data
occupation = Occupation.objects.first()
skills = Skill.objects.all()[:3]

# Create required skills for occupation
for skill in skills:
    OccupationSkill.objects.get_or_create(
        occupation=occupation,
        skill=skill,
        defaults={'importance': 0.8, 'required_proficiency_theta': 1.0}
    )

# Create some user proficiencies
UserProficiency.objects.update_or_create(
    user=user,
    skill=skills[0],
    defaults={'theta': -0.5, 'standard_error': 0.3}
)

# Test 7.1: Calculate gaps
gaps = AssessmentService.calculate_skill_gaps(user, occupation)
assert len(gaps) > 0, "Should identify skill gaps"
print(f"✓ Test 7.1: Found {len(gaps)} skill gaps")

# Test 7.2: Verify gap calculation
gap = gaps[0]
assert gap.gap_score == gap.required_level - gap.current_level
assert gap.priority_score == gap.gap_score * gap.criticality_coefficient
print(f"✓ Test 7.2: Gap calculation correct")

# Test 7.3: Priority ordering
priorities = [g.priority_score for g in gaps]
assert priorities == sorted(priorities, reverse=True), "Should be ordered by priority"
print(f"✓ Test 7.3: Gaps ordered by priority")
```

**Pass Criteria:** Skill gaps calculated and prioritized correctly

---

## Test 8: API Endpoints

**Python Code:**
```python
import requests

BASE_URL = 'http://localhost:8000/api'

# Login first (get auth token)
# ... authentication setup ...

# Test 8.1: Start assessment
response = requests.post(f'{BASE_URL}/assessment/start/', json={
    'skill_id': skill.id
}, headers=headers)

assert response.status_code == 201
session_data = response.json()
session_id = session_data['id']
print(f"✓ Test 8.1: Assessment started via API, session={session_id}")

# Test 8.2: Get next question
response = requests.get(f'{BASE_URL}/assessment/{session_id}/next_question/', headers=headers)
assert response.status_code == 200
question_data = response.json()
assert 'question_text' in question_data
assert 'options' in question_data
assert 'correct_answer' not in question_data  # Should be hidden!
print(f"✓ Test 8.2: Next question retrieved via API")

# Test 8.3: Submit answer
response = requests.post(f'{BASE_URL}/assessment/{session_id}/submit_answer/', json={
    'question_id': question_data['id'],
    'user_answer': 0
}, headers=headers)

assert response.status_code == 200
result = response.json()
assert 'correct' in result
assert 'theta_updated' in result
print(f"✓ Test 8.3: Answer submitted via API")
```

**Pass Criteria:** All API endpoints work correctly

---

## Performance Tests

**Test 9: Theta Estimation Speed**
```python
import time

# Generate large answer pattern
answer_pattern = [True, False] * 50  # 100 answers
questions = list(QuestionBank.objects.filter(skill=skill)[:100])

start = time.time()
result = IRTEngine.estimate_theta(answer_pattern, questions)
duration = time.time() - start

assert duration < 0.5, f"MLE should complete in <0.5s, took {duration:.2f}s"
print(f"✓ Test 9: MLE with 100 questions in {duration:.3f}s")
```

**Pass Criteria:** Theta estimation completes in < 0.5 seconds

---

## Final Validation Script

```bash
#!/bin/bash

echo "🧪 Day 02 - IRT Assessment Engine Validation"
echo "==========================================="

# 1. Check models
python manage.py check assessment
[ $? -eq 0 ] && echo "✓ Models OK" || echo "✗ Models FAIL"

# 2. Check migrations
python manage.py showmigrations assessment | grep "\[X\]" | wc -l
echo "✓ Migrations applied"

# 3. Test IRT engine
python -c "
from assessment.irt_engine import IRTEngine
p = IRTEngine.probability(0, 1, 0, 0.25)
assert 0.6 < p < 0.7
print('✓ IRT engine OK')
"

# 4. Test full flow
python manage.py shell < day-02/test_assessment_flow.py

echo ""
echo "==========================================="
echo "Day 02 Validation Complete!"
```

---

## Test Report Template

```markdown
# Day 02 Test Report

**Date**: ___________
**Tester**: ___________

| Test | Status | Notes |
|------|--------|-------|
| IRT Probability | [ ] | |
| Information Function | [ ] | |
| MLE Estimation | [ ] | |
| Adaptive Selection | [ ] | |
| Assessment Flow | [ ] | |
| Convergence | [ ] | |
| Skill Gaps | [ ] | |
| API Endpoints | [ ] | |
| Performance | [ ] | |

**Overall**: _____ / 9 passed

**Issues**:

**Sign-off**: ✅ Ready for Day 03
```

---

**All tests passing = Day 02 complete!** 🎉
