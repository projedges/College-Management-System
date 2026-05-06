from .models import UserRole, CollegeBranding
from django.core.cache import cache


def college_branding(request):
    """
    Injects `college` and `branding` into every template context.
    Cached per-user for 5 minutes to avoid 2 DB hits on every request.
    """
    if not request.user.is_authenticated or request.user.is_superuser:
        return {}

    cache_key = f'college_branding_{request.user.pk}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        role = UserRole.objects.select_related('college').get(user=request.user)
        college = role.college
    except UserRole.DoesNotExist:
        return {}

    if not college:
        return {'college': None, 'branding': None}

    branding, _ = CollegeBranding.objects.get_or_create(college=college)
    result = {'college': college, 'branding': branding}
    cache.set(cache_key, result, 300)
    return result


def impersonation_state(request):
    if not request.user.is_authenticated:
        return {
            'is_impersonating': False,
            'impersonator_name': '',
            'impersonated_target_label': '',
            'impersonated_role_label': '',
        }

    session = getattr(request, 'session', {})
    return {
        'is_impersonating': bool(session.get('_impersonator_user_id')),
        'impersonator_name': session.get('_impersonator_name', ''),
        'impersonated_target_label': session.get('_impersonated_target_label', ''),
        'impersonated_role_label': session.get('_impersonated_role_label', ''),
    }
