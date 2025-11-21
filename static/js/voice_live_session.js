/**
 * Azure Voice Live API - WebSocket Session Manager
 * Documentation: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live-how-to
 * 
 * Gère la connexion WebSocket et l'interaction audio bidirectionnelle
 */

// =============================================================================
// CONFIGURATION
// =============================================================================

const VOICE_LIVE_CONFIG = {
    // WebSocket endpoint (sera configuré dynamiquement)
    endpoint: null,
    apiVersion: '2025-10-01',

    // Audio settings
    audioSampleRate: 24000, // 24kHz recommandé
    audioFormat: 'pcm16',

    // Reconnection
    reconnectAttempts: 3,
    reconnectDelay: 2000,
};

// =============================================================================
// TOOL EXECUTION MONITOR (PATIENCE)
// =============================================================================

/**
 * Moniteur d'exécution des tools avec rappels de patience automatiques
 */
class ToolExecutionMonitor {
    constructor(session) {
        this.session = session;
        this.activeTools = new Map(); // Map<toolName, {timer, startTime, reminderCount}>
        this.patienceInterval = 30000; // 30 secondes
        this.maxReminders = 5; // Maximum 5 rappels (2min30)
    }

    /**
     * Démarrer le monitoring d'un tool
     */
    startMonitoring(toolName, toolCallId) {
        console.log(`⏱️ Démarrage monitoring tool: ${toolName} (ID: ${toolCallId})`);

        const monitorData = {
            toolCallId: toolCallId,
            startTime: Date.now(),
            reminderCount: 0,
            timer: null
        };

        // Fonction récursive pour les rappels
        const scheduleReminder = () => {
            monitorData.timer = setTimeout(() => {
                // Vérifier si le tool est toujours actif
                if (this.activeTools.has(toolName)) {
                    this.sendPatienceReminder(toolName, monitorData);

                    // Programmer le prochain rappel si pas atteint le max
                    if (monitorData.reminderCount < this.maxReminders) {
                        scheduleReminder();
                    } else {
                        console.warn(`⚠️ Tool ${toolName} dépasse le temps maximum (${this.maxReminders * 30}s)`);
                    }
                }
            }, this.patienceInterval);
        };

        // Démarrer le premier timer
        scheduleReminder();

        this.activeTools.set(toolName, monitorData);
    }

    /**
     * Envoyer un message de patience au model
     */
    sendPatienceReminder(toolName, monitorData) {
        const elapsedSeconds = Math.floor((Date.now() - monitorData.startTime) / 1000);
        monitorData.reminderCount++;

        console.log(`🔔 Rappel de patience #${monitorData.reminderCount} pour ${toolName} (${elapsedSeconds}s écoulées)`);

        // Créer le message système pour le model
        const systemMessage = {
            type: 'conversation.item.create',
            item: {
                type: 'message',
                role: 'system',
                content: [
                    {
                        type: 'input_text',
                        text: `SYSTEM: L'outil "${toolName}" prend du temps (${elapsedSeconds} secondes écoulées). Rassurez l'utilisateur en lui demandant de patienter encore un peu. Variez votre formulation.`
                    }
                ]
            }
        };

        // Envoyer via WebSocket
        if (this.session.ws && this.session.isConnected) {
            this.session.ws.send(JSON.stringify(systemMessage));

            // Forcer le model à répondre immédiatement
            const responseCommand = {
                type: 'response.create',
                response: {
                    modalities: ['text', 'audio'],
                    instructions: 'Réponds immédiatement au message système avec un message de patience naturel et rassurant.'
                }
            };

            this.session.ws.send(JSON.stringify(responseCommand));
        }
    }

    /**
     * Arrêter le monitoring d'un tool
     */
    stopMonitoring(toolName) {
        if (this.activeTools.has(toolName)) {
            const monitorData = this.activeTools.get(toolName);

            // Annuler le timer
            if (monitorData.timer) {
                clearTimeout(monitorData.timer);
            }

            const elapsedSeconds = Math.floor((Date.now() - monitorData.startTime) / 1000);
            console.log(`✅ Arrêt monitoring tool: ${toolName} (durée: ${elapsedSeconds}s, rappels: ${monitorData.reminderCount})`);

            this.activeTools.delete(toolName);
        }
    }

