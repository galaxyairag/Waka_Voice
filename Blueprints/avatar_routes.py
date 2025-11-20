"""
Blueprint pour la gestion des avatars Azure AI
"""
from flask import Blueprint, render_template, request, jsonify, session, g
import logging
import os

logger = logging.getLogger(__name__)

avatar_bp = Blueprint('avatar', __name__, url_prefix='/avatar')


@avatar_bp.before_request
def load_avatar_config():
    """Charge la config avatar dans g pour éviter requêtes redondantes"""
    agent_id = request.view_args.get('agent_id') if request.view_args else None
    if agent_id:
        try:
            from configuration.cosmos_config import get_avatar_config
            g.avatar_config = get_avatar_config(agent_id)
        except Exception as e:
            logger.warning(f"Erreur chargement config avatar {agent_id}: {e}")
            g.avatar_config = None


def validate_uuid(uuid_string):
    """Valide un UUID"""
    try:
        import uuid
        uuid.UUID(uuid_string)
        return True
    except (ValueError, AttributeError):
        return False

@avatar_bp.route('/')
def index():
    """Page principale de gestion des avatars - Affiche la galerie"""
    from flask import redirect, url_for
    return redirect(url_for('avatar.avatar_gallery'))

@avatar_bp.route('/gallery')
def avatar_gallery():
    """Galerie des agents avatar"""
    try:
        from configuration.cosmos_config import get_avatar_container
        from azure.cosmos import exceptions
        
        container = get_avatar_container()
        
        # Récupérer tous les avatars
        query = "SELECT * FROM c ORDER BY c.created_at DESC"
        avatars = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        # Log pour debug - vérifier les agent_id
        for avatar in avatars:
            if not avatar.get('agent_id'):
                logger.warning(f"⚠️ Avatar sans agent_id trouvé: {avatar.get('id')} - {avatar.get('agent_name')}")
        
        # Calculer les statistiques
        total = len(avatars)
        active_count = sum(1 for a in avatars if a.get('status') == 'active')
        draft_count = sum(1 for a in avatars if a.get('status') != 'active')
        
        logger.info(f"📊 Affichage galerie: {total} avatars ({active_count} actifs, {draft_count} en config)")
        
        return render_template(
            'avatar/avatar_gallery.html',
            avatars=avatars,
            total=total,
            active_count=active_count,
            draft_count=draft_count
        )
        
    except Exception as e:
        logger.exception("Erreur affichage galerie avatars")
        return render_template(
            'avatar/avatar_gallery.html',
            avatars=[],
            total=0,
            active_count=0,
            draft_count=0,
            error=str(e)
        )

@avatar_bp.route('/step1', methods=['GET'])
def avatar_config_step1():
    """
    Page de sélection du modèle pour avatars
    Utilise le template avatar/avatar_step1.html
    """
    return render_template('avatar/avatar_step1.html', voice_type='avatar')

@avatar_bp.route('/step2', methods=['POST'])
def avatar_config_step2_create():
    """
    Crée un agent avec avatar et redirige vers step2
    """
    try:
        from datetime import datetime
        import uuid
        from flask import redirect, url_for
        
        # Validation des paramètres requis
        config_type = request.form.get('config_type', 'voice_live')
        model_id = request.form.get('model_id')
        model_name = request.form.get('model_name')
        
        if not model_id or not config_type:
            return jsonify({"success": False, "error": "Paramètres manquants (model_id, config_type)"}), 400
        
        # Récupérer les autres paramètres
        model_description = request.form.get('model_description', '')
        model_family = request.form.get('model_family', 'F1_Realtime')
        agent_name = request.form.get('agent_name') or f"Agent Avatar {model_name}"
        
        # Générer un agent_id unique
        agent_id = str(uuid.uuid4())
        
        # Configuration initiale avec flag voice_type='avatar'
        initial_config = {
            'id': agent_id,
            'agent_id': agent_id,
            'agent_name': agent_name,
            'status': 'step1_completed',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'config_type': config_type,
            'model_id': model_id,
            'model_name': model_name,
            'model_description': model_description,
            'model_family': model_family,
            'current_step': 2,
            'voice_type': 'avatar',
            'metadata': {
                'version': 1,
                'avatar_source': 'azure_avatar'
            }
        }
        
        # Sauvegarder dans Cosmos DB
        from configuration.cosmos_config import save_avatar_config
        save_avatar_config(initial_config)
        logger.info(f"✅ Avatar {agent_id} créé: {agent_name}")
        
        # Rediriger vers step2
        return redirect(url_for('avatar.avatar_config_step2', agent_id=agent_id))
        
    except Exception as e:
        logger.exception("Erreur création avatar")
        return jsonify({"success": False, "error": str(e)}), 500

