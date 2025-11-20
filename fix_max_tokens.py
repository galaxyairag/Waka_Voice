#!/usr/bin/env python3
"""
Script pour corriger les max_tokens qui dépassent 4096 dans les avatars
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from configuration.cosmos_config import get_cosmos_client, COSMOS_DATABASE_NAME

def fix_max_tokens():
    """Corriger les max_tokens > 4096 dans tous les avatars"""
    
    # Container avatars
    cosmos_client = get_cosmos_client()
    database = cosmos_client.get_database_client(COSMOS_DATABASE_NAME)
    container = database.get_container_client('AvatarConfigurations')
    
    # Récupérer tous les avatars
    query = 'SELECT * FROM c'
    avatars = list(container.query_items(query=query, enable_cross_partition_query=True))
    
    print(f"🔍 Trouvé {len(avatars)} avatars\n")
    
    fixed_count = 0
    skipped_count = 0
    
    for avatar in avatars:
        agent_id = avatar.get('agent_id')
        agent_name = avatar.get('agent_name', 'N/A')
        max_tokens = avatar.get('max_tokens')
        
        # Vérifier si max_tokens existe et dépasse 4096
        if max_tokens is not None:
            try:
                max_tokens_int = int(max_tokens)
                
                if max_tokens_int > 4096:
                    print(f"⚠️  {agent_name} ({agent_id})")
                    print(f"   max_tokens actuel: {max_tokens_int}")
                    
                    # Mettre à jour à 4096
                    avatar['max_tokens'] = 4096
                    container.upsert_item(avatar)
                    
                    print(f"   ✅ Corrigé à: 4096\n")
                    fixed_count += 1
                else:
                    print(f"✓  {agent_name}: max_tokens = {max_tokens_int} (OK)")
                    skipped_count += 1
                    
            except (ValueError, TypeError):
                print(f"⚠️  {agent_name}: max_tokens invalide = {max_tokens}")
                # Mettre à None ou 4096
                avatar['max_tokens'] = 4096
                container.upsert_item(avatar)
                print(f"   ✅ Corrigé à: 4096\n")
                fixed_count += 1
        else:
            print(f"ℹ️  {agent_name}: max_tokens non défini (OK)")
            skipped_count += 1
    
    print("="*60)
    print("RÉSUMÉ")
    print("="*60)
    print(f"✅ Avatars corrigés: {fixed_count}")
    print(f"✓  Avatars OK: {skipped_count}")
    print(f"📊 Total: {len(avatars)}")
    
    if fixed_count > 0:
        print(f"\n✅ {fixed_count} avatar(s) ont été corrigés avec max_tokens=4096")
    else:
        print("\n✓ Aucune correction nécessaire, tous les avatars sont OK")

if __name__ == '__main__':
    print("🔧 Correction des max_tokens dans les avatars\n")
    fix_max_tokens()