    /**
     * Nettoyer tous les timers actifs
     */
    cleanup() {
        console.log(`🧹 Nettoyage de ${this.activeTools.size} tools en monitoring`);

        this.activeTools.forEach((monitorData, toolName) => {
            if (monitorData.timer) {
                clearTimeout(monitorData.timer);
            }
        });

        this.activeTools.clear();
    }

    /**
     * Obtenir les statistiques de monitoring
     */
    getStats() {
        const stats = {
            activeToolsCount: this.activeTools.size,
            tools: []
        };

        this.activeTools.forEach((monitorData, toolName) => {
            const elapsedSeconds = Math.floor((Date.now() - monitorData.startTime) / 1000);
            stats.tools.push({
                name: toolName,
                elapsedSeconds: elapsedSeconds,
                reminderCount: monitorData.reminderCount
            });
        });

        return stats;
    }
}

// =============================================================================
// CLASSE PRINCIPALE
// =============================================================================

class VoiceLiveSession {
    constructor(config) {
        this.config = config;
        this.ws = null;
        this.isConnected = false;
        this.sessionId = null;

        // Audio context
        this.audioContext = null;
        this.mediaStream = null;
        this.audioWorklet = null;
        this.audioQueue = [];
        this.isPlayingAudio = false;
        this.currentAudioSource = null;

        // State
        this.isRecording = false;
        this.isSpeaking = false;

        // Tool Execution Monitor
        this.toolMonitor = new ToolExecutionMonitor(this);

        // Event callbacks
        this.onConnected = null;
        this.onDisconnected = null;
        this.onError = null;
        this.onTranscript = null;
        this.onAudioReceived = null;
        this.onResponseStart = null;
        this.onResponseEnd = null;
        this.onSpeechStarted = null;
        this.onSpeechStopped = null;
        this.onFunctionCall = null;
    }

    /**
     * Construire l'URL WebSocket
     */
    buildWebSocketUrl() {
        const { endpoint, apiVersion, agentId, projectId, model, apiKey } = this.config;

        let url = `wss://${endpoint}/voice-live/realtime?api-version=${apiVersion}`;

        // Utiliser agent_id si disponible, sinon model
        if (agentId && projectId) {
            url += `&agent_id=${agentId}&project_id=${projectId}`;
        } else if (model) {
            url += `&model=${model}`;
        }

        // Ajouter api-key comme query parameter (pour navigateur)
        if (apiKey) {
            url += `&api-key=${apiKey}`;
        }

        return url;
    }

    /**
     * Établir la connexion WebSocket
     */
    async connect() {
        return new Promise((resolve, reject) => {
            try {
                const wsUrl = this.buildWebSocketUrl();
                console.log('🔌 Connexion WebSocket Voice Live...', wsUrl.replace(/api-key=[^&]+/, 'api-key=***'));

                this.ws = new WebSocket(wsUrl);
                this.ws.binaryType = 'arraybuffer';

                // Connection ouverte
                this.ws.onopen = () => {
                    console.log('✅ WebSocket connecté');
                    this.isConnected = true;

                    // Envoyer la configuration de session
                    this.sendSessionUpdate();

                    if (this.onConnected) {
                        this.onConnected();
                    }

                    resolve();
                };

                // Messages reçus
                this.ws.onmessage = (event) => {
                    this.handleMessage(event.data);
                };

                // Erreur
                this.ws.onerror = (error) => {
                    console.error('❌ Erreur WebSocket:', error);
                    if (this.onError) {
                        this.onError(error);
                    }
                    reject(error);
                };

                // Connexion fermée
                this.ws.onclose = (event) => {
                    console.log('🔌 WebSocket fermé:', event.code, event.reason);
                    this.isConnected = false;

                    if (this.onDisconnected) {
                        this.onDisconnected(event);
                    }
                };

            } catch (error) {
                console.error('❌ Erreur de connexion:', error);
                reject(error);
            }
        });
    }

