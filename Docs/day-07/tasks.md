# Day 07: Complete Tasks - WebSockets & Business Logic

## Phase 1: Interview WebSocket Consumer (2h)

### Create `interview/consumers.py`:

```python
"""
Real-time WebSocket consumer for mock interviews.
Handles bidirectional communication during interview sessions.
"""

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ConversationSession, InterviewTurn
import logging

logger = logging.getLogger(__name__)

class InterviewConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time mock interviews."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'interview_{self.session_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Interview WebSocket connected: session {self.session_id}")
        
        # Send welcome and first question
        await self.send_welcome_message()
        await self.send_first_question()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"Interview WebSocket disconnected: session {self.session_id}")
    
    async def receive_json(self, content):
        """
        Handle incoming WebSocket messages.
        
        Message types:
        - user_answer: Candidate's answer (from speech-to-text)
        - request_next: Request next question
        - end_interview: End session early
        """
        message_type = content.get('type')
        
        if message_type == 'user_answer':
            await self.handle_user_answer(content)
        elif message_type == 'request_next':
            await self.send_next_question()
        elif message_type == 'end_interview':
            await self.end_interview()
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def send_welcome_message(self):
        """Send welcome message to candidate."""
        await self.send_json({
            'type': 'welcome',
            'message': 'Welcome to your mock interview. Take a deep breath and relax!'
        })
    
    async def send_first_question(self):
        """Generate and send opening question."""
        from interview.services import Interview Service
        service = InterviewService()
        
        session = await self.get_session()
        question = await database_sync_to_async(service.generate_first_question)(session)
        
        # Generate TTS audio
        audio_url = await database_sync_to_async(service.generate_tts_audio)(question)
        
        # Save turn
        await self.save_turn('interviewer', question, audio_url)
        
        # Send to client
        await self.send_json({
            'type': 'question',
            'question': question,
            'audio_url': audio_url,
            'question_number': 1
        })
    
    async def send_next_question(self):
        """Generate and send follow-up question."""
        from interview.services import InterviewService
        service = InterviewService()
        
        session = await self.get_session()
        
        # Check if interview complete
        if session.current_question_number >= session.target_question_count:
            await self.end_interview()
            return
        
        # Get conversation history
        history = await self.get_conversation_history()
        
        # Generate question
        question = await database_sync_to_async(service.generate_follow_up_question)(
            session, history
        )
        
        # Generate audio
        audio_url = await database_sync_to_async(service.generate_tts_audio)(question)
        
        # Save turn
        await self.save_turn('interviewer', question, audio_url)
        
        # Send
        await self.send_json({
            'type': 'question',
            'question': question,
            'audio_url': audio_url,
            'question_number': session.current_question_number + 1
        })
    
    async def handle_user_answer(self, content):
        """
        Process candidate's answer.
        
        Args:
            content: dict with 'transcript' key
        """
        transcript = content.get('transcript', '')
        
        # Save answer turn
        await self.save_turn('candidate', transcript)
        
        # Send acknowledgment
        await self.send_json({
            'type': 'answer_received',
            'message': 'Got it! Thinking...'
        })
        
        # Send next question
        await self.send_next_question()
    
    async def end_interview(self):
        """End interview and trigger evaluation."""
        from interview.tasks import evaluate_interview_task
        
        session = await self.get_session()
        await database_sync_to_async(self._update_session_status)(session, 'completed')
        
        # Queue evaluation
        await database_sync_to_async(evaluate_interview_task.delay)(self.session_id)
        
        await self.send_json({
            'type': 'interview_ended',
            'message': 'Interview complete! Generating your evaluation...'
        })
    
    # Database helpers
    @database_sync_to_async
    def get_session(self):
        return ConversationSession.objects.get(id=self.session_id)
    
    @database_sync_to_async
    def save_turn(self, speaker, text, audio_url=''):
        session = ConversationSession.objects.get(id=self.session_id)
        turn_number = session.turns.count() + 1
        
        InterviewTurn.objects.create(
            session=session,
            turn_number=turn_number,
            speaker=speaker,
            text_content=text,
            audio_url=audio_url
        )
        
        if speaker == 'interviewer':
            session.current_question_number += 1
            session.save()
    
    @database_sync_to_async
    def get_conversation_history(self):
        session = ConversationSession.objects.get(id=self.session_id)
        return list(session.turns.order_by('turn_number'))
    
    @staticmethod
    def _update_session_status(session, status):
        session.status = status
        session.save()
```

### Create `interview/routing.py`:

```python
"""WebSocket URL routing for interviews."""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/interview/(?P<session_id>\d+)/$', consumers.InterviewConsumer.as_asgi()),
]
```

