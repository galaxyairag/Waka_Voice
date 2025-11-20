"""
Script pour extraire un document Cosmos et vérifier les champs disponibles
pour le dashboard production
"""
from configuration.cosmos_config import get_call_history_container
import json

def main():
    container = get_call_history_container()
    
    # Récupérer un document récent complété
    query = """
        SELECT TOP 1 *
        FROM c
        WHERE c.status = 'completed'
        ORDER BY c._ts DESC
    """
    
    items = list(container.query_items(
        query=query, 
        enable_cross_partition_query=True
    ))
    
    if not items:
        print("❌ Aucun document avec status='completed' trouvé")
        return
    
    doc = items[0]
    
    print("=" * 80)
    print("DOCUMENT COSMOS - STRUCTURE COMPLÈTE")
    print("=" * 80)
    print(json.dumps(doc, indent=2, default=str))
    print("=" * 80)
    print("\nCHAMPS CLÉS POUR PRODUCTION:")
    print(f"  - call_id: {doc.get('call_id')}")
    print(f"  - agent_id: {doc.get('agent_id')}")
    print(f"  - model: {doc.get('model')}")
    print(f"  - model_family: {doc.get('model_family')}")
    print(f"  - status: {doc.get('status')}")
    print(f"  - duration_minutes: {doc.get('duration_minutes')}")
    print(f"  - cost: {doc.get('cost')}")
    print(f"  - tokens: {doc.get('tokens')}")
    print(f"  - interactions_count: {doc.get('interactions_count')}")
    print(f"  - _ts: {doc.get('_ts')}")
    print("=" * 80)
    
    # Vérifier si tous les champs nécessaires existent
    required_fields = ['duration_minutes', 'cost', 'model', 'interactions_count']
    missing = [f for f in required_fields if f not in doc or doc.get(f) is None]
    
    if missing:
        print(f"\n⚠️  CHAMPS MANQUANTS: {missing}")
    else:
        print("\n✅ Tous les champs requis sont présents")

if __name__ == "__main__":
    main()
