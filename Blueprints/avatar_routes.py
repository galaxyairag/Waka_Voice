"""
Blueprint pour la gestion des avatars Azure AI
"""
from flask import Blueprint, render_template, request, jsonify
import logging
import os

logger = logging.getLogger(__name__)

avatar_bp = Blueprint('avatar', __name__, url_prefix='/avatar')

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
    from configuration.cosmos_config import get_avatar_config, update_avatar_config
    from flask import redirect, url_for
    
    if request.method == 'POST':
        try:
            # Données de configuration voix uniquement
            voice_data = {
                'voice_type': request.form.get('voice_type', 'personal'),
                'voice_name': request.form.get('voice_name'),
                'custom_voice_endpoint': request.form.get('custom_voice_endpoint'),
                'speaker_profile_id': request.form.get('speaker_profile_id'),
                'voice_locale': request.form.get('voice_locale'),
                'voice_gender': request.form.get('voice_gender'),
                'current_step': 3,
                'status': 'step2_completed'
            }
            
            # Nettoyer les valeurs vides
            voice_data = {k: v for k, v in voice_data.items() if v not in [None, '']}
            
            # Préserver les champs avatar déjà configurés (via API AJAX)
            existing_config = get_avatar_config(agent_id)
            if existing_config:
                for field in ['avatar_character', 'avatar_style', 'avatar_background_image', 'avatar_background_color', 'avatar_customized']:
                    if field in existing_config and existing_config[field]:
                        voice_data[field] = existing_config[field]
            
            # Sauvegarder
            update_avatar_config(agent_id, voice_data)
            logger.info(f"✅ Step 2 complété pour avatar {agent_id}")
            
            return redirect(url_for('avatar.avatar_config_step3', agent_id=agent_id))
            
        except Exception as e:
            logger.exception("Erreur step2 POST")
            return jsonify({"success": False, "error": str(e)}), 500
    
    # GET: afficher le formulaire
    try:
        config = get_avatar_config(agent_id)
        
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
            voice_type='avatar'
        )
        
    except Exception as e:
        logger.exception("Erreur step2 GET")
        return jsonify({"success": False, "error": str(e)}), 500

