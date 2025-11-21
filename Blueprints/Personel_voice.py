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
import azure.cognitiveservices.speech as speechsdk    
import re
from difflib import SequenceMatcher
import tempfile

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
    """Retourne les headers pour les appels API Azure Custom Voice"""
    if not AZURE_SPEECH_KEY:
        logger.error("❌ AZURE_SPEECH_KEY non configurée !")
        raise ValueError("AZURE_SPEECH_KEY non configurée")
    
    return {
        'Ocp-Apim-Subscription-Key': AZURE_SPEECH_KEY,
        'Content-Type': 'application/json'
    }

def get_blob_service_client():
    """Retourne le client Blob Storage"""
    if AZURE_STORAGE_CONNECTION_STRING:
        return BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    return None


@personal_voice_bp.route('/api/transcribe-consent', methods=['POST'])
def transcribe_consent():
    """Transcrit l'audio et compare avec le texte attendu"""
    temp_audio_path = None
    
    try:
        data = request.get_json()
        audio_url = data.get('audio_url')
        expected_text = data.get('expected_text')
        locale = data.get('locale', 'fr-FR')
        
        if not audio_url or not expected_text:
            return jsonify({
                'success': False,
                'error': 'audio_url et expected_text requis'
            }), 400
        
        print(f"🎙️ Transcription demandée:")
        print(f"  - Audio URL: {audio_url}")
        print(f"  - Locale: {locale}")
        print(f"  - Texte attendu: {expected_text[:100]}...")
        
        # Configuration Azure Speech
        speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY,
            region=AZURE_SPEECH_REGION
        )
        speech_config.speech_recognition_language = locale
        
        print(f"✅ Speech config créé - Région: {AZURE_SPEECH_REGION}, Locale: {locale}")
        
        # Télécharger l'audio temporairement
        print(f"📥 Téléchargement audio depuis: {audio_url}")
        response = requests.get(audio_url, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Erreur téléchargement: {response.status_code}")
            return jsonify({
                'success': False,
                'error': f'Impossible de télécharger l\'audio (code {response.status_code})'
            }), 400
        
        print(f"✅ Audio téléchargé: {len(response.content)} bytes")
        
        # Sauvegarder temporairement
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            temp_audio.write(response.content)
            temp_audio_path = temp_audio.name
        
        print(f"📁 Audio sauvegardé: {temp_audio_path}")
        
        # Créer AudioConfig depuis le fichier
        audio_config = speechsdk.audio.AudioConfig(filename=temp_audio_path)
        
        # Créer recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        # Reconnaissance
        print("🎤 Démarrage transcription...")
        result = speech_recognizer.recognize_once()
        
        print(f"📊 Résultat reconnaissance: {result.reason}")
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            transcribed_text = result.text
            print(f"✅ Transcription réussie: {transcribed_text}")
            
            # Comparer avec le texte attendu
            comparison = compare_texts(expected_text, transcribed_text)
            
            return jsonify({
                'success': True,
                'transcribed_text': transcribed_text,
                'expected_text': expected_text,
                'comparison': comparison
            })
        
        elif result.reason == speechsdk.ResultReason.NoMatch:
            print("❌ Aucune parole détectée")
            no_match_details = result.no_match_details
            print(f"   Raison: {no_match_details}")
            return jsonify({
                'success': False,
                'error': 'Aucune parole détectée dans l\'audio'
            }), 400
        
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"❌ Reconnaissance annulée: {cancellation_details.reason}")
            
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"   Code erreur: {cancellation_details.error_code}")
                print(f"   Détails: {cancellation_details.error_details}")
                
                return jsonify({
                    'success': False,
                    'error': f'Erreur transcription: {cancellation_details.error_details}'
                }), 500
            
            return jsonify({
                'success': False,
                'error': f'Reconnaissance annulée: {cancellation_details.reason}'
            }), 500
        
        else:
            print(f"❌ Statut inattendu: {result.reason}")
            return jsonify({
                'success': False,
                'error': f'Erreur transcription: statut {result.reason}'
            }), 500
    
    except Exception as e:
        print(f"❌ Erreur transcribe_consent: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    finally:
        # Nettoyer fichier temporaire dans tous les cas
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
                print(f"🗑️ Fichier temporaire supprimé: {temp_audio_path}")
            except Exception as cleanup_error:
                print(f"⚠️ Impossible de supprimer {temp_audio_path}: {cleanup_error}")


def compare_texts(expected, transcribed):
    """
    Compare deux textes et retourne un score de similarité
    Scores: Consentement 90%, Audios 80%
    """
    
    # Normaliser les textes
    def normalize(text):
        # Minuscules
        text = text.lower()
        # Supprimer ponctuation
        text = re.sub(r'[^\w\s]', '', text)
        # Supprimer espaces multiples
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    expected_norm = normalize(expected)
    transcribed_norm = normalize(transcribed)
    
    print(f"📊 Comparaison:")
    print(f"  - Attendu (norm): {expected_norm}")
    print(f"  - Transcrit (norm): {transcribed_norm}")
    
    # Mots attendus et transcrits
    expected_words = expected_norm.split()
    transcribed_words = transcribed_norm.split()
    
    # Mots communs
    expected_set = set(expected_words)
    transcribed_set = set(transcribed_words)
    common_words = expected_set.intersection(transcribed_set)
    
    # Calcul scores
    if len(expected_words) == 0:
        word_accuracy = 0
    else:
        word_accuracy = int((len(common_words) / len(expected_words)) * 100)
    
    # Similarité globale (Levenshtein)
    similarity_ratio = SequenceMatcher(None, expected_norm, transcribed_norm).ratio()
    similarity_percentage = int(similarity_ratio * 100)
    
    # Mots manquants
    missing_words = list(expected_set - transcribed_set)
    
    # Niveau de validation (adapté aux nouveaux seuils)
    if similarity_percentage >= 95:
        validation_level = 'parfait'
        recommendation = '✅ Validation parfaite ! Le texte correspond exactement.'
    elif similarity_percentage >= 90:
        validation_level = 'excellent'
        recommendation = '✅ Excellente correspondance ! Validation réussie.'
    elif similarity_percentage >= 80:
        validation_level = 'très bien'
        recommendation = '✅ Très bonne correspondance. Validation acceptée.'
    elif similarity_percentage >= 70:
        validation_level = 'bien'
        recommendation = '⚠️ Bonne correspondance. Vous pouvez valider ou réenregistrer.'
    elif similarity_percentage >= 60:
        validation_level = 'moyen'
        recommendation = '⚠️ Correspondance moyenne. Réenregistrez pour améliorer le score.'
    else:
        validation_level = 'faible'
        recommendation = '❌ Faible correspondance. Veuillez réenregistrer en lisant le texte précisément.'
    
    result = {
        'similarity_percentage': similarity_percentage,
        'word_accuracy': word_accuracy,
        'common_words_count': len(common_words),
        'total_expected_words': len(expected_words),
        'total_transcribed_words': len(transcribed_words),
        'missing_words': missing_words[:10],  # Limiter à 10 mots
        'validation_level': validation_level,
        'recommendation': recommendation,
        'is_valid': similarity_percentage >= 70  # Seuil général minimal
    }
    
    print(f"📈 Résultats comparaison:")
    print(f"  - Similarité: {similarity_percentage}%")
    print(f"  - Précision mots: {word_accuracy}%")
    print(f"  - Mots communs: {len(common_words)}/{len(expected_words)}")
    print(f"  - Validation: {validation_level}")
    
    return result


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


@personal_voice_bp.route('/api/upload-audio', methods=['POST'])
def upload_audio():
    """Upload d'un fichier audio vers Azure Blob Storage"""
    try:
        logger.info("📤 Début upload audio vers Blob Storage")
        
        if 'audio' not in request.files:
            logger.error("❌ Aucun fichier audio dans la requête")
            return jsonify({
                'success': False,
                'error': 'Aucun fichier audio fourni'
            }), 400

        audio_file = request.files['audio']
        audio_type = request.form.get('type', 'consent')
        project_id = request.form.get('project_id', '')
        
        logger.info(f"📁 Fichier: {audio_file.filename}, Type: {audio_type}, Projet: {project_id}")

        # Générer un nom de fichier unique
        file_extension = audio_file.filename.rsplit('.', 1)[-1] if '.' in audio_file.filename else 'wav'
        blob_name = f"{project_id}/{audio_type}_{uuid.uuid4().hex[:8]}.{file_extension}"
        
        logger.info(f"🏷️ Nom blob généré: {blob_name}")

        # Upload vers Blob Storage
        blob_service_client = get_blob_service_client()
        if not blob_service_client:
            logger.error("❌ Blob Storage client non configuré")
            return jsonify({
                'success': False,
                'error': 'Blob Storage non configuré'
            }), 500

        container_client = blob_service_client.get_container_client(BLOB_CONTAINER_ENREGISTREMENTS)

        # Créer le container s'il n'existe pas
        try:
            container_client.create_container()
            logger.info(f"✅ Container '{BLOB_CONTAINER_ENREGISTREMENTS}' créé")
        except Exception as e:
            logger.debug(f"Container existe déjà: {e}")

        blob_client = container_client.get_blob_client(blob_name)
        
        # Lire le contenu du fichier
        audio_data = audio_file.read()
        logger.info(f"📊 Taille fichier: {len(audio_data)} bytes")
        
        # Upload
        blob_client.upload_blob(audio_data, overwrite=True)
        logger.info(f"✅ Blob uploadé: {blob_name}")

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
        
        if not data:
            logger.error("❌ Aucune donnée JSON reçue")
            return jsonify({
                'success': False,
                'error': 'Aucune donnée JSON reçue'
            }), 400

        project_id = data.get('project_id')
        voice_talent_name = data.get('voice_talent_name')
        company_name = data.get('company_name')
        audio_url = data.get('audio_url')
        locale = data.get('locale', 'fr-FR')
        description = data.get('description', '')
        
        # Validation des champs requis
        if not all([project_id, voice_talent_name, company_name, audio_url]):
            logger.error(f"❌ Champs manquants")
            return jsonify({
                'success': False,
                'error': 'Tous les champs sont requis'
            }), 400

        # Générer un ID unique pour le consentement
        consent_id = f"consent-{uuid.uuid4().hex[:12]}"
        
        logger.info(f"📝 Création consentement - ID: {consent_id}")

        # Appel API Azure
        url = f"{get_custom_voice_base_url()}/consents/{consent_id}?api-version={CUSTOM_VOICE_API_VERSION}"

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
                    'status': result.get('status', 'NotStarted'),
                    'operation_location': operation_location,
                    'azure_response': result,
                    'created_at': datetime.utcnow().isoformat() + 'Z'
                }
                container.create_item(body=cosmos_doc)
                logger.info(f"✅ Consentement sauvegardé: {consent_id}")
            except Exception as cosmos_error:
                logger.warning(f"⚠️ Cosmos DB: {cosmos_error}")

            return jsonify({
                'success': True,
                'consent_id': consent_id,
                'message': 'Consentement créé avec succès',
                'data': result
            })
        else:
            logger.error(f"❌ Erreur Azure API {response.status_code}")
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


