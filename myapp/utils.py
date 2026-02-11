import re
from django.core.exceptions import ValidationError

from myapp.constants import AUTH_GROUP_AFFILIATE


def does_profile_exists(user) -> bool:
    return hasattr(user, 'customer_profile')

def is_affiliate(user) -> bool:
    return is_in_group(user, AUTH_GROUP_AFFILIATE)

def is_in_group(user, group_name: str) -> bool:
    return user.groups.filter(name=group_name).exists()

def get_user_context(user):
    return {
        'profile_exists': does_profile_exists(user),
        'is_affiliate': is_affiliate(user)
    }