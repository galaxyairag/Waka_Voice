# tools/tool_tax_calculator.py
"""
Tool : Calculateur d'impôts Burkina Faso
Calcule l'Impôt sur les Traitements et Salaires (ITS) et autres taxes pour le Burkina Faso.
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Barème ITS (Impôt sur les Traitements et Salaires) 2025
# Source: Code des impôts Burkina Faso
ITS_TAX_BRACKETS = [
    {"min": 0, "max": 30000, "rate": 0, "deduction": 0},
    {"min": 30001, "max": 50000, "rate": 12.5, "deduction": 3750},
    {"min": 50001, "max": 80000, "rate": 15.0, "deduction": 5000},
    {"min": 80001, "max": 120000, "rate": 18.0, "deduction": 7400},
    {"min": 120001, "max": 170000, "rate": 22.0, "deduction": 12200},
    {"min": 170001, "max": 250000, "rate": 24.0, "deduction": 15600},
    {"min": 250001, "max": float('inf'), "rate": 25.0, "deduction": 18100}
]

# Cotisations sociales (CNSS)
CNSS_RATES = {
    "employee": {
        "pension": 5.5,  # % du salaire brut
        "total": 5.5
    },
    "employer": {
        "pension": 5.5,
        "family_allowance": 5.75,
        "work_accident": 2.0,
        "total": 13.25
    }
}

# Abattements et déductions
DEDUCTIONS = {
    "standard_deduction": 0.20,  # 20% du salaire brut (max 75,000 FCFA/mois)
    "max_standard_deduction": 75000,  # Maximum déduction forfaitaire mensuelle
    "spouse_deduction": 10000,  # Déduction pour conjoint à charge
    "child_deduction": 15000,  # Déduction par enfant à charge (max 4 enfants)
    "max_children": 4
}

# TVA (Taxe sur la Valeur Ajoutée)
VAT_RATE = 18  # 18% au Burkina Faso


def get_tool_definition():
    """
    Définition du tool pour OpenAI function calling
    """
    return {
        "type": "function",
        "name": "calculate_tax",
        "description": """Calcule les impôts et taxes au Burkina Faso (ITS, CNSS, TVA).

IMPORTANT : Utilise ce tool pour :
- Calcul impôt sur salaire (ITS)
- Cotisations CNSS
- Calcul TVA
- Salaire net après impôts

EXEMPLE:
{
  "tax_type": "salary",
  "gross_salary": 250000,
  "dependents": 2
}

Retourne montant impôt, salaire net, détails calcul.""",
        "parameters": {
            "type": "object",
            "properties": {
                "tax_type": {
                    "type": "string",
                    "description": """Type d'impôt à calculer.

TYPES:
- "salary" ou "its" : Impôt sur Traitements et Salaires
- "vat" ou "tva" : Taxe sur Valeur Ajoutée
- "cnss" : Cotisations sociales

DEFAULT: "salary" """,
                    "default": "salary"
                },
                "gross_salary": {
                    "type": "number",
                    "description": """Salaire brut mensuel en FCFA (pour ITS/CNSS).

EXEMPLES:
- 150000 (150,000 FCFA)
- 250000 (250,000 FCFA)
- 500000 (500,000 FCFA)

FORMAT: Nombre entier""",
                    "default": 0
                },
                "dependents": {
                    "type": "integer",
                    "description": """Nombre de personnes à charge (conjoint + enfants).

CALCUL:
- Conjoint: 10,000 FCFA déduction
- Enfants: 15,000 FCFA/enfant (max 4)

EXEMPLES:
- 0 : Célibataire sans enfants
- 1 : Marié sans enfants OU 1 enfant
- 3 : Marié + 2 enfants OU 3 enfants
- 5 : Marié + 4 enfants (max)

DEFAULT: 0""",
                    "default": 0
                },
                "married": {
                    "type": "boolean",
                    "description": """Si marié (pour déduction conjoint).

DEFAULT: false""",
                    "default": False
                },
                "amount": {
                    "type": "number",
                    "description": """Montant pour calcul TVA (Hors Taxe).

FORMAT: Nombre (ex: 10000)

