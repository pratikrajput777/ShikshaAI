# Day 02: IRT Assessment Engine & Skill Gap Analysis 📊

## 📚 What You Will Achieve Today

By the end of Day 2, you will have:

1. ✅ Complete IRT (Item Response Theory) assessment engine
2. ✅ Adaptive question selection algorithm
3. ✅ Question bank with IRT parameters (a, b, c)
4. ✅ Maximum Likelihood Estimation for theta calculation
5. ✅ Convergence detection mechanism (SE < 0.3)
6. ✅ Skill gap analysis system with priority scoring
7. ✅ Answer logging and analytics
8. ✅ API endpoints for diagnostic assessments
9. ✅ Real-time progress tracking

## 🎯 Learning Objectives

### Educational Assessment Theory
- **Item Response Theory (IRT)**: Understand how IRT models learner ability
- **3PL Model**: Learn the 3-Parameter Logistic Model P(θ) = c + (1-c)/(1+e^(-a(θ-b)))
- **Theta Estimation**: Master Maximum Likelihood Estimation (MLE)
- **Adaptive Testing**: Implement intelligent question selection
- **Convergence**: Detect when assessment can terminate

### Statistical Computing
- **scipy Library**: Statistical functions and optimization
- **numpy Arrays**: Numerical computations
- **Probability Calculations**: Work with probabilities and likelihoods
- **Optimization**: Find theta that maximizes likelihood

### Algorithm Design
- **Adaptive Algorithms**: Select next question based on current estimate
- **Convergence Detection**: Know when to stop testing
- **Priority Scoring**: Rank skill gaps by importance

## 🛠️ Technology Stack (Day 2)

| Technology | Version | Purpose |
|------------|---------|---------|
| scipy | 1.11.4 | Statistical calculations, MLE |
| numpy | 1.26.0+ | Numerical operations |
| Django ORM | 4.2.7 | Complex queries, aggregations |
| PostgreSQL | 15+ | Analytics queries |
| Celery | 5.3.4 | Async theta calculations |

## 📊 Database Schema (Day 2)

### New Tables to Create
1. **diagnostic_sessions** - Assessment session tracking
2. **question_bank** - Questions with IRT parameters
3. **answer_logs** - Every answer recorded
4. **skill_gaps** - Computed gaps with priority scores

### Key Relationships
```
User 1→M DiagnosticSession 1→M AnswerLog M→1 QuestionBank
User 1→M SkillGap M→1 Skill
User 1→M SkillGap M→1 Occupation
```

## 📋 Prerequisites

- Day 01 completed and tested (100%)
- Understanding of basic statistics
- Familiarity with probability concepts
- scipy and numpy installed
- Curiosity about educational assessment!

## ⏱️ Estimated Time

- **IRT Models & Database**: 2 hours
- **IRT Calculation Engine**: 3 hours
- **Adaptive Question Selection**: 2 hours
- **Skill Gap Analysis**: 1 hour
- **Total**: ~8 hours (1 working day for 2 developers)

## 🎓 Key Concepts to Master

### 1. Item Response Theory (IRT)

**What is IRT?**
IRT is a modern testing theory that models the probability of a correct response based on:
- **Learner ability (θ - theta)**: The person's skill level
- **Item difficulty (b)**: How hard the question is
- **Item discrimination (a)**: How well the question differentiates ability levels
- **Guessing parameter (c)**: Probability of guessing correctly

**Why IRT?**
- More accurate than classical test theory
- Adaptive testing possible
- Same ability = same score regardless of questions
- Can detect when to stop testing

### 2. The 3-Parameter Logistic (3PL) Model

**Formula:**
```
P(θ) = c + (1 - c) / (1 + e^(-a(θ - b)))
```

**Where:**
- `P(θ)` = Probability person with ability θ answers correctly
- `θ` (theta) = Person's ability level (-∞ to +∞, typically -3 to +3)
- `a` = Discrimination parameter (higher = better differentiates)
- `b` = Difficulty parameter (on same scale as θ)
- `c` = Guessing parameter (0 to 1, typically 0.25 for 4 choices)

