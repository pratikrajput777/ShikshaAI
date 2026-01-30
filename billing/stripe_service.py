import stripe

from django.conf import settings
from django.contrib.auth import get_user_model

from subscriptions.models import Subscription

User = get_user_model()

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:

    PRICE_IDS = {
        'pro': settings.STRIPE_PRO_PRICE_ID,
        'premium': settings.STRIPE_PREMIUM_PRICE_ID,
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
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            StripeService._handle_checkout_complete(session)

        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            StripeService._handle_subscription_updated(subscription)

    # ----------------------------
    # helpers
    # ----------------------------
    @staticmethod
    def _get_or_create_customer(user):

        sub = Subscription.objects.filter(user=user).first()

        if sub and sub.stripe_customer_id:
            return sub.stripe_customer_id

        customer = stripe.Customer.create(
            email=user.email
        )

        Subscription.objects.update_or_create(
            user=user,
            defaults={
                "stripe_customer_id": customer.id
            }
        )

        return customer.id

    @staticmethod
    def _get_tier_from_price_id(price_id):

        for tier, pid in StripeService.PRICE_IDS.items():
            if pid == price_id:
                return tier

        return "free"

    # ----------------------------
    # webhook handlers
    # ----------------------------
    @staticmethod
    def _handle_checkout_complete(session):

        customer_id = session['customer']
        subscription_id = session['subscription']

        email = session.get('customer_details', {}).get('email')

        if not email:
            return

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return

        stripe_sub = stripe.Subscription.retrieve(subscription_id)

        price_id = stripe_sub['items']['data'][0]['price']['id']

        tier = StripeService._get_tier_from_price_id(price_id)

        Subscription.objects.update_or_create(
            user=user,
            defaults={
                'stripe_customer_id': customer_id,
                'stripe_subscription_id': subscription_id,
                'tier': tier,
                'status': stripe_sub['status'],
            }
        )

    @staticmethod
    def _handle_subscription_updated(subscription):

        stripe_sub_id = subscription['id']

        sub = Subscription.objects.filter(
            stripe_subscription_id=stripe_sub_id
        ).first()

        if not sub:
            return

        price_id = subscription['items']['data'][0]['price']['id']

        tier = StripeService._get_tier_from_price_id(price_id)

        sub.tier = tier
        sub.status = subscription['status']
        sub.save()
