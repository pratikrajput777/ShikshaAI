# Day 02: Detailed Tasks Breakdown

## Developer Assignment

- **Developer A (DA)**: Focus on IRT models, database, and question bank
- **Developer B (DB)**: Focus on IRT algorithms, theta estimation, and skill gap analysis

---

## Phase 1: Assessment Models & Database (2 hours)

### Task 1.1: DiagnosticSession Model
**Assigned to**: DA
**Duration**: 45 minutes

#### Subtasks:
- [ ] 1.1.1 Create DiagnosticSession model in `assessment/models.py`
  ```python
  class DiagnosticSession(models.Model):
      STATUS_CHOICES = [
          ('active', 'Active'),
          ('converged', 'Converged'),
          ('abandoned', 'Abandoned'),
          ('completed', 'Completed'),
      ]
      
      user = models.ForeignKey(
          settings.AUTH_USER_MODEL,
          on_delete=models.CASCADE,
          related_name='diagnostic_sessions'
      )
      skill = models.ForeignKey(
          'skills.Skill',
          on_delete=models.CASCADE,
          related_name='diagnostic_sessions'
      )
      
      # IRT State
      current_theta = models.FloatField(default=0.0)
      current_se = models.FloatField(default=1.0)
      question_count = models.IntegerField(default=0)
      status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
      
      # Timestamps
      started_at = models.DateTimeField(auto_now_add=True)
      completed_at = models.DateTimeField(null=True, blank=True)
      last_activity = models.DateTimeField(auto_now=True)
  ```

- [ ] 1.1.2 Add Meta class with indexes
  ```python
  class Meta:
      db_table = 'diagnostic_sessions'
      indexes = [
          models.Index(fields=['user', 'skill', 'status']),
          models.Index(fields=['status', 'last_activity']),
      ]
  ```

- [ ] 1.1.3 Add property methods
  ```python
  @property
  def has_converged(self):
      from django.conf import settings
      return self.current_se < settings.IRT_CONVERGENCE_THRESHOLD
  
  @property
  def should_terminate(self):
      from django.conf import settings
      return (self.has_converged or 
              self.question_count >= settings.IRT_MAX_QUESTIONS)
  ```

**Completion Criteria**: DiagnosticSession model complete with IRT tracking

---

### Task 1.2: QuestionBank Model
**Assigned to**: DA
**Duration**: 45 minutes

#### Subtasks:
- [ ] 1.2.1 Create QuestionBank model
  ```python
  class QuestionBank(models.Model):
      skill = models.ForeignKey(
          'skills.Skill',
          on_delete=models.CASCADE,
          related_name='questions'
      )
      
      question_text = models.TextField()
      options = ArrayField(
          models.CharField(max_length=500),
          size=4
      )
      correct_answer = models.IntegerField(
          validators=[MinValueValidator(0), MaxValueValidator(3)]
      )
      
      # IRT Parameters
      difficulty_b = models.FloatField(help_text='IRT difficulty parameter')
      discrimination_a = models.FloatField(default=1.0)
      guessing_c = models.FloatField(default=0.25, 
          validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
      
      # Quality Metrics
      times_used = models.IntegerField(default=0)
      times_correct = models.IntegerField(default=0)
      
      # AI Generation
      generated_by_ai = models.BooleanField(default=False)
      generation_prompt = models.TextField(blank=True)
      
      created_at = models.DateTimeField(auto_now_add=True)
      updated_at = models.DateTimeField(auto_now=True)
  ```

- [ ] 1.2.2 Add Meta and methods
  ```python
  class Meta:
      db_table = 'question_bank'
      indexes = [
          models.Index(fields=['skill', 'difficulty_b']),
          models.Index(fields=['difficulty_b']),
      ]
  
  def __str__(self):
      return f"{self.skill.preferred_label} - Q{self.id} (b={self.difficulty_b:.2f})"
  
  @property
  def difficulty_rating(self):
      if self.times_used == 0:
          return None
      return (self.times_correct / self.times_used) * 100
  ```

**Completion Criteria**: QuestionBank with IRT parameters ready

---

### Task 1.3: AnswerLog Model
**Assigned to**: DA
**Duration**: 30 minutes