Utilisé seulement si tax_type='vat'""",
                    "default": 0
                }
            },
            "required": ["tax_type"]
        }
    }


def calculate_its(gross_salary, married=False, children=0):
    """
    Calcule l'Impôt sur les Traitements et Salaires
    
    Args:
        gross_salary: Salaire brut mensuel (FCFA)
        married: Si marié
        children: Nombre d'enfants à charge
    
    Returns:
        dict: Détails du calcul ITS
    """
    # 1. Déduction forfaitaire (20% du brut, max 75,000)
    standard_deduction = min(gross_salary * DEDUCTIONS["standard_deduction"], DEDUCTIONS["max_standard_deduction"])
    
    # 2. Cotisations CNSS employé (5.5%)
    cnss_employee = gross_salary * (CNSS_RATES["employee"]["total"] / 100)
    
    # 3. Base imposable = Brut - Déduction forfaitaire - CNSS
    taxable_income = gross_salary - standard_deduction - cnss_employee
    
    # 4. Abattements pour charges de famille
    family_deduction = 0
    if married:
        family_deduction += DEDUCTIONS["spouse_deduction"]
    
    children_count = min(children, DEDUCTIONS["max_children"])
    family_deduction += children_count * DEDUCTIONS["child_deduction"]
    
    # 5. Revenu imposable final
    final_taxable_income = max(taxable_income - family_deduction, 0)
    
    # 6. Calcul ITS selon barème
    its_amount = 0
    applicable_bracket = None
    
    for bracket in ITS_TAX_BRACKETS:
        if bracket["min"] <= final_taxable_income <= bracket["max"]:
            its_amount = (final_taxable_income * bracket["rate"] / 100) - bracket["deduction"]
            applicable_bracket = bracket
            break
    
    its_amount = max(its_amount, 0)  # Pas d'impôt négatif
    
    # 7. Salaire net
    net_salary = gross_salary - cnss_employee - its_amount
    
    return {
        "gross_salary": gross_salary,
        "standard_deduction": standard_deduction,
        "cnss_employee": cnss_employee,
        "taxable_income": taxable_income,
        "family_deduction": family_deduction,
        "final_taxable_income": final_taxable_income,
        "its_amount": its_amount,
        "tax_rate": applicable_bracket["rate"] if applicable_bracket else 0,
        "net_salary": net_salary,
        "cnss_employer": gross_salary * (CNSS_RATES["employer"]["total"] / 100),
        "total_cost_employer": gross_salary + (gross_salary * CNSS_RATES["employer"]["total"] / 100)
    }


def calculate_vat(amount_ht):
    """
    Calcule la TVA
    
    Args:
        amount_ht: Montant Hors Taxe (FCFA)
    
    Returns:
        dict: Détails calcul TVA
    """
    vat_amount = amount_ht * (VAT_RATE / 100)
    amount_ttc = amount_ht + vat_amount
    
    return {
        "amount_ht": amount_ht,
        "vat_rate": VAT_RATE,
        "vat_amount": vat_amount,
        "amount_ttc": amount_ttc
    }


def calculate_cnss_only(gross_salary):
    """
    Calcule uniquement les cotisations CNSS
    
    Args:
        gross_salary: Salaire brut (FCFA)
    
    Returns:
        dict: Détails cotisations CNSS
    """
    employee_pension = gross_salary * (CNSS_RATES["employee"]["pension"] / 100)
    employer_pension = gross_salary * (CNSS_RATES["employer"]["pension"] / 100)
    employer_family = gross_salary * (CNSS_RATES["employer"]["family_allowance"] / 100)
    employer_accident = gross_salary * (CNSS_RATES["employer"]["work_accident"] / 100)
    
    total_employee = employee_pension
    total_employer = employer_pension + employer_family + employer_accident
    
    return {
        "gross_salary": gross_salary,
        "employee": {
            "pension": employee_pension,
            "total": total_employee
        },
        "employer": {
            "pension": employer_pension,
            "family_allowance": employer_family,
            "work_accident": employer_accident,
            "total": total_employer
        },
        "total_contributions": total_employee + total_employer
    }


def execute(arguments):
    """
    Exécute le calcul d'impôts
    
    Args:
        arguments: Dictionnaire contenant:
            - tax_type: Type d'impôt ('salary', 'vat', 'cnss')
            - gross_salary: Salaire brut (pour salary/cnss)
            - dependents: Personnes à charge (pour salary)
            - married: Si marié (pour salary)
            - amount: Montant HT (pour vat)
    
    Returns:
        dict: Résultat avec calcul d'impôt
    """
    tax_type = arguments.get('tax_type', 'salary').lower()
    
    logger.info(f"💰 Calcul impôt: type={tax_type}")
    
    try:
        if tax_type in ["salary", "its"]:
            gross_salary = arguments.get('gross_salary', 0)
            married = arguments.get('married', False)
            dependents = arguments.get('dependents', 0)
            
            if gross_salary <= 0:
                return {
                    "status": "error",
                    "message": "Veuillez indiquer un salaire brut valide (> 0 FCFA)."
                }
            
            # Calculer nombre d'enfants (si married, -1 dependent pour conjoint)
            children = dependents - (1 if married else 0)
            children = max(0, children)
            
            result = calculate_its(gross_salary, married, children)
            
            message = f"""💰 CALCUL IMPÔT SUR SALAIRE (ITS)

