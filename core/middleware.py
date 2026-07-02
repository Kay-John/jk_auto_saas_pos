from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # 1. Operational Guard
        # Using a tuple instead of list might be slightly faster
        premium_prefixes = ('/pos/', '/inventory/')
        is_premium = any(path.startswith(prefix) for prefix in premium_prefixes)

        if is_premium:
            if not request.user.is_authenticated:
                return redirect('login')

            tenant = getattr(request.user, 'tenant', None)
            if tenant:
                trial_ended = tenant.trial_end_date and tenant.trial_end_date < timezone.now()
                not_active = tenant.subscription_status != 'active'

                if trial_ended and not_active:
                    return redirect('billing_page')

        # 2. Billing Guard
        billing_url = reverse('billing_page')
        if path == billing_url:
            if not request.user.is_authenticated:
                return redirect('login')

            tenant = getattr(request.user, 'tenant', None)
            # If account is active, redirect away from billing to POS
            if tenant and tenant.subscription_status == 'active':
                return redirect('pos_screen')

        response = self.get_response(request)
        return response
