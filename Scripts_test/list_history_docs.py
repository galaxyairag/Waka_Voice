from configuration.cosmos_config import get_instructions_container


def main():
    container = get_instructions_container()
    query = """
        SELECT c.id, c.call_id, c.started_at, c.status
        FROM c
        
    """

    items = list(container.query_items(query=query, enable_cross_partition_query=True))

    if not items:
        print("Aucun document d'historique trouvé dans CallHistory.")
        return

    print(f"{len(items)} document(s) dans l'historique :")
    for doc in items:
        print(
            f"- id: {doc.get('id')} | call_id: {doc.get('call_id')} | "
            f"started_at: {doc.get('started_at')} | status: {doc.get('status')}"
        )


if __name__ == "__main__":
    main()