@personal_voice_bp.route('/api/consents/<consent_id>', methods=['GET'])
def get_consent(consent_id):
    """Obtenir le statut d'un consentement"""
    try:
        url = f"{get_custom_voice_base_url()}/consents/{consent_id}?api-version={CUSTOM_VOICE_API_VERSION}"
        response = requests.get(url, headers=get_headers())

        if response.status_code == 200:
            result = response.json()
            
            # Mettre à jour dans Cosmos DB
            try:
                from configuration.personal_voice_storage import get_personal_voice_consents_container
                container = get_personal_voice_consents_container()
                consent_doc = container.read_item(item=consent_id, partition_key=consent_id)
                
                if consent_doc.get('status') != result.get('status'):
                    consent_doc['status'] = result.get('status')
                    consent_doc['updated_at'] = datetime.utcnow().isoformat() + 'Z'
                    consent_doc['azure_response'] = result
                    container.replace_item(item=consent_id, body=consent_doc)
            except:
                pass
            
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
        audio_urls = data.get('audio_urls', [])  # Liste des 3 URLs
        voice_name = data.get('voice_name', '')
        description = data.get('description', '')

        # Validation détaillée
        if not project_id:
            return jsonify({
                'success': False,
                'error': 'project_id est requis'
            }), 400
        
        if not consent_id:
            return jsonify({
                'success': False,
                'error': 'consent_id est requis'
            }), 400
        
        if not audio_urls or not isinstance(audio_urls, list) or len(audio_urls) == 0:
            return jsonify({
                'success': False,
                'error': 'audio_urls (liste d\'URLs) est requis'
            }), 400

        logger.info(f"📝 Création voix personnelle:")
        logger.info(f"  - Project ID: {project_id}")
        logger.info(f"  - Consent ID: {consent_id}")
        logger.info(f"  - Audio URLs: {len(audio_urls)} fichiers")
        logger.info(f"  - Voice Name: {voice_name}")

        # Générer un ID unique
        personal_voice_id = f"voice-{uuid.uuid4().hex[:12]}"

        # Préparer les audios pour Azure
        # Azure attend un container URL, pas des URLs individuelles
        # On va uploader dans un container et donner le container URL
        
        # Extraire l'URL du container depuis la première URL
        # Format: https://account.blob.core.windows.net/container/project_id/file.wav?sas_token
        container_url = audio_urls[0].rsplit('/', 1)[0] if audio_urls else ""
        
        # Enlever le SAS token si présent
        if '?' in container_url:
            base_url, sas_token = container_url.rsplit('?', 1)
            # Garder juste l'URL du dossier avec le SAS token sur le container
            # Azure a besoin du container URL avec SAS
            container_parts = audio_urls[0].split('?')
            if len(container_parts) > 1:
                # Reconstruire avec le bon format
                container_url = container_url  # Garder l'URL du dossier projet
        
        logger.info(f"  - Container URL: {container_url}")

        url = f"{get_custom_voice_base_url()}/personalvoices/{personal_voice_id}?api-version={CUSTOM_VOICE_API_VERSION}"

        payload = {
            "projectId": project_id,
            "consentId": consent_id,
            "audios": {
                "containerUrl": container_url,
                "extensions": ['.wav']
            },
            "displayName": voice_name,
            "description": description
        }

        response = requests.put(url, headers=get_headers(), json=payload)

        if response.status_code in [200, 201, 202]:
            result = response.json()
            operation_location = response.headers.get('Operation-Location', '')

            # Sauvegarder dans Cosmos DB
            try:
                from configuration.personal_voice_storage import get_personal_voices_container
                container = get_personal_voices_container()
                cosmos_doc = {
                    'id': personal_voice_id,
                    'voice_id': personal_voice_id,
                    'voice_name': voice_name,
                    'project_id': project_id,
                    'consent_id': consent_id,
                    'speaker_profile_id': result.get('speakerProfileId', ''),
                    'status': result.get('status', 'NotStarted'),
                    'operation_location': operation_location,
                    'azure_response': result,
                    'created_at': datetime.utcnow().isoformat() + 'Z'
                }
                container.create_item(body=cosmos_doc)
                logger.info(f"✅ Voix sauvegardée: {personal_voice_id}")
            except:
                pass

            return jsonify({
                'success': True,
                'personal_voice_id': personal_voice_id,
                'speaker_profile_id': result.get('speakerProfileId', ''),
                'status': result.get('status', 'NotStarted'),
                'message': 'Voix en cours de création',
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Erreur Azure API: {response.status_code}",
                'details': response.text
            }), response.status_code

    except Exception as e:
        logger.exception("Erreur création voix")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@personal_voice_bp.route('/api/personal-voices/<voice_id>', methods=['GET', 'DELETE'])
