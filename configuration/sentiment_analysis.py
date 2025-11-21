"""
Azure Text Analytics - Analyse de Sentiment
Module pour analyser les sentiments des conversations Voice Live
"""

import os
import logging
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration Azure Text Analytics
TEXT_ANALYTICS_ENDPOINT = os.getenv('TEXT_ANALYTICS_ENDPOINT')
TEXT_ANALYTICS_KEY = os.getenv('TEXT_ANALYTICS_KEY')
TEXT_ANALYTICS_API_VERSION = os.getenv('TEXT_ANALYTICS_API_VERSION', '2023-04-01')  # Version par défaut si non spécifiée

logger.info(f"Text Analytics configuré - Endpoint: {TEXT_ANALYTICS_ENDPOINT}, API Version: {TEXT_ANALYTICS_API_VERSION}")


def analyze_sentiment(messages: List[str], language: str = "fr") -> Dict:
    """
    Analyse le sentiment d'une liste de messages
    
    Args:
        messages (list): Liste des messages à analyser
        language (str): Code langue ISO 639-1 (défaut: "fr")
        
    Returns:
        dict: Analyse de sentiment avec scores
        {
            "sentiment": "positive" | "neutral" | "negative" | "mixed",
            "positive": 0.0-1.0,
            "neutral": 0.0-1.0,
            "negative": 0.0-1.0
        }
    """
    if not TEXT_ANALYTICS_ENDPOINT or not TEXT_ANALYTICS_KEY:
        logger.warning("⚠️ Text Analytics non configuré - utilisation de sentiment par défaut")
        return {
            "sentiment": "neutral",
            "positive": 0.33,
            "neutral": 0.34,
            "negative": 0.33,
            "warning": "Text Analytics non configuré"
        }
    
    try:
        from azure.ai.textanalytics import TextAnalyticsClient
        from azure.core.credentials import AzureKeyCredential
        
        # Initialiser le client
        client = TextAnalyticsClient(
            endpoint=TEXT_ANALYTICS_ENDPOINT,
            credential=AzureKeyCredential(TEXT_ANALYTICS_KEY)
        )
        
        # Filtrer les messages vides et limiter la longueur
        valid_messages = [msg for msg in messages if msg and msg.strip()]
        
        if not valid_messages:
            logger.warning("⚠️ Aucun message valide pour l'analyse de sentiment")
            return {
                "sentiment": "neutral",
                "positive": 0.0,
                "neutral": 1.0,
                "negative": 0.0,
                "warning": "Aucun message à analyser"
            }
        
        # Combiner tous les messages en un seul texte (limité à 5120 caractères par document)
        combined_text = " ".join(valid_messages)[:5120]
        
        # Analyser le sentiment
        documents = [combined_text]
        response = client.analyze_sentiment(documents=documents, language=language)
        
        # Extraire les résultats
        result = response[0]
        
        if result.is_error:
            logger.error(f"❌ Erreur Text Analytics: {result.error}")
            return {
                "sentiment": "neutral",
                "positive": 0.33,
                "neutral": 0.34,
                "negative": 0.33,
                "error": str(result.error)
            }
        
        # Calculer le score global moyen
        confidence_scores = result.confidence_scores
        
        sentiment_result = {
            "sentiment": result.sentiment,
            "positive": round(confidence_scores.positive, 2),
            "neutral": round(confidence_scores.neutral, 2),
            "negative": round(confidence_scores.negative, 2)
        }
        
        logger.info(f"✅ Sentiment analysé: {sentiment_result['sentiment']} (pos:{sentiment_result['positive']}, neu:{sentiment_result['neutral']}, neg:{sentiment_result['negative']})")
        
        return sentiment_result
        
    except ImportError:
        logger.error("❌ azure-ai-textanalytics non installé - pip install azure-ai-textanalytics")
        return {
            "sentiment": "neutral",
            "positive": 0.33,
            "neutral": 0.34,
            "negative": 0.33,
            "error": "azure-ai-textanalytics package manquant"
        }
    
    except Exception as e:
        logger.exception(f"❌ Erreur lors de l'analyse de sentiment: {e}")
        return {
            "sentiment": "neutral",
            "positive": 0.33,
            "neutral": 0.34,
            "negative": 0.33,
            "error": str(e)
        }


