# tools/tool_email.py
"""
Outil d'envoi d'email via Azure Communication Services
"""

import os
import base64
from dotenv import load_dotenv

load_dotenv()

AZURE_COMMUNICATION_EMAIL_CONNECTION_STRING = os.getenv("AZURE_COMMUNICATION_EMAIL_CONNECTION_STRING", "")
AZURE_COMMUNICATION_EMAIL_SENDER = os.getenv("AZURE_COMMUNICATION_EMAIL_SENDER", "")


def get_tool_definition():
    """Retourne la définition du tool send_email"""
    return {
        "type": "function",
        "name": "send_email",
        "description": """Envoie un email via Azure Communication Services.
        
Utilise cet outil quand l'utilisateur demande d'envoyer un email/message/courriel.

EXEMPLE:
{
  "email": "destinataire@example.com",
  "subject": "Confirmation de réservation",
  "message": "Votre vol pour Paris est confirmé pour le 15 décembre.",
  "url": "https://exemple.com/reservation/12345"
}""",
        "parameters": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": """Adresse EMAIL du destinataire (OBLIGATOIRE).
                    
EXEMPLES VALIDES:
- "utilisateur@example.com"
- "contact@entreprise.bf"
- "prenom.nom@gmail.com"
- "info@organisation.org"

FORMAT ATTENDU:
- Format standard: texte@domaine.extension
- Extensions courantes: .com, .fr, .bf, .org, .net, .edu
- Peut contenir: lettres, chiffres, points, tirets, underscores

CONVERSION:
Si l'utilisateur donne un email incomplet:
- "envoyer à jean" → demande l'adresse complète
- "mon email" → demande l'adresse exacte

VALIDATION:
- Doit contenir un @
- Doit avoir un domaine après @
- Doit avoir une extension (.com, .fr, etc.)

FORMAT: Adresse email valide (ex: "contact@example.com")"""
                },
                "subject": {
                    "type": "string",
                    "description": """OBJET de l'email (OBLIGATOIRE) - titre/sujet du message.
                    
EXEMPLES:
Professionnels:
- "Confirmation de réservation"
- "Demande de rendez-vous"
- "Facture numéro 12345"
- "Rapport mensuel - Décembre 2024"

Personnels:
- "Invitation anniversaire"
- "Partage de photos"
- "Nouvelles du Burkina"

Informatifs:
- "Mise à jour importante"
- "Rappel réunion demain"
- "Document demandé"

CONSEILS:
- Sois clair et concis (3-8 mots)
- Décris le contenu principal
- Évite les majuscules excessives
- Pas de points d'exclamation multiples (!!!)

FORMAT: Texte libre, court et descriptif (ex: "Confirmation de vol")"""
                },
                "message": {
                    "type": "string",
                    "description": """CONTENU du message/corps de l'email (OBLIGATOIRE).
                    
EXEMPLES:
Message court:
"Bonjour,\n\nVotre réservation est confirmée pour le 15 décembre.\n\nCordialement"

Message détaillé:
"Bonjour M. Traoré,\n\nNous avons bien reçu votre demande de réservation.\n\nDétails:\n- Vol: OUA-CDG\n- Date: 15/12/2024\n- Heure: 10h30\n\nMerci de votre confiance.\n\nCordialement,\nL'équipe Waka"

STRUCTURE RECOMMANDÉE:
1. Salutation ("Bonjour", "Madame/Monsieur")
2. Corps du message (informations principales)
3. Formule de politesse ("Cordialement", "Bien à vous")

FORMATAGE:
- Utilise \\n pour les sauts de ligne
- Sois poli et professionnel
- Structure en paragraphes courts
- Inclus les détails importants

FORMAT: Texte libre avec formatage simple (ex: "Bonjour,\\n\\nVotre message...")"""
                },
                "url": {
                    "type": "string",
                    "description": """URL optionnelle à inclure dans l'email (lien cliquable).
                    
EXEMPLES:
- "https://exemple.com/reservation/12345" (lien de confirmation)
- "https://maps.google.com/?q=Ouagadougou" (lien Google Maps)
- "https://site.com/facture.pdf" (document à télécharger)
- "" (chaîne vide si aucun lien)

QUAND UTILISER:
- Pour partager un lien de confirmation
- Pour diriger vers une page web
- Pour un document en ligne
- Laisse vide (\"\") si pas de lien

FORMAT ATTENDU:
- Doit commencer par http:// ou https://
- URL complète et valide
- Ou chaîne vide \"\" si pas de lien

FORMAT: URL complète (ex: \"https://example.com/page\") ou \"\" (par défaut)""",
                    "default": ""
                }
            },
            "required": ["email", "subject", "message"]
        }
    }


