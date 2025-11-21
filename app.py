#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===================================================================
Application Flask - Configuration Voice Live Agents
===================================================================
Auteur: Waka AI
Date: 15 novembre 2025
Description: Application complète pour créer et configurer des agents Voice Live
===================================================================
"""

from flask import Flask, render_template, redirect, url_for, session, jsonify, request
import os
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# ===================================================================
# CONFIGURATION DE L'APPLICATION
# ===================================================================

app = Flask(__name__)

# Configuration de base
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
app.config['HOST'] = os.getenv('FLASK_HOST', '0.0.0.0')
app.config['PORT'] = int(os.getenv('FLASK_PORT', 8080))

# Configuration de la session (CRITIQUE pour le flux multi-étapes)
# On utilise la session intégrée de Flask (cookie signé), sans Flask-Session
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-CHANGE-IN-PRODUCTION-123456789')
app.config['SESSION_PERMANENT'] = False

# Configuration Azure Speech Service
app.config['AZURE_SPEECH_KEY'] = os.getenv('AZURE_SPEECH_KEY')
app.config['AZURE_SPEECH_REGION'] = os.getenv('AZURE_SPEECH_REGION', 'westus')

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

"""Session Flask intégrée utilisée (pas de Flask-Session filesystem)."""

# ===================================================================
# INITIALISATION DES SERVICES
# ===================================================================

# Initialiser CosmosDB au démarrage
try:
    import configuration
    logger.info("✅ Module Configuration (CosmosDB) initialisé")
except Exception as e:
    logger.warning(f"⚠️ CosmosDB non disponible: {e}")
    logger.warning("L'application fonctionnera sans persistance")

# ===================================================================
# ENREGISTREMENT DES BLUEPRINTS
# ===================================================================

# Importer les blueprints
try:
    from Blueprints.agents_config_routes import agents_config_bp
    from Blueprints.azure_voices_api import init_app as init_azure_voices
    from Blueprints.conversation_history_routes import conversation_history_bp
    from Blueprints.quality_dashboard_routes import quality_bp, quality_pages_bp
    from Blueprints.production_dashboard_routes import production_bp, production_pages_bp
    from Blueprints.personal_voice_routes import personal_voice_bp
    from Blueprints.avatar_routes import avatar_bp
    from Blueprints.background_upload_routes import background_bp
    
    # Enregistrer les blueprints
    logger.info(f"🔧 Enregistrement de agents_config_bp: {agents_config_bp}, name={agents_config_bp.name}, url_prefix={agents_config_bp.url_prefix}")
    app.register_blueprint(agents_config_bp)
    logger.info("✅ agents_config_bp enregistré")
    
    init_azure_voices(app)
    app.register_blueprint(conversation_history_bp)
    app.register_blueprint(quality_bp)
    app.register_blueprint(quality_pages_bp)
    app.register_blueprint(production_bp)
    app.register_blueprint(production_pages_bp)
    app.register_blueprint(personal_voice_bp)
    app.register_blueprint(avatar_bp)
    app.register_blueprint(background_bp)
    
    logger.info("✅ Tous les blueprints ont été enregistrés avec succès")

    # ⚡ WARMUP: Pré-charger les tools au démarrage pour éviter timeout sur /avatar/call
    try:
        from tools import warmup_tools
        if warmup_tools():
            logger.info("✅ Tools pré-chargés avec succès (warmup)")
        else:
            logger.warning("⚠️ Échec du warmup des tools")
    except Exception as warmup_err:
        logger.warning(f"⚠️ Erreur warmup tools: {warmup_err}")

except ImportError as e:
    logger.error(f"❌ Erreur lors de l'import des blueprints: {str(e)}")
    logger.error("Assurez-vous que les fichiers suivants existent:")
    logger.error("  - Blueprints/agents_config_routes.py")
    logger.error("  - Blueprints/azure_voices_api.py")
    logger.error("  - Blueprints/__init__.py")
except Exception as e:
    logger.error(f"❌ ERREUR INATTENDUE lors du chargement des blueprints: {type(e).__name__}: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())

# ===================================================================
# ROUTES DE BASE
# ===================================================================

@app.route('/')
def index():
    """
    Page d'accueil - Affiche la page de bienvenue
    """
    return render_template('home.html')

@app.route('/home')
def home():
    """
    Page de bienvenue avec date et heure
    """
    return render_template('home.html')

@app.route('/warmup')
def warmup():
    """
    Endpoint de warmup pour Azure App Service.
    Pré-charge les modules lourds pour éviter les timeouts.
    """
    try:
        from tools import warmup_tools, get_tools_definition
        from configuration.cosmos_config import get_avatar_container

        # Warmup des tools
        tools_ok = warmup_tools()
        tools_count = len(get_tools_definition())

        # Test connexion Cosmos DB
        try:
            get_avatar_container()
            cosmos_ok = True
        except Exception:
            cosmos_ok = False

        return jsonify({
            'success': True,
            'status': 'warmed_up',
            'tools_loaded': tools_ok,
            'tools_count': tools_count,
            'cosmos_connected': cosmos_ok
        })
    except Exception as e:
        logger.exception("Erreur warmup")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/debug/env-check')
def debug_env_check():
    """
    Diagnostic des variables d'environnement pour avatar.
    À SUPPRIMER en production !
    """
    import os

    def check_var(name):
        val = os.getenv(name)
        if val:
            return f"✅ SET ({len(val)} chars)"
        return "❌ NOT SET"

    return jsonify({
        'avatar_vars': {
            'AVATAR_SPEECH_KEY': check_var('AVATAR_SPEECH_KEY'),
            'AVATAR_SPEECH_REGION': check_var('AVATAR_SPEECH_REGION'),
        },
        'azure_vars': {
            'AZURE_SPEECH_KEY': check_var('AZURE_SPEECH_KEY'),
            'AZURE_SPEECH_REGION': check_var('AZURE_SPEECH_REGION'),
            'AZURE_SPEECH_ENDPOINT': check_var('AZURE_SPEECH_ENDPOINT'),
        },
        'voice_live_vars': {
            'VOICE_LIVE_KEY': check_var('VOICE_LIVE_KEY'),
            'VOICE_LIVE_NAME': check_var('VOICE_LIVE_NAME'),
            'VOICE_LIVE_ENDPOINT': check_var('VOICE_LIVE_ENDPOINT'),
        },
        'cosmos_vars': {
            'COSMOS_ENDPOINT': check_var('COSMOS_ENDPOINT'),
            'COSMOS_KEY': check_var('COSMOS_KEY'),
        }
    })


@app.route('/debug/routes')
def debug_routes():
    """
    Route de débogage - Liste toutes les routes enregistrées
    """
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
            'path': str(rule)
        })
    routes_sorted = sorted(routes, key=lambda x: x['path'])
    html = "<h1>Routes enregistrées</h1><table border='1'><tr><th>Path</th><th>Endpoint</th><th>Methods</th></tr>"
    for route in routes_sorted:
        html += f"<tr><td>{route['path']}</td><td>{route['endpoint']}</td><td>{route['methods']}</td></tr>"
    html += "</table>"
    return html

@app.route('/quality')
def quality_dashboard():
    """
    Dashboard qualité avec analyses approfondies
    """
    return render_template('quality_dashboard.html')


@app.route('/api/dashboard/summary')
def dashboard_summary():
    """API JSON pour le dashboard d'accueil (KPI quotidiens + sparklines).

    Toutes les valeurs sont calculées pour la journée courante (UTC) côté Cosmos.
    """
    try:
        from configuration.cosmos_config import get_daily_dashboard_metrics

        metrics = get_daily_dashboard_metrics()
        return jsonify({
            "success": True,
            "data": metrics
        })
    except Exception as e:
        logger.exception("❌ Erreur lors du calcul des KPI dashboard")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/agents')
def agents_list():
    """
    Page de liste des agents créés avec pagination et filtres
    """
    try:
        from configuration.cosmos_config import list_agents_by_status
        from flask import request
        
        # Récupérer les paramètres de filtrage
        status_filter = request.args.get('status', None)
        model_filter = request.args.get('model', None)
        date_from = request.args.get('date_from', None)
        date_to = request.args.get('date_to', None)
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        
        # Récupérer les agents avec pagination et filtres
        result = list_agents_by_status(
            status=status_filter,
            model_filter=model_filter,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size
        )
        
        logger.info(f"✅ {result['total']} agent(s) total - Page {result['page']}/{result['total_pages']}")
        
        # Extraire les modèles uniques pour le filtre
        unique_models = set()
        for agents_list in result['grouped_by_status'].values():
            for agent in agents_list:
                model_name = agent.get('model_name') or agent.get('model_id')
                if model_name:
                    unique_models.add(model_name)
        
        return render_template(
            'agents.html',
            agents=result['agents'],
            total=result['total'],
            page=result['page'],
            page_size=result['page_size'],
            total_pages=result['total_pages'],
            grouped_by_status=result['grouped_by_status'],
            unique_models=sorted(unique_models),
            current_filters={
                'status': status_filter,
                'model': model_filter,
                'date_from': date_from,
                'date_to': date_to
            }
        )
        
    except Exception as e:
        logger.exception("❌ Erreur lors de la liste des agents")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/avatars')
def avatars_list():
    """
    Redirection vers la nouvelle galerie d'avatars
    """
    from flask import redirect, url_for
    return redirect(url_for('avatar.avatar_gallery'))

@app.route('/agents/config', methods=['GET'])
def agents_config():
    """Route de configuration des agents"""
    from flask import redirect, url_for
    return redirect(url_for('agents_manager.agent_config_step1'))

def safe_int(value, default=0):
    if value is None or value == '' or value == 'null':
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    if value is None or value == '' or value == 'null':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
    
@app.route('/health')
def health_check():
    """
    Health check de l'application
    """
    from flask import jsonify
    
    # Vérifier la configuration Azure
    azure_configured = bool(app.config.get('AZURE_SPEECH_KEY'))
    
    return jsonify({
        "status": "healthy",
        "app": "Voice Live Agent Configuration",
        "version": "1.0.0",
        "azure_configured": azure_configured,
        "azure_region": app.config.get('AZURE_SPEECH_REGION', 'not configured'),
        "session_active": bool(session),
        "blueprints": [
            "agents_manager",
            "azure_voices"
        ]
    })


@app.route('/about')
def about():
    """
    Page À propos
    """
    return render_template('about.html')


# ===================================================================
# GESTIONNAIRES D'ERREURS
# ===================================================================

@app.errorhandler(404)
def not_found(error):
    """Gestionnaire d'erreur 404"""
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Gestionnaire d'erreur 500"""
    logger.exception("Erreur serveur interne")
    return render_template('errors/500.html'), 500


