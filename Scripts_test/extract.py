import os
import sys
import json

# Assure que la racine du projet est dans sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from configuration.cosmos_config import get_call_history_container


def main():
    container = get_call_history_container()

    # 1) On liste quelques conversations récentes
    query = """
        SELECT TOP 20 c.call_id, c.started_at, c.ended_at, c.status, c.duration_minutes
        FROM c
        WHERE IS_DEFINED(c.call_id)
        ORDER BY c._ts DESC
    """

    items = list(container.query_items(
        query=query,
        enable_cross_partition_query=True,
    ))

    if not items:
        print("Aucun document trouvé dans l'historique.")
        return

    print("Conversations récentes :")
    for idx, it in enumerate(items):
        print(
            f"[{idx}] call_id={it.get('call_id')} "
            f"status={it.get('status')} "
            f"durée={it.get('duration_minutes')} "
            f"start={it.get('started_at')}"
        )

    # 2) L'utilisateur choisit un index
    try:
        choice = int(input("Choisis un index pour voir le document complet : "))
    except ValueError:
        print("Index invalide.")
        return

    if choice < 0 or choice >= len(items):
        print("Index hors limite.")
        return

    selected_call_id = items[choice].get("call_id")

    # 3) On recharge le document complet pour ce call_id
    query_doc = """
        SELECT *
        FROM c
        WHERE c.call_id = @call_id
    """
    params = [{"name": "@call_id", "value": selected_call_id}]

    docs = list(container.query_items(
        query=query_doc,
        parameters=params,
        enable_cross_partition_query=True,
    ))

    if not docs:
        print(f"Aucun document trouvé pour call_id = {selected_call_id}")
        return

    doc = docs[0]
    print(f"\n✅ Document complet pour call_id = {selected_call_id}")
    print("-" * 80)
    print(json.dumps(doc, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()