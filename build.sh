#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Créer le dossier pour la base de données
mkdir -p data

# 3. Collecter les fichiers statiques (CSS, JS, Images)
python manage.py collectstatic --no-input

# 4. Appliquer les migrations (Création des tables)
python manage.py migrate

# 5. CRÉATION AUTOMATIQUE DU COMPTE ADMIN (Ton accès)
# Remplace 'ton_nom', 'ton_mail@gmail.com' et 'TonMotDePasse123' par tes infos
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
username = 'hopital@'
email = 'hopital@gmail.com'
password = 'hopital@'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f'Superuser "{username}" créé avec succès !')
else:
    print(f'Le superuser "{username}" existe déjà.')
EOF
