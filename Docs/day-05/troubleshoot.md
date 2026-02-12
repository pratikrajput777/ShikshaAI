# Day 05: Troubleshooting Guide

Common issues with gamification, subscriptions, and Stripe integration.

---

## Gamification Issues

### ❌ Points Not Awarded After Actions

**Symptoms:** User completes lesson but points don't increase

**Solution:**
```python
# 1. Check signals are registered
# In learning/apps.py:
class LearningConfig(AppConfig):
    name = 'learning'
    
    def ready(self):
        import learning.signals  # MUST import signals here

# 2. Test signal manually
from learning.models import Lesson
from gamification.services import PointsService

lesson = Lesson.objects.first()
lesson.status = 'completed'
lesson.save()  # Should trigger signal

# Check points
from gamification.models import UserPoints
points = UserPoints.objects.get(user=lesson.module.study_plan.user)
print(f"Total points: {points.total_points}")

# 3. Debug signal
# Add logging in signals.py
import logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Lesson)
def lesson_completed(sender, instance, **kwargs):
    logger.info(f"Signal triggered for lesson {instance.id}")
    if instance.status == 'completed':
        logger.info(f"Awarding points to {instance.module.study_plan.user}")
        PointsService.award_points(...)
```

---

### ❌ Achievements Not Unlocking

**Symptoms:** User meets criteria but achievement stays locked

**Solution:**
```python
# Check unlock criteria format
achievement = Achievement.objects.get(name="First Lesson")
print(achievement.unlock_criteria)
# Should be: {"type": "lessons_completed", "count": 1}

# Manual unlock test
from gamification.services import AchievementService

user = User.objects.first()
AchievementService.check_and_unlock(user, achievement)

# Debug criteria check
def check_unlock_criteria(user, achievement):
    criteria = achievement.unlock_criteria
    
    if criteria['type'] == 'lessons_completed':
        count = Lesson.objects.filter(
            module__study_plan__user=user,
            status='completed'
        ).count()
        
        print(f"User has {count} lessons, needs {criteria['count']}")
        return count >= criteria['count']
```

---

## Subscription Issues

### ❌ Stripe Webhook Not Receiving Events

**Symptoms:** Checkout succeeds but subscription not created

**Solution:**
```bash
# 1. Test webhook endpoint
curl -X POST http://localhost:8000/api/billing/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"type": "test"}'

# 2. Use Stripe CLI for local testing
stripe login
stripe listen --forward-to localhost:8000/api/billing/webhook/

# 3. Trigger test event
stripe trigger checkout.session.completed

# 4. Check webhook secret matches
# In .env:
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Get secret from Stripe Dashboard or CLI:
stripe listen --print-secret

# 5. Verify webhook endpoint in Stripe Dashboard
# Should be: https://yourdomain.com/api/billing/webhook/
```

---

### ❌ Stripe API Key Invalid

**Symptoms:**
```python
stripe.error.AuthenticationError: Invalid API Key
```

**Solution:**
```bash
# 1. Check API keys in .env
STRIPE_PUBLISHABLE_KEY=pk_test_xxx  # Starts with pk_test (test) or pk_live (production)
STRIPE_SECRET_KEY=sk_test_xxx  # Starts with sk_test or sk_live

# 2. Verify in Django settings
from django.conf import settings
print(f"Key: {settings.STRIPE_SECRET_KEY[:10]}...")

# 3. Test key directly
import stripe
stripe.api_key = 'sk_test_xxx'
try:
    stripe.Customer.list(limit=1)
    print("✓ Key valid")
except stripe.error.AuthenticationError:
    print("✗ Key invalid")

# 4. Don't mix test and live keys
# Use test keys (pk_test_, sk_test_) for development
# Use live keys (pk_live_, sk_live_) for production
```

---

### ❌ Feature Gate Always Allows Access

**Symptoms:** Free tier users can access unlimited features

**Solution:**
```python
# 1. Check FeatureGate exists
gates = FeatureGate.objects.all()
for gate in gates:
    print(f"{gate.feature_name}: free={gate.free_limit}")

# If missing, create:
FeatureGate.objects.get_or_create(
    feature_name='assessment',
    defaults={
        'free_limit': 3,
        'pro_limit': -1,  # unlimited
        'premium_limit': -1,
        'enterprise_limit': -1
    }
)

# 2. Check usage counting
from subscriptions.models import FeatureUsage

usage = FeatureUsage.objects.filter(
    user=user,
    feature_name='assessment',
    period_end__gte=timezone.now()
).count()

print(f"Current usage: {usage}")

# 3. Ensure usage is recorded
def record_feature_usage(user, feature_name):
    from dateutil.relativedelta import relativedelta
    
    FeatureUsage.objects.create(
        user=user,
        feature_name=feature_name,
        usage_count=1,
        period_start=timezone.now(),
        period_end=timezone.now() + relativedelta(months=1)
    )

# 4. Check subscription tier
sub = Subscription.objects.get(user=user)
print(f"User tier: {sub.tier}")

# 5. Test can_access_feature logic
result = sub.can_access_feature('assessment')
print(f"Can access: {result}")
```

---

## Leaderboard Issues

