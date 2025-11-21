"""
Cost Calculator - Calcul du coût des conversations Voice Live
Module pour calculer le coût basé sur la consommation de tokens
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


# ===================================================================
# TARIFICATION PAR CATÉGORIE DE MODÈLE
# ===================================================================

# Mapping direct: modèle → formule de pricing
MODEL_PRICING_MAP = {
    # PRO models
    "gpt-realtime": "pro",
    "gpt-4o": "pro",
    "gpt-4o-realtime": "pro",
    "gpt-4o-realtime-preview": "pro",
    "gpt-4.1": "pro",
    "gpt-5": "pro",
    "gpt-5-chat": "pro",
    
    # BASIC models
    "gpt-realtime-mini": "basic",
    "gpt-4o-mini": "basic",
    "gpt-4o-mini-realtime": "basic",
    "gpt-4o-mini-realtime-preview": "basic",
    "gpt-4.1-mini": "basic",
    "gpt-5-mini": "basic",
    
    # LITE models
    "gpt-5-nano": "lite",
    "phi4-mm-realtime": "lite",
    "phi4-mini": "lite"
}

# Classification des modèles par catégorie
MODEL_CATEGORIES = {
    "pro": [
        "gpt-realtime",
        "gpt-4o",
        "gpt-4o-realtime-preview",
        "gpt-4.1",
        "gpt-5",
        "gpt-5-chat"
    ],
    "basic": [
        "gpt-realtime-mini",
        "gpt-4o-mini",
        "gpt-4o-mini-realtime-preview",
        "gpt-4.1-mini",
        "gpt-5-mini"
    ],
    "lite": [
        "gpt-5-nano",
        "phi4-mm-realtime",
        "phi4-mini"
    ]
}

# Prix par token (en USD)
PRICING = {
    "pro": {
        "inputs_text_tokens": 0.0000055,
        "inputs_cached_tokens": 0.00000275,
        "inputs_audio_tokens": 0.000017,
        "outputs_text_tokens": 0.000022,
        "outputs_audio_tokens": 0.000055
    },
    "basic": {
        "inputs_text_tokens": 0.00000066,
        "inputs_cached_tokens": 0.00000033,
        "inputs_audio_tokens": 0.000011,
        "outputs_text_tokens": 0.00000264,
        "outputs_audio_tokens": 0.000022
    },
    "lite": {
        "inputs_text_tokens": 0.00000008,
        "inputs_cached_tokens": 0.00000004,
        "inputs_audio_tokens": 0.000004,
        "outputs_text_tokens": 0.00000032,
        "outputs_audio_tokens": 0.000033
    }
}


def get_model_category(model: str) -> str:
    """
    Détermine la catégorie d'un modèle
    
    Args:
        model (str): Nom du modèle (ex: "gpt-4o-realtime-preview-2024-10-01")
        
    Returns:
        str: Catégorie ("pro", "basic", "lite")
    """
    # Normaliser le nom du modèle
    model_lower = model.lower().strip()
    
    # 1. Vérifier d'abord le mapping direct (plus rapide et sans ambiguïté)
    if model_lower in MODEL_PRICING_MAP:
        category = MODEL_PRICING_MAP[model_lower]
        logger.debug(f"📊 Modèle '{model}' → Catégorie '{category}' (mapping direct)")
        return category
    
    # 2. Si pas trouvé, essayer de matcher avec les patterns
    # Trier les patterns par longueur décroissante pour matcher les plus spécifiques d'abord
    for category, models in MODEL_CATEGORIES.items():
        sorted_patterns = sorted(models, key=len, reverse=True)
        for model_pattern in sorted_patterns:
            if model_pattern.lower() in model_lower:
                logger.debug(f"📊 Modèle '{model}' → Catégorie '{category}' (pattern: {model_pattern})")
                return category
    
    # 3. Par défaut: pro (coût le plus élevé par sécurité)
    logger.warning(f"⚠️ Modèle '{model}' non reconnu, utilisation de la catégorie 'pro' par défaut")
    return "pro"


def calculate_cost(model: str, tokens: Dict[str, int], pricing_tier: str | None = None) -> float:
    """
    Calcule le coût d'une conversation
    
    Args:
        model (str): Nom du modèle utilisé
        tokens (dict): Dictionnaire des tokens consommés
            {
                "inputs_text_tokens": int,
                "inputs_cached_tokens": int,
                "inputs_audio_tokens": int,
                "outputs_text_tokens": int,
                "outputs_audio_tokens": int
            }
            
    Returns:
        float: Coût total en USD (6 décimales)
    """
    # Déterminer la catégorie du modèle, sauf si un niveau explicite est fourni
    category = pricing_tier or get_model_category(model)
    
    # Récupérer la tarification
    pricing = PRICING[category]
    
    # Extraire les tokens (avec valeurs par défaut à 0)
    inputs_text = tokens.get("inputs_text_tokens", 0)
    inputs_cached = tokens.get("inputs_cached_tokens", 0)
    inputs_audio = tokens.get("inputs_audio_tokens", 0)
    outputs_text = tokens.get("outputs_text_tokens", 0)
    outputs_audio = tokens.get("outputs_audio_tokens", 0)
    
    # Calculer le coût
    cost = (
        inputs_text * pricing["inputs_text_tokens"] +
        inputs_cached * pricing["inputs_cached_tokens"] +
        inputs_audio * pricing["inputs_audio_tokens"] +
        outputs_text * pricing["outputs_text_tokens"] +
        outputs_audio * pricing["outputs_audio_tokens"]
    )
    
    # Arrondir à 6 décimales
    cost_rounded = round(cost, 6)
    
    logger.info(f"💰 Coût calculé: ${cost_rounded} (catégorie: {category})")
    logger.debug(f"   Détails: in_text={inputs_text}, in_cached={inputs_cached}, in_audio={inputs_audio}, out_text={outputs_text}, out_audio={outputs_audio}")
    
    return cost_rounded


def calculate_cost_breakdown(model: str, tokens: Dict[str, int], pricing_tier: str | None = None) -> Dict:
    """
    Calcule le coût avec détails par type de token
    
    Args:
        model (str): Nom du modèle utilisé
        tokens (dict): Dictionnaire des tokens consommés
        
    Returns:
        dict: Détails du coût
        {
            "total_cost": float,
            "category": str,
            "breakdown": {
                "inputs_text": {"tokens": int, "cost": float},
                "inputs_cached": {"tokens": int, "cost": float},
                "inputs_audio": {"tokens": int, "cost": float},
                "outputs_text": {"tokens": int, "cost": float},
                "outputs_audio": {"tokens": int, "cost": float}
            }
        }
    """
    # Déterminer la catégorie du modèle, sauf si un niveau explicite est fourni
    category = pricing_tier or get_model_category(model)
    
    # Récupérer la tarification
    pricing = PRICING[category]
    
    # Calculer chaque composant
    breakdown = {}
    total = 0.0
    
    for token_type in ["inputs_text_tokens", "inputs_cached_tokens", "inputs_audio_tokens", 
                       "outputs_text_tokens", "outputs_audio_tokens"]:
        token_count = tokens.get(token_type, 0)
        token_cost = token_count * pricing[token_type]
        total += token_cost
        
        breakdown[token_type.replace("_tokens", "")] = {
            "tokens": token_count,
            "cost": round(token_cost, 6)
        }
    
    return {
        "total_cost": round(total, 6),
        "category": category,
        "breakdown": breakdown
    }


if __name__ == "__main__":
    # Tests du module
    print("=== Test Cost Calculator ===\n")
    
    # Test 1: Modèle Pro (gpt-4o-realtime-preview)
    print("Test 1 - Modèle Pro (gpt-4o-realtime-preview-2024-10-01)")
    tokens_pro = {
        "inputs_text_tokens": 1100,
        "inputs_cached_tokens": 0,
        "inputs_audio_tokens": 150,
        "outputs_text_tokens": 650,
        "outputs_audio_tokens": 240
    }
    
    cost = calculate_cost("gpt-4o-realtime-preview-2024-10-01", tokens_pro)
    print(f"  Coût: ${cost}")
    
    breakdown = calculate_cost_breakdown("gpt-4o-realtime-preview-2024-10-01", tokens_pro)
    print(f"  Catégorie: {breakdown['category']}")
    print(f"  Détails:")
    for key, value in breakdown['breakdown'].items():
        print(f"    {key}: {value['tokens']} tokens = ${value['cost']}")
    print()
    
    # Test 2: Modèle Basic (gpt-4o-mini-realtime-preview)
    print("Test 2 - Modèle Basic (gpt-4o-mini-realtime-preview)")
    tokens_basic = {
        "inputs_text_tokens": 2000,
        "inputs_cached_tokens": 500,
        "inputs_audio_tokens": 300,
        "outputs_text_tokens": 1200,
        "outputs_audio_tokens": 400
    }
    
    cost = calculate_cost("gpt-4o-mini-realtime-preview", tokens_basic)
    print(f"  Coût: ${cost}")
    
    breakdown = calculate_cost_breakdown("gpt-4o-mini-realtime-preview", tokens_basic)
    print(f"  Catégorie: {breakdown['category']}")
    print(f"  Total: ${breakdown['total_cost']}")
    print()
    
    # Test 3: Modèle Lite (phi4-mini)
    print("Test 3 - Modèle Lite (phi4-mini)")
    tokens_lite = {
        "inputs_text_tokens": 5000,
        "inputs_cached_tokens": 1000,
        "inputs_audio_tokens": 800,
        "outputs_text_tokens": 3000,
        "outputs_audio_tokens": 600
    }
    
    cost = calculate_cost("phi4-mini", tokens_lite)
    print(f"  Coût: ${cost}")
    
    breakdown = calculate_cost_breakdown("phi4-mini", tokens_lite)
    print(f"  Catégorie: {breakdown['category']}")
    print(f"  Total: ${breakdown['total_cost']}")
    print()
    
    # Test 4: Modèle inconnu (par défaut Pro)
    print("Test 4 - Modèle inconnu (par défaut Pro)")
    cost = calculate_cost("unknown-model-xyz", tokens_pro)
    print(f"  Coût: ${cost}")
