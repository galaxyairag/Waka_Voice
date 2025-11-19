# ===================================================================
# Blueprint Flask : Azure Speech Service - Voice List API
# ===================================================================
# Auteur: Waka AI
# Date: 15 novembre 2025
# Description: API pour gérer la sélection hiérarchique des voix Azure
# ===================================================================

from flask import Blueprint, jsonify, request, current_app
import requests
import os
from functools import lru_cache
import logging
from dotenv import load_dotenv

load_dotenv()

# Configuration du logger
logger = logging.getLogger(__name__)

# ===================================================================
# BLUEPRINT CONFIGURATION
# ===================================================================

azure_voices_bp = Blueprint(
    'azure_voices',
    __name__,
    url_prefix='/api/azure-voices'
)

# ===================================================================
# HELPER FUNCTIONS
# ===================================================================

def get_azure_config():
    """
    Récupère la configuration Azure depuis les variables d'environnement
    ou la configuration Flask
    """
    azure_key = current_app.config.get('AZURE_SPEECH_KEY') or os.getenv('AZURE_SPEECH_KEY')
    azure_region = current_app.config.get('AZURE_SPEECH_REGION') or os.getenv('AZURE_SPEECH_REGION', 'westus')
    
    if not azure_key:
        logger.error("AZURE_SPEECH_KEY n'est pas configurée")
        raise ValueError("AZURE_SPEECH_KEY manquante")
    
    return azure_key, azure_region


def fetch_voices_from_azure():
    """
    Récupère la liste complète des voix depuis Azure Speech Service
    Utilise un cache pour éviter les appels répétés
    """
    try:
        azure_key, azure_region = get_azure_config()
        
        endpoint = f"https://{azure_region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
        headers = {
            "Ocp-Apim-Subscription-Key": azure_key
        }
        
        logger.info(f"Récupération des voix depuis Azure region: {azure_region}")
        
        response = requests.get(endpoint, headers=headers, timeout=10)
        response.raise_for_status()
        
        voices = response.json()
        logger.info(f"✅ {len(voices)} voix récupérées depuis Azure")
        
        return voices
        
    except requests.RequestException as e:
        logger.error(f"❌ Erreur lors de la récupération des voix: {str(e)}")
        raise


# ===================================================================
# ROUTES API
# ===================================================================

@azure_voices_bp.route('/list-all', methods=['GET'])
def get_all_voices():
    """
    Route 1: Récupère la liste complète des voix Azure Speech
    
    Endpoint: GET /api/azure-voices/list-all
    
    Returns:
        JSON: {
            "success": bool,
            "total": int,
            "voices": array
        }
    
    Example:
        GET /api/azure-voices/list-all
    """
    try:
        voices = fetch_voices_from_azure()
        
        return jsonify({
            "success": True,
            "total": len(voices),
            "voices": voices
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "Configuration Azure manquante. Veuillez configurer AZURE_SPEECH_KEY."
        }), 500
        
    except requests.RequestException as e:
        return jsonify({
            "success": False,
            "error": f"Erreur de communication avec Azure: {str(e)}"
        }), 500
        
    except Exception as e:
        logger.exception("Erreur inattendue dans get_all_voices")
        return jsonify({
            "success": False,
            "error": "Erreur serveur interne"
        }), 500


@azure_voices_bp.route('/languages', methods=['GET'])
def get_languages():
    """
    Route 2: Récupère la liste des langues avec statistiques
    
    Endpoint: GET /api/azure-voices/languages
    
    Returns:
        JSON: {
            "success": bool,
            "total": int,
            "languages": [{
                "locale": str,
                "locale_name": str,
                "voice_count": int,
                "female_count": int,
                "male_count": int,
                "neutral_count": int
            }]
        }
    
    Example:
        GET /api/azure-voices/languages
    """
    try:
        voices = fetch_voices_from_azure()
        
        # Grouper par langue et compter par genre
        languages = {}
        
        for voice in voices:
            locale = voice.get('Locale', 'unknown')
            locale_name = voice.get('LocaleName', locale)
            
            if locale not in languages:
                languages[locale] = {
                    "locale": locale,
                    "locale_name": locale_name,
                    "voice_count": 0,
                    "female_count": 0,
                    "male_count": 0,
                    "neutral_count": 0
                }
            
            languages[locale]["voice_count"] += 1
            
            # Compter par genre
            gender = voice.get('Gender', 'Unknown')
            if gender == 'Female':
                languages[locale]["female_count"] += 1
            elif gender == 'Male':
                languages[locale]["male_count"] += 1
            else:
                languages[locale]["neutral_count"] += 1
        
        # Trier par locale
        sorted_languages = sorted(languages.values(), key=lambda x: x['locale'])
        
        return jsonify({
            "success": True,
            "total": len(sorted_languages),
            "languages": sorted_languages
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "Configuration Azure manquante"
        }), 500
        
    except Exception as e:
        logger.exception("Erreur dans get_languages")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@azure_voices_bp.route('/genders-by-locale', methods=['GET'])
