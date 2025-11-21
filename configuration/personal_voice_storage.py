"""
Configuration du stockage pour Personal Voice
Crée et gère les containers Cosmos DB et Azure Blob Storage
"""

import os
import logging
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

# ========================================
# CONFIGURATION COSMOS DB
# ========================================
COSMOS_URI = os.getenv('COSMOS_URI')
COSMOS_KEY = os.getenv('COSMOS_KEY')
COSMOS_DATABASE_NAME = os.getenv('COSMOS_DATABASE_NAME', 'ConversationsDB')

# Container pour les projets Personal Voice
PERSONAL_VOICE_PROJECTS_CONTAINER = 'PersonalVoiceProjects'
PERSONAL_VOICE_PROJECTS_PARTITION_KEY = '/project_id'

# Container pour les consentements
PERSONAL_VOICE_CONSENTS_CONTAINER = 'PersonalVoiceConsents'
PERSONAL_VOICE_CONSENTS_PARTITION_KEY = '/consent_id'

# Container pour les voix personnelles créées
PERSONAL_VOICES_CONTAINER = 'PersonalVoices'
PERSONAL_VOICES_PARTITION_KEY = '/voice_id'

# ========================================
# CONFIGURATION BLOB STORAGE
# ========================================
BLOB_CONNECTION_STRING = os.getenv('BLOB_CONNECTION_STRING')
BLOB_ACCOUNT_NAME = os.getenv('BLOB_ACCOUNT_NAME')
BLOB_ACCOUNT_KEY = os.getenv('BLOB_ACCOUNT_KEY')

# Containers Blob pour les fichiers audio
CONSENT_AUDIO_CONTAINER = 'consent-audio'  # Fichiers audio de consentement
VOICE_SAMPLES_CONTAINER = 'voice-samples'  # Échantillons vocaux pour l'entraînement
SYNTHESIZED_AUDIO_CONTAINER = 'synthesized-audio'  # Audio synthétisé avec voix personnelle

# Singletons
_cosmos_client = None
_database = None
_blob_service_client = None
_projects_container = None
_consents_container = None
_voices_container = None


# ========================================
# COSMOS DB - FONCTIONS UTILITAIRES
# ========================================

def get_cosmos_client():
    """Retourne le client Cosmos DB (singleton)"""
    global _cosmos_client
    
    if _cosmos_client is None:
        if not COSMOS_URI or not COSMOS_KEY:
            raise ValueError("COSMOS_URI et COSMOS_KEY doivent être définis dans .env")
        
        _cosmos_client = CosmosClient(COSMOS_URI, credential=COSMOS_KEY)
        logger.info("✅ Client Cosmos DB initialisé")
    
    return _cosmos_client


def get_database():
    """Retourne la base de données Cosmos DB"""
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


def get_personal_voice_projects_container():
    """
    Retourne le container pour les projets de voix personnelles
    
    Structure des documents:
    {
        "id": "uuid",
        "project_id": "uuid",  # Partition key
        "project_name": "Mon Projet Voice",
        "description": "Description du projet",
        "status": "created" | "active" | "archived",
        "created_at": "2025-11-18T10:30:00Z",
        "updated_at": "2025-11-18T10:30:00Z",
        "created_by": "user_id",
        "consents": ["consent_id_1", "consent_id_2"],
        "voices": ["voice_id_1", "voice_id_2"]
    }
    """
    global _projects_container
    
    if _projects_container is None:
        database = get_database()
        
        try:
            _projects_container = database.create_container_if_not_exists(
                id=PERSONAL_VOICE_PROJECTS_CONTAINER,
                partition_key=PartitionKey(path=PERSONAL_VOICE_PROJECTS_PARTITION_KEY)
            )
            logger.info(f"✅ Container '{PERSONAL_VOICE_PROJECTS_CONTAINER}' prêt")
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"❌ Erreur lors de la création du container: {e}")
            raise
    
    return _projects_container


