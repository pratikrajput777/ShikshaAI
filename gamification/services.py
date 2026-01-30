from django.db import transaction
from django.utils import timezone

from gamification.models import (
    UserPoints,
    Achievement,
    UserAchievement,
    LeaderboardEntry
)

# only for checking criteria
from learning.models import Lesson


class PointsService:

    POINT_VALUES = {
        'lesson_complete': 50,
        'quiz_pass': 30,
        'interview_complete': 100,
        'daily_login': 10,
        'streak_7day': 200,
        'referral_made': 100,
        'referred_signup': 50,
    }

    @staticmethod
    @transaction.atomic
    def award_points(user, action_type, context=None):

        points_obj, _ = UserPoints.objects.get_or_create(user=user)

        award = PointsService.POINT_VALUES.get(action_type, 0)

        if award > 0:
            points_obj.award_points(award, action_type)

        PointsService.check_achievements(user)
        PointsService.update_leaderboard(user)

        return award

    # -------------------------
    # ACHIEVEMENTS
    # -------------------------
    @staticmethod
    def check_achievements(user):

        achievements = Achievement.objects.all()

        for achievement in achievements:

            user_ach, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )

            if user_ach.unlocked_at:
                continue

            criteria = achievement.unlock_criteria
            criteria_type = criteria.get("type")

            progress = 0
            unlocked = False

            if criteria_type == "lessons_completed":

                required = int(criteria.get("count", 0))

                progress = Lesson.objects.filter(
                    module__study_plan__user=user,
                    status="completed"
                ).count()

                if progress >= required:
                    unlocked = True

            user_ach.progress = progress

            if unlocked:
                user_ach.unlocked_at = timezone.now()

                # reward achievement points
                user_points, _ = UserPoints.objects.get_or_create(user=user)
                user_points.award_points(
                    achievement.points_reward,
                    reason="achievement_unlock"
                )

            user_ach.save()

    # -------------------------
    # LEADERBOARD
    # -------------------------
    @staticmethod
    def update_leaderboard(user):

        user_points, _ = UserPoints.objects.get_or_create(user=user)

        entry, _ = LeaderboardEntry.objects.get_or_create(
            user=user,
            leaderboard_type=LeaderboardEntry.ALL_TIME,
            period_start=None,
            defaults={
                "score": 0,
                "rank": 0
            }
        )

        entry.score = user_points.total_points
        entry.save()