@avatar_bp.route('/step2/<agent_id>', methods=['GET', 'POST'])
def avatar_config_step2(agent_id):
    """
    Step 2: Configuration de la voix pour avatars
    """
    from configuration.cosmos_config import update_avatar_config
    from flask import redirect, url_for
    
    # Validation UUID
    if not validate_uuid(agent_id):
        return jsonify({"success": False, "error": "agent_id invalide"}), 400
    
    if request.method == 'POST':
        try:
            # Debug: afficher tous les champs du formulaire reçus
            logger.info(f"📥 Formulaire reçu - Tous les champs: {dict(request.form)}")
            
            # Récupérer tous les champs du formulaire (voix + avatar)
            step2_data = {
                'voice_type': request.form.get('voice_type'),
                'voice_name': request.form.get('voice_name'),
                'custom_voice_endpoint': request.form.get('custom_voice_endpoint'),
                'speaker_profile_id': request.form.get('speaker_profile_id'),
                'voice_locale': request.form.get('voice_locale'),
                'voice_gender': request.form.get('voice_gender'),
                'avatar_character': request.form.get('avatar_character'),
                'avatar_style': request.form.get('avatar_style'),
                'avatar_customized': request.form.get('avatar_customized') == 'on',
                'avatar_background_color': request.form.get('avatar_background_color'),
                'avatar_background_image': request.form.get('avatar_background_image'),
                'avatar_video_width': request.form.get('avatar_video_width'),
                'avatar_video_height': request.form.get('avatar_video_height'),
                'avatar_bitrate': request.form.get('avatar_bitrate'),
                'current_step': 3,
                'status': 'step2_completed'
            }
            
            logger.info(f"📋 Données brutes extraites: avatar_character='{step2_data.get('avatar_character')}', avatar_style='{step2_data.get('avatar_style')}'")
            
            # Nettoyer les valeurs None et les chaînes vides
            step2_data = {k: v for k, v in step2_data.items() if v not in [None, '']}
            
            # Log pour debug
            logger.info(f"📝 Données Step 2 après nettoyage: {step2_data}")
            
            # Sauvegarder
            update_avatar_config(agent_id, step2_data)
            logger.info(f"✅ Step 2 complété pour avatar {agent_id}")
            
            return redirect(url_for('avatar.avatar_config_step3', agent_id=agent_id))
            
        except Exception as e:
            logger.exception("Erreur step2 POST")
            return jsonify({"success": False, "error": str(e)}), 500
    
    # GET: afficher le formulaire
    try:
        config = g.avatar_config
        
        if not config:
            logger.error(f"Avatar {agent_id} non trouvé")
            return jsonify({"success": False, "error": "Avatar non trouvé"}), 404
        
        return render_template(
            'avatar/avatar_step2.html',
            agent_id=agent_id,
            config_type=config.get('config_type'),
            model_id=config.get('model_id'),
            model_name=config.get('model_name'),
            model_description=config.get('model_description'),
            model_family=config.get('model_family'),
            voice_type='avatar',
            avatar_config=config
        )
        
    except Exception as e:
        logger.exception("Erreur step2 GET")
        return jsonify({"success": False, "error": str(e)}), 500

