# Day 06: Troubleshooting Guide - Service Layer Implementation

Solutions for service implementation, Gemini API, and IRT calculation issues.

---

## Service Import Errors

### ❌ Problem: Cannot import GeminiService

**Symptoms:**
```python
ImportError: cannot import name 'GeminiService' from 'core.gemini_service'
ModuleNotFoundError: No module named 'core.gemini_service'
```

**Solution:**
```bash
# 1. Ensure core/__init__.py exists
touch core/__init__.py

# 2. Check file created in correct location
ls -la core/gemini_service.py

# 3. Verify INSTALLED_APPS includes 'core'
# In settings.py:
INSTALLED_APPS = [
    ...
    'core',
    ...
]

# 4. Restart Django server
python manage.py runserver

# 5. Test import in shell
python manage.py shell
>>> from core.gemini_service import GeminiService
>>> print("Success!")
```

---

## Gemini API Issues

### ❌ Problem: API Key Not Found

**Symptoms:**
```python
google.api_core.exceptions.InvalidArgument: 400 API key not valid
```

**Solution:**
```bash
# 1. Check .env file
cat .env | grep GEMINI_API_KEY

# 2. Verify settings.py loads it
python manage.py shell
>>> from django.conf import settings
>>> print(settings.GEMINI_API_KEY[:10])  # Should show first 10 chars

# 3. Get valid API key from Google AI Studio
# Visit: https://aistudio.google.com/app/apikey

# 4. Update .env
echo "GEMINI_API_KEY=your-actual-key-here" >> .env

# 5. Restart server to reload environment
```

---

### ❌ Problem: Gemini Model Not Found

**Symptoms:**
```python
google.api_core.exceptions.InvalidArgument: 400 models/gemini-2.0-flash-lite is not found
```

**Solution:**
```python
# Use correct model names (as of January 2026)
GEMINI_MODEL_LITE = 'gemini-1.5-flash-8b'  # Lightweight, fast
GEMINI_MODEL_FLASH = 'gemini-1.5-flash'    # Balanced
GEMINI_MODEL_PRO = 'gemini-1.5-pro'        # Most capable

# Update in .env:
GEMINI_MODEL_LITE=gemini-1.5-flash-8b
GEMINI_MODEL_FLASH=gemini-1.5-flash
GEMINI_MODEL_PRO=gemini-1.5-pro

# List available models:
import google.generativeai as genai
genai.configure(api_key='your-key')
for model in genai.list_models():
    print(model.name)
```

---

### ❌ Problem: JSON Parsing Fails

**Symptoms:**
```python
ValueError: Could not extract valid JSON from response: Here is the data...
```

**Solution:**
```python
# Enhanced JSON parsing in GeminiService:
def parse_json_response(self, response_text: str) -> Dict:
    """More robust JSON extraction."""
    import re
    import json
    
    text = response_text.strip()
    
    # Strategy 1: Remove all markdown
    text = re.sub(r'```(?:json)?\n?', '', text)
    text = re.sub(r'```', '', text)
    
    # Strategy 2: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Strategy 3: Find JSON object
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass
    
    # Strategy 4: Find JSON array
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass
    
    # Strategy 5: Extract with regex
    json_pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    raise ValueError(f"No valid JSON in: {text[:200]}...")
```

---

## IRT Calculation Errors

### ❌ Problem: scipy.optimize.minimize_scalar fails

**Symptoms:**
```python
ValueError: Bounds must be finite
RuntimeWarning: invalid value encountered in log
```

**Solution:**
```python
# Add bounds checking and safeguards:
def estimate_theta(answers, questions, initial_theta=0.0):
    """Safer MLE estimation."""
    if not answers or not questions:
        return initial_theta, 1.0
    
    def negative_log_likelihood(theta):
        # Bound theta to prevent overflow
        theta = np.clip(theta, -4, 4)
        
        ll = 0
        for answer, q in zip(answers, questions):
            # Calculate probability with safeguards
            a = np.clip(q['a'], 0.1, 3.0)
            b = np.clip(q['b'], -4, 4)
            c = np.clip(q['c'], 0.0, 0.5)
            
            p = c + (1 - c) / (1 + np.exp(-a * (theta - b)))
            
            # Avoid log(0) and log(1)
            p = np.clip(p, 1e-10, 1 - 1e-10)
            
            if answer:
                ll += np.log(p)
            else:
                ll += np.log(1 - p)
        
        return -ll if np.isfinite(-ll) else 1e10
    
    # Use bounded minimization
    result = minimize_scalar(
        negative_log_likelihood,
        bounds=(-4, 4),
        method='bounded',
        options={'xatol': 0.01}
    )
    
    theta = np.clip(result.x, -4, 4)
    
    # Calculate SE with protection
    try:
        total_info = sum(
            IRTEngine.information(theta, q['a'], q['b'], q['c'])
            for q in questions
        )
        se = 1.0 / np.sqrt(max(total_info, 0.01))
    except:
        se = 1.0
    
    return float(theta), float(se)
