"""
Script pour corriger les modalities des agents
Remplace ["text"] par ["text", "audio"] pour permettre les réponses vocales
"""
from configuration.cosmos_config import get_agents_container

def fix_agent_modalities():
    agents_container = get_agents_container()
    
    # Récupérer tous les agents
    query = "SELECT * FROM c"
    agents = list(agents_container.query_items(query=query, enable_cross_partition_query=True))
    
    print(f"\n📋 {len(agents)} agent(s) trouvé(s)\n")
    
    fixed_count = 0
    for agent in agents:
        agent_id = agent.get('id', 'unknown')
        agent_name = agent.get('agent_name', 'Unknown')
        current_modalities = agent.get('modalities', [])
        
        print(f"🤖 Agent: {agent_name} ({agent_id})")
        print(f"   Modalities actuelles: {current_modalities}")
        
        # Corriger si nécessaire
        if current_modalities == ["text"]:
            agent['modalities'] = ["text", "audio"]
            agents_container.upsert_item(agent)
            print(f"   ✅ Corrigé → ['text', 'audio']")
            fixed_count += 1
        elif "audio" not in current_modalities:
            agent['modalities'] = ["text", "audio"]
            agents_container.upsert_item(agent)
            print(f"   ✅ Corrigé → ['text', 'audio']")
            fixed_count += 1
        else:
            print(f"   ✔️  Déjà correct")
        print()
    
    print(f"\n{'='*50}")
    print(f"✅ {fixed_count} agent(s) corrigé(s)")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    fix_agent_modalities()
