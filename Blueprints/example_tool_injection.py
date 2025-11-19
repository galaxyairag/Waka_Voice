"""
Exemple d'intégration du Tool Injection Manager dans une conversation
Ce fichier montre comment utiliser le système d'injection dynamique
"""

from tool_injection_manager import ToolInjectionManager

# =============================================================================
# SIMULATION D'UNE CONVERSATION AVEC INJECTION DYNAMIQUE
# =============================================================================

def simulate_conversation():
    """
    Simule une conversation avec injection dynamique des instructions de tools
    """
    
    # 1. CONFIGURATION INITIALE (depuis la base de données de l'agent)
    print("=" * 80)
    print("CONFIGURATION DE L'AGENT")
    print("=" * 80)
    
    # Prompt initial (court, sans instructions détaillées)
    initial_prompt = """Tu es Waka AI, un assistant vocal amical.

TON RÔLE
Tu aides les utilisateurs avec leurs tâches quotidiennes.

RÈGLES GÉNÉRALES
- TOUJOURS informer avant d'utiliser un tool
- Être concis et clair
- Ne jamais inventer d'informations

TOOLS DISPONIBLES
Tu as accès à 3 tool(s) : Météo, Email, Calendrier
Les instructions détaillées seront fournies quand tu en auras besoin."""
    
    # Instructions détaillées (stockées séparément)
    tools_instructions = """INSTRUCTIONS TOOL MÉTÉO

Quand tu utilises le tool Météo :
1. AVANT : "Je vais consulter la météo pour [ville]"
2. UTILISER : weather_tool(city="Paris")
3. APRÈS : "Il fait actuellement 22°C à Paris avec un ciel dégagé"

INSTRUCTIONS TOOL EMAIL

PROCÉDURE STRICTE :
1. Demander d'épeler l'email lettre par lettre
2. Attendre "Terminé"
3. Répéter pour confirmation
4. AVANT : "J'utilise l'outil Email"
5. UTILISER : send_email(...)
6. APRÈS : "Email envoyé avec succès"

INSTRUCTIONS TOOL CALENDRIER

Pour les rendez-vous :
1. AVANT : "Je vais vérifier votre calendrier"
2. UTILISER : check_calendar(date="2024-01-15")
3. APRÈS : "Vous avez 3 rendez-vous ce jour"
"""
    
    selected_tools = ['weather', 'email', 'calendar']
    
    print(f"Prompt initial : {len(initial_prompt)} caractères")
    print(f"Instructions tools : {len(tools_instructions)} caractères")
    print(f"Tools sélectionnés : {selected_tools}")
    print()
    
    # 2. CRÉER LE MANAGER
    manager = ToolInjectionManager(tools_instructions, selected_tools)
    
    # 3. CONVERSATION
    print("=" * 80)
    print("CONVERSATION")
    print("=" * 80)
    
    conversation = []
    
    # Tour 1 : Demande météo
    print("\n--- Tour 1 ---")
    user_msg_1 = "Quel temps fait-il à Ouagadougou ?"
    print(f"👤 User: {user_msg_1}")
    
    # Détecter et injecter
    injection_1 = manager.inject_if_needed(user_msg_1, conversation)
    
    if injection_1:
        print(f"\n🔧 INJECTION (ajoutée au contexte):")
        print(injection_1[:200] + "...")
        print(f"   Total: {len(injection_1)} caractères")
        
        # Ajouter au contexte de conversation
        conversation.append({
            "role": "system",
            "content": injection_1
        })
    
    # Réponse de l'assistant
    assistant_response_1 = "Je vais consulter la météo pour Ouagadougou. [Utilise weather_tool] Il fait actuellement 35°C à Ouagadougou avec un ciel ensoleillé."
    conversation.append({
        "role": "user",
        "content": user_msg_1
    })
    conversation.append({
        "role": "assistant",
        "content": assistant_response_1
    })
    print(f"🤖 Assistant: {assistant_response_1}")
    
    # Tour 2 : Autre question météo (pas de ré-injection)
    print("\n--- Tour 2 ---")
    user_msg_2 = "Et la météo à Bobo-Dioulasso ?"
    print(f"👤 User: {user_msg_2}")
    
    injection_2 = manager.inject_if_needed(user_msg_2, conversation)
    
    if injection_2:
        print(f"\n🔧 INJECTION: {len(injection_2)} caractères")
    else:
        print("\n✅ Pas d'injection (tool météo déjà injecté)")
    
    conversation.append({
        "role": "user",
        "content": user_msg_2
    })
    assistant_response_2 = "Je vais consulter la météo pour Bobo-Dioulasso. [Utilise weather_tool] Il fait 32°C à Bobo-Dioulasso avec des nuages."
    conversation.append({
        "role": "assistant",
        "content": assistant_response_2
    })
    print(f"🤖 Assistant: {assistant_response_2}")
    
    # Tour 3 : Demande email (nouvelle injection)
    print("\n--- Tour 3 ---")
    user_msg_3 = "Envoie un email à mon patron pour dire que je suis en retard"
    print(f"👤 User: {user_msg_3}")
    
    injection_3 = manager.inject_if_needed(user_msg_3, conversation)
    
    if injection_3:
        print(f"\n🔧 INJECTION (ajoutée au contexte):")
        print(injection_3[:200] + "...")
        print(f"   Total: {len(injection_3)} caractères")
        
        conversation.append({
            "role": "system",
            "content": injection_3
        })
    
    conversation.append({
        "role": "user",
        "content": user_msg_3
    })
    assistant_response_3 = "D'accord, je vais vous aider. Veuillez épeler l'adresse email de votre patron lettre par lettre."
    conversation.append({
        "role": "assistant",
        "content": assistant_response_3
    })
    print(f"🤖 Assistant: {assistant_response_3}")
    
    # 4. STATISTIQUES FINALES
    print("\n" + "=" * 80)
    print("STATISTIQUES")
    print("=" * 80)
    
    total_chars = sum(len(msg["content"]) for msg in conversation)
    system_chars = sum(len(msg["content"]) for msg in conversation if msg["role"] == "system")
    
    print(f"Messages dans la conversation : {len(conversation)}")
    print(f"Total caractères : {total_chars}")
    print(f"Caractères système (injections) : {system_chars}")
    print(f"Tools injectés : {manager.injected_tools}")
    print(f"\n✅ Économie vs tout injecter au début : {len(tools_instructions) - system_chars} caractères")
    print(f"   (Instructions calendrier jamais injectées car jamais utilisées)")