#### Subtasks:
- [ ] 1.3.1 Create AnswerLog model
  ```python
  class AnswerLog(models.Model):
      session = models.ForeignKey(
          DiagnosticSession,
          on_delete=models.CASCADE,
          related_name='answers'
      )
      question = models.ForeignKey(
          QuestionBank,
          on_delete=models.CASCADE,
          related_name='answer_logs'
      )
      
      user_answer = models.IntegerField(
          validators=[MinValueValidator(0), MaxValueValidator(3)]
      )
      is_correct = models.BooleanField()
      
      # IRT State Tracking
      theta_before = models.FloatField()
      theta_after = models.FloatField()
      se_before = models.FloatField()
      se_after = models.FloatField()
      
      # Timing
      time_taken_seconds = models.IntegerField(null=True, blank=True)
      answered_at = models.DateTimeField(auto_now_add=True)
      
      class Meta:
          db_table = 'answer_logs'
          indexes = [
              models.Index(fields=['session', 'answered_at']),
              models.Index(fields=['question', 'is_correct']),
          ]
  ```

**Completion Criteria**: Complete answer tracking with IRT state snapshots

---

## Phase 2: IRT Calculation Engine (3 hours)

### Task 2.1: IRT Probability Function
**Assigned to**: DB
**Duration**: 45 minutes

#### Subtasks:
- [ ] 2.1.1 Create `assessment/irt_engine.py`
  ```python
  import numpy as np
  from scipy.optimize import minimize_scalar
  from scipy.stats import norm
  
  class IRTEngine:
      """Item Response Theory calculation engine using 3PL model."""
      
      @staticmethod
      def probability(theta, a, b, c):
          """
          Calculate probability of correct response using 3PL model.
          
          P(θ) = c + (1-c) / (1 + e^(-a(θ-b)))
          
          Args:
              theta: Ability parameter
              a: Discrimination parameter
              b: Difficulty parameter
              c: Guessing parameter
              
          Returns:
              Probability of correct response (0 to 1)
          """
          exponent = -a * (theta - b)
          return c + (1 - c) / (1 + np.exp(exponent))
  ```

- [ ] 2.1.2 Add information function
  ```python
  @staticmethod
  def information(theta, a, b, c):
      """
      Calculate Fisher information at theta.
      
      I(θ) = a² × P(θ) × Q(θ) / (1 - c)²
      where Q(θ) = 1 - P(θ)
      """
      p = IRTEngine.probability(theta, a, b, c)
      q = 1 - p
      info = (a ** 2 * p * q) / ((1 - c) ** 2)
      return info
  ```

- [ ] 2.1.3 Test the functions
  ```python
  # Test in Django shell
  from assessment.irt_engine import IRTEngine
  
  # Easy question (b=-1.0), good discrimination (a=1.5)
  prob = IRTEngine.probability(theta=0.5, a=1.5, b=-1.0, c=0.25)
  print(f"Probability: {prob:.2f}")  # Should be ~0.87
  
  info = IRTEngine.information(theta=0.5, a=1.5, b=-1.0, c=0.25)
  print(f"Information: {info:.2f}")  # Should be ~0.41
  ```

**Completion Criteria**: IRT probability and information functions working

---

### Task 2.2: Maximum Likelihood Estimation
**Assigned to**: DB
**Duration**: 1 hour 15 minutes

#### Subtasks:
- [ ] 2.2.1 Implement log-likelihood function
  ```python
  @staticmethod
  def log_likelihood(theta, answer_pattern, questions):
      """
      Calculate log-likelihood for theta given answer pattern.
      
      Args:
          theta: Ability to evaluate
          answer_pattern: List of boolean (correct/incorrect)
          questions: List of question objects with a, b, c params
          
      Returns:
          Negative log-likelihood (for minimization)
      """
      ll = 0.0
      for is_correct, q in zip(answer_pattern, questions):
          p = IRTEngine.probability(theta, q.discrimination_a, 
                                   q.difficulty_b, q.guessing_c)
          # Avoid log(0)
          p = np.clip(p, 1e-10, 1 - 1e-10)
          
          if is_correct:
              ll += np.log(p)
          else:
              ll += np.log(1 - p)
      
      return -ll  # Negative for minimization
  ```

