from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-ym9vb2_e@^od(@zm++z!)0ldu1q$xfv@ds1qx9@e^x_j2$96is'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.ngrok-free.app', '.ngrok.io']
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
    }
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
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@edutrack.local'
CSRF_FAILURE_VIEW = 'students.views.csrf_failure'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
