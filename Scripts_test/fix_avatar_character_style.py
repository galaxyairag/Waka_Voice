"""
Script pour corriger les valeurs avatar_character et avatar_style dans Cosmos DB
"""
import os
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Utiliser la configuration existante
from configuration.cosmos_config import get_cosmos_client, get_avatar_container

def fix_avatar_config(agent_id=None):
    """Corriger les valeurs avatar_character et avatar_style"""
    
    # Connexion à Cosmos DB (utilise la config existante)
    container = get_avatar_container()
    
    # Construire la requête
    if agent_id:
        query = f"SELECT * FROM c WHERE c.agent_id = '{agent_id}'"
        print(f"🔍 Recherche de l'avatar avec agent_id = {agent_id}")
    else:
        query = "SELECT * FROM c"
        print("🔍 Recherche de tous les avatars")
    
    # Récupérer les documents
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    
    if not items:
        print("❌ Aucun avatar trouvé")
        return
    
    print(f"✅ Trouvé {len(items)} avatar(s)")
    
    # Traiter chaque avatar
    for item in items:
        print(f"\n📝 Avatar: {item.get('agent_id', 'N/A')}")
        print(f"   Nom: {item.get('agent_name', 'N/A')}")
        
        # Afficher les valeurs actuelles
        current_character = item.get('avatar_character')
        current_style = item.get('avatar_style')
        print(f"   🎭 Character actuel: {current_character}")
        print(f"   🎨 Style actuel: {current_style}")
        
        # Déterminer les nouvelles valeurs
        needs_update = False
        
        if current_character is None or current_character == '':
            item['avatar_character'] = 'lisa'
            print(f"   ✏️ Mise à jour character: None → lisa")
            needs_update = True
        
        if current_style is None or current_style == '':
            item['avatar_style'] = 'casual-sitting'
            print(f"   ✏️ Mise à jour style: None → casual-sitting")
            needs_update = True
        
        # Mettre à jour si nécessaire
        if needs_update:
            try:
                container.upsert_item(item)
                print(f"   ✅ Avatar mis à jour avec succès")
            except Exception as e:
                print(f"   ❌ Erreur lors de la mise à jour: {e}")
        else:
            print(f"   ℹ️ Aucune mise à jour nécessaire")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Corriger les valeurs avatar_character et avatar_style')
    parser.add_argument('--agent-id', type=str, help='ID de l\'agent à corriger (optionnel)')
    parser.add_argument('--character', type=str, default='lisa', help='Valeur par défaut pour character (défaut: lisa)')
    parser.add_argument('--style', type=str, default='casual-sitting', help='Valeur par défaut pour style (défaut: casual-sitting)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔧 CORRECTION DES AVATARS")
    print("=" * 60)
    
    fix_avatar_config(agent_id=args.agent_id)
    
    print("\n" + "=" * 60)
    print("✅ SCRIPT TERMINÉ")
    print("=" * 60)
