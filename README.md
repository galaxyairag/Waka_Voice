# Waka_Voice

Service de synthèse vocale Azure avec contrôles avancés des paramètres de voix.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. Copiez `.env.example` vers `.env`
2. Ajoutez vos clés Azure Speech Service

```bash
cp .env.example .env
```

## Paramètres d'ajustement disponibles

| Paramètre | Description | Plage |
|-----------|-------------|-------|
| `rate` | Vitesse de parole | 0.5 - 2.0 |
| `pitch` | Hauteur de la voix | -50% à +50% |
| `volume` | Volume | silent, x-soft, soft, medium, loud, x-loud |
| `style` | Style émotionnel | cheerful, sad, angry, calm, etc. |
| `style_degree` | Intensité du style | 0.01 - 2.0 |

## Utilisation rapide

```python
from config import VoiceSettings, VoiceStyle, VoiceVolume
from services import AzureTTSService

# Configuration personnalisée
settings = VoiceSettings(
    voice_name="fr-FR-DeniseNeural",
    rate=0.9,
    pitch=5.0,
    style=VoiceStyle.CHEERFUL
)

service = AzureTTSService(settings=settings)
service.speak("Bonjour !")
```

## Presets disponibles

```python
# Utiliser un preset prédéfini
service = AzureTTSService()
service.set_preset("calm_assistant")  # ou: slow_clear, fast_energetic, whisper, etc.
```

Presets inclus:
- `default` - Configuration standard
- `slow_clear` - Lent et clair
- `fast_energetic` - Rapide et énergique
- `calm_assistant` - Assistant calme
- `news_reader` - Style journal
- `whisper` - Chuchotement
- `children_story` - Histoire pour enfants

## Voix françaises disponibles

- `fr-FR-DeniseNeural` - Féminine, polyvalente (styles: cheerful, sad, angry, etc.)
- `fr-FR-HenriNeural` - Masculine, naturelle
- `fr-FR-EloiseNeural` - Féminine, jeune
- `fr-FR-RemyMultilingualNeural` - Masculine, multilingue
- `fr-FR-VivienneMultilingualNeural` - Féminine, multilingue
- `fr-CA-SylvieNeural` - Québécoise féminine
- `fr-CA-JeanNeural` - Québécois masculin

## Exemples

Voir le dossier `examples/` pour plus d'exemples d'utilisation.
