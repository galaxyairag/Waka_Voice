"""
Test tous les endpoints de l'API du dashboard production
"""
import requests
import json

BASE_URL = "http://localhost:5000"
PERIOD = 30
PRICE = 0.1

endpoints = [
    f"/api/production/conversations-by-day?period={PERIOD}",
    f"/api/production/duration-stats-by-day?period={PERIOD}",
    f"/api/production/interactions-stats?period={PERIOD}",
    f"/api/production/cost-breakdown-by-type?period={PERIOD}",
    f"/api/production/cost-distribution?period={PERIOD}",
    f"/api/production/financial-evolution?period={PERIOD}&price={PRICE}",
    f"/api/production/margin-evolution?period={PERIOD}&price={PRICE}",
]

print("=" * 80)
print("TEST DES ENDPOINTS DE L'API DASHBOARD PRODUCTION")
print("=" * 80)

for endpoint in endpoints:
    url = BASE_URL + endpoint
    print(f"\n📍 {endpoint}")
    print("-" * 80)
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            
            # Afficher un résumé des données
            if 'labels' in data:
                print(f"   Labels: {len(data['labels'])} éléments")
                if data['labels']:
                    print(f"   Premier label: {data['labels'][0]}")
                    print(f"   Dernier label: {data['labels'][-1]}")
            
            if 'data' in data:
                print(f"   Data: {len(data['data'])} éléments")
                if data['data']:
                    print(f"   Première valeur: {data['data'][0]}")
                    total = sum(data['data']) if isinstance(data['data'][0], (int, float)) else 'N/A'
                    print(f"   Total: {total}")
            
            # Afficher toutes les clés
            print(f"   Clés disponibles: {list(data.keys())}")
            
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"   Erreur: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la requête: {e}")

print("\n" + "=" * 80)
print("TEST TERMINÉ")
print("=" * 80)
