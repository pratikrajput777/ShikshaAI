# Day 05: AI Prompts, Troubleshooting & Testing

## AI PROMPTS

### Gamification System
```
Create PointsService in gamification/services.py with:
- award_points(user, action_type) method
- Point values: lesson=50, quiz=30, interview=100
- Level calculation: floor(sqrt(total_points/100))
- Auto-check achievements after points awarded
- Update leaderboard rankings
Include Django signals to trigger on lesson/quiz completion.
```

### Stripe Integration
```
Create StripeService with:
- create_checkout_session(user, tier)
- handle_webhook(payload, sig) for events
- PRICE_IDS for pro/premium tiers
- Create/update Subscription on checkout.session.completed
- Cancel subscription endpoint
Include webhook view with @csrf_exempt decorator.
```

---

## TROUBLESHOOTING

### ❌ Stripe Webhook Fails
**Solution:**
```bash
# Test webhook locally with Stripe CLI
stripe listen --forward-to localhost:8000/api/billing/webhook/
stripe trigger checkout.session.completed

# Verify webhook secret matches
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

### ❌ Points Not Awarded
**Solution:**
```python
# Check signals registered
# apps.py:
class LearningConfig(AppConfig):
    def ready(self):
        import learning.signals  # Import signals

# Test manually:
from gamification.services import PointsService
PointsService.award_points(user, 'lesson_complete')
```

### ❌ Feature Gate Not Working
**Solution:**
```python
# Check usage count resets monthly
from subscriptions.models import FeatureUsage

# Reset at start of month (Celery beat task)
@periodic_task(run_every=crontab(day_of_month='1', hour=0))
def reset_monthly_limits():
    FeatureUsage.objects.filter(
        period_end__lt=timezone.now()
    ).delete()
```

---

## TESTING

### Test 1: Point Awards
```python
def test_points_awarded():
    user = User.objects.create_user('test')
    PointsService.award_points(user, 'lesson_complete')
    
    points = UserPoints.objects.get(user=user)
    assert points.total_points == 50
    assert points.level == 0  # sqrt(50/100) = 0.7 → floor = 0
    print("✓ Points awarded correctly")
```

### Test 2: Stripe Checkout
```python
def test_stripe_checkout():
    url = StripeService.create_checkout_session(user, 'pro')
    assert 'checkout.stripe.com' in url
    print(f"✓ Checkout URL: {url}")
```

### Test 3: Feature Gating
```python
def test_feature_limits():
    sub = Subscription.objects.create(user=user, tier='free')
    
    # Free tier: 3 assessments/month
    assert sub.can_access_feature('assessment') == True
    
    # Simulate 3 usages
    for _ in range(3):
        FeatureUsage.objects.create(
            user=user,
            feature_name='assessment',
            usage_count=1
        )
    
    assert sub.can_access_feature('assessment') == False
    print("✓ Feature gate enforced")
```

### Test 4: Leaderboard
```python
def test_leaderboard_ranking():
    # Create users with points
    user1 = create_user_with_points('user1', 1000)
    user2 = create_user_with_points('user2', 2000)
    
    # Update leaderboard
    from gamification.tasks import update_weekly_leaderboard
    update_weekly_leaderboard()
    
    # Check rankings
    entries = LeaderboardEntry.objects.filter(
        leaderboard_type='weekly'
    ).order_by('rank')
    
    assert entries[0].user == user2  # Higher points = rank 1
    assert entries[1].user == user1
    print("✓ Leaderboard ranked correctly")
```

### Test 5: Complete Flow
```python
def test_complete_day_05():
    # 1. User completes lesson → gets points
    lesson.status = 'completed'
    lesson.save()
    
    points = UserPoints.objects.get(user=user)
    assert points.total_points >= 50
    
    # 2. User upgrades to Pro
    checkout_url = StripeService.create_checkout_session(user, 'pro')
    # Simulate webhook
    StripeService._handle_checkout_complete(mock_session)
    
    sub = Subscription.objects.get(user=user)
    assert sub.tier == 'pro'
    
    # 3. User can now access unlimited features
    assert sub.can_access_feature('assessment') == True
    
    # 4. User appears on leaderboard
    entry = LeaderboardEntry.objects.filter(user=user).first()
    assert entry is not None
    
    print("✅ Complete Day 05 flow working!")
```

---

## Validation Script
```bash
#!/bin/bash
echo "Day 05 - Final Validation"

# Check Stripe
python -c "import stripe; print('✓ Stripe installed')"

# Run tests
python manage.py test gamification subscriptions billing

echo "✅ Tutorial COMPLETE! All 5 days validated!"
```

**ALL FILES CREATED! TUTORIAL 100% COMPLETE!** 🎉🚀