@avatar_bp.route('/step3/<agent_id>', methods=['GET', 'POST'])
def avatar_config_step3(agent_id):
    """
    Step 3: Sélection des Tools
    """
    from configuration.cosmos_config import update_avatar_config
    from flask import redirect, url_for
    
    # Validation UUID
    if not validate_uuid(agent_id):
        return jsonify({"success": False, "error": "agent_id invalide"}), 400
    
    if request.method == 'POST':
        try:
            # Récupérer uniquement les tools sélectionnés
            selected_tools = request.form.getlist('tools')
            
            tools_data = {
                'selected_tools': selected_tools,
                'current_step': 4,
                'status': 'step3_completed'
            }
            
            update_avatar_config(agent_id, tools_data)
            logger.info(f"✅ Step 3 complété pour avatar {agent_id}: {len(selected_tools)} tools")
            
            # Rediriger vers step4 (prompt)
            return redirect(url_for('avatar.avatar_config_step4', agent_id=agent_id))
            
        except Exception as e:
            logger.exception("Erreur step3 POST")
            return jsonify({"success": False, "error": str(e)}), 500
    
    # GET: afficher le formulaire
    try:
        if not g.avatar_config:
            logger.error(f"Avatar {agent_id} non trouvé")
            return jsonify({"success": False, "error": "Avatar non trouvé"}), 404
        
        return render_template(
            'avatar/avatar_step3.html',
            agent_id=agent_id,
            voice_type='avatar'
        )
        
    except Exception as e:
        logger.exception("Erreur step3 GET")
        return jsonify({"success": False, "error": str(e)}), 500


@avatar_bp.route('/step4/<agent_id>', methods=['GET', 'POST'])
def avatar_config_step4(agent_id):
    """
    Step 4: Prompt/Instructions pour avatars
    """
    from configuration.cosmos_config import update_avatar_config
    from flask import redirect, url_for
    
    # Validation UUID
    if not validate_uuid(agent_id):
        return jsonify({"success": False, "error": "agent_id invalide"}), 400
    
    if request.method == 'POST':
        try:
            system_prompt = request.form.get('system_prompt', '')
            
            prompt_data = {
                'system_prompt': system_prompt,
                'instructions': system_prompt,  # Compatibility
                'current_step': 4,
                'status': 'completed'
            }
            
            update_avatar_config(agent_id, prompt_data)
            logger.info(f"✅ Avatar {agent_id} configuration terminée")

            # Rediriger vers la galerie
            return redirect(url_for('avatar.avatar_gallery'))
            
        except Exception as e:
            logger.exception("Erreur step4 POST")
            return jsonify({"success": False, "error": str(e)}), 500
    
    # GET: afficher le formulaire
    try:
        if not g.avatar_config:
            logger.error(f"Avatar {agent_id} non trouvé")
            return jsonify({"success": False, "error": "Avatar non trouvé"}), 404
        
        return render_template(
            'avatar/avatar_step4.html',
            agent_id=agent_id,
            config=g.avatar_config,
            voice_type='avatar'
        )
        
    except Exception as e:
        logger.exception("Erreur step4 GET")
        return jsonify({"success": False, "error": str(e)}), 500


