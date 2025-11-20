"""
Script pour vérifier le nombre de tools dans l'agent "Agent Avatar GPT Realtime Mini"
"""
import os
import sys
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

load_dotenv()

# Configuration Cosmos DB
COSMOS_ENDPOINT = os.getenv('COSMOS_ENDPOINT')
COSMOS_KEY = os.getenv('COSMOS_KEY')
DATABASE_NAME = os.getenv('COSMOS_DATABASE_NAME', 'ChatDB')
CONTAINER_NAME = os.getenv('COSMOS_CONTAINER_NAME', 'Conversations')

if not COSMOS_ENDPOINT or not COSMOS_KEY:
    print("❌ COSMOS_ENDPOINT ou COSMOS_KEY manquant dans .env")
    sys.exit(1)

# Connexion Cosmos DB
client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)

# Requête pour trouver l'agent
query = """
SELECT c.agent_id, c.agent_name, c.model_config.model, c.selected_tools,
       ARRAY_LENGTH(c.selected_tools) as tool_count
FROM c 
WHERE c.type = 'agent_config'
  AND CONTAINS(c.agent_name, 'Agent Avatar GPT Realtime Mini')
"""

print("🔍 Recherche de l'agent 'Agent Avatar GPT Realtime Mini'...\n")

items = list(container.query_items(query=query, enable_cross_partition_query=True))

if not items:
    print("❌ Agent non trouvé")
    sys.exit(1)

for item in items:
    print(f"✅ Agent trouvé:")
    print(f"   - ID: {item.get('agent_id')}")
    print(f"   - Nom: {item.get('agent_name')}")
    print(f"   - Modèle: {item.get('model_config', {}).get('model')}")
    print(f"   - Nombre de tools: {item.get('tool_count')}")
    print(f"\n📋 Liste des tools configurés:")
    
    tools = item.get('selected_tools', [])
    if tools:
        for i, tool in enumerate(tools, 1):
            print(f"   {i:2d}. {tool}")
    else:
        print("   (aucun tool)")
