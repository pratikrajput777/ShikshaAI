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