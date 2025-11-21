"""
Smart Tool Injector - Injection Just-In-Time des instructions de tools
Injecte les instructions SEULEMENT quand l'agent annonce qu'il va utiliser un tool
"""

import re
from typing import Optional, Dict, List, Tuple


class SmartToolInjector:
    """
    Détecte quand l'agent veut utiliser un tool et injecte les instructions au bon moment
    """
    
    def __init__(self, tools_instructions: str, selected_tools: list):
        """
        Initialise l'injecteur
        
        Args:
            tools_instructions: Instructions détaillées de tous les tools
            selected_tools: Liste des tools disponibles
        """
        self.tools_instructions = tools_instructions
        self.selected_tools = selected_tools
        self.injected_tools = set()
        
        # Parse les instructions par tool
        self.tools_map = self._parse_instructions()
        
        # Map des noms de tools (variations)
        self.tool_name_variations = {
            'weather': ['météo', 'weather', 'temps', 'température'],
            'email': ['email', 'mail', 'e-mail', 'courrier'],
            'calendar': ['calendrier', 'agenda', 'calendar'],
            'cv_builder': ['cv', 'curriculum', 'cv_builder'],
            'flight_search': ['vol', 'vols', 'avion', 'flight'],
            'hotel_booking': ['hôtel', 'hotel', 'hébergement'],
            'nutrition': ['nutrition', 'nutritionnel', 'aliment'],
            'fitness': ['fitness', 'sport', 'exercice', 'entraînement'],
            'news': ['actualités', 'news', 'nouvelles', 'info'],
            'translation': ['traduction', 'traduire', 'translation'],
            'calculator': ['calculatrice', 'calcul', 'calculator'],
            'reminder': ['rappel', 'reminder']
        }
    
    def _parse_instructions(self) -> Dict[str, str]:
        """Parse les instructions pour séparer chaque tool"""
        tools_map = {}
        
        if not self.tools_instructions:
            return tools_map
        
        sections = self.tools_instructions.split('INSTRUCTIONS TOOL')
        
        for section in sections[1:]:
            lines = section.strip().split('\n', 1)
            if len(lines) >= 2:
                tool_name = lines[0].strip().lower()
                instructions = lines[1].strip()
                
                tool_key = self._normalize_tool_name(tool_name)
                if tool_key:
                    tools_map[tool_key] = f"INSTRUCTIONS TOOL {lines[0]}\n\n{instructions}"
        
        return tools_map
    
    def _normalize_tool_name(self, name: str) -> Optional[str]:
        """Normalise le nom du tool"""
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
    
    def detect_tool_announcement(self, assistant_message: str) -> Optional[str]:
        """
        Détecte si l'assistant annonce qu'il va utiliser un tool
        
        Args:
            assistant_message: Message de l'assistant
        
        Returns:
            Nom du tool détecté, ou None
        
        Exemples:
            "Je vais utiliser le tool météo" → 'weather'
            "Je vais utiliser l'outil email" → 'email'
            "J'utilise le tool calendrier" → 'calendar'
        """
        message_lower = assistant_message.lower()
        
        # Patterns de détection
        patterns = [
            r"je vais utiliser (?:le |l')?tool (\w+)",
            r"je vais utiliser (?:le |l')?outil (\w+)",
            r"j'utilise (?:le |l')?tool (\w+)",
            r"j'utilise (?:le |l')?outil (\w+)",
            r"utilisation du tool (\w+)",
            r"utilisation de l'outil (\w+)"
        ]
        
        # Chercher un match
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                tool_name = match.group(1)
                
                # Trouver le tool correspondant
                for tool_key, variations in self.tool_name_variations.items():
                    if tool_name in variations:
                        return tool_key
        
        return None
    
    def should_inject(self, tool_name: str) -> bool:
        """
        Vérifie si on doit injecter les instructions pour ce tool
        
        Args:
            tool_name: Nom du tool
        
        Returns:
            True si on doit injecter, False sinon
        """
        # Vérifier que le tool est sélectionné
        if tool_name not in self.selected_tools:
            return False
        
        # Vérifier qu'on ne l'a pas déjà injecté
        if tool_name in self.injected_tools:
            return False
        
        # Vérifier qu'on a les instructions
        if tool_name not in self.tools_map:
            return False
        
        return True
    
    def inject_tool_instructions(self, tool_name: str) -> Tuple[bool, str]:
        """
        Injecte les instructions pour un tool
        
        Args:
            tool_name: Nom du tool
        
        Returns:
            (success, instructions) tuple
        """
        if not self.should_inject(tool_name):
            return False, ""
        
        instructions = self.tools_map[tool_name]
        self.injected_tools.add(tool_name)
        
        # Format pour injection dans la conversation
        formatted = f"\n--- INSTRUCTIONS POUR LE TOOL {tool_name.upper()} ---\n\n{instructions}\n\n--- FIN DES INSTRUCTIONS ---\n"
        
        return True, formatted
    
    def process_assistant_message(self, assistant_message: str) -> Tuple[bool, Optional[str], str]:
        """
        Traite un message de l'assistant et injecte si nécessaire
        
        Args:
            assistant_message: Message de l'assistant
        
        Returns:
            (injected, tool_name, instructions) tuple
        """
        # Détecter l'annonce d'utilisation d'un tool
        tool_name = self.detect_tool_announcement(assistant_message)
        
        if not tool_name:
            return False, None, ""
        
        # Injecter les instructions
        success, instructions = self.inject_tool_instructions(tool_name)
        
        if success:
            print(f"✅ Injection des instructions pour le tool: {tool_name}")
            return True, tool_name, instructions
        else:
            print(f"⚠️ Pas d'injection pour {tool_name} (déjà injecté ou non disponible)")
            return False, tool_name, ""
    
    def reset(self):
        """Réinitialise l'état (nouvelle conversation)"""
        self.injected_tools.clear()


