from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Subscription(models.Model):

    TIERS = [
        ('free', 'Free'),
        ('pro', 'Pro - $19/month'),
        ('premium', 'Premium - $49/month'),
        ('enterprise', 'Enterprise - Custom'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    tier = models.CharField(
        max_length=20,
        choices=TIERS,
        default='free'
    )

    status = models.CharField(max_length=20)   # active, canceled, past_due

    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)

    current_period_end = models.DateTimeField(null=True, blank=True)

    def can_access_feature(self, feature_name):

        gate = FeatureGate.objects.get(feature_name=feature_name)

        usage = FeatureUsage.get_current_usage(
            self.user,
            feature_name
        )

        limit = getattr(gate, f"{self.tier}_limit")

        if limit == -1:
            return True

        return usage < limit


class FeatureGate(models.Model):

    feature_name = models.CharField(max_length=100, unique=True)

    free_limit = models.IntegerField()
    pro_limit = models.IntegerField()
    premium_limit = models.IntegerField(default=-1)
    enterprise_limit = models.IntegerField(default=-1)


class FeatureUsage(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feature_name = models.CharField(max_length=100)

    usage_count = models.IntegerField(default=0)

    period_start = models.DateTimeField()
    period_end = models.DateTimeField()

    @staticmethod
    def get_current_usage(user, feature_name):

        now = timezone.now()

        obj = FeatureUsage.objects.filter(
            user=user,
            feature_name=feature_name,
            period_start__lte=now,
            period_end__gte=now
        ).first()

        if not obj:
            return 0

        return obj.usage_count


from django.contrib import admin
from .models import Subscription, FeatureGate, FeatureUsage

admin.site.register(Subscription)
admin.site.register(FeatureGate)
admin.site.register(FeatureUsage)