- [ ] 2.2.2 Implement MLE theta estimation
  ```python
  @classmethod
  def estimate_theta(cls, answer_pattern, questions, bounds=(-4, 4)):
      """
      Estimate theta using Maximum Likelihood Estimation.
      
      Args:
          answer_pattern: List of boolean values
          questions: List of QuestionBank objects
          bounds: Search bounds for theta
          
      Returns:
          dict with theta estimate and standard error
      """
      if not answer_pattern:
          return {'theta': 0.0, 'se': 1.0}
      
      # Minimize negative log-likelihood
      result = minimize_scalar(
          lambda t: cls.log_likelihood(t, answer_pattern, questions),
          bounds=bounds,
          method='bounded'
      )
      
      theta_hat = result.x
      
      # Calculate standard error
      total_info = sum(
          cls.information(theta_hat, q.discrimination_a, 
                         q.difficulty_b, q.guessing_c)
          for q in questions
      )
      
      se = 1 / np.sqrt(total_info) if total_info > 0 else 1.0
      
      return {
          'theta': theta_hat,
          'se': se,
          'converged': result.success
      }
  ```

- [ ] 2.2.3 Test MLE estimation
  ```python
  # Create test questions
  from assessment.models import QuestionBank
  from skills.models import Skill
  
  skill = Skill.objects.first()
  questions = [
      QuestionBank(skill=skill, difficulty_b=-1.0, discrimination_a=1.5, guessing_c=0.25),
      QuestionBank(skill=skill, difficulty_b=0.0, discrimination_a=1.2, guessing_c=0.25),
      QuestionBank(skill=skill, difficulty_b=1.0, discrimination_a=1.3, guessing_c=0.25),
  ]
  
  # User got first 2 correct, last one wrong
  answer_pattern = [True, True, False]
  
  result = IRTEngine.estimate_theta(answer_pattern, questions)
  print(f"Theta: {result['theta']:.2f}, SE: {result['se']:.2f}")
  ```

**Completion Criteria**: MLE theta estimation working accurately

---

### Task 2.3: Adaptive Question Selection
**Assigned to**: DB
**Duration**: 1 hour

#### Subtasks:
- [ ] 2.3.1 Implement question selection algorithm
  ```python
  @classmethod
  def select_next_question(cls, current_theta, available_questions):
      """
      Select question that provides maximum information at current theta.
      
      Args:
          current_theta: Current ability estimate
          available_questions: QuerySet of unused questions
          
      Returns:
          QuestionBank object with highest information
      """
      if not available_questions.exists():
          return None
      
      max_info = -1
      best_question = None
      
      for question in available_questions:
          info = cls.information(
              current_theta,
              question.discrimination_a,
              question.difficulty_b,
              question.guessing_c
          )
          
          if info > max_info:
              max_info = info
              best_question = question
      
      return best_question
  ```

- [ ] 2.3.2 Add selection with difficulty spread
  ```python
  @classmethod
  def select_next_question_balanced(cls, current_theta, available_questions, 
                                    answered_count):
      """
      Select question with information maximization + difficulty balancing.
      
      Early questions: spread across difficulty range
      Later questions: focus on maximum information
      """
      if answered_count < 3:
          # First few questions: sample across difficulty range
          difficulties = [-1.5, 0.0, 1.5]
          target_b = difficulties[answered_count]
          
          # Find closest to target difficulty
          return min(
              available_questions,
              key=lambda q: abs(q.difficulty_b - target_b)
          )
      else:
          # Later questions: maximize information
          return cls.select_next_question(current_theta, available_questions)
  ```

**Completion Criteria**: Adaptive question selection implemented

---

## Phase 3: Assessment API & Service Layer (2 hours)

### Task 3.1: Assessment Service Class
**Assigned to**: DA
**Duration**: 1 hour

#### Subtasks:
- [ ] 3.1.1 Create `assessment/services.py`
  ```python
  from .models import DiagnosticSession, QuestionBank, AnswerLog
  from .irt_engine import IRTEngine
  from django.conf import settings
  
  class AssessmentService:
      """Service layer for diagnostic assessments."""
      
      @staticmethod
      def start_session(user, skill):
          """Start a new diagnostic session."""
          session = DiagnosticSession.objects.create(
              user=user,
              skill=skill,
              current_theta=0.0,
              current_se=1.0,
              status='active'
          )
          return session
      
      @staticmethod
      def get_next_question(session):
          """Get next adaptive question for session."""
          if session.should_terminate:
              return None
          
          # Get questions already answered in this session
          answered_question_ids = session.answers.values_list(
              'question_id', flat=True
          )
          
          # Get available questions for this skill
          available_questions = QuestionBank.objects.filter(
              skill=session.skill
          ).exclude(
              id__in=answered_question_ids
          )
          
          # Select next question
          next_question = IRTEngine.select_next_question_balanced(
              session.current_theta,
              available_questions,
              session.question_count
          )
          
          return next_question
  ```

