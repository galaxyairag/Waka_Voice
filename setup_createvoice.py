# personal_voice.py
# Blueprint Flask pour la création de voix personnelles Azure AI Speech
# À enregistrer dans app.py avec: app.register_blueprint(personal_voice_bp, url_prefix='/personal-voice')

from flask import Blueprint, render_template, request, jsonify, current_app
import os
import uuid
import requests
import json
from datetime import datetime
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.cosmos import CosmosClient, PartitionKey
from datetime import timedelta

personal_voice_bp = Blueprint('personal_voice', __name__)

# Configuration Azure Speech
AZURE_SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY')
AZURE_SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION')
CUSTOM_VOICE_API_VERSION = '2024-02-01-preview'

# Configuration Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
BLOB_CONTAINER_ENREGISTREMENTS = 'enregistrements'

# Configuration Azure Cosmos DB
COSMOS_URI = os.getenv('COSMOS_URI')
COSMOS_KEY = os.getenv('COSMOS_KEY')
COSMOS_DATABASE_NAME = os.getenv('COSMOS_DATABASE_NAME')
COSMOS_PROJET_CONTAINER = 'projet'
COSMOS_VOIX_CONTAINER = 'voix'

# URLs de base pour l'API Custom Voice
def get_custom_voice_base_url():
    return f"https://{AZURE_SPEECH_REGION}.api.cognitive.microsoft.com/customvoice"

def get_headers():
    return {
        'Ocp-Apim-Subscription-Key': AZURE_SPEECH_KEY,
        'Content-Type': 'application/json'
    }

# Initialisation des clients Azure
def get_blob_service_client():
    return BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

def get_cosmos_client():
    return CosmosClient(COSMOS_URI, credential=COSMOS_KEY)

def get_cosmos_database():
    client = get_cosmos_client()
    return client.get_database_client(COSMOS_DATABASE_NAME)

def get_projet_container():
    database = get_cosmos_database()
    return database.get_container_client(COSMOS_PROJET_CONTAINER)

def get_voix_container():
    database = get_cosmos_database()
    return database.get_container_client(COSMOS_VOIX_CONTAINER)

# ============================================
# ROUTE PRINCIPALE - Interface
# ============================================
@personal_voice_bp.route('/')
def index():
    """Page principale de l'interface de création de voix personnelles"""
    return render_template('personal_voice.html')

