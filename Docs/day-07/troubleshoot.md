# Day 07: Troubleshooting Guide - WebSockets & Business Logic

Solutions for WebSocket, gamification, and payment integration issues.

---

## WebSocket Issues

### ❌ Problem: WebSocket Connection Refused

**Symptoms:**
```
WebSocket connection to 'ws://localhost:8000/ws/interview/1/' failed
```

**Solution:**
```bash
# 1. Ensure Daphne is running (not Django dev server)
# Stop Django server:
pkill -f "manage.py runserver"

# Start Daphne:
daphne -b 0.0.0.0 -p 8000 jobreadiness.asgi:application

# Or use docker-compose:
docker-compose up -d daphne

# 2. Check ASGI configuration
# jobreadiness/asgi.py must have ProtocolTypeRouter

# 3. Verify routing includes interview
# jobreadiness/routing.py should import interview.routing

# 4. Check Redis is running
redis-cli ping  # Should return PONG

# 5. Test with wscat:
npm install -g wscat
wscat -c ws://localhost:8000/ws/interview/1/
```

---

### ❌ Problem: Consumer Not Found

**Symptoms:**
```
ValueError: No route found for path 'ws/interview/1/'
```

**Solution:**
```python
# Check interview/routing.py exists:
# interview/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/interview/(?P<session_id>\d+)/$', 
            consumers.InterviewConsumer.as_asgi()),
]

# Verify imported in main routing:
# jobreadiness/routing.py
from channels.routing import ProtocolTypeRouter, URLRouter
import interview.routing
import learning.routing

application = Protocol TypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            interview.routing.websocket_urlpatterns +
            learning.routing.websocket_urlpatterns
        )
    ),
})

# Check URL pattern matches:
r'ws/interview/(?P<session_id>\d+)/$'
# Should match: ws/interview/123/
```

---

### ❌ Problem: Database Queries in Async Context

**Symptoms:**
```
SynchronousOnlyOperation: You cannot call this from an async context
```

**Solution:**
```python
# Use database_sync_to_async wrapper:
from channels.db import database_sync_to_async

# Wrong:
async def connect(self):
    session = ConversationSession.objects.get(id=self.session_id)  # Error!

# Correct:
async def connect(self):
    session = await self.get_session()

@database_sync_to_async
def get_session(self):
    return ConversationSession.objects.get(id=self.session_id)

# Or wrap inline:
session = await database_sync_to_async(
    ConversationSession.objects.get
)(id=self.session_id)
```

---

## Gamification Issues

### ❌ Problem: Points Not Awarded Automatically

**Symptoms:**
```
Lesson completed but no points added to UserPoints
```

**Solution:**
```python
# 1. Check signals are registered
# gamification/apps.py:
class GamificationConfig(AppConfig):
    name = 'gamification'
    
    def ready(self):
        import gamification.signals  # MUST import here

# 2. Verify INSTALLED_APPS order
INSTALLED_APPS = [
    ...
    'learning',  # Before gamification
    'gamification',  # Must be registered
    ...
]

# 3. Test signal manually
from gamification.signals import lesson_completed_points
from learning.models import Lesson

lesson = Lesson.objects.first()
lesson.status = 'completed'
lesson_completed_points(sender=Lesson, instance=lesson)

# Check points
from gamification.models import UserPoints
points = UserPoints.objects.get(user=lesson.module.study_plan.user)
print(f"Points: {points.total_points}")

# 4. Check signal is connected
from django.db.models.signals import post_save
print(post_save._live_receivers(Lesson))  # Should show signal
```

---

### ❌ Problem: Achievement Not Unlocking

**Symptoms:**
```
User meets criteria but achievement stays locked
```

**Solution:**
```python
# Debug unlock logic:
from gamification.services import PointsService
from gamification.models import Achievement, UserAchievement

achievement = Achievement.objects.get(name="First Lesson")
user = User.objects.first()

# Check criteria
print(f"Criteria: {achievement.unlock_criteria}")

# Manual check
if achievement.unlock_criteria['type'] == 'lessons_completed':
    from learning.models import Lesson
    count = Lesson.objects.filter(
        module__study_plan__user=user,
        status='completed'
    ).count()
    
    required = achievement.unlock_criteria['count']
    print(f"User has {count} lessons, needs {required}")
    
    if count >= required:
        user_ach = UserAchievement.objects.get(user=user, achievement=achievement)
        user_ach.unlocked = True
        user_ach.save()
        print("✓ Manually unlocked")

# Ensure check_achievements is called:
PointsService.check_achievements(user)
```

---

### ❌ Problem: Level Not Calculating

**Symptoms:**
```
User has 10000 points but level is still 0
```

**Solution:**
```python
# Check level calculation:
import math

total_points = 10000
expected_level = int(math.sqrt(total_points / 100))
print(f"Expected level: {expected_level}")  # Should be 10

# Update manually if stuck:
from gamification.models import UserPoints

user_points = UserPoints.objects.get(user=user)
user_points.level = int((user_points.total_points / 100) ** 0.5)
user_points.save()

print(f"✓ Level updated to: {user_points.level}")

# Ensure award_points updates level:
def award_points(cls, user, action_type, amount=None):
    # ...
    user_points.total_points += points_awarded
    user_points.level = int((user_points.total_points / 100) ** 0.5)  # MUST update
    user_points.save()
```

---

## Stripe Integration Issues

### ❌ Problem: Stripe API Key Invalid

**Symptoms:**
```
stripe.error.AuthenticationError: No API key provided
```

