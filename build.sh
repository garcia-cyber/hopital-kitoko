#!/usr/bin/env bash
# exit on error
set -o errexit

# Installer les dépendances
pip install -r requirements.txt

# Collecter les fichiers statiques (CSS, images)
python manage.py collectstatic --no-input

# Appliquer les migrations sur le disque persistant
python manage.py migrate
