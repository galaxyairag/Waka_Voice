# ===================================================================
# Route Flask : Agent Config Step 2 - Configuration Voice Live
# ===================================================================
# Blueprint pour la configuration des agents Voice Live
# ===================================================================

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
import logging
from azure.storage.blob import BlobServiceClient
import os
import requests
from configuration.cosmos_config import (
    save_agent_config,
    get_agent_config as cosmos_get_agent_config,
    update_agent_status,
    delete_agent_config
)
from configuration.voice_live_config import VoiceLiveClient, REALTIME_MODELS

# Configuration du logger
logger = logging.getLogger(__name__)

# Blueprint
agents_config_bp = Blueprint(
    'agents_manager',
    __name__,
    url_prefix='/agents'
)

# ===================================================================
# STEP 1 : Sélection du modèle
# ===================================================================

# ===================================================================

@agents_config_bp.route('/config/step1', methods=['GET'])
def agent_config_step1():
    """
    Page de sélection du modèle (Étape 1)
    """
    try:
        logger.info("📱 Accès à la page de configuration Step 1")
        return render_template('agents/agent_config_step1.html')
    except Exception as e:
        logger.exception(f"❌ Erreur lors du rendu de Step 1: {str(e)}")
        return jsonify({"success": False, "error": "Erreur lors du chargement de la page"}), 500


# ===================================================================
# STEP 2 : Configuration Voice Live
# ===================================================================

@agents_config_bp.route('/config/step2', methods=['POST'])
def agent_config_step2_create():
    """
    Crée un nouvel agent et redirige vers step2 avec l'agent_id
    
    Reçoit les données du modèle sélectionné depuis Step 1,
    génère un agent_id et redirige vers la page de configuration.
    """
    try:
        from configuration import save_agent_config
        from datetime import datetime
        import uuid
        
        # Récupérer les données du formulaire Step 1
        config_type = request.form.get('config_type', '')
        model_id = request.form.get('model_id', '')
        model_name = request.form.get('model_name', '')
        model_description = request.form.get('model_description', '')
        model_family = request.form.get('model_family', 'F1_Realtime')
        
        logger.info(f"Step 2 - Modèle sélectionné: {model_id} ({model_family})")
        
        # Générer un agent_id unique pour cette configuration
        agent_id = str(uuid.uuid4())
        
        # Créer la configuration initiale dans Cosmos DB
        initial_config = {
            'id': agent_id,
            'agent_id': agent_id,
            'agent_name': f"Agent {model_name}",  # Nom par défaut, sera changé plus tard
            'status': 'step1_completed',  # Statut de l'étape achevée
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'config_type': config_type,
            'model_id': model_id,
            'model_name': model_name,
            'model_description': model_description,
            'model_family': model_family,
            'current_step': 2,  # Prochaine étape à compléter
            'metadata': {
                'version': 1,
                'test_count': 0
            }
        }
        
        # Sauvegarder dans Cosmos DB
        saved_config = save_agent_config(initial_config)
        logger.info(f"✅ Configuration initiale sauvegardée dans Cosmos DB (agent_id: {agent_id})")
        
        # Rediriger vers la page Step 2 avec l'agent_id dans l'URL
        return redirect(url_for('agents_manager.agent_config_step2', agent_id=agent_id))
            
    except Exception as e:
        logger.exception("Erreur dans agent_config_step2_create")
        return jsonify({
            "success": False,
            "error": f"Erreur lors du chargement: {str(e)}"
        }), 500


@agents_config_bp.route('/config/<agent_id>/step2', methods=['GET'])
def agent_config_step2(agent_id):
    """
    Affiche la page de configuration Voice Live (Step 2)
    
    Récupère la configuration depuis Cosmos DB et affiche le formulaire.
    """
    try:
        from configuration import get_agent_config
        
        # Récupérer la configuration depuis Cosmos DB
        agent_config = get_agent_config(agent_id)
        
        if not agent_config:
            logger.warning(f"Agent {agent_id} non trouvé")
            return redirect(url_for('agents_manager.agent_config_step1'))
        
        logger.info(f"📋 Chargement config pour agent {agent_id}: {len(agent_config)} champs")
        
        # Afficher le template avec TOUTE la configuration (valeurs individuelles)
        return render_template(
            'agents/agent_config_step2.html',
            agent_id=agent_id,
            config_type=agent_config.get('config_type', ''),
            model_id=agent_config.get('model_id', ''),
            model_name=agent_config.get('model_name', ''),
            model_description=agent_config.get('model_description', ''),
            model_family=agent_config.get('model_family', 'F1_Realtime'),
            # Passer TOUTES les valeurs individuellement pour remplir le formulaire
            config=agent_config
        )
            
    except Exception as e:
        logger.exception("Erreur dans agent_config_step2")
        return jsonify({
            "success": False,
            "error": f"Erreur lors du chargement: {str(e)}"
        }), 500


# ===================================================================
# STEP 3 : Finalisation et création de l'agent
# ===================================================================

