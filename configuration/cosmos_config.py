"""
Azure Cosmos DB Configuration
Initialise les containers pour la gestion des agents Voice Live
"""

import os
import logging
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from dotenv import load_dotenv
import requests
from datetime import datetime, timezone

# Charger les variables d'environnement
load_dotenv()

# Configuration du logger
logger = logging.getLogger(__name__)

# Variables de configuration Cosmos DB
COSMOS_URI = os.getenv('COSMOS_URI')
COSMOS_KEY = os.getenv('COSMOS_KEY')
COSMOS_DATABASE_NAME = os.getenv('COSMOS_DATABASE_NAME', 'ConversationsDB')

# Containers définis dans .env
CALL_HISTORY_CONTAINER = os.getenv('COSMOS_CALL_HISTORY_CONTAINER', 'CallHistory')
CALL_HISTORY_PARTITION_KEY = os.getenv('COSMOS_CALL_HISTORY_PARTITION_KEY', '/call_id')

TOKEN_CONSUMPTION_CONTAINER = os.getenv('COSMOS_TOKEN_CONSUMPTION_CONTAINER', 'TokenConsumption')
TOKEN_CONSUMPTION_PARTITION_KEY = os.getenv('COSMOS_TOKEN_CONSUMPTION_PARTITION_KEY', '/user_id')

INSTRUCTIONS_CONTAINER = os.getenv('COSMOS_INSTRUCTIONS_CONTAINER', 'ModelInstructions')
INSTRUCTIONS_PARTITION_KEY = os.getenv('COSMOS_INSTRUCTIONS_PARTITION_KEY', '/id')

# Azure OpenAI pour résumés de conversations
AZURE_OPENAI_SUMMARY_ENDPOINT = os.getenv('AZURE_OPENAI_SUMMARY_ENDPOINT')
AZURE_OPENAI_SUMMARY_KEY = os.getenv('AZURE_OPENAI_SUMMARY_KEY')
AZURE_OPENAI_SUMMARY_DEPLOYMENT = os.getenv('AZURE_OPENAI_SUMMARY_DEPLOYMENT')
AZURE_OPENAI_SUMMARY_API_VERSION = os.getenv('AZURE_OPENAI_SUMMARY_API_VERSION', '2024-08-01-preview')

# Container pour les configurations d'agents
AGENTS_CONTAINER_NAME = 'AgentConfigurations'
AGENTS_PARTITION_KEY = '/agent_id'

# Container pour les configurations d'avatars
AVATAR_CONTAINER_NAME = 'AvatarConfigurations'
AVATAR_PARTITION_KEY = '/agent_id'

# Singletons pour le client Cosmos et les containers
_cosmos_client = None
_database = None
_agents_container = None
_avatar_container = None
_call_history_container = None
_token_consumption_container = None
_instructions_container = None


def get_cosmos_client():
    """
    Retourne le client Cosmos DB (singleton)
    """
    global _cosmos_client
    
    if _cosmos_client is None:
        if not COSMOS_URI or not COSMOS_KEY:
            raise ValueError("COSMOS_URI et COSMOS_KEY doivent être définis dans .env")
        
        _cosmos_client = CosmosClient(COSMOS_URI, credential=COSMOS_KEY)
        logger.info("✅ Client Cosmos DB initialisé")
    
    return _cosmos_client


def get_database():
    """
    Retourne la base de données Cosmos DB
    Crée la database si elle n'existe pas
    """
    global _database
    
    if _database is None:
        client = get_cosmos_client()
        
        try:
            _database = client.create_database_if_not_exists(id=COSMOS_DATABASE_NAME)
            logger.info(f"✅ Database '{COSMOS_DATABASE_NAME}' prête")
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"❌ Erreur lors de la création de la database: {e}")
            raise
    
    return _database


def get_agents_container():
    """
    Retourne le container pour les configurations d'agents
    Crée le container si il n'existe pas
    
    Structure des documents:
    {
        "id": "uuid",
        "agent_id": "uuid",  # Partition key
        "agent_name": "Assistant Waka",
        "status": "en_cours_de_validation" | "actif" | "inactif" | "archive",
        "created_at": "2025-11-16T10:30:00Z",
        "updated_at": "2025-11-16T10:30:00Z",
        "config_type": "personnalise" | "template",
        "model_id": "gpt-4o-realtime-preview",
        "model_name": "GPT-4o Realtime Preview",
        "voice_config": {
            "voice_name": "fr-FR-DeniseNeural",
            "voice_speed": 1.0,
            "voice_pitch": 0,
            ...
        },
        "session_config": {
            "input_audio_sampling_rate": 24000,
            "turn_detection": {...},
            ...
        },
        "selected_tools": ["weather", "email", "search_web"],
        "system_prompt": "...",
        "metadata": {
            "created_by": "user_id",
            "last_tested_at": "2025-11-16T11:00:00Z",
            "test_count": 5,
            "version": 1
        }
    }
    """
    global _agents_container
    
    if _agents_container is None:
        database = get_database()
        
        try:
            # Créer le container avec la partition key
            # Note: offer_throughput n'est pas supporté sur les comptes serverless
            _agents_container = database.create_container_if_not_exists(
                id=AGENTS_CONTAINER_NAME,
                partition_key=PartitionKey(path=AGENTS_PARTITION_KEY)
            )
            logger.info(f"✅ Container '{AGENTS_CONTAINER_NAME}' prêt")
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"❌ Erreur lors de la création du container: {e}")
            raise
    
    return _agents_container


