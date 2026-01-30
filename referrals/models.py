from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class ReferralCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=20, unique=True)
    uses = models.IntegerField(default=0)

    def __str__(self):
        return self.code


class Referral(models.Model):
    referrer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="referrals_made"
    )
    referred_user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="referred_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reward_given = models.BooleanField(default=False)