@agents_config_bp.route('/config/<agent_id>/step3', methods=['GET', 'POST'])
def agent_config_step3(agent_id):
    """
    Traite le formulaire Step 2 et affiche la page de finalisation (Step 3)
    
    Reçoit toute la configuration Voice Live et permet de:
    - Donner un nom à l'agent
    - Ajouter une description
    - Valider la configuration finale
    - Créer l'agent
    """
    try:
        from configuration import save_agent_config, get_agent_config
        from datetime import datetime
        
        # GET: Afficher la page avec la config de Cosmos
        if request.method == 'GET':
            agent_config = get_agent_config(agent_id)
            
            if not agent_config:
                logger.warning(f"Agent {agent_id} non trouvé")
                return redirect(url_for('agents_manager.agent_config_step1'))
            
            return render_template(
                'agents/agent_config_step3.html',
                agent_id=agent_id,
                config=agent_config
            )
        
        # POST: Récupérer TOUTES les données du formulaire Step 2
        form_data = request.form.to_dict()
        
        logger.info("Step 3 - Configuration reçue:")
        logger.info(f"Nombre de paramètres: {len(form_data)}")
        
        # Récupérer la configuration depuis Cosmos
        agent_config = get_agent_config(agent_id)
        if not agent_config:
            return jsonify({
                "success": False,
                "error": "Configuration non trouvée"
            }), 404
        
        # Helper function pour convertir en int de manière sécurisée
        def safe_int(value, default):
            try:
                return int(value) if value and str(value).strip() else default
            except (ValueError, TypeError):
                return default
        
        # Helper function pour convertir en float de manière sécurisée
        def safe_float(value, default):
            try:
                return float(value) if value and str(value).strip() else default
            except (ValueError, TypeError):
                return default
        
        # Déterminer les modalités selon la famille du modèle
        model_family = agent_config.get('model_family', 'F1_Realtime')
        modalities = ['text', 'audio'] if 'Realtime' in model_family else ['text']
        
        # Construire phrase_list depuis le textarea
        phrase_list_raw = form_data.get('phrase_list', '')
        phrase_list = [phrase.strip() for phrase in phrase_list_raw.split('\n') if phrase.strip()] if phrase_list_raw else None
        
        # Construire languages depuis les checkboxes sélectionnées
        vad_languages = request.form.getlist('vad_languages')
        vad_languages = vad_languages if vad_languages else None
        
        # Construire la configuration de session
        session_config = {
            # Modalités (hardcodées selon famille modèle)
            'modalities': modalities,
            
            # Input Audio - Formats hardcodés PCM16
            'input_audio_format': 'pcm16',
            'output_audio_format': 'pcm16',
            'input_audio_sampling_rate': safe_int(form_data.get('input_audio_sampling_rate'), 24000),
            'input_audio_echo_cancellation': {
                'type': 'server_echo_cancellation'
            } if form_data.get('enable_echo_cancellation') else None,
            'input_audio_noise_reduction': {
                'type': 'azure_deep_noise_suppression'
            } if form_data.get('enable_noise_reduction') else None,
            
            # Input Transcription
            'input_audio_transcription': {
                'model': form_data.get('input_transcription_model', ''),
                'language': form_data.get('transcription_languages', ''),
                'phrase_list': phrase_list
            } if form_data.get('input_transcription_model') else None,
            
            # Turn Detection (VAD)
            'turn_detection': {
                'type': form_data.get('vad_type', 'server_vad'),
                'threshold': safe_float(form_data.get('threshold'), 0.5),
                'prefix_padding_ms': safe_int(form_data.get('prefix_padding_ms'), 300),
                'speech_duration_ms': safe_int(form_data.get('speech_duration_ms'), 80),
                'silence_duration_ms': safe_int(form_data.get('silence_duration_ms'), 500),
                'remove_filler_words': form_data.get('remove_filler_words') == 'on',
                'languages': vad_languages,
                'create_response': form_data.get('create_response') == 'on',
                'eagerness': form_data.get('eagerness', 'auto'),
                'interrupt_response': form_data.get('interrupt_response') == 'on',
                'auto_truncate': form_data.get('auto_truncate') == 'on',
                
                # End of Utterance Detection
                'end_of_utterance_detection': {
                    'model': form_data.get('end_of_utterance_model', ''),
                    'threshold_level': form_data.get('threshold_level', 'medium'),
                    'timeout_ms': safe_int(form_data.get('timeout_ms'), 1000)
                } if form_data.get('enable_end_of_utterance') == 'on' else None
            },
            
            # Voice Output - WITH ALL NEW PARAMETERS
            'voice': {
                'name': form_data.get('voice_name', ''),
                'type': form_data.get('voice_type', ''),
                'rate': form_data.get('speaking_rate', '1.0'),
                'temperature': safe_float(form_data.get('voice_temperature'), None) if form_data.get('voice_temperature') else None,
                'custom_lexicon_url': form_data.get('custom_lexicon_url', '') or None,
                'locale': form_data.get('voice_locale', '') or None,
                'prefer_locales': [loc.strip() for loc in form_data.get('voice_prefer_locales', '').split(',') if loc.strip()] or None,
                'style': form_data.get('voice_style', '') or None,
                'pitch': form_data.get('voice_pitch', '') or None,
                'volume': form_data.get('voice_volume', '') or None
            },
            
            'output_audio_timestamp_types': ['word'] if form_data.get('enable_output_timestamps') == 'on' else None
        }
        
        # Add max_tokens or max_completion_tokens conditionally
        model_name_lower = form_data.get('model_name', '').lower()
        max_completion_tokens_value = safe_int(form_data.get('max_completion_tokens'), None)
        max_tokens_value = safe_int(form_data.get('max_tokens'), None)
        
        if max_completion_tokens_value is not None:
            session_config['max_completion_tokens'] = max_completion_tokens_value
        elif max_tokens_value is not None:
            session_config['max_tokens'] = max_tokens_value
        
        # Nettoyer les valeurs None
        session_config = {k: v for k, v in session_config.items() if v is not None}
        
        # Préserver les instructions si elles existent déjà (Step 4)
        existing_session_config = agent_config.get('session_config', {})
        if 'instructions' in existing_session_config:
            session_config['instructions'] = existing_session_config['instructions']
        
        # Mettre à jour dans Cosmos DB avec status step2_completed
        agent_config['session_config'] = session_config
        agent_config['status'] = 'step2_completed'
        agent_config['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        agent_config['current_step'] = 3
        
        save_agent_config(agent_config)
        logger.info("✅ Configuration Step 2 sauvegardée dans Cosmos DB (status: step2_completed)")
        
        logger.info("Configuration complète construite avec succès")
        
        # Afficher la page Step 3 (Sélection des Tools)
        return render_template(
            'agents/agent_config_step3.html',
            agent_id=agent_id,
            config=agent_config
        )
        
    except Exception as e:
        logger.exception("Erreur dans agent_config_step3")
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la finalisation: {str(e)}"
        }), 500


# ===================================================================
# STEP 3 SAVE TOOLS : Sauvegarde des tools sélectionnés
# ===================================================================