    /**
     * Envoyer la configuration de session (session.update)
     */
    sendSessionUpdate() {
        const sessionConfig = {
            type: 'session.update',
            session: {
                // Modalities - CRITIQUE pour obtenir une sortie audio
                modalities: this.config.modalities || ["text", "audio"],

                // Instructions
                instructions: this.config.instructions || "You are a helpful AI assistant.",

                // Turn detection (VAD)
                turn_detection: this.buildTurnDetection(),

                // Input audio sampling rate
                input_audio_sampling_rate: 24000,

                // Voice configuration
                voice: this.buildVoiceConfig(),
            }
        };

        // Noise reduction (optionnel)
        if (this.config.noiseReduction) {
            sessionConfig.session.input_audio_noise_reduction = { type: "azure_deep_noise_suppression" };
        }

        // Echo cancellation (optionnel)
        if (this.config.echoCancellation) {
            sessionConfig.session.input_audio_echo_cancellation = { type: "server_echo_cancellation" };
        }

        // Input transcription (optionnel)
        if (this.config.inputTranscription) {
            sessionConfig.session.input_audio_transcription = this.config.inputTranscription;
        }

        // Audio timestamps (optionnel)
        if (this.config.audioTimestamps) {
            sessionConfig.session.output_audio_timestamp_types = ["word"];
        }

        // Animation/Viseme (optionnel)
        if (this.config.visemeEnabled) {
            sessionConfig.session.animation = { outputs: ["viseme_id"] };
        }

        // Tools (optionnel)
        if (this.config.tools && this.config.tools.length > 0) {
            sessionConfig.session.tools = this.config.tools;
            console.log(`✅ Ajout de ${this.config.tools.length} tools à la session`);
        }

        console.log('📤 Envoi session.update:', sessionConfig);
        this.sendEvent(sessionConfig);
    }

    /**
     * Construire la configuration Turn Detection
     */
    buildTurnDetection() {
        const vad = this.config.vadConfig || {};

        const turnDetection = {
            type: vad.type || 'azure_semantic_vad',
        };

        // Paramètres communs
        if (vad.threshold !== undefined) turnDetection.threshold = vad.threshold;
        if (vad.prefixPadding) turnDetection.prefix_padding_ms = vad.prefixPadding;
        if (vad.silenceDuration) turnDetection.silence_duration_ms = vad.silenceDuration;

        // Semantic VAD specifics
        if (vad.type === 'semantic_vad') {
            if (vad.eagerness) turnDetection.eagerness = vad.eagerness;
        }

        // Azure Semantic VAD specifics
        if (vad.type === 'azure_semantic_vad' || vad.type === 'azure_semantic_vad_multilingual') {
            if (vad.removeFillerWords !== undefined) {
                turnDetection.remove_filler_words = vad.removeFillerWords;
            }
            if (vad.interruptResponse !== undefined) {
                turnDetection.interrupt_response = vad.interruptResponse;
            }
        }

        // Multilingual languages
        if (vad.type === 'azure_semantic_vad_multilingual' && vad.languages) {
            turnDetection.languages = vad.languages;
        }

        // End of Utterance Detection
        if (vad.endOfUtterance) {
            turnDetection.end_of_utterance_detection = {
                model: vad.endOfUtterance.model || 'semantic_detection_v1',
                threshold_level: vad.endOfUtterance.thresholdLevel || 'default',
                timeout_ms: vad.endOfUtterance.timeout || 1000
            };
        }

        return turnDetection;
    }

    /**
     * Construire la configuration Voice
     */
    buildVoiceConfig() {
        const voice = this.config.voice || {};

        const voiceConfig = {
            name: voice.name || 'en-US-AvaNeural',
            type: voice.type || 'azure-standard',
        };

        // Temperature (HD voices)
        if (voice.temperature !== undefined) {
            voiceConfig.temperature = voice.temperature;
        }

        // Speaking rate
        if (voice.rate) {
            voiceConfig.rate = voice.rate.toString();
        }

        return voiceConfig;
    }