def get_avatar_container():
    """
    Retourne le container pour les configurations d'avatars
    Crée le container si il n'existe pas
    
    Structure des documents:
    {
        "id": "uuid",
        "agent_id": "uuid",  # Partition key
        "agent_name": "Agent Avatar Lisa",
        "status": "step1_completed" | "step2_completed" | "step3_completed" | "active" | "inactive",
        "created_at": "2025-11-18T10:30:00Z",
        "updated_at": "2025-11-18T10:30:00Z",
        "config_type": "voice_live",
        "model_id": "gpt-4o-realtime-preview",
        "model_name": "GPT-4 Omni Realtime",
        "model_description": "Model with avatar support",
        "model_family": "F1_Realtime",
        "current_step": 2,
        "voice_type": "avatar",
        "avatar_id": "lisa",
        "avatar_name": "Lisa",
        "voice_id": "fr-FR-DeniseNeural",
        "language": "fr-FR",
        "phone_number": "+33123456789",
        "description": "Avatar assistant description",
        "system_prompt": "You are a helpful assistant...",
        "voice_config": {
            "voice_speed": 1.0,
            "voice_pitch": 0,
            "temperature": 0.8,
            "max_tokens": 1000,
            "top_p": 0.9
        },
        "session_config": {
            "input_audio_sampling_rate": 24000,
            "turn_detection": {...}
        },
        "selected_tools": [],
        "metadata": {
            "version": 1,
            "avatar_source": "azure_avatar"
        }
    }
    """
    global _avatar_container
    
    if _avatar_container is None:
        database = get_database()
        
        try:
            _avatar_container = database.create_container_if_not_exists(
                id=AVATAR_CONTAINER_NAME,
                partition_key=PartitionKey(path=AVATAR_PARTITION_KEY)
            )
            logger.info(f"✅ Container '{AVATAR_CONTAINER_NAME}' prêt")
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"❌ Erreur lors de la création du container: {e}")
            raise
    
    return _avatar_container


def get_call_history_container():
    """
    Retourne le container pour l'historique des appels
    Crée le container si il n'existe pas
    
    Structure des documents:
    {
        "id": "uuid",
        "call_id": "uuid",  # Partition key
        "agent_id": "uuid",
        "user_id": "uuid",
        "started_at": "2025-11-16T10:30:00Z",
        "ended_at": "2025-11-16T10:45:00Z",
        "duration_seconds": 900,
        "conversation": [...],
        "tools_used": ["weather", "email"],
        "status": "completed" | "failed" | "in_progress"
    }
    """
    global _call_history_container
    
    if _call_history_container is None:
        database = get_database()
        
        try:
            _call_history_container = database.create_container_if_not_exists(
                id=CALL_HISTORY_CONTAINER,
                partition_key=PartitionKey(path=CALL_HISTORY_PARTITION_KEY)
            )
            logger.info(f"✅ Container '{CALL_HISTORY_CONTAINER}' prêt")
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"❌ Erreur lors de la création du container: {e}")
            raise
    
    return _call_history_container


def get_token_consumption_container():
    """
    Retourne le container pour la consommation de tokens
    Crée le container si il n'existe pas
    
    Structure des documents:
    {
        "id": "uuid",
        "user_id": "uuid",  # Partition key
        "agent_id": "uuid",
        "call_id": "uuid",
        "timestamp": "2025-11-16T10:30:00Z",
        "tokens_input": 150,
        "tokens_output": 300,
        "tokens_total": 450,
        "model_id": "gpt-4o-realtime-preview",
        "cost_usd": 0.0045
    }
    """
    global _token_consumption_container
    
    if _token_consumption_container is None:
        database = get_database()
        
        try:
            _token_consumption_container = database.create_container_if_not_exists(
                id=TOKEN_CONSUMPTION_CONTAINER,
                partition_key=PartitionKey(path=TOKEN_CONSUMPTION_PARTITION_KEY)
            )
            logger.info(f"✅ Container '{TOKEN_CONSUMPTION_CONTAINER}' prêt")
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"❌ Erreur lors de la création du container: {e}")
            raise
    
    return _token_consumption_container


def get_instructions_container():
    """
    Retourne le container pour les instructions des modèles
    Crée le container si il n'existe pas
    
    Structure des documents:
    {
        "id": "uuid",  # Partition key
        "instruction_type": "system_prompt" | "tool_instruction" | "template",
        "name": "Template Customer Service",
        "content": "Vous êtes un assistant...",
        "language": "fr",
        "created_at": "2025-11-16T10:30:00Z",
        "updated_at": "2025-11-16T10:30:00Z",
        "version": 1,
        "tags": ["customer_service", "french"]
    }
    """
    global _instructions_container
    
    if _instructions_container is None:
        database = get_database()
        
        try:
            _instructions_container = database.create_container_if_not_exists(
                id=INSTRUCTIONS_CONTAINER,
                partition_key=PartitionKey(path=INSTRUCTIONS_PARTITION_KEY)
            )
            logger.info(f"✅ Container '{INSTRUCTIONS_CONTAINER}' prêt")
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"❌ Erreur lors de la création du container: {e}")
            raise
    
    return _instructions_container