@agents_config_bp.route('/config/<agent_id>/step3/save-tools', methods=['POST'])
def agent_config_step3_save_tools(agent_id):
    """
    Sauvegarde les tools sélectionnés depuis Step 3 et redirige vers Step 4
    """
    try:
        from configuration import save_agent_config, get_agent_config
        from datetime import datetime
        
        # Récupérer les tools sélectionnés depuis le formulaire
        form_data = request.form
        
        # Récupérer la configuration existante depuis Cosmos
        agent_config = get_agent_config(agent_id)
        if not agent_config:
            return jsonify({
                "success": False,
                "error": "Configuration non trouvée"
            }), 404
        
        # Extraire les tools sélectionnés (name="tools" avec plusieurs valeurs)
        selected_tools = form_data.getlist('tools')
        
        logger.info(f"✅ Tools sélectionnés: {selected_tools}")
        
        # Charger les définitions complètes des tools pour les ajouter à session_config
        tools_definitions = []
        if selected_tools:
            # Mapping des anciens noms vers les nouveaux noms d'outils
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
            
            # Convertir les noms sélectionnés vers les vrais noms
            mapped_tool_names = [TOOL_NAME_MAPPING.get(tool, tool) for tool in selected_tools]
            
            # Importer et filtrer les outils
            from tools import get_tools_definition
            all_tools = get_tools_definition()
            tools_definitions = [tool for tool in all_tools if tool.get('name') in mapped_tool_names]
            
            logger.info(f"📦 {len(tools_definitions)} outils chargés: {[t.get('name') for t in tools_definitions]}")
        
        # Ajouter les tools dans session_config pour qu'ils soient persistés
        if 'session_config' not in agent_config:
            agent_config['session_config'] = {}
        
        agent_config['session_config']['tools'] = tools_definitions
        
        # Mettre à jour dans Cosmos DB avec status step3_completed
        agent_config['selected_tools'] = selected_tools
        agent_config['status'] = 'step3_completed'
        agent_config['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        agent_config['current_step'] = 4
        
        save_agent_config(agent_config)
        logger.info(f"✅ Tools sauvegardés dans Cosmos DB: {len(tools_definitions)} outils dans session_config (status: step3_completed)")
        
        # Rediriger vers Step 4 (Instructions & Persona)
        return redirect(url_for('agents_manager.agent_config_step4', agent_id=agent_id))
        
    except Exception as e:
        logger.exception("Erreur lors de la sauvegarde des tools")
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la sauvegarde des tools: {str(e)}"
        }), 500


# ===================================================================
# STEP 4 : Configuration Instructions & Persona
# ===================================================================

@agents_config_bp.route('/config/<agent_id>/step4', methods=['GET', 'POST'])
def agent_config_step4(agent_id):
    """
    Configuration des instructions système et persona de l'agent
    
    GET: Affiche le formulaire Step 4
    POST: Sauvegarde les instructions et redirige vers Step 5 (test smartphone)
    """
    try:
        from configuration import save_agent_config, get_agent_config
        from datetime import datetime
        
        if request.method == 'GET':
            # Afficher le formulaire Step 4
            agent_config = get_agent_config(agent_id)
            
            if not agent_config:
                logger.warning(f"Agent {agent_id} non trouvé")
                return redirect(url_for('agents_manager.agent_config_step1'))

            # Récupérer un éventuel prompt généré précédemment stocké côté client
            # (via sessionStorage 'generated_system_prompt' qui sera injecté via JS)
            return render_template(
                'agents/agent_config_step4.html',
                agent_id=agent_id,
                config=agent_config
            )
        
        if request.method == 'POST':
            # Récupérer les instructions depuis le formulaire
            form_data = request.form
            
            # Récupérer la configuration existante depuis Cosmos
            agent_config = get_agent_config(agent_id)
            if not agent_config:
                return jsonify({
                    "success": False,
                    "error": "Configuration non trouvée"
                }), 404
            
            # Extraire tous les champs du formulaire
            agent_name = form_data.get('agent_name', '')  # NOUVEAU: Nom du projet/agent
            system_prompt = form_data.get('system_prompt', '')
            assistant_name = form_data.get('assistant_name', 'Assistant IA')
            role = form_data.get('role', 'Assistant vocal')
            tone = form_data.get('tone', '')
            terminology = form_data.get('terminology', '')
            conduct_instructions = form_data.get('conduct_instructions', '')
            
            logger.info(f"System prompt reçu: {len(system_prompt)} caractères")
            logger.info(f"Nom du projet: {agent_name}, Prénom assistant: {assistant_name}, Rôle: {role}")
            
            # Mettre à jour dans Cosmos DB avec status step4_completed
            agent_config['agent_name'] = agent_name  # NOUVEAU: Nom identifiant du projet
            agent_config['instructions'] = system_prompt  # Le prompt système complet
            agent_config['system_prompt'] = system_prompt  # Gardé aussi sous ce nom
            agent_config['assistant_name'] = assistant_name
            agent_config['role'] = role
            agent_config['tone'] = tone
            agent_config['terminology'] = terminology
            agent_config['style'] = terminology  # 🔥 Alias pour compatibilité avec voice_live_config
            agent_config['conduct_instructions'] = conduct_instructions
            agent_config['conduct'] = conduct_instructions  # 🔥 Alias pour compatibilité avec voice_live_config
            agent_config['status'] = 'step4_completed'
            agent_config['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            agent_config['current_step'] = 5
            
            # Injecter instructions dans session_config également
            if 'session_config' not in agent_config:
                agent_config['session_config'] = {}
            agent_config['session_config']['instructions'] = system_prompt
            
            save_agent_config(agent_config)
            logger.info("✅ Instructions, persona et nom du projet sauvegardés dans Cosmos DB (status: step4_completed, session_config mis à jour)")
            
            # Rediriger vers l'écran d'appel (session vocale live)
            return redirect(url_for('agents_manager.call_agent', agent_id=agent_id))
        
        # Méthode non supportée
        return jsonify({"success": False, "error": "Method not allowed"}), 405
        
    except Exception as e:
        logger.exception("Erreur dans agent_config_step4")
        return jsonify({
            "success": False,
            "error": f"Erreur lors du traitement des instructions: {str(e)}"
        }), 500


# ===================================================================
# STEP 5 : Test de l'agent dans l'interface smartphone
# ===================================================================

@agents_config_bp.route('/config/<agent_id>/step5', methods=['GET', 'POST'])
def agent_config_step5(agent_id):
    """
    Affiche la page de finalisation (Step 5)
    
    Permet de:
    - Donner un nom à l'agent
    - Ajouter une description
    - Visualiser la configuration complète
    - Créer l'agent
    """
    try:
        from configuration import get_agent_config
        
        if request.method == 'GET':
            agent_config = get_agent_config(agent_id)
            
            if not agent_config:
                logger.warning(f"Agent {agent_id} non trouvé")
                return redirect(url_for('agents_manager.agent_config_step1'))
            
            return render_template(
                'agents/agent_config_step5.html',
                agent_id=agent_id,
                config=agent_config
            )
        
        return jsonify({"success": False, "error": "Method not allowed"}), 405
        
    except Exception as e:
        logger.exception("Erreur dans agent_config_step5")
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la finalisation: {str(e)}"
        }), 500