    /**
     * Gérer les messages reçus
     */
    handleMessage(data) {
        // Message texte (JSON)
        if (typeof data === 'string') {
            try {
                const message = JSON.parse(data);
                this.handleTextMessage(message);
            } catch (error) {
                console.error('❌ Erreur parsing JSON:', error);
            }
        }
        // Message binaire (audio)
        else if (data instanceof ArrayBuffer) {
            this.handleAudioMessage(data);
        }
    }

    /**
     * Gérer les messages texte (événements)
     */
    handleTextMessage(message) {
        const { type } = message;

        console.log('📥 Message reçu:', type, message);

        switch (type) {
            // Session
            case 'session.created':
                this.sessionId = message.session.id;
                console.log('✅ Session créée:', this.sessionId);
                break;

            case 'session.updated':
                console.log('✅ Session mise à jour');
                break;

            // Conversation
            case 'conversation.item.created':
                console.log('💬 Item créé:', message.item);
                break;

            // Response
            case 'response.created':
                console.log('🤖 Réponse créée:', message.response.id);
                if (this.onResponseStart) {
                    this.onResponseStart(message.response);
                }
                break;

            case 'response.done':
                console.log('✅ Réponse terminée:', message.response.id);
                if (this.onResponseEnd) {
                    this.onResponseEnd(message.response);
                }
                break;

            // Audio delta
            case 'response.audio.delta':
                // Audio en base64
                if (message.delta) {
                    const audioData = this.base64ToArrayBuffer(message.delta);
                    this.playAudio(audioData);
                }
                break;

            case 'response.audio.done':
                console.log('🔊 Audio terminé');
                break;

            // Transcription
            case 'conversation.item.input_audio_transcription.completed':
                const transcript = message.transcript;
                console.log('📝 Transcription:', transcript);
                if (this.onTranscript) {
                    this.onTranscript(transcript);
                }
                break;

            // Audio timestamps
            case 'response.audio_timestamp.delta':
                console.log('⏱️ Timestamp:', message.text, message.audio_offset_ms);
                break;

            // Viseme
            case 'response.animation_viseme.delta':
                console.log('👄 Viseme:', message.viseme_id, message.audio_offset_ms);
                break;

            // Détection de parole utilisateur - INTERROMPRE L'AUDIO
            case 'input_audio_buffer.speech_started':
                console.log('🎤 Utilisateur commence à parler - Interruption audio');
                this.interruptAudio();
                if (this.onSpeechStarted) {
                    this.onSpeechStarted();
                }
                break;

            case 'input_audio_buffer.speech_stopped':
                console.log('🎤 Utilisateur a arrêté de parler');
                if (this.onSpeechStopped) {
                    this.onSpeechStopped();
                }
                break;

            // Function calls (tools)
            case 'response.function_call_arguments.delta':
                console.log('🔧 Function call delta:', message);
                // Démarrer le monitoring de patience pour ce tool
                if (message.name && message.call_id) {
                    this.toolMonitor.startMonitoring(message.name, message.call_id);
                }
                break;

            case 'response.function_call_arguments.done':
                console.log('🔧 Function call done:', message.name, message.arguments);
                // Ici on devrait appeler le backend pour exécuter la fonction
                // Pour l'instant on log juste
                if (this.onFunctionCall) {
                    this.onFunctionCall(message.name, message.arguments, message.call_id);
                }
                // REMARQUE: Ne PAS arrêter le monitoring ici car le tool n'est pas encore exécuté
                // Le monitoring s'arrêtera quand on recevra la réponse du tool
                break;

            // Erreur
            case 'error':
                console.error('❌ Erreur serveur:', message.error);
                if (this.onError) {
                    this.onError(message.error);
                }
                break;

            default:
                console.log('📨 Message non géré:', type);
        }
    }

