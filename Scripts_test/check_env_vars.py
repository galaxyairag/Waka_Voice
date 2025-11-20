"""
Script pour vérifier les variables d'environnement Voice Live
"""
import os
from dotenv import load_dotenv

# Charger .env
load_dotenv()

print("=" * 60)
print("VÉRIFICATION DES VARIABLES D'ENVIRONNEMENT")
print("=" * 60)

print("\n🎤 VOICE LIVE (Realtime API)")
print("-" * 60)
print(f"VOICE_LIVE_KEY: {os.getenv('VOICE_LIVE_KEY', 'NOT SET')[:20]}...")
print(f"VOICE_LIVE_NAME: {os.getenv('VOICE_LIVE_NAME', 'NOT SET')}")
print(f"VOICE_LIVE_ENDPOINT: {os.getenv('VOICE_LIVE_ENDPOINT', 'NOT SET')}")
print(f"VOICE_LIVE_ENDPOINT_TYPE: {os.getenv('VOICE_LIVE_ENDPOINT_TYPE', 'NOT SET')}")

print("\n🎙️ PERSONAL VOICE")
print("-" * 60)
print(f"PERSONAL_VOICE_KEY: {os.getenv('PERSONAL_VOICE_KEY', 'NOT SET')[:20]}...")
print(f"PERSONAL_VOICE_REGION: {os.getenv('PERSONAL_VOICE_REGION', 'NOT SET')}")

print("\n🎭 AVATAR")
print("-" * 60)
print(f"AVATAR_SPEECH_KEY: {os.getenv('AVATAR_SPEECH_KEY', 'NOT SET')[:20]}...")
print(f"AVATAR_SPEECH_REGION: {os.getenv('AVATAR_SPEECH_REGION', 'NOT SET')}")

print("\n🔄 FALLBACK (variables génériques)")
print("-" * 60)
print(f"AZURE_SPEECH_KEY: {os.getenv('AZURE_SPEECH_KEY', 'NOT SET')[:20]}...")
print(f"AZURE_SPEECH_NAME: {os.getenv('AZURE_SPEECH_NAME', 'NOT SET')}")
print(f"AZURE_SPEECH_REGION: {os.getenv('AZURE_SPEECH_REGION', 'NOT SET')}")
print(f"AZURE_SPEECH_ENDPOINT: {os.getenv('AZURE_SPEECH_ENDPOINT', 'NOT SET')}")

# Test construction WebSocket URL
print("\n🌐 URL WEBSOCKET CONSTRUITE")
print("-" * 60)

voice_live_name = os.getenv('VOICE_LIVE_NAME') or os.getenv('AZURE_SPEECH_NAME')
voice_live_type = os.getenv('VOICE_LIVE_ENDPOINT_TYPE', 'cognitiveservices')

if voice_live_type == 'services':
    ws_url = f"wss://{voice_live_name}.services.ai.azure.com/voice-live/realtime"
else:
    ws_url = f"wss://{voice_live_name}.cognitiveservices.azure.com/voice-live/realtime"

print(f"WebSocket URL: {ws_url}")

print("\n" + "=" * 60)

# Vérification
if voice_live_name == 'jcmortagagesf85tlw':
    print("✅ Configuration correcte - Sweden Central")
elif voice_live_name == 'usageinterne-0509-resource':
    print("❌ ERREUR - Utilise encore East US 2 au lieu de Sweden Central!")
    print("\nVERIFIEZ:")
    print("1. Que le fichier .env contient bien VOICE_LIVE_NAME=jcmortagagesf85tlw")
    print("2. Que vous avez relancé le serveur Flask après modification du .env")
else:
    print(f"⚠️ Resource name inattendue: {voice_live_name}")
    
print("=" * 60)
