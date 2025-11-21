"""
Script pour vider les containers Cosmos DB (agents et avatars)
Supprime tous les documents dans les containers AgentConfigurations et AvatarConfigurations
"""

import logging
from configuration.cosmos_config import get_agents_container, get_avatar_container

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_container(container, container_name):
    """
    Vide tous les documents d'un container
    
    Args:
        container: Instance du container Cosmos DB
        container_name (str): Nom du container pour les logs
    """
    try:
        # Récupérer tous les documents
        query = "SELECT c.id, c.agent_id FROM c"
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        total_count = len(items)
        logger.info(f"📦 Container '{container_name}': {total_count} document(s) trouvé(s)")
        
        if total_count == 0:
            logger.info(f"✅ Container '{container_name}' déjà vide")
            return
        
        # Supprimer chaque document
        deleted_count = 0
        for item in items:
            try:
                container.delete_item(
                    item=item['id'],
                    partition_key=item['agent_id']
                )
                deleted_count += 1
                logger.info(f"  🗑️  Supprimé: {item['id']} (partition: {item['agent_id']})")
            except Exception as e:
                logger.error(f"  ❌ Erreur suppression {item['id']}: {e}")
        
        logger.info(f"✅ Container '{container_name}' vidé: {deleted_count}/{total_count} document(s) supprimé(s)")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du vidage du container '{container_name}': {e}")
        raise


def main():
    """
    Fonction principale - vide les containers agents et avatars
    """
    logger.info("🚀 Début du vidage des containers Cosmos DB")
    logger.info("=" * 60)
    
    # Vider le container des agents
    logger.info("\n📦 Vidage du container 'AgentConfigurations'...")
    agents_container = get_agents_container()
    clear_container(agents_container, "AgentConfigurations")
    
    # Vider le container des avatars
    logger.info("\n📦 Vidage du container 'AvatarConfigurations'...")
    avatar_container = get_avatar_container()
    clear_container(avatar_container, "AvatarConfigurations")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Vidage des containers terminé avec succès")


if __name__ == "__main__":
    main()
