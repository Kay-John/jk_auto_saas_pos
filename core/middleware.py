from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            tenant = request.user.tenant
            # Only block if tenant exists (it should for all operational users)
            if tenant:
                # Paths that require active subscription
                protected_prefixes = ['/pos/', '/inventory/']
                is_protected = any(request.path.startswith(prefix) for prefix in protected_prefixes)

                # Check if trial has ended
                trial_ended = tenant.trial_end_date and tenant.trial_end_date < timezone.now()
                not_active = tenant.subscription_status != 'active'

                if is_protected and trial_ended and not_active:
                    # Redirect to billing
                    # But allow Tenant Admin to see the billing page
                    if request.path != reverse('billing_page'):
                        return redirect('billing_page')

        response = self.get_response(request)
        return response