# ===================================================================
# API : Récupération de la configuration
# ===================================================================

@agents_config_bp.route('/api/config/<agent_id>', methods=['GET'])
def get_agent_config(agent_id):
    """
    Récupère la configuration complète d'un agent pour le test Voice Live
    """
    try:
        logger.info(f"📥 Récupération config agent: {agent_id}")
        
        # Récupérer depuis CosmosDB
        config = cosmos_get_agent_config(agent_id)
        
        if not config:
            return jsonify({
                "success": False,
                "error": "Agent non trouvé"
            }), 404
        
        # Ajouter les credentials Azure (depuis variables d'environnement)
        import os
        config['speech_endpoint'] = os.getenv('AZURE_SPEECH_ENDPOINT')
        config['speech_key'] = os.getenv('AZURE_SPEECH_KEY')
        config['speech_region'] = os.getenv('AZURE_SPEECH_REGION')
        config['project_id'] = os.getenv('AZURE_SPEECH_PROJECT_ID')
        
        logger.info(f"✅ Config retournée avec endpoint: {config.get('speech_endpoint')}")
        
        return jsonify(config)
        
    except Exception as e:
        logger.exception(f"❌ Erreur récupération config: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ===================================================================
# API : Récupération des définitions des tools
# ===================================================================

@agents_config_bp.route('/api/tools', methods=['GET'])
def get_all_tools():
    """
    Retourne la liste de tous les tools disponibles
    """
    try:
        from tools import get_tools_definition
        tools = get_tools_definition()
        return jsonify({
            'success': True,
            'tools': tools
        })
    except Exception as e:
        logger.error(f"❌ Erreur get_all_tools: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_config_bp.route('/api/<agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    """
    Supprime une configuration d'agent
    """
    try:
        success = delete_agent_config(agent_id)
        
        if success:
            logger.info(f"✅ Agent {agent_id} supprimé")
            return jsonify({
                'success': True,
                'message': 'Agent supprimé avec succès'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Agent non trouvé'
            }), 404
            
    except Exception as e:
        logger.error(f"❌ Erreur suppression agent {agent_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@agents_config_bp.route('/api/<agent_id>/details', methods=['GET'])
def get_agent_details(agent_id):
    """
    API : Récupérer les détails complets d'une configuration d'agent
    """
    try:
        config = cosmos_get_agent_config(agent_id)
        
        if config:
            # Générer le websocket_url pour l'agent
            try:
                model_id = config.get('model_id', 'gpt-4o-realtime-preview')
                voice_client = VoiceLiveClient(model_id=model_id, skip_validation=True)
                websocket_url = voice_client.get_websocket_url()
                config['websocket_url'] = websocket_url
            except Exception as e:
                logger.warning(f"⚠️ Impossible de générer le websocket_url: {e}")
                config['websocket_url'] = None
            
            return jsonify({
                'success': True,
                'agent': config
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Agent non trouvé'
            }), 404
            
    except Exception as e:
        logger.exception(f"❌ Erreur lors de la récupération de l'agent {agent_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur lors de la récupération de l\'agent'
        }), 500


# ===================================================================
# ENDPOINT POUR APPELER UN AGENT (SESSION VOICE LIVE)
# ===================================================================

@agents_config_bp.route('/call/<agent_id>', methods=['GET'])
def call_agent(agent_id):
    """
    Endpoint pour lancer une session Voice Live avec un agent spécifique
    Charge la configuration de l'agent depuis Cosmos DB et initialise la session
    """
    try:
        # 🔄 FORCE REFRESH: Vider la session Flask pour forcer le rechargement depuis Cosmos DB
        # Cela évite les problèmes de cache avec des anciennes configurations
        session.pop('active_agent_id', None)
        session.pop('active_agent_config', None)
        
        # Récupérer la configuration de l'agent depuis Cosmos DB
        agent_config = cosmos_get_agent_config(agent_id)
        
        if not agent_config:
            logger.error(f"❌ Agent {agent_id} non trouvé")
            return jsonify({
                'success': False,
                'error': f'Agent {agent_id} non trouvé'
            }), 404
        
        # Vérifier que l'agent est configuré (au moins step 5 complété)
        status = agent_config.get('status', '')
        current_step = agent_config.get('current_step', 0)
        
        if current_step < 5 and 'step5' not in status and status not in ['deployed', 'actif']:
            logger.warning(f"⚠️ Agent {agent_id} n'est pas complètement configuré (étape {current_step}/5)")
            return jsonify({
                'success': False,
                'error': 'Agent non configuré. Veuillez compléter la configuration.',
                'current_step': current_step
            }), 400
        
        # Extraire les paramètres de configuration
        model_id = agent_config.get('model_id', 'gpt-4o-realtime-preview')
        
        # Initialiser le client Voice Live avec n'importe quel modèle
        # Voice Live supporte tous les modèles GPT-4o
        try:
            voice_client = VoiceLiveClient(model_id=model_id, skip_validation=True)
            websocket_url = voice_client.get_websocket_url()
        except Exception as e:
            logger.exception(f"❌ Erreur lors de l'initialisation du client Voice Live: {e}")
            return jsonify({
                'success': False,
                'error': 'Erreur lors de l\'initialisation de la session Voice Live'
            }), 500
        
        # Préparer la configuration de session
        session_config = agent_config.get('session_config', {})
        
        # Extraire la voix configurée
        voice_config = session_config.get('voice', {})
        
        # IMPORTANT: voice_config peut être un dict ou None
        # S'assurer que c'est bien un dict
        if not isinstance(voice_config, dict):
            logger.warning(f"⚠️ voice_config n'est pas un dict: {type(voice_config)} = {voice_config}")
            voice_config = {}
        
        # Extraire les valeurs avec validation
        voice_name_raw = voice_config.get('name', 'en-US-AndrewMultilingualNeural')
        voice_type_raw = voice_config.get('type', 'azure-standard')
        
        # CORRECTION: Si voice_name est un dict/objet, extraire le champ 'name'
        if isinstance(voice_name_raw, dict):
            logger.warning(f"⚠️ voice_name est un dict: {voice_name_raw}")
            voice_name = voice_name_raw.get('name', 'en-US-AndrewMultilingualNeural')
        else:
            voice_name = voice_name_raw if voice_name_raw else 'en-US-AndrewMultilingualNeural'
        
        # CORRECTION: Si voice_type est un dict/objet, extraire le champ 'type'
        if isinstance(voice_type_raw, dict):
            logger.warning(f"⚠️ voice_type est un dict: {voice_type_raw}")
            voice_type = voice_type_raw.get('type', 'azure-standard')
        else:
            voice_type = voice_type_raw if voice_type_raw else 'azure-standard'
        
        logger.info(f"🎤 Voix extraite: name='{voice_name}' (type={type(voice_name)}), type='{voice_type}' (type={type(voice_type)})")
        
        # Mapping des noms de voix OpenAI vers Azure (pour compatibilité)
        OPENAI_TO_AZURE_VOICES = {
            'alloy': 'en-US-AndrewMultilingualNeural',
            'echo': 'en-US-BrianMultilingualNeural',
            'fable': 'en-US-EmmaMultilingualNeural',
            'onyx': 'en-US-GuyNeural',
            'nova': 'en-US-AriaNeural',
            'shimmer': 'en-US-JennyNeural'
        }
        
        # Convertir les noms de voix OpenAI en noms Azure si nécessaire
        if voice_name in OPENAI_TO_AZURE_VOICES:
            original_voice = voice_name
            voice_name = OPENAI_TO_AZURE_VOICES[voice_name]
            logger.info(f"🔄 Conversion voix OpenAI → Azure: '{original_voice}' → '{voice_name}'")
        
        # Valider et normaliser le voice_type selon la doc Voice Live
        # Valeurs acceptées: "azure-standard", "azure-custom", "openai"
        # Corriger si nécessaire
        if voice_type == 'azure':
            voice_type = 'azure-standard'
        elif voice_type not in ['azure-standard', 'azure-custom', 'openai']:
            logger.warning(f"⚠️ Type de voix invalide '{voice_type}', utilisation de 'azure-standard'")
            voice_type = 'azure-standard'
        
        voice_rate = voice_config.get('rate', '1.0') or '1.0'
        voice_temperature = voice_config.get('temperature', 0.7)
        
        # S'assurer que voice_rate est une chaîne valide
        if not voice_rate or voice_rate == '':
            voice_rate = '1.0'
        
        # S'assurer que voice_name et voice_type ne sont pas vides
        if not voice_name or voice_name.strip() == '':
            logger.error(f"❌ voice_name est vide! voice_config = {voice_config}")
            voice_name = 'en-US-AndrewMultilingualNeural'
        
        if not voice_type or voice_type.strip() == '':
            logger.error(f"❌ voice_type est vide! voice_config = {voice_config}")
            voice_type = 'azure-standard'
        
        # GPT-5 et dérivés ne supportent pas le paramètre temperature pour la voix
        # Détecter si le modèle est GPT-5 ou un dérivé
        model_id_lower = model_id.lower()
        is_gpt5_model = 'gpt-5' in model_id_lower or 'gpt5' in model_id_lower
        
        if is_gpt5_model and voice_temperature is not None:
            logger.info(f"🚫 Modèle GPT-5 détecté ({model_id}) - Suppression du paramètre voice.temperature")
            voice_temperature = None
        
        # Utiliser le prompt système sauvegardé directement (déjà formaté avec toutes les variables)
        system_instructions = agent_config.get('system_prompt') or agent_config.get('instructions', '')
        
        # IMPORTANT: Voice Live a une limite de tokens pour le prompt système
        # Si le prompt est trop long (>10,000 caractères), le tronquer intelligemment
        MAX_INSTRUCTION_LENGTH = 8000  # Limite sécuritaire pour Voice Live
        
        if len(system_instructions) > MAX_INSTRUCTION_LENGTH:
            logger.warning(f"⚠️ Prompt système trop long ({len(system_instructions)} car) - Troncature à {MAX_INSTRUCTION_LENGTH}")
            # Garder le début (rôle et contexte) et tronquer le reste
            system_instructions = system_instructions[:MAX_INSTRUCTION_LENGTH] + "\n\n[Prompt tronqué pour Voice Live - Limite technique]"
        
        # Si pas d'instructions, utiliser un défaut
        if not system_instructions:
            system_instructions = """Vous êtes un assistant vocal intelligent et serviable.
Aidez l'utilisateur de manière professionnelle et efficace."""
        
        # Préparer les outils sélectionnés
        selected_tools = agent_config.get('selected_tools', [])
        tools_definitions = []
        if selected_tools:
            # Mapping des anciens noms vers les nouveaux noms d'outils
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
                # Les autres outils gardent leur nom original
                'search_web': 'search_web',
                'places': 'search_places',
                'flight_search': 'search_flights',
                'flight_booking': 'book_flight',
                'hotel_search': 'search_hotels',
                'hotel_booking': 'book_hotel',
                'currency': 'convert_currency',
                'calculator': 'calculate'
            }
            
            # Convertir les noms sélectionnés vers les vrais noms
            mapped_tool_names = [TOOL_NAME_MAPPING.get(tool, tool) for tool in selected_tools]
            
            # Importer et filtrer les outils
            from tools import get_tools_definition
            all_tools = get_tools_definition()
            tools_definitions = [tool for tool in all_tools if tool.get('name') in mapped_tool_names]
            
            # OPTIMISATION: Voice Live a des limites strictes sur la taille du contexte
            # Simplifier les descriptions des outils pour réduire les tokens
            for tool in tools_definitions:
                # Garder seulement la première ligne de la description (avant \n\n)
                if 'description' in tool and len(tool['description']) > 200:
                    original_desc = tool['description']
                    # Extraire seulement la première phrase/ligne
                    short_desc = original_desc.split('\n\n')[0].split('\n')[0]
                    if len(short_desc) > 150:
                        short_desc = short_desc[:150] + "..."
                    tool['description'] = short_desc
                    logger.debug(f"🔧 Tool {tool['name']}: description réduite de {len(original_desc)} à {len(short_desc)} car")
                
                # Simplifier aussi les descriptions des paramètres
                if 'parameters' in tool and 'properties' in tool['parameters']:
                    for param_name, param_info in tool['parameters']['properties'].items():
                        if 'description' in param_info and len(param_info['description']) > 150:
                            original_param_desc = param_info['description']
                            # Garder seulement la première ligne
                            short_param_desc = original_param_desc.split('\n')[0]
                            if len(short_param_desc) > 100:
                                short_param_desc = short_param_desc[:100] + "..."
                            param_info['description'] = short_param_desc
            
            logger.debug(f"📋 Outils sélectionnés (brut): {selected_tools}")
            logger.debug(f"🔄 Outils mappés: {mapped_tool_names}")
            logger.debug(f"🔧 Outils chargés: {[t.get('name') for t in tools_definitions]}")
        
        # Stocker la config dans la session Flask pour accès depuis le template
        session['active_agent_id'] = agent_id
        session['active_agent_config'] = {
            'agent_id': agent_id,
            'agent_name': agent_config.get('agent_name', 'Agent'),
            'role': agent_config.get('role', ''),
            'model_id': model_id,
            'model_name': agent_config.get('model_name', model_id),
            'websocket_url': websocket_url,
            'modalities': session_config.get('modalities', ['text', 'audio']),
            'voice': {
                'name': voice_name,
                'type': voice_type,
                'rate': voice_rate,
                'temperature': voice_temperature
            },
            'instructions': system_instructions,
            'custom_lexicon_url': session_config.get('voice', {}).get('custom_lexicon_url', ''),
            'tools': tools_definitions,
            'temperature': agent_config.get('temperature', 0.7),
            'max_tokens': agent_config.get('max_tokens', 4096)
        }
        
        logger.info(f"✅ Session Voice Live initialisée pour l'agent {agent_id} ({agent_config.get('agent_name')})")
        logger.info(f"   Modèle: {model_id}")
        logger.info(f"   Voix: {voice_name}")
        logger.info(f"   Outils: {len(tools_definitions)} activés")
        logger.info(f"   🔌 WebSocket URL: {websocket_url}")
        
        # Rendre la page de session Voice Live
        return render_template(
            'agents/agent_voice_session.html',
            agent=session['active_agent_config']
        )
        
    except Exception as e:
        logger.exception(f"❌ Erreur lors de l'appel de l'agent {agent_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur lors de l\'initialisation de l\'agent'
        }), 500


