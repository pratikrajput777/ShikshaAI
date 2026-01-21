from django.db import models
from django.conf import settings


# -----------------------------
# Study Plan (Macro root)
# -----------------------------
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
        if self.total_modules == 0:
            self.progress_percentage = 0
        else:
            self.progress_percentage = (self.completed_modules / self.total_modules) * 100
        self.save()


# -----------------------------
# Learning Module (Macro tier)
# -----------------------------
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


# -----------------------------
# Lesson (Meso tier)
# -----------------------------
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

    # AI metadata
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


# -----------------------------
# CFU Quiz & Attempts
# -----------------------------
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


# -----------------------------
# Remediation
# -----------------------------
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
