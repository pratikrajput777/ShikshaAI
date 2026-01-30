from django.db.models.signals import post_save
from django.dispatch import receiver
from learning.models import Lesson
from assessment.models import CFUAttempt
from interview.models import ConversationSession
from .services import PointsService

@receiver(post_save, sender=Lesson)
def lesson_completed_points(sender, instance, **kwargs):
    """Award points when lesson completed."""
    if instance.status == 'completed':
        PointsService.award_points(
            instance.module.study_plan.user,
            'lesson_complete'
        )

@receiver(post_save, sender=CFUAttempt)
def quiz_passed_points(sender, instance, created, **kwargs):
    """Award points when quiz passed."""
    if created and instance.passed:
        PointsService.award_points(
            instance.user,
            'quiz_pass'
        )

@receiver(post_save, sender=ConversationSession)
def interview_completed_points(sender, instance, **kwargs):
    """Award points when interview evaluated."""
    if instance.status == 'evaluated':
        PointsService.award_points(
            instance.user,
            'interview_complete'
        )