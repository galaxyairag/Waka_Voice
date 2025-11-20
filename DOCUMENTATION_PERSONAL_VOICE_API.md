# Documentation API Personal Voice - Azure Custom Voice

## Vue d'ensemble

Ce document décrit les endpoints API pour créer et gérer des voix personnalisées via Azure Custom Voice API intégrés dans `personal_voice_routes.py`.

## Configuration requise

### Variables d'environnement

```env
# Azure Speech Service pour Custom Voice API
PERSONAL_VOICE_KEY=<votre_clé_azure_speech>
PERSONAL_VOICE_REGION=eastus  # ou autre région supportée
CUSTOM_VOICE_API_VERSION=2024-02-01-preview

# Azure Blob Storage pour les fichiers audio
BLOB_CONNECTION_STRING=<votre_connection_string>
BLOB_CONTAINER_ENREGISTREMENTS=enregistrements
```

## Endpoints disponibles

### 1. Gestion des projets

#### Créer un projet
```http
POST /personal-voice/api/projects
Content-Type: application/json

{
  "project_name": "Mon Projet Voice",
  "description": "Description du projet"
}
```

**Réponse:**
```json
{
  "success": true,
  "project_id": "pv-abc123def456",
  "status": "created",
  "message": "Projet créé avec succès",
  "data": { ... }
}
```

#### Lister les projets
```http
GET /personal-voice/api/projects
```

#### Obtenir un projet
```http
GET /personal-voice/api/projects/{project_id}
```

#### Supprimer un projet
```http
DELETE /personal-voice/api/projects/{project_id}
```

---

### 2. Upload de fichiers audio

#### Upload audio (consentement ou échantillon vocal)
```http
POST /personal-voice/api/upload-audio
Content-Type: multipart/form-data

audio: <fichier audio WAV/MP3>
type: consent|voice
project_id: pv-abc123def456
```

**Réponse:**
```json
{
  "success": true,
  "blob_name": "pv-abc123def456/consent_1a2b3c4d.wav",
  "blob_url": "https://storage.blob.core.windows.net/...",
  "message": "Audio uploadé avec succès"
}
```

---

### 3. Gestion des consentements

#### Obtenir le texte de consentement
```http
GET /personal-voice/api/consent-text/{locale}
```

Locales supportées: `fr-FR`, `en-US`, `es-ES`, `de-DE`, `pt-BR`

#### Créer un consentement
```http
POST /personal-voice/api/consents
Content-Type: application/json

{
  "project_id": "pv-abc123def456",
  "voice_talent_name": "Jean Dupont",
  "company_name": "Waka Afrique",
  "audio_url": "https://storage.blob.core.windows.net/...",
  "locale": "fr-FR",
  "description": "Consentement pour voix personnelle"
}
```

**Réponse:**
```json
{
  "success": true,
  "consent_id": "consent-abc123def456",
  "message": "Consentement créé avec succès",
  "data": { ... },
  "operation_location": "https://..."
}
```

#### Obtenir un consentement
```http
GET /personal-voice/api/consents/{consent_id}
```

---

### 4. Gestion des voix personnelles

#### Créer une voix personnelle
```http
POST /personal-voice/api/personal-voices
Content-Type: application/json

{
  "project_id": "pv-abc123def456",
  "consent_id": "consent-abc123def456",
  "container_url": "https://storage.blob.core.windows.net/voice-samples?sp=rl&sig=...",
  "audio_prefix": "jessica/",
  "audio_extensions": [".wav", ".mp3"],
  "voice_name": "Ma Voix Personnelle",
  "description": "Voix personnalisée pour l'agent"
}
```

**Paramètres:**
- `container_url` **(requis)** : URL du conteneur Azure Blob Storage avec token SAS (permissions read + list)
- `audio_prefix` *(optionnel)* : Préfixe pour filtrer les fichiers dans le conteneur (ex: "jessica/")
- `audio_extensions` *(optionnel)* : Extensions des fichiers audio (défaut: [".wav"])
- `voice_name` **(requis)** : Nom de la voix
- `description` *(optionnel)* : Description de la voix

