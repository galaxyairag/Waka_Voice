"""
Script de test pour vérifier la configuration Cosmos DB et Voice Live
"""

import logging
import sys
from datetime import datetime

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_cosmos_db():
    """
    Test de la connexion et initialisation Cosmos DB
    """
    logger.info("=" * 60)
    logger.info("TEST 1: Cosmos DB Configuration")
    logger.info("=" * 60)
    
    try:
        from configuration import (
            get_cosmos_client,
            get_database,
            get_agents_container,
            get_call_history_container,
            get_token_consumption_container,
            get_instructions_container
        )
        
        # Test client
        client = get_cosmos_client()
        logger.info(f"✅ Client Cosmos initialisé")
        
        # Test database
        database = get_database()
        logger.info(f"✅ Database '{database.id}' accessible")
        
        # Test containers
        agents_container = get_agents_container()
        logger.info(f"✅ Container '{agents_container.id}' prêt")
        
        call_history_container = get_call_history_container()
        logger.info(f"✅ Container '{call_history_container.id}' prêt")
        
        token_container = get_token_consumption_container()
        logger.info(f"✅ Container '{token_container.id}' prêt")
        
        instructions_container = get_instructions_container()
        logger.info(f"✅ Container '{instructions_container.id}' prêt")
        
        logger.info("🎯 Tous les containers sont initialisés avec succès!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test Cosmos DB: {e}")
        return False


def test_voice_live():
    """
    Test de la configuration Voice Live
    """
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Voice Live Configuration")
    logger.info("=" * 60)
    
    try:
        from configuration import get_voice_live_client, list_available_models
        
        # Liste des modèles disponibles
        models = list_available_models()
        logger.info(f"✅ {len(models)} modèles Realtime disponibles:")
        for model_id, config in models.items():
            logger.info(f"   - {model_id}: {config['description']}")
        
        # Test client par défaut
        client = get_voice_live_client()
        model_info = client.get_model_info()
        logger.info(f"✅ Client Voice Live créé avec {model_info['model_id']}")
        
        # Test URL WebSocket
        ws_url = client.get_websocket_url()
        logger.info(f"✅ WebSocket URL générée: {ws_url[:80]}...")
        
        logger.info("🎯 Configuration Voice Live OK!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test Voice Live: {e}")
        return False


def test_agent_save():
    """
    Test de sauvegarde d'une configuration d'agent
    """
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Sauvegarde d'un Agent de Test")
    logger.info("=" * 60)
    
    try:
        from configuration import save_agent_config, get_agent_config
        import uuid
        
        # Créer une configuration de test
        agent_id = str(uuid.uuid4())
        test_config = {
            "id": agent_id,
            "agent_id": agent_id,
            "agent_name": "Agent Test",
            "status": "en_cours_de_validation",
            "created_at": datetime.utcnow().isoformat() + 'Z',
            "updated_at": datetime.utcnow().isoformat() + 'Z',
            "config_type": "test",
            "model_id": "gpt-4o-realtime-preview",
            "model_name": "GPT-4o Realtime Preview",
            "voice_config": {
                "voice_name": "fr-FR-DeniseNeural"
            },
            "selected_tools": ["weather", "email"],
            "system_prompt": "Ceci est un test",
            "metadata": {
                "test": True,
                "version": 1
            }
        }
        
        # Sauvegarder
        saved_config = save_agent_config(test_config)
        logger.info(f"✅ Agent de test sauvegardé (ID: {saved_config['id']})")
        
        # Récupérer
        retrieved_config = get_agent_config(agent_id)
        if retrieved_config:
            logger.info(f"✅ Agent de test récupéré: {retrieved_config['agent_name']}")
        else:
            logger.error("❌ Impossible de récupérer l'agent de test")
            return False
        
        logger.info("🎯 Test de sauvegarde/récupération réussi!")
        logger.info(f"⚠️  N'oubliez pas de supprimer l'agent de test (ID: {agent_id})")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de sauvegarde: {e}")
        return False


def main():
    """
    Exécute tous les tests
    """
    logger.info("\n")
    logger.info("🚀 Démarrage des tests de configuration...")
    logger.info("\n")
    
    results = []
    
    # Test 1: Cosmos DB
    results.append(("Cosmos DB", test_cosmos_db()))
    
    # Test 2: Voice Live
    results.append(("Voice Live", test_voice_live()))
    
    # Test 3: Sauvegarde Agent
    results.append(("Sauvegarde Agent", test_agent_save()))
    
    # Résumé
    logger.info("\n" + "=" * 60)
    logger.info("RÉSUMÉ DES TESTS")
    logger.info("=" * 60)
    
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
        logger.info(f"{test_name:20s} : {status}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        logger.info("\n🎉 Tous les tests sont passés avec succès!")
        return 0
    else:
        logger.error("\n⚠️  Certains tests ont échoué. Vérifiez les logs ci-dessus.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
