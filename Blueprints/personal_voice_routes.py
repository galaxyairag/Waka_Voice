"""
Blueprint pour la gestion des voix personnelles Azure AI
"""
from flask import Blueprint, render_template, request, jsonify
import logging

logger = logging.getLogger(__name__)

personal_voice_bp = Blueprint('personal_voice', __name__, url_prefix='/personal-voice')

@personal_voice_bp.route('/')
def index():
    """Page principale de gestion des voix personnelles - Redirige vers step1"""
    from flask import redirect, url_for
    return redirect(url_for('personal_voice.personal_voice_config_step1'))

@personal_voice_bp.route('/api/projects', methods=['GET', 'POST'])
def manage_projects():
    """Gérer les projets de voix personnelles"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            project_name = data.get('project_name')
            description = data.get('description', '')
            
            # TODO: Implémenter la création du projet avec Azure Speech API
            import uuid
            project_id = str(uuid.uuid4())
            
            # TODO: Sauvegarder dans Cosmos DB avec status 'Creating'
            # Puis faire l'appel API Azure Speech
            
            logger.info(f"✅ Projet créé: {project_id} (statut: Creating)")
            
            return jsonify({
                'success': True,
                'project_id': project_id,
                'status': 'Creating',
                'message': 'Projet en cours de création'
            })
            
        except Exception as e:
            logger.exception("Erreur création projet")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    else:  # GET
        try:
            # TODO: Récupérer les projets depuis Azure ou base de données
            projects = [
                {
                    'id': 'project_test_1',
                    'project_name': 'Projet Test 1',
                    'description': 'Description du projet test',
                    'status': 'created'
                }
            ]
            
            return jsonify({
                'success': True,
                'projects': projects
            })
            
        except Exception as e:
            logger.exception("Erreur récupération projets")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

@personal_voice_bp.route('/api/projects/<project_id>', methods=['GET'])
def get_project_status(project_id):
    """Vérifier le statut d'un projet spécifique"""
    try:
        # TODO: Appeler Azure Speech API pour vérifier le statut du projet
        # Pour l'instant, on simule le passage de Creating à Succeeded après quelques secondes
        import time
        import random
        
        # Simuler un délai de traitement
        status = random.choice(['Creating', 'Succeeded']) if random.random() > 0.3 else 'Succeeded'
        
        project_info = {
            'id': project_id,
            'status': status,
            'project_name': 'Mon Projet',
            'description': 'Description du projet'
        }
        
        logger.info(f"📊 Statut du projet {project_id}: {status}")
        
        return jsonify({
            'success': True,
            'project': project_info
        })
        
    except Exception as e:
        logger.exception("Erreur récupération statut projet")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@personal_voice_bp.route('/api/consent-text/<locale>', methods=['GET'])
def get_consent_text(locale):
    """Récupérer le texte de consentement pour une locale donnée"""
    
    consent_texts = {
        'fr-FR': "Je [prénom et nom] suis conscient(e) que les enregistrements de ma voix seront utilisés par [nom de l'entreprise] pour créer et utiliser une version synthétique de ma voix.",
        'en-US': "I [first and last name] am aware that recordings of my voice will be used by [company name] to create and use a synthetic version of my voice.",
        'es-ES': "Yo [nombre y apellido] soy consciente de que las grabaciones de mi voz serán utilizadas por [nombre de la empresa] para crear y utilizar una versión sintética de mi voz.",
        'de-DE': "Ich [Vor- und Nachname] bin mir bewusst, dass Aufnahmen meiner Stimme von [Firmenname] verwendet werden, um eine synthetische Version meiner Stimme zu erstellen und zu verwenden.",
        'pt-BR': "Eu [primeiro e último nome] estou ciente de que as gravações da minha voz serão usadas por [nome da empresa] para criar e usar uma versão sintética da minha voz."
    }
    
    consent_text = consent_texts.get(locale, consent_texts['en-US'])
    
    return jsonify({
        'success': True,
        'consent_text': consent_text,
        'locale': locale
    })

