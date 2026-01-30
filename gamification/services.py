from django.db import transaction
from .models import UserPoints, Achievement, UserAchievement, LeaderboardEntry
from learning.models import Lesson
from assessment.models import CFUAttempt
import logging

logger = logging.getLogger(__name__)

class PointsService:
    """Service for awarding and managing points."""
    
    POINT_VALUES = {
        'lesson_complete': 50,
        'quiz_pass': 30,
        'interview_complete': 100,
        'daily_login': 10,
        'streak_7day': 200,
        'referral_made': 100,
        'referral_signup': 50,
    }
    
    @classmethod
    @transaction.atomic
    def award_points(cls, user, action_type: str, amount: int = None) -> int:
        """
        Award points for user action.
        
        Args:
            user: User object
            action_type: Type of action (from POINT_VALUES)
            amount: Optional custom amount (overrides POINT_VALUES)
        
        Returns:
            Points awarded
        """
        points_awarded = amount or cls.POINT_VALUES.get(action_type, 0)
        
        # Get or create user points
        user_points, created = UserPoints.objects.get_or_create(user=user)
        
        # Award points
        user_points.total_points += points_awarded
        
        # Calculate level: Level = floor(sqrt(total_points / 100))
        user_points.level = int((user_points.total_points / 100) ** 0.5)
        
        user_points.save()
        
        logger.info(f"Awarded {points_awarded} points to {user} for {action_type}")
        
        # Check for achievements
        cls.check_achievements(user)
        
        # Update leaderboard
        cls.update_leaderboard_entry(user)
        
        return points_awarded
    
    @classmethod
    def check_achievements(cls, user):
        """Check and unlock achievements for user."""
        achievements = Achievement.objects.all()
        user_points = UserPoints.objects.get(user=user)
        
        for achievement in achievements:
            # Check if already unlocked
            user_ach, created = UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
            
            if user_ach.unlocked:
                continue
            
            # Check unlock criteria
            criteria = achievement.unlock_criteria
            unlocked = False
            
            if criteria['type'] == 'lessons_completed':
                count = Lesson.objects.filter(
                    module__study_plan__user=user,
                    status='completed'
                ).count()
                unlocked = count >= criteria['count']
            
            elif criteria['type'] == 'points':
                unlocked = user_points.total_points >= criteria['min']
            
            elif criteria['type'] == 'level':
                unlocked = user_points.level >= criteria['min']
            
            # Unlock if criteria met
            if unlocked:
                user_ach.unlocked = True
                user_ach.save()
                
                # Award bonus points
                if achievement.points_reward > 0:
                    cls.award_points(user, 'achievement_unlock', achievement.points_reward)
                
                logger.info(f"Achievement unlocked: {achievement.name} for {user}")
    
    @classmethod
    def update_leaderboard_entry(cls, user, leaderboard_type='weekly'):
        """Update user's leaderboard entry."""
        from django.utils import timezone
        from datetime import timedelta
        
        user_points = UserPoints.objects.get(user=user)
        
        # Calculate period
        now = timezone.now()
        if leaderboard_type == 'weekly':
            period_start = now - timedelta(days=now.weekday())
        elif leaderboard_type == 'monthly':
            period_start = now.replace(day=1)
        else:
            period_start = None
        
        # Update or create entry
        entry, created = LeaderboardEntry.objects.update_or_create(
            user=user,
            leaderboard_type=leaderboard_type,
            defaults={
                'score': user_points.total_points,
                'period_start': period_start
            }
        )
        
        return entry