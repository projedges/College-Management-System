from .models import UserRole, CollegeBranding


def college_branding(request):
    """
    Injects `college` and `branding` into every template context
    for authenticated non-superuser users.
    """
    if not request.user.is_authenticated or request.user.is_superuser:
        return {}

    try:
        role = UserRole.objects.select_related('college').get(user=request.user)
        college = role.college
    except UserRole.DoesNotExist:
        return {}

    if not college:
        return {'college': None, 'branding': None}

    branding, _ = CollegeBranding.objects.get_or_create(college=college)
    return {'college': college, 'branding': branding}
