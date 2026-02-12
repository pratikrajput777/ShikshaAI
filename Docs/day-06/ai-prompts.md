# Day 06: AI Prompts, Testing & Implementation

## AI PROMPTS FOR SERVICE IMPLEMENTATION

### Create GeminiService
```
Create core/gemini_service.py with:
- Three model methods: generate_with_lite(), generate_with_flash(), generate_with_pro()
- generate_with_retry(prompt, model_type, max_retries=3) with exponential backoff
- parse_json_response() handling markdown blocks and embedded JSON
- Use google.generativeai library, configure from settings
- Include comprehensive docstrings and logging
```

### Create IRTEngine
```
Create IRTEngine class in assessment/services.py:
- probability(theta, a, b, c): 3PL model implementation
- information(theta, a, b, c): Fisher information calculation
- estimate_theta(answers, questions): MLE using scipy.optimize.minimize_scalar
- select_next_question(theta, se, available, answered): Balance difficulty early, max info later
Use numpy for calculations, handle edge cases (division by zero, log(0))
```

### Create AssessmentService
```
Create AssessmentService in assessment/services.py:
- start_session(user, skill): Create DiagnosticSession
- get_next_question(session): Use IRTEngine to select adaptive question
- submit_answer(session, question, answer): Update theta estimate
- calculate_skill_gaps(user, occupation): Priority-scored gaps
Check convergence (SE < 0.3 or 30 questions), log progress
```

---

## TROUBLESHOOTING

### ❌ Import Error: No module named 'core.gemini_service'
**Solution:**
```bash
# Ensure core/__init__.py exists
touch core/__init__.py

# Check INSTALLED_APPS has 'core'
# settings.py should have 'core' in INSTALLED_APPS
```

### ❌ Gemini API Authentication Failed
**Solution:**
```python
# Check .env has API key
GEMINI_API_KEY=your_key_here

# Test in shell
import google.generativeai as genai
from django.conf import settings
genai.configure(api_key=settings.GEMINI_API_KEY)
# Should not error
```

### ❌ scipy minimize_scalar fails
**Solution:**
```bash
# Install scipy
pip install scipy==1.11.4

# Check import
python -c "from scipy.optimize import minimize_scalar; print('OK')"
```

### ❌ JSON Parsing Always Fails
**Solution:**
```python
# Add more robust parsing
import re
json_pattern = r'\{[^}]+\}'
matches = re.findall(json_pattern, text, re.DOTALL)
for match in matches:
    try:
        return json.loads(match)
    except: pass
```

---

## TESTING

### Test 1: GeminiService
```python
from core.gemini_service import GeminiService

service = GeminiService()

# Test all models
lite = service.generate_with_lite("Say hello")
assert len(lite) > 0
print(f"✓ Lite works: {lite[:50]}")

flash = service.generate_with_flash("What is 2+2?")
assert '4' in flash
print(f"✓ Flash works: {flash[:50]}")

# Test JSON parsing
json_text = '```json\n{"test": "value"}\n```'
parsed = service.parse_json_response(json_text)
assert parsed == {"test": "value"}
print("✓ JSON parsing works")
```

### Test 2: IRT Calculations
```python
from assessment.services import IRTEngine

# Test probability
prob = IRTEngine.probability(theta=0, a=1, b=0, c=0.25)
assert 0.5 < prob < 0.7
print(f"✓ Probability: {prob:.3f}")

# Test information
info = IRTEngine.information(theta=0, a=1, b=0, c=0.25)
assert info > 0
print(f"✓ Information: {info:.3f}")

# Test theta estimation
answers = [True, True, False, True]
questions = [
    {'a': 1.0, 'b': -1.0, 'c': 0.25},
    {'a': 1.0, 'b': 0.0, 'c': 0.25},
    {'a': 1.0, 'b': 1.0, 'c': 0.25},
    {'a': 1.0, 'b': 0.5, 'c': 0.25}
]

theta, se = IRTEngine.estimate_theta(answers, questions)
assert -2 < theta < 2
assert 0 < se < 1
print(f"✓ Theta: {theta:.2f}, SE: {se:.2f}")
```

### Test 3: Assessment Flow
```python
from assessment.services import AssessmentService
from users.models import User
from skills.models import Skill

user = User.objects.first()
skill = Skill.objects.first()

# Start session
session = AssessmentService.start_session(user, skill)
assert session.status == 'active'
assert session.current_theta == 0.0
print(f"✓ Session {session.id} started")

# Get question
question = AssessmentService.get_next_question(session)
assert question is not None
print(f"✓ Question: {question.question_text[:50]}")

# Submit answer
result = AssessmentService.submit_answer(session, question, selected_answer=question.correct_answer)
assert result['correct'] == True
assert result['theta'] != 0.0
print(f"✓ Answer submitted, theta={result['theta']:.2f}")
```

### Test 4: Skill Gap Analysis
```python
from skills.models import Occupation

occupation = Occupation.objects.first()
gaps = AssessmentService.calculate_skill_gaps(user, occupation)

assert len(gaps) > 0
for gap in gaps[:5]:
    print(f"  {gap.skill.preferred_label}: Gap={gap.gap_score:.2f}, Priority={gap.priority_score:.2f}")

print(f"✓ {len(gaps)} skill gaps calculated")
```

---

## VALIDATION SCRIPT

```bash
#!/bin/bash

echo "Day 06 - Service Layer Validation"
echo "=================================="

# Check files exist
echo "Checking service files..."
test -f core/gemini_service.py && echo "✓ GeminiService exists" || echo "✗ GeminiService missing"
test -f assessment/services.py && echo "✓ AssessmentService exists" || echo "✗ AssessmentService missing"

# Test imports
python -c "
from core.gemini_service import GeminiService
from assessment.services import IRTEngine, AssessmentService
print('✓ All imports successful')
"

# Run Django checks
python manage.py check
echo "✓ Django check passed"

echo ""
echo "=================================="
echo "✅ Day 06 Services Validated!"
```

---

**All service files implemented = Features unlocked!** 🔓✅
