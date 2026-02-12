# Day 02: Troubleshooting Guide

This document contains solutions to common IRT implementation issues.

---

## Statistical & Mathematical Errors

### ❌ Problem: Theta estimates are extreme values (+10 or -10)

**Symptoms:**
```python
>>> IRTEngine.estimate_theta(answers, questions)
{'theta': 10.0, 'se': 0.1}  # Unrealistic!
```

**Solution:**
```python
# Ensure proper bounds in optimization
result = minimize_scalar(
    lambda t: cls.log_likelihood(t, answer_pattern, questions),
    bounds=(-4, 4),  # Must set bounds!
    method='bounded'  # Must  use bounded method
)

# Handle edge cases
if all(answer_pattern):  # All correct
    return {'theta': 3.0, 'se': 0.5}
if not any(answer_pattern):  # All incorrect
    return {'theta': -3.0, 'se': 0.5}
```

**Prevention:** Always bound optimization and handle extreme answer patterns.

---

### ❌ Problem: `log(0)` or `log(negative)` errors

**Symptoms:**
```python
RuntimeWarning: invalid value encountered in log
```

**Solution:**
```python
# Clip probabilities to avoid log(0)
p = IRTEngine.probability(theta, a, b, c)
p = np.clip(p, 1e-10, 1 - 1e-10)  # Add this!

if is_correct:
    ll += np.log(p)
else:
    ll += np.log(1 - p)
```

**Prevention:** Always clip probabilities before log operations.

---

### ❌ Problem: Standard Error not converging

**Symptoms:**
```python
# After 20 questions, SE still 0.8
session.current_se  # 0.85 (should be < 0.3)
```

**Solution:**
```python
# Check question discrimination values
questions = QuestionBank.objects.filter(skill=skill)
for q in questions:
    print(f"Question {q.id}: a={q.discrimination_a}")
    # a should be > 0.5, ideally 1.0-2.0

# Low discrimination = low information = slow convergence
# Regenerate questions with higher discrimination_a values
```

**Prevention:** Ensure questions have realistic IRT parameters (a ∈ [0.8, 2.0]).

---

### ❌ Problem: `scipy` optimization fails

**Symptoms:**
```python
OptimizeWarning: Optimization converged to invalid value
```

**Solution:**
```python
# Add bounds and check for valid inputs
if len(answer_pattern) == 0:
    return {'theta': 0.0, 'se': 1.0, 'converged': False}

if len(answer_pattern) < 3:
    # Not enough data for reliable estimation
    # Use simpler calculation
    correct_count = sum(answer_pattern)
    theta_estimate = (correct_count / len(answer_pattern) - 0.5) * 2
    return {'theta': theta_estimate, 'se': 0.8, 'converged': False}

# For sufficient data, use scipy
result = minimize_scalar(...)
if not result.success:
    # Fall back to simple estimate
    return {'theta': 0.0, 'se': 1.0, 'converged': False}
```

---

## Model & Database Errors

### ❌ Problem: ArrayField not working

**Symptoms:**
```python
django.db.utils.ProgrammingError: column "options" is of type character varying[] but expression is of type text
```

**Solution:**
```python
# Ensure proper ArrayField usage
from django.contrib.postgres.fields import ArrayField

class QuestionBank(models.Model):
    options = ArrayField(
        models.CharField(max_length=500),  # Base field type
        size=4  # Fixed size
    )

# In migration, ensure PostgreSQL backend
# ArrayField only works with PostgreSQL, not SQLite
```

**Prevention:** Use PostgreSQL, not SQLite, for ArrayField support.

---

### ❌ Problem: Circular import between assessment and users

**Symptoms:**
```python
ImportError: cannot import name 'UserProficiency' from partially initialized module 'users.models'
```

**Solution:**
```python
# Use lazy imports or string references
def calculate_skill_gaps(user, occupation):
    from users.models import UserProficiency  # Import inside function
    
    # Or use apps.get_model
    from django.apps import apps
    UserProficiency = apps.get_model('users', 'UserProficiency')
```

---

## API & Service Layer Errors

### ❌ Problem: Questions repeat in assessment

**Symptoms:**
```
User gets same question twice in one session
```

**Solution:**
```python
# Ensure answered questions are excluded
answered_question_ids = session.answers.values_list('question_id', flat=True)

available_questions = QuestionBank.objects.filter(
    skill=session.skill
).exclude(
    id__in=answered_question_ids  # Must exclude!
)
```

---

### ❌ Problem: Session doesn't terminate despite convergence

**Symptoms:**
```python
session.current_se = 0.25  # Below threshold
session.status = 'active'  # Still active!
```

**Solution:**
```python
# Ensure status update logic in submit_answer
if session.should_terminate:
    if session.has_converged:
        session.status = 'converged'
    else:
        session.status = 'completed'
    session.completed_at = timezone.now()  # Don't forget timestamp!

session.save()  # Must save!
```

---

### ❌ Problem: Skill gaps calculation fails with no proficiency data

**Symptoms:**
```python
UserProficiency.DoesNotExist: UserProficiency matching query does not exist
```

