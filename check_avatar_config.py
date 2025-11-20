"""Script pour vérifier la configuration d'un avatar dans Cosmos DB"""
from configuration.cosmos_config import get_avatar_container
import json

try:
    container = get_avatar_container()
    
    # Récupérer le dernier avatar créé
    query = 'SELECT * FROM c ORDER BY c.created_at DESC OFFSET 0 LIMIT 1'
    avatars = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    
    if avatars:
        avatar = avatars[0]
        print('=' * 60)
        print('DERNIER AVATAR CRÉÉ')
        print('=' * 60)
        print(f"Agent ID: {avatar.get('agent_id')}")
        print(f"Nom: {avatar.get('agent_name')}")
        print(f"Status: {avatar.get('status')}")
        print(f"Créé: {avatar.get('created_at')}")
        print()
        
        print('=' * 60)
        print('VÉRIFICATION DES CHAMPS')
        print('=' * 60)
        
        # Vérifier tous les champs attendus
        fields_check = {
            'Basique': [
                'agent_id', 'agent_name', 'status', 'created_at', 'current_step'
            ],
            'Modèle': [
                'model_id', 'model_name', 'temperature', 'max_tokens', 'top_p'
            ],
            'Voix': [
                'voice_name', 'voice_type', 'voice_rate', 'voice_temperature'
            ],
            'Avatar': [
                'avatar_character', 'avatar_style', 'avatar_customized',
                'avatar_background_color', 'avatar_background_image', 'avatar_resolution'
            ],
            'Audio Avancé': [
                'enable_echo_cancellation', 'enable_noise_reduction',
                'enable_end_of_utterance', 'end_of_utterance_config',
                'enable_output_timestamps'
            ],
            'Autres': [
                'system_prompt', 'selected_tools'
            ]
        }
        
        for category, fields in fields_check.items():
            print(f"\n📁 {category}:")
            for field in fields:
                value = avatar.get(field)
                status = '✅' if value is not None else '❌'
                if value is not None:
                    if isinstance(value, (dict, list)):
                        print(f"  {status} {field}: {type(value).__name__} ({len(value)} items)")
                    else:
                        value_str = str(value)
                        if len(value_str) > 50:
                            value_str = value_str[:47] + '...'
                        print(f"  {status} {field}: {value_str}")
                else:
                    print(f"  {status} {field}: None")
        
        print()
        print('=' * 60)
        print('RÉSUMÉ')
        print('=' * 60)
        
        all_fields = []
        for fields in fields_check.values():
            all_fields.extend(fields)
        
        present = sum(1 for f in all_fields if avatar.get(f) is not None)
        total = len(all_fields)
        
        print(f"Champs présents: {present}/{total} ({present*100//total}%)")
        
        missing = [f for f in all_fields if avatar.get(f) is None]
        if missing:
            print(f"\n❌ Champs manquants ({len(missing)}):")
            for field in missing:
                print(f"  - {field}")
        else:
            print("\n✅ Tous les champs sont présents!")
        
        print()
        print('=' * 60)
        print('DOCUMENT COMPLET (extrait)')
        print('=' * 60)
        # Afficher seulement les champs importants
        important_fields = {
            k: v for k, v in avatar.items() 
            if k in all_fields
        }
        print(json.dumps(important_fields, indent=2, default=str))
        
    else:
        print('❌ Aucun avatar trouvé dans la base de données')
        
except Exception as e:
    print(f'❌ Erreur: {e}')
    import traceback
    traceback.print_exc()