# ===================================================================
# API : Sauvegarde des messages de conversation
# ===================================================================

@agents_config_bp.route('/api/conversation/save-message', methods=['POST'])
def save_conversation_message():
    """
    Sauvegarde un message de conversation dans Cosmos DB
    
    Body JSON:
    {
        "call_id": "uuid",
        "agent_id": "uuid",
        "message_type": "user" | "agent" | "system" | "tool",
        "content": "texte du message",
        "metadata": {} (optionnel)
    }
    """
    try:
        from configuration.cosmos_config import save_conversation_message as cosmos_save_message
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Aucune donnée fournie"
            }), 400
        
        call_id = data.get('call_id')
        agent_id = data.get('agent_id')
        message_type = data.get('message_type')
        content = data.get('content')
        metadata = data.get('metadata', {})
        model = data.get('model')  # Optionnel: nom du modèle utilisé
        
        if not all([call_id, agent_id, message_type, content]):
            return jsonify({
                "success": False,
                "error": "Paramètres manquants (call_id, agent_id, message_type, content requis)"
            }), 400
        
        # Log du model reçu
        logger.info(f"💾 Sauvegarde message - call_id: {call_id}, type: {message_type}, model: {model if model else 'NON FOURNI'}")
        
        # Sauvegarder le message
        cosmos_save_message(call_id, agent_id, message_type, content, metadata, model)
        
        return jsonify({
            "success": True,
            "message": "Message sauvegardé avec succès"
        })
        
    except Exception as e:
        logger.exception(f"❌ Erreur lors de la sauvegarde du message: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agents_config_bp.route('/api/conversation/end', methods=['POST'])
def end_conversation():
    """
    Marque une conversation comme terminée dans Cosmos DB avec analyse complète
    
    Body JSON:
    {
        "call_id": "uuid",
        "tools_used": ["tool1", "tool2"] (optionnel),
        "tokens": {
            "inputs_text_tokens": int,
            "inputs_cached_tokens": int,
            "inputs_audio_tokens": int,
            "outputs_text_tokens": int,
            "outputs_audio_tokens": int
        } (optionnel)
    }
    
    Traitement automatique:
    - Mise à jour du status en "completed"
    - Calcul de duration_minutes (3 décimales)
    - Calcul de interaction_count
    - Calcul de average_interaction_duration (3 décimales)
    - Analyse de sentiment user et assistant (Azure Text Analytics)
    - Enregistrement des tokens détaillés
    - Calcul du coût selon le modèle (Pro/Basic/Lite)
    """
    try:
        from configuration.cosmos_config import end_conversation as cosmos_end_conversation
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Aucune donnée fournie"
            }), 400
        
        call_id = data.get('call_id')
        tools_used = data.get('tools_used', [])
        tokens = data.get('tokens')  # Nouveau paramètre pour les tokens détaillés
        
        if not call_id:
            return jsonify({
                "success": False,
                "error": "call_id manquant"
            }), 400
        
        # Terminer la conversation avec analyse complète
        result = cosmos_end_conversation(call_id, tools_used, tokens)
        
        cost_data = result.get('cost', {})
        
        return jsonify({
            "success": True,
            "message": "Conversation terminée avec analyse complète",
            "data": {
                "call_id": call_id,
                "status": result.get('status'),
                "duration_minutes": result.get('duration_minutes'),
                "interaction_count": result.get('interaction_count'),
                "cost": {
                    "inputs_text_cost": cost_data.get('inputs_text_cost', 0.0),
                    "inputs_cached_cost": cost_data.get('inputs_cached_cost', 0.0),
                    "inputs_audio_cost": cost_data.get('inputs_audio_cost', 0.0),
                    "outputs_text_cost": cost_data.get('outputs_text_cost', 0.0),
                    "outputs_audio_cost": cost_data.get('outputs_audio_cost', 0.0),
                    "total_cost": cost_data.get('total_cost', 0.0),
                    "cost_per_minute": cost_data.get('cost_per_minute', 0.0)
                },
                "user_sentiment": result.get('user_sentiment_analysis', {}).get('sentiment'),
                "assistant_sentiment": result.get('assistant_sentiment_analysis', {}).get('sentiment')
            }
        })
        
    except Exception as e:
        logger.exception(f"❌ Erreur lors de la finalisation de la conversation: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ===================================================================
# API : Exécution d'un tool
# ===================================================================

@agents_config_bp.route('/api/execute-tool', methods=['POST'])
def execute_tool_route():
    """
    Exécute un tool et retourne le résultat
    
    Body JSON:
    {
        "tool_name": "get_weather_forecast",
        "arguments": {"location": "Paris", "days": 3}
    }
    
    Returns:
        Résultat du tool au format JSON
    """
    try:
        from tools import execute_tool
        
        # Récupérer les données
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Aucune donnée fournie"
            }), 400
        
        tool_name = data.get('tool_name')
        arguments = data.get('arguments', {})
        
        if not tool_name:
            return jsonify({
                "success": False,
                "error": "tool_name manquant"
            }), 400
        
        logger.info(f"🔧 Exécution du tool: {tool_name}")
        logger.debug(f"   Arguments: {arguments}")
        
        # Exécuter le tool
        result = execute_tool(tool_name, arguments)
        
        logger.info(f"✅ Tool {tool_name} exécuté avec succès")
        
        return jsonify(result)
        
    except Exception as e:
        logger.exception(f"❌ Erreur exécution tool: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "tool_name": data.get('tool_name', 'unknown') if data else 'unknown'
        }), 500


