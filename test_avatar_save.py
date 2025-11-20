#!/usr/bin/env python3
"""
Script de test pour vérifier la sauvegarde complète des paramètres avatar via l'interface
IMPORTANT: Ce script ne crée PAS d'avatar de test, il vérifie le dernier avatar existant
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_latest_avatar():
    """Vérifier que tous les champs sont présents dans le dernier avatar"""
    from configuration.cosmos_config import get_cosmos_client, COSMOS_DATABASE_NAME
    
    # Container avatars
    cosmos_client = get_cosmos_client()
    database = cosmos_client.get_database_client(COSMOS_DATABASE_NAME)
    container = database.get_container_client('AvatarConfigurations')
    
    # Récupérer le dernier avatar
    query = 'SELECT * FROM c ORDER BY c.created_at DESC OFFSET 0 LIMIT 1'
    avatars = list(container.query_items(query=query, enable_cross_partition_query=True))
    
    if not avatars:
        print("❌ Aucun avatar trouvé dans la base de données")
        return False
    
    avatar = avatars[0]
    agent_id = avatar.get('agent_id')
    agent_name = avatar.get('agent_name', 'N/A')
    created_at = avatar.get('created_at', 'N/A')
    
    print(f"Agent ID: {agent_id}")
    print(f"Nom: {agent_name}")
    print(f"Créé: {created_at}\n")
    
    # Champs attendus
    expected_fields = {
        'Basique': ['agent_id', 'agent_name', 'status', 'created_at', 'current_step'],
        'Modèle': ['model_id', 'model_name', 'temperature', 'max_tokens', 'top_p'],
        'Voix': ['voice_name', 'voice_type', 'voice_rate', 'voice_temperature'],
        'Avatar': ['avatar_character', 'avatar_style', 'avatar_customized', 'avatar_background_color', 'avatar_background_image', 'avatar_resolution'],
        'Audio Avancé': ['enable_echo_cancellation', 'enable_noise_reduction', 'enable_end_of_utterance', 'end_of_utterance_config', 'enable_output_timestamps'],
        'Autres': ['system_prompt', 'selected_tools']
    }
    
    total_fields = 0
    present_fields = 0
    missing_fields = []
    
    print("="*60)
    print("VÉRIFICATION DES CHAMPS")
    print("="*60)
    
    for category, fields in expected_fields.items():
        print(f"\n📁 {category}:")
        for field in fields:
            total_fields += 1
            value = avatar.get(field)
            if value is not None:
                present_fields += 1
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + '...'
                print(f"  ✅ {field}: {value}")
            else:
                print(f"  ❌ {field}: None")
                missing_fields.append(field)
    
    percentage = (present_fields / total_fields) * 100
    print("\n" + "="*60)
    print("RÉSUMÉ")
    print("="*60)
    print(f"Champs présents: {present_fields}/{total_fields} ({percentage:.0f}%)")
    
    if missing_fields:
        print(f"\n❌ Champs manquants ({len(missing_fields)}):")
        for field in missing_fields:
            print(f"  - {field}")
    
    if present_fields == total_fields:
        print("\n✅ SUCCÈS: Tous les champs sont présents!")
        return True
    else:
        print(f"\n⚠️ ATTENTION: {len(missing_fields)} champs manquants")
        return False

if __name__ == '__main__':
    print("🔍 Vérification du dernier avatar créé\n")
    success = verify_latest_avatar()
    
    if success:
        print("\n✅ Configuration complète!")
    else:
        print("\n⚠️ Veuillez créer un nouvel avatar via l'interface pour tester la sauvegarde complète")
        print("   Utilisez l'interface web pour créer un avatar avec tous les paramètres")

