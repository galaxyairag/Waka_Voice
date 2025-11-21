"""
Test de la configuration Voice Live avec accent africain
"""
from configuration.voice_live_config import VoiceLiveClient, AFRICAN_VOICE_STYLE_INSTRUCTIONS
from configuration.cosmos_config import get_agent_config

# Test 1 : Vérifier que les instructions SSML sont présentes
print("=" * 60)
print("TEST 1 : Instructions SSML pour accent africain")
print("=" * 60)
print(AFRICAN_VOICE_STYLE_INSTRUCTIONS)
print()

# Test 2 : Charger un agent et vérifier sa config
print("=" * 60)
print("TEST 2 : Configuration d'un agent existant")
print("=" * 60)

# Liste des agents à tester (remplacez par vos IDs d'agents)
agent_ids = [
    "eaa73603-562f-41b8-8733-f1b4899be0d0",  # Agent 1
    "6def1140-f0a7-42ee-a491-09cf828b9712",  # Agent 2
]

for agent_id in agent_ids:
    try:
        agent_config = get_agent_config(agent_id)
        print(f"\n🤖 Agent : {agent_config.get('agent_name', 'Inconnu')}")
        print(f"   ID : {agent_id}")
        print(f"   Modèle : {agent_config.get('model_id', 'N/A')}")
        
        # Vérifier le flag african voice style
        use_african = agent_config.get('use_african_voice_style', True)
        print(f"   ✅ Style africain activé : {use_african}")
        
        # Construire la session config
        client = VoiceLiveClient(agent_config.get('model_id', 'gpt-4o-realtime-preview'))
        session_config = client.get_session_config(agent_config)
        
        # Vérifier que les instructions contiennent SSML
        instructions = session_config.get('instructions', '')
        has_ssml = '<speak' in instructions and '<prosody' in instructions
        
        print(f"   {'✅' if has_ssml else '❌'} Instructions contiennent SSML : {has_ssml}")
        
        if has_ssml:
            # Montrer un extrait
            ssml_start = instructions.find('<speak')
            if ssml_start > 0:
                excerpt = instructions[ssml_start-50:ssml_start+200]
                print(f"\n   Extrait des instructions :")
                print(f"   {excerpt[:100]}...")
        else:
            print(f"\n   ⚠️ ATTENTION : Les instructions ne contiennent pas de SSML !")
            print(f"   Début des instructions : {instructions[:200]}...")
            
    except Exception as e:
        print(f"   ❌ Erreur : {e}")

print("\n" + "=" * 60)
print("TEST TERMINÉ")
print("=" * 60)
