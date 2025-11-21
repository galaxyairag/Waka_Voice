"""
Script pour afficher la structure du champ conversation
"""
from configuration.cosmos_config import get_call_history_container
import json

def main():
    container = get_call_history_container()
    
    # Récupérer un document
    query = """
        SELECT TOP 1 *
        FROM c
        ORDER BY c._ts DESC
    """
    
    items = list(container.query_items(
        query=query, 
        enable_cross_partition_query=True
    ))
    
    if items:
        doc = items[0]
        print("=" * 100)
        print("STRUCTURE DU CHAMP 'conversation'")
        print("=" * 100)
        
        conversation = doc.get('conversation')
        
        if conversation:
            print(f"\n📋 Type: {type(conversation)}")
            print(f"📋 Clés disponibles dans 'conversation': {list(conversation.keys()) if isinstance(conversation, dict) else 'N/A'}")
            
            # Afficher quelques messages
            messages = conversation.get('messages', [])
            print(f"\n📨 Nombre de messages: {len(messages)}")
            
            if messages:
                print(f"\n📝 EXEMPLE DE MESSAGE:")
                print(json.dumps(messages[0], indent=2, default=str))
            
            # Vérifier s'il y a un résumé
            summary = conversation.get('conversation_summary') or conversation.get('summary')
            print(f"\n📄 Résumé présent: {'Oui' if summary else 'Non'}")
            if summary:
                print(f"📄 Résumé: {summary}")
        else:
            print("\n❌ Aucun champ 'conversation' trouvé")
            print(f"📋 Clés disponibles dans le document: {list(doc.keys())}")

if __name__ == "__main__":
    main()