def send_email(email, subject, message, url=""):
    """
    Envoie un email via Azure Communication Services avec mise en forme HTML élégante.
    
    Args:
        email: Adresse email du destinataire
        subject: Objet de l'email
        message: Contenu du message
        url: URL optionnelle à inclure
    
    Returns:
        dict: Résultat de l'envoi avec status et détails
    """
    try:
        # Vérifications
        if not AZURE_COMMUNICATION_EMAIL_CONNECTION_STRING:
            return {
                "status": "error",
                "message": "Azure Communication Email non configuré",
                "details": "AZURE_COMMUNICATION_EMAIL_CONNECTION_STRING manquant dans .env"
            }
        
        if not AZURE_COMMUNICATION_EMAIL_SENDER:
            return {
                "status": "error",
                "message": "Expéditeur email non configuré",
                "details": "AZURE_COMMUNICATION_EMAIL_SENDER manquant dans .env"
            }
        
        # Charger le logo encodé en base64 (si disponible)
        logo_base64 = ""
        logo_path = "static/images/waka_logo.jpg"
        if os.path.exists(logo_path):
            try:
                with open(logo_path, "rb") as logo_file:
                    logo_base64 = base64.b64encode(logo_file.read()).decode('utf-8')
            except Exception:
                pass  # Logo optionnel
        
        # Convertir message en HTML simple
        html_message = message.replace("\n", "<br>")
        full_message = f"{message}\n\n{url if url else ''}"
        
        # Importer Azure Communication Services Email
        from azure.communication.email import EmailClient
        
        # Créer le client email
        email_client = EmailClient.from_connection_string(AZURE_COMMUNICATION_EMAIL_CONNECTION_STRING)
        
        # Construire le message email
        email_message = {
            "senderAddress": AZURE_COMMUNICATION_EMAIL_SENDER,
            "recipients": {
                "to": [{"address": email}]
            },
            "content": {
                "subject": subject,
                "plainText": full_message,
                "html": f"""
                    <!DOCTYPE html>
                    <html>
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        </head>
                        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: 'Segoe UI', Arial, sans-serif;">
                            <div style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                                
                                <!-- En-tête avec logo -->
                                <div style="background-color: #ffffff; padding: 30px 20px; text-align: center; border-bottom: 3px solid #7B2CBF;">
                                    {f'<img src="data:image/jpeg;base64,{logo_base64}" alt="Waka Logo" style="max-width: 150px; height: auto; margin-bottom: 15px;">' if logo_base64 else ''}
                                    <h1 style="color: #7B2CBF; margin: 10px 0 0 0; font-size: 24px; font-weight: 600;">Waka AI Assistant</h1>
                                </div>
                                
                                <!-- Contenu principal -->
                                <div style="background-color: #ffffff; padding: 40px 30px;">
                                    <div style="color: #7B2CBF; font-size: 16px; line-height: 1.8; margin-bottom: 25px;">
                                        {html_message}
                                    </div>
                                    
                                    {f'''<div style="text-align: center; margin: 30px 0;">
                                        <a href="{url}" style="background-color: #7B2CBF; color: #ffffff; padding: 14px 35px; text-decoration: none; border-radius: 25px; display: inline-block; font-weight: 600; font-size: 16px; box-shadow: 0 4px 8px rgba(123, 44, 191, 0.3); transition: all 0.3s;">
                                            🔗 Cliquer ici
                                        </a>
                                    </div>''' if url else ''}
                                </div>
                                
                                <!-- Pied de page -->
                                <div style="background-color: #f9f9f9; padding: 25px 30px; text-align: center; border-top: 1px solid #e0e0e0;">
                                    <p style="color: #999999; font-size: 13px; margin: 5px 0; line-height: 1.6;">
                                        Cet email a été envoyé par <strong style="color: #7B2CBF;">Waka AI Assistant</strong>
                                    </p>
                                    <p style="color: #999999; font-size: 12px; margin: 5px 0;">
                                        © 2025 Waka AI - Tous droits réservés
                                    </p>
                                </div>
                                
                            </div>
                        </body>
                    </html>
                """
            }
        }
        
        # Envoyer l'email
        poller = email_client.begin_send(email_message)
        result = poller.result()
        
        return {
            "status": "success",
            "message": "Email envoyé avec succès",
            "to": email,
            "subject": subject,
            "message_id": result.id if hasattr(result, 'id') else "N/A"
        }
        
    except ImportError as ie:
        return {
            "status": "error",
            "message": "Package Azure Communication Email non installé",
            "error_type": "ImportError",
            "error_details": str(ie),
            "solution": "Exécutez: pip install azure-communication-email"
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"Erreur envoi email: {str(e)}",
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "to": email,
            "details": "Vérifiez AZURE_COMMUNICATION_EMAIL_CONNECTION_STRING et AZURE_COMMUNICATION_EMAIL_SENDER dans .env"
        }


def execute(arguments):
    """Point d'entrée pour l'exécution du tool"""
    email = arguments.get("email", "")
    subject = arguments.get("subject", "")
    message = arguments.get("message", "")
    url = arguments.get("url", "")
    
    return send_email(email, subject, message, url)