# ===================================================================
# API : Sauvegarde de l'agent
# ===================================================================

@agents_config_bp.route('/api/save', methods=['POST'])
def save_agent():
    """
    Sauvegarde l'agent avec toute la configuration finale
    """
    try:
        # Récupérer les données du formulaire
        data = request.get_json()
        agent_name = data.get('agent_name', 'Mon Agent')
        agent_description = data.get('agent_description', '')
        
        # Récupérer la configuration complète depuis la session
        complete_config = session.get('complete_agent_config', {})
        
        if not complete_config:
            return jsonify({
                "success": False,
                "error": "Configuration manquante"
            }), 400
        
        # Ajouter le nom et la description
        complete_config['agent_name'] = agent_name
        complete_config['agent_description'] = agent_description
        
        # TODO: Sauvegarder dans la base de données
        # TODO: Créer l'agent dans Azure
        
        logger.info(f"Agent créé: {agent_name}")
        
        # Nettoyer la session
        session.pop('complete_agent_config', None)
        
        return jsonify({
            "success": True,
            "message": "Agent créé avec succès",
            "agent_id": "generated-id",  # À remplacer par l'ID réel
            "config": complete_config
        })
        
    except Exception as e:
        logger.exception("Erreur lors de la création de l'agent")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ===================================================================