- [ ] 3.1.2 Add answer submission method
  ```python
  @staticmethod
  def submit_answer(session, question, user_answer):
      """Submit answer and update theta estimate."""
      is_correct = (user_answer == question.correct_answer)
      
      # Get all answers including this one
      all_answers = list(session.answers.select_related('question'))
      answer_pattern = [a.is_correct for a in all_answers] + [is_correct]
      all_questions = [a.question for a in all_answers] + [question]
      
      # Estimate new theta
      theta_before = session.current_theta
      se_before = session.current_se
      
      estimation = IRTEngine.estimate_theta(answer_pattern, all_questions)
      theta_after = estimation['theta']
      se_after = estimation['se']
      
      # Log the answer
      answer_log = AnswerLog.objects.create(
          session=session,
          question=question,
          user_answer=user_answer,
          is_correct=is_correct,
          theta_before=theta_before,
          theta_after=theta_after,
          se_before=se_before,
          se_after=se_after
      )
      
      # Update session
      session.current_theta = theta_after
      session.current_se = se_after
      session.question_count += 1
      
      if session.should_terminate:
          session.status = 'converged' if session.has_converged else 'completed'
          session.completed_at = timezone.now()
      
      session.save()
      
      # Update question stats
      question.times_used += 1
      if is_correct:
          question.times_correct += 1
      question.save()
      
      return answer_log
  ```

**Completion Criteria**: Complete assessment service with theta updates

---

### Task 3.2: Assessment API Views
**Assigned to**: DA
**Duration**: 1 hour

#### Subtasks:
- [ ] 3.2.1 Create serializers in `assessment/serializers.py`
  ```python
  from rest_framework import serializers
  from .models import DiagnosticSession, QuestionBank, AnswerLog
  
  class QuestionBankSerializer(serializers.ModelSerializer):
      class Meta:
          model = QuestionBank
          fields = ['id', 'question_text', 'options']
          # Don't expose correct_answer or IRT params to client
  
  class DiagnosticSessionSerializer(serializers.ModelSerializer):
      skill_name = serializers.CharField(source='skill.preferred_label', read_only=True)
      
      class Meta:
          model = DiagnosticSession
          fields = ['id', 'skill', 'skill_name', 'current_theta', 
                   'current_se', 'question_count', 'status', 
                   'started_at', 'completed_at']
          read_only_fields = ['current_theta', 'current_se', 'question_count']
  
  class AnswerSubmitSerializer(serializers.Serializer):
      question_id = serializers.IntegerField()
      user_answer = serializers.IntegerField(min_value=0, max_value=3)
  ```

- [ ] 3.2.2 Create viewsets in `assessment/views.py`
  ```python
  from rest_framework import viewsets, status
  from rest_framework.decorators import action
  from rest_framework.response import Response
  from .models import DiagnosticSession
  from .services import AssessmentService
  from .serializers import *
  
  class AssessmentViewSet(viewsets.ViewSet):
      """Diagnostic assessment endpoints."""
      
      @action(detail=False, methods=['post'])
      def start(self, request):
          """Start new diagnostic session for a skill."""
          skill_id = request.data.get('skill_id')
          
          if not skill_id:
              return Response(
                  {'error': 'skill_id required'},
                  status=status.HTTP_400_BAD_REQUEST
              )
          
          session = AssessmentService.start_session(
              user=request.user,
              skill_id=skill_id
          )
          
          return Response(
              DiagnosticSessionSerializer(session).data,
              status=status.HTTP_201_CREATED
          )
      
      @action(detail=True, methods=['get'])
      def next_question(self, request, pk=None):
          """Get next adaptive question."""
          session = DiagnosticSession.objects.get(pk=pk, user=request.user)
          
          question = AssessmentService.get_next_question(session)
          
          if question is None:
              return Response({
                  'completed': True,
                  'final_theta': session.current_theta,
                  'final_se': session.current_se
              })
          
          return Response(QuestionBankSerializer(question).data)
      
      @action(detail=True, methods=['post'])
      def submit_answer(self, request, pk=None):
          """Submit answer to question."""
          session = DiagnosticSession.objects.get(pk=pk, user=request.user)
          
          serializer = AnswerSubmitSerializer(data=request.data)
          serializer.is_valid(raise_exception=True)
          
          question = QuestionBank.objects.get(
              id=serializer.validated_data['question_id']
          )
          
          answer_log = AssessmentService.submit_answer(
              session=session,
              question=question,
              user_answer=serializer.validated_data['user_answer']
          )
          
          return Response({
              'correct': answer_log.is_correct,
              'theta_updated': answer_log.theta_after,
              'se': answer_log.se_after,
              'should_continue': not session.should_terminate
          })
  ```

