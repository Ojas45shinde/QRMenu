"""
Run this script to fix all Render deployment issues.
Command: python render_fix.py
"""
import os
import sys
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
print("=" * 60)
print("QR Menu — Render Deployment Fix")
print("=" * 60)

# ── 1. Create management command directory ────────────────────────────────────
cmd_dir = os.path.join(BASE, 'apps', 'core', 'management', 'commands')
os.makedirs(cmd_dir, exist_ok=True)

# Create __init__.py files
for d in [
    os.path.join(BASE, 'apps', 'core', 'management'),
    cmd_dir,
]:
    init = os.path.join(d, '__init__.py')
    if not os.path.exists(init):
        open(init, 'w').close()

# ── 2. Write create_admin management command ─────────────────────────────────
create_admin = '''import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Creates superuser from environment variables"

    def handle(self, *args, **kwargs):
        username = os.environ.get("DJANGO_ADMIN_USERNAME", "admin")
        password = os.environ.get("DJANGO_ADMIN_PASSWORD", "")
        email    = os.environ.get("DJANGO_ADMIN_EMAIL", "admin@example.com")

        if not password:
            self.stdout.write(self.style.WARNING(
                "DJANGO_ADMIN_PASSWORD not set — skipping superuser creation."
            ))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(
                f\'Superuser "{username}" already exists — skipping.\'
            ))
            return

        User.objects.create_superuser(username=username, password=password, email=email)
        self.stdout.write(self.style.SUCCESS(
            f\'Superuser "{username}" created successfully!\'
        ))
'''
with open(os.path.join(cmd_dir, 'create_admin.py'), 'w', encoding='utf-8') as f:
    f.write(create_admin)
print("✓ apps/core/management/commands/create_admin.py created")

# ── 3. Write updated build.sh ─────────────────────────────────────────────────
build_sh = """#!/usr/bin/env bash
set -o errexit

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Running migrations..."
python manage.py migrate

echo "==> Creating superuser (if DJANGO_ADMIN_PASSWORD is set)..."
python manage.py create_admin

echo "==> Build complete!"
"""
build_path = os.path.join(BASE, 'build.sh')
with open(build_path, 'w', newline='\n') as f:
    f.write(build_sh)
import stat
st = os.stat(build_path)
os.chmod(build_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
print("✓ build.sh updated with create_admin command")

# ── 4. Write updated settings.py ─────────────────────────────────────────────
settings = """import environ
import dj_database_url
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(DEBUG=(bool, False))

# Read .env file if it exists (local development)
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(env_file)

SECRET_KEY    = env("SECRET_KEY", default="local-dev-key-change-in-production")
DEBUG         = env("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "apps.core",
    "apps.restaurants",
    "apps.menus",
    "apps.qrcodes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "apps.restaurants.middleware.TenantMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": { "context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

WSGI_APPLICATION = "config.wsgi.application"

# ── Database ──────────────────────────────────────────────────────────────────
# Render injects DATABASE_URL automatically
DATABASE_URL = env("DATABASE_URL", default=None)

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Local PostgreSQL fallback
    DATABASES = {"default": {
        "ENGINE":   "django.db.backends.postgresql",
        "NAME":     env("DB_NAME",     default="qrmenu_db"),
        "USER":     env("DB_USER",     default="postgres"),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST":     env("DB_HOST",     default="localhost"),
        "PORT":     env("DB_PORT",     default="5432"),
    }}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Static files ──────────────────────────────────────────────────────────────
STATIC_URL   = "/static/"
STATIC_ROOT  = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ── Media files ───────────────────────────────────────────────────────────────
MEDIA_URL  = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ── Auth ──────────────────────────────────────────────────────────────────────
LOGIN_URL           = "/auth/login/"
LOGIN_REDIRECT_URL  = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# ── Security (production only) ────────────────────────────────────────────────
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER   = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS             = "DENY"
    SESSION_COOKIE_SECURE       = True
    CSRF_COOKIE_SECURE          = True

LANGUAGE_CODE      = "en-us"
TIME_ZONE          = "Asia/Kolkata"
USE_I18N = USE_TZ  = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
"""
settings_path = os.path.join(BASE, 'config', 'settings.py')
with open(settings_path, 'w', encoding='utf-8') as f:
    f.write(settings)
print("✓ config/settings.py updated")

# ── 5. Install dj-database-url ────────────────────────────────────────────────
print("\nInstalling dj-database-url...")
subprocess.run([sys.executable, '-m', 'pip', 'install', 'dj-database-url==2.1.0'], check=True)
print("✓ dj-database-url installed")

# ── 6. Print instructions ─────────────────────────────────────────────────────
import secrets
new_key = secrets.token_urlsafe(50)

print("\n" + "=" * 60)
print("ALL FILES FIXED!")
print("=" * 60)

print("""
STEP 1 — Add these Environment Variables on Render:
  (Go to Render → Your Web Service → Environment)

  SECRET_KEY              = """ + new_key + """
  DEBUG                   = False
  DATABASE_URL            = (paste your Render Internal Database URL)
  ALLOWED_HOSTS           = your-app-name.onrender.com
  PYTHON_VERSION          = 3.12.4
  DJANGO_ADMIN_USERNAME   = admin
  DJANGO_ADMIN_PASSWORD   = choose_a_strong_password_here
  DJANGO_ADMIN_EMAIL      = your@email.com

STEP 2 — Push to GitHub:
  git add .
  git commit -m "Fix Render deployment"
  git push origin main

STEP 3 — Render will auto-redeploy in ~3 minutes.
  The superuser will be created automatically during build.
  Then login at: https://your-app.onrender.com/auth/login/
  Username: admin
  Password: (whatever you set as DJANGO_ADMIN_PASSWORD)
""")
print("=" * 60)
