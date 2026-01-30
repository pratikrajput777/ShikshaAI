from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from billing.stripe_service import StripeService


@csrf_exempt
def stripe_webhook(request):

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        StripeService.handle_webhook(payload, sig_header)
        return HttpResponse(status=200)
    except Exception:
        return HttpResponse(status=400)