**Solution:**
```python
# Use try/except or get_or_create
try:
    proficiency = UserProficiency.objects.get(user=user, skill=skill)
    current_theta = proficiency.theta
except UserProficiency.DoesNotExist:
    current_theta = -2.0  # Assume low proficiency if not assessed
    # Or skip this skill in gap calculation
```

---

## Testing & Validation Errors

### ❌ Problem: Test theta estimation gives inconsistent results

**Symptoms:**
```python
# Same answer pattern, different theta estimates on different runs
```

**Solution:**
```python
# Set random seed for reproducibility in tests
import numpy as np
np.random.seed(42)

# Or use deterministic optimization
result = minimize_scalar(
    objective,
    bounds=bounds,
    method='bounded',
    options={'xatol': 1e-8}  # Tighter tolerance
)
```

---

### ❌ Problem: Information function returns negative values

**Symptoms:**
```python
info = IRTEngine.information(theta, a, b, c)
# info = -0.5  # Should never be negative!
```

**Solution:**
```python
# Check for invalid IRT parameters
if a <= 0:
    raise ValueError(f"Discrimination a must be positive, got {a}")
if not 0 <= c < 1:
    raise ValueError(f"Guessing c must be in [0, 1), got {c}")

# Ensure probability calculation is correct
p = cls.probability(theta, a, b, c)
q = 1 - p

# Information formula
info = (a ** 2 * p * q) / ((1 - c) ** 2)
return max(0, info)  # Safeguard against numerical errors
```

---

## Performance Issues

### ❌ Problem: Adaptive selection slow with many questions

**Symptoms:**
```
get_next_question takes 5+ seconds
```

**Solution:**
```python
# Optimize by calculating information in bulk
available_questions = QuestionBank.objects.filter(...)

# Instead of iterating in Python
max_info_question = max(
    available_questions,
    key=lambda q: IRTEngine.information(
        current_theta, q.discrimination_a, q.difficulty_b, q.guessing_c
    )
)

# Better: Use database-level filtering
# Pre-filter to questions near current theta
nearby_questions = available_questions.filter(
    difficulty_b__gte=current_theta - 1.5,
    difficulty_b__lte=current_theta + 1.5
)

# Then find max information from smaller set
```

---

### ❌ Problem: MLE optimization too slow

**Symptoms:**
```
estimate_theta takes 2+ seconds per call
```

**Solution:**
```python
# Use faster optimization method
from scipy.optimize import minimize

# Instead of minimize_scalar, use minimize with gradient
def neg_log_likelihood_with_grad(theta, answers, questions):
    # Implement with gradient for faster convergence
    pass

# Or use simpler methods for initial estimates
# Only use full MLE after 5+ questions
if len(answer_pattern) >= 5:
    result = minimize_scalar(...)
else:
    # Use simple scoring
    theta_estimate = (correct_count / total) * 4 - 2
```

---

## Data Quality Issues

### ❌ Problem: Unrealistic IRT parameters in question bank

**Symptoms:**
```python
# Questions with:
difficulty_b = 10.0  # Way too high
discrimination_a = 0.1  # Way too low
guessing_c = 0.8  # Too high for 4 options
```

**Solution:**
```python
# Add validation to QuestionBank model
from django.core.validators import MinValueValidator, MaxValueValidator

class QuestionBank(models.Model):
    difficulty_b = models.FloatField(
        validators=[MinValueValidator(-3.0), MaxValueValidator(3.0)]
    )
    discrimination_a = models.FloatField(
        validators=[MinValueValidator(0.5), MaxValueValidator(2.5)]
    )
    guessing_c = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(0.5)]
    )
```

**Prevention:** Validate IRT parameters on save.

---

## Integration Issues

### ❌ Problem: Celery task for theta calculation fails

**Symptoms:**
```python
Task assessment.tasks.calculate_theta[abc-123] raised exception
```

**Solution:**
```python
# In assessment/tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=3)
def calculate_theta_async(self, session_id):
    try:
        session = DiagnosticSession.objects.get(id=session_id)
        # ... calculation logic
        
    except Exception as exc:
        logger.error(f"Theta calculation failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
```

---

## Complete System Test

```python
# Run this to validate entire IRT system
from assessment.services import AssessmentService
from assessment.irt_engine import IRTEngine
from users.models import User
from skills.models import Skill

# 1. Start session
user = User.objects.first()
skill = Skill.objects.first()
session = AssessmentService.start_session(user, skill)

# 2. Answer questions
for i in range(10):
    question = AssessmentService.get_next_question(session)
    if not question:
        break
    
    # Simulate answer
    answer = question.correct_answer if i % 2 == 0 else (question.correct_answer + 1) % 4
    
    AssessmentService.submit_answer(session, question, answer)
    
    print(f"Q{i+1}: theta={session.current_theta:.2f}, SE={session.current_se:.2f}")

# 3. Check convergence
print(f"\nFinal: theta={session.current_theta:.2f}, SE={session.current_se:.2f}")
print(f"Converged: {session.has_converged}")
print(f"Status: {session.status}")
```

---

**If all else fails**: Drop assessment tables, delete migrations, and rebuild from scratch in development!