@avatar_bp.route('/api/<agent_id>/generate_prompt_stream', methods=['POST'])
def generate_prompt_stream_api(agent_id):
    """
    API endpoint pour générer un prompt système via GPT-5-mini avec streaming
    """
    from openai import OpenAI
    import os
    from flask import Response, stream_with_context
    import json
    
    try:
        data = request.get_json()
        user_instruction = data.get('user_instruction', '') or data.get('instruction', '')
        
        if not user_instruction:
            return jsonify({
                'success': False,
                'error': 'Instruction utilisateur manquante'
            }), 400
        
        # Initialiser le client OpenAI
        azure_endpoint = os.getenv('AZURE_OPENAI_SUMMARY_ENDPOINT')
        api_key = os.getenv('AZURE_OPENAI_SUMMARY_KEY')
        deployment_name = os.getenv('AZURE_OPENAI_GPT5_MINI_DEPLOYMENT', 'gpt-5-mini')
        
        if not azure_endpoint or not api_key:
            return jsonify({
                'success': False,
                'error': 'Configuration Azure OpenAI manquante'
            }), 500
        
        base_url = f"{azure_endpoint}openai/v1/"
        
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        
        # Prompt de génération (même que version non-streaming)
        generation_prompt = f"""Tu es un assistant expert en création de prompts système pour des agents IA conversationnels vocaux.

L'utilisateur souhaite créer un agent avatar avec les caractéristiques suivantes :
{user_instruction}

Génère un prompt système professionnel, détaillé et efficace pour cet agent avatar.

Le prompt DOIT obligatoirement inclure :

**1. RÔLE** :
   - Si spécifié dans la consigne → utiliser ce rôle
   - Sinon → "Agent conversationnel généraliste"

**2. TON** :
   - Par défaut → "familier et chaleureux"
   - Sauf si l'utilisateur spécifie un autre ton (professionnel, formel, etc.)

**3. PREMIER MESSAGE** :
   - Souhaiter chaleureusement la bienvenue
   - Expliquer brièvement 3 missions principales maximum
   - Mentionner qu'il peut faire des dizaines de choses au service de l'utilisateur

**4. DEMANDE DU PRÉNOM** :
   - Demander le prénom de l'utilisateur pour personnaliser la conversation
   - Ne pas insister si l'utilisateur ne veut pas le donner

**5. SALUTATIONS** :
   - Saluer uniquement dans le PREMIER message
   - Ne PAS saluer à chaque message suivant

**6. UTILISATION DES TOOLS** :
   - Quand il utilise un tool, ANNONCER à l'utilisateur ce qu'il fait
   - Répondre immédiatement avec le résultat dès réception

**7. COLLECTE D'EMAIL** :
   - Demander de l'épeler en 3 parties :
     1. Partie avant le @
     2. Partie après le @ et avant le point
     3. Partie après le point

**8. COLLECTE DE CV/INFORMATIONS** :
   - UNE seule demande par message
   - Reformuler l'information reçue
   - Puis demander l'information suivante dans le message suivant

**9. CONTEXTE CULTUREL** :
   - Si un pays est mentionné dans la consigne :
     * Lister au moins 20 expressions courantes et citations de ce pays
     * Adopter une attitude et des références culturelles du pays
     * Utiliser ces expressions MODÉRÉMENT et naturellement dans les conversations (pas à chaque phrase)
     * Varier les expressions utilisées pour maintenir la diversité

**10. FIN DE CONVERSATION** :
   - Si l'agent utilise l'outil "end_conversation"
   - NE PAS réanimer la conversation même si l'utilisateur parle après
   - La conversation est définitivement terminée

Structure le prompt en sections claires (Rôle, Ton, Comportement, Consignes spécifiques, etc.)
Fais environ 300-500 mots.

Réponds uniquement avec le prompt système, sans introduction ni explication."""

        def generate():
            try:
                # Stream avec OpenAI
                stream = client.chat.completions.create(
                    model=deployment_name,
                    messages=[
                        {"role": "system", "content": "Tu es un expert en création de prompts système pour agents IA."},
                        {"role": "user", "content": generation_prompt}
                    ],
                    temperature=1,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if delta.content:
                            # Envoyer en format SSE
                            yield f"data: {json.dumps({'content': delta.content})}\n\n"
                
                # Signal de fin
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.exception("Erreur streaming génération prompt")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        logger.exception("Erreur endpoint streaming")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@avatar_bp.route('/api/<agent_id>/generate_prompt', methods=['POST'])
def generate_prompt_api(agent_id):
    """
    API endpoint pour générer un prompt système via GPT-5-mini
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


@avatar_bp.route('/api/avatars', methods=['GET'])
def list_avatars():
    """
    Liste des avatars Azure disponibles via Azure TTS Avatar API
    Endpoint: https://{region}.tts.speech.microsoft.com/cognitiveservices/avatar/list
    """
    try:
        import os
        import requests
        
        # Récupérer les credentials Azure Speech pour Avatar
        speech_key = os.getenv('AVATAR_SPEECH_KEY') or os.getenv('AZURE_SPEECH_KEY')
        speech_region = os.getenv('AVATAR_SPEECH_REGION') or os.getenv('AZURE_SPEECH_REGION', 'eastus2')
        
        if not speech_key:
            logger.error("AVATAR_SPEECH_KEY ou AZURE_SPEECH_KEY non configurée")
            return jsonify({
                'success': False,
                'error': 'Configuration Azure Speech pour Avatar manquante'
            }), 500
        
        logger.info(f"🎭 Avatar - Région: {speech_region}")
        
        # API endpoint pour lister les avatars
        api_url = f"https://{speech_region}.tts.speech.microsoft.com/cognitiveservices/avatar/list"
        
        headers = {
            'Ocp-Apim-Subscription-Key': speech_key
        }
        
        logger.info(f"🔍 Appel API Azure Avatar: {api_url}")
        
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            avatars_data = response.json()
            
            # Transformer les données Azure en format attendu par le frontend
            avatars = []
            for avatar in avatars_data:
                avatar_info = {
                    'avatar_id': avatar.get('id', ''),
                    'avatar_name': avatar.get('name', ''),
                    'character': avatar.get('id', ''),
                    'description': avatar.get('description', f"Avatar {avatar.get('name', '')}"),
                    'styles': avatar.get('styles', []),
                    'locale': avatar.get('locale', 'en-US'),
                    'gender': avatar.get('gender', 'Unknown'),
                    'preview_url': avatar.get('thumbnailUrl', ''),
                    'video_url': avatar.get('videoUrl', ''),
                    'supported_resolutions': avatar.get('supportedResolutions', ['1920x1080', '1280x720', '960x540'])
                }
                avatars.append(avatar_info)
            
            logger.info(f"✅ {len(avatars)} avatars Azure récupérés depuis l'API")
            
            return jsonify({
                'success': True,
                'avatars': avatars,
                'total_count': len(avatars)
            })
        else:
            logger.error(f"❌ Erreur API Azure Avatar: {response.status_code} - {response.text}")
            # Fallback sur liste hardcodée si API échoue
            
        # Fallback: Liste hardcodée des avatars standards si API échoue
        fallback_avatars = [
            {
                'avatar_id': 'lisa',
                'avatar_name': 'Lisa',
                'character': 'lisa',
                'description': 'Avatar féminin professionnel avec plusieurs styles',
                'styles': ['casual-sitting', 'graceful-sitting', 'graceful-standing', 'technical-sitting', 'technical-standing'],
                'locale': 'en-US',
                'gender': 'Female',
                'preview_url': 'https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech-avatar/media/lisa-casual-sitting.png',
                'video_url': '',
                'supported_resolutions': ['1920x1080', '1280x720', '960x540']
            },
            {
                'avatar_id': 'harry',
                'avatar_name': 'Harry',
                'character': 'harry',
                'description': 'Avatar masculin professionnel',
                'styles': ['business', 'casual', 'youthful'],
                'locale': 'en-US',
                'gender': 'Male',
                'preview_url': 'https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech-avatar/media/harry-business.png',
                'video_url': '',
                'supported_resolutions': ['1920x1080', '1280x720', '960x540']
            },
            {
                'avatar_id': 'jeff',
                'avatar_name': 'Jeff',
                'character': 'jeff',
                'description': 'Avatar masculin business',
                'styles': ['business', 'formal'],
                'locale': 'en-US',
                'gender': 'Male',
                'preview_url': 'https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech-avatar/media/jeff-business.png',
                'video_url': '',
                'supported_resolutions': ['1920x1080', '1280x720', '960x540']
            },
            {
                'avatar_id': 'lori',
                'avatar_name': 'Lori',
                'character': 'lori',
                'description': 'Avatar féminin élégant',
                'styles': ['casual', 'graceful', 'formal'],
                'locale': 'en-US',
                'gender': 'Female',
                'preview_url': 'https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech-avatar/media/lori-formal.png',
                'video_url': '',
                'supported_resolutions': ['1920x1080', '1280x720', '960x540']
            },
            {
                'avatar_id': 'max',
                'avatar_name': 'Max',
                'character': 'max',
                'description': 'Avatar masculin moderne',
                'styles': ['business', 'casual', 'formal'],
                'locale': 'en-US',
                'gender': 'Male',
                'preview_url': 'https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech-avatar/media/max-business.png',
                'video_url': '',
                'supported_resolutions': ['1920x1080', '1280x720', '960x540']
            },
            {
                'avatar_id': 'meg',
                'avatar_name': 'Meg',
                'character': 'meg',
                'description': 'Avatar féminin dynamique',
                'styles': ['formal', 'casual', 'business'],
                'locale': 'en-US',
                'gender': 'Female',
                'preview_url': 'https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech-avatar/media/meg-formal.png',
                'video_url': '',
                'supported_resolutions': ['1920x1080', '1280x720', '960x540']
            }
        ]
        # Marquer les avatars expressifs et supprimer tous les conversationnels
        for avatar in fallback_avatars:
            avatar['avatar_type'] = 'expressive'
            avatar['styles'] = avatar.get('styles', [])
            avatar['supported_resolutions'] = avatar.get('supported_resolutions', ['1920x1080', '1280x720', '960x540'])
            avatar['video_url'] = ''
        
        logger.warning("⚠️ API Azure Avatar indisponible, fallback expressif uniquement")
        logger.info(f"📊 Total avatars expressifs fallback: {len(fallback_avatars)}")
        
        return jsonify({
            'success': True,
            'avatars': fallback_avatars,
            'total_count': len(fallback_avatars),
            'expressive_count': len(fallback_avatars),
            'conversational_count': 0
        })
    except Exception as e:
        logger.exception("Erreur récupération avatars")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@avatar_bp.route('/api/agents', methods=['POST'])
def create_agent_with_avatar():
    """Créer un nouvel agent avec un avatar"""
    try:
        data = request.get_json()
        
        agent_name = data.get('agent_name')
        description = data.get('description', '')
        phone_number = data.get('phone_number')
        language = data.get('language', 'fr-FR')
        system_prompt = data.get('system_prompt')
        avatar_id = data.get('avatar_id')
        avatar_name = data.get('avatar_name')
        voice_id = data.get('voice_id')
        temperature = data.get('temperature', 0.8)
        max_tokens = data.get('max_tokens', 1000)
        top_p = data.get('top_p', 0.9)
        gpt_model = data.get('gpt_model', 'gpt-4o-realtime-preview')
        
        # Validation
        if not all([agent_name, phone_number, system_prompt, avatar_id]):
            return jsonify({
                'success': False,
                'error': 'Champs obligatoires manquants'
            }), 400
        
        # Sauvegarder l'agent dans Cosmos DB avec toutes les infos
        import uuid
        from datetime import datetime
        from configuration.cosmos_config import save_avatar_config
        
        agent_id = str(uuid.uuid4())
        
        agent_config = {
            'id': agent_id,
            'agent_id': agent_id,
            'agent_name': agent_name,
            'description': description,
            'phone_number': phone_number,
            'language': language,
            'system_prompt': system_prompt,
            'voice_type': 'avatar',
            'avatar_id': avatar_id,
            'avatar_name': avatar_name,
            'voice_id': voice_id,
            'voice_config': {
                'temperature': temperature,
                'max_tokens': max_tokens,
                'top_p': top_p
            },
            'model_id': gpt_model,
            'gpt_model': gpt_model,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'status': 'active',
            'current_step': 4,
            'config_type': 'voice_live'
        }
        
        save_avatar_config(agent_config)
        logger.info(f"✅ Agent créé et sauvegardé avec avatar: {agent_id}")
        
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


@avatar_bp.route('/api/<agent_id>', methods=['DELETE'])
def delete_avatar(agent_id):
    """Supprimer un agent avatar"""
    try:
        from configuration.cosmos_config import get_avatar_container
        
        container = get_avatar_container()
        
        # Récupérer l'avatar pour avoir l'ID du document
        query = "SELECT * FROM c WHERE c.agent_id = @agent_id"
        parameters = [{"name": "@agent_id", "value": agent_id}]
        
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False,
            partition_key=agent_id
        ))
        
        if not items:
            return jsonify({
                'success': False,
                'error': 'Avatar non trouvé'
            }), 404
        
        avatar = items[0]
        
        # Supprimer le document
        container.delete_item(
            item=avatar['id'],
            partition_key=agent_id
        )
        
        logger.info(f"🗑️ Avatar supprimé: {agent_id}")
        
        return jsonify({
            'success': True,
            'message': 'Avatar supprimé avec succès'
        })
        
    except Exception as e:
        logger.exception("Erreur suppression avatar")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@avatar_bp.route('/api/<agent_id>/details', methods=['GET'])
def get_avatar_details(agent_id):
    """Récupérer les détails d'un avatar"""
    try:
        from configuration.cosmos_config import get_avatar_config
        
        avatar = get_avatar_config(agent_id)
        
        if not avatar:
            return jsonify({
                'success': False,
                'error': 'Avatar non trouvé'
            }), 404
        
        return jsonify({
            'success': True,
            'avatar': avatar
        })

    except Exception as e:
        logger.exception("Erreur récupération détails avatar")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@avatar_bp.route('/api/<agent_id>/update_avatar_character', methods=['POST'])
@avatar_bp.route('/api/<agent_id>/update', methods=['PATCH'])
def update_avatar_partial(agent_id):
    """
    Mise à jour partielle générique d'un avatar
    Supporte tous les champs de configuration avatar
    """
    try:
        from configuration.cosmos_config import update_avatar_config
        import uuid
        
        # Validation de l'UUID
        try:
            uuid.UUID(agent_id)
        except ValueError:
            return jsonify({'success': False, 'error': 'agent_id invalide'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Aucune donnée fournie'}), 400
        
        # Champs autorisés pour mise à jour
        allowed_fields = [
            'avatar_character', 'avatar_style', 'avatar_customized',
            'avatar_background_color', 'avatar_background_image',
            'voice_name', 'voice_type', 'voice_locale', 'voice_gender',
            'custom_voice_endpoint', 'speaker_profile_id',
            'agent_name', 'description', 'system_prompt',
            'temperature', 'max_tokens', 'top_p'
        ]
        
        # Filtrer uniquement les champs autorisés
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return jsonify({'success': False, 'error': 'Aucun champ valide à mettre à jour'}), 400
        
        # Mise à jour
        update_avatar_config(agent_id, update_data)
        
        logger.info(f"✅ Avatar {agent_id} mis à jour: {', '.join(update_data.keys())}")
        
        return jsonify({
            'success': True,
            'updated_fields': list(update_data.keys()),
            'message': f'{len(update_data)} champ(s) mis à jour'
        })
        
    except ValueError as e:
        logger.error(f"Erreur validation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        logger.exception("Erreur mise à jour avatar")
        return jsonify({'success': False, 'error': str(e)}), 500


@avatar_bp.route('/call/<agent_id>', methods=['GET'])
def call_avatar(agent_id):
    """
    Endpoint pour lancer une session avatar avec un agent spécifique
    Charge la configuration de l'avatar depuis Cosmos DB et initialise la session
    """
    try:
        from flask import session
        from configuration.cosmos_config import get_avatar_config
        from configuration.voice_live_config import VoiceLiveClient
        from tools import get_tools_definition
        
        # 🔄 FORCE REFRESH: Vider la session Flask pour forcer le rechargement
        session.pop('active_agent_id', None)
        session.pop('active_agent_config', None)
        
        # Récupérer la configuration de l'avatar depuis Cosmos DB
        avatar_config = get_avatar_config(agent_id)
        
        if not avatar_config:
            logger.error(f"❌ Avatar {agent_id} non trouvé")
            return jsonify({
                'success': False,
                'error': f'Avatar {agent_id} non trouvé'
            }), 404
        
        # Vérifier que l'avatar est configuré (au moins step 4 complété)
        status = avatar_config.get('status', '')
        current_step = avatar_config.get('current_step', 0)
        
        if current_step < 4 and 'step4' not in status and status not in ['deployed', 'actif', 'active']:
            logger.warning(f"⚠️ Avatar {agent_id} n'est pas complètement configuré (étape {current_step}/4)")
            return jsonify({
                'success': False,
                'error': 'Avatar non configuré. Veuillez compléter la configuration.',
                'current_step': current_step
            }), 400
        
        # Extraire les paramètres de configuration
        model_id = avatar_config.get('model_id', 'gpt-4o-realtime-preview')
        
        # Récupérer les credentials Azure Speech
        speech_key = os.getenv('AVATAR_SPEECH_KEY') or os.getenv('AZURE_SPEECH_KEY')
        speech_region = os.getenv('AVATAR_SPEECH_REGION') or os.getenv('AZURE_SPEECH_REGION', 'eastus2')
        
        if not speech_key:
            logger.error("AVATAR_SPEECH_KEY ou AZURE_SPEECH_KEY non configurée")
            return jsonify({
                'success': False,
                'error': 'Clé Azure Speech manquante'
            }), 500
        
        # Initialiser le client Voice Live
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
        voice_name = avatar_config.get('voice_name', 'fr-FR-DeniseNeural')
        voice_type = avatar_config.get('voice_type', 'personal')
        
        # Utiliser le prompt système sauvegardé
        system_instructions = avatar_config.get('system_prompt') or avatar_config.get('instructions', '')
        
        if not system_instructions:
            system_instructions = """Vous êtes un assistant avatar intelligent et serviable.
Aidez l'utilisateur de manière professionnelle et efficace."""
        
        # Préparer les outils sélectionnés
        selected_tools = avatar_config.get('selected_tools', [])
        logger.info(f"🔧 Tools sélectionnés dans la config: {selected_tools}")
        
        tools_definitions = []
        if selected_tools:
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
                'calculator': 'calculate'
            }
            
            mapped_tool_names = [TOOL_NAME_MAPPING.get(tool, tool) for tool in selected_tools]
            logger.info(f"🔧 Tools mappés: {mapped_tool_names}")
            
            all_tools = get_tools_definition()
            logger.info(f"🔧 Nombre total de tools disponibles: {len(all_tools)}")
            
            tools_definitions = [tool for tool in all_tools if tool.get('name') in mapped_tool_names]
            logger.info(f"🔧 Tools définitions trouvées: {len(tools_definitions)}")
            
            if len(tools_definitions) == 0 and len(selected_tools) > 0:
                logger.warning(f"⚠️ Aucun tool trouvé pour: {mapped_tool_names}")
        else:
            logger.info("🔧 Aucun outil sélectionné")
        
        # Configuration avatar spécifique
        avatar_character = avatar_config.get('avatar_character') or 'lisa'
        avatar_style = avatar_config.get('avatar_style') or 'casual-sitting'
        avatar_customized = avatar_config.get('avatar_customized', False)
        avatar_background_color = avatar_config.get('avatar_background_color') or '#FFFFFF'
        avatar_background_image = avatar_config.get('avatar_background_image', '')
        
        # Log pour debug
        logger.info(f"🎭 Avatar character depuis DB: {avatar_config.get('avatar_character')} -> utilise: {avatar_character}")
        logger.info(f"🎭 Avatar style depuis DB: {avatar_config.get('avatar_style')} -> utilise: {avatar_style}")
        
        # Déterminer le crop selon le personnage
        crop_top_left = [560, 0]
        crop_bottom_right = [1360, 1080]
        
        if avatar_character == 'lisa':
            crop_top_left = [560, 0]
            crop_bottom_right = [1360, 1080]
        elif avatar_style == 'casual-sitting':
            crop_top_left = [0, 0]
            crop_bottom_right = [800, 1080]
        
        # Stocker la config dans la session Flask
        session['active_agent_id'] = agent_id
        session['active_agent_config'] = {
            'agent_id': agent_id,
            'agent_name': avatar_config.get('agent_name', 'Avatar'),
            'role': avatar_config.get('role', ''),
            'model_id': model_id,
            'model_name': avatar_config.get('model_name', model_id),
            'websocket_url': websocket_url,
            'modalities': avatar_config.get('modalities', ['text', 'audio']),
            'voice': {
                'name': voice_name,
                'type': voice_type,
                'rate': '1.0',
                'temperature': 0.7
            },
            'instructions': system_instructions,
            'tools': tools_definitions,
            'temperature': avatar_config.get('temperature', 0.7),
            'max_tokens': avatar_config.get('max_tokens', 4096),
            'avatar_enabled': True,
            'avatar_config': {
                'character': avatar_character,
                'style': avatar_style,
                'customized': avatar_customized,
                'background_color': avatar_background_color,
                'background_image': avatar_background_image,
                'video': {
                    'codec': 'h264',
                    'bitrate': 2000000,
                    'resolution': {
                        'width': 1920,
                        'height': 1080
                    },
                    'crop': {
                        'top_left': crop_top_left,
                        'bottom_right': crop_bottom_right
                    }
                },
                'ice_servers': [
                    {'urls': ['stun:stun.l.google.com:19302']}
                ]
            },
            'speech_key': speech_key,
            'speech_region': speech_region
        }
        
        logger.info(f"✅ Session Avatar initialisée pour l'agent {agent_id} ({avatar_config.get('agent_name')})")
        logger.info(f"   Modèle: {model_id}")
        logger.info(f"   Voix: {voice_name}")
        logger.info(f"   Avatar: {avatar_character} - {avatar_style}")
        logger.info(f"   Outils: {len(tools_definitions)} activés")

        # Cache buster pour forcer le rechargement du JavaScript
        import time
        cache_buster = int(time.time())

        # Rendre la page de session Avatar
        return render_template(
            'avatar/avatar_voice_session.html',
            agent=session['active_agent_config'],
            cache_buster=cache_buster
        )
        
    except Exception as e:
        logger.exception(f"❌ Erreur lors de l'appel de l'avatar {agent_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur lors de l\'initialisation de l\'avatar'
        }), 500


logger.info("✅ Blueprint Avatar enregistré")
