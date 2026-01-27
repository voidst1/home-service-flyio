# decorators.py
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .utils import does_profile_exist


def onboarding_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not does_profile_exist(request.user):
            messages.info(request, "Please complete your onboarding first.")
            return redirect('profile')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
