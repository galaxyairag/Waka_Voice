"""
Tool Agent Assistant - Chatbot RAG pour la configuration d'agents
Détecte les demandes de configuration, répond aux questions sur les paramètres,
et peut créer automatiquement un agent après 3 questions clés.
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

# ============================================================
# DOCUMENTATION COMPLÈTE DES PARAMÈTRES DE CONFIGURATION
# ============================================================

PARAMETERS_DOCUMENTATION = {
    "modeles": {
        "titre": "Modèles de Langage Disponibles",
        "description": "Les modèles GPT disponibles pour les agents vocaux",
        "parametres": {
            "gpt-4o-realtime-preview": {
                "nom": "GPT-4o Realtime Preview",
                "description": "Modèle le plus avancé pour les conversations complexes. Haute qualité de compréhension et génération.",
                "cas_usage": "Agents nécessitant une compréhension fine, support client complexe, assistants polyvalents",
                "capacite": 20,
                "recommande_pour": "Conversations naturelles et complexes"
            },
            "gpt-4o-mini-realtime-preview": {
                "nom": "GPT-4o Mini Realtime",
                "description": "Version allégée, plus rapide et économique. Idéal pour les tâches simples.",
                "cas_usage": "Agents simples, FAQ, confirmation de rendez-vous, volume élevé d'appels",
                "capacite": 6,
                "recommande_pour": "Tâches simples avec volume élevé"
            },
            "gpt-realtime": {
                "nom": "GPT Realtime Standard",
                "description": "Version standard équilibrée entre performance et coût.",
                "cas_usage": "Usage général, bon compromis qualité/prix",
                "capacite": 30,
                "recommande_pour": "Usage général"
            },
            "gpt-realtime-mini": {
                "nom": "GPT Realtime Mini",
                "description": "Version ultra-légère avec très haute capacité. Pour les déploiements massifs.",
                "cas_usage": "Très grands volumes, agents basiques, notifications",
                "capacite": 200,
                "recommande_pour": "Très hauts volumes"
            }
        }
    },

    "configuration_audio": {
        "titre": "Configuration Audio",
        "description": "Paramètres de qualité et traitement audio",
        "parametres": {
            "input_audio_sampling_rate": {
                "nom": "Taux d'échantillonnage",
                "description": "Fréquence d'échantillonnage audio en Hz. 24000 Hz est la valeur standard pour la voix.",
                "type": "number",
                "valeur_defaut": 24000,
                "valeurs_possibles": [8000, 16000, 24000, 44100, 48000],
                "conseil": "24000 Hz offre un bon équilibre qualité/performance pour la voix"
            },
            "input_audio_format": {
                "nom": "Format audio d'entrée",
                "description": "Format de codage audio pour l'entrée utilisateur",
                "type": "string",
                "valeur_defaut": "pcm16",
                "valeurs_possibles": ["pcm16", "g711_ulaw", "g711_alaw"],
                "conseil": "pcm16 pour la meilleure qualité, g711 pour la compatibilité téléphonie"
            },
            "output_audio_format": {
                "nom": "Format audio de sortie",
                "description": "Format de codage audio pour la voix de l'agent",
                "type": "string",
                "valeur_defaut": "pcm16",
                "valeurs_possibles": ["pcm16", "g711_ulaw", "g711_alaw"],
                "conseil": "Utiliser le même format que l'entrée pour éviter les conversions"
            },
            "echo_cancellation": {
                "nom": "Annulation d'écho",
                "description": "Active la suppression des échos lors des appels avec haut-parleurs",
                "type": "boolean",
                "valeur_defaut": True,
                "conseil": "Activer si les utilisateurs utilisent des haut-parleurs plutôt qu'un casque"
            },
            "noise_reduction": {
                "nom": "Réduction de bruit",
                "description": "Active la suppression du bruit de fond",
                "type": "boolean",
                "valeur_defaut": True,
                "conseil": "Activer pour les environnements bruyants (open space, extérieur)"
            }
        }
    },

    "detection_vocale": {
        "titre": "Détection de la Parole (VAD)",
        "description": "Voice Activity Detection - Paramètres pour détecter quand l'utilisateur parle",
        "parametres": {
            "vad_type": {
                "nom": "Type de VAD",
                "description": "Méthode de détection vocale",
                "type": "string",
                "valeur_defaut": "server_vad",
                "valeurs_possibles": ["server_vad", "none"],
                "conseil": "server_vad pour la détection automatique côté serveur"
            },
            "threshold": {
                "nom": "Seuil de détection",
                "description": "Sensibilité de détection de la voix (0.0 à 1.0). Plus bas = plus sensible.",
                "type": "number",
                "valeur_defaut": 0.5,
                "min": 0.0,
                "max": 1.0,
                "conseil": "0.3-0.4 pour voix faibles ou environnements calmes, 0.6-0.7 pour environnements bruyants"
            },
            "prefix_padding_ms": {
                "nom": "Padding préfixe (ms)",
                "description": "Temps capturé avant le début détecté de la parole, en millisecondes",
                "type": "number",
                "valeur_defaut": 300,
                "min": 100,
                "max": 500,
                "conseil": "300ms capture bien le début des phrases sans couper"
            },
            "speech_duration_ms": {
                "nom": "Durée minimale de parole (ms)",
                "description": "Durée minimale pour considérer qu'il y a parole active",
                "type": "number",
                "valeur_defaut": 100,
                "min": 50,
                "max": 200,
                "conseil": "100ms évite les faux positifs (bruits courts)"
            },
            "silence_duration_ms": {
                "nom": "Durée de silence (ms)",
                "description": "Durée de silence nécessaire pour considérer que l'utilisateur a fini de parler",
                "type": "number",
                "valeur_defaut": 500,
                "min": 300,
                "max": 1500,
                "conseil": "300-400ms pour conversations rapides, 700-1000ms pour support technique où les utilisateurs réfléchissent"
            }
        }
    },

    "configuration_voix": {
        "titre": "Configuration de la Voix de l'Agent",
        "description": "Paramètres de la voix synthétique Azure",
        "parametres": {
            "voice_name": {
                "nom": "Nom de la voix",
                "description": "Identifiant de la voix Azure Neural à utiliser",
                "type": "string",
                "valeur_defaut": "fr-FR-DeniseNeural",
                "exemples_fr": ["fr-FR-DeniseNeural", "fr-FR-HenriNeural", "fr-FR-AlainNeural", "fr-FR-BrigitteNeural"],
                "conseil": "DeniseNeural pour voix féminine professionnelle, HenriNeural pour voix masculine"
            },
            "voice_speed": {
                "nom": "Vitesse de la voix",
                "description": "Rapidité d'élocution (0.5 = lent, 1.0 = normal, 2.0 = rapide)",
                "type": "number",
                "valeur_defaut": 1.0,
                "min": 0.5,
                "max": 2.0,
                "conseil": "0.9 pour un ton posé et calme, 1.1 pour un ton dynamique"
            },
            "voice_pitch": {
                "nom": "Tonalité",
                "description": "Ajustement de la hauteur de voix en pourcentage (-20% à +20%)",
                "type": "number",
                "valeur_defaut": 0,
                "min": -20,
                "max": 20,
                "conseil": "Laisser à 0 sauf besoin spécifique"
            }
        }
    },

    "parametres_modele": {
        "titre": "Paramètres du Modèle de Langage",
        "description": "Contrôle du comportement génératif du modèle",
        "parametres": {
            "temperature": {
                "nom": "Température",
                "description": "Contrôle la créativité des réponses. 0 = déterministe, 1 = créatif",
                "type": "number",
                "valeur_defaut": 0.8,
                "min": 0.0,
                "max": 1.0,
                "conseil": "0.3-0.5 pour support technique précis, 0.7-0.9 pour assistants conversationnels"
            },
            "max_tokens": {
                "nom": "Tokens maximum",
                "description": "Limite maximale de tokens pour la réponse générée",
                "type": "number",
                "valeur_defaut": 1000,
                "min": 50,
                "max": 4096,
                "conseil": "500-800 pour réponses concises, 1000-2000 pour explications détaillées"
            },
            "top_p": {
                "nom": "Top P (Nucleus Sampling)",
                "description": "Probabilité cumulative pour la sélection de tokens",
                "type": "number",
                "valeur_defaut": 0.9,
                "min": 0.0,
                "max": 1.0,
                "conseil": "0.9 est une bonne valeur par défaut, réduire à 0.7 pour plus de focus"
            }
        }
    },

    "outils_disponibles": {
        "titre": "Outils (Tools) Disponibles",
        "description": "Fonctionnalités que l'agent peut utiliser pendant les conversations",
        "parametres": {
            "weather": {
                "nom": "Météo",
                "description": "Fournit les prévisions météorologiques pour une ville",
                "cas_usage": "Questions sur le temps, température, conditions météo"
            },
            "news": {
                "nom": "Actualités",
                "description": "Récupère les dernières actualités par catégorie",
                "cas_usage": "Questions sur l'actualité, nouvelles du jour"
            },
            "email": {
                "nom": "Email",
                "description": "Permet d'envoyer des emails",
                "cas_usage": "Envoyer confirmations, notifications par email"
            },
            "translator": {
                "nom": "Traducteur",
                "description": "Traduit du texte entre différentes langues",
                "cas_usage": "Traductions à la demande"
            },
            "search_web": {
                "nom": "Recherche Web",
                "description": "Effectue des recherches sur internet",
                "cas_usage": "Questions nécessitant des informations actualisées"
            },
            "places": {
                "nom": "Recherche de Lieux",
                "description": "Trouve des lieux à proximité (restaurants, pharmacies, etc.)",
                "cas_usage": "Trouver des commerces, services de proximité"
            },
            "flight_search": {
                "nom": "Recherche de Vols",
                "description": "Recherche des vols disponibles",
                "cas_usage": "Réservation de voyage, recherche de billets d'avion"
            },
            "flight_booking": {
                "nom": "Réservation de Vol",
                "description": "Permet de réserver un vol",
                "cas_usage": "Finalisation de réservation de vol"
            },
            "hotel_search": {
                "nom": "Recherche d'Hôtels",
                "description": "Recherche des hôtels disponibles",
                "cas_usage": "Trouver un hébergement"
            },
            "hotel_booking": {
                "nom": "Réservation d'Hôtel",
                "description": "Permet de réserver un hôtel",
                "cas_usage": "Finalisation de réservation d'hôtel"
            },
            "calculator": {
                "nom": "Calculatrice",
                "description": "Effectue des calculs mathématiques",
                "cas_usage": "Calculs, pourcentages, conversions"
            },
            "currency": {
                "nom": "Convertisseur de Devises",
                "description": "Convertit des montants entre devises",
                "cas_usage": "Conversion monétaire"
            },
            "health_advice": {
                "nom": "Conseils Santé",
                "description": "Fournit des conseils de santé généraux",
                "cas_usage": "Questions de bien-être général (non médical)"
            },
            "exercises": {
                "nom": "Exercices",
                "description": "Propose des programmes d'exercices",
                "cas_usage": "Fitness, exercices physiques"
            },
            "prayer_times": {
                "nom": "Horaires de Prière",
                "description": "Donne les horaires de prière",
                "cas_usage": "Heures de prière selon la localisation"
            },
            "pharmacy_locator": {
                "nom": "Pharmacies",
                "description": "Trouve les pharmacies, y compris celles de garde",
                "cas_usage": "Trouver une pharmacie ouverte"
            },
            "taxi_estimate": {
                "nom": "Estimation Taxi",
                "description": "Estime le coût d'une course en taxi",
                "cas_usage": "Prix estimé d'un trajet en taxi"
            },
            "bus_schedule": {
                "nom": "Horaires de Bus",
                "description": "Consulte les horaires de bus",
                "cas_usage": "Transport en commun"
            },
            "government_services": {
                "nom": "Services Gouvernementaux",
                "description": "Informations sur les démarches administratives",
                "cas_usage": "Papiers, documents officiels"
            },
            "school_info": {
                "nom": "Informations Scolaires",
                "description": "Renseignements sur les établissements scolaires",
                "cas_usage": "Écoles, inscriptions, calendrier scolaire"
            },
            "tax_calculator": {
                "nom": "Calculateur d'Impôts",
                "description": "Estime les impôts selon les revenus",
                "cas_usage": "Estimation fiscale"
            },
            "knowledge_base": {
                "nom": "Base de Connaissances",
                "description": "Recherche dans une base documentaire personnalisée",
                "cas_usage": "FAQ internes, documentation entreprise"
            },
            "cv_builder": {
                "nom": "Création de CV",
                "description": "Aide à créer un curriculum vitae",
                "cas_usage": "Génération de CV professionnel"
            },
            "end_conversation": {
                "nom": "Fin de Conversation",
                "description": "Termine proprement la conversation",
                "cas_usage": "Clôture de l'appel"
            }
        }
    },

    "prompt_systeme": {
        "titre": "Prompt Système",
        "description": "Instructions qui définissent le comportement de l'agent",
        "structure_recommandee": {
            "role": "Définir clairement le rôle de l'agent (ex: 'Tu es un assistant pour l'agence X')",
            "ton": "Spécifier le ton de communication (professionnel, amical, formel)",
            "missions": "Lister les missions principales de l'agent",
            "comportement": "Règles de comportement (salutation, personnalisation, limites)",
            "consignes": "Instructions spécifiques au contexte métier"
        },
        "conseils": [
            "Être précis et concis",
            "Éviter les instructions contradictoires",
            "Définir ce que l'agent NE doit PAS faire",
            "Inclure des exemples si nécessaire"
        ]
    }
}

# ============================================================
# QUESTIONS POUR LA CRÉATION AUTOMATIQUE D'AGENT
# ============================================================

CREATION_QUESTIONS = [
    {
        "id": "purpose",
        "question": "Quel est l'objectif principal de votre agent ? (ex: support client, prise de rendez-vous, information produit, assistant général...)",
        "champ_cible": "description",
        "obligatoire": True
    },
    {
        "id": "tone",
        "question": "Quel ton souhaitez-vous pour votre agent ? (professionnel, amical, formel, décontracté)",
        "champ_cible": "tone",
        "obligatoire": True,
        "valeurs_suggerees": ["professionnel", "amical", "formel", "decontracte"]
    },
    {
        "id": "tools",
        "question": "Quelles fonctionnalités votre agent doit-il avoir ? (ex: météo, email, recherche web, réservations...)",
        "champ_cible": "selected_tools",
        "obligatoire": False
    }
]


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def detect_creation_intent(message: str) -> bool:
    """
    Détecte si le message de l'utilisateur exprime une intention de créer un agent.

    Args:
        message: Message de l'utilisateur

    Returns:
        True si intention de création détectée
    """
    creation_keywords = [
        "créer un agent", "creer un agent",
        "nouveau agent", "nouvel agent",
        "configurer un agent",
        "faire un agent", "construire un agent",
        "créer un assistant", "creer un assistant",
        "je veux un agent", "je voudrais un agent",
        "mettre en place un agent",
        "déployer un agent", "deployer un agent",
        "créer mon agent", "creer mon agent"
    ]

    message_lower = message.lower()
    return any(keyword in message_lower for keyword in creation_keywords)


def detect_parameter_question(message: str) -> Optional[str]:
    """
    Détecte si le message est une question sur un paramètre de configuration.

    Args:
        message: Message de l'utilisateur

    Returns:
        Catégorie du paramètre ou None
    """
    message_lower = message.lower()

    # Mapping des mots-clés vers les catégories
    keyword_mapping = {
        "modeles": ["modèle", "modele", "model", "gpt", "realtime", "mini"],
        "configuration_audio": ["audio", "échantillonnage", "sampling", "format audio", "bruit", "écho", "echo"],
        "detection_vocale": ["vad", "détection", "detection", "silence", "seuil", "threshold", "parole"],
        "configuration_voix": ["voix", "voice", "vitesse", "speed", "tonalité", "pitch", "neural"],
        "parametres_modele": ["température", "temperature", "token", "top_p", "créativité"],
        "outils_disponibles": ["outil", "tool", "fonction", "météo", "email", "recherche", "réservation"],
        "prompt_systeme": ["prompt", "instruction", "comportement", "personnalité", "ton"]
    }

    for category, keywords in keyword_mapping.items():
        if any(kw in message_lower for kw in keywords):
            return category

    return None


def get_parameter_documentation(category: Optional[str] = None) -> str:
    """
    Retourne la documentation formatée des paramètres.

    Args:
        category: Catégorie spécifique ou None pour tout

    Returns:
        Documentation formatée en texte
    """
    if category and category in PARAMETERS_DOCUMENTATION:
        doc = PARAMETERS_DOCUMENTATION[category]
        result = f"## {doc['titre']}\n\n{doc['description']}\n\n"

        if 'parametres' in doc:
            for param_id, param_info in doc['parametres'].items():
                result += f"### {param_info.get('nom', param_id)}\n"
                result += f"- **Description**: {param_info.get('description', 'N/A')}\n"

                if 'valeur_defaut' in param_info:
                    result += f"- **Valeur par défaut**: {param_info['valeur_defaut']}\n"
                if 'valeurs_possibles' in param_info:
                    result += f"- **Valeurs possibles**: {', '.join(map(str, param_info['valeurs_possibles']))}\n"
                if 'conseil' in param_info:
                    result += f"- **Conseil**: {param_info['conseil']}\n"
                if 'cas_usage' in param_info:
                    result += f"- **Cas d'usage**: {param_info['cas_usage']}\n"

                result += "\n"

        return result
    else:
        # Retourner un résumé de toutes les catégories
        result = "# Documentation des Paramètres de Configuration\n\n"
        for cat_id, doc in PARAMETERS_DOCUMENTATION.items():
            result += f"## {doc['titre']}\n{doc['description']}\n\n"
        return result


def search_documentation(query: str) -> str:
    """
    Recherche dans la documentation (RAG simplifié).

    Args:
        query: Requête de recherche

    Returns:
        Extraits pertinents de la documentation
    """
    query_lower = query.lower()
    results = []

    # Recherche dans toutes les catégories
    for category_id, category in PARAMETERS_DOCUMENTATION.items():
        # Recherche dans le titre et la description de la catégorie
        if query_lower in category.get('titre', '').lower() or query_lower in category.get('description', '').lower():
            results.append(get_parameter_documentation(category_id))
            continue

        # Recherche dans les paramètres
        if 'parametres' in category:
            for param_id, param_info in category['parametres'].items():
                searchable_text = ' '.join([
                    str(param_info.get('nom', '')),
                    str(param_info.get('description', '')),
                    str(param_info.get('conseil', '')),
                    str(param_info.get('cas_usage', ''))
                ]).lower()

                if query_lower in searchable_text or param_id.lower() in query_lower:
                    results.append(f"**{param_info.get('nom', param_id)}**: {param_info.get('description', 'N/A')}")
                    if 'conseil' in param_info:
                        results.append(f"  → Conseil: {param_info['conseil']}")

    if results:
        return "\n\n".join(results[:5])  # Limiter à 5 résultats
    else:
        return "Aucune information trouvée pour cette recherche. Essayez avec d'autres termes."


def generate_agent_config_from_answers(answers: Dict[str, str]) -> Dict[str, Any]:
    """
    Génère une configuration d'agent Cosmos DB à partir des réponses utilisateur.

    Args:
        answers: Dictionnaire des réponses aux 3 questions

    Returns:
        Configuration d'agent conforme au schéma Cosmos DB
    """
    agent_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # Déterminer les outils à partir de la réponse
    tools_mapping = {
        "météo": "weather",
        "meteo": "weather",
        "email": "email",
        "recherche": "search_web",
        "web": "search_web",
        "traduction": "translator",
        "traduire": "translator",
        "vol": "flight_search",
        "avion": "flight_search",
        "hôtel": "hotel_search",
        "hotel": "hotel_search",
        "réservation": "flight_booking",
        "reservation": "flight_booking",
        "calcul": "calculator",
        "devise": "currency",
        "monnaie": "currency",
        "santé": "health_advice",
        "sante": "health_advice",
        "pharmacie": "pharmacy_locator",
        "taxi": "taxi_estimate",
        "bus": "bus_schedule",
        "prière": "prayer_times",
        "priere": "prayer_times",
        "actualité": "news",
        "actualites": "news",
        "news": "news",
        "lieu": "places",
        "restaurant": "places",
        "cv": "cv_builder"
    }

    selected_tools = ["end_conversation"]  # Toujours inclure
    tools_answer = answers.get("tools", "").lower()

    for keyword, tool_id in tools_mapping.items():
        if keyword in tools_answer and tool_id not in selected_tools:
            selected_tools.append(tool_id)

    # Générer le prompt système
    purpose = answers.get("purpose", "assistant général")
    tone = answers.get("tone", "professionnel")

    tone_instructions = {
        "professionnel": "Tu adoptes un ton professionnel et courtois. Tu vouvoies l'utilisateur.",
        "amical": "Tu adoptes un ton amical et chaleureux. Tu tutoies l'utilisateur si approprié.",
        "formel": "Tu adoptes un ton très formel et respectueux. Tu vouvoies systématiquement.",
        "decontracte": "Tu adoptes un ton décontracté et accessible. Tu tutoies l'utilisateur."
    }

    system_prompt = f"""## RÔLE
