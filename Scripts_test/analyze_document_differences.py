"""
Script pour analyser les différences entre documents complets et incomplets
"""
from configuration.cosmos_config import get_call_history_container
import json

def main():
    container = get_call_history_container()
    
    # Récupérer 20 documents récents
    query = """
        SELECT TOP 20 *
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
    
    complete_docs = []
    minimal_docs = []
    
    for item in items:
        # Un document complet a messages ET conversation_summary
        if 'messages' in item and item.get('messages') and 'conversation_summary' in item:
            complete_docs.append(item)
        else:
            minimal_docs.append(item)
    
    print(f"\n📊 STATISTIQUES:")
    print(f"   Documents complets: {len(complete_docs)}")
    print(f"   Documents minimaux: {len(minimal_docs)}")
    
    # Analyser les documents complets
    if complete_docs:
        print(f"\n✅ EXEMPLE DE DOCUMENT COMPLET:")
        doc = complete_docs[0]
        print(f"   ID: {doc.get('id')}")
        print(f"   call_id: {doc.get('call_id')}")
        print(f"   status: {doc.get('status')}")
        print(f"   start_time: {doc.get('start_time', 'N/A')}")
        print(f"   end_time: {doc.get('end_time', 'N/A')}")
        print(f"   duration_minutes: {doc.get('duration_minutes', 'N/A')}")
        print(f"   Nombre de messages: {len(doc.get('messages', []))}")
        print(f"   Résumé présent: {'Oui' if doc.get('conversation_summary') else 'Non'}")
        print(f"   Clés disponibles: {list(doc.keys())}")
    
    # Analyser les documents minimaux
    if minimal_docs:
        print(f"\n❌ EXEMPLE DE DOCUMENT MINIMAL:")
        doc = minimal_docs[0]
        print(f"   ID: {doc.get('id')}")
        print(f"   call_id: {doc.get('call_id')}")
        print(f"   status: {doc.get('status')}")
        print(f"   start_time: {doc.get('start_time', 'N/A')}")
        print(f"   end_time: {doc.get('end_time', 'N/A')}")
        print(f"   duration_minutes: {doc.get('duration_minutes', 'N/A')}")
        print(f"   Nombre de messages: {len(doc.get('messages', []))}")
        print(f"   Résumé présent: {'Oui' if doc.get('conversation_summary') else 'Non'}")
        print(f"   Clés disponibles: {list(doc.keys())}")
    
    # Vérifier les différences de structure
    if complete_docs and minimal_docs:
        print(f"\n🔍 DIFFÉRENCES CLÉS:")
        complete_keys = set(complete_docs[0].keys())
        minimal_keys = set(minimal_docs[0].keys())
        
        keys_only_in_complete = complete_keys - minimal_keys
        keys_only_in_minimal = minimal_keys - complete_keys
        
        if keys_only_in_complete:
            print(f"   Clés présentes seulement dans documents complets:")
            for key in sorted(keys_only_in_complete):
                print(f"      - {key}")
        
        if keys_only_in_minimal:
            print(f"   Clés présentes seulement dans documents minimaux:")
            for key in sorted(keys_only_in_minimal):
                print(f"      - {key}")

if __name__ == "__main__":
    main()