@personal_voice_bp.route('/api/upload-audio', methods=['POST'])
def upload_audio():
    """Upload d'un fichier audio (consentement ou échantillon vocal)"""
    try:
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Aucun fichier audio fourni'
            }), 400
        
        audio_file = request.files['audio']
        audio_type = request.form.get('type', 'unknown')  # 'consent' ou 'voice'
        project_id = request.form.get('project_id')
        
        # TODO: Upload vers Azure Blob Storage
        # Pour l'instant, on simule un blob URL
        blob_url = f"https://fakestorage.blob.core.windows.net/{project_id}/{audio_type}_{audio_file.filename}"
        
        logger.info(f"✅ Audio uploadé: {blob_url}")
        
        return jsonify({
            'success': True,
            'blob_url': blob_url,
            'message': 'Audio uploadé avec succès'
        })
        
    except Exception as e:
        logger.exception("Erreur upload audio")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@personal_voice_bp.route('/api/consents', methods=['POST'])
def create_consent():
    """Créer un consentement de voix personnelle"""
    try:
        data = request.get_json()
        
        project_id = data.get('project_id')
        voice_talent_name = data.get('voice_talent_name')
        company_name = data.get('company_name')
        audio_url = data.get('audio_url')
        locale = data.get('locale', 'en-US')
        description = data.get('description', '')
        
        # TODO: Appeler l'API Azure Speech pour créer le consentement
        consent_id = f"consent_{project_id}_{voice_talent_name.replace(' ', '_').lower()}"
        
        logger.info(f"✅ Consentement créé: {consent_id}")
        
        return jsonify({
            'success': True,
            'consent_id': consent_id,
            'message': 'Consentement créé avec succès'
        })
        
    except Exception as e:
        logger.exception("Erreur création consentement")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@personal_voice_bp.route('/api/personal-voices', methods=['POST'])
def create_personal_voice():
    """Créer une voix personnelle"""
    try:
        data = request.get_json()
        
        project_id = data.get('project_id')
        consent_id = data.get('consent_id')
        audio_url = data.get('audio_url')
        voice_name = data.get('voice_name')
        description = data.get('description', '')
        
        # TODO: Appeler l'API Azure Speech pour créer la voix personnelle
        personal_voice_id = f"voice_{project_id}_{voice_name.replace(' ', '_').lower()}"
        
        logger.info(f"✅ Voix personnelle créée: {personal_voice_id}")
        
        return jsonify({
            'success': True,
            'personal_voice_id': personal_voice_id,
            'message': 'Voix personnelle créée avec succès'
        })
        
    except Exception as e:
        logger.exception("Erreur création voix personnelle")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@personal_voice_bp.route('/api/personal-voices/<voice_id>', methods=['GET'])
def get_personal_voice(voice_id):
    """Récupérer les informations d'une voix personnelle"""
    try:
        # TODO: Récupérer depuis Azure Speech API
        # Pour l'instant, on simule une voix réussie
        
        voice_info = {
            'id': voice_id,
            'status': 'Succeeded',
            'speakerProfileId': f"spkr_{voice_id}",
            'voice_name': 'Ma Voix Personnelle',
            'description': 'Voix créée avec succès'
        }
        
        return jsonify({
            'success': True,
            'voice': voice_info
        })
        
    except Exception as e:
        logger.exception("Erreur récupération voix")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@personal_voice_bp.route('/api/synthesize', methods=['POST'])
def synthesize_speech():
    """Synthétiser un texte avec la voix personnelle"""
    try:
        data = request.get_json()
        
        text = data.get('text')
        speaker_profile_id = data.get('speaker_profile_id')
        voice_name = data.get('voice_name', 'en-US-AvaMultilingualNeural')
        
        # TODO: Appeler Azure Speech API pour la synthèse
        # Pour l'instant, on retourne une URL fictive
        audio_url = f"https://fakestorage.blob.core.windows.net/synthesized/audio_{speaker_profile_id}.mp3"
        
        logger.info(f"✅ Synthèse réalisée pour: {speaker_profile_id}")
        
        return jsonify({
            'success': True,
            'audio_url': audio_url,
            'message': 'Synthèse réussie'
        })
        
    except Exception as e:
        logger.exception("Erreur synthèse vocale")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@personal_voice_bp.route('/api/personal-voices', methods=['GET'])
