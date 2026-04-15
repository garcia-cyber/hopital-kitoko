import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Chemins de base
BASE_DIR = Path(__file__).resolve().parent.parent

# Charge le fichier .env en local pour la sécurité
load_dotenv(os.path.join(BASE_DIR, '.env'))

# 2. Sécurité
# Récupère la clé depuis le .env, sinon utilise une clé par défaut en local
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-votre-cle-de-test-ici')

# DEBUG est True en local, False sur Render (via variable d'environnement)
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Autorise localhost et ton adresse sur Render
#ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.onrender.com'] avec la version de l'application
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'hopital-kitoko.onrender.com']

# 3. Applications installées
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Ton application
    'hopital_site', 
]

# 4. Middlewares (Important : WhiteNoise doit être juste après SecurityMiddleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Pour les fichiers statiques sur Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'conf.urls'

# 5. Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'conf.wsgi.application'

# 6. Base de données (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 7. Internationalisation (Configuré pour Kinshasa)
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Kinshasa'
USE_I18N = True
USE_TZ = True

# 8. Fichiers Statiques (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Dossier source des fichiers statiques
STATICFILES_DIRS = [
    BASE_DIR /'static',
]

# Dossier où Django rassemble les fichiers pour la production (Render)
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Optimisation WhiteNoise (Compression et cache)
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 9. Sécurité HTTPS pour la production
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField' 

# 10 . Redirection du login 
# redirection apres authentification
#
LOGIN_REDIRECT_URL = '/panel/' 
LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = '/home/' 

# 11 configuration media pour gere les images 
#
MEDIA_URL = '/media/'
MEDIA_ROOT = '/media/'