# =============================================================================
# EXEMPLE D'INTÉGRATION DANS UNE ROUTE FLASK
# =============================================================================

def example_flask_integration():
    """
    Exemple de comment intégrer dans une route Flask
    """
    
    code_example = '''
from flask import Blueprint, request, jsonify, session
from tool_injection_manager import ToolInjectionManager

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint de chat avec injection dynamique"""
    
    data = request.json
    user_message = data.get('message')
    
    # 1. Récupérer la config de l'agent depuis la session ou DB
    agent_config = session.get('agent_config')
    initial_prompt = agent_config['system_prompt']  # Prompt court
    tools_instructions = agent_config['tools_instructions']  # Instructions détaillées
    selected_tools = agent_config['tools']
    
    # 2. Récupérer ou créer le manager
    if 'tool_manager' not in session:
        session['tool_manager'] = ToolInjectionManager(
            tools_instructions, 
            selected_tools
        )
    
    manager = session['tool_manager']
    
    # 3. Récupérer l'historique de conversation
    conversation_history = session.get('conversation', [])
    
    # 4. Détecter et injecter les instructions si nécessaire
    new_instructions = manager.inject_if_needed(user_message, conversation_history)
    
    # 5. Construire le contexte pour l'API
    messages = []
    
    # Prompt initial (seulement au premier message)
    if len(conversation_history) == 0:
        messages.append({
            "role": "system",
            "content": initial_prompt
        })
    
    # Historique
    messages.extend(conversation_history)
    
    # Injection dynamique (si détectée)
    if new_instructions:
        messages.append({
            "role": "system",
            "content": new_instructions
        })
        conversation_history.append({
            "role": "system",
            "content": new_instructions
        })
    
    # Message utilisateur
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    # 6. Appeler l'API OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages
    )
    
    assistant_message = response.choices[0].message.content
    
    # 7. Sauvegarder dans l'historique
    conversation_history.append({"role": "user", "content": user_message})
    conversation_history.append({"role": "assistant", "content": assistant_message})
    session['conversation'] = conversation_history
    
    # 8. Retourner la réponse
    return jsonify({
        "response": assistant_message,
        "tools_injected": list(manager.injected_tools)
    })
'''
    
    print("=" * 80)
    print("EXEMPLE D'INTÉGRATION FLASK")
    print("=" * 80)
    print(code_example)


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == "__main__":
    simulate_conversation()
    print("\n\n")
    example_flask_integration()