def get_genders_by_locale():
    """
    Route 3: Récupère les genres disponibles pour une langue donnée
    
    Endpoint: GET /api/azure-voices/genders-by-locale?locale=fr-FR
    
    Query Parameters:
        locale (str, required): Code de langue (ex: fr-FR, en-US)
    
    Returns:
        JSON: {
            "success": bool,
            "locale": str,
            "genders": [{
                "gender": str,
                "count": int,
                "emoji": str
            }]
        }
    
    Example:
        GET /api/azure-voices/genders-by-locale?locale=fr-FR
    """
    try:
        locale = request.args.get('locale', '').strip()
        
        if not locale:
            return jsonify({
                "success": False,
                "error": "Le paramètre 'locale' est requis"
            }), 400
        
        voices = fetch_voices_from_azure()
        
        # Filtrer par locale et compter par genre
        locale_voices = [v for v in voices if v.get('Locale', '').lower() == locale.lower()]
        
        if not locale_voices:
            return jsonify({
                "success": False,
                "error": f"Aucune voix trouvée pour la langue '{locale}'"
            }), 404
        
        genders = {}
        for voice in locale_voices:
            gender = voice.get('Gender', 'Unknown')
            if gender not in genders:
                genders[gender] = {
                    "gender": gender,
                    "count": 0,
                    "emoji": "👤" if gender == "Male" else ("👩" if gender == "Female" else "⚪")
                }
            genders[gender]["count"] += 1
        
        return jsonify({
            "success": True,
            "locale": locale,
            "genders": list(genders.values())
        })
        
    except Exception as e:
        logger.exception("Erreur dans get_genders_by_locale")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@azure_voices_bp.route('/voices-by-locale', methods=['GET'])
def get_voices_by_locale():
    """
    Route 4: Récupère les voix filtrées par langue et genre
    
    Endpoint: GET /api/azure-voices/voices-by-locale?locale=fr-FR&gender=Female
    
    Query Parameters:
        locale (str, required): Code de langue (ex: fr-FR)
        gender (str, optional): Genre de la voix (Female, Male, ou vide pour tous)
    
    Returns:
        JSON: {
            "success": bool,
            "locale": str,
            "gender": str,
            "total": int,
            "voices": [...]
        }
    
    Example:
        GET /api/azure-voices/voices-by-locale?locale=fr-FR&gender=Female
    """
    try:
        locale = request.args.get('locale', '').strip()
        gender = request.args.get('gender', '').strip()
        
        if not locale:
            return jsonify({
                "success": False,
                "error": "Le paramètre 'locale' est requis"
            }), 400
        
        voices = fetch_voices_from_azure()
        
        # Filtrer par locale
        filtered_voices = [v for v in voices if v.get('Locale', '').lower() == locale.lower()]
        
        # Filtrer par genre si spécifié
        if gender:
            filtered_voices = [v for v in filtered_voices if v.get('Gender', '').lower() == gender.lower()]
        
        # Formater les voix pour l'interface
        formatted_voices = []
        for voice in filtered_voices:
            formatted_voices.append({
                "name": voice.get('Name', ''),
                "display_name": voice.get('DisplayName', ''),
                "local_name": voice.get('LocalName', ''),
                "short_name": voice.get('ShortName', ''),
                "gender": voice.get('Gender', 'Unknown'),
                "locale": voice.get('Locale', ''),
                "locale_name": voice.get('LocaleName', ''),
                "sample_rate_hertz": voice.get('SampleRateHertz', 24000),
                "voice_type": voice.get('VoiceType', 'Standard'),
                "status": voice.get('Status', 'GA'),
                "styles": voice.get('StyleList', []),
                "roles": voice.get('RolePlayList', []),
                "words_per_minute": voice.get('WordsPerMinute', 0)
            })
        
        return jsonify({
            "success": True,
            "locale": locale,
            "gender": gender if gender else "all",
            "total": len(formatted_voices),
            "voices": formatted_voices
        })
        
    except Exception as e:
        logger.exception("Erreur dans get_voices_by_locale")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@azure_voices_bp.route('/voice-details', methods=['GET'])