def list_personal_voices():
    """
    Liste des voix personnalisées via Azure Speech REST API Endpoints
    https://learn.microsoft.com/en-us/rest/api/aiservices/speechapi/endpoints/list
    """
    try:
        import os
        import requests
        
        # Récupérer les credentials Azure Speech pour Personal Voice
        # Priorité aux variables spécifiques PERSONAL_VOICE, sinon fallback sur AZURE_SPEECH
        speech_key = os.getenv('PERSONAL_VOICE_KEY') or os.getenv('AZURE_SPEECH_KEY')
        speech_region = os.getenv('PERSONAL_VOICE_REGION') or os.getenv('AZURE_SPEECH_REGION', 'eastus')
        
        if not speech_key:
            logger.error("PERSONAL_VOICE_KEY ou AZURE_SPEECH_KEY non configurée")
            return jsonify({
                'success': False,
                'error': 'Configuration Azure Speech pour Personal Voice manquante'
            }), 500
        
        logger.info(f"🎤 Personal Voice - Région: {speech_region}")
        
        # URL de l'API REST Azure Speech Endpoints
        # Note: Utiliser v3.0 qui est stable et supporté dans toutes les régions
        api_url = f"https://{speech_region}.api.cognitive.microsoft.com/speechapi/texttospeech/v3.0/endpoints"
        
        headers = {
            'Ocp-Apim-Subscription-Key': speech_key,
            'Content-Type': 'application/json'
        }
        
        logger.info(f"🔍 Appel API Azure Speech Endpoints: {api_url}")
        
        response = requests.get(api_url, headers=headers, timeout=10)
        
        # 404 peut signifier: région non supportée OU aucun endpoint créé
        if response.status_code == 404:
            logger.warning(f"⚠️ 404 pour région {speech_region} - soit région non supportée, soit aucun Personal Voice endpoint")
            return jsonify({
                'success': True,
                'voices': [],
                'total_count': 0,
                'info': f'Aucune voix personnalisée trouvée dans la région {speech_region}. Vérifiez que vous avez créé des Personal Voice endpoints dans cette région, ou utilisez une région supportée (eastus, westeurope, etc.).'
            })
        
        response.raise_for_status()
        
        data = response.json()
        
        # Filtrer uniquement les endpoints de type Personal Voice
        endpoints = data.get('value', [])
        personal_voices = []
        
        for endpoint in endpoints:
            properties = endpoint.get('properties', {})
            voice_kind = properties.get('voiceKind', '')
            
            # Filtrer les Personal Voices et les endpoints actifs
            if voice_kind == 'PersonalVoice' and endpoint.get('status') == 'Succeeded':
                voice_info = {
                    'voice_id': endpoint.get('id'),
                    'voice_name': endpoint.get('name', 'Voix personnalisée'),
                    'description': endpoint.get('description', ''),
                    'endpoint_id': endpoint.get('id'),
                    'speaker_profile_id': properties.get('speakerProfileId', ''),
                    'status': endpoint.get('status'),
                    'locale': properties.get('locale', 'fr-FR'),
                    'gender': properties.get('gender', 'Unknown'),
                    'created_at': endpoint.get('createdDateTime'),
                    'last_modified': endpoint.get('lastActionDateTime'),
                    'voice_type': 'personal',
                    'usage_count': 0  # TODO: Calculer depuis historique
                }
                personal_voices.append(voice_info)
        
        logger.info(f"✅ {len(personal_voices)} voix personnalisées trouvées")
        
        return jsonify({
            'success': True,
            'voices': personal_voices,
            'total_count': len(personal_voices)
        })
        
    except requests.exceptions.RequestException as e:
        logger.exception(f"Erreur appel API Azure Speech: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur API Azure: {str(e)}'
        }), 500
    except Exception as e:
        logger.exception("Erreur récupération voix personnalisées")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@personal_voice_bp.route('/create-agent')