**Réponse:**
```json
{
  "success": true,
  "personal_voice_id": "voice-abc123def456",
  "speaker_profile_id": "spkr_profile_abc123",
  "message": "Voix personnelle en cours de création",
  "data": { ... },
  "operation_location": "https://..."
}
```

#### Obtenir une voix personnelle
```http
GET /personal-voice/api/personal-voices/{voice_id}
```

#### Lister toutes les voix personnelles
```http
GET /personal-voice/api/personal-voices
```

**Note:** Cette route utilise l'endpoint Azure Speech `/speechapi/texttospeech/v3.0/endpoints` pour lister les Personal Voice endpoints déjà créés.

#### Supprimer une voix personnelle
```http
DELETE /personal-voice/api/personal-voices/{voice_id}
```

---

### 5. Suivi des opérations asynchrones

#### Vérifier le statut d'une opération via Operation-Location
```http
POST /personal-voice/api/operations/status
Content-Type: application/json

{
  "operation_location": "https://eastus.api.cognitive.microsoft.com/customvoice/operations/abc123..."
}
```

**Réponse:**
```json
{
  "success": true,
  "status": "Running" | "Succeeded" | "Failed" | "NotStarted",
  "data": { ... }
}
```

#### Polling du statut de création d'une voix
```http
GET /personal-voice/api/personal-voices/{voice_id}/poll
```

**Réponse:**
```json
{
  "success": true,
  "voice_id": "voice-abc123",
  "status": "Succeeded",
  "speaker_profile_id": "spkr_profile_abc123",
  "is_complete": true,
  "data": { ... }
}
```

**Note:** Cette route met automatiquement à jour le statut dans Cosmos DB et retourne `is_complete: true` quand la création est terminée (succès ou échec).

#### Lister toutes les opérations en cours
```http
GET /personal-voice/api/operations/pending
```

**Réponse:**
```json
{
  "success": true,
  "pending_voices": [
    {
      "voice_id": "voice-abc123",
      "status": "Running",
      "created_at": "2025-11-19T10:00:00Z"
    }
  ],
  "pending_consents": [
    {
      "consent_id": "consent-def456",
      "status": "Running",
      "created_at": "2025-11-19T10:05:00Z"
    }
  ],
  "total_pending": 2
}
```

**Utilisation recommandée:**
- Appeler `/poll` toutes les 5-10 secondes après création d'une voix
- Arrêter le polling quand `is_complete: true`
- Utiliser `/operations/pending` pour un dashboard de suivi global

---

### 6. Synthèse vocale

#### Synthétiser du texte avec une voix personnelle
```http
POST /personal-voice/api/synthesize
Content-Type: application/json

{
  "text": "Bonjour, ceci est un test de ma voix personnalisée.",
  "speaker_profile_id": "spkr_profile_abc123",
  "voice_name": "fr-FR-DeniseNeural"
}
```

**Réponse:**
```json
{
  "success": true,
  "audio_url": "https://storage.blob.core.windows.net/synthesized/abc123.mp3?sas_token...",
  "message": "Synthèse vocale réussie"
}
```

**Note:** La synthèse utilise SSML avec `<mstts:ttsembedding speakerProfileId="...">` pour appliquer le timbre de voix personnalisé.

---

## Flux de travail complet

### Étape 1: Créer un projet
```bash
POST /personal-voice/api/projects
{
  "project_name": "Voix Agent Waka",
  "description": "Voix personnalisée pour l'agent commercial"
}
→ Retourne: project_id
```

### Étape 2: Enregistrer et uploader l'audio de consentement
```bash
# Enregistrer l'utilisateur lisant le texte de consentement
GET /personal-voice/api/consent-text/fr-FR
→ Retourne: "Je [prénom et nom] suis conscient(e)..."

# Upload du fichier audio
POST /personal-voice/api/upload-audio
→ Retourne: blob_url pour le consentement
```

### Étape 3: Créer le consentement
```bash
POST /personal-voice/api/consents
{
  "project_id": "pv-abc123",
  "voice_talent_name": "Jean Dupont",
  "company_name": "Waka Afrique",
  "audio_url": "<blob_url du consentement>",
  "locale": "fr-FR"
}
→ Retourne: consent_id
```