def save_agent_config(config_data):
    """
    Sauvegarde une configuration d'agent dans Cosmos DB
    
    Args:
        config_data (dict): Configuration de l'agent
        
    Returns:
        dict: Document sauvegardé avec l'ID généré
    """
    container = get_agents_container()
    
    try:
        # Upsert (create or update)
        created_item = container.upsert_item(config_data)
        logger.info(f"✅ Configuration agent '{config_data.get('agent_name')}' sauvegardée (ID: {created_item['id']})")
        return created_item
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"❌ Erreur lors de la sauvegarde: {e}")
        raise


def save_avatar_config(config_data):
    """
    Sauvegarde une configuration d'avatar dans Cosmos DB
    
    Args:
        config_data (dict): Configuration de l'avatar
        
    Returns:
        dict: Document sauvegardé avec l'ID généré
    """
    container = get_avatar_container()
    
    try:
        # Upsert (create or update)
        created_item = container.upsert_item(config_data)
        logger.info(f"✅ Configuration avatar '{config_data.get('agent_name')}' sauvegardée (ID: {created_item['id']})")
        return created_item
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"❌ Erreur lors de la sauvegarde de l'avatar: {e}")
        raise


def get_avatar_config(agent_id):
    """
    Récupère une configuration d'avatar par son ID
    
    Args:
        agent_id (str): ID de l'agent avatar
        
    Returns:
        dict: Configuration de l'avatar ou None si non trouvé
    """
    container = get_avatar_container()
    
    try:
        # Query pour trouver l'avatar
        query = "SELECT * FROM c WHERE c.agent_id = @agent_id"
        parameters = [{"name": "@agent_id", "value": agent_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False,
            partition_key=agent_id
        ))
        
        if items:
            logger.info(f"✅ Configuration avatar '{agent_id}' trouvée")
            return items[0]
        else:
            logger.warning(f"⚠️ Configuration avatar '{agent_id}' non trouvée")
            return None
            
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"❌ Erreur lors de la récupération de l'avatar: {e}")
        raise


def update_avatar_config(agent_id, update_data):
    """
    Met à jour partiellement une configuration d'avatar existante
    
    Args:
        agent_id (str): ID de l'agent avatar
        update_data (dict): Dictionnaire des champs à mettre à jour
        
    Returns:
        dict: Configuration mise à jour
    """
    container = get_avatar_container()
    
    try:
        # Récupérer la config existante
        existing_config = get_avatar_config(agent_id)

        if not existing_config:
            logger.error(f"❌ Configuration avatar '{agent_id}' non trouvée pour mise à jour")
            raise ValueError(f"Avatar config {agent_id} not found")

        logger.info(f"🔍 Config existante avant mise à jour: id={existing_config.get('id')}, agent_id={existing_config.get('agent_id')}")
        logger.info(f"🔍 Données à fusionner: {update_data}")

        # Fusionner les données
        existing_config.update(update_data)

        logger.info(f"🔍 Config après fusion: avatar_character={existing_config.get('avatar_character')}, avatar_style={existing_config.get('avatar_style')}")

        # Sauvegarder via upsert
        updated_item = container.upsert_item(existing_config)

        logger.info(f"✅ Configuration avatar '{agent_id}' mise à jour dans Cosmos DB")
        logger.info(f"🔍 Vérification après upsert: avatar_character={updated_item.get('avatar_character')}")

        return updated_item
        
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"❌ Erreur lors de la mise à jour de l'avatar: {e}")
        raise


def list_avatars_by_status(status=None, model_filter=None, date_from=None, date_to=None, page=1, page_size=10):
    """
    Liste les avatars par statut avec pagination et filtres
    
    Args:
        status (str, optional): Filtre par statut. Si None, retourne tous les avatars
        model_filter (str, optional): Filtre par modèle (model_name ou model_id)
        date_from (str, optional): Date de début (ISO format: YYYY-MM-DD)
        date_to (str, optional): Date de fin (ISO format: YYYY-MM-DD)
        page (int): Numéro de page (commence à 1)
        page_size (int): Nombre d'avatars par page
        
    Returns:
        dict: {
            'avatars': list,
            'total': int,
            'page': int,
            'page_size': int,
            'total_pages': int,
            'grouped_by_status': dict
        }
    """
    container = get_avatar_container()
    
    try:
        # Construction de la requête
        query_parts = ["SELECT * FROM c WHERE 1=1"]
        parameters = []
        
        # Filtre par statut
        if status:
            query_parts.append("AND c.status = @status")
            parameters.append({"name": "@status", "value": status})
        
        # Filtre par modèle
        if model_filter:
            query_parts.append("AND (c.model_name = @model OR c.model_id = @model)")
            parameters.append({"name": "@model", "value": model_filter})
        
        # Filtre par date de création (plage)
        if date_from:
            query_parts.append("AND c.created_at >= @date_from")
            parameters.append({"name": "@date_from", "value": date_from})
        
        if date_to:
            # Ajouter 23:59:59 à la date de fin pour inclure toute la journée
            date_to_end = f"{date_to}T23:59:59Z" if 'T' not in date_to else date_to
            query_parts.append("AND c.created_at <= @date_to")
            parameters.append({"name": "@date_to", "value": date_to_end})
        
        # Tri par date de création décroissante
        query_parts.append("ORDER BY c.created_at DESC")
        
        query = " ".join(query_parts)
        
        # Récupérer tous les résultats pour le comptage et le regroupement
        all_items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        total_count = len(all_items)
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        
        # Pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = all_items[start_idx:end_idx]
        
        # Regroupement par statut (tous les avatars, pas seulement la page)
        grouped_by_status = {}
        for item in all_items:
            item_status = item.get('status', 'draft')
            if item_status not in grouped_by_status:
                grouped_by_status[item_status] = []
            grouped_by_status[item_status].append(item)
        
        logger.info(f"✅ {len(paginated_items)}/{total_count} avatar(s) - Page {page}/{total_pages}")
        
        return {
            'avatars': paginated_items,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'grouped_by_status': grouped_by_status
        }
        
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"❌ Erreur lors de la liste des avatars: {e}")
        raise


