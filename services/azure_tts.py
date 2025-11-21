"""
Service de synthèse vocale Azure avec ajustements de voix
"""

import os
from pathlib import Path
from typing import Optional, Callable
import azure.cognitiveservices.speech as speechsdk

from config.voice_config import VoiceSettings, VOICE_PRESETS
from .ssml_builder import SSMLBuilder


class AzureTTSService:
    """
    Service de Text-to-Speech Azure avec support complet des ajustements.

    Exemple:
        service = AzureTTSService()

        # Utiliser un preset
        service.set_preset("calm_assistant")

        # Ou configurer manuellement
        service.settings.rate = 0.9
        service.settings.pitch = 5.0

        # Synthétiser
        service.speak("Bonjour !")
    """

    def __init__(
        self,
        subscription_key: Optional[str] = None,
        region: Optional[str] = None,
        settings: Optional[VoiceSettings] = None,
    ):
        """
        Initialise le service TTS Azure.

        Args:
            subscription_key: Clé d'abonnement Azure (ou AZURE_SPEECH_KEY env)
            region: Région Azure (ou AZURE_SPEECH_REGION env)
            settings: Paramètres de voix (défaut si non fourni)
        """
        self.subscription_key = subscription_key or os.getenv("AZURE_SPEECH_KEY")
        self.region = region or os.getenv("AZURE_SPEECH_REGION", "westeurope")

        if not self.subscription_key:
            raise ValueError(
                "Clé Azure requise. Définissez AZURE_SPEECH_KEY ou passez subscription_key"
            )

        self.settings = settings or VoiceSettings()
        self._speech_config: Optional[speechsdk.SpeechConfig] = None
        self._synthesizer: Optional[speechsdk.SpeechSynthesizer] = None

    @property
    def speech_config(self) -> speechsdk.SpeechConfig:
        """Configuration Azure Speech (créée à la demande)"""
        if self._speech_config is None:
            self._speech_config = speechsdk.SpeechConfig(
                subscription=self.subscription_key,
                region=self.region
            )
            # Format audio haute qualité
            self._speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Audio24Khz160KBitRateMonoMp3
            )
        return self._speech_config

    @property
    def synthesizer(self) -> speechsdk.SpeechSynthesizer:
        """Synthétiseur (créé à la demande)"""
        if self._synthesizer is None:
            self._synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=None  # Pas de sortie audio par défaut
            )
        return self._synthesizer

    def set_preset(self, preset_name: str) -> None:
        """
        Applique un preset de configuration.

        Args:
            preset_name: Nom du preset (voir VOICE_PRESETS)

        Raises:
            KeyError: Si le preset n'existe pas
        """
        if preset_name not in VOICE_PRESETS:
            available = ", ".join(VOICE_PRESETS.keys())
            raise KeyError(f"Preset '{preset_name}' inconnu. Disponibles: {available}")

        self.settings = VOICE_PRESETS[preset_name]

    def update_settings(self, **kwargs) -> None:
        """
        Met à jour les paramètres de voix.

        Args:
            **kwargs: Paramètres à modifier (rate, pitch, volume, style, etc.)
        """
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
            else:
                raise AttributeError(f"Paramètre inconnu: {key}")

    def get_ssml(self, text: str) -> str:
        """
        Génère le SSML pour le texte sans synthétiser.

        Args:
            text: Texte à convertir

        Returns:
            Document SSML
        """
        builder = SSMLBuilder(self.settings)
        return builder.build(text)

    def speak(self, text: str) -> speechsdk.SpeechSynthesisResult:
        """
        Synthétise et joue le texte sur les haut-parleurs.

        Args:
            text: Texte à synthétiser

        Returns:
            Résultat de la synthèse
        """
        # Créer synthétiseur avec sortie audio
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )

        ssml = self.get_ssml(text)
        result = synthesizer.speak_ssml_async(ssml).get()
        self._check_result(result)
        return result

    def synthesize_to_file(
        self,
        text: str,
        output_path: str | Path,
    ) -> speechsdk.SpeechSynthesisResult:
        """
        Synthétise le texte vers un fichier audio.

        Args:
            text: Texte à synthétiser
            output_path: Chemin du fichier de sortie

        Returns:
            Résultat de la synthèse
        """
        output_path = Path(output_path)
        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))

        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )

        ssml = self.get_ssml(text)
        result = synthesizer.speak_ssml_async(ssml).get()
        self._check_result(result)
        return result

    def synthesize_to_bytes(self, text: str) -> bytes:
        """
        Synthétise le texte et retourne les données audio.

        Args:
            text: Texte à synthétiser

        Returns:
            Données audio en bytes
        """
        ssml = self.get_ssml(text)
        result = self.synthesizer.speak_ssml_async(ssml).get()
        self._check_result(result)
        return result.audio_data

    def synthesize_to_stream(
        self,
        text: str,
        callback: Callable[[bytes], None],
    ) -> speechsdk.SpeechSynthesisResult:
        """
        Synthétise avec streaming des données audio.

        Args:
            text: Texte à synthétiser
            callback: Fonction appelée avec chaque chunk audio

        Returns:
            Résultat de la synthèse
        """
        pull_stream = speechsdk.audio.PullAudioOutputStream()
        audio_config = speechsdk.audio.AudioOutputConfig(stream=pull_stream)

        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )

        ssml = self.get_ssml(text)
        result = synthesizer.speak_ssml_async(ssml).get()
        self._check_result(result)

        # Lire les chunks et appeler le callback
        audio_buffer = bytes(32000)
        while True:
            filled_size = pull_stream.read(audio_buffer)
            if filled_size == 0:
                break
            callback(audio_buffer[:filled_size])

        return result

    def _check_result(self, result: speechsdk.SpeechSynthesisResult) -> None:
        """Vérifie le résultat et lève une exception si erreur"""
        if result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            raise RuntimeError(
                f"Synthèse annulée: {cancellation.reason}. "
                f"Détails: {cancellation.error_details}"
            )
