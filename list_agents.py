"""Liste tous les agents dans Cosmos DB"""
from configuration.cosmos_config import get_agents_container

container = get_agents_container()

# Lister tous les agents
query = "SELECT c.id, c.agent_name, c.model_id FROM c"
agents = list(container.query_items(query=query, enable_cross_partition_query=True))

print(f"\n📋 {len(agents)} agents trouvés :\n")
for agent in agents:
    print(f"  - {agent.get('agent_name', 'Sans nom'):30} | ID: {agent['id']} | Modèle: {agent.get('model_id', 'N/A')}")
