#!/usr/bin/env python3
"""
Script pour vider le cache Flask
"""
import shutil
import os

# Supprimer le dossier flask_session
session_folder = "flask_session"
if os.path.exists(session_folder):
    shutil.rmtree(session_folder)
    print(f"✅ Dossier {session_folder} supprimé")
    os.makedirs(session_folder)
    print(f"✅ Dossier {session_folder} recréé")
else:
    print(f"ℹ️  Dossier {session_folder} n'existe pas")

# Supprimer __pycache__
for root, dirs, files in os.walk('.'):
    if '__pycache__' in dirs:
        cache_path = os.path.join(root, '__pycache__')
        shutil.rmtree(cache_path)
        print(f"✅ Cache supprimé: {cache_path}")

print("\n🎉 Cache vidé avec succès!")
print("💡 Relancez votre serveur Flask avec: python app.py")
