# Agent Voice Session - Structure du Code

## 📁 Structure des Fichiers

### 1. **HTML** - `templates/agents/agent_voice_session.html`
**Rôle**: Structure et interface utilisateur
- Barre de statut style smartphone
- En-tête avec avatar de l'agent
- Zone de conversation avec messages
- Contrôles vocaux (bouton micro/stop)
- Visualiseur audio
- Panneau de configuration collapsible
- Intégration avec Flask (Jinja2 templates)

### 2. **CSS** - `static/css/agent_voice_session.css`
**Rôle**: Styles et design responsive
- Design moderne avec glassmorphism
- Responsive (mobile, tablet, desktop)
- Animations (messageSlide, recording-pulse, audioWave)
- Thème dark/light avec variables CSS
- Breakpoints:
  - Mobile: < 768px
  - Tablet: 768px - 1023px
  - Desktop: ≥ 1024px

### 3. **JavaScript** - `static/js/agent_voice_session.js`
**Rôle**: Logique métier et interactions
- **WebSocket**: Connexion Azure Realtime Voice API
- **Audio Recording**: Capture microphone (PCM16, 24kHz)
- **Audio Playback**: Lecture séquentielle avec queue
- **Tool Execution**: Exécution d'outils via API
- **Cosmos DB**: Sauvegarde des conversations
- **UI Management**: Mise à jour statuts, messages, visualiseur

## 🔧 Configuration

### Variables Globales (JavaScript)
```javascript
window.agentConfig = {
    agentId: string,
    agentName: string,
    modelId: string,
    voice: string,
    temperature: number,
    maxTokens: number,
    instructions: string,
    tools: array,
    customLexiconUrl: string|null
}
```

### Fonctions Principales

#### Conversation
- `startConversation()` - Démarre la session vocale
- `stopConversation()` - Arrête la session
- `startNewConversation()` - Nouvelle conversation (nouveau UUID)

#### WebSocket
- `connectWebSocket()` - Connexion au serveur Azure
- `handleWebSocketMessage(message)` - Traitement des messages

#### Audio
- `startAudioRecording()` - Capture du microphone
- `playAudioChunk(base64Audio, responseId)` - Lecture audio
- `stopAllAudio()` - Arrêt immédiat de tout audio

#### UI
- `addMessage(type, content, id)` - Ajoute un message
- `updateConnectionStatus(status, text)` - Met à jour le statut
- `toggleConfig()` - Affiche/cache la configuration

#### Outils
- `executeToolCall(callId, toolName, args)` - Exécute un outil
- `saveInstructions()` - Sauvegarde les instructions
- `saveLexiconUrl()` - Sauvegarde l'URL du lexique

## 📡 Communication Backend

### Endpoints Utilisés
```
POST /agents/api/conversation/message
POST /agents/api/conversation/end
POST /api/tools/execute
POST /agents/api/{agentId}/update_session_config
```

### WebSocket Events
**Entrants** (serveur → client):
- `session.created`, `session.updated`
- `response.audio.delta`
- `response.audio_transcript.delta/done`
- `conversation.item.input_audio_transcription.completed`
- `response.output_item.added`
- `response.created`, `response.done`, `response.cancelled`
- `input_audio_buffer.speech_started`
- `response.function_call_arguments.delta/done`

**Sortants** (client → serveur):
- `session.update` - Configuration de session
- `input_audio_buffer.append` - Envoi audio microphone
- `response.cancel` - Annulation de réponse
- `conversation.item.create` - Résultats d'outils
- `response.create` - Demande de réponse

## 🎨 Design Responsive

### Mobile (< 768px)
- Plein écran sans bordure
- Panneau config en modal bas
- Bouton vocal 80px

### Tablet (768px - 1023px)
- Cadre smartphone avec notch
- Max-width: 480px
- Bordures arrondies 42px

### Desktop (≥ 1024px)
- Max-width: 1200px
- Panneau config centré
- Avatar 80px
- Messages plus lisibles

## 🔄 Flux de Travail

1. **Initialisation**
   - Chargement de `window.agentConfig` depuis Flask
   - Génération/récupération du `callId` (UUID)
   - Mise à jour horloge status bar

2. **Démarrage Conversation**
   - Connexion WebSocket
   - Configuration session (instructions, voice, tools)
   - Démarrage capture microphone
   - Activation visualiseur audio

3. **Conversation Active**
   - Envoi audio micro → WebSocket (PCM16 base64)
   - Réception audio agent → Playback queue
   - Transcription affichée en temps réel
   - Sauvegarde messages dans Cosmos DB

4. **Gestion Interruptions**
   - Détection parole utilisateur (RMS)
   - Arrêt immédiat audio agent
   - Envoi `response.cancel` au serveur
   - Réactivation micro

5. **Exécution Outils**
   - Détection `function_call` dans WebSocket
   - Appel backend `/api/tools/execute`
   - Renvoi résultat au modèle
   - Affichage notification UI

6. **Fin de Conversation**
   - Fermeture WebSocket
   - Arrêt capture audio
   - Arrêt visualiseur
   - Sauvegarde tokens/coûts dans Cosmos DB

## 💾 Persistance des Données

### SessionStorage
- `current_call_id` - UUID de la conversation active

### Cosmos DB (via API)
- **Messages**: role, content, model_id, metadata
- **Conversation**: call_id, agent_id, tokens, timestamp

## 🚀 Optimisations

### Audio
- **Queue système**: Évite les coupures lors de chunks multiples
- **LAG_MAX**: 500ms pour synchronisation
- **Interruption immédiate**: Stop & cancel lors de parole utilisateur

### Performance
- **Lazy loading**: Audio context créé à la demande
- **Cleanup**: Fermeture contexts après usage
- **Debounce**: Mise à jour visualiseur via requestAnimationFrame

### UX
- **Animations fluides**: cubic-bezier(0.34, 1.56, 0.64, 1)
- **Feedback visuel**: Status badges, pulse animations
- **Responsive**: Breakpoints optimisés pour tous devices

## 📝 Notes de Développement

- **Cache busting**: `?v={{ range(1, 9999) | random }}` sur CSS/JS
- **Compatibilité**: Chrome, Edge, Firefox, Safari
- **Audio format**: PCM16, 24kHz, mono
- **WebSocket**: Azure Cognitive Services Realtime API
- **Sécurité**: Validation côté backend pour tools

## 🐛 Debugging

Console logs:
- `🆕` Nouvelle conversation
- `📞` Call ID
- `✅` Succès opération
- `❌` Erreur
- `🎙️` Audio microphone
- `🔊` Audio playback
- `🔧` Exécution outil
- `💾` Sauvegarde Cosmos DB
- `📡` Messages WebSocket