def create_agent_page():
    """
    Point d'entrée pour créer un agent avec voix personnalisée
    Redirige vers Step 1 avec flag voice_type=personal
    """
    from flask import redirect, url_for
    return redirect(url_for('personal_voice.personal_voice_config_step1'))


@personal_voice_bp.route('/config/step1', methods=['GET'])
def personal_voice_config_step1():
    """
    Page de sélection du modèle pour voix personnalisées
    Utilise le template personal_voice/step1.html
    """
    return render_template('personal_voice/step1.html', voice_type='personal')

@personal_voice_bp.route('/config/step2', methods=['POST'])
def personal_voice_config_step2_create():
    """
    Crée un agent avec voix personnalisée et redirige vers step2
    """
    try:
        from datetime import datetime
        import uuid
        from flask import redirect, url_for
        
        # Récupérer les données du formulaire
        config_type = request.form.get('config_type', 'voice_live')
        model_id = request.form.get('model_id', 'gpt-4o-realtime-preview')
        model_name = request.form.get('model_name', 'GPT-4 Omni Realtime')
        model_description = request.form.get('model_description', '')
        model_family = request.form.get('model_family', 'F1_Realtime')
        
        # Générer un agent_id unique
        agent_id = str(uuid.uuid4())
        
        # Configuration avec flag voice_type='personal'
        initial_config = {
            'id': agent_id,
            'agent_id': agent_id,
            'agent_name': f"Agent Voix Waka {model_name}",
            'status': 'step1_completed',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'config_type': config_type,
            'model_id': model_id,
            'model_name': model_name,
            'model_description': model_description,
            'model_family': model_family,
            'current_step': 2,
            'voice_type': 'personal',
            'metadata': {
                'version': 1,
                'voice_source': 'waka_personal'
            }
        }
        
        # Sauvegarder dans Cosmos DB
        from configuration.cosmos_config import save_agent_config
        save_agent_config(initial_config)
        logger.info(f"✅ Configuration voix personnalisée créée et sauvegardée (agent_id: {agent_id})")
        
        # Rediriger vers step2 personal_voice avec les paramètres du modèle
        return redirect(url_for('personal_voice.personal_voice_config_step2', 
                                agent_id=agent_id,
                                model_id=model_id,
                                model_name=model_name,
                                model_description=model_description,
                                model_family=model_family))
        
    except Exception as e:
        logger.exception("Erreur dans personal_voice_config_step2_create")
        return jsonify({"success": False, "error": str(e)}), 500

@personal_voice_bp.route('/config/step2/<agent_id>', methods=['GET'])
def personal_voice_config_step2(agent_id):
    """
    Page de configuration Voice Live pour voix personnalisées
    Utilise le template personal_voice/step2.html
    """
    try:
        # Récupérer la config depuis Cosmos DB
        from configuration.cosmos_config import get_agent_config
        config = get_agent_config(agent_id)
        
        # Si pas trouvé, utiliser les paramètres de l'URL
        if not config:
            config = {
                'agent_id': agent_id,
                'config_type': 'voice_live',
                'model_id': request.args.get('model_id', 'gpt-4o-realtime-preview'),
                'model_name': request.args.get('model_name', 'GPT-4 Omni Realtime'),
                'model_description': request.args.get('model_description', ''),
                'model_family': request.args.get('model_family', 'F1_Realtime'),
                'voice_type': 'personal'
            }
        
        logger.info(f"📄 Rendu Step 2 pour voix personnalisée (agent: {agent_id})")
        
        return render_template(
            'personal_voice/step2.html',
            agent_id=agent_id,
            config_type=config.get('config_type'),
            model_id=config.get('model_id'),
            model_name=config.get('model_name'),
            model_description=config.get('model_description'),
            model_family=config.get('model_family'),
            voice_type='personal'
        )
        
    except Exception as e:
        logger.exception("Erreur dans personal_voice_config_step2")
        return jsonify({"success": False, "error": str(e)}), 500