Tu es un assistant vocal intelligent pour {purpose}.

## TON
{tone_instructions.get(tone, tone_instructions['professionnel'])}

## COMPORTEMENT
- Salue l'utilisateur au premier message uniquement
- Sois concis et va droit au but
- Utilise les outils disponibles pour répondre aux demandes
- Si tu ne peux pas aider, propose des alternatives

## MISSIONS
- Répondre aux questions des utilisateurs
- Utiliser les outils pour effectuer des actions concrètes
- Assurer une expérience utilisateur fluide et agréable
"""

    # Construire la configuration complète
    config = {
        "id": agent_id,
        "agent_id": agent_id,
        "agent_name": f"Agent Assistant - {purpose[:30]}",
        "description": purpose,
        "status": "active",
        "created_at": now,
        "updated_at": now,
        "config_type": "voice_live",
        "model_id": "gpt-4o-realtime-preview",
        "model_name": "GPT-4o Realtime Preview",
        "model_family": "F1_Realtime",
        "current_step": 5,
        "voice_type": "azure",
        "voice_config": {
            "voice_name": "fr-FR-DeniseNeural",
            "voice_speed": 1.0,
            "voice_pitch": 0
        },
        "session_config": {
            "modalities": ["audio", "text"],
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "input_audio_sampling_rate": 24000,
            "input_audio_transcription": {
                "model": "whisper-1"
            },
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 500
            },
            "voice": {
                "name": "fr-FR-DeniseNeural",
                "speed": 1.0,
                "pitch": 0
            },
            "temperature": 0.8,
            "max_tokens": 1000,
            "top_p": 0.9
        },
        "selected_tools": selected_tools,
        "system_prompt": system_prompt,
        "metadata": {
            "created_by": "chatbot_assistant",
            "version": 1,
            "tone": tone,
            "auto_generated": True
        }
    }

    return config


# ============================================================
# CLASSE PRINCIPALE DU TOOL
# ============================================================

class AgentAssistantTool:
    """
    Tool de chatbot assistant pour la configuration d'agents.
    Gère le RAG sur la documentation et la création guidée d'agents.
    """

    def __init__(self):
        self.conversation_state = {}
        self.creation_in_progress = {}

    def process_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Traite un message utilisateur et retourne une réponse.

        Args:
            user_id: Identifiant de l'utilisateur
            message: Message de l'utilisateur

        Returns:
            Dictionnaire avec la réponse et éventuellement une configuration d'agent
        """
        # Initialiser l'état de conversation si nécessaire
        if user_id not in self.conversation_state:
            self.conversation_state[user_id] = {
                "creation_mode": False,
                "current_question": 0,
                "answers": {}
            }

        state = self.conversation_state[user_id]

        # Mode création en cours ?
        if state["creation_mode"]:
            return self._handle_creation_mode(user_id, message)

        # Détecter intention de création
        if detect_creation_intent(message):
            state["creation_mode"] = True
            state["current_question"] = 0
            state["answers"] = {}

            first_question = CREATION_QUESTIONS[0]
            return {
                "type": "creation_start",
                "response": f"Parfait ! Je vais vous aider à créer votre agent en 3 questions simples.\n\n**Question 1/3**: {first_question['question']}",
                "question_id": first_question["id"]
            }

        # Détecter question sur les paramètres
        category = detect_parameter_question(message)
        if category:
            doc = get_parameter_documentation(category)
            return {
                "type": "documentation",
                "response": doc,
                "category": category
            }

        # Recherche générale dans la documentation
        results = search_documentation(message)
        return {
            "type": "search",
            "response": results
        }

    def _handle_creation_mode(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Gère le mode création d'agent étape par étape.
        """
        state = self.conversation_state[user_id]
        current_q_index = state["current_question"]

        # Sauvegarder la réponse
        if current_q_index < len(CREATION_QUESTIONS):
            question = CREATION_QUESTIONS[current_q_index]
            state["answers"][question["id"]] = message

        # Passer à la question suivante
        state["current_question"] += 1

        # Vérifier si toutes les questions ont été posées
        if state["current_question"] >= len(CREATION_QUESTIONS):
            # Générer la configuration
            config = generate_agent_config_from_answers(state["answers"])

            # Réinitialiser l'état
            state["creation_mode"] = False
            state["current_question"] = 0
            state["answers"] = {}

            return {
                "type": "creation_complete",
                "response": f"""Excellent ! Voici la configuration de votre agent :

**Nom**: {config['agent_name']}
**Modèle**: {config['model_name']}
**Voix**: {config['voice_config']['voice_name']}
**Outils activés**: {', '.join(config['selected_tools'])}

L'agent est prêt à être sauvegardé. Voulez-vous le créer maintenant ?""",
                "agent_config": config
            }
        else:
            # Poser la question suivante
            next_question = CREATION_QUESTIONS[state["current_question"]]
            return {
                "type": "creation_question",
                "response": f"**Question {state['current_question'] + 1}/3**: {next_question['question']}",
                "question_id": next_question["id"]
            }

    def save_agent_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sauvegarde la configuration d'agent dans Cosmos DB.

        Args:
            config: Configuration de l'agent

        Returns:
            Résultat de la sauvegarde
        """
        try:
            from configuration.cosmos_config import save_agent_config

            saved_config = save_agent_config(config)
            logger.info(f"✅ Agent créé via chatbot: {saved_config['agent_id']}")

            return {
                "success": True,
                "agent_id": saved_config["agent_id"],
                "message": f"Agent '{saved_config['agent_name']}' créé avec succès !"
            }
        except Exception as e:
            logger.error(f"❌ Erreur création agent: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def reset_conversation(self, user_id: str):
        """Réinitialise l'état de conversation pour un utilisateur."""
        if user_id in self.conversation_state:
            del self.conversation_state[user_id]