# ============================================
# ÉTAPE 1: Créer un projet
# ============================================
@personal_voice_bp.route('/api/projects', methods=['POST'])
def create_project():
    """Créer un nouveau projet Personal Voice"""
    try:
        data = request.json
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
            container = get_projet_container()
            cosmos_doc = {
                'id': project_id,
                'project_name': project_name,
                'description': description,
                'kind': 'PersonalVoice',
                'status': 'created',
                'azure_response': result,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            container.create_item(body=cosmos_doc)
            
            return jsonify({
                'success': True,
                'project_id': project_id,
                'message': 'Projet créé avec succès',
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Erreur Azure: {response.status_code}",
                'details': response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@personal_voice_bp.route('/api/projects', methods=['GET'])
def list_projects():
    """Lister tous les projets Personal Voice"""
    try:
        container = get_projet_container()
        query = "SELECT * FROM c ORDER BY c.created_at DESC"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        return jsonify({
            'success': True,
            'projects': items
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@personal_voice_bp.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Obtenir les détails d'un projet"""
    try:
        # Récupérer depuis Azure
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
                'error': f"Erreur Azure: {response.status_code}"
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# ÉTAPE 2: Upload enregistrement et consentement
# ============================================
@personal_voice_bp.route('/api/upload-audio', methods=['POST'])
def upload_audio():
    """Upload un fichier audio vers Blob Storage"""
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
        
        return jsonify({
            'success': True,
            'blob_name': blob_name,
            'blob_url': blob_url,
            'message': 'Audio uploadé avec succès'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@personal_voice_bp.route('/api/consents', methods=['POST'])
def create_consent():
    """Créer un consentement pour une voix personnelle"""
    try:
        data = request.json
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
        
        payload = {
            "projectId": project_id,
            "voiceTalentName": voice_talent_name,
            "companyName": company_name,
            "audioUrl": audio_url,
            "locale": locale,
            "description": description
        }
        
        response = requests.put(url, headers=get_headers(), json=payload)
        
        if response.status_code in [200, 201, 202]:
            result = response.json()
            
            # Récupérer l'Operation-Location pour le suivi
            operation_location = response.headers.get('Operation-Location', '')
            
            # Mettre à jour le projet dans Cosmos DB
            container = get_projet_container()
            try:
                project = container.read_item(item=project_id, partition_key=project_id)
                project['consent_id'] = consent_id
                project['consent_status'] = result.get('status', 'NotStarted')
                project['operation_location'] = operation_location
                project['updated_at'] = datetime.utcnow().isoformat()
                container.replace_item(item=project_id, body=project)
            except:
                pass
            
            return jsonify({
                'success': True,
                'consent_id': consent_id,
                'message': 'Consentement envoyé avec succès',
                'data': result,
                'operation_location': operation_location
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Erreur Azure: {response.status_code}",
                'details': response.text
            }), response.status_code
            
    except Exception as e:
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
            return jsonify({
                'success': True,
                'consent': response.json()
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Erreur Azure: {response.status_code}"
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# ÉTAPE 3: Créer la voix personnelle
# ============================================
@personal_voice_bp.route('/api/personal-voices', methods=['POST'])
def create_personal_voice():
    """Créer une voix personnelle et obtenir le speaker profile ID"""
    try:
        data = request.json
        project_id = data.get('project_id')
        consent_id = data.get('consent_id')
        audio_url = data.get('audio_url')  # URL de l'échantillon vocal
        description = data.get('description', '')
        voice_name = data.get('voice_name', '')
        
        # Générer un ID unique pour la voix personnelle
        personal_voice_id = f"voice-{uuid.uuid4().hex[:12]}"
        
        # Appel API Azure pour créer la voix personnelle
        url = f"{get_custom_voice_base_url()}/personalvoices/{personal_voice_id}?api-version={CUSTOM_VOICE_API_VERSION}"
        
        payload = {
            "projectId": project_id,
            "consentId": consent_id,
            "audios": {
                "containerUrl": audio_url,
                "extensions": ["wav", "mp3"]
            },
            "description": description
        }
        
        response = requests.put(url, headers=get_headers(), json=payload)
        
        if response.status_code in [200, 201, 202]:
            result = response.json()
            
            # Récupérer l'Operation-Location pour le suivi
            operation_location = response.headers.get('Operation-Location', '')
            
            # Sauvegarder dans Cosmos DB (container voix)
            container = get_voix_container()
            cosmos_doc = {
                'id': personal_voice_id,
                'voice_name': voice_name,
                'project_id': project_id,
                'consent_id': consent_id,
                'speaker_profile_id': result.get('speakerProfileId', ''),
                'status': result.get('status', 'NotStarted'),
                'operation_location': operation_location,
                'azure_response': result,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            container.create_item(body=cosmos_doc)
            
            return jsonify({
                'success': True,
                'personal_voice_id': personal_voice_id,
                'speaker_profile_id': result.get('speakerProfileId', ''),
                'message': 'Voix personnelle en cours de création',
                'data': result,
                'operation_location': operation_location
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Erreur Azure: {response.status_code}",
                'details': response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@personal_voice_bp.route('/api/personal-voices/<voice_id>', methods=['GET'])
def get_personal_voice(voice_id):
    """Obtenir le statut d'une voix personnelle"""
    try:
        url = f"{get_custom_voice_base_url()}/personalvoices/{voice_id}?api-version={CUSTOM_VOICE_API_VERSION}"
        response = requests.get(url, headers=get_headers())
        
        if response.status_code == 200:
            result = response.json()
            
            # Mettre à jour dans Cosmos DB si le statut a changé
            if result.get('speakerProfileId'):
                try:
                    container = get_voix_container()
                    voice = container.read_item(item=voice_id, partition_key=voice_id)
                    voice['speaker_profile_id'] = result.get('speakerProfileId')
                    voice['status'] = result.get('status')
                    voice['updated_at'] = datetime.utcnow().isoformat()
                    container.replace_item(item=voice_id, body=voice)
                except:
                    pass
            
            return jsonify({
                'success': True,
                'voice': result
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Erreur Azure: {response.status_code}"
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@personal_voice_bp.route('/api/personal-voices', methods=['GET'])
def list_personal_voices():
    """Lister toutes les voix personnelles"""
    try:
        container = get_voix_container()
        query = "SELECT * FROM c ORDER BY c.created_at DESC"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        return jsonify({
            'success': True,
            'voices': items
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# ÉTAPE 4: Utiliser la voix personnelle
# ============================================
@personal_voice_bp.route('/api/synthesize', methods=['POST'])
def synthesize_speech():
    """Synthétiser du texte avec une voix personnelle"""
    try:
        data = request.json
        text = data.get('text', '')
        speaker_profile_id = data.get('speaker_profile_id', '')
        voice_name = data.get('voice_name', 'en-US-AvaMultilingualNeural')  # Voix de base
        
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# Vérification du statut des opérations
# ============================================
@personal_voice_bp.route('/api/operations/<operation_id>', methods=['GET'])
def check_operation(operation_id):
    """Vérifier le statut d'une opération Azure"""
    try:
        url = f"{get_custom_voice_base_url()}/operations/{operation_id}?api-version={CUSTOM_VOICE_API_VERSION}"
        response = requests.get(url, headers=get_headers())
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'operation': response.json()
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Erreur Azure: {response.status_code}"
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# Texte de consentement
# ============================================
@personal_voice_bp.route('/api/consent-text/<locale>', methods=['GET'])
def get_consent_text(locale):
    """Obtenir le texte de consentement pour une locale donnée"""
    consent_texts = {
        'fr-FR': "Je [prénom et nom] suis conscient(e) que les enregistrements de ma voix seront utilisés par [nom de l'entreprise] pour créer et utiliser une version synthétique de ma voix.",
        'en-US': "I [state your first and last name] am aware that recordings of my voice will be used by [state the name of the company] to create and use a synthetic version of my voice.",
        'en-GB': "I [state your first and last name] am aware that recordings of my voice will be used by [state the name of the company] to create and use a synthetic version of my voice.",
        'es-ES': "Yo [nombre y apellido] soy consciente de que las grabaciones de mi voz serán utilizadas por [nombre de la empresa] para crear y usar una versión sintética de mi voz.",
        'de-DE': "Ich [Vor- und Nachname] bin mir bewusst, dass Aufnahmen meiner Stimme von [Name des Unternehmens] verwendet werden, um eine synthetische Version meiner Stimme zu erstellen und zu verwenden.",
        'pt-BR': "Eu [nome completo] estou ciente de que as gravações da minha voz serão usadas por [nome da empresa] para criar e usar uma versão sintética da minha voz."
    }
    
    text = consent_texts.get(locale, consent_texts.get('en-US'))
    
    return jsonify({
        'success': True,
        'locale': locale,
        'consent_text': text
    })

# ============================================
# Suppression
# ============================================
@personal_voice_bp.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Supprimer un projet"""
    try:
        # Supprimer dans Azure
        url = f"{get_custom_voice_base_url()}/projects/{project_id}?api-version={CUSTOM_VOICE_API_VERSION}"
        response = requests.delete(url, headers=get_headers())
        
        # Supprimer dans Cosmos DB
        try:
            container = get_projet_container()
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

@personal_voice_bp.route('/api/personal-voices/<voice_id>', methods=['DELETE'])
def delete_personal_voice(voice_id):
    """Supprimer une voix personnelle"""
    try:
        # Supprimer dans Azure
        url = f"{get_custom_voice_base_url()}/personalvoices/{voice_id}?api-version={CUSTOM_VOICE_API_VERSION}"
        response = requests.delete(url, headers=get_headers())
        
        # Supprimer dans Cosmos DB
        try:
            container = get_voix_container()
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