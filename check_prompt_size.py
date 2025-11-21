"""
Vérifier la taille du system prompt de l'agent
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from azure.cosmos import CosmosClient
from dotenv import load_dotenv

load_dotenv()

COSMOS_URI = os.getenv('COSMOS_URI')
COSMOS_KEY = os.getenv('COSMOS_KEY')
DATABASE_NAME = os.getenv('COSMOS_DATABASE_NAME', 'ConversationsDB')

client = CosmosClient(COSMOS_URI, credential=COSMOS_KEY)
database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client('AvatarConfigurations')

# Récupérer l'agent
query = "SELECT * FROM c WHERE c.agent_id = '88a01513-3b68-4864-9681-35b06bb7764a'"
items = list(container.query_items(query=query, enable_cross_partition_query=True))

if items:
    config = items[0]
    system_prompt = config.get('system_prompt', '')
    instructions = config.get('instructions', '')
    
    print(f"📊 Analyse de l'agent: {config.get('agent_name')}")
    print(f"\n📝 System Prompt:")
    print(f"   - Longueur: {len(system_prompt)} caractères")
    print(f"   - Tokens estimés: ~{len(system_prompt) // 4}")
    
    print(f"\n📋 Instructions:")
    print(f"   - Longueur: {len(instructions)} caractères")
    print(f"   - Tokens estimés: ~{len(instructions) // 4}")
    
    print(f"\n🔧 Tools: {len(config.get('selected_tools', []))}")
    
    total_chars = len(system_prompt) + len(instructions)
    print(f"\n💰 Total prompt:")
    print(f"   - {total_chars} caractères")
    print(f"   - ~{total_chars // 4} tokens")
    
    print(f"\n🎯 Avec 25 tools (~3750 tokens) + prompt (~{total_chars // 4} tokens) = ~{(total_chars // 4) + 3750} tokens")
    
    # Afficher un extrait du prompt
    print(f"\n📄 Début du system_prompt:")
    print("=" * 60)
    print(system_prompt[:500])
    print("...")
else:
    print("❌ Agent non trouvé")