💵 Salaire brut: {result['gross_salary']:,.0f} FCFA

📊 CALCUL:
1. Déduction forfaitaire (20%): -{result['standard_deduction']:,.0f} FCFA
2. CNSS employé (5.5%): -{result['cnss_employee']:,.0f} FCFA
3. Revenu imposable: {result['taxable_income']:,.0f} FCFA
4. Abattements famille: -{result['family_deduction']:,.0f} FCFA
5. Base imposable: {result['final_taxable_income']:,.0f} FCFA

🏛️ IMPÔT (ITS):
• Taux applicable: {result['tax_rate']}%
• Montant ITS: {result['its_amount']:,.0f} FCFA

✅ SALAIRE NET: {result['net_salary']:,.0f} FCFA

📋 CHARGES EMPLOYEUR:
• CNSS employeur (13.25%): {result['cnss_employer']:,.0f} FCFA
• Coût total employeur: {result['total_cost_employer']:,.0f} FCFA

👨‍👩‍👧‍👦 Charges famille: {"Marié" if married else "Célibataire"}, {children} enfant(s)"""
            
            return {
                "status": "success",
                "tax_type": "salary",
                "data": result,
                "message": message
            }
        
        elif tax_type in ["vat", "tva"]:
            amount_ht = arguments.get('amount', 0)
            
            if amount_ht <= 0:
                return {
                    "status": "error",
                    "message": "Veuillez indiquer un montant HT valide (> 0 FCFA)."
                }
            
            result = calculate_vat(amount_ht)
            
            message = f"""💰 CALCUL TVA (Taxe sur Valeur Ajoutée)

💵 Montant HT: {result['amount_ht']:,.0f} FCFA

📊 CALCUL:
• Taux TVA: {result['vat_rate']}%
• Montant TVA: {result['vat_amount']:,.0f} FCFA

✅ MONTANT TTC: {result['amount_ttc']:,.0f} FCFA"""
            
            return {
                "status": "success",
                "tax_type": "vat",
                "data": result,
                "message": message
            }
        
        elif tax_type == "cnss":
            gross_salary = arguments.get('gross_salary', 0)
            
            if gross_salary <= 0:
                return {
                    "status": "error",
                    "message": "Veuillez indiquer un salaire brut valide (> 0 FCFA)."
                }
            
            result = calculate_cnss_only(gross_salary)
            
            message = f"""💰 COTISATIONS CNSS

💵 Salaire brut: {result['gross_salary']:,.0f} FCFA

👤 PART EMPLOYÉ (5.5%):
• Retraite: {result['employee']['pension']:,.0f} FCFA
• TOTAL: {result['employee']['total']:,.0f} FCFA

🏢 PART EMPLOYEUR (13.25%):
• Retraite: {result['employer']['pension']:,.0f} FCFA
• Prestations familiales: {result['employer']['family_allowance']:,.0f} FCFA
• Accidents de travail: {result['employer']['work_accident']:,.0f} FCFA
• TOTAL: {result['employer']['total']:,.0f} FCFA

✅ TOTAL COTISATIONS: {result['total_contributions']:,.0f} FCFA"""
            
            return {
                "status": "success",
                "tax_type": "cnss",
                "data": result,
                "message": message
            }
        
        else:
            return {
                "status": "error",
                "message": f"Type d'impôt '{tax_type}' non reconnu. Utilisez 'salary', 'vat' ou 'cnss'."
            }
        
    except Exception as e:
        logger.exception(f"❌ Erreur calcul impôt: {str(e)}")
        return {
            "status": "error",
            "message": f"Erreur lors du calcul: {str(e)}"
        }
