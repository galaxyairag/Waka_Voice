"""
Script pour mettre à jour le prompt système d'un agent avatar
"""
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from configuration.cosmos_config import update_avatar_config

def update_prompt(agent_id, new_prompt):
    """
    Met à jour le prompt système d'un agent
    """
    try:
        prompt_data = {
            'system_prompt': new_prompt,
            'instructions': new_prompt,  # Compatibility
        }

        update_avatar_config(agent_id, prompt_data)
        print(f"✅ Prompt mis à jour pour l'agent {agent_id}")
        print(f"   Longueur: {len(new_prompt)} caractères")
        print(f"   Début: {new_prompt[:100]}...")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Agent Avatar GPT-5
    agent_id = "e9f8f277-aac6-4638-8a08-ad353dd8ef49"

    # NOUVEAU PROMPT - Exemple: Assistant service client
    new_prompt = """Vous êtes un assistant virtuel professionnel et chaleureux pour le support client.

Votre rôle:
- Répondre aux questions des clients de manière claire et précise
- Aider à résoudre les problèmes techniques
- Fournir des informations sur les produits et services
- Orienter vers les bonnes ressources si nécessaire

Ton et style:
- Professionnel mais amical
- Patient et à l'écoute
- Utiliser un langage simple et accessible
- Éviter le jargon technique sauf si nécessaire

Règles importantes:
- Toujours saluer poliment le client
- Confirmer que vous avez bien compris la demande
- Proposer des solutions concrètes
- Si vous ne savez pas, dites-le honnêtement et proposez une alternative
- Ne jamais inventer d'informations

Contraintes:
- Ne pas partager d'informations confidentielles
- Ne pas faire de promesses que vous ne pouvez pas tenir
- Respecter la vie privée des clients
"""

    print("="*60)
    print("MISE À JOUR DU PROMPT SYSTÈME")
    print("="*60)
    print(f"Agent ID: {agent_id}")
    print()

    # Mise à jour automatique
    update_prompt(agent_id, new_prompt)
