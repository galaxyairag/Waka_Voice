"""
Service Chatbot Assistant avec Azure OpenAI et RAG
Intègre l'API RAG existante et Azure OpenAI avec tool de création d'agent
"""

import os
import json
import uuid
import logging
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION AZURE OPENAI
# ============================================================

AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_SUMMARY_ENDPOINT')
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_SUMMARY_KEY')
AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT', 'gpt-4o')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-08-01-preview')

# URL de l'API RAG existante
RAG_API_URL = os.getenv('RAG_API_URL', 'http://localhost:8000/api/rag/search')


# ============================================================
# TOOL DEFINITIONS POUR AZURE OPENAI
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_voice_agent",
            "description": "Crée un nouvel agent vocal dans Cosmos DB avec la configuration spécifiée. Utiliser uniquement quand l'utilisateur confirme explicitement vouloir créer l'agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Nom de l'agent (ex: 'Assistant Support Client')"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description de l'objectif de l'agent"
                    },
                    "tone": {
                        "type": "string",
                        "enum": ["professionnel", "amical", "formel", "decontracte"],
                        "description": "Ton de communication de l'agent"
                    },
                    "model_id": {
                        "type": "string",
                        "enum": ["gpt-4o-realtime-preview", "gpt-4o-mini-realtime-preview", "gpt-realtime", "gpt-realtime-mini"],
                        "description": "Modèle de langage à utiliser"
                    },
                    "voice_name": {
                        "type": "string",
                        "description": "Nom de la voix Azure (ex: 'fr-FR-DeniseNeural')"
                    },
                    "selected_tools": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Liste des outils à activer (weather, email, search_web, etc.)"
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Température du modèle (0.0-1.0)"
                    },
                    "silence_duration_ms": {
                        "type": "integer",
                        "description": "Durée de silence avant fin de tour (ms)"
                    },
                    "system_prompt": {
                        "type": "string",
                        "description": "Prompt système personnalisé (optionnel)"
                    }
                },
                "required": ["agent_name", "description", "tone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_configuration_help",
            "description": "Retourne de l'aide détaillée sur un paramètre de configuration spécifique",
            "parameters": {
                "type": "object",
                "properties": {
                    "parameter_name": {
                        "type": "string",
                        "description": "Nom du paramètre (temperature, silence_duration_ms, threshold, etc.)"
                    }
                },
                "required": ["parameter_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_tools",
            "description": "Liste tous les outils disponibles pour les agents vocaux",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_voices",
            "description": "Liste les voix Azure disponibles pour les agents",
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "description": "Code langue (fr-FR, en-US, etc.)"
                    }
                }
            }
        }
    }
]


# ============================================================
# SYSTÈME PROMPT POUR LE CHATBOT
# ============================================================

SYSTEM_PROMPT = """Tu es l'Assistant Waka, un expert en configuration d'agents vocaux IA pour la plateforme Waka AI Voice Live.

## TON RÔLE
- Aider les utilisateurs à comprendre les paramètres de configuration
- Répondre aux questions sur les fonctionnalités de l'application
- Guider les utilisateurs dans la création d'agents vocaux
- Créer des agents quand l'utilisateur le demande explicitement

## COMPORTEMENT
- Sois concis et direct dans tes réponses
- Utilise les documents de référence fournis pour répondre précisément
- Si tu n'as pas l'information, dis-le clairement
- Propose de créer un agent uniquement si l'utilisateur l'a demandé

## CRÉATION D'AGENT
Quand l'utilisateur veut créer un agent, pose ces 3 questions :
1. Quel est l'objectif/cas d'usage de l'agent ?
2. Quel ton souhaite-t-il ? (professionnel, amical, formel, décontracté)
3. Quelles fonctionnalités/outils sont nécessaires ?

Une fois les réponses obtenues, utilise le tool `create_voice_agent` pour créer l'agent.

## PARAMÈTRES CLÉS À CONNAÎTRE
- **temperature** : 0.3-0.5 pour précision, 0.7-0.9 pour créativité
- **silence_duration_ms** : 300-500ms conversations rapides, 700-1000ms réflexion
- **threshold** : Sensibilité VAD, 0.5 par défaut
- **voice_name** : fr-FR-DeniseNeural (femme), fr-FR-HenriNeural (homme)

## FORMAT DE RÉPONSE
- Réponds en français
- Utilise des listes pour les énumérations
- Mets en **gras** les termes importants
"""


# ============================================================
# DOCUMENTATION DES PARAMÈTRES (FALLBACK)
# ============================================================

