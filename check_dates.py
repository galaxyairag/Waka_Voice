#!/usr/bin/env python3
"""
Vérifier les dates ended_at des conversations
"""
from configuration.cosmos_config import get_call_history_container
from datetime import datetime, timezone

container = get_call_history_container()

query = """
SELECT c.id, c.status, c.ended_at, c.started_at
FROM c 
WHERE c.status = 'completed'
ORDER BY c.ended_at DESC
"""

items = list(container.query_items(
    query=query,
    enable_cross_partition_query=True
))

print(f"📊 Nombre de conversations complétées: {len(items)}")
print("\n" + "="*80)

for item in items[:20]:  # Afficher les 20 premières
    ended_at = item.get('ended_at', 'N/A')
    started_at = item.get('started_at', 'N/A')
    conv_id = item.get('id', 'N/A')
    
    # Extraire la date (sans l'heure)
    date_ended = ended_at.split('T')[0] if 'T' in str(ended_at) else ended_at
    
    print(f"ID: {conv_id[:20]:<20} | Terminée: {date_ended} | Heure: {ended_at}")

# Aujourd'hui en UTC
now = datetime.now(timezone.utc)
day_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
day_end = day_start.replace(hour=23, minute=59, second=59, microsecond=999999)

day_start_iso = day_start.isoformat().replace("+00:00", "Z")
day_end_iso = day_end.isoformat().replace("+00:00", "Z")

print("\n" + "="*80)
print(f"🕐 Aujourd'hui (UTC): {now.date()}")
print(f"   Début: {day_start_iso}")
print(f"   Fin:   {day_end_iso}")

# Compter combien aujourd'hui
today_query = f"""
SELECT VALUE COUNT(1) 
FROM c 
WHERE c.status = 'completed'
AND c.ended_at >= '{day_start_iso}' 
AND c.ended_at <= '{day_end_iso}'
"""

count_today = list(container.query_items(
    query=today_query,
    enable_cross_partition_query=True
))

print(f"\n📊 Conversations complétées AUJOURD'HUI: {count_today[0] if count_today else 0}")
