#!/usr/bin/env python3
"""
Script pour supprimer la clé 'avatar_style' du dernier avatar créé
"""

import os
import sys
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def remove_style_from_last_avatar():
    """Supprime la clé avatar_style du dernier avatar"""
    try:
        from azure.cosmos import CosmosClient
        
        # Configuration Cosmos DB
        endpoint = os.getenv('COSMOS_URI')
        key = os.getenv('COSMOS_KEY')
        database_name = os.getenv('COSMOS_DATABASE_NAME', 'WakaVoiceDB')
        
        if not endpoint or not key:
            print("❌ COSMOS_URI ou COSMOS_KEY manquant dans .env")
            return
        
        # Connexion
        client = CosmosClient(endpoint, key)
        database = client.get_database_client(database_name)
        container = database.get_container_client('AvatarConfigurations')
        
        # Récupérer le dernier avatar
        query = "SELECT * FROM c ORDER BY c.created_at DESC OFFSET 0 LIMIT 1"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if not items:
            print("❌ Aucun avatar trouvé")
            return
        
        avatar = items[0]
        agent_id = avatar.get('id')
        agent_name = avatar.get('agent_name', 'N/A')
        
        print(f"\n📋 Dernier avatar trouvé:")
        print(f"   ID: {agent_id}")
        print(f"   Nom: {agent_name}")
        print(f"   Character: {avatar.get('avatar_character', 'N/A')}")
        print(f"   Style actuel: {avatar.get('avatar_style', 'N/A')}")
        
        # Vérifier si la clé existe
        if 'avatar_style' not in avatar:
            print("\n✅ La clé 'avatar_style' n'existe déjà pas")
            return
        
        # Supprimer la clé avatar_style
        del avatar['avatar_style']
        
        # Mettre à jour dans Cosmos DB
        container.upsert_item(avatar)
        
        print(f"\n✅ Clé 'avatar_style' supprimée avec succès !")
        print(f"   Avatar: {agent_name} ({agent_id})")
        
        # Vérification
        updated = container.read_item(item=agent_id, partition_key=agent_id)
        if 'avatar_style' not in updated:
            print("✅ Vérification OK - clé bien supprimée")
        else:
            print("⚠️  La clé existe encore:", updated.get('avatar_style'))
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    remove_style_from_last_avatar()
