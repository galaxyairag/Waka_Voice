"""
Script pour vérifier et configurer Azure Blob Storage pour Personal Voice
"""

import os
import sys
from dotenv import load_dotenv

# Ajouter le dossier parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

print("=" * 70)
print("Configuration Azure Blob Storage pour Personal Voice")
print("=" * 70)

# Vérifier les variables d'environnement
print("\n📋 Variables d'environnement actuelles:")
print(f"   BLOB_CONNECTION_STRING: {'✅ Défini' if os.getenv('BLOB_CONNECTION_STRING') else '❌ Non défini'}")
print(f"   BLOB_ACCOUNT_NAME: {'✅ Défini' if os.getenv('BLOB_ACCOUNT_NAME') else '❌ Non défini'}")
print(f"   BLOB_ACCOUNT_KEY: {'✅ Défini' if os.getenv('BLOB_ACCOUNT_KEY') else '❌ Non défini'}")
print(f"   COSMOS_URI: {'✅ Défini' if os.getenv('COSMOS_URI') else '❌ Non défini'}")
print(f"   COSMOS_KEY: {'✅ Défini' if os.getenv('COSMOS_KEY') else '❌ Non défini'}")

print("\n" + "=" * 70)
print("Instructions pour configurer Azure Blob Storage:")
print("=" * 70)

print("""
Option 1: Créer un nouveau compte de stockage Azure (RECOMMANDÉ)
----------------------------------------------------------------
1. Aller sur le portail Azure: https://portal.azure.com
2. Créer une nouvelle ressource "Compte de stockage"
3. Configuration recommandée:
   - Nom: wakavoicestorage (ou autre nom unique)
   - Région: Même que vos autres ressources (East US 2)
   - Performance: Standard
   - Redondance: LRS (Local Redundant Storage)
   - Niveau d'accès: Hot (accès fréquent)

4. Une fois créé, aller dans "Clés d'accès" et copier:
   - Le nom du compte de stockage
   - Une des deux clés d'accès (key1 ou key2)
   - La chaîne de connexion complète

5. Ajouter dans votre fichier .env:
   BLOB_CONNECTION_STRING=<coller la chaîne de connexion complète>

Option 2: Utiliser un compte existant
--------------------------------------
Si vous avez déjà un compte de stockage Azure:
1. Aller dans le portail Azure
2. Ouvrir votre compte de stockage
3. Aller dans "Clés d'accès"
4. Copier la chaîne de connexion
5. L'ajouter dans .env comme ci-dessus

Option 3: Utiliser les credentials Cosmos DB (automatique)
-----------------------------------------------------------
Le système essaiera automatiquement d'utiliser les mêmes credentials
que Cosmos DB. Cependant, cela ne fonctionnera que si votre compte
Cosmos DB inclut également le service Blob Storage.

""")

print("=" * 70)
print("Test de connexion:")
print("=" * 70)

try:
    from configuration.personal_voice_storage import init_personal_voice_storage
    
    print("\n🔄 Tentative d'initialisation du stockage...")
    success = init_personal_voice_storage()
    
    if success:
        print("\n✅ SUCCÈS! Le stockage Personal Voice est configuré correctement.")
        print("   Les containers suivants ont été créés/vérifiés:")
        print("   - Cosmos DB: PersonalVoiceProjects")
        print("   - Cosmos DB: PersonalVoiceConsents")
        print("   - Cosmos DB: PersonalVoices")
        print("   - Blob Storage: consent-audio")
        print("   - Blob Storage: voice-samples")
        print("   - Blob Storage: synthesized-audio")
    else:
        print("\n⚠️ L'initialisation a échoué. Vérifiez les logs ci-dessus.")
        
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    print("\n💡 Solution:")
    print("   Vous devez configurer un compte Azure Blob Storage.")
    print("   Suivez les instructions ci-dessus (Option 1 recommandée).")

print("\n" + "=" * 70)
