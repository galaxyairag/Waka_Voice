"""
Script de test pour mettre à jour avatar_character dans Cosmos DB
"""
import sys
from configuration.cosmos_config import update_avatar_config, get_avatar_config

def test_update(agent_id, character, style='casual-sitting'):
    """Test de mise à jour d'avatar_character"""
    print(f"\n{'='*80}")
    print(f"TEST DE MISE À JOUR - Agent: {agent_id}")
    print(f"{'='*80}\n")

    try:
        # 1. Récupérer la config AVANT
        print("[1] AVANT MISE A JOUR:")
        before = get_avatar_config(agent_id)
        if not before:
            print(f"[ERROR] Agent {agent_id} non trouve")
            return

        print(f"   avatar_character: {before.get('avatar_character')}")
        print(f"   avatar_style: {before.get('avatar_style')}")

        # 2. Préparer les données à mettre à jour
        update_data = {
            'avatar_character': character,
            'avatar_style': style
        }
        print(f"\n[2] DONNEES A METTRE A JOUR:")
        print(f"   {update_data}")

        # 3. Effectuer la mise à jour
        print(f"\n[3] MISE A JOUR EN COURS...")
        result = update_avatar_config(agent_id, update_data)
        print(f"   [OK] Mise a jour effectuee")

        # 4. Récupérer la config APRÈS
        print(f"\n[4] APRES MISE A JOUR:")
        after = get_avatar_config(agent_id)
        print(f"   avatar_character: {after.get('avatar_character')}")
        print(f"   avatar_style: {after.get('avatar_style')}")

        # 5. Vérification
        print(f"\n[5] VERIFICATION:")
        if after.get('avatar_character') == character:
            print(f"   [OK] avatar_character correctement mis a jour")
        else:
            print(f"   [ERREUR] avatar_character PAS mis a jour! Attendu: {character}, Reel: {after.get('avatar_character')}")

        if after.get('avatar_style') == style:
            print(f"   [OK] avatar_style correctement mis a jour")
        else:
            print(f"   [ERREUR] avatar_style PAS mis a jour! Attendu: {style}, Reel: {after.get('avatar_style')}")

        print(f"\n{'='*80}")
        print("[OK] Test termine")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"[ERROR] Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_update_avatar_character.py <agent_id> <character> [style]")
        print("\nExemple:")
        print("  python test_update_avatar_character.py b0ad7dc3-9a2a-4ada-a919-9ef3624cfdac lisa casual-sitting")
        sys.exit(1)

    agent_id = sys.argv[1]
    character = sys.argv[2]
    style = sys.argv[3] if len(sys.argv) > 3 else 'casual-sitting'

    test_update(agent_id, character, style)
