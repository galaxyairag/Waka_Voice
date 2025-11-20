#!/usr/bin/env python3
"""
Test de l'endpoint /api/dashboard/summary
"""
import requests
import json

url = "http://localhost:5000/api/dashboard/summary"

try:
    print(f"🔍 Test de l'endpoint: {url}")
    print("-" * 60)
    
    response = requests.get(url, timeout=10)
    
    print(f"\n✅ Status Code: {response.status_code}")
    print(f"✅ Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 Réponse JSON:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Vérifier les champs attendus
        print(f"\n🔎 Analyse des données:")
        print(f"  - total_conversations: {data.get('total_conversations', 'MANQUANT')}")
        print(f"  - total_cost: {data.get('total_cost', 'MANQUANT')}")
        print(f"  - total_cost_usd: {data.get('total_cost_usd', 'MANQUANT')}")
    else:
        print(f"\n❌ Erreur: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ Impossible de se connecter au serveur. Est-il démarré sur http://localhost:5000 ?")
except Exception as e:
    print(f"❌ Erreur: {e}")
