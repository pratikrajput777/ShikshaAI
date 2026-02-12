# Day 07: AI Prompts - WebSockets & Business Logic

Ready-to-use prompts for implementing real-time features and business services.

---

## WebSocket Implementation

### Prompt 1.1: Interview WebSocket Consumer

```
Create interview/consumers.py with AsyncJsonWebsocketConsumer:

Methods:
- connect(): Accept connection, join room group, send welcome + first question
- disconnect(): Leave room group
- receive_json(content): Handle 'user_answer', 'request_next', 'end_interview'
- send_first_question(): Generate with InterviewService, create TTS, save turn
- send_next_question(): Get history, generate follow-up, send
- handle_user_answer(content): Save transcript, acknowledge, get next question
- end_interview(): Update status='completed', queue evaluation task

Database helpers:
- get_session(), save_turn(), get_conversation_history() with @database_sync_to_async

Use Django Channels, log all events, handle errors gracefully.
```

---

### Prompt 1.2: Learning Progress WebSocket

```
Create learning/consumers.py with StudyPlanProgressConsumer:

Handle real-time study plan generation progress updates.

Methods:
- connect(): Join user-specific room group
- disconnect(): Leave group
- study_plan_update(event): Send progress to client

Message format:
{
  'type': 'study_plan_update',
  'status': 'generating'|'ready'|'error',
  'progress': 0-100,
  'message': 'Human-readable update'
}

Integrate with learning/tasks.py to send updates during generation.
```

---

## Gamification Services

### Prompt 2.1: Points Service

```
Create gamification/services.py with PointsService class:

POINT_VALUES = {
    'lesson_complete': 50,
    'quiz_pass': 30,
    'interview_complete': 100,
    'daily_login': 10,
    'streak_7day': 200
}

Methods:
- award_points(user, action_type, amount=None): Award points, calculate level
  Level formula: floor(sqrt(total_points / 100))
- check_achievements(user): Check unlock criteria, award bonus points
- update_leaderboard_entry(user, type='weekly'): Update ranking

Use @transaction.atomic for consistency.
Include logging for all point awards.
```

---

### Prompt 2.2: Auto-Award Signals

```
Create gamification/signals.py with Django signals:

@receiver(post_save, sender=Lesson)
def lesson_completed_points(sender, instance, **kwargs):
    if instance.status == 'completed':
        PointsService.award_points(instance.module.study_plan.user, 'lesson_complete')

@receiver(post_save, sender=CFUAttempt)
def quiz_passed_points(sender, instance, created, **kwargs):
    if created and instance.passed:
        PointsService.award_points(instance.user, 'quiz_pass')

@receiver(post_save, sender=ConversationSession)
def interview_completed_points(sender, instance, **kwargs):
    if instance.status == 'evaluated':
        PointsService.award_points(instance.user, 'interview_complete')

Register signals in apps.py ready() method.
```

---

## Stripe Integration

### Prompt 3.1: Stripe Service

```
Create billing/stripe_service.py with StripeService:

PRICE_IDS = {
    'pro': settings.STRIPE_PRICE_ID_PRO,
    'premium': settings.STRIPE_PRICE_ID_PREMIUM
}

Methods:
- create_checkout_session(user, tier): Create Stripe checkout, return session.url
- _get_or_create_customer(user): Get or create Stripe customer
- handle_webhook(payload, sig_header): Process webhook events
- _handle_checkout_complete(session): Create/update subscription
- _handle_subscription_updated(subscription): Update tier/status
- _handle_subscription_deleted(subscription): Cancel subscription

Use stripe.api_key from settings, validate webhook signatures.
Handle events: checkout.session.completed, customer.subscription.*
```

---

### Prompt 3.2: Webhook View

```
Create billing/views.py with stripe_webhook view:

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    
    try:
        StripeService.handle_webhook(payload, sig_header)
        return HttpResponse(status=200)
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

Add to billing/urls.py:
path('webhook/', stripe_webhook, name='stripe_webhook')
```

---

## Feature Gating

