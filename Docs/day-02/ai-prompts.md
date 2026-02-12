# Day 02: AI Agent Prompts

This document contains ready-to-use prompts for AI coding assistants for Day 02 IRT implementation.

---

## Phase 1: Assessment Models

### Prompt 1.1: DiagnosticSession Model with IRT Tracking

```
Create a Django model called DiagnosticSession in assessment/models.py that tracks IRT-based diagnostic assessment sessions:

1. Fields:
   - user (ForeignKey to User)
   - skill (ForeignKey to Skill)
   - current_theta (FloatField, default 0.0) - current ability estimate
   - current_se (FloatField, default 1.0) - standard error of theta
   - question_count (IntegerField, default 0)
   - status (CharField with choices: active, converged, abandoned, completed)
   - started_at, completed_at, last_activity (DateTimeFields)

2. Meta:
   - db_table = 'diagnostic_sessions'
   - indexes on [user, skill, status] and [status, last_activity]

3. Property methods:
   - has_converged: returns True if current_se < 0.3
   - should_terminate: returns True if converged OR question_count >= 30

Include docstrings explaining IRT theta and standard error.
```

---

###Prompt 1.2: QuestionBank with IRT Parameters

```
Create a QuestionBank model for storing IRT-calibrated questions:

1. Fields:
   - skill (ForeignKey to Skill)
   - question_text (TextField)
   - options (ArrayField of CharField, size 4)
   - correct_answer (IntegerField, 0-3, with validators)
   - difficulty_b (FloatField) - IRT difficulty parameter
   - discrimination_a (FloatField, default 1.0) - IRT discrimination
   - guessing_c (FloatField, default 0.25, 0-1 range) - IRT guessing parameter
   - times_used, times_correct (IntegerField, default 0)
   - generated_by_ai (BooleanField)
   - generation_prompt (TextField)
   - created_at, updated_at

2. Meta:
   - db_table = 'question_bank'
   - indexes on [skill, difficulty_b] and [difficulty_b]

3. Methods:
   - difficulty_rating property: returns (times_correct/times_used)*100 or None

Explain what a, b, c parameters mean in IRT 3PL model.
```

---

## Phase 2: IRT Calculation Engine

### Prompt 2.1: IRT 3PL Probability Function

```
Create an IRTEngine class in assessment/irt_engine.py with:

1. Static method `probability(theta, a, b, c)`:
   - Implements 3-Parameter Logistic Model
   - Formula: P(θ) = c + (1-c) / (1 + e^(-a(θ-b)))
   - Parameters:
     - theta: ability level
     - a: discrimination (how well question differentiates)
     - b: difficulty (on same scale as theta)
     - c: guessing probability
   - Use numpy for calculations
   - Return probability between 0 and 1

2. Static method `information(theta, a, b, c)`:
   - Fisher information function
   - Formula: I(θ) = a² × P(θ) × Q(θ) / (1-c)²
   - where Q(θ) = 1 - P(θ)

Include docstrings with formula explanations and example usage.
Use numpy for mathematical operations.
```

---

### Prompt 2.2: Maximum Likelihood Estimation

```
Implement MLE theta estimation in IRTEngine class:

1. Static method `log_likelihood(theta, answer_pattern, questions)`:
   - Calculate log-likelihood for given theta
   - For each answer:
     - If correct: add log(P(θ))
     - If incorrect: add log(1 - P(θ))
   - Use np.clip to avoid log(0)
   - Return negative LL for minimization

2. Class method `estimate_theta(answer_pattern, questions, bounds=(-4, 4))`:
   - Use scipy.optimize.minimize_scalar
   - Minimize negative log-likelihood
   - Calculate standard error: SE = 1 / sqrt(total_information)
   - Return dict with:
     - 'theta': estimated ability
     - 'se': standard error
     - 'converged': optimization success

3. Handle edge cases:
   - Empty answer pattern: return theta=0, se=1
   - All correct/incorrect

Include example usage with test questions and answer patterns.
```

---

### Prompt 2.3: Adaptive Question Selection

```
Add adaptive question selection to IRTEngine:

1. Class method `select_next_question(current_theta, available_questions)`:
   - For each question, calculate information at current_theta
   - Select question with maximum information
   - Return QuestionBank object

2. Class method `select_next_question_balanced(current_theta, available_questions, answered_count)`:
   - First 3 questions: spread across difficulty range (-1.5, 0, 1.5)
   - Later questions: maximize information
   - This ensures good coverage while being adaptive

Explain why maximum information criterion works for adaptive testing.
```

---

## Phase 3: Assessment Service Layer

### Prompt 3.1: AssessmentService Class

```
Create AssessmentService class in assessment/services.py:

1. Static method `start_session(user, skill)`:
   - Create new DiagnosticSession
   - Initialize theta=0, se=1, status='active'
   - Return session object

2. Static method `get_next_question(session)`:
   - Check if session.should_terminate
   - Get questions already answered
   - Get available questions for skill
   - Use IRTEngine.select_next_question_balanced
   - Return next question or None

3. Static method `submit_answer(session, question, user_answer)`:
   - Check if answer correct
   - Get all previous answers + current
   - Use IRTEngine.estimate_theta to get new theta
   - Create AnswerLog with before/after theta
   - Update session theta, se, question_count
   - Check if should terminate, update status
   - Update question statistics
   - Return answer_log

Handle all edge cases and use transactions where needed.
```