**Example:**
```python
# Question: difficulty b=0.5, discrimination a=1.2, guessing c=0.25
# Person: ability θ=0.8

P(0.8) = 0.25 + (1 - 0.25) / (1 + e^(-1.2 * (0.8 - 0.5)))
       = 0.25 + 0.75 / (1 + e^(-0.36))
       = 0.25 + 0.75 / 1.43
       = 0.25 + 0.52
       = 0.77  (77% chance of correct answer)
```

### 3. Maximum Likelihood Estimation (MLE)

**Purpose:** Find the θ value that best explains observed answers

**Likelihood Function:**
```
L(θ) = ∏ P(θ)^correct × (1-P(θ))^incorrect
```

**Process:**
1. Start with initial θ estimate (usually 0)
2. Calculate likelihood for current θ
3. Adjust θ to maximize likelihood
4. Repeat until convergence
5. Take log-likelihood for numerical stability

**Implementation:**
```python
from scipy.optimize import minimize_scalar

def log_likelihood(theta, answers, questions):
    ll = 0
    for answer, question in zip(answers, questions):
        p = irt_probability(theta, question.a, question.b, question.c)
        if answer.is_correct:
            ll += np.log(p)
        else:
            ll += np.log(1 - p)
    return -ll  # Negative for minimization

# Find theta that maximizes likelihood
result = minimize_scalar(log_likelihood, bounds=(-4, 4))
theta_hat = result.x
```

### 4. Adaptive Question Selection

**Strategy:** Select the question that provides most information

**Information Function:**
```
I(θ) = a² × P(θ) × (1 - P(θ)) / (1 - c)²
```

**Selection Algorithm:**
1. Calculate current θ estimate
2. For each unused question, calculate I(θ)
3. Select question with maximum I(θ)
4. Present to user
5. Update θ based on response

**Why this works:**
- Questions near current ability level provide most info
- Too easy/hard questions don't help much
- Maximizes efficiency (fewer questions needed)

### 5. Convergence Detection

**When to Stop:**
- Standard Error (SE) < 0.3 threshold
- OR maximum questions reached (e.g., 30)
- OR time limit exceeded

**Standard Error Calculation:**
```
SE(θ) = 1 / √(Σ I(θ))
```

Where I(θ) is information from each question answered

**Example:**
```
Questions answered: 10
Total information: 12.5
SE = 1 / √12.5 = 0.28

0.28 < 0.3 → CONVERGED! Can stop testing.
```

### 6. Skill Gap Analysis

**Formula:**
```
Gap Score = (Required θ - Current θ) × Criticality Coefficient
```

**Criticality Coefficient depends on:**
- Importance weight (from OccupationSkill)
- Number of prerequisites
- How many other skills depend on this

**Priority Ranking:**
1. Calculate gap for each skill
2. Apply criticality weights
3. Sort by priority score
4. Top gaps = focus areas for learning

## 📖 Resources for Day 2

### IRT Theory
- [IRT from SSI](http://www.ssicentral.com/irt/index.html)
- [Understanding IRT](https://www.rasch.org/rmt/rmt162f.htm)
- [CAT (Computerized Adaptive Testing)](https://en.wikipedia.org/wiki/Computerized_adaptive_testing)

### Python Libraries
- [scipy.optimize](https://docs.scipy.org/doc/scipy/reference/optimize.html)
- [numpy Documentation](https://numpy.org/doc/)

### Academic Papers
- "Item Response Theory for Psychologists" - Embretson & Reise
- "Computerized Adaptive Testing: A Primer" - Wainer

## 🚀 Success Criteria

By end of day, you should be able to:

- [x] Explain IRT 3PL model
- [x] Calculate probability given θ and item parameters
- [x] Implement MLE theta estimation
- [x] Select next question adaptively
- [x] Detect convergence
- [x] Calculate skill gaps with priorities
- [x] API returns adaptive questions
- [x] System knows when to stop testing

## 🎯 Next Steps (Day 3 Preview)

Tomorrow you will implement:
- Google Gemini API integration
- AI-generated study plans
- Cascaded content generation (Macro → Meso → Micro)
- CFU quiz generation
- Remediation content creation
- Batch API for cost optimization

---

**Remember**: IRT might seem complex initially, but it's just probability and optimization. Take it step by step, and you'll master adaptive testing!
