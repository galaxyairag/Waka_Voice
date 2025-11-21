"""
Script pour générer des conversations de test avec le bon schéma
"""

import os
import sys
from datetime import datetime, timezone, timedelta
import uuid

# Ajouter le chemin racine pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configuration.cosmos_config import save_conversation_message, end_conversation

def generate_sample_conversations():
    """Génère 5 conversations de test avec différents profils"""
    
    print("=" * 80)
    print("GÉNÉRATION DE CONVERSATIONS DE TEST")
    print("=" * 80)
    print()
    
    conversations = [
        {
            "agent_id": str(uuid.uuid4()),
            "model": "gpt-4o-realtime-preview-2024-10-01",
            "messages": [
                ("user", "Bonjour, je voudrais réserver un vol pour Paris"),
                ("agent", "Bonjour ! Je serais ravi de vous aider avec votre réservation. Quelles sont vos dates de voyage ?"),
                ("user", "Du 15 au 20 décembre"),
                ("agent", "Parfait ! Je vais chercher les vols disponibles. Combien de passagers ?"),
                ("user", "Deux adultes"),
                ("agent", "Excellent, j'ai trouvé plusieurs options. Le vol AF1234 part à 10h et coûte 450€ par personne. Cela vous convient ?"),
                ("user", "Oui parfait, je prends celui-là"),
                ("agent", "Très bien ! Votre réservation est confirmée. Vous recevrez un email de confirmation dans quelques minutes. Bon voyage !")
            ],
            "tokens": {
                "inputs_text_tokens": 150,
                "inputs_cached_tokens": 50,
                "inputs_audio_tokens": 2000,
                "outputs_text_tokens": 200,
                "outputs_audio_tokens": 2500
            }
        },
        {
            "agent_id": str(uuid.uuid4()),
            "model": "gpt-4o-mini-realtime-preview-2024-12-17",
            "messages": [
                ("user", "J'ai un problème avec ma commande"),
                ("agent", "Je suis désolé d'apprendre que vous rencontrez un problème. Pouvez-vous me donner votre numéro de commande ?"),
                ("user", "C'est le #12345"),
                ("agent", "Merci. Je vois que votre commande a été expédiée hier. Quel est le problème exactement ?"),
                ("user", "Je n'ai pas reçu l'email de suivi"),
                ("agent", "Je comprends. Je vais vous renvoyer l'email de suivi immédiatement."),
                ("user", "Merci beaucoup"),
                ("agent", "De rien ! L'email vient d'être envoyé. Autre chose ?"),
                ("user", "Non c'est bon"),
                ("agent", "Parfait ! N'hésitez pas à nous contacter si besoin. Bonne journée !")
            ],
            "tokens": {
                "inputs_text_tokens": 120,
                "inputs_cached_tokens": 30,
                "inputs_audio_tokens": 1800,
                "outputs_text_tokens": 180,
                "outputs_audio_tokens": 2200
            }
        },
        {
            "agent_id": str(uuid.uuid4()),
            "model": "gpt-4.1-preview",
            "messages": [
                ("user", "Quelles sont vos heures d'ouverture ?"),
                ("agent", "Nous sommes ouverts du lundi au vendredi de 9h à 18h, et le samedi de 10h à 16h."),
                ("user", "Et le dimanche ?"),
                ("agent", "Nous sommes fermés le dimanche. Puis-je vous aider avec autre chose ?"),
                ("user", "Non merci"),
                ("agent", "Très bien ! Passez une excellente journée !")
            ],
            "tokens": {
                "inputs_text_tokens": 80,
                "inputs_cached_tokens": 20,
                "inputs_audio_tokens": 1200,
                "outputs_text_tokens": 100,
                "outputs_audio_tokens": 1400
            }
        }
    ]
    
    for i, conv_data in enumerate(conversations, 1):
        print(f"\n📝 Création de la conversation {i}/{len(conversations)}...")
        
        call_id = str(uuid.uuid4())
        agent_id = conv_data["agent_id"]
        model = conv_data["model"]
        
        # Sauvegarder chaque message
        for msg_type, content in conv_data["messages"]:
            save_conversation_message(
                call_id=call_id,
                agent_id=agent_id,
                message_type=msg_type,
                content=content,
                metadata={},
                model=model
            )
            print(".", end="", flush=True)
        
        # Terminer la conversation avec les tokens
        end_conversation(
            call_id=call_id,
            tools_used=[],
            tokens=conv_data["tokens"]
        )
        
        print(f" ✅ Conversation {call_id[:8]}... créée")
    
    print()
    print("=" * 80)
    print(f"✅ {len(conversations)} conversations de test créées avec succès!")
    print("=" * 80)
    print()

if __name__ == "__main__":
    generate_sample_conversations()