def get_voice_details():
    """
    Route 5: Récupère les détails complets d'une voix spécifique
    
    Endpoint: GET /api/azure-voices/voice-details?name=fr-FR-DeniseNeural
    
    Query Parameters:
        name (str, required): Nom complet de la voix ou ShortName
    
    Returns:
        JSON: {
            "success": bool,
            "voice": {...}
        }
    
    Example:
        GET /api/azure-voices/voice-details?name=fr-FR-DeniseNeural
    """
    try:
        voice_name = request.args.get('name', '').strip()
        
        if not voice_name:
            return jsonify({
                "success": False,
                "error": "Le paramètre 'name' est requis"
            }), 400
        
        voices = fetch_voices_from_azure()
        
        # Trouver la voix
        voice = next(
            (v for v in voices if v.get('Name', '') == voice_name or v.get('ShortName', '') == voice_name),
            None
        )
        
        if not voice:
            return jsonify({
                "success": False,
                "error": f"Voix '{voice_name}' non trouvée"
            }), 404
        
        return jsonify({
            "success": True,
            "voice": voice
        })
        
    except Exception as e:
        logger.exception("Erreur dans get_voice_details")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ===================================================================
# HEALTH CHECK
# ===================================================================

@azure_voices_bp.route('/health', methods=['GET'])
def health_check():
    """
    Route de santé pour vérifier la disponibilité de l'API Azure
    
    Endpoint: GET /api/azure-voices/health
    
    Returns:
        JSON: {
            "status": str,
            "azure_configured": bool,
            "region": str
        }
    """
    try:
        azure_key, azure_region = get_azure_config()
        
        return jsonify({
            "status": "healthy",
            "azure_configured": True,
            "region": azure_region
        })
        
    except ValueError:
        return jsonify({
            "status": "unhealthy",
            "azure_configured": False,
            "error": "AZURE_SPEECH_KEY non configurée"
        }), 500


# ===================================================================
# ERROR HANDLERS
# ===================================================================

@azure_voices_bp.errorhandler(404)
def not_found(error):
    """Gestionnaire d'erreur 404"""
    return jsonify({
        "success": False,
        "error": "Endpoint non trouvé"
    }), 404


@azure_voices_bp.errorhandler(500)
def internal_error(error):
    """Gestionnaire d'erreur 500"""
    logger.exception("Erreur serveur interne")
    return jsonify({
        "success": False,
        "error": "Erreur serveur interne"
    }), 500


# ===================================================================
# BLUEPRINT INITIALIZATION
# ===================================================================

def init_app(app):
    """
    Initialise le Blueprint avec l'application Flask
    
    Usage dans app.py:
        from blueprints.azure_voices import azure_voices_bp, init_app
        init_app(app)
    
    Args:
        app: Instance Flask
    """
    # Enregistrer le blueprint
    app.register_blueprint(azure_voices_bp)
    
    # Log de confirmation
    logger.info("✅ Blueprint Azure Voices enregistré")
    logger.info(f"   Routes disponibles:")
    logger.info(f"   - GET /api/azure-voices/list-all")
    logger.info(f"   - GET /api/azure-voices/languages")
    logger.info(f"   - GET /api/azure-voices/genders-by-locale")
    logger.info(f"   - GET /api/azure-voices/voices-by-locale")
    logger.info(f"   - GET /api/azure-voices/voice-details")
    logger.info(f"   - GET /api/azure-voices/health")