PARAMETERS_HELP = {
    "temperature": {
        "description": "Contrôle la créativité des réponses du modèle",
        "type": "number",
        "range": "0.0 - 1.0",
        "default": 0.8,
        "conseil": "0.3-0.5 pour support technique précis, 0.7-0.9 pour conversations naturelles"
    },
    "silence_duration_ms": {
        "description": "Durée de silence (en millisecondes) avant de considérer que l'utilisateur a fini de parler",
        "type": "integer",
        "range": "300 - 1500",
        "default": 500,
        "conseil": "300-400ms pour conversations rapides, 700-1000ms pour support technique"
    },
    "threshold": {
        "description": "Seuil de détection vocale (VAD). Plus bas = plus sensible",
        "type": "number",
        "range": "0.0 - 1.0",
        "default": 0.5,
        "conseil": "0.3-0.4 environnements calmes, 0.6-0.7 environnements bruyants"
    },
    "prefix_padding_ms": {
        "description": "Temps capturé avant le début détecté de la parole",
        "type": "integer",
        "range": "100 - 500",
        "default": 300,
        "conseil": "300ms capture bien le début des phrases"
    },
    "max_tokens": {
        "description": "Limite maximale de tokens pour les réponses",
        "type": "integer",
        "range": "50 - 4096",
        "default": 1000,
        "conseil": "500-800 réponses concises, 1000-2000 explications détaillées"
    },
    "voice_speed": {
        "description": "Vitesse d'élocution de l'agent",
        "type": "number",
        "range": "0.5 - 2.0",
        "default": 1.0,
        "conseil": "0.9 ton posé, 1.1 ton dynamique"
    }
}

AVAILABLE_TOOLS = {
    "weather": "Prévisions météorologiques",
    "news": "Actualités du jour",
    "email": "Envoi d'emails",
    "translator": "Traduction de texte",
    "search_web": "Recherche sur internet",
    "places": "Recherche de lieux",
    "flight_search": "Recherche de vols",
    "flight_booking": "Réservation de vol",
    "hotel_search": "Recherche d'hôtels",
    "hotel_booking": "Réservation d'hôtel",
    "calculator": "Calculs mathématiques",
    "currency": "Conversion de devises",
    "health_advice": "Conseils santé généraux",
    "exercises": "Programmes d'exercices",
    "prayer_times": "Horaires de prière",
    "pharmacy_locator": "Trouver une pharmacie",
    "taxi_estimate": "Estimation course taxi",
    "bus_schedule": "Horaires de bus",
    "government_services": "Démarches administratives",
    "school_info": "Informations scolaires",
    "tax_calculator": "Calcul d'impôts",
    "knowledge_base": "Base de connaissances interne",
    "cv_builder": "Création de CV",
    "end_conversation": "Fin de conversation"
}

AVAILABLE_VOICES = {
    "fr-FR": [
        {"name": "fr-FR-DeniseNeural", "gender": "Female", "style": "Professionnel, chaleureux"},
        {"name": "fr-FR-HenriNeural", "gender": "Male", "style": "Professionnel, posé"},
        {"name": "fr-FR-AlainNeural", "gender": "Male", "style": "Mature, autoritaire"},
        {"name": "fr-FR-BrigitteNeural", "gender": "Female", "style": "Amical, dynamique"},
        {"name": "fr-FR-CelesteNeural", "gender": "Female", "style": "Jeune, moderne"},
        {"name": "fr-FR-ClaudeNeural", "gender": "Male", "style": "Conversationnel"}
    ],
    "en-US": [
        {"name": "en-US-JennyNeural", "gender": "Female", "style": "Professionnel"},
        {"name": "en-US-GuyNeural", "gender": "Male", "style": "Conversationnel"},
        {"name": "en-US-AriaNeural", "gender": "Female", "style": "Expressif"}
    ]
}


# ============================================================
# FONCTIONS D'EXÉCUTION DES TOOLS
# ============================================================