@personal_voice_bp.route('/config/step3/<agent_id>', methods=['GET', 'POST'])
def personal_voice_config_step3(agent_id):
    """
    Step 3: Configuration des outils pour voix personnalisées
    Utilise le même template que les voix Azure
    """
    if request.method == 'GET':
        try:
            # Récupérer la config depuis Cosmos DB
            from configuration.cosmos_config import get_agent_config
            config = get_agent_config(agent_id)
            
            if not config:
                config = {
                    'agent_id': agent_id,
                    'voice_type': 'personal'
                }
            
            logger.info(f"📄 Rendu Step 3 pour voix personnalisée (agent: {agent_id})")
            
            return render_template(
                'agents/agent_config_step3.html',
                agent_id=agent_id,
                voice_type='personal'
            )
            
        except Exception as e:
            logger.exception("Erreur dans personal_voice_config_step3 GET")
            return jsonify({"success": False, "error": str(e)}), 500
    
    else:  # POST
        try:
            from flask import redirect, url_for
            # Les outils sont sauvegardés via l'API, rediriger vers step 4
            return redirect(url_for('personal_voice.personal_voice_config_step4', agent_id=agent_id))
            
        except Exception as e:
            logger.exception("Erreur dans personal_voice_config_step3 POST")
            return jsonify({"success": False, "error": str(e)}), 500


@personal_voice_bp.route('/config/step4/<agent_id>', methods=['GET'])
def personal_voice_config_step4(agent_id):
    """
    Step 4: Paramètres avancés pour voix personnalisées
    Utilise le même template que les voix Azure
    """
    try:
        # Récupérer la config depuis Cosmos DB
        from configuration.cosmos_config import get_agent_config
        config = get_agent_config(agent_id)
        
        if not config:
            config = {
                'agent_id': agent_id,
                'voice_type': 'personal'
            }
        
        logger.info(f"📄 Rendu Step 4 pour voix personnalisée (agent: {agent_id})")
        
        return render_template(
            'agents/agent_config_step4.html',
            agent_id=agent_id,
            voice_type='personal'
        )
        
    except Exception as e:
        logger.exception("Erreur dans personal_voice_config_step4")
        return jsonify({"success": False, "error": str(e)}), 500


@personal_voice_bp.route('/api/agents', methods=['POST'])
def create_agent_with_personal_voice():
    """Créer un nouvel agent avec une voix personnalisée"""
    try:
        data = request.get_json()
        
        agent_name = data.get('agent_name')
        description = data.get('description', '')
        phone_number = data.get('phone_number')
        language = data.get('language', 'fr-FR')
        system_prompt = data.get('system_prompt')
        voice_id = data.get('voice_id')
        speaker_profile_id = data.get('speaker_profile_id')
        voice_name = data.get('voice_name')
        temperature = data.get('temperature', 0.8)
        max_tokens = data.get('max_tokens', 1000)
        top_p = data.get('top_p', 0.9)
        gpt_model = data.get('gpt_model', 'gpt-4o-realtime-preview')
        
        # Validation
        if not all([agent_name, phone_number, system_prompt, voice_id, speaker_profile_id]):
            return jsonify({
                'success': False,
                'error': 'Champs obligatoires manquants'
            }), 400
        
        # TODO: Sauvegarder l'agent dans Cosmos DB avec toutes les infos
        import uuid
        agent_id = str(uuid.uuid4())
        
        agent_config = {
            'id': agent_id,
            'agent_id': agent_id,
            'agent_name': agent_name,
            'description': description,
            'phone_number': phone_number,
            'language': language,
            'system_prompt': system_prompt,
            'voice_type': 'personal',
            'voice_id': voice_id,
            'speaker_profile_id': speaker_profile_id,
            'voice_name': voice_name,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'top_p': top_p,
            'gpt_model': gpt_model,
            'created_at': '2025-11-18T12:00:00Z',
            'status': 'active'
        }
        
        logger.info(f"✅ Agent créé avec voix personnalisée: {agent_id}")
        
        return jsonify({
            'success': True,
            'agent_id': agent_id,
            'agent': agent_config,
            'message': 'Agent créé avec succès'
        })
        
    except Exception as e:
        logger.exception("Erreur création agent")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


logger.info("✅ Blueprint Personal Voice enregistré")
