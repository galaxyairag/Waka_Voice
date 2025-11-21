#!/bin/bash
# Supprimer tous les caches Python
find /home/site/wwwroot -name "*.pyc" -delete
find /home/site/wwwroot -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
# Démarrer Gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 --threads 2 --timeout 120 --worker-class sync app:app