def get_personal_voice_consents_container():
    """
    Retourne le container pour les consentements de voix personnelles
    
    Structure des documents:
    {
        "id": "uuid",
        "consent_id": "uuid",  # Partition key
        "project_id": "uuid",
        "voice_talent_name": "Jean Dupont",
        "company_name": "Waka Afrique",
        "locale": "fr-FR",
        "description": "Consentement pour...",
        "audio_url": "https://storage.blob.core.windows.net/consent-audio/...",
        "audio_blob_name": "consent_123.wav",
        "consent_text": "Je [prénom et nom] suis conscient(e)...",
        "status": "pending" | "approved" | "rejected",
        "created_at": "2025-11-18T10:30:00Z",
        "approved_at": "2025-11-18T11:00:00Z",
        "azure_consent_id": "consent-azure-id-from-api"
    }
    """
    global _consents_container
    
    if _consents_container is None:
        database = get_database()
        
        try:
            _consents_container = database.create_container_if_not_exists(
                id=PERSONAL_VOICE_CONSENTS_CONTAINER,
                partition_key=PartitionKey(path=PERSONAL_VOICE_CONSENTS_PARTITION_KEY)
            )
            logger.info(f"✅ Container '{PERSONAL_VOICE_CONSENTS_CONTAINER}' prêt")
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"❌ Erreur lors de la création du container: {e}")
            raise
    
    return _consents_container


def get_personal_voices_container():
    """
    Retourne le container pour les voix personnelles créées
    
    Structure des documents:
    {
        "id": "uuid",
        "voice_id": "uuid",  # Partition key
        "project_id": "uuid",
        "consent_id": "uuid",
        "voice_name": "Voix de Jean",
        "description": "Voix personnelle pour...",
        "locale": "fr-FR",
        "training_audio_url": "https://storage.blob.core.windows.net/voice-samples/...",
        "training_blob_name": "training_123.wav",
        "status": "training" | "succeeded" | "failed",
        "azure_voice_id": "voice-azure-id-from-api",
        "speaker_profile_id": "spkr_profile_id",
        "created_at": "2025-11-18T10:30:00Z",
        "trained_at": "2025-11-18T12:00:00Z",
        "error_message": "Error details if failed",
        "usage_count": 0,
        "last_used_at": "2025-11-18T14:00:00Z"
    }
    """
    global _voices_container
    
    if _voices_container is None:
        database = get_database()
        
        try:
            _voices_container = database.create_container_if_not_exists(
                id=PERSONAL_VOICES_CONTAINER,
                partition_key=PartitionKey(path=PERSONAL_VOICES_PARTITION_KEY)
            )
            logger.info(f"✅ Container '{PERSONAL_VOICES_CONTAINER}' prêt")
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"❌ Erreur lors de la création du container: {e}")
            raise
    
    return _voices_container


# ========================================
# BLOB STORAGE - FONCTIONS UTILITAIRES
# ========================================

def get_blob_service_client():
    """Retourne le client Blob Storage (singleton)"""
    global _blob_service_client
    
    if _blob_service_client is None:
        # Essayer d'abord avec la connection string
        if BLOB_CONNECTION_STRING:
            try:
                _blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
                logger.info("✅ Blob Service Client initialisé (connection string)")
            except Exception as e:
                logger.warning(f"⚠️ Échec avec BLOB_CONNECTION_STRING: {e}")
                _blob_service_client = None
        
        # Sinon avec account name + key
        if _blob_service_client is None and BLOB_ACCOUNT_NAME and BLOB_ACCOUNT_KEY:
            try:
                account_url = f"https://{BLOB_ACCOUNT_NAME}.blob.core.windows.net"
                _blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=BLOB_ACCOUNT_KEY
                )
                logger.info("✅ Blob Service Client initialisé (account + key)")
            except Exception as e:
                logger.warning(f"⚠️ Échec avec BLOB_ACCOUNT_NAME/KEY: {e}")
                _blob_service_client = None
        
        # Dernier recours: essayer avec les mêmes credentials que Cosmos DB
        if _blob_service_client is None and COSMOS_KEY:
            try:
                # Extraire le nom du compte à partir de COSMOS_URI
                # Format: https://ACCOUNT_NAME.documents.azure.com:443/
                import re
                match = re.search(r'https://([^.]+)\.', COSMOS_URI)
                if match:
                    cosmos_account_name = match.group(1)
                    # Essayer avec le même nom de compte mais pour blob storage
                    account_url = f"https://{cosmos_account_name}.blob.core.windows.net"
                    _blob_service_client = BlobServiceClient(
                        account_url=account_url,
                        credential=COSMOS_KEY
                    )
                    logger.info(f"✅ Blob Service Client initialisé avec credentials Cosmos DB ({cosmos_account_name})")
            except Exception as e:
                logger.warning(f"⚠️ Échec avec credentials Cosmos DB: {e}")
                _blob_service_client = None
        
        if _blob_service_client is None:
            raise ValueError(
                "Impossible d'initialiser Blob Storage. Veuillez définir dans .env:\n"
                "- BLOB_CONNECTION_STRING, ou\n"
                "- BLOB_ACCOUNT_NAME + BLOB_ACCOUNT_KEY, ou\n"
                "- Créer un compte Blob Storage Azure"
            )
    
    return _blob_service_client