def manage_personal_voice(voice_id):
    """Obtenir ou supprimer une voix personnelle"""
    if request.method == 'GET':
        try:
            url = f"{get_custom_voice_base_url()}/personalvoices/{voice_id}?api-version={CUSTOM_VOICE_API_VERSION}"
            response = requests.get(url, headers=get_headers())

            if response.status_code == 200:
                result = response.json()

                # Mettre à jour dans Cosmos DB
                if result.get('speakerProfileId'):
                    try:
                        from configuration.personal_voice_storage import get_personal_voices_container
                        container = get_personal_voices_container()
                        voice = container.read_item(item=voice_id, partition_key=voice_id)
                        voice['speaker_profile_id'] = result.get('speakerProfileId')
                        voice['status'] = result.get('status')
                        voice['updated_at'] = datetime.utcnow().isoformat() + 'Z'
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
                'message': 'Voix supprimée'
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


@personal_voice_bp.route('/api/synthesize', methods=['POST'])
def synthesize_speech():
    """Synthétiser du texte avec une voix personnelle"""
    try:
        data = request.get_json()

        text = data.get('text', '')
        speaker_profile_id = data.get('speaker_profile_id', '')
        voice_name = data.get('voice_name', 'en-US-AvaMultilingualNeural')

        # Construire le SSML
        ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
                   xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="en-US">
            <voice name="{voice_name}">
                <mstts:ttsembedding speakerProfileId="{speaker_profile_id}">
                    {text}
                </mstts:ttsembedding>
            </voice>
        </speak>'''

        # Appel API TTS
        url = f"https://{AZURE_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"

        headers = {
            'Ocp-Apim-Subscription-Key': AZURE_SPEECH_KEY,
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': 'audio-24khz-48kbitrate-mono-mp3'
        }

        response = requests.post(url, headers=headers, data=ssml.encode('utf-8'))

        if response.status_code == 200:
            # Sauvegarder l'audio
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
                audio_url = "data:audio/mp3;base64,..."

            return jsonify({
                'success': True,
                'audio_url': audio_url,
                'message': 'Synthèse réussie'
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Erreur Azure TTS: {response.status_code}",
                'details': response.text
            }), response.status_code

    except Exception as e:
        logger.exception("Erreur synthèse")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@personal_voice_bp.route('/')
def index():
    """Page principale de création de voix personnalisée"""
    return render_template('personal_voice.html')


logger.info("✅ Blueprint Personal Voice enregistré - Scores: Consentement 90%, Audios 80%")