- [ ] 3.2.3 Add URL routing in `assessment/urls.py`
  ```python
  from rest_framework.routers import DefaultRouter
  from .views import AssessmentViewSet
  
  router = DefaultRouter()
  router.register(r'assessment', AssessmentViewSet, basename='assessment')
  
  urlpatterns = router.urls
  ```

**Completion Criteria**: Complete API for starting, getting questions, submitting answers

---

## Phase 4: Skill Gap Analysis (1 hour)

### Task 4.1: SkillGap Model & Calculation
**Assigned to**: DB
**Duration**: 1 hour

#### Subtasks:
- [ ] 4.1.1 Create SkillGap model
  ```python
  class SkillGap(models.Model):
      user = models.ForeignKey(
          settings.AUTH_USER_MODEL,
          on_delete=models.CASCADE,
          related_name='skill_gaps'
      )
      occupation = models.ForeignKey(
          'skills.Occupation',
          on_delete=models.CASCADE,
          related_name='user_gaps'
      )
      skill = models.ForeignKey(
          'skills.Skill',
          on_delete=models.CASCADE,
          related_name='user_gaps'
      )
      
      # Gap Metrics
      current_level = models.FloatField(help_text='Current theta')
      required_level = models.FloatField(help_text='Required theta for occupation')
      gap_score = models.FloatField(help_text='required - current')
      
      criticality_coefficient = models.FloatField(
          default=1.0,
          help_text='Weight based on importance and prerequisites'
      )
      priority_score = models.FloatField(
          help_text='gap_score * criticality_coefficient'
      )
      
      addressed = models.BooleanField(default=False)
      
      computed_at = models.DateTimeField(auto_now_add=True)
      updated_at = models.DateTimeField(auto_now=True)
      
      class Meta:
          db_table = 'skill_gaps'
          unique_together = ['user', 'occupation', 'skill']
          indexes = [
              models.Index(fields=['user', 'priority_score']),
              models.Index(fields=['addressed']),
          ]
          ordering = ['-priority_score']
  ```

- [ ] 4.1.2 Create gap calculation service
  ```python
  # In assessment/services.py
  
  @staticmethod
  def calculate_skill_gaps(user, target_occupation):
      """Calculate skill gaps for user targeting specific occupation."""
      from skills.models import OccupationSkill
      from users.models import UserProficiency
      
      # Get required skills for occupation
      required_skills = OccupationSkill.objects.filter(
          occupation=target_occupation
      ).select_related('skill')
      
      gaps = []
      
      for occ_skill in required_skills:
          # Get user's current proficiency
          try:
              proficiency = UserProficiency.objects.get(
                  user=user,
                  skill=occ_skill.skill
              )
              current_theta = proficiency.theta
          except UserProficiency.DoesNotExist:
              current_theta = -2.0  # Assume very low if not assessed
          
          # Calculate gap
          required_theta = occ_skill.required_proficiency_theta
          gap = required_theta - current_theta
          
          if gap > 0:  # Only gaps, not excesses
              # Calculate criticality coefficient
              importance = occ_skill.importance
              prerequisite_count = occ_skill.skill.prerequisites.count()
              dependent_count = occ_skill.skill.required_for.count()
              
              criticality = importance * (1 + 0.1 * prerequisite_count + 
                                         0.1 * dependent_count)
              
              priority = gap * criticality
              
              skill_gap = SkillGap.objects.update_or_create(
                  user=user,
                  occupation=target_occupation,
                  skill=occ_skill.skill,
                  defaults={
                      'current_level': current_theta,
                      'required_level': required_theta,
                      'gap_score': gap,
                      'criticality_coefficient': criticality,
                      'priority_score': priority
                  }
              )[0]
              
              gaps.append(skill_gap)
      
      return gaps
  ```