### ❌ Leaderboard Rankings Wrong

**Symptoms:** Users with more points ranked lower

**Solution:**
```python
# Check update_leaderboard task
from gamification.tasks import update_weekly_leaderboard

# Run manually
update_weekly_leaderboard()

# Verify ranking logic
from gamification.models import LeaderboardEntry, UserPoints

# Get all users sorted by points
users_by_points = UserPoints.objects.order_by('-total_points')

for rank, user_points in enumerate(users_by_points, 1):
    entry, created = LeaderboardEntry.objects.update_or_create(
        user=user_points.user,
        leaderboard_type='weekly',
        period_start=week_start,
        defaults={
            'score': user_points.total_points,
            'rank': rank  # 1st place = rank 1
        }
    )
    print(f"Rank {rank}: {entry.user.username} ({entry.score} points)")

# Check database ordering
entries = LeaderboardEntry.objects.filter(
    leaderboard_type='weekly'
).order_by('rank')  # Lower rank number = higher position

for entry in entries[:10]:
    print(f"{entry.rank}. {entry.user.username}: {entry.score}")
```

---

## Payment Issues

### ❌ Checkout Session Creation Fails

**Symptoms:**
```python
stripe.error.InvalidRequestError: No such price
```

**Solution:**
```python
# 1. Create prices in Stripe Dashboard first
# Products → Add Product → Add Price
# Copy Price ID (starts with price_)

# 2. Update PRICE_IDS in StripeService
PRICE_IDS = {
    'pro': 'price_1234567890',  # From Stripe Dashboard
    'premium': 'price_0987654321',
}

# 3. Test price exists
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

try:
    price = stripe.Price.retrieve('price_xxx')
    print(f"✓ Price exists: {price.unit_amount/100} {price.currency}")
except stripe.error.InvalidRequestError:
    print("✗ Price not found - create in Stripe Dashboard")

# 4. Alternative: Create prices programmatically
price = stripe.Price.create(
    product='prod_xxx',  # Product ID
    unit_amount=1900,  # $19.00 in cents
    currency='usd',
    recurring={'interval': 'month'}
)
print(f"Created price: {price.id}")
```

---

##Referral Issues

### ❌ Referral Code Not Working

**Symptoms:** New user signs up with code but referral not recorded

**Solution:**
```python
# 1. Check code exists
code = request.POST.get('referral_code')
try:
    ref_code = ReferralCode.objects.get(code=code)
    print(f"✓ Code {code} belongs to {ref_code.user.username}")
except ReferralCode.DoesNotExist:
    print(f"✗ Code {code} not found")

# 2. Generate code if missing
import string
import random

def generate_referral_code(user):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    ref_code, created = ReferralCode.objects.get_or_create(
        user=user,
        defaults={'code': code}
    )
    
    return ref_code.code

# 3. Process referral on signup
def register_user(username, email, password, referral_code=None):
    user = User.objects.create_user(username, email, password)
    
    if referral_code:
        try:
            ref = ReferralCode.objects.get(code=referral_code)
            Referral.objects.create(
                referrer=ref.user,
                referred_user=user
            )
            
            # Award points
            PointsService.award_points(ref.user, 'referral_success', 100)
            PointsService.award_points(user, 'signup_via_referral', 50)
            
        except ReferralCode.DoesNotExist:
            pass  # Invalid code, ignore
    
    return user
```

---

## Complete System Test

```python
def test_complete_day_05_system():
    """Test entire gamification and billing flow."""
    
    print("Testing Day 05 Complete System...")
    
    # 1. Create user
    user = User.objects.create_user('testuser', 'test@example.com', 'password')
    print("✓ User created")
    
    # 2. Award points for actions
    PointsService.award_points(user, 'lesson_complete')
    points = UserPoints.objects.get(user=user)
    assert points.total_points == 50
    print(f"✓ Points awarded: {points.total_points}")
    
    # 3. Check achievement unlock
    # (Assuming "First Lesson" achievement exists)
    ach = UserAchievement.objects.filter(user=user, unlocked=True).first()
    if ach:
        print(f"✓ Achievement unlocked: {ach.achievement.name}")
    
    # 4. Create subscription
    sub = Subscription.objects.create(user=user, tier='free')
    print(f"✓ Subscription created: {sub.tier}")
    
    # 5. Test feature gate
    can_access = sub.can_access_feature('assessment')
    print(f"✓ Can access assessment: {can_access}")
    
    # 6. Upgrade to Pro (simulate Stripe checkout)
    sub.tier = 'pro'
    sub.status = 'active'
    sub.save()
    print("✓ Upgraded to Pro")
    
    # 7. Generate referral code
    ref_code = ReferralCode.objects.create(user=user, code='TEST1234')
    print(f"✓ Referral code generated: {ref_code.code}")
    
    # 8. Update leaderboard
    LeaderboardEntry.objects.create(
        user=user,
        leaderboard_type='weekly',
        score=points.total_points,
        rank=1
    )
    print("✓ Leaderboard entry created")
    
    print("\n✅ Complete Day 05 system test PASSED!")

# Run test
test_complete_day_05_system()
```

---

**All troubleshooting covered!** Ready for production! 🚀
