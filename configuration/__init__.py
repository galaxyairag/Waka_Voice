"""
Configuration module for Waka Voice Burkina
"""

from .cosmos_config import (
    get_cosmos_client,
    get_database,
    get_agents_container,
    get_call_history_container,
    get_token_consumption_container,
    get_instructions_container,
    save_agent_config,
    get_agent_config,
    update_agent_status,
    list_agents_by_status
)
from .voice_live_config import (
    get_voice_live_client,
    list_available_models,
    VoiceLiveClient
)

__all__ = [
    # Cosmos DB
    'get_cosmos_client',
    'get_database',
    'get_agents_container',
    'get_call_history_container',
    'get_token_consumption_container',
    'get_instructions_container',
    'save_agent_config',
    'get_agent_config',
    'update_agent_status',
    'list_agents_by_status',
    # Voice Live
    'get_voice_live_client',
    'list_available_models',
    'VoiceLiveClient'
]
