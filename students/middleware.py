import time
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse


class SessionTimeoutMiddleware:
    IDLE_TIMEOUT    = getattr(settings, 'SESSION_IDLE_TIMEOUT', 30 * 60)
    WARNING_BEFORE  = getattr(settings, 'SESSION_IDLE_WARNING_BEFORE', 2 * 60)
    EXEMPT_PREFIXES = ('/login/', '/logout/', '/static/', '/media/')

    # Roles that should NOT see the session countdown timer in the top bar.
    ADMIN_ROLES = {1}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            request.is_college_admin = False
            request.user_college = None
            return self.get_response(request)

        path = request.path_info
        if any(path.startswith(p) for p in self.EXEMPT_PREFIXES):
            request.is_college_admin = False
            request.user_college = None
            return self.get_response(request)

        now = time.time()
        last_activity = request.session.get('_last_activity')

        # Cache role + college in session to avoid DB hit on every request
        if '_user_role' not in request.session or '_user_college_id' not in request.session:
            try:
                from students.models import UserRole
                role_obj = UserRole.objects.select_related('college').only(
                    'role', 'college_id'
                ).get(user_id=request.user.pk)
                request.session['_user_role'] = role_obj.role
                request.session['_user_college_id'] = role_obj.college_id
            except Exception:
                request.session['_user_role'] = None
                request.session['_user_college_id'] = None

        user_role = request.session.get('_user_role')
        college_id = request.session.get('_user_college_id')

        # Attach college_id to request for use in views and the college-scope guard
        request.user_college_id = college_id
        request.is_college_admin = request.user.is_superuser or (user_role in self.ADMIN_ROLES)

        if last_activity is not None:
            idle_seconds = now - last_activity
            if idle_seconds > self.IDLE_TIMEOUT:
                logout(request)
                request.session.pop('_user_role', None)
                request.session.pop('_user_college_id', None)
                login_url = reverse('login')
                return redirect(f'{login_url}?timeout=1')
            request.session_seconds_left = max(0, int(self.IDLE_TIMEOUT - idle_seconds))
        else:
            request.session_seconds_left = self.IDLE_TIMEOUT

        request.session['_last_activity'] = now
        request.session.modified = True
        request.session_idle_timeout  = self.IDLE_TIMEOUT
        request.session_warning_before = self.WARNING_BEFORE

        return self.get_response(request)


class CollegeScopeMiddleware:
    """
    Detects cross-college data access attempts.
    Logs a warning if a view returns data belonging to a different college
    than the requesting user's college. Does NOT block (views handle that),
    but provides a safety net for audit and debugging.

    In DEBUG mode it raises an exception so developers catch scoping bugs immediately.
    """
    EXEMPT_PREFIXES = ('/static/', '/media/', '/admin/', '/superadmin1/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Before each view: if a college-scoped user is accessing a URL that
        contains a college PK or department PK, verify it belongs to their college.
        This is a belt-and-suspenders check — views should already scope correctly.
        """
        if not request.user.is_authenticated or request.user.is_superuser:
            return None

        path = request.path_info
        if any(path.startswith(p) for p in self.EXEMPT_PREFIXES):
            return None

        # Nothing to check if user has no college
        college_id = getattr(request, 'user_college_id', None)
        if not college_id:
            return None

        # Belt-and-suspenders: check if URL kwargs contain a college or department PK
        # that doesn't belong to this user's college.
        from django.core.exceptions import PermissionDenied
        from students.models import Department, College

        dept_pk = view_kwargs.get('dept_id') or view_kwargs.get('department_id')
        if dept_pk:
            try:
                dept = Department.objects.only('college_id').get(pk=dept_pk)
                if dept.college_id != college_id:
                    raise PermissionDenied('Cross-college access denied.')
            except Department.DoesNotExist:
                pass

        college_pk = view_kwargs.get('college_id')
        if college_pk and int(college_pk) != college_id:
            raise PermissionDenied('Cross-college access denied.')

        return None
