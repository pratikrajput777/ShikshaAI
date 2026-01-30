from django.db.models.signals import post_save
from django.dispatch import receiver

from learning.models import Lesson
from gamification.services import PointsService


@receiver(post_save, sender=Lesson)
def lesson_completed(sender, instance, created, **kwargs):


    if created and instance.status == "completed":
        PointsService.award_points(
            instance.module.study_plan.user,
            "lesson_complete"
        )
        return

    # update case
    if not created:
        try:
            old = Lesson.objects.get(pk=instance.pk)
        except Lesson.DoesNotExist:
            return

    
        if instance.status == "completed":
            PointsService.award_points(
                instance.module.study_plan.user,
                "lesson_complete"
            )