- [ ] 4.1.3 Add API endpoint for skill gaps
  ```python
  # In assessment/views.py, add to AssessmentViewSet:
  
  @action(detail=False, methods=['get'])
  def skill_gaps(self, request):
      """Get user's skill gaps for target occupation."""
      occupation_id = request.query_params.get('occupation_id')
      
      if not occupation_id:
          return Response(
              {'error': 'occupation_id required'},
              status=status.HTTP_400_BAD_REQUEST
          )
      
      occupation = Occupation.objects.get(id=occupation_id)
      gaps = AssessmentService.calculate_skill_gaps(
          user=request.user,
          target_occupation=occupation
      )
      
      return Response(SkillGapSerializer(gaps, many=True).data)
  ```

**Completion Criteria**: Skill gap calculation with priority ranking working

---

## Phase 5: Sample Data & Testing (30 minutes)

### Task 5.1: Generate Sample Questions
**Assigned to**: DA
**Duration**: 30 minutes

#### Subtasks:
- [ ] 5.1.1 Create management command `assessment/management/commands/generate_sample_questions.py`
  ```python
  from django.core.management.base import BaseCommand
  from assessment.models import QuestionBank
  from skills.models import Skill
  import random
  
  class Command(BaseCommand):
      help = 'Generate sample IRT-calibrated questions'
      
      def handle(self, *args, **options):
          skills = Skill.objects.all()[:5]
          
          for skill in skills:
              # Generate 20 questions per skill across difficulty range
              for i in range(20):
                  difficulty_b = random.uniform(-2.0, 2.0)
                  discrimination_a = random.uniform(0.8, 2.0)
                  
                  QuestionBank.objects.create(
                      skill=skill,
                      question_text=f"Sample {skill.preferred_label} question {i+1} (b={difficulty_b:.2f})",
                      options=[
                          f"Option A for difficulty {difficulty_b:.1f}",
                          f"Option B for difficulty {difficulty_b:.1f}",
                          f"Option C for difficulty {difficulty_b:.1f}",
                          f"Option D for difficulty {difficulty_b:.1f}",
                      ],
                      correct_answer=random.randint(0, 3),
                      difficulty_b=difficulty_b,
                      discrimination_a=discrimination_a,
                      guessing_c=0.25,
                      generated_by_ai=False
                  )
              
              self.stdout.write(
                  self.style.SUCCESS(
                      f'Generated 20 questions for {skill.preferred_label}'
                  )
              )
  ```

- [ ] 5.1.2 Run the command
  ```bash
  python manage.py generate_sample_questions
  ```

**Completion Criteria**: Sample questions available for testing

---

## Summary Checklist

### Must Complete Today
- [x] DiagnosticSession, QuestionBank, AnswerLog models created
- [x] IRT probability and information functions working
- [x] MLE theta estimation implemented
- [x] Adaptive question selection algorithm
- [x] API endpoints for assessment flow
- [x] Skill gap calculation with priority scoring
- [x] Sample questions generated
- [x] Migrations run successfully
- [x] Tests passing

### Good to Have (If Time Permits)
- [ ] Question difficulty calibration algorithm
- [ ] Advanced analytics on theta convergence
- [ ] Visualization of theta trajectory
- [ ] Export assessment results

---

## Developer Sync Points

### Morning Standup (15 min)
- Review IRT concepts together
- Assign Phase 1-2 tasks
- DA: Models, DB: Algorithms

### Mid-Day Check-in (15 min)
- DA: Models complete?
- DB: IRT engine working?
- Integrate and test together

### End-of-Day Review (30 min)
- Run complete assessment flow
- Test adaptive selection
- Calculate skill gaps
- Review theta estimation accuracy

---

## Time Tracking

| Phase | Estimated | Actual | Notes |
|-------|-----------|--------|-------|
| Phase 1: Models | 2h | | |
| Phase 2: IRT Engine | 3h | | |
| Phase 3: API Layer | 2h | | |
| Phase 4: Skill Gaps | 1h | | |
| **Total** | **8h** | | |

---

**Notes**:
- IRT is mathematically intensive - take time to understand
- Test theta estimation with known answer patterns
- Validate convergence detection works
- Ensure adaptive selection improves with each question
