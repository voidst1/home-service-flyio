import re
from django.core.exceptions import ValidationError


def does_profile_exist(user):
    return hasattr(user, 'customer_profile')
