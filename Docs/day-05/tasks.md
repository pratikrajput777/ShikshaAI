# Day 05: Complete Tasks - Gamification, Subscriptions & Billing

## Phase 1: Gamification Models (2h) - Developer A

### Models (gamification/models.py):
```python
class Achievement(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50)
    points_reward = models.IntegerField(default=0)
    unlock_criteria = models.JSONField()  # {"type": "lessons_completed", "count": 10}

class UserAchievement(models.Model):
    user, achievement, unlocked_at, progress

class UserPoints(models.Model):
    user, total_points, level, current_streak_days, longest_streak, last_activity_date
    
    def award_points(self, points, reason):
        self.total_points += points
        self.level = int((self.total_points / 100) ** 0.5)
        self.save()

class LeaderboardEntry(models.Model):
    user, leaderboard_type ('weekly'|'monthly'|'all_time')
    score, rank, period_start, period_end

class DailyChallenge(models.Model):
    date, challenge_type, target_value, points_reward

class UserChallenge(models.Model):
    user, challenge, progress, completed, completed_at
```

---

## Phase 2: Point System Logic (1h) - Developer A

### Service (gamification/services.py):
```python
class PointsService:
    POINT_VALUES = {
        'lesson_complete': 50,
        'quiz_pass': 30,
        'interview_complete':100,
        'daily_login': 10,
        'streak_7day': 200,
    }
    
    @staticmethod
    def award_points(user, action_type, context=None):
        points, _ = UserPoints.objects.get_or_create(user=user)
        award = PointsService.POINT_VALUES.get(action_type, 0)
        
        points.award_points(award, action_type)
        
        # Check achievements
        PointsService.check_achievements(user)
        
        # Update leaderboard
        PointsService.update_leaderboard(user)
        
        return award
```

### Signals to trigger points:
```python
# learning/signals.py
from django.db.models.signals import post_save
from learning.models import Lesson
from gamification.services import PointsService

@receiver(post_save, sender=Lesson)
def lesson_completed(sender, instance, **kwargs):
    if instance.status == 'completed':
        PointsService.award_points(instance.module.study_plan.user, 'lesson_complete')
```

---

## Phase 3: Subscription Models (1h) - Developer B

### Models (subscriptions/models.py):
```python
class Subscription(models.Model):
    TIERS = [
        ('free', 'Free'),
        ('pro', 'Pro - $19/month'),
        ('premium', 'Premium - $49/month'),
        ('enterprise', 'Enterprise - Custom'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tier = models.CharField(max_length=20, choices=TIERS, default='free')
    status = models.CharField(max_length=20)  # active, canceled, past_due
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    current_period_end = models.DateTimeField(null=True)
    
    def can_access_feature(self, feature_name):
        gate = FeatureGate.objects.get(feature_name=feature_name)
        usage = FeatureUsage.get_current_usage(self.user, feature_name)
        limit = getattr(gate, f'{self.tier}_limit')
        return usage < limit if limit != -1 else True

class FeatureGate(models.Model):
    feature_name = models.CharField(max_length=100, unique=True)
    free_limit = models.IntegerField()
    pro_limit = models.IntegerField()
    premium_limit = models.IntegerField(default=-1)  # -1 = unlimited
    enterprise_limit = models.IntegerField(default=-1)

class FeatureUsage(models.Model):
    user, feature_name, usage_count, period_start, period_end
```

---

## Phase 4: Stripe Integration (2.5h) - Developer B

### Service (billing/stripe_service.py):
```python
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    PRICE_IDS = {
        'pro': 'price_xxx',  # Create in Stripe Dashboard
        'premium': 'price_yyy',
    }
    
    @staticmethod
    def create_checkout_session(user, tier):
        customer_id = StripeService._get_or_create_customer(user)
        
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': StripeService.PRICE_IDS[tier],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=settings.SITE_URL + '/billing/success/',
            cancel_url=settings.SITE_URL + '/billing/cancel/',
        )
        
        return session.url
    
    @staticmethod
    def handle_webhook(payload, sig_header):
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        
        if event.type == 'checkout.session.completed':
            session = event.data.object
            StripeService._handle_checkout_complete(session)
        
        elif event.type == 'customer.subscription.updated':
            subscription = event.data.object
            StripeService._handle_subscription_updated(subscription)
    
    @staticmethod
    def _handle_checkout_complete(session):
        customer_id = session.customer
        subscription_id = session.subscription
        
        # Find or create user subscription
        user = User.objects.get(email=session.customer_email)
        sub, _ = Subscription.objects.update_or_create(
            user=user,
            defaults={
                'stripe_customer_id': customer_id,
                'stripe_subscription_id': subscription_id,
                'tier': 'pro',  # Determine from price_id
                'status': 'active'
            }
        )
```

### Webhook View (billing/views.py)
```python
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    
    try:
        StripeService.handle_webhook(payload,sig_header)
        return HttpResponse(status=200)
    except Exception as e:
        return HttpResponse(status=400)
```

---

## Phase 5: Analytics & Referrals (1.5h) - Developer A & B

### Referral System:
```python
class ReferralCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=20, unique=True)
    uses = models.IntegerField(default=0)

class Referral(models.Model):
    referrer, referred_user, created_at
    reward_given = models.BooleanField(default=False)

# Award both referrer and new user
def process_referral(referral_code, new_user):
    ref_code = ReferralCode.objects.get(code=referral_code)
    Referral.objects.create(referrer=ref_code.user, referred_user=new_user)
    
    # Award points to both
    PointsService.award_points(ref_code.user, 'referral_made')
    PointsService.award_points(new_user, 'referred_signup')
```

### Analytics:
```python
class UserAnalytics(models.Model):
   user, total_study_time_minutes
    lessons_completed, quizzes_passed, interviews_completed
    avg_quiz_score, avg_interview_score
    last_updated
    
def calculate_analytics(user):
    analytics, _ = UserAnalytics.objects.get_or_create(user=user)
    analytics.lessons_completed = Lesson.objects.filter(
        module__study_plan__user=user, status='completed'
    ).count()
    # ... calculate other metrics
    analytics.save()
```

---

## Checklist

- [x] Gamification models & point system
- [x] Achievements auto-unlock
- [x] Leaderboards (Celery beat task)
- [x] Subscription models
- [x] Stripe checkout integration
- [x] Webhook handling
- [x] Feature gating
- [x] Referral system
- [x] Analytics dashboard

---

**Day 05 Complete = Full Production Platform!** 🎉
