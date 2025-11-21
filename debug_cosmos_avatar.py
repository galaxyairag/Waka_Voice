"""
Script de debug pour inspecter un document avatar dans Cosmos DB
"""
import json
import sys
import os

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from configuration.cosmos_config import get_avatar_config

def debug_avatar(agent_id):
    """Récupère et affiche les détails d'un avatar depuis Cosmos DB"""
    print(f"\n{'='*80}")
    print(f"🔍 INSPECTION COSMOS DB - Avatar: {agent_id}")
    print(f"{'='*80}\n")

    try:
        # Récupérer la config
        config = get_avatar_config(agent_id)

        if not config:
            print(f"❌ Aucune configuration trouvée pour l'agent_id: {agent_id}")
            return

        # Afficher les informations essentielles
        print(f"📋 INFORMATIONS GÉNÉRALES:")
        print(f"  - ID: {config.get('id')}")
        print(f"  - Agent ID: {config.get('agent_id')}")
        print(f"  - Agent Name: {config.get('agent_name')}")
        print(f"  - Status: {config.get('status')}")
        print(f"  - Current Step: {config.get('current_step')}")

        print(f"\n🎭 CONFIGURATION AVATAR:")
        print(f"  - avatar_character: {config.get('avatar_character')}")
        print(f"  - avatar_style: {config.get('avatar_style')}")
        print(f"  - avatar_type: {config.get('avatar_type')}")
        print(f"  - avatar_customized: {config.get('avatar_customized')}")
        print(f"  - avatar_background_color: {config.get('avatar_background_color')}")
        print(f"  - avatar_background_image: {config.get('avatar_background_image')}")

        print(f"\n🎤 CONFIGURATION VOIX:")
        print(f"  - voice_name: {config.get('voice_name')}")
        print(f"  - voice_type: {config.get('voice_type')}")
        print(f"  - voice_locale: {config.get('voice_locale')}")
        print(f"  - voice_gender: {config.get('voice_gender')}")

        print(f"\n🤖 CONFIGURATION MODÈLE:")
        print(f"  - model_id: {config.get('model_id')}")
        print(f"  - model_name: {config.get('model_name')}")
        print(f"  - model_family: {config.get('model_family')}")

        print(f"\n🔧 OUTILS SÉLECTIONNÉS ({len(config.get('selected_tools', []))}):")
        for tool in config.get('selected_tools', []):
            print(f"  - {tool}")

        print(f"\n📝 MÉTADONNÉES COSMOS DB:")
        print(f"  - _rid: {config.get('_rid')}")
        print(f"  - _self: {config.get('_self')}")
        print(f"  - _etag: {config.get('_etag')}")
        print(f"  - _ts: {config.get('_ts')}")

        print(f"\n📄 DOCUMENT JSON COMPLET:")
        print(json.dumps(config, indent=2, ensure_ascii=False))

        print(f"\n{'='*80}")
        print("✅ Inspection terminée")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"❌ Erreur lors de l'inspection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_cosmos_avatar.py <agent_id>")
        print("\nExemple:")
        print("  python debug_cosmos_avatar.py b0ad7dc3-9a2a-4ada-a919-9ef3624cfdac")
        sys.exit(1)

    agent_id = sys.argv[1]
    debug_avatar(agent_id)
