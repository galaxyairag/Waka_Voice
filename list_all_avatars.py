"""
Script pour lister tous les avatars dans Cosmos DB
"""
import os
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration
COSMOS_URI = os.getenv("COSMOS_URI")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = "ConversationsDB"
CONTAINER_NAME = "AvatarConfigurations"

if not COSMOS_URI or not COSMOS_KEY:
    print("❌ COSMOS_URI et COSMOS_KEY doivent être définis dans .env")
    exit(1)

# Connexion à Cosmos DB
client = CosmosClient(COSMOS_URI, credential=COSMOS_KEY)
database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)

# Requête pour lister tous les avatars
query = "SELECT c.id, c.agent_id, c.agent_name, c.avatar_character, c.avatar_style FROM c"
items = list(container.query_items(query=query, enable_cross_partition_query=True))

print("\n" + "="*80)
print(f"📋 LISTE DE TOUS LES AVATARS ({len(items)} trouvés)")
print("="*80 + "\n")

for i, item in enumerate(items, 1):
    print(f"{i}. Agent: {item.get('agent_name', 'Sans nom')}")
    print(f"   - ID: {item.get('id')}")
    print(f"   - Agent ID: {item.get('agent_id')}")
    print(f"   - Character: {item.get('avatar_character')}")
    
    if 'avatar_style' in item and item['avatar_style']:
        print(f"   - Style: {item.get('avatar_style')}")
    else:
        print(f"   - Style: ✅ ABSENTE/VIDE")
    print()

print("="*80 + "\n")
