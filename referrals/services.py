from django.db import transaction

from referrals.models import ReferralCode, Referral
from gamification.services import PointsService


@transaction.atomic
def process_referral(referral_code, new_user):

    ref_code = ReferralCode.objects.select_for_update().get(
        code=referral_code
    )

    Referral.objects.create(
        referrer=ref_code.user,
        referred_user=new_user
    )

    ref_code.uses += 1
    ref_code.save()

    # points (Phase-2 gamification)
    PointsService.award_points(ref_code.user, "referral_made")
    PointsService.award_points(new_user, "referred_signup")
