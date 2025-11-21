"""
Script pour vérifier les champs messages et conversation_summary
"""
from configuration.cosmos_config import get_call_history_container
import json

def main():
    container = get_call_history_container()
    
    # Récupérer les 5 documents les plus récents
    query = """
        SELECT TOP 5 c.id, c.call_id, c.agent_name, c.status, c.messages, c.conversation_summary, c.start_time
        FROM c
        ORDER BY c._ts DESC
    """
    
    items = list(container.query_items(
        query=query, 
        enable_cross_partition_query=True
    ))
    
    if not items:
        print("❌ Aucun document trouvé")
        return
    
    print("=" * 100)
    print(f"ANALYSE DE {len(items)} DOCUMENTS RÉCENTS")
    print("=" * 100)
    
    for i, doc in enumerate(items, 1):
        print(f"\n📄 DOCUMENT {i}:")
        print(f"   ID: {doc.get('id', 'N/A')}")
        print(f"   Call ID: {doc.get('call_id', 'N/A')}")
        print(f"   Agent Name: {doc.get('agent_name', 'N/A')}")
        print(f"   Status: {doc.get('status', 'N/A')}")
        print(f"   Start Time: {doc.get('start_time', 'N/A')}")
        
        # Vérifier le champ messages
        messages = doc.get('messages')
        if messages is None:
            print("   ❌ Champ 'messages': ABSENT")
        elif isinstance(messages, list):
            print(f"   ✅ Messages: {len(messages)} messages trouvés")
            if len(messages) > 0:
                print(f"      Premier message: {messages[0].get('role', 'N/A')} - {messages[0].get('content', 'N/A')[:50]}...")
        else:
            print(f"   ⚠️  Messages: Type inattendu ({type(messages)})")
        
        # Vérifier le champ conversation_summary
        summary = doc.get('conversation_summary')
        if summary is None:
            print("   ❌ Champ 'conversation_summary': ABSENT")
        elif summary:
            print(f"   ✅ Résumé: '{summary}'")
        else:
            print("   ⚠️  Résumé: Vide")
        
        print("-" * 100)
    
    # Afficher un document complet pour analyse
    print("\n" + "=" * 100)
    print("STRUCTURE COMPLÈTE DU PREMIER DOCUMENT:")
    print("=" * 100)
    print(json.dumps(items[0], indent=2, default=str))
    print("=" * 100)

if __name__ == "__main__":
    main()
