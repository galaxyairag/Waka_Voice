"""
Blueprint pour la gestion des voix personnelles Azure AI
Intègre les API Microsoft Azure Custom Voice pour créer et gérer des voix personnalisées
"""
from flask import Blueprint, render_template, request, jsonify
import logging
import os
import uuid
import requests
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

logger = logging.getLogger(__name__)

personal_voice_bp = Blueprint('personal_voice', __name__, url_prefix='/creer-une-voix')

# Configuration Azure Speech pour Custom Voice API
AZURE_SPEECH_KEY = os.getenv('PERSONAL_VOICE_KEY') or os.getenv('AZURE_SPEECH_KEY')
AZURE_SPEECH_REGION = os.getenv('PERSONAL_VOICE_REGION') or os.getenv('AZURE_SPEECH_REGION', 'eastus')
CUSTOM_VOICE_API_VERSION = '2024-02-01-preview'

# Configuration Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING = os.getenv('BLOB_CONNECTION_STRING')
BLOB_CONTAINER_ENREGISTREMENTS = 'enregistrements'

# URLs de base pour l'API Custom Voice
def get_custom_voice_base_url():
    return f"https://{AZURE_SPEECH_REGION}.api.cognitive.microsoft.com/customvoice"

def get_headers():
    return {
        'Ocp-Apim-Subscription-Key': AZURE_SPEECH_KEY,
        'Content-Type': 'application/json'
    }

def get_blob_service_client():
    """Retourne le client Blob Storage"""
    if AZURE_STORAGE_CONNECTION_STRING:
        return BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    return None


def calculate_usage_counts():
    """
    Calcule le nombre d'utilisations de chaque voix personnelle basé sur l'historique des conversations.

    Returns:
        dict: Dictionnaire {speaker_profile_id: usage_count}
    """
    usage_counts = {}

    try:
        from configuration.cosmos_config import get_call_history_container, get_agents_container

        # Récupérer l'historique des conversations
        call_history_container = get_call_history_container()
        agents_container = get_agents_container()

        # Requête pour récupérer toutes les conversations complétées
        query = "SELECT c.agent_id FROM c WHERE c.status = 'completed'"

        conversations = list(call_history_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))

        logger.info(f"📊 Analyse de {len(conversations)} conversations pour calculer usage_count")

        # Créer un cache pour les configurations d'agents pour éviter les requêtes multiples
        agent_cache = {}

        for conv in conversations:
            agent_id = conv.get('agent_id')

            if not agent_id:
                continue

            # Vérifier si l'agent est déjà dans le cache
            if agent_id not in agent_cache:
                try:
                    agent = agents_container.read_item(item=agent_id, partition_key=agent_id)
                    agent_cache[agent_id] = agent
                except Exception:
                    # Agent non trouvé ou supprimé
                    agent_cache[agent_id] = None
                    continue

            agent = agent_cache[agent_id]

            if not agent:
                continue

            # Vérifier si l'agent utilise une voix personnelle
            voice_type = agent.get('voice_type')
            speaker_profile_id = agent.get('speaker_profile_id')

            if voice_type == 'personal' and speaker_profile_id:
                usage_counts[speaker_profile_id] = usage_counts.get(speaker_profile_id, 0) + 1

        logger.info(f"✅ Usage counts calculés: {len(usage_counts)} voix personnelles utilisées")
        return usage_counts

    except Exception as e:
        logger.warning(f"⚠️ Erreur lors du calcul des usage_counts: {e}")
        return {}


