# tools/tool_school_info.py
"""
Tool : Informations écoles et universités
Fournit des informations sur les établissements scolaires et universitaires au Burkina Faso.
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Base de données des principales universités du Burkina Faso
UNIVERSITIES = {
    "Université Joseph Ki-Zerbo": {
        "type": "Université publique",
        "location": "Ouagadougou",
        "address": "03 BP 7021 Ouagadougou 03",
        "phone": "+226 25 30 70 64",
        "website": "www.univ-ouaga.bf",
        "faculties": [
            "Sciences Exactes et Appliquées (SEA)",
            "Sciences de la Santé (SDS)",
            "Sciences Économiques et de Gestion (SEG)",
            "Lettres et Sciences Humaines (LASH)",
            "Sciences Juridiques et Politiques (SJP)"
        ],
        "programs": "Licence, Master, Doctorat",
        "founded": 1974,
        "description": "Principale université publique du Burkina Faso, anciennement Université de Ouagadougou."
    },
    "Université Nazi Boni": {
        "type": "Université publique",
        "location": "Bobo-Dioulasso",
        "address": "01 BP 1091 Bobo-Dioulasso 01",
        "phone": "+226 20 97 31 52",
        "website": "www.unb.bf",
        "faculties": [
            "Sciences et Techniques",
            "Sciences de la Santé",
            "Sciences Économiques et de Gestion",
            "Lettres, Arts et Communication"
        ],
        "programs": "Licence, Master, Doctorat",
        "founded": 1995,
        "description": "Deuxième université publique du Burkina Faso."
    },
    "Université Thomas Sankara": {
        "type": "Université publique",
        "location": "Kaya",
        "address": "BP 417 Kaya",
        "phone": "+226 24 45 12 34",
        "website": "www.uts.bf",
        "faculties": [
            "Sciences et Technologies",
            "Développement Rural",
            "Sciences Économiques"
        ],
        "programs": "Licence, Master",
        "founded": 2017,
        "description": "Université publique récente axée sur le développement."
    },
    "Université Aube Nouvelle": {
        "type": "Université privée",
        "location": "Ouagadougou",
        "address": "Ouagadougou, secteur 22",
        "phone": "+226 25 37 52 91",
        "website": "www.aube-nouvelle.bf",
        "faculties": [
            "Informatique et Télécommunications",
            "Gestion et Commerce",
            "Droit et Sciences Politiques"
        ],
        "programs": "Licence, Master",
        "founded": 2005,
        "description": "Université privée réputée en informatique et gestion."
    },
    "Université Saint Thomas d'Aquin": {
        "type": "Université privée catholique",
        "location": "Ouagadougou",
        "address": "Route de Kaya, Ouagadougou",
        "phone": "+226 25 40 91 23",
        "website": "www.usta.bf",
        "faculties": [
            "Théologie",
            "Philosophie",
            "Sciences Sociales",
            "Éducation"
        ],
        "programs": "Licence, Master, Doctorat",
        "founded": 2009,
        "description": "Université catholique offrant formations en théologie et sciences humaines."
    }
}

# Grandes écoles et instituts
GRANDES_ECOLES = {
    "2iE": {
        "name": "Institut International d'Ingénierie de l'Eau et de l'Environnement",
        "type": "École d'ingénieurs",
        "location": "Ouagadougou",
        "address": "Rue de la Science, 01 BP 594 Ouagadougou 01",
        "phone": "+226 25 49 28 00",
        "website": "www.2ie-edu.org",
        "specializations": [
            "Génie Civil et Hydraulique",
            "Génie Électrique et Énergétique",
            "Génie de l'Environnement",
            "Management de projets"
        ],
        "programs": "Licence, Master, MBA, Doctorat",
        "international": True,
        "description": "École d'ingénieurs internationale reconnue en Afrique de l'Ouest."
    },
    "ENAM": {
        "name": "École Nationale d'Administration et de Magistrature",
        "type": "École d'administration",
        "location": "Ouagadougou",
        "address": "Ouagadougou",
        "phone": "+226 25 30 62 45",
        "website": "www.enam.gov.bf",
        "specializations": [
            "Administration publique",
            "Magistrature",
            "Diplomatie"
        ],
        "programs": "Formation professionnelle",
        "description": "École de formation des cadres de l'administration publique."
    },
    "ENEP": {
        "name": "École Nationale des Enseignants du Primaire",
        "type": "École normale",
        "location": "Plusieurs villes",
        "specializations": [
            "Enseignement primaire",
            "Éducation préscolaire"
        ],
        "programs": "Formation professionnelle",
        "description": "Formation des instituteurs et professeurs du primaire."
    }
}

# Informations système éducatif
EDUCATION_SYSTEM = {
    "structure": {
        "Préscolaire": "3-6 ans (optionnel)",
        "Primaire": "6 ans (CP1 à CM2) - Obligatoire",
        "Post-primaire": "4 ans (6ème à 3ème) - Collège",
        "Secondaire": "3 ans (Seconde à Terminale) - Lycée",
        "Supérieur": "Université, Grandes Écoles"
    },
    "examens": {
        "CEP": "Certificat d'Études Primaires (fin primaire)",
        "BEPC": "Brevet d'Études du Premier Cycle (fin collège)",
        "BAC": "Baccalauréat (fin lycée)",
        "Séries BAC": ["A (Littéraire)", "C (Sciences exactes)", "D (Sciences naturelles)", "G (Gestion)"]
    },
    "calendar": {
        "Rentrée scolaire": "Début octobre",
        "Fin année scolaire": "Fin juin",
        "Vacances": "Juillet - Septembre"
    }
}


def get_tool_definition():
    """
    Définition du tool pour OpenAI function calling
    """
    return {
        "type": "function",
        "name": "get_school_info",
        "description": """Fournit des informations sur les universités, grandes écoles et le système éducatif du Burkina Faso.

