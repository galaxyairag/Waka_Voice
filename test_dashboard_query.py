"""
Test pour comprendre pourquoi le dashboard retourne 0 résultats
"""
from configuration.cosmos_config import get_call_history_container
from datetime import datetime, timedelta

container = get_call_history_container()

# Test 1: Compter toutes les conversations completed
print("=" * 80)
print("TEST 1: Conversations avec status='completed'")
print("=" * 80)

query1 = "SELECT VALUE COUNT(1) FROM c WHERE c.status = 'completed'"
result1 = list(container.query_items(query=query1, enable_cross_partition_query=True))
print(f"Total conversations completed: {result1[0] if result1 else 0}")

# Test 2: Compter les conversations avec ended_at
print("\n" + "=" * 80)
print("TEST 2: Conversations avec ended_at (existe)")
print("=" * 80)

query2 = "SELECT VALUE COUNT(1) FROM c WHERE c.status = 'completed' AND IS_DEFINED(c.ended_at)"
result2 = list(container.query_items(query=query2, enable_cross_partition_query=True))
print(f"Conversations avec ended_at défini: {result2[0] if result2 else 0}")

# Test 3: Vérifier les dernières conversations avec ended_at
print("\n" + "=" * 80)
print("TEST 3: 5 dernières conversations avec ended_at")
print("=" * 80)

query3 = """
SELECT TOP 5 c.call_id, c.ended_at, c._ts
FROM c
WHERE c.status = 'completed' AND IS_DEFINED(c.ended_at)
ORDER BY c.ended_at DESC
"""
result3 = list(container.query_items(query=query3, enable_cross_partition_query=True))
for item in result3:
    print(f"  - call_id: {item['call_id']}")
    print(f"    ended_at: {item['ended_at']}")
    print(f"    _ts: {item['_ts']} ({datetime.utcfromtimestamp(item['_ts']).isoformat()})")
    print()

# Test 4: Tester la requête exacte du dashboard de production (30 derniers jours)
print("=" * 80)
print("TEST 4: Requête du dashboard production (30 derniers jours)")
print("=" * 80)

end_date = datetime.utcnow()
start_date = end_date - timedelta(days=30)
start_timestamp = start_date.isoformat() + "Z"

query4 = """
SELECT c.call_id, c.agent_id, c.model, c.model_family, c.status,
       c.duration_minutes, c.cost, c.tokens, c.interaction_count,
       c.start_time, c.end_time, c.ended_at, c._ts
FROM c
WHERE c.status = 'completed'
      AND c.ended_at >= @start_timestamp
ORDER BY c.ended_at DESC
"""

parameters = [{"name": "@start_timestamp", "value": start_timestamp}]

result4 = list(container.query_items(
    query=query4,
    parameters=parameters,
    enable_cross_partition_query=True
))

print(f"Date de début: {start_timestamp}")
print(f"Conversations trouvées: {len(result4)}")

if result4:
    print(f"\nPremière conversation:")
    conv = result4[0]
    print(f"  - call_id: {conv.get('call_id')}")
    print(f"  - ended_at: {conv.get('ended_at')}")
    print(f"  - duration_minutes: {conv.get('duration_minutes')}")
    print(f"  - cost: {conv.get('cost')}")
    print(f"  - interaction_count: {conv.get('interaction_count')}")
else:
    print("\n⚠️  AUCUNE CONVERSATION TROUVÉE avec la requête du dashboard!")
    print(f"\nDébug: Vérifions s'il y a des conversations avec ended_at > {start_timestamp}")
    
    query_debug = f"""
    SELECT TOP 5 c.call_id, c.ended_at
    FROM c
    WHERE c.status = 'completed'
    ORDER BY c.ended_at DESC
    """
    debug_result = list(container.query_items(query=query_debug, enable_cross_partition_query=True))
    print(f"\n5 dernières conversations (sans filtre de date):")
    for item in debug_result:
        print(f"  - {item.get('call_id')}: {item.get('ended_at')}")

# Test 5: Tester la requête du dashboard qualité (utilise _ts)
print("\n" + "=" * 80)
print("TEST 5: Requête du dashboard qualité (30 derniers jours avec _ts)")
print("=" * 80)

start_timestamp_quality = int(start_date.timestamp())

query5 = """
SELECT c.call_id, c.agent_id, c.model, c.model_family, c.status,
       c.duration_minutes, c.cost, c.tokens,
       c.user_sentiment_analysis, c.assistant_sentiment_analysis,
       c.start_time, c.end_time, c._ts
FROM c
WHERE c.status = 'completed'
      AND c._ts >= @start_timestamp
ORDER BY c._ts DESC
"""

parameters5 = [{"name": "@start_timestamp", "value": start_timestamp_quality}]

result5 = list(container.query_items(
    query=query5,
    parameters=parameters5,
    enable_cross_partition_query=True
))

print(f"Timestamp de début: {start_timestamp_quality} ({start_date.isoformat()})")
print(f"Conversations trouvées: {len(result5)}")

print("\n" + "=" * 80)
print("RÉSUMÉ")
print("=" * 80)
print(f"Conversations completed total: {result1[0] if result1 else 0}")
print(f"Conversations avec ended_at: {result2[0] if result2 else 0}")
print(f"Dashboard Production (ended_at >= 30j): {len(result4)}")
print(f"Dashboard Qualité (_ts >= 30j): {len(result5)}")