# Fonction d'initialisation
# ===================================================================

def init_app(app):
    """
    Initialise le blueprint avec l'application Flask
    
    Usage dans app.py:
        from blueprints.agents_config import agents_config_bp, init_app
        init_app(app)
    
    Args:
        app: Instance Flask
    """
    app.register_blueprint(agents_config_bp)
    
    logger.info("✅ Blueprint Agents Config enregistré")
    logger.info(f"   Routes disponibles:")
    logger.info(f"   - GET  /agents/config/step1")
    logger.info(f"   - POST /agents/config/step2")
    logger.info(f"   - POST /agents/config/step3")
    logger.info(f"   - POST /agents/api/create")
    logger.info("   - GET  /agents/api/tools")


# ===================================================================
# API : Mise à jour de la configuration de session (instructions, lexique)
# ===================================================================

@agents_config_bp.route('/api/<agent_id>/update_session_config', methods=['POST'])
def update_session_config(agent_id):
    """
    Met à jour la configuration de session d'un agent (instructions, custom_lexicon_url)
    Utilisé par l'éditeur dans l'écran d'appel vocal
    """
    try:
        # Récupérer les données JSON
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Aucune donnée fournie'
            }), 400
        
        # Récupérer la configuration de l'agent
        agent_config = cosmos_get_agent_config(agent_id)
        
        if not agent_config:
            return jsonify({
                'success': False,
                'error': f'Agent {agent_id} non trouvé'
            }), 404
        
        # Mettre à jour les champs fournis
        updated_fields = []
        
        if 'instructions' in data:
            agent_config['instructions'] = data['instructions']
            # Mettre à jour aussi dans session_config
            if 'session_config' not in agent_config:
                agent_config['session_config'] = {}
            agent_config['session_config']['instructions'] = data['instructions']
            updated_fields.append('instructions')
            logger.info(f"📝 Instructions mises à jour pour l'agent {agent_id}")
        
        if 'custom_lexicon_url' in data:
            # Mettre à jour dans session_config.voice
            if 'session_config' not in agent_config:
                agent_config['session_config'] = {}
            if 'voice' not in agent_config['session_config']:
                agent_config['session_config']['voice'] = {}
            
            agent_config['session_config']['voice']['custom_lexicon_url'] = data['custom_lexicon_url'] or None
            updated_fields.append('custom_lexicon_url')
            logger.info(f"📚 Lexique personnalisé mis à jour pour l'agent {agent_id}: {data['custom_lexicon_url']}")
        
        # Sauvegarder dans Cosmos DB
        save_agent_config(agent_config)
        
        logger.info(f"✅ Configuration de session mise à jour pour l'agent {agent_id} (champs: {', '.join(updated_fields)})")
        
        return jsonify({
            'success': True,
            'message': f'Configuration mise à jour: {", ".join(updated_fields)}',
            'updated_fields': updated_fields
        })
        
    except Exception as e:
        logger.exception(f"Erreur lors de la mise à jour de la configuration de l'agent {agent_id}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===================================================================
# API : Liste des lexiques depuis Azure Storage
# ===================================================================

@agents_config_bp.route('/api/lexicons', methods=['GET'])
def get_lexicons():
    """
    Récupère la liste des fichiers lexiques depuis le container Azure Storage 'luxicoms'
    """
    try:
        # Connection string Azure Storage
        connection_string = "DefaultEndpointsProtocol=https;AccountName=solutionsdocs;AccountKey=Mn1HQb4qQTFopcP29OaBncT2lj3xQd4Ip1icIqrI0B1nkEH/TzppVisJQPKNfxK7gaYfjgR8a0JE+AStLKf0bw==;EndpointSuffix=core.windows.net"
        container_name = "luxicoms"
        
        # Créer le client Blob Service
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        
        # Lister tous les blobs
        blobs = []
        for blob in container_client.list_blobs():
            # Construire l'URL publique du blob
            blob_url = f"https://solutionsdocs.blob.core.windows.net/{container_name}/{blob.name}"
            blobs.append({
                'name': blob.name,
                'url': blob_url,
                'size': blob.size,
                'last_modified': blob.last_modified.isoformat() if blob.last_modified else None
            })
        
        logger.info(f"✅ {len(blobs)} lexiques trouvés dans le container {container_name}")
        
        return jsonify({
            'success': True,
            'lexicons': blobs,
            'count': len(blobs)
        })
        
    except Exception as e:
        logger.exception("Erreur lors de la récupération des lexiques")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@agents_config_bp.route('/api/<agent_id>/generate_prompt', methods=['POST'])
def generate_agent_prompt(agent_id):
    """
    API endpoint pour générer un prompt système via GPT-5-mini (VERSION OPTIMISÉE AVATAR)
    """
    try:
        from openai import OpenAI
        import os
        
        data = request.get_json()
        user_instruction = data.get('user_instruction', '') or data.get('instruction', '')
        
        if not user_instruction:
            return jsonify({
                'success': False,
                'error': 'Instruction utilisateur manquante'
            }), 400
        
        # Initialiser le client OpenAI avec la syntaxe Azure compatible
        azure_endpoint = os.getenv('AZURE_OPENAI_SUMMARY_ENDPOINT')
        api_key = os.getenv('AZURE_OPENAI_SUMMARY_KEY')
        deployment_name = os.getenv('AZURE_OPENAI_GPT5_MINI_DEPLOYMENT', 'gpt-5-mini')
        
        if not azure_endpoint or not api_key:
            return jsonify({
                'success': False,
                'error': 'Configuration Azure OpenAI manquante'
            }), 500
        
        # Construire l'endpoint avec le format Azure OpenAI v1
        base_url = f"{azure_endpoint}openai/v1/"
        
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        
        # Créer le prompt pour générer le system prompt (VERSION OPTIMISÉE - CONCISE)
        generation_prompt = f"""Crée un prompt système CONCIS (150-200 mots max) pour un agent IA vocal avec :
{user_instruction}

INCLURE obligatoirement :
1. Rôle et ton (familier par défaut)
2. Missions principales (3 max)
3. Comportement : saluer au 1er message seulement, demander le prénom, utiliser les tools disponibles
4. Si email/CV : collecter UNE info par message
5. Si pays mentionné : connaître 5-10 expressions culturelles, les utiliser MODÉRÉMENT

6. 🇧🇫 EXPRESSIONS BURKINABÉES OBLIGATOIRES (sans excès) :
   Instruire l'agent à utiliser NATURELLEMENT des expressions burkinabées (Burkina Faso).
   Fournir au moins 50 expressions classées par famille :
   
   **SALUTATIONS & POLITESSE** (10 expressions minimum) :
   - "Bonjour mon frère / ma sœur", "Ça va bien ?", "C'est comment ?", "On dit quoi ?", "Tu es là ?", "Bonne arrivée", "Merci bien hein", "C'est gentil", "Que Dieu te bénisse", "On se voit"
   
   **AFFIRMATIONS & RÉACTIONS** (10 expressions minimum) :
   - "Ça va aller", "Normalement", "Inch'Allah", "Dieu merci", "C'est un peu ça", "Effectivement", "Sincèrement", "Franchement", "Vraiment même", "C'est sûr"
   
   **EXPRESSIONS COURANTES** (10 expressions minimum) :
   - "Eh ben", "On va gérer ça", "Pas de souci", "Ça va aller comme ça", "On se débrouille", "Doucement doucement", "On est ensemble", "Petit à petit", "On fait comment ?", "Laisse-moi voir"
   
   **ENCOURAGEMENT & SOUTIEN** (10 expressions minimum) :
   - "Courage à toi", "Tiens bon", "Ça va s'arranger", "Faut pas décourager", "Tu vas réussir", "On est avec toi", "Force à toi", "Aie confiance", "Ça va passer", "Dieu est grand"
   
   **QUOTIDIEN & VIE PRATIQUE** (10 expressions minimum) :
   - "On fait avec", "C'est la vie", "Faut gérer", "On n'a pas le choix", "C'est déjà ça", "Ça peut aller", "On verra", "Si Dieu veut", "Faut patienter", "On espère"
   
   RÈGLES D'UTILISATION :
   - Utiliser 2-3 expressions par réponse MAX (rester naturel)
   - Adapter au contexte de la conversation
   - NE PAS surcharger - l'authenticité prime sur la quantité

7. 🎭 TON ET DIALECTE BURKINABÉ :
   Ajuster le ton de l'agent au style burkinabé authentique :
   - Ton chaleureux, posé et fraternel
   - Vouvoiement occasionnel pour le respect, tutoiement amical sinon
   - Rythme de parole détendu (pas pressé)
   - Formulations typiques : "Hein ?", "Là", "Même", "Un peu", "Bien bien"
   - Empathie et solidarité dans les réponses

Réponds uniquement avec le prompt, concis et efficace."""

        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "Tu es un expert en création de prompts système pour agents IA."},
                {"role": "user", "content": generation_prompt}
            ],
            temperature=1
        )
        
        generated_prompt = response.choices[0].message.content
        if not generated_prompt:
            generated_prompt = ""
        generated_prompt = generated_prompt.strip()

        # Ajouter automatiquement la section TOOLS au prompt généré
        # Importer les tools pour obtenir leurs définitions
        from tools import get_tools_definition

        all_tools = get_tools_definition()

        # Section outils optimisée - Liste compacte
        tools_list = ", ".join([tool.get("name", "") for tool in all_tools])
        
        tools_section = f"""

## 🛠️ OUTILS DISPONIBLES

Tu as accès à ces outils: {tools_list}

### 📋 RÈGLES

1. ✅ Annonce avant d'appeler: "Je vérifie...", "Je cherche..."
2. ✅ Appelle IMMÉDIATEMENT dès que tu as les infos
3. ❌ NE propose JAMAIS - AGIS directement!

### 💡 EXEMPLES

**Météo**: "Quel temps à Paris?" → Appelle get_weather_forecast{{"city":"Paris"}}
**Traduction**: "Traduis bonjour" → Appelle translate_text{{"text":"bonjour","target_lang":"en"}}
**Calcul**: "15 fois 7?" → Appelle calculate{{"expression":"15*7"}}
**Email**: Demande to/subject/body puis appelle send_email
**Fin**: "Au revoir" → Appelle end_conversation{{"reason":"salutations"}}
"""

        # Concaténer le prompt généré avec la section tools
        final_prompt = generated_prompt + tools_section

        logger.info(f"✅ Prompt généré pour agent {agent_id} (avec section tools)")

        return jsonify({
            'success': True,
            'prompt': final_prompt
        })
        
    except Exception as e:
        logger.exception("Erreur lors de la génération du prompt")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Fin du Blueprint agents_config_bp
