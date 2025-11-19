"""
Azure OpenAI Voice Live (Realtime API) Configuration
Initialise le client pour les sessions Voice Live
"""

import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du logger
logger = logging.getLogger(__name__)

# Variables de configuration Azure AI Foundry Voice Live
# Priorité aux variables spécifiques VOICE_LIVE, sinon fallback sur AZURE_SPEECH
AZURE_OPENAI_API_KEY = os.getenv('VOICE_LIVE_KEY') or os.getenv('AZURE_SPEECH_KEY')
AZURE_RESOURCE_NAME = os.getenv('VOICE_LIVE_NAME') or os.getenv('AZURE_SPEECH_NAME')
AZURE_ENDPOINT = os.getenv('VOICE_LIVE_ENDPOINT') or os.getenv('AZURE_SPEECH_ENDPOINT')

# Support des deux formats d'endpoint :
# - Nouveau: services.ai.azure.com
# - Ancien: cognitiveservices.azure.com
VOICE_LIVE_ENDPOINT_TYPE = os.getenv('VOICE_LIVE_ENDPOINT_TYPE', 'cognitiveservices')  # 'services' ou 'cognitiveservices'

if VOICE_LIVE_ENDPOINT_TYPE == 'services':
    AZURE_WEBSOCKET_BASE = f"wss://{os.getenv('VOICE_LIVE_NAME') or os.getenv('AZURE_SPEECH_NAME')}.services.ai.azure.com/voice-live/realtime"
else:
    AZURE_WEBSOCKET_BASE = f"wss://{os.getenv('VOICE_LIVE_NAME') or os.getenv('AZURE_SPEECH_NAME')}.cognitiveservices.azure.com/voice-live/realtime"

# Configurations des modèles Realtime disponibles
REALTIME_MODELS = {
    'gpt-4o-realtime-preview': {
        'version': os.getenv('GPT_4O_REALTIME_PREVIEW_VERSION', '2024-10-01'),
        'capacity': int(os.getenv('GPT_4O_REALTIME_PREVIEW_CAPACITY', 20)),
        'deployment_name': 'gpt-4o-realtime-preview',
        'description': 'GPT-4o Realtime Preview - Haute qualité'
    },
    'gpt-4o-mini-realtime-preview': {
        'version': os.getenv('GPT_4O_MINI_REALTIME_PREVIEW_VERSION', '2024-12-17'),
        'capacity': int(os.getenv('GPT_4O_MINI_REALTIME_PREVIEW_CAPACITY', 6)),
        'deployment_name': 'gpt-4o-mini-realtime-preview',
        'description': 'GPT-4o Mini Realtime Preview - Léger et rapide'
    },
    'gpt-realtime': {
        'version': os.getenv('GPT_REALTIME_VERSION', '2025-08-28'),
        'capacity': int(os.getenv('GPT_REALTIME_CAPACITY', 30)),
        'deployment_name': 'gpt-realtime',
        'description': 'GPT Realtime - Standard'
    },
    'gpt-realtime-mini': {
        'version': os.getenv('GPT_REALTIME_MINI_VERSION', '2025-10-06'),
        'capacity': int(os.getenv('GPT_REALTIME_MINI_CAPACITY', 200)),
        'deployment_name': 'gpt-realtime-mini',
        'description': 'GPT Realtime Mini - Haute capacité'
    }
}


def get_ouagadougou_datetime_string() -> str:
    """Retourne la date/heure actuelle à Ouagadougou au format
    "jour_de_la_semaine dd mm aaaa hh:mm" en français.

    Ouagadougou est sur le fuseau UTC sans changement d'heure,
    donc on utilise simplement l'heure UTC.
    """
    # On garde les noms de jours en anglais si la locale FR n'est pas dispo,
    # le plus important est que le format reste constant.
    now_ouaga = datetime.now(timezone.utc)
    return now_ouaga.strftime("%A %d %m %Y %H:%M")


