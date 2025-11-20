"""
Script pour trouver des documents avec des champs complets
"""
from configuration.cosmos_config import get_call_history_container
import json

def main():
    container = get_call_history_container()
    
    # Récupérer tous les documents
    query = """
        SELECT TOP 50 *
        FROM c
        ORDER BY c._ts DESC
    """
    
    items = list(container.query_items(
        query=query, 
        enable_cross_partition_query=True
    ))
    
    print("=" * 100)
    print(f"ANALYSE DE {len(items)} DOCUMENTS")
    print("=" * 100)
    
    documents_with_messages = []
    documents_with_summary = []
    documents_with_interactions = []
    
    for item in items:
        has_messages = 'messages' in item and item['messages']
        has_summary = 'conversation_summary' in item and item['conversation_summary']
        has_interactions = 'interactions' in item and item['interactions']
        
        if has_messages:
            documents_with_messages.append(item)
        if has_summary:
            documents_with_summary.append(item)
        if has_interactions:
            documents_with_interactions.append(item)
    
    print(f"\n📊 STATISTIQUES:")
    print(f"   Total documents: {len(items)}")
    print(f"   Documents avec 'messages': {len(documents_with_messages)}")
    print(f"   Documents avec 'conversation_summary': {len(documents_with_summary)}")
    print(f"   Documents avec 'interactions': {len(documents_with_interactions)}")
    
    # Afficher les clés disponibles dans le premier document
    if items:
        print(f"\n📋 CLÉS DISPONIBLES DANS LE PREMIER DOCUMENT:")
        print(f"   {list(items[0].keys())}")
    
    # Si on trouve un document avec messages, l'afficher
    if documents_with_messages:
        print(f"\n✅ DOCUMENT AVEC MESSAGES TROUVÉ:")
        print(json.dumps(documents_with_messages[0], indent=2, default=str))
    elif documents_with_interactions:
        print(f"\n✅ DOCUMENT AVEC INTERACTIONS TROUVÉ:")
        print(json.dumps(documents_with_interactions[0], indent=2, default=str))
    else:
        print(f"\n❌ AUCUN DOCUMENT AVEC MESSAGES OU INTERACTIONS TROUVÉ")
        print(f"\n📄 STRUCTURE D'UN DOCUMENT TYPIQUE:")
        if items:
            print(json.dumps(items[0], indent=2, default=str))

if __name__ == "__main__":
    main()
