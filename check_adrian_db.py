"""
Vérifier la config complète de l'agent adrian dans Cosmos DB
"""
import sys
import json

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from configuration.cosmos_config import get_avatar_container

container = get_avatar_container()

def check_agent_in_db(agent_id):
    """Vérifier directement dans Cosmos DB"""
    try:
        item = container.read_item(item=agent_id, partition_key=agent_id)

        print("="*70)
        print(f"🔍 Agent {agent_id} dans Cosmos DB")
        print("="*70)

        print(f"\navatar_character: {repr(item.get('avatar_character'))}")
        print(f"avatar_style: {repr(item.get('avatar_style'))}")
        print(f"Type de avatar_style: {type(item.get('avatar_style'))}")
        print(f"Clé 'avatar_style' existe: {'avatar_style' in item}")

        # Test si c'est la chaîne "None"
        avatar_style_val = item.get('avatar_style')
        if avatar_style_val == "None":
            print(f"\n⚠️  PROBLÈME TROUVÉ: avatar_style contient la CHAÎNE 'None' !")
            print(f"   C'est différent de None (Python) ou null (JSON)")
        elif avatar_style_val is None:
            print(f"\n✅ avatar_style est None (Python) - normal")
        elif 'avatar_style' not in item:
            print(f"\n✅ Clé avatar_style n'existe pas - normal")
        else:
            print(f"\n⚠️  Valeur inattendue: {repr(avatar_style_val)}")

        print(f"\n📋 Toutes les clés dans l'item:")
        for key in sorted(item.keys()):
            if 'avatar' in key.lower() or 'style' in key.lower():
                print(f"   {key}: {repr(item[key])}")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Agent adrian
    agent_id = "7d78514a-b7ec-462d-84c5-26c6e7d2b00c"
    check_agent_in_db(agent_id)