    /**
     * Gérer les messages audio binaires
     */
    handleAudioMessage(arrayBuffer) {
        console.log('🔊 Audio binaire reçu:', arrayBuffer.byteLength, 'bytes');
        this.playAudio(arrayBuffer);
    }

    /**
     * Envoyer un événement
     */
    sendEvent(event) {
        if (!this.isConnected || !this.ws) {
            console.error('❌ WebSocket non connecté');
            return;
        }

        const message = JSON.stringify(event);
        this.ws.send(message);
    }

    /**
     * Démarrer l'enregistrement audio
     */
    async startRecording() {
        if (this.isRecording) {
            console.warn('⚠️ Enregistrement déjà en cours');
            return;
        }

        try {
            // Créer le contexte audio
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 24000
            });

            // Demander l'accès au micro
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 24000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                }
            });

            // Créer le source node
            const source = this.audioContext.createMediaStreamSource(this.mediaStream);

            // Créer le processor pour capturer l'audio
            const processor = this.audioContext.createScriptProcessor(4096, 1, 1);

            processor.onaudioprocess = (e) => {
                if (!this.isRecording) return;

                const inputData = e.inputBuffer.getChannelData(0);

                // Convertir Float32 en PCM16
                const pcm16 = this.float32ToPCM16(inputData);

                // Envoyer l'audio au serveur
                this.sendAudio(pcm16);
            };

            source.connect(processor);
            processor.connect(this.audioContext.destination);

            this.isRecording = true;
            console.log('🎤 Enregistrement démarré');

        } catch (error) {
            console.error('❌ Erreur accès micro:', error);
            throw error;
        }
    }

    /**
     * Arrêter l'enregistrement
     */
    stopRecording() {
        if (!this.isRecording) return;

        this.isRecording = false;

        // Arrêter les tracks
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        // Fermer le contexte audio
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        console.log('⏹️ Enregistrement arrêté');
    }

    /**
     * Envoyer l'audio au serveur
     */
    sendAudio(pcm16Data) {
        if (!this.isConnected || !this.ws) return;

        // Envoyer l'événement input_audio_buffer.append
        const event = {
            type: 'input_audio_buffer.append',
            audio: this.arrayBufferToBase64(pcm16Data.buffer)
        };

        this.sendEvent(event);
    }

    /**
     * Lire l'audio reçu (PCM16 raw audio)
     */
    async playAudio(arrayBuffer) {
        // Ajouter à la queue
        this.audioQueue.push(arrayBuffer);

        // Si on n'est pas déjà en train de jouer, démarrer la lecture
        if (!this.isPlayingAudio) {
            this.playNextAudioChunk();
        }
    }

    /**
     * Jouer le prochain chunk audio de la queue
     */
    async playNextAudioChunk() {
        if (this.audioQueue.length === 0) {
            this.isPlayingAudio = false;
            return;
        }

        this.isPlayingAudio = true;
        const arrayBuffer = this.audioQueue.shift();

        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 24000
            });
        }

        try {
            // L'audio est du PCM16 raw (16-bit signed integer, mono, 24kHz)
            // On doit le convertir en AudioBuffer manuellement
            const int16Array = new Int16Array(arrayBuffer);
            const float32Array = new Float32Array(int16Array.length);

            // Convertir PCM16 (-32768 to 32767) en Float32 (-1.0 to 1.0)
            for (let i = 0; i < int16Array.length; i++) {
                float32Array[i] = int16Array[i] / 32768.0;
            }

            // Créer un AudioBuffer
            const audioBuffer = this.audioContext.createBuffer(
                1,                          // 1 canal (mono)
                float32Array.length,        // nombre de samples
                24000                       // sample rate
            );

            // Copier les données dans le buffer
            audioBuffer.getChannelData(0).set(float32Array);

            // Arrêter l'ancien source s'il existe
            if (this.currentAudioSource) {
                try {
                    this.currentAudioSource.stop();
                } catch (e) {
                    // Ignorer les erreurs si déjà arrêté
                }
            }

            // Créer le nouveau source
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);
            this.currentAudioSource = source;

            // Quand ce chunk finit, jouer le suivant
            source.onended = () => {
                this.currentAudioSource = null;
                this.playNextAudioChunk();
            };

            // Jouer
            source.start(0);

            if (this.onAudioReceived) {
                this.onAudioReceived(audioBuffer);
            }

        } catch (error) {
            console.error('❌ Erreur lecture audio:', error);
            // Continuer avec le prochain chunk même en cas d'erreur
            this.playNextAudioChunk();
        }
    }

    /**
     * Envoyer un message texte
     */
    sendTextMessage(text) {
        const event = {
            type: 'conversation.item.create',
            item: {
                type: 'message',
                role: 'user',
                content: [
                    {
                        type: 'input_text',
                        text: text
                    }
                ]
            }
        };

        this.sendEvent(event);

        // Créer la réponse
        this.sendEvent({ type: 'response.create' });
    }

    /**
     * Soumettre le résultat d'un tool au modèle
     * @param {string} callId - L'ID de l'appel de fonction
     * @param {string} toolName - Le nom du tool
     * @param {string} output - La sortie du tool (JSON string)
     */
    submitToolResult(callId, toolName, output) {
        console.log(`📤 Soumission résultat tool: ${toolName} (ID: ${callId})`);

        // Arrêter le monitoring de patience pour ce tool
        this.toolMonitor.stopMonitoring(toolName);

        const event = {
            type: 'conversation.item.create',
            item: {
                type: 'function_call_output',
                call_id: callId,
                output: output
            }
        };

        this.sendEvent(event);

        // Créer la réponse pour que le modèle traite le résultat
        this.sendEvent({ type: 'response.create' });
    }

    /**
     * Interrompre l'audio en cours (quand l'utilisateur parle)
     */
    interruptAudio() {
        console.log('⚠️ Interruption de l\'audio en cours');

        // Arrêter l'audio source actuel
        if (this.currentAudioSource) {
            try {
                this.currentAudioSource.stop();
            } catch (e) {
                // Ignorer si déjà arrêté
            }
            this.currentAudioSource = null;
        }

        // Vider la queue audio pour éviter que les chunks en attente jouent
        this.audioQueue = [];
        this.isPlayingAudio = false;

        // Envoyer un événement pour annuler la réponse en cours
        this.sendEvent({ type: 'response.cancel' });

        console.log('✅ Audio interrompu et queue vidée');
    }

    /**
     * Fermer la connexion
     */
    disconnect() {
        this.stopRecording();

        // Nettoyer les timers de monitoring de patience
        if (this.toolMonitor) {
            this.toolMonitor.cleanup();
        }

        // Arrêter l'audio en cours
        if (this.currentAudioSource) {
            try {
                this.currentAudioSource.stop();
            } catch (e) {
                // Ignorer si déjà arrêté
            }
            this.currentAudioSource = null;
        }

        // Vider la queue audio
        this.audioQueue = [];
        this.isPlayingAudio = false;

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.isConnected = false;
        console.log('👋 Déconnecté');
    }

    // =============================================================================
    // UTILITAIRES
    // =============================================================================

    /**
     * Convertir Float32Array en PCM16
     */
    float32ToPCM16(float32Array) {
        const pcm16 = new Int16Array(float32Array.length);

        for (let i = 0; i < float32Array.length; i++) {
            let s = Math.max(-1, Math.min(1, float32Array[i]));
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        return pcm16;
    }

    /**
     * Convertir ArrayBuffer en Base64
     */
    arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        const len = bytes.byteLength;

        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }

        return btoa(binary);
    }

    /**
     * Convertir Base64 en ArrayBuffer
     */
    base64ToArrayBuffer(base64) {
        const binaryString = atob(base64);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);

        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }

        return bytes.buffer;
    }
}

// Export
window.VoiceLiveSession = VoiceLiveSession;
