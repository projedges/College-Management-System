from pathlib import Path
import os
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}

# ── Security ──────────────────────────────────────────────────────────────────
# In production set SECRET_KEY as an environment variable — never commit it.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# Set DJANGO_DEBUG=False in production.
DEBUG = _env_bool('DJANGO_DEBUG', default=True)

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-dev-only-change-me'
    else:
        raise ImproperlyConfigured('DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is False.')

ALLOWED_HOSTS = os.environ.get(
    'DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1'
).split(',') + ['.ngrok-free.app', '.ngrok.io']
CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://127.0.0.1',
    'https://*.ngrok-free.app',
    'https://*.ngrok.io',
]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'students',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'students.middleware.SessionTimeoutMiddleware',
    'students.middleware.CollegeScopeMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'studentmanagementsystem.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'students.context_processors.college_branding',
            ],
        },
    },
]

WSGI_APPLICATION = 'studentmanagementsystem.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    # MySQL config — uncomment and comment out SQLite above when 192.168.7.21 is reachable
    # 'default': {
    #     'ENGINE': 'django.db.backends.mysql',
    #     'NAME': 'student_management_db',
    #     'USER': 'student',
    #     'PASSWORD': '1432',
    #     'HOST': '192.168.7.21',
    #     'PORT': '3306',
    #     'OPTIONS': {
    #         'charset': 'utf8mb4',
    #         'connect_timeout': 10,
    #         'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    #     },
    #     'CONN_MAX_AGE': 60,
    # },
    'sqlite': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
}

# ── Production database override via DATABASE_URL env var ────────────────────
# Set DATABASE_URL=mysql://USER:PASSWORD@HOST:PORT/DBNAME to override the
# default MySQL config above (useful for CI/CD or cloud deployments).
_db_url = os.environ.get('DATABASE_URL')
if _db_url:
    import urllib.parse as _up
    _u = _up.urlparse(_db_url)
    _scheme = _u.scheme.lower()
    if 'mysql' in _scheme:
        DATABASES['default'] = {
            'ENGINE': 'django.db.backends.mysql',
            'NAME':     _u.path.lstrip('/'),
            'USER':     _u.username,
            'PASSWORD': _u.password or '',
            'HOST':     _u.hostname,
            'PORT':     str(_u.port or 3306),
            'OPTIONS':  {'charset': 'utf8mb4', 'connect_timeout': 10},
            'CONN_MAX_AGE': 60,
        }
    elif 'postgres' in _scheme:
        DATABASES['default'] = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME':     _u.path.lstrip('/'),
            'USER':     _u.username,
            'PASSWORD': _u.password or '',
            'HOST':     _u.hostname,
            'PORT':     str(_u.port or 5432),
            'CONN_MAX_AGE': 60,
        }

# ── Password hashing ──────────────────────────────────────────────────────────
# Argon2 is the strongest hasher available in Django (winner of Password Hashing
# Competition 2015). Falls back to PBKDF2 for any existing hashes on first login.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Timezone — Indian Standard Time (UTC+5:30) ────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ── Session security ──────────────────────────────────────────────────────────
# Absolute max lifetime: 8 hours. After this the user must log in again
# regardless of activity.
SESSION_COOKIE_AGE = 8 * 60 * 60           # 8 hours in seconds

# Session expires when the browser is closed (unless "Remember me" is checked).
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Idle timeout enforced by SessionTimeoutMiddleware (30 minutes of inactivity).
SESSION_IDLE_TIMEOUT = 30 * 60             # 30 minutes in seconds

# Warn the user this many seconds before idle timeout fires (countdown modal).
SESSION_IDLE_WARNING_BEFORE = 2 * 60       # warn 2 minutes before expiry

# Prevent JavaScript from reading the session cookie.
SESSION_COOKIE_HTTPONLY = True

# Restrict cross-site cookie sending.
SESSION_COOKIE_SAMESITE = 'Lax'

# ── Static / Media ────────────────────────────────────────────────────────────
STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'  # override with smtp in production
)
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@edutrack.local')
CSRF_FAILURE_VIEW = 'students.views.csrf_failure'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Razorpay ──────────────────────────────────────────────────────────────────
# Set these in your environment / .env file:
#   RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxxxx
#   RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
RAZORPAY_KEY_ID     = os.environ.get('RAZORPAY_KEY_ID', '').strip()
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '').strip()

# ── Production security headers ───────────────────────────────────────────────
# These are safe no-ops in dev (DEBUG=True) and active in production.
if not DEBUG:
    SECURE_HSTS_SECONDS           = 31536000   # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD           = True
    SECURE_SSL_REDIRECT           = True
    SESSION_COOKIE_SECURE         = True
    CSRF_COOKIE_SECURE            = True
    SECURE_CONTENT_TYPE_NOSNIFF   = True
    SECURE_BROWSER_XSS_FILTER     = True
    X_FRAME_OPTIONS               = 'DENY'

# ── Email (production) ────────────────────────────────────────────────────────
# Set these environment variables to enable real email:
#   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
#   EMAIL_HOST=smtp.gmail.com
#   EMAIL_PORT=587
#   EMAIL_HOST_USER=your@email.com
#   EMAIL_HOST_PASSWORD=yourpassword
#   EMAIL_USE_TLS=True
#   DEFAULT_FROM_EMAIL=EduTrack <your@email.com>
#
# For Gmail: use an App Password (not your account password).
# For SendGrid: EMAIL_HOST=smtp.sendgrid.net, EMAIL_HOST_USER=apikey
#
EMAIL_HOST          = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS       = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_USE_SSL       = os.environ.get('EMAIL_USE_SSL', 'False') == 'True'
