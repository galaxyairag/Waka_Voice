"""
Tool: End Conversation
Détecte sémantiquement la fin d'une conversation et déclenche la clôture automatique.

Ce tool est appelé par l'agent quand l'utilisateur exprime son intention de terminer
la conversation via des phrases comme "au revoir", "merci c'est tout", "terminé", etc.
"""

import logging

logger = logging.getLogger(__name__)


def get_tool_definition():
    """
    Définition du tool pour l'API OpenAI Realtime
    
    Returns:
        dict: Définition au format OpenAI Function Calling
    """
    return {
        "type": "function",
        "name": "end_conversation",
        "description": """Termine la conversation de manière automatique et élégante.

⚠️ COMPORTEMENT OBLIGATOIRE AVANT D'APPELER CET OUTIL:
AVANT d'appeler cet outil, vous DEVEZ:
1. Saluer chaleureusement l'utilisateur (utiliser son nom si connu)
2. Le remercier d'avoir utilisé le service
3. L'inviter explicitement à rappeler quand il le souhaite
4. Préciser que le service est disponible 7 jours sur 7, 24 heures sur 24
5. ENSUITE SEULEMENT, appeler ce tool pour déclencher la clôture technique

EXEMPLE DE RÉPONSE ATTENDUE:
"Au revoir [Nom] ! Merci d'avoir utilisé notre service. N'hésitez pas à me rappeler quand vous le souhaitez, je suis disponible 7 jours sur 7, 24 heures sur 24. Passez une excellente journée !"

QUAND UTILISER CET OUTIL:
Appelle cet outil APRÈS avoir salué l'utilisateur et l'avoir invité à rappeler 24/7, quand il exprime clairement son intention de terminer.

PHRASES DE DÉTECTION (exemples):
- "au revoir", "à bientôt", "à plus tard", "bye", "goodbye", "ciao", "salut"
- "merci c'est tout", "merci beaucoup", "c'est parfait merci", "OK merci"
- "terminé", "c'est bon", "j'ai fini", "c'est tout pour moi"
- "je dois y aller", "je te laisse", "bonne journée", "bonne soirée"
- "ça ira comme ça", "c'est suffisant", "plus de questions"

EXEMPLE DE FLUX COMPLET:
Utilisateur: "Merci beaucoup, au revoir !"
1. L'agent répond: "Au revoir Monsieur Ouédraogo ! Merci d'avoir utilisé Waka Voice. N'hésitez pas à me rappeler quand vous voulez, je suis disponible 7j/7 et 24h/24. Bonne journée !"
2. L'agent appelle end_conversation(user_farewell_message="Merci beaucoup, au revoir !", conversation_summary="Réservation vol confirmée")
3. Le système clôture automatiquement la session (sauvegarde, analyse, calculs)
""",
        "parameters": {
            "type": "object",
            "properties": {
                "user_farewell_message": {
                    "type": "string",
                    "description": "Le message exact de l'utilisateur qui indique la fin de la conversation. Exemples: 'au revoir', 'merci c'est tout', 'terminé'"
                },
                "conversation_summary": {
                    "type": "string",
                    "description": "Résumé très court de ce qui a été accompli pendant la conversation. Exemples: 'Réservation de vol pour Paris', 'Recherche météo Ouagadougou', 'Traduction français-mooré'. Maximum 100 caractères."
                }
            },
            "required": ["user_farewell_message"]
        }
    }


def execute(user_farewell_message: str, conversation_summary: str = None):
    """
    Exécute le tool de fin de conversation
    
    Ce tool ne fait PAS la clôture technique (Cosmos DB, calculs, etc.).
    Il retourne simplement un signal qui sera intercepté par le frontend
    pour déclencher le processus de clôture complet.
    
    Args:
        user_farewell_message (str): Message de l'utilisateur indiquant la fin
        conversation_summary (str, optional): Résumé de la conversation
        
    Returns:
        dict: Résultat avec signal de clôture
    """
    logger.info(f"🛑 Fin de conversation détectée: '{user_farewell_message}'")
    
    if conversation_summary:
        logger.info(f"📝 Résumé: {conversation_summary}")
    
    return {
        "action": "end_conversation",
        "status": "conversation_ending",
        "message": "Conversation terminée par l'utilisateur",
        "user_farewell": user_farewell_message,
        "summary": conversation_summary or "Conversation terminée",
        "next_step": "Le système va clôturer automatiquement la session et effectuer les calculs nécessaires."
    }


# Alias pour la compatibilité
call_function = execute


if __name__ == "__main__":
    # Test du tool
    print("=== Test du tool end_conversation ===\n")
    
    # Test 1: Fin simple
    result = execute("au revoir")
    print("Test 1 - Fin simple:")
    print(result)
    print()
    
    # Test 2: Fin avec résumé
    result = execute("merci c'est tout", "Réservation vol Ouagadougou-Paris confirmée")
    print("Test 2 - Fin avec résumé:")
    print(result)
    print()
    
    # Affichage de la définition
    print("Définition du tool:")
    import json
    print(json.dumps(get_tool_definition(), indent=2, ensure_ascii=False))
