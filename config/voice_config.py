"""
Configuration des voix Azure Speech Service
Ajustements disponibles sans voix personnalisées
"""

from dataclasses import dataclass, field
from typing import Optional, Literal
from enum import Enum


class VoiceStyle(str, Enum):
    """Styles émotionnels disponibles (dépend de la voix choisie)"""
    DEFAULT = "default"
    CHEERFUL = "cheerful"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    DISGRUNTLED = "disgruntled"
    SERIOUS = "serious"
    AFFECTIONATE = "affectionate"
    GENTLE = "gentle"
    EMBARRASSED = "embarrassed"
    CALM = "calm"
    HOPEFUL = "hopeful"
    EMPATHETIC = "empathetic"
    CHAT = "chat"
    NEWSCAST = "newscast"
    CUSTOMERSERVICE = "customerservice"
    NARRATION = "narration-professional"
    ASSISTANT = "assistant"
    SHOUTING = "shouting"
    WHISPERING = "whispering"


class VoiceVolume(str, Enum):
    """Niveaux de volume"""
    SILENT = "silent"
    X_SOFT = "x-soft"
    SOFT = "soft"
    MEDIUM = "medium"
    LOUD = "loud"
    X_LOUD = "x-loud"


@dataclass
class VoiceSettings:
    """
    Paramètres d'ajustement d'une voix Azure.

    Attributes:
        voice_name: Nom de la voix Azure (ex: "fr-FR-DeniseNeural")
        rate: Vitesse de parole (0.5 = 50%, 1.0 = normal, 2.0 = 200%)
        pitch: Hauteur de la voix en % (-50 à +50)
        volume: Niveau de volume
        style: Style émotionnel (si supporté par la voix)
        style_degree: Intensité du style (0.01 à 2.0, 1.0 = normal)
        emphasis: Niveau d'emphase ("reduced", "moderate", "strong")
    """
    voice_name: str = "fr-FR-DeniseNeural"
    rate: float = 1.0  # 0.5 à 2.0
    pitch: float = 0.0  # -50 à +50 (%)
    volume: VoiceVolume = VoiceVolume.MEDIUM
    style: Optional[VoiceStyle] = None
    style_degree: float = 1.0  # 0.01 à 2.0
    emphasis: Optional[Literal["reduced", "moderate", "strong"]] = None

    def __post_init__(self):
        """Validation des paramètres"""
        if not 0.5 <= self.rate <= 2.0:
            raise ValueError("rate doit être entre 0.5 et 2.0")
        if not -50 <= self.pitch <= 50:
            raise ValueError("pitch doit être entre -50 et +50")
        if not 0.01 <= self.style_degree <= 2.0:
            raise ValueError("style_degree doit être entre 0.01 et 2.0")


# Voix françaises recommandées avec leurs styles supportés
FRENCH_VOICES = {
    "fr-FR-DeniseNeural": {
        "gender": "Female",
        "styles": ["cheerful", "sad", "angry", "fearful", "serious", "default"],
        "description": "Voix féminine française polyvalente"
    },
    "fr-FR-HenriNeural": {
        "gender": "Male",
        "styles": ["cheerful", "sad", "angry", "default"],
        "description": "Voix masculine française naturelle"
    },
    "fr-FR-EloiseNeural": {
        "gender": "Female",
        "styles": ["default"],
        "description": "Voix féminine française jeune"
    },
    "fr-FR-RemyMultilingualNeural": {
        "gender": "Male",
        "styles": ["default"],
        "description": "Voix masculine multilingue"
    },
    "fr-FR-VivienneMultilingualNeural": {
        "gender": "Female",
        "styles": ["default"],
        "description": "Voix féminine multilingue"
    },
    "fr-CA-SylvieNeural": {
        "gender": "Female",
        "styles": ["default"],
        "description": "Voix féminine québécoise"
    },
    "fr-CA-JeanNeural": {
        "gender": "Male",
        "styles": ["default"],
        "description": "Voix masculine québécoise"
    },
}


# Presets de configuration courants
VOICE_PRESETS = {
    "default": VoiceSettings(),

    "slow_clear": VoiceSettings(
        rate=0.8,
        pitch=0.0,
        volume=VoiceVolume.LOUD,
        style=None
    ),

    "fast_energetic": VoiceSettings(
        rate=1.3,
        pitch=5.0,
        volume=VoiceVolume.LOUD,
        style=VoiceStyle.CHEERFUL,
        style_degree=1.2
    ),

    "calm_assistant": VoiceSettings(
        voice_name="fr-FR-DeniseNeural",
        rate=0.9,
        pitch=-5.0,
        volume=VoiceVolume.MEDIUM,
        style=VoiceStyle.CALM,
        style_degree=1.0
    ),

    "news_reader": VoiceSettings(
        voice_name="fr-FR-HenriNeural",
        rate=1.1,
        pitch=0.0,
        volume=VoiceVolume.MEDIUM,
        style=VoiceStyle.NEWSCAST
    ),

    "whisper": VoiceSettings(
        rate=0.85,
        pitch=-10.0,
        volume=VoiceVolume.SOFT,
        style=VoiceStyle.WHISPERING,
        style_degree=1.5
    ),

    "children_story": VoiceSettings(
        voice_name="fr-FR-EloiseNeural",
        rate=0.85,
        pitch=10.0,
        volume=VoiceVolume.MEDIUM,
        style=VoiceStyle.CHEERFUL,
        style_degree=1.3
    ),
}