def get_agent_config(agent_id):
    """
    Récupère une configuration d'agent par son ID
    
    Args:
        agent_id (str): ID de l'agent
        
    Returns:
        dict: Configuration de l'agent ou None si non trouvé
    """
    container = get_agents_container()
    
    try:
        # Query pour trouver l'agent
        query = "SELECT * FROM c WHERE c.agent_id = @agent_id"
        parameters = [{"name": "@agent_id", "value": agent_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False,
            partition_key=agent_id
        ))
        
        if items:
            logger.info(f"✅ Configuration agent '{agent_id}' trouvée")
            return items[0]
        else:
            logger.warning(f"⚠️ Configuration agent '{agent_id}' non trouvée")
            return None
            
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"❌ Erreur lors de la récupération: {e}")
        raise


def update_agent_status(agent_id, new_status):
    """
    Met à jour le statut d'un agent
    
    Args:
        agent_id (str): ID de l'agent
        new_status (str): Nouveau statut (en_cours_de_validation, actif, inactif, archive)
        
    Returns:
        dict: Document mis à jour
    """
    from datetime import datetime
    
    config = get_agent_config(agent_id)
    if not config:
        raise ValueError(f"Agent '{agent_id}' non trouvé")
    
    config['status'] = new_status
    config['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    
    return save_agent_config(config)


def list_agents_by_status(status=None, model_filter=None, date_from=None, date_to=None, page=1, page_size=10):
    """
    Liste les agents par statut avec pagination et filtres
    
    Args:
        status (str, optional): Filtre par statut. Si None, retourne tous les agents
        model_filter (str, optional): Filtre par modèle (model_name ou model_id)
        date_from (str, optional): Date de début (ISO format: YYYY-MM-DD)
        date_to (str, optional): Date de fin (ISO format: YYYY-MM-DD)
        page (int): Numéro de page (commence à 1)
        page_size (int): Nombre d'agents par page
        
    Returns:
        dict: {
            'agents': list,
            'total': int,
            'page': int,
            'page_size': int,
            'total_pages': int,
            'grouped_by_status': dict
        }
    """
    container = get_agents_container()
    
    try:
        # Construction de la requête
        query_parts = ["SELECT * FROM c WHERE 1=1"]
        parameters = []
        
        # Filtre par statut
        if status:
            query_parts.append("AND c.status = @status")
            parameters.append({"name": "@status", "value": status})
        
        # Filtre par modèle
        if model_filter:
            query_parts.append("AND (c.model_name = @model OR c.model_id = @model)")
            parameters.append({"name": "@model", "value": model_filter})
        
        # Filtre par date de création (plage)
        if date_from:
            query_parts.append("AND c.created_at >= @date_from")
            parameters.append({"name": "@date_from", "value": date_from})
        
        if date_to:
            # Ajouter 23:59:59 à la date de fin pour inclure toute la journée
            date_to_end = f"{date_to}T23:59:59Z" if 'T' not in date_to else date_to
            query_parts.append("AND c.created_at <= @date_to")
            parameters.append({"name": "@date_to", "value": date_to_end})
        
        # Tri par date de création décroissante
        query_parts.append("ORDER BY c.created_at DESC")
        
        query = " ".join(query_parts)
        
        # Récupérer tous les résultats pour le comptage et le regroupement
        all_items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        total_count = len(all_items)
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        
        # Pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = all_items[start_idx:end_idx]
        
        # Regroupement par statut (tous les agents, pas seulement la page)
        grouped_by_status = {}
        for item in all_items:
            item_status = item.get('status', 'draft')
            if item_status not in grouped_by_status:
                grouped_by_status[item_status] = []
            grouped_by_status[item_status].append(item)
        
        logger.info(f"✅ {len(paginated_items)}/{total_count} agent(s) - Page {page}/{total_pages}")
        
        return {
            'agents': paginated_items,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'grouped_by_status': grouped_by_status
        }
        
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"❌ Erreur lors de la liste: {e}")
        raise


def delete_agent_config(agent_id):
    """
    Supprime une configuration d'agent de Cosmos DB
    
    Args:
        agent_id (str): ID de l'agent à supprimer
        
    Returns:
        bool: True si suppression réussie, False sinon
    """
    container = get_agents_container()
    
    try:
        # Récupérer d'abord la configuration pour avoir l'ID du document
        config = get_agent_config(agent_id)
        if not config:
            logger.warning(f"⚠️ Agent '{agent_id}' non trouvé pour suppression")
            return False
        
        # Supprimer le document
        container.delete_item(
            item=config['id'],
            partition_key=agent_id
        )
        
        logger.info(f"✅ Agent '{agent_id}' supprimé avec succès")
        return True
        
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"❌ Erreur lors de la suppression de l'agent '{agent_id}': {e}")
        return False


