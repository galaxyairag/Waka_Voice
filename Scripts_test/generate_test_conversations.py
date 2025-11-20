"""
Script pour générer des conversations de test pour la démo
Génère 5 conversations par jour sur les 7 derniers jours
"""

import os
import sys
from datetime import datetime, timedelta, timezone
import random
import uuid

# Ajouter le chemin racine pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configuration.cosmos_config import get_call_history_container

# Données de base d'une conversation GPT-4o réelle (à multiplier)
BASE_CONVERSATION = {
    "model": "gpt-4o-realtime",
    "model_family": "gpt-4o-realtime",
    "pricing_tier": "pro",
    "status": "completed",
    "duration_minutes": 9.104,
    "interaction_count": 6,
    "average_interaction_duration": 1.517,
    "tokens": {
        "inputs_text_tokens": 15603,
        "inputs_cached_tokens": 15616,
        "inputs_audio_tokens": 80,
        "outputs_text_tokens": 34,
        "outputs_audio_tokens": 140
    },
    "cost": {
        "inputs_text_cost": 0.085817,
        "inputs_cached_cost": 0.042944,
        "inputs_audio_cost": 0.00136,
        "outputs_text_cost": 0.000748,
        "outputs_audio_cost": 0.0077,
        "total_cost": 0.138569,
        "cost_per_minute": 0.015221
    }
}

# Multiplicateurs pour varier les données
MULTIPLIERS = [1, 1.5, 2, 2.5, 3, 0.8, 1.2]

def generate_conversation(day_offset, conv_index):
    """Génère une conversation de test"""
    
    # Date de la conversation (dans le passé selon day_offset)
    target_date = datetime.now(timezone.utc) - timedelta(days=day_offset)
    started_at = target_date.replace(hour=random.randint(8, 18), minute=random.randint(0, 59), second=random.randint(0, 59))
    
    # Choisir un multiplicateur
    multiplier = MULTIPLIERS[conv_index % len(MULTIPLIERS)]
    
    # Calculer les nouvelles valeurs
    duration = round(BASE_CONVERSATION["duration_minutes"] * multiplier, 3)
    interaction_count = max(1, int(BASE_CONVERSATION["interaction_count"] * multiplier))
    avg_interaction_duration = round(duration / interaction_count, 3)
    
    # Tokens multipliés
    tokens = {
        "inputs_text_tokens": int(BASE_CONVERSATION["tokens"]["inputs_text_tokens"] * multiplier),
        "inputs_cached_tokens": int(BASE_CONVERSATION["tokens"]["inputs_cached_tokens"] * multiplier),
        "inputs_audio_tokens": int(BASE_CONVERSATION["tokens"]["inputs_audio_tokens"] * multiplier),
        "outputs_text_tokens": int(BASE_CONVERSATION["tokens"]["outputs_text_tokens"] * multiplier),
        "outputs_audio_tokens": int(BASE_CONVERSATION["tokens"]["outputs_audio_tokens"] * multiplier)
    }
    
    # Coûts multipliés
    cost = {
        "inputs_text_cost": round(BASE_CONVERSATION["cost"]["inputs_text_cost"] * multiplier, 6),
        "inputs_cached_cost": round(BASE_CONVERSATION["cost"]["inputs_cached_cost"] * multiplier, 6),
        "inputs_audio_cost": round(BASE_CONVERSATION["cost"]["inputs_audio_cost"] * multiplier, 6),
        "outputs_text_cost": round(BASE_CONVERSATION["cost"]["outputs_text_cost"] * multiplier, 6),
        "outputs_audio_cost": round(BASE_CONVERSATION["cost"]["outputs_audio_cost"] * multiplier, 6),
        "total_cost": round(BASE_CONVERSATION["cost"]["total_cost"] * multiplier, 6),
        "cost_per_minute": round(BASE_CONVERSATION["cost"]["cost_per_minute"] * multiplier, 6)
    }
    
    ended_at = started_at + timedelta(minutes=duration)
    
    # Générer IDs uniques
    call_id = str(uuid.uuid4())
    agent_id = "demo-agent-" + str(uuid.uuid4())[:8]
    
    conversation = {
        "id": str(uuid.uuid4()),
        "call_id": call_id,
        "agent_id": agent_id,
        "started_at": started_at.isoformat() + "Z",
        "updated_at": ended_at.isoformat() + "Z",
        "ended_at": ended_at.isoformat() + "Z",
        "conversation": [
            {
                "timestamp": started_at.isoformat() + "Z",
                "type": "user",
                "content": "Bonjour, j'ai besoin d'aide.",
                "metadata": {}
            },
            {
                "timestamp": (started_at + timedelta(seconds=2)).isoformat() + "Z",
                "type": "agent",
                "content": "Bonjour ! Je suis ravi de vous aider. Comment puis-je vous assister aujourd'hui ?",
                "metadata": {}
            },
            {
                "timestamp": ended_at.isoformat() + "Z",
                "type": "agent",
                "content": "Conversation terminée.",
                "metadata": {}
            }
        ],
        "status": "completed",
        "tools_used": [],
        "model": BASE_CONVERSATION["model"],
        "model_family": BASE_CONVERSATION["model_family"],
        "pricing_tier": BASE_CONVERSATION["pricing_tier"],
        "duration_minutes": duration,
        "interaction_count": interaction_count,
        "average_interaction_duration": avg_interaction_duration,
        "user_sentiment_analysis": {
            "sentiment": "positive" if random.random() > 0.5 else "neutral",
            "positive": round(random.uniform(0.4, 0.7), 2),
            "neutral": round(random.uniform(0.2, 0.4), 2),
            "negative": round(random.uniform(0.1, 0.3), 2)
        },
        "assistant_sentiment_analysis": {
            "sentiment": "positive",
            "positive": round(random.uniform(0.6, 0.8), 2),
            "neutral": round(random.uniform(0.1, 0.3), 2),
            "negative": round(random.uniform(0.05, 0.15), 2)
        },
        "tokens": tokens,
        "cost": cost
    }
    
    return conversation

def main():
    """Génère et insère les conversations de test"""
    
    print("=" * 80)
    print("GÉNÉRATION DE CONVERSATIONS DE TEST POUR LA DÉMO")
    print("=" * 80)
    print()
    
    container = get_call_history_container()
    
    total_conversations = 0
    
    # Générer 5 conversations par jour sur les 7 derniers jours
    for day in range(7):
        print(f"📅 Jour -{day} : ", end="")
        
        for conv_index in range(5):
            conversation = generate_conversation(day, conv_index)
            
            try:
                container.create_item(body=conversation)
                total_conversations += 1
                print("✓", end=" ")
            except Exception as e:
                print(f"✗ Erreur: {e}", end=" ")
        
        print()
    
    print()
    print("=" * 80)
    print(f"✅ {total_conversations} conversations de test créées avec succès!")
    print("=" * 80)
    print()
    print("Résumé:")
    print(f"  - Période: 7 derniers jours")
    print(f"  - Conversations par jour: 5")
    print(f"  - Total: {total_conversations}")
    print(f"  - Modèle: {BASE_CONVERSATION['model']}")
    print(f"  - Multiplicateurs utilisés: {MULTIPLIERS}")
    print()

if __name__ == "__main__":
    main()
