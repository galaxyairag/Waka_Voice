"""
Ajouter les tools dans session_config pour l'agent Samir
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from configuration.cosmos_config import get_agents_container
from tools import get_tools_definition
from datetime import datetime

# Récupérer l'agent
agents_container = get_agents_container()
query = "SELECT * FROM c WHERE c.id = '0dea0e1b-a3d7-466f-a697-87a4260e22e3'"
items = list(agents_container.query_items(query=query, enable_cross_partition_query=True))

if not items:
    print("❌ Agent non trouvé")
    sys.exit(1)

agent_config = items[0]
print(f"📊 Agent: {agent_config.get('agent_name', 'Sans nom')}")

# Récupérer les tools sélectionnés
selected_tools = agent_config.get('selected_tools', [])
print(f"🔧 Tools sélectionnés: {len(selected_tools)} - {selected_tools}")

if not selected_tools:
    print("⚠️ Aucun tool sélectionné, impossible de continuer")
    sys.exit(1)

# Mapping des noms
TOOL_NAME_MAPPING = {
    'weather': 'get_weather_forecast',
    'news': 'get_news',
    'email': 'send_email',
    'cv': 'create_cv',
    'knowledge_base': 'search_knowledge_base',
    'translator': 'translate_text',
    'health_advice': 'get_health_advice',
    'exercises': 'search_exercises',
    'dogs': 'search_dog_breeds',
    'search_web': 'search_web',
    'places': 'search_places',
    'flight_search': 'search_flights',
    'flight_booking': 'book_flight',
    'hotel_search': 'search_hotels',
    'hotel_booking': 'book_hotel',
    'currency': 'convert_currency',
    'calculator': 'calculate',
    'prayers': 'get_prayer_times',
    'pharmacy': 'find_pharmacy',
    'taxi': 'estimate_taxi_fare',
    'bus': 'get_bus_schedule',
    'schools': 'get_school_info',
    'government': 'get_government_service_info',
    'tax': 'calculate_tax',
    'end_conversation': 'end_conversation'
}

# Convertir les noms
mapped_tool_names = [TOOL_NAME_MAPPING.get(tool, tool) for tool in selected_tools]
print(f"🔄 Tools mappés: {mapped_tool_names}")

# Charger les définitions
all_tools = get_tools_definition()
tools_definitions = [tool for tool in all_tools if tool.get('name') in mapped_tool_names]

print(f"📦 {len(tools_definitions)} outils chargés")
for tool in tools_definitions:
    print(f"   - {tool.get('name')}")

# Ajouter dans session_config
if 'session_config' not in agent_config:
    agent_config['session_config'] = {}

agent_config['session_config']['tools'] = tools_definitions
agent_config['updated_at'] = datetime.utcnow().isoformat() + 'Z'

# Sauvegarder
print(f"\n💾 Sauvegarde dans Cosmos DB...")
agents_container.upsert_item(agent_config)
print(f"✅ Tools ajoutés dans session_config!")

# Vérification
print(f"\n🔍 Vérification:")
updated = agents_container.read_item(item=agent_config['id'], partition_key=agent_config['id'])
tools_in_config = updated.get('session_config', {}).get('tools', [])
print(f"   Tools dans session_config: {len(tools_in_config)} outils")
