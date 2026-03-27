import os
from pathlib import Path
from dotenv import load_dotenv

# Chemin de base du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# Charge le fichier .env en local
load_dotenv(os.path.join(BASE_DIR, '.env'))

# --- SÉCURITÉ ---
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key-change-me')

# DEBUG est True en local, False en production (Render)
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Autorise localhost et l'adresse Render
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.onrender.com']


# --- APPLICATIONS ---
INSTALLED_APPS = [
    # On garde le minimum nécessaire pour les templates et les fichiers statiques
    'django.contrib.staticfiles',
    'hopital_site', 
]

# --- MIDDLEWARES ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Pour servir les CSS/JS sur Render
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'conf.urls'

# --- TEMPLATES ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'conf.wsgi.application'


# --- BASE DE DONNÉES (DÉSACTIVÉE) ---
# On laisse un dictionnaire vide ou une config SQLite minimale 
# car Django en a parfois besoin pour démarrer, mais on ne s'en servira pas.
DATABASES = {}


# --- INTERNATIONALISATION ---
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Kinshasa'
USE_I18N = True
USE_TZ = True


# --- FICHIERS STATIQUES (CSS, JS, IMAGES) ---
STATIC_URL = 'static/'

# Où Django cherche les fichiers en développement
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Où Django rassemble les fichiers pour Render (Production)
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Optimisation WhiteNoise pour la production
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- CONFIGURATION LOGS (Optionnel) ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'