"""
Run this script from your project root to create all deployment files.
Command: python create_deploy_files.py
"""
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
print("=" * 60)
print("QR Menu — Creating Deployment Files")
print("=" * 60)

# ── 1. requirements.txt ───────────────────────────────────────────────────────
req = """Django==5.0.6
psycopg2-binary==2.9.9
Pillow==10.3.0
qrcode[pil]==7.4.2
django-environ==0.11.2
whitenoise==6.7.0
gunicorn==22.0.0
django-htmx==1.18.0
dj-database-url==2.1.0
"""
with open(os.path.join(BASE, 'requirements.txt'), 'w') as f:
    f.write(req)
print("✓ requirements.txt updated")

# ── 2. config/settings.py ────────────────────────────────────────────────────
settings = """import environ
import dj_database_url
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY    = env("SECRET_KEY", default="change-me-in-production-abc123xyz")
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

# Database — uses DATABASE_URL from Render, falls back to local PostgreSQL
DATABASE_URL = env("DATABASE_URL", default=None)
if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
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

# Static files
STATIC_URL   = "/static/"
STATIC_ROOT  = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files
MEDIA_URL  = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Auth
LOGIN_URL           = "/auth/login/"
LOGIN_REDIRECT_URL  = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# Security (only active in production when DEBUG=False)
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

# ── 3. build.sh ───────────────────────────────────────────────────────────────
build_sh = """#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
"""
build_path = os.path.join(BASE, 'build.sh')
with open(build_path, 'w', newline='\n') as f:
    f.write(build_sh)
# Make executable on Linux/Mac (no effect on Windows but needed for Render)
try:
    import stat
    st = os.stat(build_path)
    os.chmod(build_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
except:
    pass
print("✓ build.sh created")

# ── 4. Procfile ───────────────────────────────────────────────────────────────
procfile = "web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2\n"
with open(os.path.join(BASE, 'Procfile'), 'w', newline='\n') as f:
    f.write(procfile)
print("✓ Procfile created")

# ── 5. .gitignore ─────────────────────────────────────────────────────────────
gitignore = """.env
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
staticfiles/
media/
db.sqlite3
.DS_Store
Thumbs.db
.vscode/
.idea/
*.egg-info/
dist/
build/
"""
with open(os.path.join(BASE, '.gitignore'), 'w') as f:
    f.write(gitignore)
print("✓ .gitignore created")

# ── 6. Install dj-database-url locally ───────────────────────────────────────
print("\nInstalling dj-database-url...")
subprocess.run([sys.executable, '-m', 'pip', 'install', 'dj-database-url==2.1.0'], check=True)
print("✓ dj-database-url installed")

# ── 7. Generate a secret key ─────────────────────────────────────────────────
import secrets
new_key = secrets.token_urlsafe(50)

print("\n" + "=" * 60)
print("ALL FILES CREATED SUCCESSFULLY!")
print("=" * 60)
print("\nNEXT STEPS:")
print("\n1. Copy this SECRET_KEY for Render (don't use your local one):")
print(f"\n   {new_key}\n")
print("2. Push to GitHub:")
print("   git init")
print("   git add .")
print('   git commit -m "Deploy QR Menu to Render"')
print("   git branch -M main")
print("   git remote add origin https://github.com/YOUR_USERNAME/qrmenu.git")
print("   git push -u origin main")
print("\n3. Follow the deployment guide document for Render setup.")
print("=" * 60)
