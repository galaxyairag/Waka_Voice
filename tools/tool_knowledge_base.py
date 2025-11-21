#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tool: Knowledge Base Search (Custom API)
Description: Recherche vectorielle dans une base de données via API custom Waka
API: https://www.waka.digital/api/kbsearch
Retourne: Les 7 chunks les plus pertinents pour le message utilisateur
"""

import requests


def get_tool_definition():
    """
    Retourne la définition du tool pour knowledge base search.
    """
    return {
        "type": "function",
        "name": "search_knowledge_base",
        "description": """Effectue une recherche vectorielle dans la base de connaissances Waka Moove BK. 
            Utilise l'API custom www.waka.digital/api/kbsearch pour trouver les informations les plus pertinentes 
            par rapport au message de l'utilisateur. Retourne les 7 meilleurs chunks (extraits) de la base de données.
            Utile pour répondre aux questions sur Waka Moove BK avec contexte précis.""",
        "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message ou question de l'utilisateur pour la recherche vectorielle."
                    }
            },
            "required": ["message"]
        }
    }
def search_knowledge_base(message):
    """
    Effectue une recherche vectorielle dans la base de connaissances.
    
    Args:
        message (str): Message ou question de l'utilisateur
    
    Returns:
        dict: Résultats avec les 7 chunks les plus pertinents
    """
    
    if not message or not message.strip():
        return {
            "status": "error",
            "message": "❌ Le message ne peut pas être vide."
        }
    
    # Configuration de l'API
    api_url = "https://www.waka.digital/api/kbsearch"
    
    # Données à envoyer
    payload = {
        "message": message.strip(),
        "projet": "waka_moove-bk"
    }
    
    try:
        # Appel API
        response = requests.post(
            api_url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=30
        )
        
        response.raise_for_status()
        
        # Récupération des résultats
        result_data = response.json()
        
        # Vérification de la structure de réponse
        if not result_data:
            return {
                "status": "success",
                "total_chunks": 0,
                "message": "Aucun résultat trouvé dans la base de connaissances.",
                "chunks": []
            }
        
        # Extraction des chunks (adapter selon la structure réelle de l'API)
        # Hypothèse: l'API retourne une liste de chunks ou un objet avec clé "chunks", "results", "data", etc.
        chunks = []
        
        if isinstance(result_data, list):
            chunks = result_data[:7]  # Limiter à 7 chunks
        elif isinstance(result_data, dict):
            # Essayer différentes clés possibles
            for key in ["chunks", "results", "data", "matches", "items"]:
                if key in result_data:
                    chunks = result_data[key][:7]
                    break
            
            # Si aucune clé standard, prendre tout le dict comme résultat
            if not chunks and result_data:
                chunks = [result_data]
        
        # Formatage des chunks
        formatted_chunks = []
        for i, chunk in enumerate(chunks, 1):
            if isinstance(chunk, dict):
                formatted_chunk = {
                    "rank": i,
                    "content": chunk.get("content") or chunk.get("text") or chunk.get("chunk") or str(chunk),
                    "score": chunk.get("score") or chunk.get("similarity") or chunk.get("relevance"),
                    "source": chunk.get("source") or chunk.get("document") or chunk.get("file"),
                    "metadata": chunk.get("metadata") or {}
                }
            elif isinstance(chunk, str):
                formatted_chunk = {
                    "rank": i,
                    "content": chunk,
                    "score": None,
                    "source": None,
                    "metadata": {}
                }
            else:
                formatted_chunk = {
                    "rank": i,
                    "content": str(chunk),
                    "score": None,
                    "source": None,
                    "metadata": {}
                }
            
            formatted_chunks.append(formatted_chunk)
        
        return {
            "status": "success",
            "total_chunks": len(formatted_chunks),
            "query": message,
            "project": "waka_moove-bk",
            "chunks": formatted_chunks
        }
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            return {
                "status": "error",
                "message": f"❌ Requête invalide (400): {e.response.text}"
            }
        elif e.response.status_code == 404:
            return {
                "status": "error",
                "message": "❌ API non trouvée (404). Vérifiez l'URL: www.waka.digital/api/kbsearch"
            }
        elif e.response.status_code == 500:
            return {
                "status": "error",
                "message": f"❌ Erreur serveur (500): {e.response.text}"
            }
        else:
            return {
                "status": "error",
                "message": f"❌ Erreur HTTP {e.response.status_code}: {e.response.text}"
            }
    
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "❌ Délai d'attente dépassé (30s). Le serveur ne répond pas."
        }
    
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "message": "❌ Impossible de se connecter à www.waka.digital. Vérifiez votre connexion internet."
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"❌ Erreur de connexion: {str(e)}"
        }
    
    except ValueError as e:
        return {
            "status": "error",
            "message": f"❌ Erreur de parsing JSON: {str(e)}"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Erreur inattendue: {str(e)}"
        }


def execute(params):
    """
    Point d'entrée pour l'exécution du tool.
    """
    message = params.get("message", "")
    return search_knowledge_base(message)


# Test direct du script
if __name__ == "__main__":
    print("Test: Recherche vectorielle dans la base de connaissances Waka Moove BK")
    print("-" * 80)
    
    test_message = "Comment fonctionne le système de réservation?"
    
    print(f"Message: {test_message}\n")
    
    result = search_knowledge_base(test_message)
    
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