# ============================================================
# DÉFINITION DU TOOL POUR L'API OPENAI
# ============================================================

def get_tool_definition():
    """
    Retourne la définition du tool pour l'API OpenAI Functions.
    """
    return {
        "type": "function",
        "function": {
            "name": "agent_assistant",
            "description": "Assistant pour répondre aux questions sur la configuration des agents vocaux et aider à créer de nouveaux agents. Utilise une base de connaissances sur les paramètres de configuration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["ask_question", "create_agent", "get_documentation"],
                        "description": "Action à effectuer: poser une question, créer un agent, ou obtenir la documentation"
                    },
                    "query": {
                        "type": "string",
                        "description": "La question ou requête de l'utilisateur"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["modeles", "configuration_audio", "detection_vocale", "configuration_voix", "parametres_modele", "outils_disponibles", "prompt_systeme"],
                        "description": "Catégorie de documentation à consulter"
                    }
                },
                "required": ["action"]
            }
        }
    }


# Instance singleton du tool
_tool_instance = None

def get_tool_instance() -> AgentAssistantTool:
    """Retourne l'instance singleton du tool."""
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = AgentAssistantTool()
    return _tool_instance


def execute_tool(action: str, query: str = None, category: str = None, user_id: str = "default") -> Dict[str, Any]:
    """
    Exécute le tool avec les paramètres donnés.

    Args:
        action: Action à effectuer
        query: Question ou requête
        category: Catégorie de documentation
        user_id: ID de l'utilisateur

    Returns:
        Résultat de l'exécution
    """
    tool = get_tool_instance()

    if action == "get_documentation":
        doc = get_parameter_documentation(category)
        return {"type": "documentation", "response": doc}

    elif action == "ask_question" and query:
        return tool.process_message(user_id, query)

    elif action == "create_agent" and query:
        # Démarrer le processus de création
        return tool.process_message(user_id, "créer un agent")

    else:
        return {"type": "error", "response": "Action non reconnue ou paramètres manquants"}


# Export pour le module tools
__all__ = [
    'AgentAssistantTool',
    'get_tool_definition',
    'get_tool_instance',
    'execute_tool',
    'PARAMETERS_DOCUMENTATION',
    'CREATION_QUESTIONS'
]