def save_conversation_message(call_id, agent_id, message_type, content, metadata=None, model=None):
    """
    Sauvegarde un message de conversation dans l'historique
    
    Args:
        call_id (str): ID de l'appel
        agent_id (str): ID de l'agent
        message_type (str): 'user', 'agent', 'system', 'tool'
        content (str): Contenu du message
        metadata (dict, optional): Métadonnées supplémentaires (tool_name, etc.)
        model (str, optional): Nom du modèle utilisé (ex: 'gpt-4o-realtime-preview')
        
    Returns:
        dict: Document sauvegardé
    """
    from datetime import datetime
    import uuid
    
    container = get_call_history_container()
    
    try:
        # Récupérer la conversation existante ou créer une nouvelle
        query = "SELECT * FROM c WHERE c.call_id = @call_id"
        parameters = [{"name": "@call_id", "value": call_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False,
            partition_key=call_id
        ))
        
        # Petite fonction utilitaire locale pour dériver family/tier à partir du model
        def _get_model_family_and_tier(model_name: str):
            if not model_name:
                return None, None
            m = model_name.lower().strip()
            # Famille: on garde un label simple basé sur le préfixe
            if "gpt-4o" in m:
                family = "gpt-4o"
            elif "gpt-5" in m:
                family = "gpt-5"
            elif "gpt-realtime" in m:
                family = "gpt-realtime"
            elif "phi4" in m:
                family = "phi4"
            else:
                family = "unknown"

            # Niveau de tarification: on s'aligne sur les catégories du cost_calculator
            from configuration.cost_calculator import get_model_category
            pricing_tier = get_model_category(model_name)
            return family, pricing_tier

        if items:
            # Conversation existe, ajouter le message
            conversation_doc = items[0]
            conversation_doc['conversation'].append({
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'type': message_type,
                'content': content,
                'metadata': metadata or {}
            })
            conversation_doc['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            # Toujours mettre à jour le model si fourni (même s'il existe déjà)
            # Cela permet de corriger les conversations qui n'ont pas de model
            if model:
                conversation_doc['model'] = model
                family, pricing_tier = _get_model_family_and_tier(model)
                if family:
                    conversation_doc['model_family'] = family
                if pricing_tier:
                    conversation_doc['pricing_tier'] = pricing_tier
        else:
            # Nouvelle conversation
            conversation_doc = {
                'id': str(uuid.uuid4()),
                'call_id': call_id,
                'agent_id': agent_id,
                'started_at': datetime.utcnow().isoformat() + 'Z',
                'updated_at': datetime.utcnow().isoformat() + 'Z',
                'conversation': [{
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'type': message_type,
                    'content': content,
                    'metadata': metadata or {}
                }],
                'status': 'in_progress',
                'tools_used': []
            }
            # Ajouter le model si fourni
            if model:
                conversation_doc['model'] = model
                family, pricing_tier = _get_model_family_and_tier(model)
                if family:
                    conversation_doc['model_family'] = family
                if pricing_tier:
                    conversation_doc['pricing_tier'] = pricing_tier
        
        # Sauvegarder
        saved_doc = container.upsert_item(conversation_doc)
        logger.info(f"✅ Message {message_type} sauvegardé pour call_id: {call_id}")
        return saved_doc
        
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"❌ Erreur lors de la sauvegarde du message: {e}")
        raise


def get_conversation_history(call_id):
    """
    Récupère l'historique complet d'une conversation
    
    Args:
        call_id (str): ID de l'appel
        
    Returns:
        dict: Document de conversation ou None si non trouvé
    """
    container = get_call_history_container()
    
    try:
        query = "SELECT * FROM c WHERE c.call_id = @call_id"
        parameters = [{"name": "@call_id", "value": call_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False,
            partition_key=call_id
        ))
        
        if items:
            logger.info(f"✅ Historique trouvé pour call_id: {call_id} ({len(items[0].get('conversation', []))} messages)")
            return items[0]
        else:
            logger.warning(f"⚠️ Aucun historique trouvé pour call_id: {call_id}")
            return None
            
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"❌ Erreur lors de la récupération de l'historique: {e}")
        raise


