"""
Blueprint pour l'historique des conversations
Affiche la liste des conversations avec analytics et KPIs
"""

from flask import Blueprint, render_template, jsonify, request
from configuration.cosmos_config import get_call_history_container
from configuration.cost_calculator import calculate_cost_breakdown
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

conversations_history_bp = Blueprint('conversations_history', __name__, url_prefix='/conversations')

@conversations_history_bp.route('/history', methods=['GET'])
def conversations_history():
    """
    Page d'historique des conversations avec liste et analytics
    """
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        # Récupérer toutes les conversations
        container = get_call_history_container()
        query = """
            SELECT 
                c.id,
                c.agent_id,
                c.model,
                c.started_at,
                c.ended_at,
                c.duration,
                c.messages,
                c.tokens,
                c.cost,
                c.sentiment_analysis
            FROM c
            WHERE c.type = 'call_history'
            ORDER BY c.started_at DESC
        """
        
        conversations = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        # Calculer pagination
        total = len(conversations)
        start = (page - 1) * page_size
        end = start + page_size
        conversations_page = conversations[start:end]
        
        # Enrichir les données
        for conv in conversations_page:
            # Formater les dates
            if conv.get('started_at'):
                conv['started_at_formatted'] = datetime.fromisoformat(
                    conv['started_at'].replace('Z', '+00:00')
                ).strftime('%d/%m/%Y %H:%M')
            
            # Calculer durée en minutes
            if conv.get('duration'):
                conv['duration_minutes'] = round(conv['duration'] / 60, 1)
            
            # Compter interactions
            messages = conv.get('messages', [])
            conv['total_interactions'] = len(messages)
            conv['user_messages'] = len([m for m in messages if m.get('sender') == 'user'])
            conv['assistant_messages'] = len([m for m in messages if m.get('sender') == 'assistant'])
            
            # Extraire 3 premiers messages
            conv['first_messages'] = messages[:3] if messages else []
            
            # Analyser sentiment
            sentiment = conv.get('sentiment_analysis', {})
            conv['sentiment_stats'] = {
                'user': sentiment.get('user', {'positive': 0, 'negative': 0, 'neutral': 0}),
                'assistant': sentiment.get('assistant', {'positive': 0, 'negative': 0, 'neutral': 0})
            }
            
            # Coût formaté
            total_cost = conv.get('cost', {}).get('total_cost', 0)
            conv['cost_formatted'] = f"${total_cost:.6f}"
        
        return render_template(
            'conversations_history.html',
            conversations=conversations_page,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=(total + page_size - 1) // page_size
        )
        
    except Exception as e:
        logger.exception("Erreur lors de la récupération de l'historique")
        return render_template('errors/500.html', error=str(e)), 500


@conversations_history_bp.route('/api/conversation/<conversation_id>', methods=['GET'])
def get_conversation_details(conversation_id):
    """
    API pour récupérer les détails complets d'une conversation
    """
    try:
        container = get_call_history_container()
        conversation = container.read_item(
            item=conversation_id,
            partition_key=conversation_id
        )
        
        return jsonify({
            'success': True,
            'conversation': conversation
        })
        
    except Exception as e:
        logger.exception(f"Erreur récupération conversation {conversation_id}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@conversations_history_bp.route('/api/conversation/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """
    API pour supprimer une conversation
    """
    try:
        container = get_call_history_container()
        container.delete_item(
            item=conversation_id,
            partition_key=conversation_id
        )
        
        logger.info(f"✅ Conversation {conversation_id} supprimée")
        
        return jsonify({
            'success': True,
            'message': 'Conversation supprimée avec succès'
        })
        
    except Exception as e:
        logger.exception(f"Erreur suppression conversation {conversation_id}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@conversations_history_bp.route('/api/conversation/<conversation_id>/analytics', methods=['GET'])
def get_conversation_analytics(conversation_id):
    """
    API pour récupérer les analytics détaillées d'une conversation
    """
    try:
        container = get_call_history_container()
        conversation = container.read_item(
            item=conversation_id,
            partition_key=conversation_id
        )
        
        # Préparer les données pour les graphiques
        tokens = conversation.get('tokens', {})
        cost_breakdown = conversation.get('cost', {})
        
        # Tokens breakdown
        tokens_data = {
            'labels': ['Input Text', 'Input Cached', 'Input Audio', 'Output Text', 'Output Audio'],
            'values': [
                tokens.get('inputs_text_tokens', 0),
                tokens.get('inputs_cached_tokens', 0),
                tokens.get('inputs_audio_tokens', 0),
                tokens.get('outputs_text_tokens', 0),
                tokens.get('outputs_audio_tokens', 0)
            ]
        }
        
        # Cost breakdown
        cost_data = {
            'labels': ['Input Text', 'Input Cached', 'Input Audio', 'Output Text', 'Output Audio'],
            'values': [
                cost_breakdown.get('inputs_text_cost', 0),
                cost_breakdown.get('inputs_cached_cost', 0),
                cost_breakdown.get('inputs_audio_cost', 0),
                cost_breakdown.get('outputs_text_cost', 0),
                cost_breakdown.get('outputs_audio_cost', 0)
            ]
        }
        
        # Sentiment analysis
        sentiment = conversation.get('sentiment_analysis', {})
        sentiment_data = {
            'user': sentiment.get('user', {'positive': 0, 'negative': 0, 'neutral': 0}),
            'assistant': sentiment.get('assistant', {'positive': 0, 'negative': 0, 'neutral': 0})
        }
        
        return jsonify({
            'success': True,
            'analytics': {
                'tokens': tokens_data,
                'cost': cost_data,
                'sentiment': sentiment_data,
                'total_cost': cost_breakdown.get('total_cost', 0),
                'total_tokens': sum(tokens_data['values']),
                'cost_per_minute': cost_breakdown.get('cost_per_minute', 0)
            }
        })
        
    except Exception as e:
        logger.exception(f"Erreur analytics conversation {conversation_id}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Enregistrement du blueprint dans app.py
logger.info("✅ Blueprint Conversations History enregistré")
logger.info("   Routes disponibles:")
logger.info("   - GET  /conversations/history")
logger.info("   - GET  /conversations/api/conversation/<id>")
logger.info("   - DELETE /conversations/api/conversation/<id>")
logger.info("   - GET  /conversations/api/conversation/<id>/analytics")
