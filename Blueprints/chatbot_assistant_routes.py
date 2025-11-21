"""
Blueprint pour le Chatbot Assistant
API pour le chatbot RAG avec Azure OpenAI qui aide à configurer les agents
"""

from flask import Blueprint, request, jsonify, session
import logging
import uuid

logger = logging.getLogger(__name__)

chatbot_assistant_bp = Blueprint('chatbot_assistant', __name__, url_prefix='/api/chatbot')


def get_session_id():
    """Génère ou récupère un ID de session pour le chatbot."""
    if 'chatbot_session_id' not in session:
        session['chatbot_session_id'] = str(uuid.uuid4())
    return session['chatbot_session_id']


@chatbot_assistant_bp.route('/message', methods=['POST'])
def process_message():
    """
    Traite un message utilisateur via Azure OpenAI avec RAG.

    Body JSON:
        - message (str): Message de l'utilisateur
        - include_rag (bool, optional): Inclure la recherche RAG (default: True)

    Returns:
        JSON avec la réponse du chatbot, les sources RAG et les résultats d'outils
    """
    try:
        from services.chatbot_assistant_service import get_chatbot_service

        data = request.get_json()
        message = data.get('message', '').strip()
        include_rag = data.get('include_rag', True)

        if not message:
            return jsonify({
                'success': False,
                'error': 'Message vide'
            }), 400

        session_id = get_session_id()
        service = get_chatbot_service()

        # Traiter le message via Azure OpenAI
        result = service.process_message(session_id, message, include_rag)

        if result.get('success'):
            logger.info(f"Chatbot message traité - Session: {session_id[:8]}...")
            return jsonify({
                'success': True,
                'response': result.get('response'),
                'tool_results': result.get('tool_results', []),
                'rag_sources': result.get('rag_sources', [])
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Erreur inconnue')
            }), 500

    except ValueError as e:
        # Configuration Azure OpenAI manquante
        logger.error(f"Configuration manquante: {e}")
        return jsonify({
            'success': False,
            'error': 'Service chatbot non configuré. Vérifiez les variables d\'environnement Azure OpenAI.'
        }), 503

    except Exception as e:
        logger.exception("Erreur traitement message chatbot")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_assistant_bp.route('/reset', methods=['POST'])
def reset_conversation():
    """
    Réinitialise l'historique de conversation du chatbot.

    Returns:
        JSON confirmant la réinitialisation
    """
    try:
        from services.chatbot_assistant_service import get_chatbot_service

        session_id = get_session_id()
        service = get_chatbot_service()
        service.reset_conversation(session_id)

        # Générer un nouveau session ID
        session['chatbot_session_id'] = str(uuid.uuid4())

        return jsonify({
            'success': True,
            'message': 'Conversation réinitialisée'
        })

    except Exception as e:
        logger.exception("Erreur réinitialisation conversation")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_assistant_bp.route('/tools', methods=['GET'])
def list_available_tools():
    """
    Liste tous les outils disponibles pour les agents vocaux.

    Returns:
        JSON avec la liste des outils
    """
    try:
        from services.chatbot_assistant_service import AVAILABLE_TOOLS

        tools = [
            {'id': tool_id, 'description': desc}
            for tool_id, desc in AVAILABLE_TOOLS.items()
        ]

        return jsonify({
            'success': True,
            'tools': tools,
            'count': len(tools)
        })

    except Exception as e:
        logger.exception("Erreur listing tools")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_assistant_bp.route('/voices', methods=['GET'])
def list_available_voices():
    """
    Liste les voix Azure disponibles.

    Query params:
        - language (str, optional): Code langue (fr-FR, en-US, etc.)

    Returns:
        JSON avec la liste des voix
    """
    try:
        from services.chatbot_assistant_service import AVAILABLE_VOICES

        language = request.args.get('language', 'fr-FR')
        voices = AVAILABLE_VOICES.get(language, AVAILABLE_VOICES.get('fr-FR', []))

        return jsonify({
            'success': True,
            'language': language,
            'voices': voices,
            'available_languages': list(AVAILABLE_VOICES.keys())
        })

    except Exception as e:
        logger.exception("Erreur listing voices")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_assistant_bp.route('/parameters', methods=['GET'])
