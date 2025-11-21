"""
Générateur SSML pour Azure Speech Service
Construit le markup SSML avec les ajustements de voix
"""

from typing import Optional
import xml.etree.ElementTree as ET
from config.voice_config import VoiceSettings, VoiceStyle


class SSMLBuilder:
    """
    Construit des documents SSML pour Azure Speech avec tous les ajustements.

    Exemple d'utilisation:
        settings = VoiceSettings(rate=0.9, pitch=5.0, style=VoiceStyle.CHEERFUL)
        builder = SSMLBuilder(settings)
        ssml = builder.build("Bonjour, comment allez-vous ?")
    """

    def __init__(self, settings: VoiceSettings):
        self.settings = settings

    def build(self, text: str) -> str:
        """
        Génère le SSML complet pour le texte donné.

        Args:
            text: Texte à synthétiser

        Returns:
            Document SSML formaté
        """
        # Racine speak
        speak = ET.Element("speak")
        speak.set("version", "1.0")
        speak.set("xmlns", "http://www.w3.org/2001/10/synthesis")
        speak.set("xmlns:mstts", "https://www.w3.org/2001/mstts")
        speak.set("xml:lang", self._get_language())

        # Voice element
        voice = ET.SubElement(speak, "voice")
        voice.set("name", self.settings.voice_name)

        # Conteneur pour le contenu
        content_parent = voice

        # Ajouter express-as si style défini
        if self.settings.style and self.settings.style != VoiceStyle.DEFAULT:
            express_as = ET.SubElement(voice, "mstts:express-as")
            express_as.set("style", self.settings.style.value)
            express_as.set("styledegree", str(self.settings.style_degree))
            content_parent = express_as

        # Ajouter prosody pour rate, pitch, volume
        prosody = ET.SubElement(content_parent, "prosody")
        prosody.set("rate", self._format_rate())
        prosody.set("pitch", self._format_pitch())
        prosody.set("volume", self.settings.volume.value)

        # Ajouter le texte avec emphasis si nécessaire
        if self.settings.emphasis:
            emphasis = ET.SubElement(prosody, "emphasis")
            emphasis.set("level", self.settings.emphasis)
            emphasis.text = text
        else:
            prosody.text = text

        return ET.tostring(speak, encoding="unicode")

    def build_with_breaks(self, segments: list[tuple[str, Optional[int]]]) -> str:
        """
        Génère SSML avec des pauses entre segments.

        Args:
            segments: Liste de tuples (texte, pause_ms)
                      pause_ms = None pour pas de pause après

        Returns:
            Document SSML formaté
        """
        speak = ET.Element("speak")
        speak.set("version", "1.0")
        speak.set("xmlns", "http://www.w3.org/2001/10/synthesis")
        speak.set("xmlns:mstts", "https://www.w3.org/2001/mstts")
        speak.set("xml:lang", self._get_language())

        voice = ET.SubElement(speak, "voice")
        voice.set("name", self.settings.voice_name)

        content_parent = voice

        if self.settings.style and self.settings.style != VoiceStyle.DEFAULT:
            express_as = ET.SubElement(voice, "mstts:express-as")
            express_as.set("style", self.settings.style.value)
            express_as.set("styledegree", str(self.settings.style_degree))
            content_parent = express_as

        prosody = ET.SubElement(content_parent, "prosody")
        prosody.set("rate", self._format_rate())
        prosody.set("pitch", self._format_pitch())
        prosody.set("volume", self.settings.volume.value)

        for i, (text, pause_ms) in enumerate(segments):
            if i == 0:
                prosody.text = text
            else:
                # Ajouter le texte après le dernier élément
                if len(prosody) > 0:
                    prosody[-1].tail = text
                else:
                    prosody.text = (prosody.text or "") + text

            if pause_ms is not None:
                break_elem = ET.SubElement(prosody, "break")
                break_elem.set("time", f"{pause_ms}ms")

        return ET.tostring(speak, encoding="unicode")

    def _get_language(self) -> str:
        """Extrait la langue depuis le nom de la voix"""
        # Format: "fr-FR-DeniseNeural" -> "fr-FR"
        parts = self.settings.voice_name.split("-")
        if len(parts) >= 2:
            return f"{parts[0]}-{parts[1]}"
        return "fr-FR"

    def _format_rate(self) -> str:
        """Formate le rate pour SSML (ex: 1.2 -> "+20%")"""
        if self.settings.rate == 1.0:
            return "default"
        percentage = (self.settings.rate - 1.0) * 100
        if percentage > 0:
            return f"+{percentage:.0f}%"
        return f"{percentage:.0f}%"

    def _format_pitch(self) -> str:
        """Formate le pitch pour SSML"""
        if self.settings.pitch == 0:
            return "default"
        if self.settings.pitch > 0:
            return f"+{self.settings.pitch:.0f}%"
        return f"{self.settings.pitch:.0f}%"


def generate_ssml(text: str, settings: VoiceSettings) -> str:
    """
    Fonction utilitaire pour générer du SSML rapidement.

    Args:
        text: Texte à synthétiser
        settings: Configuration de la voix

    Returns:
        Document SSML
    """
    builder = SSMLBuilder(settings)
    return builder.build(text)