def end_conversation(call_id, tools_used=None, tokens=None):
    """
    Marque une conversation comme terminée avec analyse complète
    
    Args:
        call_id (str): ID de l'appel
        tools_used (list, optional): Liste des outils utilisés pendant la conversation
        tokens (dict, optional): Tokens consommés pendant la conversation
            {
                "inputs_text_tokens": int,
                "inputs_cached_tokens": int,
                "inputs_audio_tokens": int,
                "outputs_text_tokens": int,
                "outputs_audio_tokens": int
            }
        
    Returns:
        dict: Document mis à jour avec tous les nouveaux champs
    """
    from datetime import datetime
    from configuration.sentiment_analysis import analyze_conversation_sentiments
    from configuration.cost_calculator import calculate_cost_breakdown
    
    container = get_call_history_container()
    
    try:
        conversation_doc = get_conversation_history(call_id)
        if not conversation_doc:
            raise ValueError(f"Conversation '{call_id}' non trouvée")
        
        # 1. Mise à jour du status et timestamps
        conversation_doc['status'] = 'completed'
        conversation_doc['ended_at'] = datetime.utcnow().isoformat() + 'Z'
        conversation_doc['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        if tools_used:
            conversation_doc['tools_used'] = tools_used
        
        # 2. Calculer la durée en minutes (3 décimales)
        if 'started_at' in conversation_doc and 'ended_at' in conversation_doc:
            start = datetime.fromisoformat(conversation_doc['started_at'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(conversation_doc['ended_at'].replace('Z', '+00:00'))
            duration_seconds = (end - start).total_seconds()
            conversation_doc['duration_minutes'] = round(duration_seconds / 60, 3)
        
        # 3. Calculer le nombre d'interactions
        messages = conversation_doc.get('conversation', [])  # ✅ Utiliser 'conversation' au lieu de 'messages'
        user_message_count = sum(1 for msg in messages if msg.get('type') == 'user')  # ✅ Utiliser 'type' au lieu de 'role'
        conversation_doc['interaction_count'] = user_message_count
        
        # 4. Calculer la durée moyenne par interaction (3 décimales)
        if user_message_count > 0 and 'duration_minutes' in conversation_doc:
            conversation_doc['average_interaction_duration'] = round(
                conversation_doc['duration_minutes'] / user_message_count, 3
            )
        else:
            conversation_doc['average_interaction_duration'] = 0.0
        
        # 5. Analyser les sentiments (user et assistant)
        try:
            sentiments = analyze_conversation_sentiments(messages)
            conversation_doc['user_sentiment_analysis'] = sentiments['user_sentiment_analysis']
            conversation_doc['assistant_sentiment_analysis'] = sentiments['assistant_sentiment_analysis']
            logger.info(f"✅ Sentiments analysés: user={sentiments['user_sentiment_analysis']['sentiment']}, assistant={sentiments['assistant_sentiment_analysis']['sentiment']}")
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de l'analyse de sentiment: {e}")
            conversation_doc['user_sentiment_analysis'] = {
                "sentiment": "neutral",
                "positive": 0.33,
                "neutral": 0.34,
                "negative": 0.33,
                "error": str(e)
            }
            conversation_doc['assistant_sentiment_analysis'] = {
                "sentiment": "neutral",
                "positive": 0.33,
                "neutral": 0.34,
                "negative": 0.33,
                "error": str(e)
            }
        
        # 6. Enregistrer les tokens détaillés
        if tokens:
            conversation_doc['tokens'] = tokens
        
        # 7. Calculer le coût de la conversation avec détails
        if tokens and 'model' in conversation_doc:
            try:
                from configuration.cost_calculator import calculate_cost_breakdown

                pricing_tier = conversation_doc.get('pricing_tier')
                cost_details = calculate_cost_breakdown(conversation_doc['model'], tokens, pricing_tier=pricing_tier)

                # Stocker les coûts détaillés
                conversation_doc['cost'] = {
                    'inputs_text_cost': cost_details['breakdown']['inputs_text']['cost'],
                    'inputs_cached_cost': cost_details['breakdown']['inputs_cached']['cost'],
                    'inputs_audio_cost': cost_details['breakdown']['inputs_audio']['cost'],
                    'outputs_text_cost': cost_details['breakdown']['outputs_text']['cost'],
                    'outputs_audio_cost': cost_details['breakdown']['outputs_audio']['cost'],
                    'total_cost': cost_details['total_cost']
                }

                # Ajouter coût par minute si durée disponible
                if 'duration_minutes' in conversation_doc and conversation_doc['duration_minutes'] > 0:
                    conversation_doc['cost']['cost_per_minute'] = round(
                        cost_details['total_cost'] / conversation_doc['duration_minutes'], 6
                    )
                else:
                    conversation_doc['cost']['cost_per_minute'] = 0.0

                logger.info(f"💰 Coût total: ${cost_details['total_cost']}")
                logger.info(f"💰 Coût/min: ${conversation_doc['cost']['cost_per_minute']}")
            except Exception as e:
                logger.warning(f"⚠️ Erreur lors du calcul du coût: {e}")
                conversation_doc['cost'] = {
                    'inputs_text_cost': 0.0,
                    'inputs_cached_cost': 0.0,
                    'inputs_audio_cost': 0.0,
                    'outputs_text_cost': 0.0,
                    'outputs_audio_cost': 0.0,
                    'total_cost': 0.0,
                    'cost_per_minute': 0.0
                }
        else:
            logger.warning("⚠️ Tokens ou model manquant, coût non calculé")
            conversation_doc['cost'] = {
                'inputs_text_cost': 0.0,
                'inputs_cached_cost': 0.0,
                'inputs_audio_cost': 0.0,
                'outputs_text_cost': 0.0,
                'outputs_audio_cost': 0.0,
                'total_cost': 0.0,
                'cost_per_minute': 0.0
            }
        
        # 8. Générer un résumé de la conversation via Azure OpenAI (si configuré)
        try:
            if AZURE_OPENAI_SUMMARY_ENDPOINT and AZURE_OPENAI_SUMMARY_KEY and AZURE_OPENAI_SUMMARY_DEPLOYMENT:
                # Construire un texte source simple à partir de l'historique
                history_lines = []
                for msg in messages:
                    m_type = msg.get('type', 'system')
                    prefix = 'Utilisateur' if m_type == 'user' else ('Assistant' if m_type == 'agent' else 'Système')
                    content = msg.get('content', '')
                    history_lines.append(f"{prefix}: {content}")

                history_text = "\n".join(history_lines)

                prompt = (
                    "Tu es un assistant qui résume des conversations téléphoniques pour un centre d'appel. "
                    "À partir de l'historique de conversation ci-dessous, produis un PARAGRAPHE de 4 lignes maximum en français. "
                    "Ton résumé doit obligatoirement : 1) rappeler les principaux sujets abordés, 2) donner une évaluation globale de la conversation "
                    "(tonalité de l'échange, satisfaction probable du client, qualité de la prise en charge). "
                    "Sois factuel, synthétique, sans puces, sans titres.")

                url = f"{AZURE_OPENAI_SUMMARY_ENDPOINT}openai/deployments/{AZURE_OPENAI_SUMMARY_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_SUMMARY_API_VERSION}"
                headers = {
                    "Content-Type": "application/json",
                    "api-key": AZURE_OPENAI_SUMMARY_KEY
                }
                payload = {
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": history_text[:12000]}
                    ],
                    "max_completion_tokens": 512
                }

                resp = requests.post(url, headers=headers, json=payload, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    summary_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if summary_text:
                        conversation_doc["summary"] = summary_text
                else:
                    logger.warning(f"⚠️ Erreur Azure OpenAI summary ({resp.status_code}): {resp.text[:200]}")
            else:
                logger.warning("⚠️ Azure OpenAI Summary n'est pas configuré, aucun résumé généré")
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de la génération du résumé Azure OpenAI: {e}")

        # 9. Sauvegarder le document mis à jour
        saved_doc = container.upsert_item(conversation_doc)
        
        logger.info(f"✅ Conversation {call_id} terminée avec analyse complète")
        logger.info(f"   Durée: {conversation_doc.get('duration_minutes', 0)} min")
        logger.info(f"   Interactions: {conversation_doc.get('interaction_count', 0)}")
        cost_info = conversation_doc.get('cost', {})
        logger.info(f"   Coût total: ${cost_info.get('total_cost', 0)}")
        logger.info(f"   Coût/min: ${cost_info.get('cost_per_minute', 0)}")
        
        return saved_doc
        
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"❌ Erreur lors de la finalisation de la conversation: {e}")
        raise


def get_daily_dashboard_metrics(current_time=None):
    """Retourne les KPI agrégés pour la journée courante.

    KPI calculés (uniquement sur les conversations complétées aujourd'hui, en UTC):
      - total_conversations
      - active_conversations (status == 'in_progress')
      - avg_user_satisfaction (0-1)
      - avg_agent_satisfaction (0-1)
    - total_tokens (tous types + par type)
    - total_cost_usd (tous types + par type)
    - total_minutes (durée totale des conversations)
      - cost_per_minute
      - avg_duration_minutes (durée moyenne d'une conversation)
      - avg_interactions_per_conversation (interaction_count moyen)
      - sparkline_conversations (par tranche de 15 min)
      - sparkline_costs (par tranche de 15 min)
      - sparkline_minutes (par tranche de 15 min)
    """
    container = get_call_history_container()

    # Déterminer le début/fin de journée en UTC
    now = current_time or datetime.now(timezone.utc)
    day_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    day_end = day_start.replace(hour=23, minute=59, second=59, microsecond=999999)

    day_start_iso = day_start.isoformat().replace("+00:00", "Z")
    day_end_iso = day_end.isoformat().replace("+00:00", "Z")

    # Conversations complétées aujourd'hui
    completed_query = (
        "SELECT c.id, c.started_at, c.ended_at, c.status, "
        "c.duration_minutes, c.interaction_count, c.cost, c.tokens, "
        "c.user_sentiment_analysis, c.assistant_sentiment_analysis "
        "FROM c WHERE c.status = 'completed' "
        "AND c.ended_at >= @day_start AND c.ended_at <= @day_end"
    )

    params = [
        {"name": "@day_start", "value": day_start_iso},
        {"name": "@day_end", "value": day_end_iso},
    ]

    completed_items = list(
        container.query_items(
            query=completed_query,
            parameters=params,
            enable_cross_partition_query=True,
        )
    )

    # Conversations en cours (pour le compteur temps réel)
    active_query = "SELECT VALUE COUNT(1) FROM c WHERE c.status = 'in_progress'"
    active_items = list(
        container.query_items(
            query=active_query,
            enable_cross_partition_query=True,
        )
    )
    active_conversations = active_items[0] if active_items else 0

    total_conversations = len(completed_items)

    total_minutes = 0.0
    total_cost_usd = 0.0
    total_tokens = 0

    # Détail par type de tokens / coûts (aligné sur cost_calculator)
    total_tokens_breakdown = {
        "inputs_text_tokens": 0,
        "inputs_cached_tokens": 0,
        "inputs_audio_tokens": 0,
        "outputs_text_tokens": 0,
        "outputs_audio_tokens": 0,
    }

    total_cost_breakdown = {
        "inputs_text_cost": 0.0,
        "inputs_cached_cost": 0.0,
        "inputs_audio_cost": 0.0,
        "outputs_text_cost": 0.0,
        "outputs_audio_cost": 0.0,
    }
    total_user_score = 0.0
    total_agent_score = 0.0
    user_score_count = 0
    agent_score_count = 0
    
    # Sentiment breakdown
    total_user_positive = 0.0
    total_user_neutral = 0.0
    total_user_negative = 0.0
    total_agent_positive = 0.0
    total_agent_neutral = 0.0
    total_agent_negative = 0.0
    
    total_interactions = 0

    # Préparation des buckets pour les sparklines (tranches de 15 minutes)
    # On couvre la journée de 00:00 à 24:00 en pas de 15 min => 96 points
    interval_seconds = 15 * 60
    bucket_count = int((24 * 60 * 60) / interval_seconds)
    spark_conversations = [0] * bucket_count
    spark_costs = [0.0] * bucket_count
    spark_minutes = [0.0] * bucket_count

    def _get_bucket_index(dt: datetime) -> int:
        if dt < day_start or dt > day_end:
            return None
        delta = (dt - day_start).total_seconds()
        idx = int(delta // interval_seconds)
        if 0 <= idx < bucket_count:
            return idx
        return None

    for doc in completed_items:
        duration = doc.get("duration_minutes") or 0.0
        interaction_count = doc.get("interaction_count") or 0
        cost = (doc.get("cost") or {}).get("total_cost", 0.0)

        tokens_info = doc.get("tokens") or {}
        tokens_total = 0
        for key in [
            "inputs_text_tokens",
            "inputs_cached_tokens",
            "inputs_audio_tokens",
            "outputs_text_tokens",
            "outputs_audio_tokens",
        ]:
            value = int(tokens_info.get(key) or 0)
            tokens_total += value
            total_tokens_breakdown[key] += value

        total_minutes += float(duration)
        total_cost_usd += float(cost)
        total_tokens += tokens_total
        total_interactions += interaction_count

        # Scores de satisfaction (moyenne pondérée au nombre de conversations)
        user_sa = doc.get("user_sentiment_analysis") or {}
        user_pos = user_sa.get("positive")
        if isinstance(user_pos, (int, float)):
            total_user_score += float(user_pos)
            user_score_count += 1
            total_user_positive += float(user_pos)
            total_user_neutral += float(user_sa.get("neutral", 0))
            total_user_negative += float(user_sa.get("negative", 0))

        agent_sa = doc.get("assistant_sentiment_analysis") or {}
        agent_pos = agent_sa.get("positive")
        if isinstance(agent_pos, (int, float)):
            total_agent_score += float(agent_pos)
            agent_score_count += 1
            total_agent_positive += float(agent_pos)
            total_agent_neutral += float(agent_sa.get("neutral", 0))
            total_agent_negative += float(agent_sa.get("negative", 0))

        # Sparklines: bucket basé sur ended_at
        ended_at = doc.get("ended_at") or doc.get("updated_at") or doc.get("started_at")
        if ended_at:
            try:
                if isinstance(ended_at, str):
                    dt = datetime.fromisoformat(ended_at.replace("Z", "+00:00"))
                else:
                    dt = ended_at
                idx = _get_bucket_index(dt.astimezone(timezone.utc))
                if idx is not None:
                    spark_conversations[idx] += 1
                    spark_costs[idx] += float(cost)
                    spark_minutes[idx] += float(duration)
            except Exception:
                # En cas de problème de parsing, on ignore le point
                continue

    avg_user_satisfaction = (
        total_user_score / user_score_count if user_score_count > 0 else 0.0
    )
    avg_agent_satisfaction = (
        total_agent_score / agent_score_count if agent_score_count > 0 else 0.0
    )
    
    avg_user_positive = (
        total_user_positive / user_score_count if user_score_count > 0 else 0.0
    )
    avg_user_neutral = (
        total_user_neutral / user_score_count if user_score_count > 0 else 0.0
    )
    avg_user_negative = (
        total_user_negative / user_score_count if user_score_count > 0 else 0.0
    )
    
    avg_agent_positive = (
        total_agent_positive / agent_score_count if agent_score_count > 0 else 0.0
    )
    avg_agent_neutral = (
        total_agent_neutral / agent_score_count if agent_score_count > 0 else 0.0
    )
    avg_agent_negative = (
        total_agent_negative / agent_score_count if agent_score_count > 0 else 0.0
    )

    avg_duration_minutes = (
        total_minutes / total_conversations if total_conversations > 0 else 0.0
    )
    avg_interactions_per_conversation = (
        total_interactions / total_conversations if total_conversations > 0 else 0.0
    )

    cost_per_minute = (
        total_cost_usd / total_minutes if total_minutes > 0 else 0.0
    )

    return {
        "total_conversations": total_conversations,
        "active_conversations": active_conversations,
        "avg_user_satisfaction": round(avg_user_satisfaction, 3),
        "avg_agent_satisfaction": round(avg_agent_satisfaction, 3),
        "avg_user_positive": round(avg_user_positive, 3),
        "avg_user_neutral": round(avg_user_neutral, 3),
        "avg_user_negative": round(avg_user_negative, 3),
        "avg_agent_positive": round(avg_agent_positive, 3),
        "avg_agent_neutral": round(avg_agent_neutral, 3),
        "avg_agent_negative": round(avg_agent_negative, 3),
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost_usd, 6),
        "total_minutes": round(total_minutes, 3),
        "cost_per_minute": round(cost_per_minute, 6),
        "avg_duration_minutes": round(avg_duration_minutes, 3),
        "avg_interactions_per_conversation": round(
            avg_interactions_per_conversation, 3
        ),
        "sparkline_conversations": spark_conversations,
        "sparkline_costs": [round(v, 6) for v in spark_costs],
        "sparkline_minutes": [round(v, 3) for v in spark_minutes],
        "tokens_breakdown": total_tokens_breakdown,
        "cost_breakdown": {k: round(v, 6) for k, v in total_cost_breakdown.items()},
        "day_start": day_start_iso,
        "day_end": day_end_iso,
        "generated_at": now.isoformat().replace("+00:00", "Z"),
    }


# Initialisation au démarrage du module - tous les containers
try:
    get_cosmos_client()
    get_database()
    get_agents_container()
    get_avatar_container()
    get_call_history_container()
    get_token_consumption_container()
    get_instructions_container()
    logger.info("🎯 Module Cosmos DB initialisé avec succès - Tous les containers prêts")
except Exception as e:
    logger.error(f"❌ Échec de l'initialisation Cosmos DB: {e}")