def get_parameters_help():
    """
    Retourne l'aide sur les paramètres de configuration.

    Query params:
        - name (str, optional): Nom du paramètre spécifique

    Returns:
        JSON avec la documentation des paramètres
    """
    try:
        from services.chatbot_assistant_service import PARAMETERS_HELP

        param_name = request.args.get('name')

        if param_name:
            if param_name.lower() in PARAMETERS_HELP:
                return jsonify({
                    'success': True,
                    'parameter': param_name,
                    'info': PARAMETERS_HELP[param_name.lower()]
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f"Paramètre '{param_name}' non trouvé",
                    'available_parameters': list(PARAMETERS_HELP.keys())
                }), 404
        else:
            return jsonify({
                'success': True,
                'parameters': PARAMETERS_HELP
            })

    except Exception as e:
        logger.exception("Erreur récupération aide paramètres")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_assistant_bp.route('/suggest-config', methods=['POST'])
def suggest_configuration():
    """
    Suggère une configuration basée sur un cas d'usage décrit.

    Body JSON:
        - use_case (str): Description du cas d'usage

    Returns:
        JSON avec les suggestions de configuration
    """
    try:
        from services.chatbot_assistant_service import AVAILABLE_TOOLS

        data = request.get_json()
        use_case = data.get('use_case', '').lower()

        if not use_case:
            return jsonify({
                'success': False,
                'error': 'Description du cas d\'usage manquante'
            }), 400

        # Configuration par défaut
        suggestions = {
            'model': 'gpt-4o-realtime-preview',
            'voice': 'fr-FR-DeniseNeural',
            'temperature': 0.8,
            'silence_duration_ms': 500,
            'tools': ['end_conversation'],
            'tone': 'professionnel'
        }

        # Support client
        if any(kw in use_case for kw in ['support', 'client', 'aide', 'assistance', 'service']):
            suggestions['temperature'] = 0.6
            suggestions['silence_duration_ms'] = 700
            suggestions['tools'].extend(['email', 'knowledge_base', 'search_web'])
            suggestions['conseil'] = "Pour le support client, utilisez une température basse pour des réponses précises."
            suggestions['tone'] = 'professionnel'

        # Réservation / Voyage
        elif any(kw in use_case for kw in ['réservation', 'reservation', 'voyage', 'vol', 'hôtel', 'hotel', 'tourisme']):
            suggestions['tools'].extend(['flight_search', 'flight_booking', 'hotel_search', 'hotel_booking', 'currency', 'weather'])
            suggestions['conseil'] = "Pour les réservations, incluez les outils de recherche et réservation de vols/hôtels."
            suggestions['tone'] = 'amical'

        # Information générale
        elif any(kw in use_case for kw in ['information', 'renseignement', 'faq', 'accueil']):
            suggestions['tools'].extend(['search_web', 'weather', 'news', 'places'])
            suggestions['conseil'] = "Pour l'information générale, activez la recherche web et les actualités."
            suggestions['tone'] = 'amical'

        # Administratif
        elif any(kw in use_case for kw in ['administratif', 'papiers', 'impôt', 'impot', 'gouvernement', 'mairie']):
            suggestions['tools'].extend(['government_services', 'tax_calculator'])
            suggestions['conseil'] = "Pour les démarches administratives, utilisez les outils gouvernementaux."
            suggestions['tone'] = 'formel'

        # Santé
        elif any(kw in use_case for kw in ['santé', 'sante', 'médical', 'medical', 'pharmacie', 'docteur']):
            suggestions['tools'].extend(['health_advice', 'pharmacy_locator', 'exercises'])
            suggestions['temperature'] = 0.5
            suggestions['conseil'] = "Pour la santé, gardez une température basse pour des conseils précis."
            suggestions['tone'] = 'professionnel'

        # Commercial / Vente
        elif any(kw in use_case for kw in ['vente', 'commercial', 'produit', 'boutique', 'shop']):
            suggestions['tools'].extend(['search_web', 'calculator', 'email'])
            suggestions['temperature'] = 0.7
            suggestions['conseil'] = "Pour la vente, un ton engageant et des outils de calcul sont recommandés."
            suggestions['tone'] = 'amical'

        # Supprimer les doublons
        suggestions['tools'] = list(dict.fromkeys(suggestions['tools']))

        return jsonify({
            'success': True,
            'use_case': use_case,
            'suggestions': suggestions
        })

    except Exception as e:
        logger.exception("Erreur suggestion configuration")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_assistant_bp.route('/health', methods=['GET'])
def health_check():
    """
    Vérifie l'état du service chatbot.

    Returns:
        JSON avec le statut du service
    """
    try:
        from services.chatbot_assistant_service import get_chatbot_service

        # Tente d'instancier le service
        service = get_chatbot_service()

        return jsonify({
            'success': True,
            'status': 'healthy',
            'service': 'ChatbotAssistantService',
            'azure_openai': 'configured'
        })

    except ValueError as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'azure_openai': 'not_configured'
        }), 503

    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': str(e)
        }), 500


logger.info("Blueprint Chatbot Assistant (Azure OpenAI) enregistré")