@avatar_bp.route('/step3/<agent_id>', methods=['GET', 'POST'])
def avatar_config_step3(agent_id):
    """
    Step 3: Sélection des Tools
    """
    from configuration.cosmos_config import get_avatar_config, update_avatar_config
    from flask import redirect, url_for
    
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
        config = get_avatar_config(agent_id)
        
        if not config:
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
    if request.method == 'GET':
        try:
            # Récupérer la config depuis Cosmos DB
            from configuration.cosmos_config import get_avatar_config
            config = get_avatar_config(agent_id)
            
            if not config:
                config = {
                    'agent_id': agent_id,
                    'voice_type': 'avatar'
                }
            
            logger.info(f"📄 Rendu Step 4 (Prompt) pour avatar (agent: {agent_id})")
            
            return render_template(
                'avatar/avatar_step4.html',
                agent_id=agent_id,
                config=config,
                voice_type='avatar'
            )
            
        except Exception as e:
            logger.exception("Erreur dans avatar_config_step4 GET")
            return jsonify({"success": False, "error": str(e)}), 500
    
    else:  # POST - soumission finale du prompt
        try:
            from configuration.cosmos_config import update_avatar_config
            from flask import redirect, url_for
            
            system_prompt = request.form.get('system_prompt', '')
            
            prompt_data = {
                'system_prompt': system_prompt,
                'instructions': system_prompt,  # Compatibility
                'current_step': 4,  # Configuration terminée (4 étapes)
                'status': 'completed'
            }
            
            update_avatar_config(agent_id, prompt_data)
            logger.info(f"✅ Prompt final sauvegardé pour avatar {agent_id}, configuration terminée (4/4)")

            # Rediriger vers la galerie des avatars
            return redirect(url_for('avatar.avatar_gallery'))
            
        except Exception as e:
            logger.exception("Erreur dans avatar_config_step4 POST")
            return jsonify({"success": False, "error": str(e)}), 500


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
        
        # Créer le prompt pour générer le system prompt
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

        tools_section = """

## 🛠️ OUTILS DISPONIBLES - DÉFINITIONS COMPLÈTES

IMPORTANT: Ces outils sont déjà configurés et prêts à être appelés. Utilise-les ACTIVEMENT!

### 📋 RÈGLES IMPÉRATIVES

1. ✅ **Annonce** avant d'appeler: "Je vérifie...", "J'envoie...", "Je cherche..."
2. ✅ **Appelle IMMÉDIATEMENT** dès que tu as les infos nécessaires
3. ✅ **Réponds avec le résultat** dès réception
4. ❌ **NE propose JAMAIS** - AGIS directement!

---

### 🌟 OUTILS PRIORITAIRES (Utilise-les en premier!)

"""

        # Liste des tools prioritaires avec documentation complète
        priority_tools = {
            "get_weather_forecast": {
                "emoji": "🌤️",
                "usage": "Dès que météo/temps/température mentionné",
                "params": "city (ville), country (pays, optionnel), days (1-5 jours)"
            },
            "send_email": {
                "emoji": "📧",
                "usage": "Envoi d'email/mail/courriel",
                "params": "to (destinataire), subject (sujet), body (message)"
            },
            "create_cv": {
                "emoji": "📄",
                "usage": "Créer/enregistrer CV/candidature",
                "params": "name, email, phone, experience, education, skills"
            },
            "end_conversation": {
                "emoji": "👋",
                "usage": "Au revoir/fin/partir - Termine la conversation",
                "params": "reason (motif de fin)"
            },
            "search_web": {
                "emoji": "🔍",
                "usage": "Recherche générale/Google/infos actuelles",
                "params": "query (recherche)"
            },
            "convert_currency": {
                "emoji": "💱",
                "usage": "Conversion monétaire/devises",
                "params": "amount, from_currency, to_currency"
            },
            "translate_text": {
                "emoji": "🌐",
                "usage": "Traduction de texte",
                "params": "text, source_lang, target_lang"
            },
            "calculate": {
                "emoji": "🧮",
                "usage": "Calculs mathématiques",
                "params": "expression (ex: '2+2', '10*5')"
            }
        }

        for tool in all_tools:
            tool_name = tool.get("name", "")
            if tool_name in priority_tools:
                info = priority_tools[tool_name]
                tools_section += f"""
#### {info['emoji']} **{tool_name}**
- **Utilisation**: {info['usage']}
- **Paramètres**: {info['params']}
- **Appel JSON**:
```json
{{
  "type": "function",
  "name": "{tool_name}",
  "parameters": {{ ... }}
}}
```

"""

        tools_section += """
---

### 🔧 TOUS LES OUTILS DISPONIBLES

"""

        # Lister TOUS les tools avec leur nom et description courte
        for tool in all_tools:
            tool_name = tool.get("name", "")
            description = tool.get("description", "").split('\n')[0].strip()[:80]
            tools_section += f"- **{tool_name}**: {description}...\n"

        tools_section += """

---

### 💡 EXEMPLES CONCRETS

**✅ EXCELLENT**:
User: "Quel temps à Paris?"
Agent: "Je vérifie la météo..." [APPELLE get_weather_forecast{"city":"Paris"}]
→ "Il fait 18°C, ciel dégagé!"

**❌ MAUVAIS**:
Agent: "Voulez-vous que je vérifie?" → NON! Appelle directement!

**✅ EXCELLENT**:
User: "Traduis bonjour en anglais"
Agent: "Je traduis..." [APPELLE translate_text{"text":"bonjour","target_lang":"en"}]
→ "Traduction: Hello"

**✅ EXCELLENT**:
User: "Combien font 15 fois 7?"
Agent: "Je calcule..." [APPELLE calculate{"expression":"15*7"}]
→ "15 × 7 = 105"

---

### ⚡ RAPPELS IMPORTANTS

1. Les tools sont DÉJÀ configurés - appelle-les directement!
2. Collecte les infos manquantes PUIS appelle immédiatement
3. Pour email: demande to, subject, body PUIS envoie
4. Pour météo: appelle dès que tu as la ville
5. Pour end_conversation: appelle dès "au revoir"
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
    Liste des avatars Azure disponibles via Azure AI Avatar API
    Retourne tous les avatars pré-construits disponibles pour TTS Avatar
    """
    try:
        import os
        import requests
        
        # Récupérer les credentials Azure Speech pour Avatar
        # Priorité aux variables spécifiques AVATAR, sinon fallback sur AZURE_SPEECH
        speech_key = os.getenv('AVATAR_SPEECH_KEY') or os.getenv('AZURE_SPEECH_KEY')
        speech_region = os.getenv('AVATAR_SPEECH_REGION') or os.getenv('AZURE_SPEECH_REGION', 'eastus2')
        
        if not speech_key:
            logger.error("AVATAR_SPEECH_KEY ou AZURE_SPEECH_KEY non configurée")
            return jsonify({
                'success': False,
                'error': 'Configuration Azure Speech pour Avatar manquante'
            }), 500
        
        logger.info(f"🎭 Avatar - Région: {speech_region}")
        
        # URL de l'API Azure Avatar
        # https://learn.microsoft.com/azure/ai-services/speech-service/text-to-speech-avatar/avatar-gestures-with-ssml
        api_url = f"https://{speech_region}.api.cognitive.microsoft.com/avatar/prebuilt/v1/models"
        
        headers = {
            'Ocp-Apim-Subscription-Key': speech_key,
            'Content-Type': 'application/json'
        }
        
        logger.info(f"🔍 Appel API Azure Avatar: {api_url}")
        
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Transformer les données Azure en format attendu par le frontend
        avatars = []
        for avatar in data.get('value', []):
            properties = avatar.get('properties', {})
            avatar_info = {
                'avatar_id': avatar.get('id', ''),
                'avatar_name': avatar.get('name', ''),
                'character': avatar.get('character', ''),
                'description': avatar.get('description', ''),
                'styles': avatar.get('styles', []),
                'locale': avatar.get('locale', 'en-US'),
                'gender': properties.get('gender', 'Unknown'),
                'preview_url': properties.get('previewImageUrl', properties.get('thumbnailUrl', '')),
                'video_url': properties.get('previewVideoUrl', properties.get('videoUrl', '')),
                'supported_resolutions': properties.get('supportedResolutions', ['1920x1080', '1280x720', '960x540'])
            }
            avatars.append(avatar_info)
        
        logger.info(f"✅ {len(avatars)} avatars Azure trouvés")
        
        return jsonify({
            'success': True,
            'avatars': avatars,
            'total_count': len(avatars)
        })
        
    except requests.exceptions.RequestException as e:
        logger.exception(f"Erreur appel API Azure Avatar: {str(e)}")
        # Fallback sur des avatars standards avec vraies images de la documentation Microsoft
        # URLs basées sur https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech-avatar/standard-avatars
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
        # Ajouter les avatars conversationnels (photo avatars)
        # Base URL pour les images de la documentation Microsoft
        base_url = 'https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech-avatar/media'
        
        conversational_avatars = [
            {'avatar_id': 'adrian', 'avatar_name': 'Adrian', 'character': 'adrian', 'description': 'Avatar conversationnel professionnel', 'locale': 'en-US', 'gender': 'Male', 'preview_url': f'{base_url}/adrian.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'amara', 'avatar_name': 'Amara', 'character': 'amara', 'description': 'Avatar conversationnel féminin', 'locale': 'en-US', 'gender': 'Female', 'preview_url': f'{base_url}/amara.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'amira', 'avatar_name': 'Amira', 'character': 'amira', 'description': 'Avatar conversationnel élégant', 'locale': 'en-US', 'gender': 'Female', 'preview_url': f'{base_url}/amira-avatar.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'anika', 'avatar_name': 'Anika', 'character': 'anika', 'description': 'Avatar conversationnel moderne', 'locale': 'en-US', 'gender': 'Female', 'preview_url': f'{base_url}/anika-avatar.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'bianca', 'avatar_name': 'Bianca', 'character': 'bianca', 'description': 'Avatar conversationnel dynamique', 'locale': 'en-US', 'gender': 'Female', 'preview_url': f'{base_url}/bianca.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'camila', 'avatar_name': 'Camila', 'character': 'camila', 'description': 'Avatar conversationnel amical', 'locale': 'en-US', 'gender': 'Female', 'preview_url': f'{base_url}/camila.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'carlos', 'avatar_name': 'Carlos', 'character': 'carlos', 'description': 'Avatar conversationnel confiant', 'locale': 'en-US', 'gender': 'Male', 'preview_url': f'{base_url}/carlos.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'clara', 'avatar_name': 'Clara', 'character': 'clara', 'description': 'Avatar conversationnel professionnel', 'locale': 'en-US', 'gender': 'Female', 'preview_url': f'{base_url}/clara.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'darius', 'avatar_name': 'Darius', 'character': 'darius', 'description': 'Avatar conversationnel charismatique', 'locale': 'en-US', 'gender': 'Male', 'preview_url': f'{base_url}/darius.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'diego', 'avatar_name': 'Diego', 'character': 'diego', 'description': 'Avatar conversationnel engageant', 'locale': 'en-US', 'gender': 'Male', 'preview_url': f'{base_url}/diego.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'elise', 'avatar_name': 'Elise', 'character': 'elise', 'description': 'Avatar conversationnel sophistiqué', 'locale': 'en-US', 'gender': 'Female', 'preview_url': f'{base_url}/elise.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'farhan', 'avatar_name': 'Farhan', 'character': 'farhan', 'description': 'Avatar conversationnel chaleureux', 'locale': 'en-US', 'gender': 'Male', 'preview_url': f'{base_url}/farhan-avatar.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'faris', 'avatar_name': 'Faris', 'character': 'faris', 'description': 'Avatar conversationnel cordial', 'locale': 'en-US', 'gender': 'Male', 'preview_url': f'{base_url}/faris-avatar.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'gabrielle', 'avatar_name': 'Gabrielle', 'character': 'gabrielle', 'description': 'Avatar conversationnel expressif', 'locale': 'en-US', 'gender': 'Female', 'preview_url': f'{base_url}/gabrielle.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'hyejin', 'avatar_name': 'Hyejin', 'character': 'hyejin', 'description': 'Avatar conversationnel souriant', 'locale': 'en-US', 'gender': 'Female', 'preview_url': f'{base_url}/hyejin-avatar.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'imran', 'avatar_name': 'Imran', 'character': 'imran', 'description': 'Avatar conversationnel sympathique', 'locale': 'en-US', 'gender': 'Male', 'preview_url': f'{base_url}/imran-avatar.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'isabella', 'avatar_name': 'Isabella', 'character': 'isabella', 'description': 'Avatar conversationnel élégant', 'locale': 'en-US', 'gender': 'Female', 'preview_url': f'{base_url}/isabella.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'layla', 'avatar_name': 'Layla', 'character': 'layla', 'description': 'Avatar conversationnel accueillant', 'locale': 'en-US', 'gender': 'Female', 'preview_url': f'{base_url}/layla.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'liwei', 'avatar_name': 'Liwei', 'character': 'liwei', 'description': 'Avatar conversationnel professionnel', 'locale': 'en-US', 'gender': 'Male', 'preview_url': f'{base_url}/liwei-avatar.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'ling', 'avatar_name': 'Ling', 'character': 'ling', 'description': 'Avatar conversationnel moderne', 'locale': 'en-US', 'gender': 'Female', 'preview_url': f'{base_url}/ling.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'marcus', 'avatar_name': 'Marcus', 'character': 'marcus', 'description': 'Avatar conversationnel confiant', 'locale': 'en-US', 'gender': 'Male', 'preview_url': f'{base_url}/marcus.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'matteo', 'avatar_name': 'Matteo', 'character': 'matteo', 'description': 'Avatar conversationnel dynamique', 'locale': 'en-US', 'gender': 'Male', 'preview_url': f'{base_url}/matteo.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'rahul', 'avatar_name': 'Rahul', 'character': 'rahul', 'description': 'Avatar conversationnel amical', 'locale': 'en-US', 'gender': 'Male', 'preview_url': f'{base_url}/rahul-avatar.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'rana', 'avatar_name': 'Rana', 'character': 'rana', 'description': 'Avatar conversationnel chaleureux', 'locale': 'en-US', 'gender': 'Female', 'preview_url': f'{base_url}/rana.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'ren', 'avatar_name': 'Ren', 'character': 'ren', 'description': 'Avatar conversationnel engageant', 'locale': 'en-US', 'gender': 'Male', 'preview_url': f'{base_url}/ren-avatar.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'riya', 'avatar_name': 'Riya', 'character': 'riya', 'description': 'Avatar conversationnel souriant', 'locale': 'en-US', 'gender': 'Female', 'preview_url': f'{base_url}/riya-avatar.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'sakura', 'avatar_name': 'Sakura', 'character': 'sakura', 'description': 'Avatar conversationnel élégant', 'locale': 'en-US', 'gender': 'Female', 'preview_url': f'{base_url}/sakura-avatar.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'simone', 'avatar_name': 'Simone', 'character': 'simone', 'description': 'Avatar conversationnel professionnel', 'locale': 'en-US', 'gender': 'Female', 'preview_url': f'{base_url}/simone.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'zayd', 'avatar_name': 'Zayd', 'character': 'zayd', 'description': 'Avatar conversationnel confiant', 'locale': 'en-US', 'gender': 'Male', 'preview_url': f'{base_url}/zayd-avatar.png', 'avatar_type': 'conversational'},
            {'avatar_id': 'zoe', 'avatar_name': 'Zoe', 'character': 'zoe', 'description': 'Avatar conversationnel dynamique', 'locale': 'en-US', 'gender': 'Female', 'preview_url': f'{base_url}/zoe.png', 'avatar_type': 'conversational'}
        ]
        
        # Marquer les avatars expressifs
        for avatar in fallback_avatars:
            avatar['avatar_type'] = 'expressive'
            avatar['styles'] = avatar.get('styles', [])
            avatar['supported_resolutions'] = avatar.get('supported_resolutions', ['1920x1080', '1280x720', '960x540'])
            avatar['video_url'] = ''
        
        # Ajouter les champs nécessaires aux avatars conversationnels
        for avatar in conversational_avatars:
            avatar['styles'] = []  # Pas de styles pour les avatars conversationnels
            avatar['supported_resolutions'] = ['1920x1080', '1280x720', '960x540']
            avatar['video_url'] = ''
        
        all_avatars = fallback_avatars + conversational_avatars
        
        logger.warning(f"⚠️ Utilisation des avatars fallback (erreur API: {str(e)})")
        logger.info(f"📊 Total avatars: {len(all_avatars)} (6 expressifs + 30 conversationnels)")
        
        return jsonify({
            'success': True,
            'avatars': all_avatars,
            'total_count': len(all_avatars),
            'expressive_count': len(fallback_avatars),
            'conversational_count': len(conversational_avatars),
            'source': 'fallback'
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
def update_avatar_character(agent_id):
    """Mettre à jour le character et le style de l'avatar directement"""
    try:
        from configuration.cosmos_config import update_avatar_config, get_avatar_config

        data = request.get_json()
        character = data.get('character')
        style = data.get('style')

        logger.info(f"🔄 API update_avatar_character appelée - agent_id: {agent_id}")
        logger.info(f"📦 Données reçues: character={character}, style={style}")

        if not character:
            logger.warning("⚠️ Character manquant dans la requête")
            return jsonify({
                'success': False,
                'error': 'Character requis'
            }), 400

        # Mettre à jour dans Cosmos DB
        update_data = {
            'avatar_character': character
        }

        if style:
            update_data['avatar_style'] = style

        logger.info(f"📝 Données à mettre à jour dans Cosmos: {update_data}")

        # Mettre à jour
        update_avatar_config(agent_id, update_data)

        # Vérifier que la mise à jour a bien été effectuée
        updated_config = get_avatar_config(agent_id)
        actual_character = updated_config.get('avatar_character') if updated_config else None

        logger.info(f"✅ Avatar character mis à jour pour {agent_id}: {character} (style: {style})")
        logger.info(f"🔍 Vérification après mise à jour - avatar_character dans DB: {actual_character}")

        return jsonify({
            'success': True,
            'message': f'Avatar character mis à jour: {character}',
            'character': character,
            'style': style,
            'verified_character': actual_character  # Pour vérifier
        })

    except Exception as e:
        logger.exception("❌ Erreur mise à jour avatar character")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@avatar_bp.route('/call/<agent_id>', methods=['GET'])
def call_avatar(agent_id):
    """
    Endpoint pour lancer une session avatar avec un agent spécifique
    Charge la configuration de l'avatar depuis Cosmos DB et initialise la session
    """
    try:
        from flask import session, redirect, url_for
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
