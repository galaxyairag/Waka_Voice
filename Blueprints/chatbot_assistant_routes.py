"""
Blueprint pour le Chatbot Assistant
API pour le chatbot RAG qui aide à configurer les agents
"""

from flask import Blueprint, request, jsonify, session
import logging
import uuid

logger = logging.getLogger(__name__)

chatbot_assistant_bp = Blueprint('chatbot_assistant', __name__, url_prefix='/api/chatbot')


def get_user_id():
    """Génère ou récupère un ID utilisateur pour la session."""
    if 'chatbot_user_id' not in session:
        session['chatbot_user_id'] = str(uuid.uuid4())
    return session['chatbot_user_id']


@chatbot_assistant_bp.route('/message', methods=['POST'])
def process_message():
    """
    Traite un message utilisateur et retourne une réponse.

    Body JSON:
        - message (str): Message de l'utilisateur

    Returns:
        JSON avec la réponse du chatbot
    """
    try:
        from tools.tool_agent_assistant import get_tool_instance

        data = request.get_json()
        message = data.get('message', '').strip()

        if not message:
            return jsonify({
                'success': False,
                'error': 'Message vide'
            }), 400

        user_id = get_user_id()
        tool = get_tool_instance()

        # Traiter le message
        result = tool.process_message(user_id, message)

        logger.info(f"Chatbot message traité - Type: {result.get('type')}")

        return jsonify({
            'success': True,
            'type': result.get('type'),
            'response': result.get('response'),
            'agent_config': result.get('agent_config'),
            'question_id': result.get('question_id'),
            'category': result.get('category')
        })

    except Exception as e:
        logger.exception("Erreur traitement message chatbot")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_assistant_bp.route('/documentation', methods=['GET'])
def get_documentation():
    """
    Récupère la documentation des paramètres.

    Query params:
        - category (str, optional): Catégorie spécifique

    Returns:
        JSON avec la documentation
    """
    try:
        from tools.tool_agent_assistant import get_parameter_documentation, PARAMETERS_DOCUMENTATION

        category = request.args.get('category')

        if category and category not in PARAMETERS_DOCUMENTATION:
            return jsonify({
                'success': False,
                'error': f"Catégorie '{category}' non trouvée",
                'categories_disponibles': list(PARAMETERS_DOCUMENTATION.keys())
            }), 400

        doc = get_parameter_documentation(category)

        return jsonify({
            'success': True,
            'documentation': doc,
            'category': category,
            'categories': list(PARAMETERS_DOCUMENTATION.keys())
        })

    except Exception as e:
        logger.exception("Erreur récupération documentation")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_assistant_bp.route('/documentation/categories', methods=['GET'])
def list_documentation_categories():
    """
    Liste toutes les catégories de documentation disponibles.

    Returns:
        JSON avec la liste des catégories
    """
    try:
        from tools.tool_agent_assistant import PARAMETERS_DOCUMENTATION

        categories = []
        for cat_id, cat_data in PARAMETERS_DOCUMENTATION.items():
            categories.append({
                'id': cat_id,
                'titre': cat_data.get('titre'),
                'description': cat_data.get('description')
            })

        return jsonify({
            'success': True,
            'categories': categories
        })

    except Exception as e:
        logger.exception("Erreur listing catégories")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_assistant_bp.route('/search', methods=['GET'])
def search_documentation():
    """
    Recherche dans la documentation.

    Query params:
        - q (str): Requête de recherche

    Returns:
        JSON avec les résultats
    """
    try:
        from tools.tool_agent_assistant import search_documentation as search_doc

        query = request.args.get('q', '').strip()

        if not query:
            return jsonify({
                'success': False,
                'error': 'Requête de recherche vide'
            }), 400

        results = search_doc(query)

        return jsonify({
            'success': True,
            'query': query,
            'results': results
        })

    except Exception as e:
        logger.exception("Erreur recherche documentation")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_assistant_bp.route('/create-agent', methods=['POST'])