### Update `jobreadiness/routing.py`:

```python
"""Main WebSocket routing."""

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import interview.routing
import learning.routing
import users.routing

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            interview.routing.websocket_urlpatterns +
            learning.routing.websocket_urlpatterns +
            users.routing.websocket_urlpatterns
        )
    ),
})
```

---

## Phase 2: Gamification Services (2h)

### Create `gamification/services.py`:

```python
"""
Gamification service for points, levels, and achievements.
"""

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
```

### Create `gamification/signals.py`:

```python
"""
Django signals to automatically award points on actions.
"""

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
```

---

## Phase 3: Stripe Service (2h)

### Create `billing/stripe_service.py`:

```python
"""
Stripe payment integration service.
"""

import stripe
from django.conf import settings
from subscriptions.models import Subscription
import logging

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    """Service for Stripe payment processing."""
    
    # Price IDs from Stripe Dashboard
    PRICE_IDS = {
        'pro': settings.STRIPE_PRICE_ID_PRO,
        'premium': settings.STRIPE_PRICE_ID_PREMIUM,
    }
    
    @classmethod
    def create_checkout_session(cls, user, tier: str):
        """
        Create Stripe checkout session for subscription.
        
        Args:
            user: User object
            tier: 'pro' or 'premium'
        
        Returns:
            Checkout session URL
        """
        customer_id = cls._get_or_create_customer(user)
        
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': cls.PRICE_IDS[tier],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{settings.SITE_URL}/billing/success/",
            cancel_url=f"{settings.SITE_URL}/billing/cancel/",
            client_reference_id=str(user.id)
        )
        
        logger.info(f"Created checkout session for {user}: {session.id}")
        return session.url
    
    @classmethod
    def _get_or_create_customer(cls, user):
        """Get or create Stripe customer for user."""
        # Check if user has customer ID
        try:
            subscription = Subscription.objects.get(user=user)
            if subscription.stripe_customer_id:
                return subscription.stripe_customer_id
        except Subscription.DoesNotExist:
            pass
        
        # Create new customer
        customer = stripe.Customer.create(
            email=user.email,
            name=user.get_full_name(),
            metadata={'user_id': user.id}
        )
        
        # Save customer ID
        Subscription.objects.update_or_create(
            user=user,
            defaults={'stripe_customer_id': customer.id}
        )
        
        logger.info(f"Created Stripe customer for {user}: {customer.id}")
        return customer.id
    
    @classmethod
    def handle_webhook(cls, payload, sig_header):
        """
        Handle Stripe webhook events.
        
        Events:
        - checkout.session.completed
        - customer.subscription.updated
        - customer.subscription.deleted
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            logger.error("Invalid webhook payload")
            raise
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            raise
        
        # Handle event
        if event.type == 'checkout.session.completed':
            cls._handle_checkout_complete(event.data.object)
        
        elif event.type == 'customer.subscription.updated':
            cls._handle_subscription_updated(event.data.object)
        
        elif event.type == 'customer.subscription.deleted':
            cls._handle_subscription_deleted(event.data.object)
        
        logger.info(f"Handled webhook event: {event.type}")
    
    @classmethod
    def _handle_checkout_complete(cls, session):
        """Handle successful checkout."""
        from users.models import User
        
        user_id = session.client_reference_id
        customer_id = session.customer
        subscription_id = session.subscription
        
        # Determine tier from price
        price_id = session['line_items']['data'][0]['price']['id']
        tier = 'pro' if price_id == cls.PRICE_IDS['pro'] else 'premium'
        
        # Update subscription
        user = User.objects.get(id=user_id)
        Subscription.objects.update_or_create(
            user=user,
            defaults={
                'tier': tier,
                'status': 'active',
                'stripe_customer_id': customer_id,
                'stripe_subscription_id': subscription_id
            }
        )
        
        logger.info(f"Subscription activated: {user} → {tier}")
```

---

## Checklist

### Day 07 Completion
- [ ] interview/consumers.py with real-time WebSocket
- [ ] interview/routing.py for WebSocket URLs
- [ ] gamification/services.py with PointsService
- [ ] gamification/signals.py auto-awarding points
- [ ] billing/stripe_service.py for payments
- [ ] subscriptions/services.py for feature gates
- [ ] All services tested and functional

### Integration Testing
- [ ] Real-time interview works end-to-end
- [ ] Points awarded automatically
- [ ] Stripe checkout creates subscription
- [ ] Feature gates enforce correctly
- [ ] All gaps from FEATURE-GAP-ANALYSIS.md closed

**Time: 8 hours | Result: 100% Complete Platform** 🎉
