"""
Script simple pour vérifier les valeurs actuelles des avatars
"""
import os
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from configuration.cosmos_config import get_avatar_container

def check_avatars():
    """Vérifier les valeurs actuelles"""
    container = get_avatar_container()
    
    query = "SELECT c.agent_id, c.agent_name, c.avatar_character, c.avatar_style FROM c"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    
    print("=" * 70)
    print("📊 VALEURS ACTUELLES DES AVATARS")
    print("=" * 70)
    
    for item in items:
        print(f"\n🎯 Avatar: {item.get('agent_name', 'N/A')}")
        print(f"   ID: {item.get('agent_id', 'N/A')}")
        print(f"   Character: {item.get('avatar_character', 'N/A')}")
        print(f"   Style: {item.get('avatar_style', 'N/A')}")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    check_avatars()
