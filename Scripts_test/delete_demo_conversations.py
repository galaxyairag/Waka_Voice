"""
Script pour supprimer les conversations de démo
"""

import os
import sys
from datetime import datetime, timedelta, timezone

# Ajouter le chemin racine pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configuration.cosmos_config import get_call_history_container

def delete_demo_conversations():
    """Supprime les conversations de démo (des 7 derniers jours)"""
    
    print("=" * 80)
    print("SUPPRESSION DES CONVERSATIONS DE DÉMO")
    print("=" * 80)
    print()
    
    container = get_call_history_container()
    
    # Calculer la date il y a 7 jours
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    timestamp = int(seven_days_ago.timestamp())
    
    # Query pour trouver les conversations récentes
    query = f"SELECT c.id, c.call_id FROM c WHERE c._ts >= {timestamp}"
    
    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    
    print(f"📋 Trouvé {len(items)} conversations à supprimer")
    print()
    
    deleted = 0
    for item in items:
        try:
            container.delete_item(item=item['id'], partition_key=item['call_id'])
            deleted += 1
            print(".", end="", flush=True)
            if deleted % 50 == 0:
                print(f" {deleted}")
        except Exception as e:
            print(f"\n✗ Erreur: {e}")
    
    print()
    print()
    print("=" * 80)
    print(f"✅ {deleted} conversations supprimées avec succès!")
    print("=" * 80)
    print()

if __name__ == "__main__":
    delete_demo_conversations()