def create_agent():
    """
    Crée un agent à partir d'une configuration générée par le chatbot.

    Body JSON:
        - agent_config (dict): Configuration de l'agent générée

    Returns:
        JSON avec le résultat de la création
    """
    try:
        from tools.tool_agent_assistant import get_tool_instance

        data = request.get_json()
        agent_config = data.get('agent_config')

        if not agent_config:
            return jsonify({
                'success': False,
                'error': 'Configuration d\'agent manquante'
            }), 400

        tool = get_tool_instance()
        result = tool.save_agent_config(agent_config)

        if result.get('success'):
            logger.info(f"Agent créé via chatbot: {result.get('agent_id')}")
            return jsonify({
                'success': True,
                'agent_id': result.get('agent_id'),
                'message': result.get('message')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error')
            }), 500

    except Exception as e:
        logger.exception("Erreur création agent via chatbot")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@chatbot_assistant_bp.route('/reset', methods=['POST'])
def reset_conversation():
    """
    Réinitialise l'état de conversation du chatbot.

    Returns:
        JSON confirmant la réinitialisation
    """
    try:
        from tools.tool_agent_assistant import get_tool_instance

        user_id = get_user_id()
        tool = get_tool_instance()
        tool.reset_conversation(user_id)

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
    Liste tous les outils disponibles pour les agents.

    Returns:
        JSON avec la liste des outils
    """
    try:
        from tools.tool_agent_assistant import PARAMETERS_DOCUMENTATION

        tools_doc = PARAMETERS_DOCUMENTATION.get('outils_disponibles', {})
        tools_params = tools_doc.get('parametres', {})

        tools = []
        for tool_id, tool_info in tools_params.items():
            tools.append({
                'id': tool_id,
                'nom': tool_info.get('nom'),
                'description': tool_info.get('description'),
                'cas_usage': tool_info.get('cas_usage')
            })

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
        data = request.get_json()
        use_case = data.get('use_case', '').lower()

        if not use_case:
            return jsonify({
                'success': False,
                'error': 'Description du cas d\'usage manquante'
            }), 400

        # Suggestions basées sur des mots-clés
        suggestions = {
            'model': 'gpt-4o-realtime-preview',
            'voice': 'fr-FR-DeniseNeural',
            'temperature': 0.8,
            'silence_duration_ms': 500,
            'tools': ['end_conversation']
        }

        # Support client
        if any(kw in use_case for kw in ['support', 'client', 'aide', 'assistance']):
            suggestions['temperature'] = 0.6
            suggestions['silence_duration_ms'] = 700
            suggestions['tools'].extend(['email', 'knowledge_base', 'search_web'])
            suggestions['conseil'] = "Pour le support client, utilisez une température basse pour des réponses précises."

        # Réservation / Voyage
        if any(kw in use_case for kw in ['réservation', 'reservation', 'voyage', 'vol', 'hôtel', 'hotel']):
            suggestions['tools'].extend(['flight_search', 'flight_booking', 'hotel_search', 'hotel_booking', 'currency'])
            suggestions['conseil'] = "Pour les réservations, incluez les outils de recherche et réservation de vols/hôtels."

        # Information générale
        if any(kw in use_case for kw in ['information', 'renseignement', 'faq']):
            suggestions['tools'].extend(['search_web', 'weather', 'news', 'places'])
            suggestions['conseil'] = "Pour l'information générale, activez la recherche web et les actualités."

        # Administratif
        if any(kw in use_case for kw in ['administratif', 'papiers', 'impôt', 'impot', 'gouvernement']):
            suggestions['tools'].extend(['government_services', 'tax_calculator'])
            suggestions['conseil'] = "Pour les démarches administratives, utilisez les outils gouvernementaux."

        # Santé
        if any(kw in use_case for kw in ['santé', 'sante', 'médical', 'medical', 'pharmacie']):
            suggestions['tools'].extend(['health_advice', 'pharmacy_locator', 'exercises'])
            suggestions['temperature'] = 0.5
            suggestions['conseil'] = "Pour la santé, gardez une température basse pour des conseils précis."

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


logger.info("Blueprint Chatbot Assistant enregistré")
