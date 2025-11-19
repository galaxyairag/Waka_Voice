# tools/__init__.py
"""
Orchestrateur des outils pour Waka Agent AI
Importe tous les modules d'outils et fournit les fonctions centrales:
- get_tools_definition(): Retourne toutes les définitions d'outils
- execute_tool(tool_name, arguments): Exécute un outil spécifique
"""

from . import tool_search_web
from . import tool_email
from . import tool_cv
from . import tool_weather
from . import tool_currency
from . import tool_flight_search
from . import tool_hotel_search
from . import tool_flight_booking
from . import tool_hotel_booking
from . import tool_exercises
from . import tool_dogs
from . import tool_knowledge_base
from . import tool_health_advice
from . import tool_news
from . import tool_places
from . import tool_translator
from . import tool_calculator
from . import tool_end_conversation
from . import tool_prayer_times
from . import tool_pharmacy_locator
from . import tool_taxi_estimate
from . import tool_bus_schedule
from . import tool_school_info
from . import tool_government_services
from . import tool_tax_calculator


def get_tools_definition():
    """
    Retourne la liste complète des définitions d'outils.
    Collecte les définitions de tous les modules de tools/.
    
    Returns:
        list: Liste des définitions d'outils au format OpenAI function calling
    """
    tools = [
        tool_search_web.get_tool_definition(),
        tool_email.get_tool_definition(),
        tool_weather.get_tool_definition(),
        tool_cv.get_tool_definition(),
        tool_currency.get_tool_definition(),
        tool_flight_search.get_tool_definition(),
        tool_hotel_search.get_tool_definition(),
        tool_flight_booking.get_tool_definition(),
        tool_hotel_booking.get_tool_definition(),
        tool_exercises.get_tool_definition(),
        tool_dogs.get_tool_definition(),
        tool_knowledge_base.get_tool_definition(),
        tool_health_advice.get_tool_definition(),
        tool_news.get_tool_definition(),
        tool_places.get_tool_definition(),
        tool_translator.get_tool_definition(),
        tool_calculator.get_tool_definition(),
        tool_end_conversation.get_tool_definition(),
        tool_prayer_times.get_tool_definition(),
        tool_pharmacy_locator.get_tool_definition(),
        tool_taxi_estimate.get_tool_definition(),
        tool_bus_schedule.get_tool_definition(),
        tool_school_info.get_tool_definition(),
        tool_government_services.get_tool_definition(),
        tool_tax_calculator.get_tool_definition()
    ]
    
    return tools


def execute_tool(tool_name, arguments):
    """
    Exécute un outil spécifique avec les arguments fournis.
    
    Args:
        tool_name: Nom de l'outil à exécuter
        arguments: Dictionnaire des arguments pour l'outil
    
    Returns:
        dict: Résultat de l'exécution de l'outil
    """
    # Mapping des noms d'outils vers leurs modules
    tool_map = {
        "search_web": tool_search_web,
        "send_email": tool_email,
        "get_weather_forecast": tool_weather,
        "create_cv": tool_cv,
        "convert_currency": tool_currency,
        "search_flights": tool_flight_search,
        "search_hotels": tool_hotel_search,
        "book_flight": tool_flight_booking,
        "book_hotel": tool_hotel_booking,
        "search_exercises": tool_exercises,
        "search_dog_breeds": tool_dogs,
        "search_knowledge_base": tool_knowledge_base,
        "get_health_advice": tool_health_advice,
        "get_news": tool_news,
        "search_places": tool_places,
        "translate_text": tool_translator,
        "calculate": tool_calculator,
        "end_conversation": tool_end_conversation,
        "get_prayer_times": tool_prayer_times,
        "find_pharmacy": tool_pharmacy_locator,
        "estimate_taxi_fare": tool_taxi_estimate,
        "get_bus_schedule": tool_bus_schedule,
        "get_school_info": tool_school_info,
        "get_government_service_info": tool_government_services,
        "calculate_tax": tool_tax_calculator
    }
    
    # Chercher le module correspondant
    tool_module = tool_map.get(tool_name)
    
    if not tool_module:
        return {
            "status": "error",
            "message": f"Outil '{tool_name}' non trouvé. Outils disponibles: {', '.join(tool_map.keys())}"
        }
    
    try:
        # Exécuter l'outil via sa fonction execute()
        result = tool_module.execute(arguments)
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur lors de l'exécution de l'outil '{tool_name}': {str(e)}"
        }


# Export des fonctions principales
__all__ = ['get_tools_definition', 'execute_tool']