class VoiceLiveClient:
    """
    Client pour gérer les sessions Azure OpenAI Voice Live (Realtime API)
    """
    
    def __init__(self, model_id='gpt-4o-realtime-preview', skip_validation=False):
        """
        Initialise le client Voice Live
        
        Args:
            model_id (str): ID du modèle à utiliser
            skip_validation (bool): Si True, accepte tous les modèles sans validation
        """
        if not AZURE_OPENAI_API_KEY:
            raise ValueError("VOICE_LIVE_KEY ou AZURE_SPEECH_KEY doit être défini dans .env")
        
        if not AZURE_RESOURCE_NAME:
            raise ValueError("VOICE_LIVE_NAME ou AZURE_SPEECH_NAME doit être défini dans .env")
        
        # Voice Live supporte tous les modèles GPT-4o
        if not skip_validation and model_id not in REALTIME_MODELS:
            logger.warning(f"⚠️ Modèle '{model_id}' non dans REALTIME_MODELS, mais Voice Live le supporte")
        
        self.model_id = model_id
        # Utiliser la config du modèle si disponible, sinon config par défaut
        self.model_config = REALTIME_MODELS.get(model_id, {
            'version': '2024-10-01',
            'capacity': 20,
            'deployment_name': model_id,
            'description': f'{model_id} (modèle supporté)'
        })
        self.api_key = AZURE_OPENAI_API_KEY
        self.websocket_base = AZURE_WEBSOCKET_BASE
        
        logger.info(f"✅ Client Voice Live initialisé avec {model_id}")
    
    
    def get_websocket_url(self):
        """
        Construit l'URL WebSocket pour la session Azure AI Foundry Voice Live
        
        Returns:
            str: URL WebSocket complète avec API key et paramètre model
        """
        # Format: wss://<resource>.services.ai.azure.com/voice-live/realtime?api-version=2025-10-01&model=<model>&api-key=<key>
        # Ou pour anciennes ressources: wss://<resource>.cognitiveservices.azure.com/voice-live/realtime?api-version=2025-10-01&model=<model>&api-key=<key>
        api_version = '2025-10-01'
        model_name = self.model_id  # Utiliser l'ID du modèle (gpt-realtime, gpt-realtime-mini, etc.)
        
        # L'URL de base est déjà construite dans __init__ avec le bon format
        url = f"{self.websocket_base}?api-version={api_version}&model={model_name}&api-key={self.api_key}"
        
        logger.debug(f"🔗 WebSocket URL: {url.replace(self.api_key, '***KEY***')}")
        return url
    
    
    def get_session_config(self, agent_config):
        """
        Construit la configuration de session pour l'API Realtime
        
        Args:
            agent_config (dict): Configuration complète de l'agent depuis Cosmos DB
            
        Returns:
            dict: Configuration de session prête pour l'API Realtime
        """
        # Récupérer la voix configurée - essayer plusieurs sources
        voice_name = None
        
        # Essayer d'abord session_config.voice.name (nouveau format)
        if 'session_config' in agent_config and isinstance(agent_config['session_config'], dict):
            voice_info = agent_config['session_config'].get('voice', {})
            if isinstance(voice_info, dict):
                voice_name = voice_info.get('name')
        
        # Fallback sur voice_config.voice_name (ancien format)
        if not voice_name:
            voice_name = agent_config.get('voice_config', {}).get('voice_name')
        
        # Vérifier si c'est une voix OpenAI invalide pour Azure
        if not voice_name or voice_name in ['alloy', 'echo', 'shimmer', 'nova', 'fable', 'onyx']:
            # Si c'est une voix OpenAI ou pas de voix, utiliser la voix Azure par défaut
            voice_name = 'fr-FR-DeniseNeural'
            logger.warning(f"⚠️ Voix OpenAI ou invalide détectée, utilisation de {voice_name}")
        
        logger.info(f"🎤 Voix configurée: {voice_name}")
        
        # Date/heure de Ouagadougou pour le contexte du modèle
        ouaga_datetime_str = get_ouagadougou_datetime_string()

        session_config = {
            'modalities': ['audio', 'text'],
            'instructions': f"Nous sommes (heure de Ouagadougou) : {ouaga_datetime_str}.\n" + agent_config.get('system_prompt', ''),
            'voice': voice_name,
            'input_audio_format': 'pcm16',
            'output_audio_format': 'pcm16',
            'input_audio_transcription': {
                'model': 'whisper-1'
            },
            'turn_detection': {
                'type': 'server_vad',
                'threshold': 0.5,
                'prefix_padding_ms': 300,
                'silence_duration_ms': 500
            },
            'tools': self._build_tools_config(agent_config.get('selected_tools', []))
        }
        
        # Fusionner avec la configuration de session personnalisée si présente
        # Cela écrasera les valeurs par défaut avec celles de l'agent
        if 'session_config' in agent_config and isinstance(agent_config['session_config'], dict):
            custom_config = agent_config['session_config'].copy()
            
            # Gérer la fusion de l'objet voice
            if 'voice' in custom_config and isinstance(custom_config['voice'], dict):
                # Si voice est un objet, le conserver tel quel
                voice_obj = custom_config['voice']
                session_config.update(custom_config)
                session_config['voice'] = voice_obj
            else:
                # Sinon, fusion normale
                session_config.update(custom_config)
        
        logger.info(f"📋 Configuration de session construite pour '{agent_config.get('agent_name', 'Agent')}'")
        logger.debug(f"🔧 Session config: {session_config}")
        return session_config
    
    
    def _build_tools_config(self, selected_tools):
        """
        Construit la configuration des tools pour l'API Realtime
        
        Args:
            selected_tools (list): Liste des noms de tools sélectionnés
            
        Returns:
            list: Configuration des tools au format OpenAI Functions
        """
        # Import dynamique des tools
        import importlib
        
        tools_definitions = []
        
        # Map des noms de tools vers les modules
        tool_modules = {
            'weather': 'tools.tool_weather',
            'email': 'tools.tool_email',
            'cv_builder': 'tools.tool_cv',
            'flight_search': 'tools.tool_flight_search',
            'flight_booking': 'tools.tool_flight_booking',
            'hotel_search': 'tools.tool_hotel_search',
            'hotel_booking': 'tools.tool_hotel_booking',
            'exercises': 'tools.tool_exercises',
            'dogs': 'tools.tool_dogs',
            'knowledge_base': 'tools.tool_knowledge_base',
            'health_advice': 'tools.tool_health_advice',
            'news': 'tools.tool_news',
            'places': 'tools.tool_places',
            'search_web': 'tools.tool_search_web',
            'translator': 'tools.tool_translator',
            'calculator': 'tools.tool_calculator',
            'currency': 'tools.tool_currency'
        }
        
        for tool_name in selected_tools:
            if tool_name in tool_modules:
                try:
                    # Import le module du tool
                    module = importlib.import_module(tool_modules[tool_name])
                    
                    # Récupère la définition du tool
                    if hasattr(module, 'get_tool_definition'):
                        tool_def = module.get_tool_definition()
                        tools_definitions.append(tool_def)
                        logger.debug(f"✅ Tool chargé: {tool_name}")
                except Exception as e:
                    logger.error(f"⚠️ Erreur lors du chargement du tool {tool_name}: {e}")
        
        logger.debug(f"🛠️ {len(tools_definitions)} tool(s) configuré(s)")
        return tools_definitions
    
    
    def get_headers(self):
        """
        Retourne les headers HTTP pour l'authentification
        
        Returns:
            dict: Headers avec API key
        """
        return {
            'api-key': self.api_key
        }
    
    
    def get_model_info(self):
        """
        Retourne les informations sur le modèle configuré
        
        Returns:
            dict: Informations du modèle
        """
        return {
            'model_id': self.model_id,
            'deployment_name': self.model_config['deployment_name'],
            'version': self.model_config['version'],
            'capacity': self.model_config['capacity'],
            'description': self.model_config['description']
        }


# Singleton pour le client par défaut
_default_client = None


def get_voice_live_client(model_id='gpt-4o-realtime-preview'):
    """
    Retourne un client Voice Live configuré
    
    Args:
        model_id (str): ID du modèle à utiliser
        
    Returns:
        VoiceLiveClient: Client configuré
    """
    global _default_client
    
    if _default_client is None or _default_client.model_id != model_id:
        _default_client = VoiceLiveClient(model_id)
    
    return _default_client


def list_available_models():
    """
    Liste tous les modèles Realtime disponibles
    
    Returns:
        dict: Dictionnaire des modèles avec leurs configurations
    """
    return REALTIME_MODELS


# Vérification au démarrage
try:
    if AZURE_OPENAI_API_KEY and AZURE_WEBSOCKET_BASE:
        logger.info("🎯 Module Voice Live configuré avec succès")
    else:
        logger.warning("⚠️ Configuration Voice Live incomplète - vérifiez .env")
except Exception as e:
    logger.error(f"❌ Erreur lors de l'initialisation Voice Live: {e}")