# ===================================================================
# CONTEXTE DES TEMPLATES
# ===================================================================

@app.context_processor
def inject_config():
    """
    Injecte des variables de configuration dans tous les templates
    """
    import random as _random
    return {
        'app_name': 'Waka AI - Voice Live',
        'app_version': '1.0.0',
        'azure_configured': bool(app.config.get('AZURE_SPEECH_KEY')),
        'random': _random.randint,
        'range': range  # Aussi nécessaire pour range(1, 9999999)
    }


# ===================================================================
# COMMANDES CLI (optionnel)
# ===================================================================

@app.cli.command()
def test_azure():
    """
    Teste la connexion à Azure Speech Service
    """
    import requests
    
    azure_key = app.config.get('AZURE_SPEECH_KEY')
    azure_region = app.config.get('AZURE_SPEECH_REGION')
    
    if not azure_key:
        print("❌ AZURE_SPEECH_KEY n'est pas configurée")
        return
    
    try:
        endpoint = f"https://{azure_region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
        headers = {"Ocp-Apim-Subscription-Key": azure_key}
        
        print(f"🔍 Test de connexion à Azure ({azure_region})...")
        response = requests.get(endpoint, headers=headers, timeout=10)
        response.raise_for_status()
        
        voices = response.json()
        print(f"✅ Connexion réussie ! {len(voices)} voix disponibles")
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {str(e)}")


