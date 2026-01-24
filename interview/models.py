from django.db import models

from django.db import models
from django.conf import settings


class ConversationSession(models.Model):
    """
    Represents a single mock interview session for a user
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('evaluated', 'Evaluated'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interview_sessions'
    )

    occupation = models.ForeignKey(
        'skills.Occupation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    job_description = models.TextField(blank=True)

    # Session state
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    current_question_number = models.PositiveIntegerField(default=0)
    target_question_count = models.PositiveIntegerField(default=10)

    # AI models used
    question_generator_model = models.CharField(
        max_length=50,
        default='gemini-1.5-flash'
    )
    evaluator_model = models.CharField(
        max_length=50,
        default='gemini-1.5-pro'
    )

    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'conversation_sessions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['started_at']),
        ]

    def __str__(self):
        return f"InterviewSession #{self.id} - {self.user}"

class InterviewTurn(models.Model):
    """
    Stores each question and answer exchanged during the interview
    """

    SPEAKER_CHOICES = [
        ('interviewer', 'Interviewer (AI)'),
        ('candidate', 'Candidate (User)'),
    ]

    session = models.ForeignKey(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name='turns'
    )

    turn_number = models.PositiveIntegerField()
    speaker = models.CharField(max_length=20, choices=SPEAKER_CHOICES)

    text_content = models.TextField()
    audio_url = models.URLField(max_length=500, blank=True)

    # Optional analytics fields
    sentiment_score = models.FloatField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'interview_turns'
        ordering = ['turn_number']
        unique_together = ('session', 'turn_number')

    def __str__(self):
        return f"Turn {self.turn_number} ({self.speaker})"

class InterviewEvaluation(models.Model):
    """
    Stores AI evaluation after interview completion
    """

    session = models.OneToOneField(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name='evaluation'
    )

    # Three judge scores (0.0 - 1.0)
    technical_score = models.FloatField()
    behavioral_score = models.FloatField()
    structural_score = models.FloatField()

    overall_score = models.FloatField()

    # Detailed feedback (JSON)
    technical_feedback = models.JSONField(default=dict)
    behavioral_feedback = models.JSONField(default=dict)
    structural_feedback = models.JSONField(default=dict)

    overall_feedback = models.TextField()
    improvement_areas = models.JSONField(default=list)

    evaluated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'interview_evaluations'

    def __str__(self):
        return f"Evaluation for Session #{self.session.id}"

