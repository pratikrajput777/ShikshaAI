# Day 03: AI Agent Prompts

Ready-to-use prompts for AI coding assistants for Gemini integration and learning path generation.

---

## Gemini API Setup

### Prompt 1.1: GeminiService Class with Three Models

```
Create a comprehensive GeminiService class in core/gemini_service.py with:

1. Three generation methods:
   - generate_with_lite(): Use gemini-2.0-flash-lite (cheapest, fastest)
   - generate_with_flash(): Use gemini-1.5-flash (balanced)
   - generate_with_pro(): Use gemini-1.5-pro (most capable)

2. Retry logic with exponential backoff:
   - generate_with_retry(prompt, model_type, max_retries=3)
   - Wait: 2^attempt seconds between retries
   - Handle rate limiting and API errors

3. JSON parsing helper:
   - parse_json_response(response_text)
   - Handle markdown code blocks (```json)
   - Extract JSON even if surrounded by text
   - Robust error handling

Use google-generativeai library, configure from Django settings.
Include docstrings and type hints.
```

---

## Study Plan Models

### Prompt 2.1: Complete Learning Models

```
Create comprehensive learning models in learning/models.py:

1. StudyPlan model:
   - user, target_occupation (ForeignKeys)
   - status: pending, generating, ready, in_progress, completed
   - skill_gaps_snapshot (JSONField) - store gaps at creation
   - total_modules, completed_modules, progress_percentage
   - generated_by_model, generation_prompt, batch_job_id
   - timestamps:started_at, completed_at, created_at, updated_at
   - Method: update_progress() - recalculate completion %

2. LearningModule model (Macro tier):
   - study_plan (ForeignKey)
   - title, description, order
   - estimated_hours
   - primary_skill (ForeignKey to Skill, nullable)
   - created_at
   - Meta: ordering by order, unique_together study_plan+order

3. Lesson model (Meso tier):
   - module (ForeignKey)
   - title, content (TextField for AI-generated content)
   - learning_objectives (JSONField list)
   - order, estimated_minutes
   - status: locked, available, in_progress, completed
   - generated_by_model, generation_prompt
   - timestamps: created_at, started_at, completed_at, updated_at
   - Meta: ordering by order

4. CFUQuiz model:
   - lesson (ForeignKey)
   - questions (JSONField with question/options/correct_answer/explanation)
   - passing_score (default 70)
   - generated_at, generation_prompt

5. CFUAttempt model:
   - quiz,user (ForeignKeys)
   - answers (JSONField), score, passed
   - time_taken_seconds, remediation_generated
   - attempt_number, attempted_at

6. Remediation model:
   - cfu_attempt (ForeignKey)
   - misconception, explanation, simplified_content
   - additional_examples (JSONField list)
   - helpful (Boolean nullable), created_at

Include proper indexes, Meta options, and __str__ methods.
Use PostgreSQL JSONField, not django.contrib.postgres.
```

---

## Study Plan Generation

### Prompt 3.1: Macro Tier Generation (Overall Plan)

```
Create StudyPlanService class in learning/services.py:

Method: generate_macro_plan(user, target_occupation)

1. Get skill gaps from AssessmentService (Day 02)
2. Create StudyPlan record with status='generating'
3. Build prompt for Gemini Pro:
   - Include occupation, user experience, skill level
   - List top 10 skill gaps with priorities
   - Request 5-8 learning modules in JSON format
   - Each module: title, description, primary_skill, estimated_hours, order
   - Requirements: address priority gaps, prerequisites first, realistic estimates

4. Call Gemini Pro API (use generate_with_retry)
5. Parse JSON response
6. Create LearningModule records for each module
7. Match skills by name (handle not found gracefully)
8. Update study_plan: total_modules, status='ready'
9. Handle errors: set status='pending', raise exception

Include comprehensive error handling and logging.
```

---

### Prompt 3.2: Meso Tier Generation (Detailed Lessons)

```
Add to StudyPlanService:

Method: generate_lessons_for_module(module)