**Solution:**
```bash
# 1. Get API keys from Stripe Dashboard
# https://dashboard.stripe.com/test/apikeys

# 2. Add to .env:
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# 3. Create Price IDs in Stripe
# Products → Create Product → Add Price
STRIPE_PRICE_ID_PRO=price_xxxxx
STRIPE_PRICE_ID_PREMIUM=price_xxxxx

# 4. Test key:
python manage.py shell
>>> import stripe
>>> from django.conf import settings
>>> stripe.api_key = settings.STRIPE_SECRET_KEY
>>> stripe.Customer.list(limit=1)  # Should not error
```

---

### ❌ Problem: Webhook Signature Verification Fails

**Symptoms:**
```
stripe.error.SignatureVerificationError: No signatures found matching the expected signature
```

**Solution:**
```bash
# 1. Use Stripe CLI for local testing
stripe login
stripe listen --forward-to localhost:8000/api/billing/webhook/

# This outputs webhook secret:
# whsec_xxxxx

# 2. Update .env with this secret
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# 3. Test webhook:
stripe trigger checkout.session.completed

# 4. Check webhook view:
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    # Log for debugging
    print(f"Signature: {sig_header}")
    print(f"Secret: {settings.STRIPE_WEBHOOK_SECRET[:10]}...")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        # ...
```

---

### ❌ Problem: Checkout Session Not Creating Subscription

**Symptoms:**
```
Checkout succeeds but no subscription in database
```

**Solution:**
```python
# Check webhook event handler:
def _handle_checkout_complete(cls, session):
    print(f"Checkout session: {session}")
    
    # Debug fields:
    customer_id = session.get('customer')
    subscription_id = session.get('subscription')
    client_ref = session.get('client_reference_id')
    
    print(f"Customer: {customer_id}")
    print(f"Subscription: {subscription_id}")
    print(f"User ID: {client_ref}")
    
    if not all([customer_id, subscription_id, client_ref]):
        print("✗ Missing required fields!")
        return
    
    # Create subscription
    from users.models import User
    from subscriptions.models import Subscription
    
    user = User.objects.get(id=client_ref)
    
    Subscription.objects.update_or_create(
        user=user,
        defaults={
            'stripe_customer_id': customer_id,
            'stripe_subscription_id': subscription_id,
            'tier': 'pro',  # Determine from price_id
            'status': 'active'
        }
    )
    
    print(f"✓ Subscription created for user {user.id}")
```

---

## Feature Gate Issues

### ❌ Problem: Free User Can Access Unlimited Features

**Symptoms:**
```
Free tier user completes 10 assessments (limit is 3)
```

**Solution:**
```python
# Ensure feature gate enforcement:
from subscriptions.models import Subscription, FeatureGate, FeatureUsage

def can_access_feature(user, feature_name):
    # 1. Get subscription
    try:
        sub = Subscription.objects.get(user=user)
    except Subscription.DoesNotExist:
        # No subscription = free tier
        sub = Subscription.objects.create(user=user, tier='free')
    
    # 2. Get feature gate
    try:
        gate = FeatureGate.objects.get(feature_name=feature_name)
    except FeatureGate.DoesNotExist:
        # No gate = unlimited access
        return True
    
    # 3. Get limit for tier
    limit = getattr(gate, f'{sub.tier}_limit')
    
    if limit == -1:  # Unlimited
        return True
    
    # 4. Count current usage
    from django.utils import timezone
    from dateutil.relativedelta import relativedelta
    
    period_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)
    period_end = period_start + relativedelta(months=1)
    
    usage_count = FeatureUsage.objects.filter(
        user=user,
        feature_name=feature_name,
        period_start__gte=period_start,
        period_end__lte=period_end
    ).count()
    
    print(f"Usage: {usage_count}/{limit}")
    
    return usage_count < limit

# Add to views:
from subscriptions.services import FeatureGateService

def start_assessment(request):
    if not FeatureGateService.can_access_feature(request.user, 'assessment'):
        return JsonResponse({'error': 'Upgrade to continue'}, status=403)
    
    # Record usage
    FeatureGateService.record_usage(request.user, 'assessment')
    
    # Continue...
```

---

## Complete Integration Test

```python
# Test all Day 07 components together
from channels.testing import WebsocketCommunicator
from interview.consumers import InterviewConsumer
from gamification.services import PointsService
from billing.stripe_service import StripeService
import pytest

@pytest.mark.asyncio
async def test_complete_day_07():
    print("\nTesting Day 07 Complete Integration\n")
    
    # 1. Start interview via WebSocket
    communicator = WebsocketCommunicator(
        InterviewConsumer.as_asgi(),
        '/ws/interview/1/'
    )
    
    connected, _ = await communicator.connect()
    assert connected
    print("✓ Step 1: WebSocket connected")
    
    # 2. Receive question
    response = await communicator.receive_json_from(timeout=5)
    assert response['type'] == 'question'
    print("✓ Step 2: Question received")
    
    # 3. Close interview
    await communicator.send_json_to({'type': 'end_interview'})
    await communicator.disconnect()
    print("✓ Step 3: Interview ended")
    
    # 4. Check points awarded
    # (Would be awarded by signal when interview evaluated)
    user_points = UserPoints.objects.get(user=test_user)
    initial_points = user_points.total_points
    
    PointsService.award_points(test_user, 'interview_complete')
    user_points.refresh_from_db()
    
    assert user_points.total_points == initial_points + 100
    print("✓ Step 4: Points awarded")
    
    # 5. Test Stripe (mocked)
    from unittest.mock import patch, MagicMock
    
    with patch('stripe.checkout.Session.create') as mock:
        mock.return_value = MagicMock(url='http://test.com')
        url = StripeService.create_checkout_session(test_user, 'pro')
        assert 'test.com' in url
    
    print("✓ Step 5: Stripe checkout works")
    
    print("\n✅ Complete Day 07 Integration PASSED!")
```

---

**All issues resolved = Platform complete!** ✅🔧
