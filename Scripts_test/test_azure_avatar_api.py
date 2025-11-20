"""
Script de test pour l'API Azure Avatar
"""
import os
import requests
from dotenv import load_dotenv
import json

# Charger les variables d'environnement
load_dotenv()

speech_key = os.getenv('AZURE_SPEECH_KEY')
speech_region = os.getenv('AZURE_SPEECH_REGION', 'eastus2')

print(f"🔍 Configuration:")
print(f"   Région: {speech_region}")
print(f"   Clé: {'***' + speech_key[-4:] if speech_key else 'NON CONFIGURÉE'}")
print()

# URL de l'API Azure Avatar
api_url = f"https://{speech_region}.api.cognitive.microsoft.com/avatar/prebuilt/v1/models"

headers = {
    'Ocp-Apim-Subscription-Key': speech_key,
    'Content-Type': 'application/json'
}

print(f"🌐 URL API: {api_url}")
print()

try:
    print("📡 Appel de l'API Azure Avatar...")
    response = requests.get(api_url, headers=headers, timeout=10)
    
    print(f"✅ Status Code: {response.status_code}")
    print(f"📦 Headers Response:")
    for key, value in response.headers.items():
        print(f"   {key}: {value}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Réponse JSON reçue")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Analyser les avatars
        avatars = data.get('value', [])
        print(f"\n📊 Nombre d'avatars: {len(avatars)}")
        
        for i, avatar in enumerate(avatars, 1):
            print(f"\n--- Avatar {i} ---")
            print(f"ID: {avatar.get('id', 'N/A')}")
            print(f"Name: {avatar.get('name', 'N/A')}")
            print(f"Character: {avatar.get('character', 'N/A')}")
            
            properties = avatar.get('properties', {})
            print(f"Properties:")
            print(f"  - Gender: {properties.get('gender', 'N/A')}")
            print(f"  - Preview Image URL: {properties.get('previewImageUrl', 'N/A')}")
            print(f"  - Thumbnail URL: {properties.get('thumbnailUrl', 'N/A')}")
            print(f"  - Preview Video URL: {properties.get('previewVideoUrl', 'N/A')}")
            
    else:
        print(f"❌ Erreur HTTP {response.status_code}")
        print(f"📄 Response Text: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Erreur lors de l'appel API: {e}")
except Exception as e:
    print(f"❌ Erreur inattendue: {e}")