1. Build prompt for Gemini Flash-Lite:
   - Module title and description
   - Target skill
   - Request 8-12 progressive lessons in JSON format
   - Each lesson: title, content (500-800 words), learning_objectives (3-5), estimated_minutes, order
   - Requirements: progressive difficulty, practical examples, clear for beginners, real-world applications

2. Call Gemini Flash-Lite (cheaper for simpler task)
3. Parse JSON response
4. Create Lesson records
5. First lesson status='available', rest status='locked'
6. Store generation metadata

Method: generate_all_lessons(study_plan)
- Iterate through all modules
- Generate lessons for each
- Return completed study plan

Use parallel processing if possible (Celery group tasks).
```

---

## CFU & Remediation

### Prompt 4.1: CFU Quiz Generation

```
Add to StudyPlanService:

Method: generate_cfu_quiz(lesson)

1. Build prompt for Gemini Flash-Lite:
   - Lesson title and content summary
   - Learning objectives list
   - Request 5 multiple-choice questions in JSON format
   - Each question: question, options (4), correct_answer (0-3), explanation, difficulty
   - Mix: 2 easy, 2 medium, 1 hard
   - Requirements: test understanding not memorization, plausible distractors, clear questions

2. Call Gemini Flash-Lite API
3. Parse JSON response
4. Create CFUQuiz record with questions JSONField
5. Set passing_score=70

Include validation: ensure exactly 5 questions, all have correct_answer 0-3.
```

---

### Prompt 4.2: Personalized Remediation

```
Add to StudyPlanService:

Method: generate_remediation(cfu_attempt)

1. Analyze failed attempt:
   - Get quiz questions
   - Identify which questions user answered incorrectly
   - Extract user's wrong answers vs correct answers

2. Build prompt for Gemini Flash:
   - Lesson context
   - Student score and passing threshold
   - Wrong questions with user answers and correct answers
   - Request remediation in JSON format:
     - misconception: main misunderstanding
     - explanation: addressing misconception
     - simplified_content: re-explanation (300-400 words)
     - additional_examples: list of 3 concrete examples
   - Requirements: simple language, analogies, encouraging tone

3. Call Gemini Flash API
4. Parse JSON response
5. Create Remediation record
6. Mark cfu_attempt.remediation_generated = True

Handle edge case: all questions wrong vs specific misconceptions.
```

---

## Batch Processing & WebSocket

### Prompt 5.1: Batch API Task

```
Create Celery task in learning/tasks.py:

@shared_task(bind=True, max_retries=3)
def generate_study_plan_batch_task(self, study_plan_id):

1. Get StudyPlan from database
2. Send WebSocket update: "Analyzing skill gaps..." (10% progress)
3. Generate macro plan using StudyPlanService
4. Send WebSocket update: "Creating modules..." (30%)
5. Generate lessons for all modules
6. Send WebSocket update per module (40-90%)
7. Send WebSocket update: "Study plan ready!" (100%)
8. Handle errors: send error update, retry with countdown=60

Use channels.layers.get_channel_layer() and async_to_sync for WebSocket messages.
Send to group: f'study_plan_{user_id}'
```

---

### Prompt 5.2: WebSocket Consumer

```
Create WebSocket consumer in learning/consumers.py:

AsyncJsonWebsocketConsumer for real-time study plan progress:

1. connect():
   - Get user from scope
   - Create room_group_name: f'study_plan_{user.id}'
   - Join channel group
   - Accept connection

2. disconnect():
   - Leave channel group

3. study_plan_update(event):
   - Receive: type, status, progress, message
   - Send JSON to WebSocket with update

Add routing in learning/routing.py:
- Path: ws/study-plan/progress/
- Consumer: StudyPlanProgressConsumer.as_asgi()

Update main routing.py to include learning WebSocket URLs.
```

---

## API Endpoints

###Prompt 6.1: Study Plan API ViewSet

```
Create REST API views in learning/views.py:

StudyPlanViewSet(viewsets.ModelViewSet):

Actions:
1. POST /api/learning/study-plans/
   - Create study plan for target occupation
   - Queue batch generation task
   - Return study plan with status='pending'

