from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from functools import wraps

from django.shortcuts import render

def role_required(allowed_roles):
    """
    Decorator for views that checks if the user has one of the allowed roles.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            # If unauthorized, show the styled 403 page
            return render(request, 'core/403.html', status=403)
        return _wrapped_view
    return decorator

def tenant_context_required(view_func):
    """
    Ensures that the user has a tenant and branch assigned (except for superusers or specific roles).
    Crucial for multi-tenant isolation in operational views.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if not request.user.tenant:
            return render(request, 'core/403.html', {'error': 'No Tenant assigned to user.'}, status=403)

        return view_func(request, *args, **kwargs)
    return _wrapped_view
