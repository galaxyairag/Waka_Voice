"""
Exemples d'utilisation du service Azure TTS avec ajustements de voix
"""

from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

from config import VoiceSettings, VoiceStyle, VoiceVolume, VOICE_PRESETS, FRENCH_VOICES
from services import AzureTTSService, generate_ssml


def exemple_configuration_manuelle():
    """Exemple avec configuration manuelle des paramètres"""
    print("=== Configuration manuelle ===\n")

    # Créer des settings personnalisés
    settings = VoiceSettings(
        voice_name="fr-FR-DeniseNeural",
        rate=0.9,          # 90% de la vitesse normale
        pitch=5.0,         # Légèrement plus aigu
        volume=VoiceVolume.MEDIUM,
        style=VoiceStyle.CHEERFUL,
        style_degree=1.2   # Style un peu plus marqué
    )

    service = AzureTTSService(settings=settings)

    # Voir le SSML généré
    ssml = service.get_ssml("Bonjour ! Comment allez-vous aujourd'hui ?")
    print(f"SSML généré:\n{ssml}\n")

    # Synthétiser (décommenter pour tester)
    # service.speak("Bonjour ! Comment allez-vous aujourd'hui ?")


def exemple_presets():
    """Exemple avec les presets prédéfinis"""
    print("=== Utilisation des presets ===\n")
    print(f"Presets disponibles: {list(VOICE_PRESETS.keys())}\n")

    service = AzureTTSService()

    # Tester différents presets
    for preset_name in ["calm_assistant", "fast_energetic", "whisper"]:
        service.set_preset(preset_name)
        ssml = service.get_ssml("Ceci est un test.")
        print(f"Preset '{preset_name}':")
        print(f"  Rate: {service.settings.rate}")
        print(f"  Pitch: {service.settings.pitch}")
        print(f"  Style: {service.settings.style}")
        print()


def exemple_modification_dynamique():
    """Exemple de modification des paramètres en cours d'exécution"""
    print("=== Modification dynamique ===\n")

    service = AzureTTSService()

    # Configuration initiale
    print(f"Rate initial: {service.settings.rate}")

    # Modifier un paramètre
    service.update_settings(rate=1.3, pitch=10.0)
    print(f"Rate après modification: {service.settings.rate}")
    print(f"Pitch après modification: {service.settings.pitch}")

    # Changer la voix
    service.update_settings(voice_name="fr-FR-HenriNeural")
    print(f"Voix: {service.settings.voice_name}")


def exemple_voix_disponibles():
    """Affiche les voix françaises disponibles"""
    print("=== Voix françaises disponibles ===\n")

    for voice_name, info in FRENCH_VOICES.items():
        print(f"{voice_name}")
        print(f"  Genre: {info['gender']}")
        print(f"  Styles: {', '.join(info['styles'])}")
        print(f"  Description: {info['description']}")
        print()


def exemple_synthese_fichier():
    """Exemple de synthèse vers un fichier"""
    print("=== Synthèse vers fichier ===\n")

    settings = VoiceSettings(
        voice_name="fr-FR-DeniseNeural",
        style=VoiceStyle.NARRATION
    )
    service = AzureTTSService(settings=settings)

    # Décommenter pour générer le fichier
    # service.synthesize_to_file(
    #     "Bienvenue dans cette démonstration de synthèse vocale Azure.",
    #     "output.mp3"
    # )
    print("Fichier audio généré: output.mp3")


def exemple_ssml_direct():
    """Génération de SSML sans service"""
    print("=== Génération SSML directe ===\n")

    settings = VoiceSettings(
        voice_name="fr-FR-HenriNeural",
        rate=1.1,
        style=VoiceStyle.NEWSCAST
    )

    ssml = generate_ssml("Les dernières nouvelles du jour.", settings)
    print(f"SSML:\n{ssml}")


if __name__ == "__main__":
    # Exécuter les exemples qui ne nécessitent pas de clé Azure
    exemple_voix_disponibles()
    exemple_presets()
    exemple_ssml_direct()

    # Ces exemples nécessitent une clé Azure valide
    # exemple_configuration_manuelle()
    # exemple_modification_dynamique()
    # exemple_synthese_fichier()