def create_blob_containers():
    """Crée tous les containers blob nécessaires pour Personal Voice"""
    blob_service = get_blob_service_client()
    
    containers = [
        (CONSENT_AUDIO_CONTAINER, "Fichiers audio de consentement"),
        (VOICE_SAMPLES_CONTAINER, "Échantillons vocaux pour l'entraînement"),
        (SYNTHESIZED_AUDIO_CONTAINER, "Audio synthétisé avec voix personnelle")
    ]
    
    for container_name, description in containers:
        try:
            container_client = blob_service.get_container_client(container_name)
            if not container_client.exists():
                blob_service.create_container(container_name)
                logger.info(f"✅ Container Blob '{container_name}' créé - {description}")
            else:
                logger.info(f"✅ Container Blob '{container_name}' existe déjà - {description}")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création du container '{container_name}': {e}")
            raise


def upload_audio_file(file_stream, file_name, container_name, content_type='audio/wav'):
    """
    Upload un fichier audio vers Azure Blob Storage
    
    Args:
        file_stream: Stream du fichier (ex: request.files['audio'])
        file_name: Nom du fichier dans le blob
        container_name: Nom du container blob (consent-audio, voice-samples, etc.)
        content_type: Type MIME du fichier (audio/wav, audio/mpeg, etc.)
        
    Returns:
        str: URL du blob uploadé
    """
    blob_service = get_blob_service_client()
    
    try:
        blob_client = blob_service.get_blob_client(
            container=container_name,
            blob=file_name
        )
        
        # Upload avec metadata
        blob_client.upload_blob(
            file_stream,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type)
        )
        
        blob_url = blob_client.url
        logger.info(f"✅ Fichier uploadé: {blob_url}")
        
        return blob_url
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'upload du fichier: {e}")
        raise


def delete_blob(blob_name, container_name):
    """
    Supprime un blob du stockage
    
    Args:
        blob_name: Nom du blob à supprimer
        container_name: Nom du container
        
    Returns:
        bool: True si suppression réussie
    """
    blob_service = get_blob_service_client()
    
    try:
        blob_client = blob_service.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        
        blob_client.delete_blob()
        logger.info(f"✅ Blob supprimé: {blob_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la suppression du blob: {e}")
        return False


def get_blob_url(blob_name, container_name):
    """
    Retourne l'URL d'un blob
    
    Args:
        blob_name: Nom du blob
        container_name: Nom du container
        
    Returns:
        str: URL du blob
    """
    blob_service = get_blob_service_client()
    
    blob_client = blob_service.get_blob_client(
        container=container_name,
        blob=blob_name
    )
    
    return blob_client.url


# ========================================
# INITIALISATION
# ========================================

def init_personal_voice_storage():
    """
    Initialise tous les containers Cosmos DB et Blob Storage pour Personal Voice
    À appeler au démarrage de l'application
    """
    logger.info("🎙️ Initialisation du stockage Personal Voice...")
    
    try:
        # Cosmos DB Containers
        get_personal_voice_projects_container()
        get_personal_voice_consents_container()
        get_personal_voices_container()
        
        # Blob Storage Containers
        create_blob_containers()
        
        logger.info("✅ Stockage Personal Voice initialisé avec succès")
        return True
        
    except Exception as e:
        logger.error(f"❌ Échec de l'initialisation du stockage Personal Voice: {e}")
        return False


# Auto-initialisation au démarrage du module
if __name__ != "__main__":
    try:
        init_personal_voice_storage()
    except Exception as e:
        logger.warning(f"⚠️ Impossible d'initialiser Personal Voice Storage: {e}")
        logger.warning("⚠️ Assurez-vous que BLOB_CONNECTION_STRING est défini dans .env")
        logger.warning("⚠️ Les fonctionnalités Personal Voice ne seront pas disponibles")