def analyze_conversation_sentiments(messages: List[Dict]) -> Dict:
    """
    Analyse les sentiments séparés pour les messages user et assistant
    
    Args:
        messages (list): Liste des messages de conversation
            Format: [{"type": "user", "content": "..."}, {"type": "agent", "content": "..."}]
            OU [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            
    Returns:
        dict: Sentiments user et assistant
        {
            "user_sentiment_analysis": {
                "sentiment": "positive",
                "positive": 0.89,
                "neutral": 0.08,
                "negative": 0.03
            },
            "assistant_sentiment_analysis": {
                "sentiment": "positive",
                "positive": 0.92,
                "neutral": 0.07,
                "negative": 0.01
            }
        }
    """
    # Séparer les messages user et assistant
    user_messages = []
    assistant_messages = []
    
    for msg in messages:
        # Support des deux formats: 'type' (nouveau) et 'role' (ancien)
        msg_type = msg.get('type', msg.get('role', ''))
        content = msg.get('content', '')
        
        if msg_type == 'user' and content:
            user_messages.append(content)
        elif msg_type in ['agent', 'assistant'] and content:
            assistant_messages.append(content)
    
    logger.info(f"📊 Analyse de sentiment: {len(user_messages)} messages user, {len(assistant_messages)} messages assistant")
    
    # Analyser les sentiments
    user_sentiment = analyze_sentiment(user_messages) if user_messages else {
        "sentiment": "neutral",
        "positive": 0.0,
        "neutral": 1.0,
        "negative": 0.0,
        "warning": "Aucun message utilisateur"
    }
    
    assistant_sentiment = analyze_sentiment(assistant_messages) if assistant_messages else {
        "sentiment": "neutral",
        "positive": 0.0,
        "neutral": 1.0,
        "negative": 0.0,
        "warning": "Aucun message assistant"
    }
    
    return {
        "user_sentiment_analysis": user_sentiment,
        "assistant_sentiment_analysis": assistant_sentiment
    }


if __name__ == "__main__":
    # Test du module
    print("=== Test Azure Text Analytics ===\n")
    
    # Test 1: Sentiment positif
    positive_messages = [
        "Bonjour, je suis très content de votre service !",
        "Merci beaucoup, c'est parfait !",
        "Excellente assistance, je recommande vivement."
    ]
    
    result = analyze_sentiment(positive_messages)
    print("Test 1 - Messages positifs:")
    print(f"  Sentiment: {result['sentiment']}")
    print(f"  Scores: pos={result['positive']}, neu={result['neutral']}, neg={result['negative']}")
    print()
    
    # Test 2: Sentiment négatif
    negative_messages = [
        "Je ne suis pas satisfait du tout.",
        "C'est vraiment décevant.",
        "Je suis très mécontent de ce service."
    ]
    
    result = analyze_sentiment(negative_messages)
    print("Test 2 - Messages négatifs:")
    print(f"  Sentiment: {result['sentiment']}")
    print(f"  Scores: pos={result['positive']}, neu={result['neutral']}, neg={result['negative']}")
    print()
    
    # Test 3: Conversation complète
    conversation = [
        {"role": "user", "content": "Bonjour, je voudrais réserver un vol"},
        {"role": "assistant", "content": "Bonjour ! Je serais ravi de vous aider avec votre réservation."},
        {"role": "user", "content": "Parfait, merci beaucoup !"},
        {"role": "assistant", "content": "Avec plaisir ! N'hésitez pas si vous avez d'autres questions."}
    ]
    
    result = analyze_conversation_sentiments(conversation)
    print("Test 3 - Conversation complète:")
    print(f"  User: {result['user_sentiment_analysis']['sentiment']} (pos={result['user_sentiment_analysis']['positive']})")
    print(f"  Assistant: {result['assistant_sentiment_analysis']['sentiment']} (pos={result['assistant_sentiment_analysis']['positive']})")