### Prompt 4.1: Subscription Service

```
Create subscriptions/services.py with FeatureGateService:

Methods:
- can_access_feature(user, feature_name): Check if user can use feature
  Logic:
  1. Get user's subscription tier
  2. Get feature gate limits
  3. Get current usage for period
  4. Compare: usage < limit (or limit == -1 for unlimited)

- record_usage(user, feature_name): Increment usage counter
  Create FeatureUsage with period (monthly or per-billing-cycle)

- reset_monthly_limits(): Celery beat task to clear old usage records
  Run on 1st of month at midnight

Use timezone-aware dates for period tracking.
```

---

## Referral System

### Prompt 5.1: Referral Service

```
Create referrals/services.py with ReferralService:

Methods:
- generate_code(user): Create unique 8-character code
  Use: random.choices(string.ascii_uppercase + string.digits, k=8)
  Ensure uniqueness with get_or_create

- process_referral(referral_code, new_user): 
  1. Find ReferralCode
  2. Create Referral record
  3. Award points: referrer gets 100, new user gets 50
  4. Increment uses count

- get_referral_stats(user):
  Return: total_referrals, active_referrals, points_earned

Include validation: user can't refer themselves
```

---

## Testing Prompts

### Test WebSocket

```
Help me test WebSocket consumers:

1. Use channels.testing.WebsocketCommunicator:
   communicator = WebsocketCommunicator(
       InterviewConsumer.as_asgi(),
       '/ws/interview/1/'
   )
   connected, _ = await communicator.connect()
   assert connected

2. Test message flow:
   - Receive welcome message
   - Receive first question
   - Send user_answer
   - Receive next question
   - Send end_interview
   - Receive interview_ended

3. Verify database updates:
   - Turns created
   - Session status updated

Show pytest async test implementation.
```

---

### Test Gamification

```
Create test for automatic point awards:

1. Trigger action (complete lesson)
2. Check UserPoints increased
3. Verify signal fired
4. Check achievement unlocked if criteria met
5. Verify leaderboard updated

Use Django signals testing:
from django.test import override_settings

@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_lesson_points():
    lesson.status = 'completed'
    lesson.save()
    
    points = UserPoints.objects.get(user=lesson.user)
    assert points.total_points >= 50

Show complete test case.
```

---

### Test Stripe Integration

```
Test Stripe without hitting live API:

1. Mock stripe.checkout.Session.create:
   from unittest.mock import patch, MagicMock
   
   @patch('stripe.checkout.Session.create')
   def test_checkout(mock_create):
       mock_create.return_value = MagicMock(url='http://checkout.com')
       url = StripeService.create_checkout_session(user, 'pro')
       assert 'checkout' in url

2. Test webhook with test events:
   from stripe import Webhook
   
   # Create test event
   event = {...}  # Stripe test event JSON
   
   StripeService.handle_webhook(json.dumps(event), 'test_sig')

Show complete mocking setup.
```

---

## Integration Prompts

### Complete Flow Test

```
Create end-to-end test for Day 07 features:

1. User completes lesson → Points awarded automatically
2. Points unlock achievement → Bonus points given
3. User upgrades via Stripe → Subscription created
4. User starts interview → WebSocket connects
5. Interview completes → Evaluation triggers
6. Points awarded for interview → Leaderboard updated

Test all integrations between services.
Verify no race conditions.
Check database consistency.

Show pytest test suite structure.
```

---

## Deployment Prompts

### WebSocket Deployment

```
Configure production WebSocket deployment:

1. Update ASGI application in asgi.py
2. Configure Daphne in docker-compose:
   daphne:
     command: daphne -b 0.0.0.0 -p 8001 jobreadiness.asgi:application
     
3. Configure Nginx for WebSocket:
   location /ws/ {
       proxy_pass http://daphne:8001;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
   }

4. Test WebSocket connection:
   wscat -c ws://domain.com/ws/interview/1/

Show complete config files.
```

---

**Use these prompts to complete Day 07 efficiently!** 🚀
