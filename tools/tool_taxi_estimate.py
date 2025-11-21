# tools/tool_taxi_estimate.py
"""
Tool : Estimation de prix de course taxi
Calcule le prix estimé d'une course de taxi à Ouagadougou et Bobo-Dioulasso.
Utilise Azure Maps Distance Matrix pour calculer la distance et applique les tarifs locaux.
"""

import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Azure Maps configuration
AZURE_MAPS_SUBSCRIPTION_KEY = os.getenv('AZURE_MAPS_SUBSCRIPTION_KEY', '')
AZURE_MAPS_ROUTE_URL = 'https://atlas.microsoft.com/route/directions/json'

# Tarifs taxi Burkina Faso (en FCFA)
# Source: tarifs moyens 2025
TAXI_RATES = {
    "Ouagadougou": {
        "base_fare": 500,  # Prix de prise en charge
        "per_km": 250,     # Prix par kilomètre
        "per_minute": 50,  # Prix par minute (si embouteillage)
        "minimum_fare": 1000,  # Course minimum
        "night_multiplier": 1.5,  # Majoration nuit (22h-6h)
        "airport_supplement": 1000  # Supplément aéroport
    },
    "Bobo-Dioulasso": {
        "base_fare": 400,
        "per_km": 200,
        "per_minute": 40,
        "minimum_fare": 800,
        "night_multiplier": 1.5,
        "airport_supplement": 800
    },
    "default": {
        "base_fare": 500,
        "per_km": 250,
        "per_minute": 50,
        "minimum_fare": 1000,
        "night_multiplier": 1.5,
        "airport_supplement": 0
    }
}

# Lieux populaires (pour géocodage rapide)
POPULAR_PLACES = {
    "Ouagadougou": {
        "aéroport": {"lat": 12.3532, "lon": -1.5124, "name": "Aéroport International de Ouagadougou"},
        "gare routière": {"lat": 12.3858, "lon": -1.5352, "name": "Gare Routière de Ouagadougou"},
        "ouaga 2000": {"lat": 12.3219, "lon": -1.4753, "name": "Quartier Ouaga 2000"},
        "zone du bois": {"lat": 12.3890, "lon": -1.5080, "name": "Zone du Bois"},
        "université": {"lat": 12.3608, "lon": -1.5336, "name": "Université de Ouagadougou"},
        "hôpital yalgado": {"lat": 12.3758, "lon": -1.5213, "name": "CHU Yalgado Ouédraogo"},
        "place des nations unies": {"lat": 12.3686, "lon": -1.5275, "name": "Place des Nations Unies"}
    },
    "Bobo-Dioulasso": {
        "aéroport": {"lat": 11.1601, "lon": -4.3309, "name": "Aéroport de Bobo-Dioulasso"},
        "gare": {"lat": 11.1810, "lon": -4.2926, "name": "Gare de Bobo-Dioulasso"},
        "grand marché": {"lat": 11.1785, "lon": -4.2889, "name": "Grand Marché"},
        "université nazi boni": {"lat": 11.1550, "lon": -4.3150, "name": "Université Nazi Boni"}
    }
}