@personal_voice_bp.route('/api/projects', methods=['GET', 'POST'])
def manage_projects():
    """Gérer les projets de voix personnelles via Azure Custom Voice API"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            project_name = data.get('project_name', '')
            description = data.get('description', '')

            # Générer un ID unique pour le projet
            project_id = f"pv-{uuid.uuid4().hex[:12]}"

            # Appel API Azure pour créer le projet
            url = f"{get_custom_voice_base_url()}/projects/{project_id}?api-version={CUSTOM_VOICE_API_VERSION}"

            payload = {
                "description": description,
                "kind": "PersonalVoice"
            }

            response = requests.put(url, headers=get_headers(), json=payload)

            if response.status_code in [200, 201]:
                result = response.json()

                # Sauvegarder dans Cosmos DB
                try:
                    from configuration.personal_voice_storage import get_personal_voice_projects_container
                    container = get_personal_voice_projects_container()
                    cosmos_doc = {
                        'id': project_id,
                        'project_id': project_id,
                        'project_name': project_name,
                        'description': description,
                        'kind': 'PersonalVoice',
                        'status': 'created',
                        'azure_response': result,
                        'created_at': datetime.utcnow().isoformat() + 'Z',
                        'updated_at': datetime.utcnow().isoformat() + 'Z'
                    }
                    container.create_item(body=cosmos_doc)
                    logger.info(f"✅ Projet sauvegardé dans Cosmos DB: {project_id}")
                except Exception as cosmos_error:
                    logger.warning(f"⚠️ Impossible de sauvegarder dans Cosmos DB: {cosmos_error}")

                logger.info(f"✅ Projet créé via Azure API: {project_id}")

                return jsonify({
                    'success': True,
                    'project_id': project_id,
                    'status': 'created',
                    'message': 'Projet créé avec succès',
                    'data': result
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f"Erreur Azure API: {response.status_code}",
                    'details': response.text
                }), response.status_code

        except Exception as e:
            logger.exception("Erreur création projet")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    else:  # GET
        try:
            # Récupérer les projets depuis Cosmos DB
            try:
                from configuration.personal_voice_storage import get_personal_voice_projects_container
                container = get_personal_voice_projects_container()
                query = "SELECT * FROM c ORDER BY c.created_at DESC"
                items = list(container.query_items(query=query, enable_cross_partition_query=True))

                return jsonify({
                    'success': True,
                    'projects': items
                })
            except Exception as cosmos_error:
                logger.warning(f"⚠️ Cosmos DB non disponible: {cosmos_error}")
                # Fallback: retourner liste vide
                return jsonify({
                    'success': True,
                    'projects': []
                })

        except Exception as e:
            logger.exception("Erreur récupération projets")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

@personal_voice_bp.route('/api/projects/<project_id>', methods=['GET', 'DELETE'])
def manage_project(project_id):
    """Obtenir les détails ou supprimer un projet"""
    if request.method == 'GET':
        try:
            # Récupérer depuis Azure API
            url = f"{get_custom_voice_base_url()}/projects/{project_id}?api-version={CUSTOM_VOICE_API_VERSION}"
            response = requests.get(url, headers=get_headers())

            if response.status_code == 200:
                return jsonify({
                    'success': True,
                    'project': response.json()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f"Erreur Azure API: {response.status_code}"
                }), response.status_code

        except Exception as e:
            logger.exception("Erreur récupération projet")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    elif request.method == 'DELETE':
        try:
            # Supprimer dans Azure
            url = f"{get_custom_voice_base_url()}/projects/{project_id}?api-version={CUSTOM_VOICE_API_VERSION}"
            response = requests.delete(url, headers=get_headers())

            # Supprimer dans Cosmos DB
            try:
                from configuration.personal_voice_storage import get_personal_voice_projects_container
                container = get_personal_voice_projects_container()
                container.delete_item(item=project_id, partition_key=project_id)
            except:
                pass

            return jsonify({
                'success': True,
                'message': 'Projet supprimé'
            })

        except Exception as e:
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
    """Upload d'un fichier audio vers Azure Blob Storage"""
    try:
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Aucun fichier audio fourni'
            }), 400

        audio_file = request.files['audio']
        audio_type = request.form.get('type', 'consent')  # 'consent' ou 'voice'
        project_id = request.form.get('project_id', '')

        # Générer un nom de fichier unique
        file_extension = audio_file.filename.rsplit('.', 1)[-1] if '.' in audio_file.filename else 'wav'
        blob_name = f"{project_id}/{audio_type}_{uuid.uuid4().hex[:8]}.{file_extension}"

        # Upload vers Blob Storage
        blob_service_client = get_blob_service_client()
        if not blob_service_client:
            return jsonify({
                'success': False,
                'error': 'Blob Storage non configuré'
            }), 500

        container_client = blob_service_client.get_container_client(BLOB_CONTAINER_ENREGISTREMENTS)

        # Créer le container s'il n'existe pas
        try:
            container_client.create_container()
        except:
            pass  # Container existe déjà

        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(audio_file, overwrite=True)

        # Générer une URL SAS pour accès temporaire
        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=BLOB_CONTAINER_ENREGISTREMENTS,
            blob_name=blob_name,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=24)
        )

        blob_url = f"{blob_client.url}?{sas_token}"

        logger.info(f"✅ Audio uploadé vers Blob Storage: {blob_name}")

        return jsonify({
            'success': True,
            'blob_name': blob_name,
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
    """Créer un consentement via Azure Custom Voice API"""
    try:
        data = request.get_json()

        project_id = data.get('project_id')
        voice_talent_name = data.get('voice_talent_name')
        company_name = data.get('company_name')
        audio_url = data.get('audio_url')
        locale = data.get('locale', 'fr-FR')
        description = data.get('description', '')

        # Générer un ID unique pour le consentement
        consent_id = f"consent-{uuid.uuid4().hex[:12]}"

        # Appel API Azure pour créer le consentement
        url = f"{get_custom_voice_base_url()}/consents/{consent_id}?api-version={CUSTOM_VOICE_API_VERSION}"

        # Payload conforme à la documentation Microsoft
        payload = {
            "projectId": project_id,
            "voiceTalentName": voice_talent_name,
            "companyName": company_name,
            "audioUrl": audio_url,
            "locale": locale,
            "displayName": f"Consentement {voice_talent_name}",
            "description": description
        }

        response = requests.put(url, headers=get_headers(), json=payload)

        if response.status_code in [200, 201, 202]:
            result = response.json()

            # Récupérer l'Operation-Location pour le suivi
            operation_location = response.headers.get('Operation-Location', '')

            # Sauvegarder dans Cosmos DB
            try:
                from configuration.personal_voice_storage import get_personal_voice_consents_container
                container = get_personal_voice_consents_container()
                cosmos_doc = {
                    'id': consent_id,
                    'consent_id': consent_id,
                    'project_id': project_id,
                    'voice_talent_name': voice_talent_name,
                    'company_name': company_name,
                    'locale': locale,
                    'description': description,
                    'audio_url': audio_url,
                    'status': result.get('status', 'NotStarted'),
                    'operation_location': operation_location,
                    'azure_response': result,
                    'created_at': datetime.utcnow().isoformat() + 'Z'
                }
                container.create_item(body=cosmos_doc)
                logger.info(f"✅ Consentement sauvegardé dans Cosmos DB: {consent_id}")
            except Exception as cosmos_error:
                logger.warning(f"⚠️ Impossible de sauvegarder le consentement: {cosmos_error}")

            logger.info(f"✅ Consentement créé via Azure API: {consent_id}")

            return jsonify({
                'success': True,
                'consent_id': consent_id,
                'message': 'Consentement créé avec succès',
                'data': result,
                'operation_location': operation_location
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Erreur Azure API: {response.status_code}",
                'details': response.text
            }), response.status_code

    except Exception as e:
        logger.exception("Erreur création consentement")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@personal_voice_bp.route('/api/operations/status', methods=['POST'])
def check_operation_status():
    """Vérifier le statut d'une opération asynchrone Azure via Operation-Location"""
    try:
        data = request.get_json()
        operation_location = data.get('operation_location')
        
        if not operation_location:
            return jsonify({
                'success': False,
                'error': 'operation_location requis'
            }), 400
        
        # Appeler l'URL d'opération Azure
        response = requests.get(operation_location, headers=get_headers())
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status', 'Unknown')
            
            logger.info(f"📊 Statut opération: {status}")
            
            return jsonify({
                'success': True,
                'status': status,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Erreur Azure API: {response.status_code}",
                'details': response.text
            }), response.status_code
            
    except Exception as e:
        logger.exception("Erreur vérification statut opération")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@personal_voice_bp.route('/api/consents/<consent_id>', methods=['GET'])
def get_consent(consent_id):
    """Obtenir le statut d'un consentement"""
    try:
        url = f"{get_custom_voice_base_url()}/consents/{consent_id}?api-version={CUSTOM_VOICE_API_VERSION}"
        response = requests.get(url, headers=get_headers())

        if response.status_code == 200:
            result = response.json()
            
            # Mettre à jour le statut dans Cosmos DB si changé
            try:
                from configuration.personal_voice_storage import get_personal_voice_consents_container
                container = get_personal_voice_consents_container()
                consent_doc = container.read_item(item=consent_id, partition_key=consent_id)
                
                if consent_doc.get('status') != result.get('status'):
                    consent_doc['status'] = result.get('status')
                    consent_doc['updated_at'] = datetime.utcnow().isoformat() + 'Z'
                    consent_doc['azure_response'] = result
                    container.replace_item(item=consent_id, body=consent_doc)
                    logger.info(f"✅ Statut consentement mis à jour: {consent_id} -> {result.get('status')}")
            except Exception as cosmos_error:
                logger.warning(f"⚠️ Impossible de mettre à jour Cosmos DB: {cosmos_error}")
            
            return jsonify({
                'success': True,
                'consent': result
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Erreur Azure API: {response.status_code}"
            }), response.status_code

    except Exception as e:
        logger.exception("Erreur récupération consentement")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@personal_voice_bp.route('/api/personal-voices', methods=['POST'])
def create_personal_voice():
    """Créer une voix personnelle via Azure Custom Voice API"""
    try:
        data = request.get_json()

        project_id = data.get('project_id')
        consent_id = data.get('consent_id')
        # Support ancien format (audio_url) et nouveau format (container_url)
        container_url = data.get('container_url') or data.get('audio_url')
        audio_prefix = data.get('audio_prefix', '')  # Préfixe optionnel pour les fichiers
        audio_extensions = data.get('audio_extensions', ['.wav'])  # Extensions avec point
        voice_name = data.get('voice_name', '')
        description = data.get('description', '')

        # Validation des entrées
        if not all([project_id, consent_id, container_url]):
            logger.error(f"❌ Paramètres manquants - project_id: {project_id}, consent_id: {consent_id}, container_url: {container_url}")
            return jsonify({
                'success': False,
                'error': 'project_id, consent_id et container_url (ou audio_url) sont requis',
                'received': {
                    'project_id': project_id,
                    'consent_id': consent_id, 
                    'container_url': container_url
                }
            }), 400

        # Générer un ID unique pour la voix personnelle
        personal_voice_id = f"voice-{uuid.uuid4().hex[:12]}"

        # Appel API Azure pour créer la voix personnelle
        url = f"{get_custom_voice_base_url()}/personalvoices/{personal_voice_id}?api-version={CUSTOM_VOICE_API_VERSION}"

        # Payload conforme à la documentation Microsoft
        payload = {
            "projectId": project_id,
            "consentId": consent_id,
            "audios": {
                "containerUrl": container_url,  # URL conteneur blob + SAS
                "extensions": audio_extensions,  # ['.wav', '.mp3']
                "prefix": audio_prefix  # Optionnel
            },
            "displayName": voice_name,
            "description": description
        }
        
        # Retirer prefix s'il est vide
        if not audio_prefix:
            del payload["audios"]["prefix"]

        response = requests.put(url, headers=get_headers(), json=payload)

        if response.status_code in [200, 201, 202]:
            result = response.json()

            # Récupérer l'Operation-Location et Operation-Id pour le suivi
            operation_location = response.headers.get('Operation-Location', '')
            operation_id = response.headers.get('Operation-Id', '')

            # Sauvegarder dans Cosmos DB
            try:
                from configuration.personal_voice_storage import get_personal_voices_container
                container = get_personal_voices_container()
                cosmos_doc = {
                    'id': personal_voice_id,
                    'voice_id': personal_voice_id,
                    'voice_name': voice_name,
                    'display_name': result.get('displayName', voice_name),
                    'project_id': project_id,
                    'consent_id': consent_id,
                    'speaker_profile_id': result.get('speakerProfileId', ''),
                    'status': result.get('status', 'NotStarted'),
                    'operation_location': operation_location,
                    'operation_id': operation_id,
                    'failure_reason': result.get('properties', {}).get('failureReason'),
                    'azure_response': result,
                    'created_at': result.get('createdDateTime', datetime.utcnow().isoformat() + 'Z'),
                    'last_action_at': result.get('lastActionDateTime', datetime.utcnow().isoformat() + 'Z'),
                    'updated_at': datetime.utcnow().isoformat() + 'Z'
                }
                container.create_item(body=cosmos_doc)
                logger.info(f"✅ Voix sauvegardée dans Cosmos DB: {personal_voice_id}")
            except Exception as cosmos_error:
                logger.warning(f"⚠️ Impossible de sauvegarder la voix: {cosmos_error}")

            logger.info(f"✅ Voix personnelle créée via Azure API: {personal_voice_id} (status: {result.get('status')})")

            return jsonify({
                'success': True,
                'personal_voice_id': personal_voice_id,
                'speaker_profile_id': result.get('speakerProfileId', ''),
                'status': result.get('status', 'NotStarted'),
                'message': 'Voix personnelle en cours de création',
                'data': result,
                'operation_location': operation_location,
                'operation_id': operation_id
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Erreur Azure API: {response.status_code}",
                'details': response.text
            }), response.status_code

    except Exception as e:
        logger.exception("Erreur création voix personnelle")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@personal_voice_bp.route('/api/personal-voices/<voice_id>/poll', methods=['GET'])
def poll_voice_creation_status(voice_id):
    """Polling du statut de création d'une voix personnelle avec mise à jour Cosmos DB"""
    try:
        # Récupérer depuis Cosmos DB pour avoir l'operation_location
        from configuration.personal_voice_storage import get_personal_voices_container
        container = get_personal_voices_container()
        
        voice_doc = container.read_item(item=voice_id, partition_key=voice_id)
        operation_location = voice_doc.get('operation_location')
        
        if not operation_location:
            # Fallback: appeler l'API directement
            url = f"{get_custom_voice_base_url()}/personalvoices/{voice_id}?api-version={CUSTOM_VOICE_API_VERSION}"
            response = requests.get(url, headers=get_headers())
        else:
            # Utiliser l'operation_location pour un suivi précis
            response = requests.get(operation_location, headers=get_headers())
        
        if response.status_code == 200:
            result = response.json()
            current_status = result.get('status', 'Unknown')
            
            # Mettre à jour Cosmos DB
            voice_doc['status'] = current_status
            voice_doc['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            
            if result.get('speakerProfileId'):
                voice_doc['speaker_profile_id'] = result.get('speakerProfileId')
            
            # Si terminé avec succès ou échec, mettre à jour les infos
            if current_status == 'Succeeded':
                voice_doc['trained_at'] = datetime.utcnow().isoformat() + 'Z'
                logger.info(f"✅ Voix {voice_id} créée avec succès")
            elif current_status == 'Failed':
                voice_doc['error_message'] = result.get('error', {}).get('message', 'Erreur inconnue')
                logger.error(f"❌ Échec création voix {voice_id}: {voice_doc['error_message']}")
            
            voice_doc['azure_response'] = result
            container.replace_item(item=voice_id, body=voice_doc)
            
            return jsonify({
                'success': True,
                'voice_id': voice_id,
                'status': current_status,
                'speaker_profile_id': voice_doc.get('speaker_profile_id', ''),
                'is_complete': current_status in ['Succeeded', 'Failed'],
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Erreur Azure API: {response.status_code}",
                'details': response.text
            }), response.status_code
            
    except Exception as e:
        logger.exception(f"Erreur polling voix {voice_id}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@personal_voice_bp.route('/api/personal-voices/<voice_id>', methods=['GET', 'DELETE'])
def manage_personal_voice(voice_id):
    """Obtenir les détails ou supprimer une voix personnelle"""
    if request.method == 'GET':
        try:
            # Récupérer depuis Azure API
            url = f"{get_custom_voice_base_url()}/personalvoices/{voice_id}?api-version={CUSTOM_VOICE_API_VERSION}"
            response = requests.get(url, headers=get_headers())

            if response.status_code == 200:
                result = response.json()

                # Mettre à jour dans Cosmos DB si le statut a changé
                if result.get('speakerProfileId'):
                    try:
                        from configuration.personal_voice_storage import get_personal_voices_container
                        container = get_personal_voices_container()
                        voice = container.read_item(item=voice_id, partition_key=voice_id)
                        voice['speaker_profile_id'] = result.get('speakerProfileId')
                        voice['status'] = result.get('status')
                        voice['updated_at'] = datetime.utcnow().isoformat() + 'Z'
                        voice['azure_response'] = result
                        container.replace_item(item=voice_id, body=voice)
                        logger.info(f"✅ Voix {voice_id} mise à jour dans Cosmos DB")
                    except Exception as cosmos_error:
                        logger.warning(f"⚠️ Impossible de mettre à jour Cosmos: {cosmos_error}")

                return jsonify({
                    'success': True,
                    'voice': result
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f"Erreur Azure API: {response.status_code}"
                }), response.status_code

        except Exception as e:
            logger.exception("Erreur récupération voix")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    elif request.method == 'DELETE':
        try:
            # Supprimer dans Azure
            url = f"{get_custom_voice_base_url()}/personalvoices/{voice_id}?api-version={CUSTOM_VOICE_API_VERSION}"
            response = requests.delete(url, headers=get_headers())

            # Supprimer dans Cosmos DB
            try:
                from configuration.personal_voice_storage import get_personal_voices_container
                container = get_personal_voices_container()
                container.delete_item(item=voice_id, partition_key=voice_id)
            except:
                pass

            return jsonify({
                'success': True,
                'message': 'Voix personnelle supprimée'
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

@personal_voice_bp.route('/api/synthesize', methods=['POST'])
def synthesize_speech():
    """Synthétiser du texte avec une voix personnelle via Azure TTS"""
    try:
        data = request.get_json()

        text = data.get('text', '')
        speaker_profile_id = data.get('speaker_profile_id', '')
        voice_name = data.get('voice_name', 'en-US-AvaMultilingualNeural')

        # Construire le SSML avec la voix personnelle
        ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
                   xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="en-US">
            <voice name="{voice_name}">
                <mstts:ttsembedding speakerProfileId="{speaker_profile_id}">
                    {text}
                </mstts:ttsembedding>
            </voice>
        </speak>'''

        # Appel API Text-to-Speech
        url = f"https://{AZURE_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"

        headers = {
            'Ocp-Apim-Subscription-Key': AZURE_SPEECH_KEY,
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': 'audio-24khz-48kbitrate-mono-mp3'
        }

        response = requests.post(url, headers=headers, data=ssml.encode('utf-8'))

        if response.status_code == 200:
            # Sauvegarder l'audio généré dans Blob Storage
            blob_name = f"synthesized/{uuid.uuid4().hex[:12]}.mp3"

            blob_service_client = get_blob_service_client()
            if blob_service_client:
                container_client = blob_service_client.get_container_client(BLOB_CONTAINER_ENREGISTREMENTS)
                blob_client = container_client.get_blob_client(blob_name)
                blob_client.upload_blob(response.content, overwrite=True)

                # Générer URL SAS
                sas_token = generate_blob_sas(
                    account_name=blob_service_client.account_name,
                    container_name=BLOB_CONTAINER_ENREGISTREMENTS,
                    blob_name=blob_name,
                    account_key=blob_service_client.credential.account_key,
                    permission=BlobSasPermissions(read=True),
                    expiry=datetime.utcnow() + timedelta(hours=1)
                )

                audio_url = f"{blob_client.url}?{sas_token}"
            else:
                # Fallback si pas de Blob Storage
                audio_url = "data:audio/mp3;base64,..."

            logger.info(f"✅ Synthèse réalisée pour speaker: {speaker_profile_id}")

            return jsonify({
                'success': True,
                'audio_url': audio_url,
                'message': 'Synthèse vocale réussie'
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Erreur Azure TTS: {response.status_code}",
                'details': response.text
            }), response.status_code

    except Exception as e:
        logger.exception("Erreur synthèse vocale")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@personal_voice_bp.route('/api/operations/pending', methods=['GET'])
def list_pending_operations():
    """Liste toutes les opérations de création de voix en cours"""
    try:
        from configuration.personal_voice_storage import get_personal_voices_container, get_personal_voice_consents_container
        
        voices_container = get_personal_voices_container()
        consents_container = get_personal_voice_consents_container()
        
        # Requête pour les voix en cours de création
        voices_query = "SELECT * FROM c WHERE c.status IN ('NotStarted', 'Running')"
        pending_voices = list(voices_container.query_items(
            query=voices_query,
            enable_cross_partition_query=True
        ))
        
        # Requête pour les consentements en cours
        consents_query = "SELECT * FROM c WHERE c.status IN ('NotStarted', 'Running')"
        pending_consents = list(consents_container.query_items(
            query=consents_query,
            enable_cross_partition_query=True
        ))
        
        logger.info(f"📊 {len(pending_voices)} voix et {len(pending_consents)} consentements en cours")
        
        return jsonify({
            'success': True,
            'pending_voices': pending_voices,
            'pending_consents': pending_consents,
            'total_pending': len(pending_voices) + len(pending_consents)
        })
        
    except Exception as e:
        logger.exception("Erreur récupération opérations en cours")
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


@personal_voice_bp.route('/')
def index():
    """
    Page principale de création de voix personnalisée
    Interface complète pour créer une nouvelle voix personnalisée Azure AI
    """
    return render_template('Personal_voice.html')


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
