#!/usr/bin/env bash
# exit on error
set -o errexit

# Installer les dépendances
pip install -r requirements.txt

# --- AJOUTE CETTE LIGNE ICI ---
# Créer le dossier pour la base de données s'il n'existe pas
mkdir -p data

# Collecter les fichiers statiques
python manage.py collectstatic --no-input

# Appliquer les migrations
python manage.py migrate
