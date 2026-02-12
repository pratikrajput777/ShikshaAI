# Day 03: Detailed Tasks Breakdown

## Developer Assignment

- **Developer A (DA)**: Focus on Gemini API integration, study plan models, and Batch API
- **Developer B (DB)**: Focus on content generation, CFU quizzes, WebSocket, and remediation

---

## Phase 1: Gemini API Setup (1.5 hours)

### Task 1.1: Install and Configure Gemini API
**Assigned to**: DA
**Duration**: 30 minutes

#### Subtasks:
- [ ] 1.1.1 Install Google Generative AI SDK
  ```bash
  pip install google-generativeai==0.3.2
  # Add to requirements.txt
  echo "google-generativeai==0.3.2" >> requirements.txt
  ```

- [ ] 1.1.2 Add Gemini API key to `.env`
  ```env
  # Gemini API Configuration
  GEMINI_API_KEY=your-gemini-api-key-here
  
  # Model selections
  GEMINI_MODEL_LITE=gemini-2.0-flash-lite
  GEMINI_MODEL_FLASH=gemini-1.5-flash
  GEMINI_MODEL_PRO=gemini-1.5-pro
  ```

- [ ] 1.1.3 Update Django settings
  ```python
  # In settings.py
  GEMINI_API_KEY = env('GEMINI_API_KEY')
  GEMINI_MODEL_LITE = env('GEMINI_MODEL_LITE', default='gemini-2.0-flash-lite')
  GEMINI_MODEL_FLASH = env('GEMINI_MODEL_FLASH', default='gemini-1.5-flash')
  GEMINI_MODEL_PRO = env('GEMINI_MODEL_PRO', default='gemini-1.5-pro')
  
  # IRT Settings (from Day 02)
  IRT_CONVERGENCE_THRESHOLD = 0.3
  IRT_MAX_QUESTIONS = 30
  ```

- [ ] 1.1.4 Test API connection
  ```python
  # In Django shell
  import google.generativeai as genai
  from django.conf import settings
  
  genai.configure(api_key=settings.GEMINI_API_KEY)
  model = genai.GenerativeModel('gemini-1.5-flash')
  response = model.generate_content("Say hello!")
  print(response.text)
  ```

**Completion Criteria**: Gemini API configured and responding

---

### Task 1.2: Create Gemini Service Class
**Assigned to**: DA
**Duration**: 1 hour

#### Subtasks:
- [ ] 1.2.1 Create `core/gemini_service.py`
  ```python
  import google.generativeai as genai
  from django.conf import settings
  import json
  import time
  from typing import Dict, List, Optional
  
  class GeminiService:
      """Service for interacting with Google Gemini API."""
      
      def __init__(self):
          genai.configure(api_key=settings.GEMINI_API_KEY)
      
      def generate_with_lite(self, prompt: str, **kwargs) -> str:
          """Generate content using Flash-Lite (cheapest, fastest)."""
          model = genai.GenerativeModel(settings.GEMINI_MODEL_LITE)
          response = model.generate_content(prompt, **kwargs)
          return response.text
      
      def generate_with_flash(self, prompt: str, **kwargs) -> str:
          """Generate content using Flash (balanced)."""
          model = genai.GenerativeModel(settings.GEMINI_MODEL_FLASH)
          response = model.generate_content(prompt, **kwargs)
          return response.text
      
      def generate_with_pro(self, prompt: str, **kwargs) -> str:
          """Generate content using Pro (most capable)."""
          model = genai.GenerativeModel(settings.GEMINI_MODEL_PRO)
          response = model.generate_content(prompt, **kwargs)
          return response.text
  ```

- [ ] 1.2.2 Add retry logic with exponential backoff
  ```python
  def generate_with_retry(self, prompt: str, model_type='flash', 
                         max_retries=3, **kwargs) -> str:
      """Generate with automatic retry on failure."""
      for attempt in range(max_retries):
          try:
              if model_type == 'lite':
                  return self.generate_with_lite(prompt, **kwargs)
              elif model_type == 'flash':
                  return self.generate_with_flash(prompt, **kwargs)
              elif model_type == 'pro':
                  return self.generate_with_pro(prompt, **kwargs)
          except Exception as e:
              if attempt == max_retries - 1:
                  raise
              wait_time = 2 ** attempt  # Exponential backoff
              time.sleep(wait_time)
      
      raise Exception("Failed after max retries")
  ```

