"""
Blueprint pour l'historique des conversations
Affiche les conversations avec pagination, filtres et modals détaillés
"""
from flask import Blueprint, render_template, request, jsonify
from configuration.cosmos_config import get_call_history_container
from configuration.cost_calculator import calculate_cost_breakdown
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

conversation_history_bp = Blueprint('conversation_history', __name__, url_prefix='/conversations')

@conversation_history_bp.route('/history', methods=['GET'])
def conversation_history():
    """Page d'historique des conversations"""
    return render_template('conversation_history.html')

@conversation_history_bp.route('/api/list', methods=['GET'])
def list_conversations():
    """API pour récupérer la liste des conversations avec pagination et filtres"""
    try:
        # Paramètres de pagination
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        
        # Paramètres de filtre
        date_from = request.args.get('date_from')  # Format: YYYY-MM-DD
        date_to = request.args.get('date_to')
        duration_min = request.args.get('duration_min', type=int)  # en secondes
        duration_max = request.args.get('duration_max', type=int)
        cost_min = request.args.get('cost_min', type=float)
        cost_max = request.args.get('cost_max', type=float)
        model_filter = request.args.get('model')
        agent_name_filter = request.args.get('agent_name')
        status_filter = request.args.get('status')  # Nouveau filtre de status
        
        container = get_call_history_container()
        
        # Construire la requête SQL avec filtres (schéma: started_at, duration_minutes)
        # Modifier pour permettre tous les status si un filtre est appliqué
        if status_filter:
            query = "SELECT * FROM c WHERE c.status = @status"
        else:
            query = "SELECT * FROM c WHERE 1=1"  # Afficher tous les status par défaut
        parameters = []
        
        # Filtre par date (utiliser started_at au lieu de start_time)
        if date_from:
            query += " AND c.started_at >= @date_from"
            parameters.append({"name": "@date_from", "value": f"{date_from}T00:00:00Z"})
        
        if date_to:
            query += " AND c.started_at <= @date_to"
            parameters.append({"name": "@date_to", "value": f"{date_to}T23:59:59Z"})
        
        # Filtre par durée (convertir secondes en minutes)
        if duration_min is not None:
            duration_min_minutes = duration_min / 60.0
            query += " AND c.duration_minutes >= @duration_min"
            parameters.append({"name": "@duration_min", "value": duration_min_minutes})
        
        if duration_max is not None:
            duration_max_minutes = duration_max / 60.0
            query += " AND c.duration_minutes <= @duration_max"
            parameters.append({"name": "@duration_max", "value": duration_max_minutes})
        
        # Filtre par coût
        if cost_min is not None:
            query += " AND c.cost.total_cost >= @cost_min"
            parameters.append({"name": "@cost_min", "value": cost_min})
        
        if cost_max is not None:
            query += " AND c.cost.total_cost <= @cost_max"
            parameters.append({"name": "@cost_max", "value": cost_max})
        
        # Filtre par model
        if model_filter:
            query += " AND c.model = @model"
            parameters.append({"name": "@model", "value": model_filter})
        
        # Filtre par status
        if status_filter:
            parameters.append({"name": "@status", "value": status_filter})
        
        # Filtre par nom d'agent (supprimer car agent_name n'existe pas dans le schéma)
        # if agent_name_filter:
        #     query += " AND CONTAINS(LOWER(c.agent_name), LOWER(@agent_name))"
        #     parameters.append({"name": "@agent_name", "value": agent_name_filter})
        
        # Trier par date décroissante (utiliser started_at)
        query += " ORDER BY c.started_at DESC"
        
        # Exécuter la requête
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        # Pagination
        total_count = len(items)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = items[start_idx:end_idx]
        
        # Formater les résultats (adapter au schéma: conversation[], summary, user_sentiment_analysis, assistant_sentiment_analysis)
        conversations = []
        for item in paginated_items:
            # Récupérer les 3 premiers messages du champ 'conversation'
            messages = item.get('conversation', [])[:3]
            
            # Calculer les KPIs de sentiment depuis user_sentiment_analysis et assistant_sentiment_analysis
            user_sentiment = item.get('user_sentiment_analysis', {})
            assistant_sentiment = item.get('assistant_sentiment_analysis', {})
            
            sentiment_kpis = {
                'user': {
                    'positive': round(user_sentiment.get('positive', 0) * 100, 1),
                    'negative': round(user_sentiment.get('negative', 0) * 100, 1),
                    'neutral': round(user_sentiment.get('neutral', 0) * 100, 1),
                    'total_messages': len([m for m in item.get('conversation', []) if m.get('type') == 'user'])
                },
                'assistant': {
                    'positive': round(assistant_sentiment.get('positive', 0) * 100, 1),
                    'negative': round(assistant_sentiment.get('negative', 0) * 100, 1),
                    'neutral': round(assistant_sentiment.get('neutral', 0) * 100, 1),
                    'total_messages': len([m for m in item.get('conversation', []) if m.get('type') == 'agent'])
                }
            }
            
            # Formater la durée (duration_minutes -> duration_formatted)
            duration_minutes = item.get('duration_minutes', 0)
            duration_formatted = format_duration(duration_minutes * 60)  # Convertir en secondes
            
            conv = {
                'id': item['id'],
                'call_id': item.get('call_id', item['id']),
                'agent_id': item.get('agent_id', 'N/A'),
                'conversation_summary': item.get('summary', 'Aucun résumé disponible'),
                'model': item.get('model', 'N/A'),
                'status': item.get('status', 'completed'),
                'start_time': item.get('started_at'),  # Mapper started_at -> start_time
                'end_time': item.get('ended_at'),  # Mapper ended_at -> end_time
                'duration': duration_minutes * 60,  # En secondes pour compatibilité
                'duration_formatted': duration_formatted,
                'messages_preview': [
                    {
                        'role': msg.get('type'),  # type -> role pour compatibilité template
                        'content': msg.get('content', '')
                    } for msg in messages
                ],
                'message_count': len(item.get('conversation', [])),
                'tokens': item.get('tokens', {}),
                'cost': item.get('cost', {}),
                'sentiment_kpis': sentiment_kpis
            }
            conversations.append(conv)
        
        return jsonify({
            'success': True,
            'conversations': conversations,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size,
                'has_previous': page > 1,
                'has_next': end_idx < total_count
            }
        })
        
    except Exception as e:
        logger.exception("Erreur lors de la récupération des conversations")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@conversation_history_bp.route('/api/details/<call_id>', methods=['GET'])
