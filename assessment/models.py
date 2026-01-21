from django.db import models
from django.conf import settings

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


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

    # IRT state
    current_theta = models.FloatField(default=0.0)
    current_se = models.FloatField(default=1.0)
    question_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    # timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'diagnostic_sessions'
        indexes = [
            models.Index(fields=['user', 'skill', 'status']),
            models.Index(fields=['status', 'last_activity']),
        ]

    @property
    def has_converged(self):
        return self.current_se < settings.IRT_CONVERGENCE_THRESHOLD

    @property
    def should_terminate(self):
        return (
            self.has_converged or
            self.question_count >= settings.IRT_MAX_QUESTIONS
        )


class QuestionBank(models.Model):
      skill = models.ForeignKey(
          'skills.Skill',
          on_delete=models.CASCADE,
          related_name='questions'
      )
      
      question_text = models.TextField()
      options = models.JSONField(default=list)
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



class Meta:
      db_table = 'question_bank'
      indexes = [
          models.Index(fields=['skill', 'difficulty_b']),
          models.Index(fields=['difficulty_b']),
      ]
  
def _str_(self):
      return f"{self.skill.preferred_label} - Q{self.id} (b={self.difficulty_b:.2f})"
  
@property
def difficulty_rating(self):
      if self.times_used == 0:
          return None
      return (self.times_correct / self.times_used) * 100

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




