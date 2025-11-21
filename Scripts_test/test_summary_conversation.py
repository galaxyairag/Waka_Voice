import uuid
from datetime import datetime, timedelta

from configuration.cosmos_config import (
    save_conversation_message,
    end_conversation,
    get_conversation_history,
    get_call_history_container,
)


def main():
    # 1) Créer un call_id de test
    call_id = f"test-summary-{uuid.uuid4()}"
    agent_id = "agent-summary-test"
    model_name = "gpt-5-mini"  # adapte si besoin

    print(f"🔎 Test résumé pour call_id = {call_id}")

    # 2) Injecter quelques messages dans l'historique
    save_conversation_message(
        call_id=call_id,
        agent_id=agent_id,
        message_type="user",
        content="Bonjour, je voudrais des informations sur l'ouverture d'un compte bancaire.",
        metadata={},
        model=model_name,
    )
    save_conversation_message(
        call_id=call_id,
        agent_id=agent_id,
        message_type="agent",
        content="Bonjour, je peux vous aider avec plaisir. Quel type de compte recherchez-vous ?",
        metadata={},
        model=model_name,
    )
    save_conversation_message(
        call_id=call_id,
        agent_id=agent_id,
        message_type="user",
        content="Un compte courant avec une carte bancaire internationale, et savoir les frais.",
        metadata={},
        model=model_name,
    )
    save_conversation_message(
        call_id=call_id,
        agent_id=agent_id,
        message_type="agent",
        content=(
            "Très bien, nos comptes courants incluent une carte Visa internationale. "
            "Les frais de tenue de compte sont de 5 000 FCFA par mois."
        ),
        metadata={},
        model=model_name,
    )

    # 3) Simuler que la conversation a duré quelques minutes
    doc = get_conversation_history(call_id)
    if not doc:
        print("❌ Impossible de relire la conversation juste après l'écriture.")
        return

    # On triche en mettant started_at 5 minutes avant maintenant
    started_at = (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z"
    doc["started_at"] = started_at

    # Sauvegarde rapide de cette modif avant end_conversation
    container = get_call_history_container()
    container.upsert_item(doc)

    # 4) Appeler end_conversation pour déclencher toutes les analyses + résumé
    tokens = {
        "inputs_text_tokens": 300,
        "inputs_cached_tokens": 0,
        "inputs_audio_tokens": 0,
        "outputs_text_tokens": 400,
        "outputs_audio_tokens": 0,
    }

    print("✅ Appel de end_conversation(...)")
    updated = end_conversation(call_id, tools_used=["test_summary_tool"], tokens=tokens)

    # 5) Afficher les infos clés
    print("\n=== Résultat end_conversation ===")
    print(f"status: {updated.get('status')}")
    print(f"duration_minutes: {updated.get('duration_minutes')}")
    print(f"interaction_count: {updated.get('interaction_count')}")
    cost = updated.get("cost", {})
    print(f"total_cost: {cost.get('total_cost')}")
    print(f"cost_per_minute: {cost.get('cost_per_minute')}")

    print("\n=== Résumé généré (summary) ===")
    summary = updated.get("summary")
    if summary:
        print(summary)
    else:
        print(
            "⚠️ Aucun résumé présent dans le document. "
            "Vérifie les variables AZURE_OPENAI_SUMMARY_* et les logs."
        )


if __name__ == "__main__":
    main()