- [ ] 1.2.3 Add JSON parsing helper
  ```python
  def parse_json_response(self, response_text: str) -> Dict:
      """Parse JSON from Gemini response, handling code blocks."""
      # Remove markdown code blocks if present
      text = response_text.strip()
      if text.startswith('```json'):
          text = text[7:]  # Remove ```json
      if text.startswith('```'):
          text = text[3:]  # Remove ```
      if text.endswith('```'):
          text = text[:-3]  # Remove closing ```
      
      text = text.strip()
      
      try:
          return json.loads(text)
      except json.JSONDecodeError as e:
          # Try to extract JSON from text
          import re
          json_match = re.search(r'\{.*\}', text, re.DOTALL)
          if json_match:
              return json.loads(json_match.group())
          raise ValueError(f"Could not parse JSON: {e}")
  ```

**Completion Criteria**: GeminiService class with all 3 models and helpers

---

## Phase 2: Study Plan Models (1 hour)

### Task 2.1: Create Learning Models
**Assigned to**: DB
**Duration**: 1 hour

#### Subtasks:
- [ ] 2.1.1 Create StudyPlan model in `learning/models.py`
  ```python
  from django.db import models
  from django.conf import settings
  from django.contrib.postgres.fields import JSONField
  
  class StudyPlan(models.Model):
      STATUS_CHOICES = [
          ('pending', 'Pending Generation'),
          ('generating', 'Generating'),
          ('ready', 'Ready'),
          ('in_progress', 'In Progress'),
          ('completed', 'Completed'),
      ]
      
      user = models.ForeignKey(
          settings.AUTH_USER_MODEL,
          on_delete=models.CASCADE,
          related_name='study_plans'
      )
      target_occupation = models.ForeignKey(
          'skills.Occupation',
          on_delete=models.CASCADE,
          related_name='study_plans'
      )
      
      # Generation metadata
      status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
      skill_gaps_snapshot = models.JSONField(default=dict)
      
      # Progress tracking
      total_modules = models.IntegerField(default=0)
      completed_modules = models.IntegerField(default=0)
      progress_percentage = models.FloatField(default=0.0)
      
      # AI generation tracking
      generated_by_model = models.CharField(max_length=50, default='gemini-1.5-pro')
      generation_prompt = models.TextField(blank=True)
      batch_job_id = models.CharField(max_length=100, blank=True)
      
      # Timestamps
      created_at = models.DateTimeField(auto_now_add=True)
      started_at = models.DateTimeField(null=True, blank=True)
      completed_at = models.DateTimeField(null=True, blank=True)
      updated_at = models.DateTimeField(auto_now=True)
      
      class Meta:
          db_table = 'study_plans'
          indexes = [
              models.Index(fields=['user', 'status']),
              models.Index(fields=['status']),
          ]
      
      def __str__(self):
          return f"{self.user.username} - {self.target_occupation.preferred_label}"
      
      def update_progress(self):
          """Recalculate completion percentage."""
          if self.total_modules == 0:
              self.progress_percentage = 0
          else:
              self.progress_percentage = (self.completed_modules / self.total_modules) * 100
          self.save()
  ```

- [ ] 2.1.2 Create LearningModule model (Macro tier)
  ```python
  class LearningModule(models.Model):
      study_plan = models.ForeignKey(
          StudyPlan,
          on_delete=models.CASCADE,
          related_name='learning_modules'
      )
      
      title = models.CharField(max_length=255)
      description = models.TextField()
      order = models.IntegerField(help_text='Order in study plan')
      estimated_hours = models.FloatField(default=0.0)
      
      # Associated skill
      primary_skill = models.ForeignKey(
          'skills.Skill',
          on_delete=models.SET_NULL,
          null=True,
          related_name='learning_modules'
      )
      
      created_at = models.DateTimeField(auto_now_add=True)
      
      class Meta:
          db_table = 'learning_modules'
          ordering = ['order']
          unique_together = ['study_plan', 'order']
      
      def __str__(self):
          return f"{self.study_plan.user.username} - Module {self.order}: {self.title}"
  ```

- [ ] 2.1.3 Create Lesson model (Meso tier)
  ```python
  class Lesson(models.Model):
      STATUS_CHOICES = [
          ('locked', 'Locked'),
          ('available', 'Available'),
          ('in_progress', 'In Progress'),
          ('completed', 'Completed'),
      ]
      
      module = models.ForeignKey(
          LearningModule,
          on_delete=models.CASCADE,
          related_name='lessons'
      )
      
      title = models.CharField(max_length=255)
      content = models.TextField(help_text='AI-generated lesson content')
      learning_objectives = models.JSONField(default=list)
      
      order = models.IntegerField()
      estimated_minutes = models.IntegerField(default=30)
      
      status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='locked')
      
      # AI generation metadata
      generated_by_model = models.CharField(max_length=50, default='gemini-2.0-flash-lite')
      generation_prompt = models.TextField(blank=True)
      
      # Timestamps
      created_at = models.DateTimeField(auto_now_add=True)
      started_at = models.DateTimeField(null=True, blank=True)
      completed_at = models.DateTimeField(null=True, blank=True)
      updated_at = models.DateTimeField(auto_now=True)
      
      class Meta:
          db_table = 'lessons'
          ordering = ['order']
          unique_together = ['module', 'order']
          indexes = [
              models.Index(fields=['module', 'status']),
          ]
      
      def __str__(self):
          return f"{self.module.title} - Lesson {self.order}: {self.title}"
  ```

- [ ] 2.1.4 Create CFUQuiz and CFUAttempt models
  ```python
  class CFUQuiz(models.Model):
      """Check for Understanding quiz."""
      lesson = models.ForeignKey(
          Lesson,
          on_delete=models.CASCADE,
          related_name='cfu_quizzes'
      )
      
      questions = models.JSONField(help_text='List of quiz questions with options')
      passing_score = models.IntegerField(default=70)
      
      generated_at = models.DateTimeField(auto_now_add=True)
      generation_prompt = models.TextField(blank=True)
      
      class Meta:
          db_table = 'cfu_quizzes'
          verbose_name = 'CFU Quiz'
          verbose_name_plural = 'CFU Quizzes'
      
      def __str__(self):
          return f"CFU for {self.lesson.title}"
  
  class CFUAttempt(models.Model):
      """User attempt at CFU quiz."""
      quiz = models.ForeignKey(
          CFUQuiz,
          on_delete=models.CASCADE,
          related_name='attempts'
      )
      user = models.ForeignKey(
          settings.AUTH_USER_MODEL,
          on_delete=models.CASCADE,
          related_name='cfu_attempts'
      )
      
      answers = models.JSONField(help_text='User answers')
      score = models.IntegerField()
      passed = models.BooleanField()
      
      time_taken_seconds = models.IntegerField(null=True, blank=True)
      remediation_generated = models.BooleanField(default=False)
      
      attempt_number = models.IntegerField(default=1)
      attempted_at = models.DateTimeField(auto_now_add=True)
      
      class Meta:
          db_table = 'cfu_attempts'
          indexes = [
              models.Index(fields=['user', 'quiz']),
              models.Index(fields=['passed']),
          ]
          ordering = ['-attempted_at']
  ```

- [ ] 2.1.5 Create Remediation model
  ```python
  class Remediation(models.Model):
      """Scaffolded remediation for failed CFU."""
      cfu_attempt = models.ForeignKey(
          CFUAttempt,
          on_delete=models.CASCADE,
          related_name='remediations'
      )
      
      misconception = models.CharField(max_length=500)
      explanation = models.TextField()
      simplified_content = models.TextField()
      additional_examples = models.JSONField(default=list)
      
      helpful = models.BooleanField(null=True, blank=True)
      created_at = models.DateTimeField(auto_now_add=True)
      
      class Meta:
          db_table = 'remediations'
  ```

**Completion Criteria**: All learning models created with proper relationships

---

## Phase 3: Study Plan Generation Service (2.5 hours)

### Task 3.1: Macro Tier - Overall Study Plan
**Assigned to**: DA
**Duration**: 1 hour

#### Subtasks:
- [ ] 3.1.1 Create `learning/services.py`
  ```python
  from core.gemini_service import GeminiService
  from .models import StudyPlan, LearningModule
  from assessment.models import SkillGap
  import json
  
  class StudyPlanService:
      """Service for generating AI-powered study plans."""
      
      def __init__(self):
          self.gemini = GeminiService()
      
      @staticmethod
      def create_macro_plan_prompt(user, target_occupation, skill_gaps):
          """Create prompt for overall study plan (Macro tier)."""
          gaps_summary = "\n".join([
              f"- {gap.skill.preferred_label}: "
              f"Gap {gap.gap_score:.2f} (Priority: {gap.priority_score:.2f})"
              for gap in skill_gaps[:10]  # Top 10 gaps
          ])
          
          prompt = f"""You are an expert learning path designer. Create a comprehensive study plan.

  **Target Role**: {target_occupation.preferred_label}
  **User Background**: {user.experience_years} years experience, {user.skill_level} level

  **Skill Gaps** (ordered by priority):
  {gaps_summary}

  **Task**: Design a structured learning plan with 5-8 learning modules.

  **Output Format** (JSON):
  {{
    "modules": [
      {{
        "title": "Module title",
        "description": "What student will learn",
        "primary_skill": "Skill name",
        "estimated_hours": 20,
        "order": 1
      }}
    ]
  }}

  **Requirements**:
  1. Address highest priority gaps first
  2. Build prerequisite skills before advanced topics
  3. Realistic time estimates (10-40 hours per module)
  4. Clear progression from fundamentals to advanced
  5. Practical, job-focused content

  Provide only valid JSON, no additional text.
  """
          return prompt
      
      def generate_macro_plan(self, user, target_occupation):
          """Generate overall study plan structure using Gemini Pro."""
          # Get skill gaps (from Day 02)
          from assessment.services import AssessmentService
          skill_gaps = AssessmentService.calculate_skill_gaps(user, target_occupation)
          
          # Create study plan record
          study_plan = StudyPlan.objects.create(
              user=user,
              target_occupation=target_occupation,
              status='generating',
              skill_gaps_snapshot={
                  'gaps': [
                      {
                          'skill': gap.skill.preferred_label,
                          'gap_score': gap.gap_score,
                          'priority': gap.priority_score
                      }
                      for gap in skill_gaps[:10]
                  ]
              }
          )
          
          # Generate with Gemini Pro (most capable)
          prompt = self.create_macro_plan_prompt(user, target_occupation, skill_gaps)
          study_plan.generation_prompt = prompt
          study_plan.save()
          
          try:
              response = self.gemini.generate_with_retry(prompt, model_type='pro')
              plan_data = self.gemini.parse_json_response(response)
              
              # Create learning modules
              from skills.models import Skill
              for module_data in plan_data['modules']:
                  # Find matching skill
                  skill = None
                  try:
                      skill = Skill.objects.filter(
                          preferred_label__icontains=module_data['primary_skill']
                      ).first()
                  except:
                      pass
                  
                  LearningModule.objects.create(
                      study_plan=study_plan,
                      title=module_data['title'],
                      description=module_data['description'],
                      primary_skill=skill,
                      estimated_hours=module_data['estimated_hours'],
                      order=module_data['order']
                  )
              
              study_plan.total_modules = len(plan_data['modules'])
              study_plan.status = 'ready'
              study_plan.save()
              
              return study_plan
              
          except Exception as e:
              study_plan.status = 'pending'
              study_plan.save()
              raise
  ```

**Completion Criteria**: Macro tier study plan generation working

---

### Task 3.2: Meso Tier - Detailed Lessons
**Assigned to**: DA
**Duration**: 1 hour 30 minutes

#### Subtasks:
- [ ] 3.2.1 Add lesson generation method
  ```python
  # In StudyPlanService class
  
  @staticmethod
  def create_lesson_prompt(module):
      """Create prompt for detailed lesson generation (Meso tier)."""
      prompt = f"""Generate a detailed lesson for a learning module.

  **Module**: {module.title}
  **Description**: {module.description}
  **Target Skill**: {module.primary_skill.preferred_label if module.primary_skill else 'General'}

  **Task**: Create 8-12 progressive lessons for this module.

  **Output Format** (JSON):
  {{
    "lessons": [
      {{
        "title": "Lesson title",
        "content": "Detailed lesson content (500-800 words)",
        "learning_objectives": ["Objective 1", "Objective 2", "Objective 3"],
        "estimated_minutes": 45,
        "order": 1
      }}
    ]
  }}

  **Requirements**:
  1. Progressive difficulty (easy to advanced)
  2. Practical examples and analogies
  3. Clear explanations for beginners
  4. Code examples where applicable
  5. Real-world applications
  6. 3-5 specific learning objectives per lesson

  Provide only valid JSON.
  """
      return prompt
  
  def generate_lessons_for_module(self, module):
      """Generate detailed lessons using Gemini Flash-Lite (cheaper)."""
      prompt = self.create_lesson_prompt(module)
      
      try:
          # Use Flash-Lite for cost savings (simpler task)
          response = self.gemini.generate_with_retry(prompt, model_type='lite')
          lessons_data = self.gemini.parse_json_response(response)
          
          # Create lesson records
          from .models import Lesson
          created_lessons = []
          
          for lesson_data in lessons_data['lessons']:
              lesson = Lesson.objects.create(
                  module=module,
                  title=lesson_data['title'],
                  content=lesson_data['content'],
                  learning_objectives=lesson_data['learning_objectives'],
                  estimated_minutes=lesson_data['estimated_minutes'],
                  order=lesson_data['order'],
                  status='available',  # First lesson available
                  generated_by_model='gemini-2.0-flash-lite',
                  generation_prompt=prompt
              )
              created_lessons.append(lesson)
              
              # Lock all but first lesson
              if lesson.order > 1:
                  lesson.status = 'locked'
                  lesson.save()
          
          return created_lessons
          
      except Exception as e:
          raise Exception(f"Lesson generation failed: {str(e)}")
  
  def generate_all_lessons(self, study_plan):
      """Generate lessons for all modules in study plan."""
      modules = study_plan.learning_modules.all()
      
      for module in modules:
          self.generate_lessons_for_module(module)
      
      return study_plan
  ```

**Completion Criteria**: Lesson generation for modules working

---

## Phase 4: CFU Quiz & Remediation (2 hours)

### Task 4.1: CFU Quiz Generation
**Assigned to**: DB
**Duration**: 1 hour

#### Subtasks:
- [ ] 4.1.1 Add CFU quiz generation to service
  ```python
  # In StudyPlanService class
  
  @staticmethod
  def create_cfu_quiz_prompt(lesson):
      """Create prompt for CFU quiz generation."""
      prompt = f"""Generate a Check for Understanding (CFU) quiz for a lesson.

  **Lesson**: {lesson.title}
  **Content Summary**: {lesson.content[:500]}...
  **Learning Objectives**:
  {chr(10).join(f"- {obj}" for obj in lesson.learning_objectives)}

  **Task**: Create a 5-question multiple-choice quiz to check understanding.

  **Output Format** (JSON):
  {{
    "questions": [
      {{
        "question": "Question text?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": 0,
        "explanation": "Why this is correct",
        "difficulty": "easy|medium|hard"
      }}
    ]
  }}

  **Requirements**:
  1. 5 questions total
  2. Mix of difficulty (2 easy, 2 medium, 1 hard)
  3. Test understanding, not memorization
  4. Clear, unambiguous questions
  5. Plausible distractors
  6. Comprehensive explanations

  Provide only valid JSON.
  """
      return prompt
  
  def generate_cfu_quiz(self, lesson):
      """Generate CFU quiz for lesson using Gemini Flash-Lite."""
      from .models import CFUQuiz
      
      prompt = self.create_cfu_quiz_prompt(lesson)
      
      try:
          response = self.gemini.generate_with_retry(prompt, model_type='lite')
          quiz_data = self.gemini.parse_json_response(response)
          
          cfu_quiz = CFUQuiz.objects.create(
              lesson=lesson,
              questions=quiz_data['questions'],
              passing_score=70,
              generation_prompt=prompt
          )
          
          return cfu_quiz
          
      except Exception as e:
          raise Exception(f"CFU quiz generation failed: {str(e)}")
  ```

**Completion Criteria**: CFU quiz generation working with 5 questions

---

### Task 4.2: Remediation Content Generation
**Assigned to**: DB
**Duration**: 1 hour

#### Subtasks:
- [ ] 4.2.1 Add remediation generation
  ```python
  # In StudyPlanService class
  
  @staticmethod
  def create_remediation_prompt(cfu_attempt, lesson):
      """Create prompt for personalized remediation."""
      # Analyze wrong answers
      wrong_questions = []
      for i, answer in enumerate(cfu_attempt.answers):
          quiz_question = cfu_attempt.quiz.questions[i]
          if answer != quiz_question['correct_answer']:
              wrong_questions.append({
                  'question': quiz_question['question'],
                  'user_answer': quiz_question['options'][answer],
                  'correct_answer': quiz_question['options'][quiz_question['correct_answer']],
                  'explanation': quiz_question['explanation']
              })
      
      prompt = f"""Create personalized remediation content for a student who failed a CFU quiz.

  **Lesson**: {lesson.title}
  **Student Score**: {cfu_attempt.score}% (Failed - needed {cfu_attempt.quiz.passing_score}%)

  **Questions Answered Incorrectly**:
  {json.dumps(wrong_questions, indent=2)}

  **Task**: Create scaffolded remediation content.

  **Output Format** (JSON):
  {{
    "misconception": "The main misunderstanding",
    "explanation": "Clear explanation addressing the misconception",
    "simplified_content": "Simplified re-explanation of concept (300-400 words)",
    "additional_examples": [
      "Concrete example 1",
      "Concrete example 2",
      "Practice problem"
    ]
  }}

  **Requirements**:
  1. Identify core misconception
  2. Use analogies and simple language
  3. Break down complex concepts
  4. Provide concrete examples
  5. Encouraging tone

  Provide only valid JSON.
  """
      return prompt
  
  def generate_remediation(self, cfu_attempt):
      """Generate personalized remediation content."""
      from .models import Remediation
      
      lesson = cfu_attempt.quiz.lesson
      prompt = self.create_remediation_prompt(cfu_attempt, lesson)
      
      try:
          response = self.gemini.generate_with_retry(prompt, model_type='flash')
          remediation_data = self.gemini.parse_json_response(response)
          
          remediation = Remediation.objects.create(
              cfu_attempt=cfu_attempt,
              misconception=remediation_data['misconception'],
              explanation=remediation_data['explanation'],
              simplified_content=remediation_data['simplified_content'],
              additional_examples=remediation_data['additional_examples']
          )
          
          cfu_attempt.remediation_generated = True
          cfu_attempt.save()
          
          return remediation
          
      except Exception as e:
          raise Exception(f"Remediation generation failed: {str(e)}")
  ```

**Completion Criteria**: Automatic remediation for failed CFU quizzes

---

## Phase 5: Batch API & WebSocket (1 hour)

### Task 5.1: Batch API Integration
**Assigned to**: DA
**Duration**: 30 minutes

#### Subtasks:
- [ ] 5.1.1 Add batch generation method
  ```python
  # In StudyPlanService class
  
  def generate_study_plan_batch(self, user, target_occupation):
      """Queue study plan generation as batch job for cost savings."""
      # Create study plan in 'pending' status
      study_plan = StudyPlan.objects.create(
          user=user,
          target_occupation=target_occupation,
          status='pending'
      )
      
      # Queue Celery task for batch processing
      from .tasks import generate_study_plan_batch_task
      task = generate_study_plan_batch_task.delay(study_plan.id)
      
      study_plan.batch_job_id = task.id
      study_plan.save()
      
      return study_plan
  ```

- [ ] 5.1.2 Create batch task in `learning/tasks.py`
  ```python
  from celery import shared_task
  from .models import StudyPlan
  from .services import StudyPlanService
  
  @shared_task(bind=True, max_retries=3)
  def generate_study_plan_batch_task(self, study_plan_id):
      """Background task for study plan generation."""
      try:
          study_plan = StudyPlan.objects.get(id=study_plan_id)
          service = StudyPlanService()
          
          # Macro generation (Gemini Pro)
          service.generate_macro_plan(study_plan.user, study_plan.target_occupation)
          
          # Meso generation (Gemini Flash-Lite) - parallel
          service.generate_all_lessons(study_plan)
          
          return f"Study plan {study_plan_id} generated successfully"
          
      except Exception as exc:
          self.retry(exc=exc, countdown=60)
  ```

**Completion Criteria**: Study plans can be generated as batch jobs

---

### Task 5.2: WebSocket Progress Notifications
**Assigned to**: DB
**Duration**: 30 minutes

#### Subtasks:
- [ ] 5.2.1 Create WebSocket consumer in `learning/consumers.py`
  ```python
  from channels.generic.websocket import AsyncJsonWebsocketConsumer
  from channels.db import database_sync_to_async
  
  class StudyPlanProgressConsumer(AsyncJsonWebsocketConsumer):
      """WebSocket consumer for real-time study plan progress."""
      
      async def connect(self):
          self.user = self.scope['user']
          self.room_group_name = f'study_plan_{self.user.id}'
          
          # Join room group
          await self.channel_layer.group_add(
              self.room_group_name,
              self.channel_name
          )
          
          await self.accept()
      
      async def disconnect(self, close_code):
          # Leave room group
          await self.channel_layer.group_discard(
              self.room_group_name,
              self.channel_name
          )
      
      async def study_plan_update(self, event):
          """Send study plan update to WebSocket."""
          await self.send_json({
              'type': 'study_plan_update',
              'status': event['status'],
              'progress': event['progress'],
              'message': event['message']
          })
  ```

- [ ] 5.2.2 Add WebSocket routing in `learning/routing.py`
  ```python
  from django.urls import re_path
  from . import consumers
  
  websocket_urlpatterns = [
      re_path(r'ws/study-plan/progress/$', consumers.StudyPlanProgressConsumer.as_asgi()),
  ]
  ```

- [ ] 5.2.3 Send progress updates from service
  ```python
  # In tasks.py, update the batch task:
  
  from channels.layers import get_channel_layer
  from asgiref.sync import async_to_sync
  
  @shared_task(bind=True)
  def generate_study_plan_batch_task(self, study_plan_id):
      channel_layer = get_channel_layer()
      
      def send_update(status, progress, message):
          async_to_sync(channel_layer.group_send)(
              f'study_plan_{study_plan.user.id}',
              {
                  'type': 'study_plan_update',
                  'status': status,
                  'progress': progress,
                  'message': message
              }
          )
      
      try:
          study_plan = StudyPlan.objects.get(id=study_plan_id)
          
          send_update('generating', 10, 'Analyzing skill gaps...')
          service.generate_macro_plan(...)
          
          send_update('generating', 50, 'Creating learning modules...')
          service.generate_all_lessons(...)
          
          send_update('ready', 100, 'Study plan ready!')
          
      except Exception as exc:
          send_update('error', 0, f'Generation failed: {str(exc)}')
          raise
  ```

**Completion Criteria**: Real-time WebSocket updates during generation

---

## Summary Checklist

### Must Complete Today
- [x] Gemini API configured and tested
- [x] GeminiService with 3 model tiers
- [x] Study plan and learning models created
- [x] Macro tier generation (Gemini Pro)
- [x] Meso tier lesson generation (Flash-Lite)
- [x] CFU quiz generation
- [x] Automatic remediation
- [x] Batch API task queuing
- [x] WebSocket progress updates
- [x] All migrations applied

---

## Time Tracking

| Phase | Estimated | Actual | Notes |
|-------|-----------|--------|-------|
| Phase 1: Gemini Setup | 1.5h | | |
| Phase 2: Models | 1h | | |
| Phase 3: Generation | 2.5h | | |
| Phase 4: CFU & Remediation | 2h | | |
| Phase 5: Batch & WebSocket | 1h | | |
| **Total** | **8h** | | |

---

**Ready to generate AI-powered personalized learning paths!** 🎓