def execute_create_voice_agent(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crée un agent vocal dans Cosmos DB.
    """
    try:
        from configuration.cosmos_config import save_agent_config

        agent_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Construire le prompt système
        tone_prompts = {
            "professionnel": "Tu adoptes un ton professionnel et courtois. Tu vouvoies l'utilisateur.",
            "amical": "Tu adoptes un ton amical et chaleureux. Tu peux tutoyer si approprié.",
            "formel": "Tu adoptes un ton très formel et respectueux. Tu vouvoies systématiquement.",
            "decontracte": "Tu adoptes un ton décontracté et accessible."
        }

        tone = params.get('tone', 'professionnel')
        system_prompt = params.get('system_prompt') or f"""## RÔLE
Tu es un assistant vocal pour {params.get('description', 'aider les utilisateurs')}.

## TON
{tone_prompts.get(tone, tone_prompts['professionnel'])}

## COMPORTEMENT
- Salue l'utilisateur au premier message uniquement
- Sois concis et efficace
- Utilise les outils disponibles pour répondre aux demandes
"""

        # Mapping des tools
        tools_mapping = {
            "météo": "weather", "meteo": "weather", "weather": "weather",
            "email": "email", "mail": "email",
            "recherche": "search_web", "web": "search_web", "search_web": "search_web",
            "traduction": "translator", "translator": "translator",
            "vol": "flight_search", "avion": "flight_search", "flight_search": "flight_search",
            "hôtel": "hotel_search", "hotel": "hotel_search", "hotel_search": "hotel_search",
            "calcul": "calculator", "calculator": "calculator",
            "devise": "currency", "currency": "currency",
            "santé": "health_advice", "health_advice": "health_advice",
            "actualités": "news", "news": "news",
            "lieu": "places", "places": "places"
        }

        selected_tools = ["end_conversation"]
        for tool in params.get('selected_tools', []):
            mapped = tools_mapping.get(tool.lower(), tool)
            if mapped not in selected_tools:
                selected_tools.append(mapped)

        # Configuration complète
        config = {
            "id": agent_id,
            "agent_id": agent_id,
            "agent_name": params.get('agent_name', 'Nouvel Agent'),
            "description": params.get('description', ''),
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "config_type": "voice_live",
            "model_id": params.get('model_id', 'gpt-4o-realtime-preview'),
            "model_name": params.get('model_id', 'GPT-4o Realtime'),
            "model_family": "F1_Realtime",
            "current_step": 5,
            "voice_type": "azure",
            "voice_config": {
                "voice_name": params.get('voice_name', 'fr-FR-DeniseNeural'),
                "voice_speed": 1.0,
                "voice_pitch": 0
            },
            "session_config": {
                "modalities": ["audio", "text"],
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_sampling_rate": 24000,
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": params.get('silence_duration_ms', 500)
                },
                "voice": {
                    "name": params.get('voice_name', 'fr-FR-DeniseNeural'),
                    "speed": 1.0
                },
                "temperature": params.get('temperature', 0.8),
                "max_tokens": 1000
            },
            "selected_tools": selected_tools,
            "system_prompt": system_prompt,
            "instructions": system_prompt,
            "metadata": {
                "created_by": "chatbot_assistant",
                "version": 1,
                "tone": tone,
                "auto_generated": True
            }
        }

        # Sauvegarder
        saved = save_agent_config(config)

        logger.info(f"✅ Agent créé via chatbot: {agent_id}")

        return {
            "success": True,
            "agent_id": agent_id,
            "agent_name": config["agent_name"],
            "message": f"Agent '{config['agent_name']}' créé avec succès !",
            "url": f"/agents/call/{agent_id}"
        }

    except Exception as e:
        logger.exception("Erreur création agent via chatbot")
        return {
            "success": False,
            "error": str(e)
        }


def execute_get_configuration_help(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retourne l'aide sur un paramètre de configuration.
    """
    param_name = params.get('parameter_name', '').lower()

    if param_name in PARAMETERS_HELP:
        info = PARAMETERS_HELP[param_name]
        return {
            "parameter": param_name,
            "description": info["description"],
            "type": info["type"],
            "range": info.get("range", "N/A"),
            "default": info.get("default", "N/A"),
            "conseil": info.get("conseil", "")
        }
    else:
        return {
            "error": f"Paramètre '{param_name}' non trouvé",
            "available_parameters": list(PARAMETERS_HELP.keys())
        }


def execute_list_available_tools(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Liste tous les outils disponibles.
    """
    return {
        "tools": [{"id": k, "description": v} for k, v in AVAILABLE_TOOLS.items()],
        "count": len(AVAILABLE_TOOLS)
    }


def execute_list_available_voices(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Liste les voix disponibles.
    """
    language = params.get('language', 'fr-FR')
    voices = AVAILABLE_VOICES.get(language, AVAILABLE_VOICES.get('fr-FR', []))

    return {
        "language": language,
        "voices": voices,
        "count": len(voices)
    }


# Mapping des fonctions
TOOL_EXECUTORS = {
    "create_voice_agent": execute_create_voice_agent,
    "get_configuration_help": execute_get_configuration_help,
    "list_available_tools": execute_list_available_tools,
    "list_available_voices": execute_list_available_voices
}


# ============================================================
# SERVICE PRINCIPAL
# ============================================================

class ChatbotAssistantService:
    """
    Service de chatbot avec Azure OpenAI et RAG.
    """

    def __init__(self):
        if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_KEY:
            raise ValueError("Configuration Azure OpenAI manquante")

        self.client = AzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_KEY,
            api_version=AZURE_OPENAI_API_VERSION
        )

        # Historique des conversations par session
        self.conversations: Dict[str, List[Dict]] = {}

    def get_rag_context(self, query: str) -> List[Dict[str, Any]]:
        """
        Appelle l'API RAG pour obtenir les documents de référence.

        Args:
            query: Question de l'utilisateur

        Returns:
            Liste de documents avec chunks et URLs sources
        """
        try:
            response = requests.post(
                RAG_API_URL,
                json={"query": query},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('documents', [])
            else:
                logger.warning(f"RAG API returned {response.status_code}")
                return []

        except requests.exceptions.RequestException as e:
            logger.warning(f"RAG API unavailable: {e}")
            return []

    def format_rag_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Formate les documents RAG en contexte pour le prompt.
        """
        if not documents:
            return ""

        context_parts = ["## Documents de Référence\n"]

        for i, doc in enumerate(documents[:5], 1):  # Max 5 documents
            chunk = doc.get('chunk', doc.get('content', ''))
            source = doc.get('source_url', doc.get('url', 'Manuel Waka'))

            context_parts.append(f"### Source {i}: {source}\n{chunk}\n")

        return "\n".join(context_parts)

    def process_message(
        self,
        session_id: str,
        user_message: str,
        include_rag: bool = True
    ) -> Dict[str, Any]:
        """
        Traite un message utilisateur avec RAG et Azure OpenAI.

        Args:
            session_id: ID de session pour l'historique
            user_message: Message de l'utilisateur
            include_rag: Inclure la recherche RAG

        Returns:
            Réponse du chatbot avec éventuelles actions
        """
        # Initialiser l'historique si nécessaire
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        # Obtenir le contexte RAG
        rag_context = ""
        rag_documents = []
        if include_rag:
            rag_documents = self.get_rag_context(user_message)
            rag_context = self.format_rag_context(rag_documents)

        # Construire le message système avec contexte RAG
        system_message = SYSTEM_PROMPT
        if rag_context:
            system_message += f"\n\n{rag_context}"

        # Construire les messages
        messages = [{"role": "system", "content": system_message}]

        # Ajouter l'historique (max 10 derniers échanges)
        messages.extend(self.conversations[session_id][-20:])

        # Ajouter le message utilisateur
        messages.append({"role": "user", "content": user_message})

        try:
            # Appel Azure OpenAI avec tools
            response = self.client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1000
            )

            assistant_message = response.choices[0].message

            # Vérifier si un tool a été appelé
            tool_results = []
            if assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    logger.info(f"Tool appelé: {function_name} avec {function_args}")

                    # Exécuter le tool
                    if function_name in TOOL_EXECUTORS:
                        result = TOOL_EXECUTORS[function_name](function_args)
                        tool_results.append({
                            "tool": function_name,
                            "result": result
                        })

                        # Ajouter le résultat au contexte pour la réponse finale
                        messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [tool_call]
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result, ensure_ascii=False)
                        })

                # Obtenir la réponse finale après exécution des tools
                final_response = self.client.chat.completions.create(
                    model=AZURE_OPENAI_DEPLOYMENT,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )

                final_content = final_response.choices[0].message.content
            else:
                final_content = assistant_message.content

            # Mettre à jour l'historique
            self.conversations[session_id].append({
                "role": "user",
                "content": user_message
            })
            self.conversations[session_id].append({
                "role": "assistant",
                "content": final_content
            })

            return {
                "success": True,
                "response": final_content,
                "tool_results": tool_results,
                "rag_sources": [
                    {"url": d.get('source_url', d.get('url', '')), "title": d.get('title', 'Document')}
                    for d in rag_documents
                ] if rag_documents else []
            }

        except Exception as e:
            logger.exception("Erreur Azure OpenAI")
            return {
                "success": False,
                "error": str(e)
            }

    def reset_conversation(self, session_id: str):
        """Réinitialise l'historique d'une session."""
        if session_id in self.conversations:
            del self.conversations[session_id]


# Singleton
_service_instance: Optional[ChatbotAssistantService] = None

def get_chatbot_service() -> ChatbotAssistantService:
    """Retourne l'instance singleton du service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ChatbotAssistantService()
    return _service_instance