def get_conversation_details(call_id):
    """API pour récupérer tous les détails d'une conversation"""
    try:
        container = get_call_history_container()
        
        query = "SELECT * FROM c WHERE c.id = @call_id OR c.call_id = @call_id"
        parameters = [{"name": "@call_id", "value": call_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return jsonify({
                'success': False,
                'error': 'Conversation non trouvée'
            }), 404
        
        conversation = items[0]
        
        # Calculer les détails du coût (adapter au nouveau schéma avec cost breakdown détaillé)
        tokens = conversation.get('tokens', {})
        model = conversation.get('model', 'unknown')
        cost_info = conversation.get('cost', {})
        
        # Créer un breakdown compatible avec le format attendu par le template
        cost_breakdown = {
            'model': model,
            'total_cost': cost_info.get('total_cost', 0.0),
            'breakdown': {
                'inputs_text': {
                    'tokens': tokens.get('inputs_text_tokens', 0),
                    'cost': cost_info.get('inputs_text_cost', 0.0)
                },
                'inputs_cached': {
                    'tokens': tokens.get('inputs_cached_tokens', 0),
                    'cost': cost_info.get('inputs_cached_cost', 0.0)
                },
                'inputs_audio': {
                    'tokens': tokens.get('inputs_audio_tokens', 0),
                    'cost': cost_info.get('inputs_audio_cost', 0.0)
                },
                'outputs_text': {
                    'tokens': tokens.get('outputs_text_tokens', 0),
                    'cost': cost_info.get('outputs_text_cost', 0.0)
                },
                'outputs_audio': {
                    'tokens': tokens.get('outputs_audio_tokens', 0),
                    'cost': cost_info.get('outputs_audio_cost', 0.0)
                }
            }
        }
        
        # Calculer les KPIs de sentiment depuis le document
        user_sentiment = conversation.get('user_sentiment_analysis', {})
        assistant_sentiment = conversation.get('assistant_sentiment_analysis', {})
        
        sentiment_kpis = {
            'user': {
                'positive': round(user_sentiment.get('positive', 0) * 100, 1),
                'negative': round(user_sentiment.get('negative', 0) * 100, 1),
                'neutral': round(user_sentiment.get('neutral', 0) * 100, 1),
                'total_messages': len([m for m in conversation.get('conversation', []) if m.get('type') == 'user'])
            },
            'assistant': {
                'positive': round(assistant_sentiment.get('positive', 0) * 100, 1),
                'negative': round(assistant_sentiment.get('negative', 0) * 100, 1),
                'neutral': round(assistant_sentiment.get('neutral', 0) * 100, 1),
                'total_messages': len([m for m in conversation.get('conversation', []) if m.get('type') == 'agent'])
            }
        }
        
        # Formater la durée
        duration_minutes = conversation.get('duration_minutes', 0)
        duration_formatted = format_duration(duration_minutes * 60)
        
        return jsonify({
            'success': True,
            'conversation': {
                'id': conversation['id'],
                'call_id': conversation.get('call_id', conversation['id']),
                'agent_id': conversation.get('agent_id'),
                'model': model,
                'start_time': conversation.get('started_at'),  # Mapper started_at
                'end_time': conversation.get('ended_at'),  # Mapper ended_at
                'duration': duration_minutes * 60,  # En secondes
                'duration_formatted': duration_formatted,
                'messages': [
                    {
                        'role': msg.get('type'),  # Mapper type -> role
                        'content': msg.get('content', ''),
                        'timestamp': msg.get('timestamp')
                    } for msg in conversation.get('conversation', [])
                ],
                'message_count': len(conversation.get('conversation', [])),
                'tokens': tokens,
                'cost': cost_info,
                'cost_breakdown': cost_breakdown,
                'sentiment_kpis': sentiment_kpis
            }
        })
        
    except Exception as e:
        logger.exception(f"Erreur lors de la récupération des détails de {call_id}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@conversation_history_bp.route('/api/models', methods=['GET'])
def get_available_models():
    """API pour récupérer la liste des modèles disponibles"""
    try:
        from configuration.voice_live_config import REALTIME_MODELS
        
        # Récupérer aussi les modèles uniques depuis la base de données
        container = get_call_history_container()
        query = "SELECT DISTINCT c.model FROM c WHERE IS_DEFINED(c.model)"
        
        db_models = set()
        try:
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            db_models = {item['model'] for item in items if item.get('model')}
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des modèles DB: {e}")
        
        # Combiner les modèles configurés et ceux utilisés
        all_models = list(REALTIME_MODELS.keys()) + list(db_models)
        unique_models = sorted(set(all_models))
        
        return jsonify({
            'success': True,
            'models': unique_models
        })
        
    except Exception as e:
        logger.exception("Erreur lors de la récupération des modèles")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@conversation_history_bp.route('/api/end/<call_id>', methods=['POST'])
def end_conversation(call_id):
    """API pour clôturer manuellement une conversation"""
    try:
        container = get_call_history_container()
        
        # Récupérer la conversation
        query = "SELECT * FROM c WHERE c.id = @call_id OR c.call_id = @call_id"
        parameters = [{"name": "@call_id", "value": call_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return jsonify({
                'success': False,
                'error': 'Conversation non trouvée'
            }), 404
        
        conversation = items[0]
        
        # Vérifier si déjà terminée
        if conversation.get('status') == 'completed':
            return jsonify({
                'success': False,
                'error': 'Cette conversation est déjà terminée'
            }), 400
        
        # Mettre à jour le status à 'completed' et ajouter ended_at
        from datetime import datetime, timezone
        
        conversation['status'] = 'completed'
        conversation['ended_at'] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Calculer la durée si pas déjà fait
        if not conversation.get('duration_minutes'):
            started_at = conversation.get('started_at')
            if started_at:
                start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                end_time = datetime.now(timezone.utc)
                duration_seconds = (end_time - start_time).total_seconds()
                conversation['duration_minutes'] = duration_seconds / 60.0
        
        # Sauvegarder
        container.upsert_item(conversation)
        
        logger.info(f"✅ Conversation {call_id} clôturée manuellement")
        
        return jsonify({
            'success': True,
            'message': 'Conversation clôturée avec succès',
            'ended_at': conversation['ended_at']
        })
        
    except Exception as e:
        logger.exception(f"Erreur lors de la clôture de {call_id}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@conversation_history_bp.route('/api/delete/<call_id>', methods=['DELETE'])
def delete_conversation(call_id):
    """API pour supprimer une conversation"""
    try:
        container = get_call_history_container()
        
        # Récupérer d'abord l'item pour avoir la partition key
        query = "SELECT * FROM c WHERE c.id = @call_id OR c.call_id = @call_id"
        parameters = [{"name": "@call_id", "value": call_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        if not items:
            return jsonify({
                'success': False,
                'error': 'Conversation non trouvée'
            }), 404
        
        item = items[0]
        
        # Log pour debug
        logger.info(f"🔍 Suppression conversation:")
        logger.info(f"   - call_id cherché: {call_id}")
        logger.info(f"   - Document trouvé - id: {item['id']}")
        logger.info(f"   - Document trouvé - call_id: {item.get('call_id', 'N/A')}")
        logger.info(f"   - Document trouvé - agent_id: {item.get('agent_id', 'N/A')}")
        
        # Supprimer l'item avec le bon ID et partition key
        # IMPORTANT: Le container CallHistory utilise '/call_id' comme partition key
        container.delete_item(
            item=item['id'],  # Utiliser l'ID du document trouvé
            partition_key=item.get('call_id')  # ✅ Utiliser call_id, pas agent_id
        )
        
        logger.info(f"✅ Conversation {call_id} supprimée (document ID: {item['id']})")
        
        return jsonify({
            'success': True,
            'message': 'Conversation supprimée avec succès'
        })
        
    except Exception as e:
        logger.exception(f"Erreur lors de la suppression de {call_id}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def format_duration(seconds):
    """Formater la durée en format lisible"""
    if not seconds:
        return "0s"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)

logger.info("✅ Blueprint Conversation History enregistré")
