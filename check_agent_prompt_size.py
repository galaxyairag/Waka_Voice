"""
Vérifier la taille du prompt de l'agent Samir
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from configuration.cosmos_config import get_agents_container
import json

# Récupérer l'agent
agents_container = get_agents_container()
query = "SELECT * FROM c WHERE c.id = '0dea0e1b-a3d7-466f-a697-87a4260e22e3'"
items = list(agents_container.query_items(query=query, enable_cross_partition_query=True))

if items:
    config = items[0]
    session_config = config.get('session_config', {})
    instructions = session_config.get('instructions', '')
    tools = session_config.get('tools', [])
    
    print(f"📊 Agent: {config.get('agent_name')}")
    print(f"\n📝 Instructions: {len(instructions)} chars (~{len(instructions)//4} tokens)")
    print(f"🔧 Tools: {len(tools)} outils")
    
    tools_json = json.dumps(tools, ensure_ascii=False)
    print(f"📦 Tools JSON: {len(tools_json)} chars (~{len(tools_json)//4} tokens)")
    
    total_tokens = (len(instructions) + len(tools_json)) // 4
    print(f"\n💰 TOTAL ESTIMÉ: ~{total_tokens} tokens")
    
    if total_tokens > 4000:
        print(f"\n⚠️ WARNING: Prompt trop long! Voice Live limite: 4096 tokens")
    
    # Afficher début des instructions
    print(f"\n📄 Instructions (premiers 300 chars):")
    print("=" * 60)
    print(instructions[:300])
    print("...")
else:
    print("❌ Agent non trouvé")
