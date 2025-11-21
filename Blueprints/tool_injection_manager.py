"""
Tool Injection Manager - Gestion dynamique des instructions de tools
Injecte les instructions détaillées uniquement quand un tool est détecté en conversation
"""

class ToolInjectionManager:
    """
    Gère l'injection dynamique des instructions de tools dans la conversation
    """
    
    def __init__(self, tools_instructions: str, selected_tools: list):
        """
        Initialise le manager avec les instructions des tools
        
        Args:
            tools_instructions: Instructions détaillées de tous les tools sélectionnés
            selected_tools: Liste des tools sélectionnés (ex: ['weather', 'email'])
        """
        self.tools_instructions = tools_instructions
        self.selected_tools = selected_tools
        self.injected_tools = set()  # Track quels tools ont déjà été injectés
        
        # Parse les instructions par tool
        self.tools_map = self._parse_instructions()
    
    def _parse_instructions(self) -> dict:
        """
        Parse les instructions pour séparer chaque tool
        
        Returns:
            Dict avec {tool_name: instructions}
        """
        tools_map = {}
        
        if not self.tools_instructions:
            return tools_map
        
        # Séparer par "INSTRUCTIONS TOOL"
        sections = self.tools_instructions.split('INSTRUCTIONS TOOL')
        
        for section in sections[1:]:  # Skip first empty section
            lines = section.strip().split('\n', 1)
            if len(lines) >= 2:
                tool_name = lines[0].strip().lower()
                instructions = lines[1].strip()
                
                # Map tool names (ex: "MÉTÉO" -> "weather")
                tool_key = self._normalize_tool_name(tool_name)
                if tool_key:
                    tools_map[tool_key] = f"INSTRUCTIONS TOOL {lines[0]}\n\n{instructions}"
        
        return tools_map
    
    def _normalize_tool_name(self, name: str) -> str:
        """
        Normalise le nom du tool pour correspondre aux clés
        
        Args:
            name: Nom du tool (ex: "MÉTÉO", "EMAIL")
        
        Returns:
            Clé normalisée (ex: "weather", "email")
        """
        name = name.lower().strip()
        
        mapping = {
            'météo': 'weather',
            'email': 'email',
            'calendrier': 'calendar',
            'cv': 'cv_builder',
            'recherche de vols': 'flight_search',
            'réservation hôtel': 'hotel_booking',
            'nutrition': 'nutrition',
            'fitness': 'fitness',
            'actualités': 'news',
            'traduction': 'translation',
            'calculatrice': 'calculator',
            'rappels': 'reminder'
        }
        
        return mapping.get(name)
    
    def detect_tool_usage(self, message: str) -> list:
        """
        Détecte quels tools sont mentionnés dans un message
        
        Args:
            message: Message de l'utilisateur ou de l'assistant
        
        Returns:
            Liste des tools détectés
        """
        detected = []
        message_lower = message.lower()
        
        # Keywords par tool
        tool_keywords = {
            'weather': ['météo', 'température', 'temps', 'temps qu\'il fait', 'prévisions', 'quel temps'],
            'email': ['email', 'mail', 'envoyer un message', 'écrire à', 'envoie'],
            'calendar': ['calendrier', 'rendez-vous', 'agenda', 'événement'],
            'cv_builder': ['cv', 'curriculum', 'créer mon cv', 'préparer cv'],
            'flight_search': ['vol', 'avion', 'billet', 'voyager'],
            'hotel_booking': ['hôtel', 'réservation', 'chambre'],
            'nutrition': ['nutrition', 'calories', 'aliment', 'manger'],
            'fitness': ['exercice', 'sport', 'entraînement', 'workout'],
            'news': ['actualités', 'nouvelles', 'info', 'news'],
            'translation': ['traduire', 'traduction', 'translate'],
            'calculator': ['calculer', 'calcul', 'combien'],
            'reminder': ['rappel', 'reminder', 'me rappeler']
        }
        
        for tool, keywords in tool_keywords.items():
            if tool in self.selected_tools:
                if any(keyword in message_lower for keyword in keywords):
                    detected.append(tool)
        
        return detected
    
    def get_instructions_for_tools(self, tools: list) -> str:
        """
        Récupère les instructions pour une liste de tools
        
        Args:
            tools: Liste de tools détectés
        
        Returns:
            Instructions concaténées
        """
        instructions = []
        
        for tool in tools:
            if tool in self.tools_map and tool not in self.injected_tools:
                instructions.append(self.tools_map[tool])
                self.injected_tools.add(tool)
        
        if not instructions:
            return ""
        
        header = "\n\n--- INSTRUCTIONS DÉTAILLÉES DES TOOLS ---\n\n"
        return header + "\n\n".join(instructions)
    
    def inject_if_needed(self, user_message: str, conversation_history: list) -> str:
        """
        Injecte les instructions si un tool est détecté
        
        Args:
            user_message: Message actuel de l'utilisateur
            conversation_history: Historique de la conversation
        
        Returns:
            Instructions à ajouter (vide si rien à injecter)
        """
        # Détecter les tools dans le message utilisateur
        detected_tools = self.detect_tool_usage(user_message)
        
        # Récupérer les instructions non encore injectées
        new_instructions = self.get_instructions_for_tools(detected_tools)
        
        if new_instructions:
            print(f"✅ Injection des instructions pour: {detected_tools}")
        
        return new_instructions
    
    def reset_injections(self):
        """Réinitialise le tracking des injections (nouveau chat)"""
        self.injected_tools.clear()


# =============================================================================
# EXEMPLE D'UTILISATION
# =============================================================================

if __name__ == "__main__":
    # Exemple de données
    tools_instructions = """
INSTRUCTIONS TOOL MÉTÉO

Quand tu utilises le tool Météo :
1. AVANT : "Je vais consulter la météo"
2. UTILISER : weather_tool()
3. APRÈS : "Il fait 22°C"

INSTRUCTIONS TOOL EMAIL

PROCÉDURE STRICTE :
1. Demander d'épeler l'email
2. Confirmer
3. Envoyer
"""
    
    selected_tools = ['weather', 'email', 'calendar']
    
    # Créer le manager
    manager = ToolInjectionManager(tools_instructions, selected_tools)
    
    # Test détection
    message1 = "Quel temps fait-il à Paris ?"
    detected = manager.detect_tool_usage(message1)
    print(f"Détecté: {detected}")
    
    # Test injection
    instructions = manager.inject_if_needed(message1, [])
    print(f"À injecter: {instructions[:100]}...")
    
    # Deuxième message météo (pas de ré-injection)
    message2 = "Et à Lyon, la météo ?"
    instructions2 = manager.inject_if_needed(message2, [])
    print(f"Deuxième injection: {instructions2}")  # Vide car déjà injecté