@app.route('/api/tools/execute', methods=['POST'])
def execute_tool_api():
    """
    Exécute un tool demandé par le modèle Voice Live
    """
    try:
        data = request.get_json()
        tool_name = data.get('tool_name')
        arguments = data.get('arguments', {})
        
        logger.info(f"🔧 Exécution du tool: {tool_name} avec args: {arguments}")
        
        # Utiliser la fonction centralisée d'exécution des tools
        from tools import execute_tool
        
        result = execute_tool(tool_name, arguments)
        
        logger.info(f"✅ Tool {tool_name} exécuté avec succès")
        
        return jsonify({
            'success': True,
            'tool_name': tool_name,
            'result': result
        }), 200
        
    except Exception as e:
        logger.exception("❌ Erreur lors de l'exécution du tool")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/agents/config/finalize', methods=['POST'])
def finalize_agent_config():
    try:
        data = request.get_json()
        
        config = {
            'model_name': data.get('model_name', 'gpt-4o-mini'),
            'temperature': safe_float(data.get('temperature', ''), 0.7),
            'max_tokens': safe_int(data.get('max_tokens', ''), 1000),
            'vad_threshold': safe_float(data.get('vad_threshold', ''), 0.5),
            'vad_prefix_padding_ms': safe_int(data.get('vad_prefix_padding_ms', ''), 300),
            'language': data.get('language', 'fr'),
            'voice': data.get('voice', 'fr-FR-DeniseNeural'),
            'tools': data.get('tools', [])
        }
        
        print(f"✅ Config validée: {config['model_name']}")
        
        return jsonify({
            'success': True,
            'message': 'Agent créé avec succès !',
            'config': config
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ===================================================================
# POINT D'ENTRÉE
# ===================================================================

def create_app():
    """
    Factory pattern pour créer l'application
    Utile pour les tests
    """
    return app


if __name__ == '__main__':
    # Vérifications avant le démarrage
    print("\n" + "="*60)
    print("🚀 Démarrage de l'application Waka AI - Voice Live")
    print("="*60)
    
    # Vérifier la configuration
    if not app.config.get('AZURE_SPEECH_KEY'):
        print("\n⚠️  ATTENTION : AZURE_SPEECH_KEY n'est pas configurée")
        print("   Les fonctionnalités de sélection de voix ne fonctionneront pas.")
        print("   Configurez AZURE_SPEECH_KEY dans votre fichier .env")
    else:
        print(f"\n✅ Azure Speech configuré (région: {app.config['AZURE_SPEECH_REGION']})")
    
    if app.config['SECRET_KEY'] == 'dev-secret-key-CHANGE-IN-PRODUCTION-123456789':
        print("\n⚠️  ATTENTION : Utilisation de la SECRET_KEY par défaut")
        print("   Changez SECRET_KEY dans votre fichier .env en production !")
    else:
        print("\n✅ SECRET_KEY personnalisée configurée")
    
    # Afficher les routes disponibles
    port = app.config['PORT']
    print("\n📋 Routes disponibles :")
    print(f"   - http://localhost:{port}/")
    print(f"   - http://localhost:{port}/health")
    print(f"   - http://localhost:{port}/agents/config/step1")
    print(f"   - http://localhost:{port}/api/azure-voices/health")
    
    print("\n" + "="*60)
    print(f"🌐 Serveur démarré sur http://{app.config['HOST']}:{port}")
    print("="*60 + "\n")
    
    # Démarrer l'application
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG'],
        use_reloader=app.config['DEBUG']
    )