```

---

### ❌ Problem: Division by Zero in Information Function

**Symptoms:**
```python
RuntimeWarning: divide by zero encountered in double_scalars
```

**Solution:**
```python
@staticmethod
def information(theta: float, a: float, b: float, c: float) -> float:
    """Calculate information with safeguards."""
    # Clip parameters
    a = np.clip(a, 0.1, 3.0)
    b = np.clip(b, -4, 4)
    c = np.clip(c, 0.0, 0.5)
    theta = np.clip(theta, -4, 4)
    
    # Calculate probability
    p = c + (1 - c) / (1 + np.exp(-a * (theta - b)))
    
    # Ensure p is in valid range (not 0 or 1)
    p = np.clip(p, 0.01, 0.99)
    q = 1 - p
    
    # Calculate derivative
    p_prime = a * (p - c) * q / (1 - c)
    
    # Protection against division by zero
    denominator = p * q
    if denominator < 1e-10:
        return 0.0
    
    info = (p_prime ** 2) / denominator
    
    # Return finite value
    return float(info) if np.isfinite(info) else 0.0
```

---

## Assessment Service Issues

### ❌ Problem: No Questions Available for Skill

**Symptoms:**
```python
AssessmentService.get_next_question() returns None immediately
```

**Solution:**
```python
# Check QuestionBank has questions
from assessment.models import QuestionBank
from skills.models import Skill

skill = Skill.objects.first()
question_count = QuestionBank.objects.filter(skill=skill).count()
print(f"Questions for {skill}: {question_count}")

# If 0, create sample questions:
QuestionBank.objects.create(
    skill=skill,
    question_text="Sample question?",
    options=["A", "B", "C", "D"],
    correct_answer=0,
    difficulty_b=0.0,
    discrimination_a=1.0,
    guessing_c=0.25
)

# Or import from data file
python manage.py import_questions data/sample_questions.json
```

---

### ❌ Problem: Session Doesn't Converge

**Symptoms:**
```
Session reaches 30 questions but SE still > 0.3
```

**Solution:**
```python
# Debug theta estimation:
session = DiagnosticSession.objects.get(id=session_id)
logs = session.answer_logs.all()

print(f"Questions answered: {logs.count()}")
print(f"Current theta: {session.current_theta:.3f}")
print(f"Current SE: {session.current_se:.3f}")

# Check answer pattern
correct_count = logs.filter(is_correct=True).count()
print(f"Correct: {correct_count}/{logs.count()}")

# Check question difficulty spread
difficulties = [log.question.difficulty_b for log in logs]
print(f"Difficulty range: {min(difficulties):.2f} to {max(difficulties):.2f}")

# If SE not decreasing:
# 1. Questions might have poor discrimination (a < 0.5)
# 2. Questions might all be same difficulty
# 3. Need more questions with high information at current theta
```

---

## Performance Issues

### ❌ Problem: Theta Estimation Takes Too Long

**Symptoms:**
```
submit_answer() takes >5 seconds
```

**Solution:**
```python
# Optimize MLE:
1. Use better initial guess (current theta)
2. Reduce tolerance
3. Limit iteration count

result = minimize_scalar(
    negative_log_likelihood,
    bounds=(-4, 4),
    method='bounded',
    options={
        'maxiter': 20,  # Limit iterations
        'xatol': 0.05    # Looser tolerance
    }
)

# Or use faster approximation for real-time:
def estimate_theta_fast(answers, questions, current_theta):
    """Fast approximation using single Newton-Raphson step."""
    # Implementation using gradient descent instead of MLE
    pass
```

---

## Complete Service Test

```python
# End-to-end service test
from core.gemini_service import GeminiService
from assessment.services import IRTEngine, AssessmentService
from users.models import User
from skills.models import Skill

print("Testing Service Layer Implementation...")

# 1. Test GeminiService
print("\n1. Testing GeminiService...")
gemini = GeminiService()
response = gemini.generate_with_flash("Say 'Services work!'")
assert len(response) > 0
print(f"✓ Gemini: {response[:50]}")

# 2. Test IRTEngine
print("\n2. Testing IRTEngine...")
prob = IRTEngine.probability(0, 1, 0, 0.25)
assert 0 < prob < 1
print(f"✓ IRT Probability: {prob:.3f}")

info = IRTEngine.information(0, 1, 0, 0.25)
assert info > 0
print(f"✓ IRT Information: {info:.3f}")

# 3. Test AssessmentService
print("\n3. Testing AssessmentService...")
user = User.objects.first()
skill = Skill.objects.first()

session = AssessmentService.start_session(user, skill)
assert session.status == 'active'
print(f"✓ Session started: {session.id}")

question = AssessmentService.get_next_question(session)
if question:
    print(f"✓ Question retrieved: {question.question_text[:50]}")
    
    result = AssessmentService.submit_answer(session, question, question.correct_answer)
    print(f"✓ Answer submitted: theta={result['theta']:.2f}, SE={result['se']:.2f}")
else:
    print("⚠ No questions available for skill")

print("\n✅ All service tests PASSED!")
```

---

**All services working = Platform functional!** ✅🔧
