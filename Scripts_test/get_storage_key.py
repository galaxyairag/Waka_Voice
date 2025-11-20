"""
Script pour récupérer la clé du compte de stockage Azure
et mettre à jour le .env avec la bonne BLOB_CONNECTION_STRING
"""

import os
import subprocess
import json
from dotenv import load_dotenv

# Charger le .env
load_dotenv()

def get_storage_account_key():
    """Récupère la clé du compte de stockage via Azure CLI"""
    
    storage_account_name = "wakavoicestorage"
    
    print(f"🔍 Recherche de la clé pour le compte: {storage_account_name}")
    
    try:
        # Essayer de récupérer via Azure CLI
        cmd = [
            "az", "storage", "account", "keys", "list",
            "--account-name", storage_account_name,
            "--query", "[0].value",
            "-o", "tsv"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        storage_key = result.stdout.strip()
        
        if storage_key:
            print(f"✅ Clé trouvée: {storage_key[:20]}...")
            return storage_key
        else:
            print("❌ Aucune clé retournée")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur Azure CLI: {e}")
        print(f"   STDOUT: {e.stdout}")
        print(f"   STDERR: {e.stderr}")
        return None
    except FileNotFoundError:
        print("❌ Azure CLI non trouvé. Installez avec: winget install Microsoft.AzureCLI")
        return None


def update_env_file(storage_key):
    """Met à jour le fichier .env avec la bonne connection string"""
    
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    
    storage_account_name = "wakavoicestorage"
    new_connection_string = (
        f"DefaultEndpointsProtocol=https;"
        f"AccountName={storage_account_name};"
        f"AccountKey={storage_key};"
        f"EndpointSuffix=core.windows.net"
    )
    
    # Lire le fichier .env
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Remplacer la ligne BLOB_CONNECTION_STRING
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('BLOB_CONNECTION_STRING='):
            lines[i] = f'BLOB_CONNECTION_STRING={new_connection_string}\n'
            updated = True
            break
    
    # Si la ligne n'existe pas, l'ajouter
    if not updated:
        lines.append(f'\nBLOB_CONNECTION_STRING={new_connection_string}\n')
    
    # Écrire le fichier .env
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✅ Fichier .env mis à jour avec la nouvelle connection string")
    print(f"   AccountName: {storage_account_name}")
    print(f"   AccountKey: {storage_key[:20]}...")


def main():
    print("=" * 70)
    print("Récupération de la clé du compte de stockage Azure")
    print("=" * 70)
    print()
    
    # Vérifier si Azure CLI est connecté
    try:
        result = subprocess.run(
            ["az", "account", "show"],
            capture_output=True,
            text=True,
            check=True
        )
        account_info = json.loads(result.stdout)
        print(f"✅ Connecté à Azure: {account_info.get('name', 'N/A')}")
        print(f"   Subscription: {account_info.get('id', 'N/A')}")
        print()
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        print("❌ Vous devez vous connecter à Azure CLI")
        print("   Exécutez: az login")
        print()
        return
    
    # Récupérer la clé
    storage_key = get_storage_account_key()
    
    if storage_key:
        print()
        print("Voulez-vous mettre à jour le fichier .env ? (o/n)")
        response = input("> ").strip().lower()
        
        if response == 'o':
            update_env_file(storage_key)
            print()
            print("✅ Configuration terminée!")
            print("   Vous pouvez maintenant relancer l'application")
        else:
            print()
            print("📋 Voici la connection string à copier dans .env:")
            print()
            print(f"BLOB_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=wakavoicestorage;AccountKey={storage_key};EndpointSuffix=core.windows.net")
    else:
        print()
        print("❌ Impossible de récupérer la clé")
        print()
        print("Solutions alternatives:")
        print("1. Connectez-vous à Azure CLI: az login")
        print("2. Récupérez la clé via le portail Azure:")
        print("   - Allez sur https://portal.azure.com")
        print("   - Recherchez le compte 'wakavoicestorage'")
        print("   - Allez dans 'Access Keys'")
        print("   - Copiez une des clés")
        print("   - Mettez à jour BLOB_CONNECTION_STRING dans .env")


if __name__ == "__main__":
    main()