# =============================================================================
# EXEMPLE D'UTILISATION DANS UNE CONVERSATION
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("DÉMONSTRATION : Smart Tool Injector")
    print("=" * 80)
    
    # Configuration
    tools_instructions = """INSTRUCTIONS TOOL MÉTÉO

Quand tu utilises le tool Météo :
1. AVANT : "Je vais consulter la météo pour [ville]"
2. UTILISER : weather_tool(city="Paris")
3. APRÈS : "Il fait actuellement 22°C à Paris"

INSTRUCTIONS TOOL EMAIL

PROCÉDURE STRICTE :
1. Demander d'épeler l'email
2. Confirmer avant envoi
3. Annoncer le succès
"""
    
    selected_tools = ['weather', 'email', 'calendar']
    
    # Créer l'injecteur
    injector = SmartToolInjector(tools_instructions, selected_tools)
    
    # Simulation de conversation
    print("\n--- CONVERSATION SIMULÉE ---\n")
    
    # Tour 1
    print("👤 User: Quel temps à Paris ?")
    
    # L'agent répond (simulation)
    assistant_msg_1 = "Je vais utiliser le tool météo pour obtenir cette information."
    print(f"🤖 Assistant: {assistant_msg_1}")
    
    # Détection et injection
    injected, tool, instructions = injector.process_assistant_message(assistant_msg_1)
    
    if injected:
        print(f"\n🔧 INJECTION DÉTECTÉE pour le tool: {tool}")
        print(f"📝 Instructions injectées ({len(instructions)} caractères)\n")
        # Maintenant l'agent a les instructions et peut utiliser le tool correctement
        print("🤖 Assistant (après injection): D'accord, je consulte... Il fait 22°C à Paris !")
    
    print("\n" + "-" * 80 + "\n")
    
    # Tour 2 - Même tool (pas de ré-injection)
    print("👤 User: Et à Lyon ?")
    assistant_msg_2 = "Je vais utiliser le tool météo pour Lyon."
    print(f"🤖 Assistant: {assistant_msg_2}")
    
    injected, tool, instructions = injector.process_assistant_message(assistant_msg_2)
    
    if not injected:
        print(f"\n✅ Pas de ré-injection (tool {tool} déjà injecté)")
        print("🤖 Assistant: Il fait 19°C à Lyon !")
    
    print("\n" + "-" * 80 + "\n")
    
    # Tour 3 - Nouveau tool
    print("👤 User: Envoie un email à mon patron")
    assistant_msg_3 = "Je vais utiliser le tool email pour envoyer votre message."
    print(f"🤖 Assistant: {assistant_msg_3}")
    
    injected, tool, instructions = injector.process_assistant_message(assistant_msg_3)
    
    if injected:
        print(f"\n🔧 INJECTION DÉTECTÉE pour le tool: {tool}")
        print(f"📝 Instructions injectées ({len(instructions)} caractères)\n")
        print("🤖 Assistant (après injection): Veuillez épeler l'adresse email lettre par lettre.")
    
    print("\n" + "=" * 80)
    print(f"RÉSUMÉ : Tools injectés = {injector.injected_tools}")
    print("=" * 80)