IMPORTANT : Utilise ce tool pour :
- Infos universités et écoles
- Programmes d'études disponibles
- Contact établissements
- Système éducatif burkinabé

EXEMPLE:
{
  "query": "Université Joseph Ki-Zerbo",
  "info_type": "university"
}

Retourne coordonnées, programmes, facultés et descriptions.""",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": """Nom de l'établissement ou type d'information recherché.

EXEMPLES:
- "Université Joseph Ki-Zerbo" (université spécifique)
- "universités Ouagadougou" (liste par ville)
- "écoles d'ingénieurs" (par type)
- "système éducatif" (infos générales)
- "2iE" (grande école)
- "toutes" (liste complète)

CONVERSION:
- "université de ouaga" → "Université Joseph Ki-Zerbo"
- "faso" → toutes les universités
- Pas de query → liste toutes les universités

FORMAT: Texte libre""",
                    "default": "all"
                },
                "info_type": {
                    "type": "string",
                    "description": """Type d'établissement ou information.

TYPES:
- "university" : Universités
- "school" : Grandes écoles et instituts
- "system" : Système éducatif burkinabé
- "all" : Toutes les informations

DEFAULT: "all" """,
                    "default": "all"
                }
            },
            "required": []
        }
    }


def search_universities(query):
    """
    Recherche universités correspondant à la query
    
    Args:
        query: Terme de recherche
    
    Returns:
        dict: Universités correspondantes
    """
    query_lower = query.lower()
    
    # Recherche exacte ou partielle
    results = {}
    for name, info in UNIVERSITIES.items():
        if (query_lower in name.lower() or 
            query_lower in info['location'].lower() or
            query_lower == "all" or
            query_lower == "toutes"):
            results[name] = info
    
    return results


def search_schools(query):
    """
    Recherche grandes écoles correspondant à la query
    
    Args:
        query: Terme de recherche
    
    Returns:
        dict: Écoles correspondantes
    """
    query_lower = query.lower()
    
    results = {}
    for code, info in GRANDES_ECOLES.items():
        if (query_lower in code.lower() or 
            query_lower in info['name'].lower() or
            query_lower in info['type'].lower() or
            query_lower == "all" or
            query_lower == "toutes"):
            results[code] = info
    
    return results


def execute(arguments):
    """
    Exécute la recherche d'informations scolaires
    
    Args:
        arguments: Dictionnaire contenant:
            - query: Terme de recherche (optionnel, défaut: 'all')
            - info_type: Type d'info (optionnel, défaut: 'all')
    
    Returns:
        dict: Résultat avec informations scolaires
    """
    query = arguments.get('query', 'all')
    info_type = arguments.get('info_type', 'all')
    
    logger.info(f"🎓 Recherche infos scolaires: query={query}, type={info_type}")
    
    try:
        # Recherche système éducatif
        if query.lower() in ["système", "system", "éducatif", "educatif"] or info_type == "system":
            structure_text = "\n".join([f"• {level}: {desc}" for level, desc in EDUCATION_SYSTEM['structure'].items()])
            exams_text = "\n".join([f"• {exam}: {desc}" for exam, desc in EDUCATION_SYSTEM['examens'].items()])
            calendar_text = "\n".join([f"• {event}: {date}" for event, date in EDUCATION_SYSTEM['calendar'].items()])
            
            message = f"""🎓 SYSTÈME ÉDUCATIF BURKINABÉ