def get_tool_definition():
    """
    Définition du tool pour OpenAI function calling
    """
    return {
        "type": "function",
        "name": "estimate_taxi_fare",
        "description": """Estime le prix d'une course de taxi au Burkina Faso (Ouagadougou, Bobo-Dioulasso).

IMPORTANT : Utilise ce tool pour :
- Estimation prix taxi
- Combien coûte course taxi
- Prix trajet de A à B

EXEMPLE:
{
  "city": "Ouagadougou",
  "origin": "aéroport",
  "destination": "ouaga 2000",
  "night_time": false
}

Retourne estimation prix en FCFA avec détails (distance, durée).""",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": """Ville où se fait la course.

VILLES SUPPORTÉES:
- Ouagadougou (défaut)
- Bobo-Dioulasso

FORMAT: Nom de ville""",
                    "default": "Ouagadougou"
                },
                "origin": {
                    "type": "string",
                    "description": """Point de départ de la course.

EXEMPLES OUAGADOUGOU:
- "aéroport"
- "gare routière"
- "ouaga 2000"
- "zone du bois"
- "université"
- "hôpital yalgado"
- Ou adresse complète

EXEMPLES BOBO-DIOULASSO:
- "aéroport"
- "gare"
- "grand marché"
- "université nazi boni"

FORMAT: Nom de lieu ou adresse"""
                },
                "destination": {
                    "type": "string",
                    "description": """Point d'arrivée de la course.

Même format que origin.

FORMAT: Nom de lieu ou adresse"""
                },
                "night_time": {
                    "type": "boolean",
                    "description": """Si true, applique majoration nocturne (22h-6h).

DEFAULT: false""",
                    "default": False
                },
                "from_airport": {
                    "type": "boolean",
                    "description": """Si true, applique supplément aéroport.

DEFAULT: false""",
                    "default": False
                }
            },
            "required": ["city", "origin", "destination"]
        }
    }


def geocode_place(city, place_name):
    """
    Convertit un nom de lieu en coordonnées GPS
    
    Args:
        city: Ville
        place_name: Nom du lieu
    
    Returns:
        dict: {"lat": ..., "lon": ..., "name": ...} ou None
    """
    # Chercher dans lieux populaires d'abord
    city_normalized = city.replace("Ouaga", "Ouagadougou").replace("Bobo", "Bobo-Dioulasso")
    
    if city_normalized in POPULAR_PLACES:
        place_lower = place_name.lower().strip()
        if place_lower in POPULAR_PLACES[city_normalized]:
            return POPULAR_PLACES[city_normalized][place_lower]
    
    # TODO: Intégrer Azure Maps Geocoding pour adresses complètes
    # Pour l'instant, retourner None si pas trouvé
    return None


def calculate_route_azure_maps(origin_coords, dest_coords):
    """
    Calcule la route via Azure Maps
    
    Args:
        origin_coords: {"lat": ..., "lon": ...}
        dest_coords: {"lat": ..., "lon": ...}
    
    Returns:
        dict: {"distance_km": ..., "duration_min": ...} ou None
    """
    try:
        if not AZURE_MAPS_SUBSCRIPTION_KEY:
            logger.warning("⚠️ Azure Maps key non configurée")
            return None
        
        # Query format: lat1,lon1:lat2,lon2
        query = f"{origin_coords['lat']},{origin_coords['lon']}:{dest_coords['lat']},{dest_coords['lon']}"
        
        params = {
            'subscription-key': AZURE_MAPS_SUBSCRIPTION_KEY,
            'api-version': '1.0',
            'query': query,
            'travelMode': 'car',
            'language': 'fr-FR'
        }
        
        response = requests.get(AZURE_MAPS_ROUTE_URL, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        routes = data.get('routes', [])
        
        if not routes:
            return None
        
        summary = routes[0].get('summary', {})
        distance_meters = summary.get('lengthInMeters', 0)
        duration_seconds = summary.get('travelTimeInSeconds', 0)
        
        return {
            "distance_km": distance_meters / 1000,
            "duration_min": duration_seconds / 60
        }
        
    except Exception as e:
        logger.exception(f"❌ Erreur Azure Maps routing: {str(e)}")
        return None


def estimate_fare(city, distance_km, duration_min, night_time=False, from_airport=False):
    """
    Calcule le prix estimé de la course
    
    Args:
        city: Ville
        distance_km: Distance en km
        duration_min: Durée en minutes
        night_time: Tarif nuit
        from_airport: Supplément aéroport
    
    Returns:
        dict: Détails de l'estimation
    """
    city_normalized = city.replace("Ouaga", "Ouagadougou").replace("Bobo", "Bobo-Dioulasso")
    rates = TAXI_RATES.get(city_normalized, TAXI_RATES["default"])
    
    # Calcul base
    base_price = rates["base_fare"]
    distance_price = distance_km * rates["per_km"]
    time_price = duration_min * rates["per_minute"]
    
    total = base_price + distance_price + time_price
    
    # Majoration nuit
    if night_time:
        total *= rates["night_multiplier"]
    
    # Supplément aéroport
    if from_airport:
        total += rates["airport_supplement"]
    
    # Minimum
    if total < rates["minimum_fare"]:
        total = rates["minimum_fare"]
    
    return {
        "base_fare": base_price,
        "distance_fare": distance_price,
        "time_fare": time_price,
        "total_before_adjustments": base_price + distance_price + time_price,
        "night_multiplier": rates["night_multiplier"] if night_time else 1.0,
        "airport_supplement": rates["airport_supplement"] if from_airport else 0,
        "minimum_fare": rates["minimum_fare"],
        "estimated_fare": int(total),
        "distance_km": round(distance_km, 2),
        "duration_min": int(duration_min)
    }


def execute(arguments):
    """
    Exécute l'estimation de prix taxi
    
    Args:
        arguments: Dictionnaire contenant:
            - city: Ville
            - origin: Départ
            - destination: Arrivée
            - night_time: Tarif nuit (optionnel)
            - from_airport: Depuis aéroport (optionnel)
    
    Returns:
        dict: Résultat avec estimation prix
    """
    city = arguments.get('city', 'Ouagadougou')
    origin = arguments.get('origin', '')
    destination = arguments.get('destination', '')
    night_time = arguments.get('night_time', False)
    from_airport = arguments.get('from_airport', False)
    
    logger.info(f"🚕 Estimation taxi: {city}, {origin} → {destination}")
    
    try:
        # Géocoder origine et destination
        origin_coords = geocode_place(city, origin)
        dest_coords = geocode_place(city, destination)
        
        if not origin_coords or not dest_coords:
            return {
                "status": "error",
                "message": f"Impossible de localiser '{origin}' ou '{destination}' à {city}. Utilisez des lieux connus (aéroport, gare, université, etc.)."
            }
        
        # Calculer itinéraire
        route = calculate_route_azure_maps(origin_coords, dest_coords)
        
        if not route:
            # Fallback: estimation basique (distance à vol d'oiseau * 1.3)
            import math
            lat1, lon1 = origin_coords['lat'], origin_coords['lon']
            lat2, lon2 = dest_coords['lat'], dest_coords['lon']
            
            # Formule haversine
            R = 6371  # Rayon Terre en km
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance_km = R * c * 1.3  # Facteur route réelle
            
            duration_min = distance_km / 30 * 60  # Assumé 30 km/h moyenne
            
            route = {
                "distance_km": distance_km,
                "duration_min": duration_min
            }
        
        # Estimer prix
        estimate = estimate_fare(city, route['distance_km'], route['duration_min'], night_time, from_airport)
        
        # Formater message
        message = f"""🚕 Estimation course taxi à {city}

📍 Trajet: {origin_coords['name']} → {dest_coords['name']}
📏 Distance: {estimate['distance_km']} km
⏱️ Durée estimée: {estimate['duration_min']} min

💰 PRIX ESTIMÉ: {estimate['estimated_fare']:,} FCFA

Détails:
• Prise en charge: {estimate['base_fare']} FCFA
• Distance ({estimate['distance_km']} km): {int(estimate['distance_fare'])} FCFA
• Temps ({estimate['duration_min']} min): {int(estimate['time_fare'])} FCFA"""

        if night_time:
            message += f"\n• Majoration nuit (x{estimate['night_multiplier']}): incluse"
        
        if from_airport:
            message += f"\n• Supplément aéroport: {estimate['airport_supplement']} FCFA"
        
        message += f"\n\n⚠️ Prix indicatif. Peut varier selon trafic et chauffeur."
        
        return {
            "status": "success",
            "city": city,
            "origin": origin_coords['name'],
            "destination": dest_coords['name'],
            "estimate": estimate,
            "message": message
        }
        
    except Exception as e:
        logger.exception(f"❌ Erreur estimation taxi: {str(e)}")
        return {
            "status": "error",
            "message": f"Erreur lors de l'estimation: {str(e)}"
        }