### Étape 4: Enregistrer et uploader les échantillons vocaux
```bash
# Upload des échantillons vocaux (5-10 minutes d'audio)
POST /personal-voice/api/upload-audio
{
  "type": "voice",
  "project_id": "pv-abc123"
}
→ Retourne: blob_url pour les échantillons
```

### Étape 5: Créer la voix personnelle
```bash
POST /personal-voice/api/personal-voices
{
  "project_id": "pv-abc123",
  "consent_id": "consent-abc123",
  "audio_url": "<blob_url des échantillons>",
  "voice_name": "Voix Jean Dupont"
}
→ Retourne: personal_voice_id, speaker_profile_id
```

### Étape 6: Vérifier le statut de création (Polling)
```bash
# Polling automatique toutes les 5 secondes
GET /personal-voice/api/personal-voices/{voice_id}/poll
→ Vérifie status: "NotStarted" | "Running" | "Succeeded" | "Failed"
→ Met à jour automatiquement Cosmos DB
→ Retourne is_complete: true quand terminé

# Alternative: vérifier via operation_location
POST /personal-voice/api/operations/status
{
  "operation_location": "<operation_location du step 5>"
}
```

**Recommandation:** Utiliser la route `/poll` qui gère automatiquement la mise à jour Cosmos DB.

### Étape 7: Utiliser la voix pour la synthèse
```bash
POST /personal-voice/api/synthesize
{
  "text": "Bonjour, comment puis-je vous aider ?",
  "speaker_profile_id": "spkr_profile_abc123",
  "voice_name": "fr-FR-DeniseNeural"
}
→ Retourne: audio_url
```

---

## Stockage Cosmos DB

### Container: PersonalVoiceProjects
```json
{
  "id": "pv-abc123",
  "project_id": "pv-abc123",
  "project_name": "Voix Agent Waka",
  "description": "...",
  "status": "created",
  "created_at": "2025-11-19T10:00:00Z"
}
```

### Container: PersonalVoiceConsents
```json
{
  "id": "consent-abc123",
  "consent_id": "consent-abc123",
  "project_id": "pv-abc123",
  "voice_talent_name": "Jean Dupont",
  "audio_url": "...",
  "status": "Succeeded"
}
```

### Container: PersonalVoices
```json
{
  "id": "voice-abc123",
  "voice_id": "voice-abc123",
  "project_id": "pv-abc123",
  "consent_id": "consent-abc123",
  "speaker_profile_id": "spkr_profile_abc123",
  "status": "Succeeded",
  "voice_name": "Voix Jean Dupont"
}
```

---

## Gestion des erreurs

Toutes les routes retournent un format cohérent:

**Succès:**
```json
{
  "success": true,
  "...": "..."
}
```

**Erreur:**
```json
{
  "success": false,
  "error": "Description de l'erreur",
  "details": "Détails techniques (optionnel)"
}
```

**Codes HTTP:**
- `200`: Succès
- `201`: Ressource créée
- `202`: Opération acceptée (traitement asynchrone)
- `400`: Requête invalide
- `404`: Ressource non trouvée
- `500`: Erreur serveur

---

## Références

- [Azure Custom Voice API Documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-custom-voice)
- [Personal Voice Documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/personal-voice-overview)
- [SSML ttsembedding Documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-voice#speaker-profile-id)

---

## Notes de déploiement

1. **Blob Storage**: S'assurer que `BLOB_CONNECTION_STRING` est configuré
2. **Cosmos DB**: Les containers sont créés automatiquement au démarrage
3. **Azure Speech**: Vérifier que la région supporte Personal Voice API
4. **Permissions**: L'application a besoin d'accès en lecture/écriture sur Blob Storage et Cosmos DB

---

## Blueprint Flask

Le blueprint est enregistré avec le préfixe `/personal-voice`:

```python
# Dans app.py
from Blueprints.personal_voice_routes import personal_voice_bp
app.register_blueprint(personal_voice_bp)
```

Toutes les routes sont accessibles via: `https://votre-app.azurewebsites.net/personal-voice/api/...`
