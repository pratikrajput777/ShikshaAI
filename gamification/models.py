from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Achievement(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50)
    points_reward = models.IntegerField(default=0)

    # example:
    # {"type":"lessons_completed","count":10}
    unlock_criteria = models.JSONField()

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    progress = models.IntegerField(default=0)

    class Meta:
        unique_together = ("user", "achievement")


class UserPoints(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_points = models.IntegerField(default=0)
    level = models.IntegerField(default=0)

    current_streak_days = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    def award_points(self, points, reason=None):
        self.total_points += points

        # simple level formula
        self.level = int((self.total_points / 100) ** 0.5)

        self.save()


class LeaderboardEntry(models.Model):

    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"

    LEADERBOARD_TYPES = (
        (WEEKLY, "Weekly"),
        (MONTHLY, "Monthly"),
        (ALL_TIME, "All Time"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    leaderboard_type = models.CharField(
        max_length=20,
        choices=LEADERBOARD_TYPES
    )

    score = models.IntegerField(default=0)
    rank = models.IntegerField(default=0)

    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "leaderboard_type", "period_start")


class DailyChallenge(models.Model):
    date = models.DateField(unique=True)
    challenge_type = models.CharField(max_length=50)
    target_value = models.IntegerField()
    points_reward = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.challenge_type} - {self.date}"


class UserChallenge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(DailyChallenge, on_delete=models.CASCADE)

    progress = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "challenge")

from django.contrib import admin
from .models import (
    Achievement,
    UserAchievement,
    UserPoints,
    LeaderboardEntry,
    DailyChallenge,
    UserChallenge
)

admin.site.register(Achievement)
admin.site.register(UserAchievement)
admin.site.register(UserPoints)
admin.site.register(LeaderboardEntry)
admin.site.register(DailyChallenge)
admin.site.register(UserChallenge)