2. GET /api/learning/study-plans/<id>/
   - Return study plan with nested modules and lessons
   - Include progress percentage

3. GET /api/learning/study-plans/<id>/modules/
   - List all modules for study plan

4. GET /api/learning/modules/<id>/lessons/
   - List all lessons for module

5. POST /api/learning/lessons/<id>/start/
   - Mark lesson as 'in_progress'
   - Update started_at timestamp

6. POST /api/learning/lessons/<id>/complete/
   - Mark lesson as 'completed'
   - Update completed_at
   - Unlock next lesson
   - Update module/plan progress

7. POST /api/learning/lessons/<id>/cfu/attempt/
   - Submit CFU quiz answers
   - Calculate score
   - Generate remediation if failed (async task)
   - Return result with pass/fail

Use proper serializers with nested representations where appropriate.
Add permissions: IsAuthenticated, user can only access own plans.
```

---

## Testing Prompts

### Test Gemini Integration

```
Help me test Gemini API integration:

1. Test basic connectivity:
   - Generate simple content with each model (lite, flash, pro)
   - Verify responses returned
   - Check model selection logic

2. Test JSON parsing:
   - Response with ```json code blocks
   - Response with plain JSON
   - Response with JSON embedded in text
   - Invalid JSON responses

3. Test retry logic:
   - Simulate API failure
   - Verify exponential backoff
   - Check max retries respected

Show me test cases in django.test.TestCase format.
```

---

### Test Study Plan Generation

```
Create integration test for study plan generation:

1. Create test user with target occupation
2. Create skill gaps (mock data)
3. Generate study plan
4. Verify:
   - StudyPlan created with correct status
   - Modules created (5-8 range)
   - Lessons created for each module (8-12 range)
   - First lesson unlocked, rest locked
   - Progress calculations correct
   - CFU quizzes generated

5. Simulate lesson completion flow:
   - Start lesson
   - Complete lesson
   - Take CFU quiz
   - Fail quiz → verify remediation generated
   - Retake quiz → pass
   - Verify next lesson unlocked

Use mocking for Gemini API calls (don't hit real API in tests).
```

---

## Common Issues

### Issue: JSON Parsing Fails

```
Gemini response doesn't parse as JSON. Help me debug:

1. Log raw response to see format
2. Check for markdown code blocks
3. Extract JSON using regex if needed
4. Add fallback parsing strategies
5. Validate JSON structure before processing

Show robust parsing function that handles all edge cases.
```

---

### Issue: Rate Limiting

```
Getting 429 Rate Limit errors from Gemini. Implement:

1. Exponential backoff (already have?)
2. Check retry-after header
3. Queue management for burst requests
4. Use batch API for non-urgent requests
5. Implement request throttling

Show updated retry logic with rate limit handling.
```

---

### Issue: Context Length Exceeded

```
Getting "context length exceeded" for large prompts. Solutions:

1. Truncate skill gaps list (top N only)
2. Summarize lesson content for CFU/remediation
3. Use prompt caching for repeated context
4. Split into multiple smaller prompts
5. Use streaming for long responses

Show token counting and prompt optimization code.
```

---

## Cost Optimization Prompts

### Implement Context Caching

```
Add context caching to reduce costs by 90%:

1. Identify static prompt parts (system instructions)
2. Use Gemini's cached_content API
3. Cache: system prompts, occupation descriptions, skill lists
4. Only pay for variable part (specific question/lesson)
5. Set TTL appropriately (24 hours)

Show implementation in GeminiService with cache management.
```

---

### Route to Appropriate Model

```
Implement intelligent model routing:

Rules:
- Simple, structured tasks → Flash-Lite (cheapest)
- Real-time, moderate complexity → Flash
- Complex reasoning, planning → Pro

Create ModelRouter class:
- analyze_task_complexity(prompt) → returns model tier
- Consider: prompt length, required reasoning, structure vs creativity
- Route automatically in generate_with_retry

Show decision logic and implementation.
```

---

**Use these prompts to accelerate Day 03 development while maintaining code quality!**