📚 STRUCTURE:
{structure_text}

📝 EXAMENS:
{exams_text}

📅 CALENDRIER:
{calendar_text}"""
            
            return {
                "status": "success",
                "type": "education_system",
                "data": EDUCATION_SYSTEM,
                "message": message
            }
        
        # Recherche universités
        if info_type in ["university", "all"]:
            universities = search_universities(query)
            
            if universities:
                unis_text = "\n\n".join([
                    f"🎓 {name}\n   Type: {info['type']}\n   Ville: {info['location']}\n   Tél: {info['phone']}\n   Site: {info['website']}\n   Programmes: {info['programs']}\n   Facultés: {len(info['faculties'])}"
                    for name, info in universities.items()
                ])
                
                # Si une seule université, donner détails complets
                if len(universities) == 1:
                    name, info = list(universities.items())[0]
                    faculties_text = "\n".join([f"   • {fac}" for fac in info['faculties']])
                    
                    message = f"""🎓 {name}

📌 Type: {info['type']}
📍 Localisation: {info['location']}
📫 Adresse: {info['address']}
📞 Téléphone: {info['phone']}
🌐 Site web: {info['website']}

🏛️ FACULTÉS:
{faculties_text}

📚 Programmes: {info['programs']}
📅 Fondée en: {info['founded']}

ℹ️ {info['description']}"""
                else:
                    message = f"🎓 UNIVERSITÉS AU BURKINA FASO ({len(universities)}):\n\n{unis_text}"
                
                return {
                    "status": "success",
                    "type": "universities",
                    "count": len(universities),
                    "data": universities,
                    "message": message
                }
        
        # Recherche grandes écoles
        if info_type in ["school", "all"]:
            schools = search_schools(query)
            
            if schools:
                schools_text = "\n\n".join([
                    f"🏫 {info['name']}\n   Type: {info['type']}\n   Ville: {info['location']}\n   Tél: {info.get('phone', 'N/A')}\n   Site: {info.get('website', 'N/A')}\n   Programmes: {info['programs']}"
                    for code, info in schools.items()
                ])
                
                # Si une seule école, donner détails complets
                if len(schools) == 1:
                    code, info = list(schools.items())[0]
                    specs_text = "\n".join([f"   • {spec}" for spec in info['specializations']])
                    
                    message = f"""🏫 {info['name']}

📌 Type: {info['type']}
📍 Localisation: {info['location']}
📫 Adresse: {info.get('address', 'N/A')}
📞 Téléphone: {info.get('phone', 'N/A')}
🌐 Site web: {info.get('website', 'N/A')}

🎯 SPÉCIALISATIONS:
{specs_text}

📚 Programmes: {info['programs']}

ℹ️ {info['description']}"""
                else:
                    message = f"🏫 GRANDES ÉCOLES ET INSTITUTS ({len(schools)}):\n\n{schools_text}"
                
                return {
                    "status": "success",
                    "type": "schools",
                    "count": len(schools),
                    "data": schools,
                    "message": message
                }
        
        return {
            "status": "error",
            "message": f"Aucune information trouvée pour '{query}'. Essayez 'toutes' pour voir tous les établissements."
        }
        
    except Exception as e:
        logger.exception(f"❌ Erreur recherche écoles: {str(e)}")
        return {
            "status": "error",
            "message": f"Erreur lors de la recherche: {str(e)}"
        }
