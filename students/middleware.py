import time
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse


class SessionTimeoutMiddleware:
    """
    Enforces an idle session timeout.

    - Tracks the timestamp of the last request in the session.
    - If the user has been idle for longer than SESSION_IDLE_TIMEOUT seconds,
      they are logged out and redirected to the login page with a message.
    - The absolute session lifetime (SESSION_COOKIE_AGE) is handled by Django
      itself via the session backend.
    - Passes two values to every request so templates can drive the warning modal:
        request.session_idle_timeout   — total idle seconds allowed
        request.session_seconds_left   — seconds remaining before forced logout
    """

    IDLE_TIMEOUT = getattr(settings, 'SESSION_IDLE_TIMEOUT', 30 * 60)
    WARNING_BEFORE = getattr(settings, 'SESSION_IDLE_WARNING_BEFORE', 2 * 60)

    # Paths that should never trigger a timeout redirect (login, logout, static).
    EXEMPT_PREFIXES = ('/login/', '/logout/', '/static/', '/media/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip unauthenticated users and exempt paths.
        if not request.user.is_authenticated:
            return self.get_response(request)

        path = request.path_info
        if any(path.startswith(p) for p in self.EXEMPT_PREFIXES):
            return self.get_response(request)

        now = time.time()
        last_activity = request.session.get('_last_activity')

        if last_activity is not None:
            idle_seconds = now - last_activity
            if idle_seconds > self.IDLE_TIMEOUT:
                # Idle timeout exceeded — log the user out.
                logout(request)
                login_url = reverse('login')
                return redirect(f'{login_url}?timeout=1')

            # Attach remaining seconds so the template can show a countdown.
            request.session_seconds_left = max(0, int(self.IDLE_TIMEOUT - idle_seconds))
        else:
            request.session_seconds_left = self.IDLE_TIMEOUT

        # Refresh the last-activity timestamp on every request.
        request.session['_last_activity'] = now
        request.session.modified = True

        # Expose config to templates.
        request.session_idle_timeout = self.IDLE_TIMEOUT
        request.session_warning_before = self.WARNING_BEFORE

        return self.get_response(request)