---

### Prompt 3.2: Assessment API Views

```
Create REST API viewsets for diagnostic assessment in assessment/views.py:

1. AssessmentViewSet with actions:
   
   @action POST /start/:
   - Accept skill_id in request body
   - Call AssessmentService.start_session
   - Return session data
   
   @action GET /<session_id>/next_question/:
   - Get next question for session
   - If None, return completion status with final theta
   - Otherwise return question (without correct_answer)
   
   @action POST /<session_id>/submit_answer/:
   - Accept question_id and user_answer
   - Call AssessmentService.submit_answer
   - Return: correct/incorrect, updated theta, se, should_continue

Use proper serializers that hide sensitive data (correct answers, IRT params from client).
```

---

## Phase 4: Skill Gap Analysis

### Prompt 4.1: SkillGap Model

```
Create SkillGap model in assessment/models.py:

1. Fields:
   - user, occupation, skill (ForeignKeys)
   - current_level (FloatField) - user's current theta
   - required_level (FloatField) - required theta for occupation
   - gap_score (FloatField) - difference: required - current
   - criticality_coefficient (FloatField) - weight based on importance
   - priority_score (FloatField) - gap * criticality
   - addressed (BooleanField) - if included in study plan
   - computed_at, updated_at

2. Meta:
   - unique_together = [user, occupation, skill]
   - ordering = ['-priority_score']
   - indexes on priority_score

Explain how priority scoring helps focus learning efforts.
```

---

### Prompt 4.2: Skill Gap Calculation

```
Add to AssessmentService class:

Static method `calculate_skill_gaps(user, target_occupation)`:

1. Get all required skills for occupation (from OccupationSkill)
2. For each required skill:
   - Get user's current theta (from UserProficiency)
   - If not assessed, assume theta = -2.0
   - Calculate gap = required_theta - current_theta
   - If gap > 0:
     - Calculate criticality coefficient:
       - Base: importance weight from OccupationSkill
       - Bonus: +0.1 per prerequisite skill
       - Bonus: +0.1 per dependent skill
     - Calculate priority = gap * criticality
     - Create/update SkillGap record

3. Return list of skill gaps sorted by priority

This helps users focus on high-impact skills first.
```

---

## Testing & Debugging Prompts

### Test IRT Probability Calculation

```
Help me test the IRT probability function:

1. Create test cases:
   - theta=0, a=1, b=0, c=0.25 → P should be ~0.625
   - theta=-2, a=1.5, b=0, c=0.25 → P should be low
   - theta=2, a=1.5, b=0, c=0.25 → P should be high

2. Verify information function makes sense:
   - Information should be maximum when theta ≈ b
   - Higher discrimination a → higher information
   - Plot information curve for b=-1, 0, 1

Show me how to write unit tests for these functions.
```

---

### Test MLE Estimation

```
Help me validate MLE theta estimation:

1. Generate synthetic data:
   - True theta = 0.5
   - 10 questions with varying difficulties
   - Simulate responses using true theta
   
2. Estimate theta from responses
3. Compare estimated theta to true theta
4. Should be close if enough questions

5. Test convergence:
   - Plot SE vs number of questions
   - Should decrease and converge below 0.3

Show me the code to run this validation.
```

---

### Debug Adaptive Selection

```
I'm getting questions that seem too easy/hard. Debug the adaptive selection algorithm:

1. Log information values for all questions at current theta
2. Verify maximum information question is selected
3. Check if question difficulties span the range
4. Ensure answered questions are excluded

Show me debugging print statements to add.
```

---

## Common Issues & Solutions

### Issue: Theta estimation gives extreme values

```
My theta estimates are -10 or +10, which is unrealistic. How do I fix this?

Expected solution:
1. Bound theta search range to (-4, 4)
2. Check answer patterns (all correct/incorrect edge case)
3. Ensure questions have reasonable IRT parameters
4. Add regularization if needed

Show corrected estimate_theta method.
```

---

### Issue: SE not converging

```
Standard error stays high even after many questions. What's wrong?

Possible causes:
1. Questions have low discrimination (a < 0.5)
2. Questions all have same difficulty
3. Information calculation error

How do I diagnose and fix this?
```

---

## Advanced Prompts

### Multi-Skill Assessment

```
Extend the assessment system to handle multiple skills simultaneously:

1. Modify DiagnosticSession to support multiple skills
2. Maintain separate theta for each skill
3. Select questions that provide information for multiple skills where possible
4. Update all thetas after each answer

Show implementation approach.
```

---

### Automated Question Calibration

```
Implement automatic IRT parameter calibration:

1. Collect response data for new questions
2. Estimate difficulty_b from percentage correct
3. Estimate discrimination_a  from correlation with total score
4. Update Question model with estimated parameters

Use classical test theory initial estimates, then refine with IRT.
```

---

## Tips for Using These Prompts

1. **Copy exact prompt** - Don't modify unless needed
2. **Provide context** - Mention related models/functions
3. **Ask for tests** - Always request test cases
4. **Request explanations** - Understand the math
5. **Iterate** - Refine based on results

---

**Remember**: IRT is mathematically complex. Use AI to generate code, but make sure you understand the underlying principles!
