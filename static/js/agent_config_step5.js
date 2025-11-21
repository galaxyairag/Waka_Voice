/**
 * Agent Configuration Step 5 - Test sur Smartphone
 * Implémentation WebSocket Voice Live
 */

// =============================================================================
// VARIABLES GLOBALES
// =============================================================================

let voiceLiveSession = null;
let isSessionActive = false;
let currentConfig = null;
let allToolsDefinitions = []; // Cache des définitions de tous les tools

// Éléments DOM
let voiceBtn, sendBtn, textInput, chatContainer;
let statusIndicator, connectionStatus;

// =============================================================================
// INITIALISATION
// =============================================================================

document.addEventListener('DOMContentLoaded', async function () {
    console.log('🚀 Initialisation Step 5 - Test Voice Live');

    // Récupérer les éléments DOM
    voiceBtn = document.getElementById('voiceBtn');
    sendBtn = document.getElementById('sendBtn');
    textInput = document.getElementById('textInput');
    chatContainer = document.getElementById('chatContainer');
    statusIndicator = document.getElementById('statusIndicator');
    connectionStatus = document.getElementById('connectionStatus');

    // Charger la configuration de l'agent
    try {
        // Charger les définitions des tools depuis le backend
        await loadToolsDefinitions();

        await loadAgentConfig();

        // Setup event listeners
        setupEventListeners();

        // Démarrer la session automatiquement
        await startVoiceLiveSession();

    } catch (error) {
        console.error('❌ Erreur initialisation:', error);
        updateConnectionStatus('Erreur', 'error');
    }
});

// =============================================================================
// CHARGEMENT CONFIG
// =============================================================================

/**
 * Charger les définitions de tous les tools depuis le backend
 */
async function loadToolsDefinitions() {
    try {
        console.log('📦 Chargement des définitions de tools...');
        const response = await fetch('/agents/api/tools');

        if (!response.ok) {
            throw new Error(`Erreur HTTP ${response.status}`);
        }

        const data = await response.json();
        if (data.success && data.tools) {
            allToolsDefinitions = data.tools;
            console.log(`✅ ${allToolsDefinitions.length} tools chargés:`, allToolsDefinitions.map(t => t.name));
        } else {
            console.warn('⚠️ Aucun tool disponible');
            allToolsDefinitions = [];
        }
    } catch (error) {
        console.error('❌ Erreur chargement tools:', error);
        allToolsDefinitions = [];
    }
}

/**
 * Charger la configuration de l'agent depuis le serveur
 */
async function loadAgentConfig() {
    try {
        // Récupérer l'agent_id depuis l'URL
        const pathParts = window.location.pathname.split('/');
        const agentId = pathParts[pathParts.indexOf('config') + 1];

        console.log('📍 URL actuelle:', window.location.pathname);
        console.log('📍 Path parts:', pathParts);
        console.log('📥 Chargement configuration agent:', agentId);

        if (!agentId || agentId === 'step5') {
            throw new Error('Agent ID non trouvé dans l\'URL. Format attendu: /agents/config/<agent_id>/step5');
        }

        const apiUrl = `/agents/api/config/${agentId}`;
        console.log('📡 Appel API:', apiUrl);

        const response = await fetch(apiUrl);

        console.log('📡 Réponse HTTP:', response.status, response.statusText);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        currentConfig = await response.json();
        console.log('✅ Configuration chargée:', currentConfig);

        // Vérifier les champs critiques
        if (!currentConfig.speech_endpoint) {
            console.warn('⚠️ speech_endpoint manquant dans la config');
        }
        if (!currentConfig.speech_key) {
            console.warn('⚠️ speech_key manquant dans la config');
        }

        // Afficher les infos dans l'UI
        updateUIWithConfig(currentConfig);

    } catch (error) {
        console.error('❌ Erreur chargement config:', error);
        addSystemMessage('Erreur de chargement de la configuration: ' + error.message);
        throw error; // Re-throw pour bloquer startVoiceLiveSession
    }
}

/**
 * Mettre à jour l'UI avec la config
 */
function updateUIWithConfig(config) {
    // Mettre à jour le header
    const agentNameEl = document.querySelector('.phone-header h2');
    if (agentNameEl && config.assistant_name) {
        agentNameEl.textContent = config.assistant_name;
    }

    const agentStatusEl = document.querySelector('.agent-status');
    if (agentStatusEl && config.role) {
        agentStatusEl.textContent = config.role;
    }
}

// =============================================================================
// SESSION VOICE LIVE
// =============================================================================

/**
 * Démarrer la session Voice Live
 */
async function startVoiceLiveSession() {
    if (isSessionActive) {
        console.warn('⚠️ Session déjà active');
        return;
    }

    try {
        // Vérifier que la config est chargée
        if (!currentConfig) {
            throw new Error('Configuration de l\'agent non chargée. Veuillez rafraîchir la page.');
        }

        console.log('🔧 Configuration actuelle:', currentConfig);
        updateConnectionStatus('Connexion...', 'connecting');

        // Construire la config pour Voice Live
        const sessionConfig = buildVoiceLiveConfig(currentConfig);
        console.log('🔧 Session config:', sessionConfig);

        // Créer la session
        voiceLiveSession = new VoiceLiveSession(sessionConfig);

        // Setup callbacks
        voiceLiveSession.onConnected = handleSessionConnected;
        voiceLiveSession.onDisconnected = handleSessionDisconnected;
        voiceLiveSession.onError = handleSessionError;
        voiceLiveSession.onTranscript = handleTranscript;
        voiceLiveSession.onAudioReceived = handleAudioReceived;
        voiceLiveSession.onResponseStart = handleResponseStart;
        voiceLiveSession.onResponseEnd = handleResponseEnd;
        voiceLiveSession.onFunctionCall = handleFunctionCall;

        // Connecter
        await voiceLiveSession.connect();

        isSessionActive = true;

    } catch (error) {
        console.error('❌ Erreur démarrage session:', error);
        const errorMsg = error.message || error.toString() || 'Erreur inconnue';
        updateConnectionStatus('Erreur de connexion', 'error');
        addSystemMessage('Impossible de démarrer la session: ' + errorMsg);
    }
}

/**
 * Construire la config Voice Live depuis la config agent
 */
function buildVoiceLiveConfig(agentConfig) {
    // Vérifier que agentConfig existe
    if (!agentConfig) {
        throw new Error('agentConfig est null ou undefined');
    }

    // Vérifier les paramètres requis
    if (!agentConfig.speech_endpoint) {
        throw new Error('speech_endpoint manquant dans la configuration');
    }
    if (!agentConfig.speech_key) {
        throw new Error('speech_key manquant dans la configuration');
    }

    const config = {
        // Endpoint Azure
        endpoint: agentConfig.speech_endpoint,
        apiKey: agentConfig.speech_key,
        apiVersion: '2025-10-01',  // Azure Voice Live API version

        // Model/Deployment name
        model: agentConfig.model_id || 'gpt-realtime-mini',
        // Note: agent_id/project_id ne sont pas supportés par tous les endpoints
        // agentId: agentConfig.agent_id || null,
        // projectId: agentConfig.project_id || null,

        // Instructions
        instructions: agentConfig.instructions || "You are a helpful AI assistant.",

        // Modalities
        modalities: ["text", "audio"],

        // VAD Configuration
        vadConfig: buildVADConfig(agentConfig),

        // Voice - récupérer depuis session_config.voice
        voice: {
            name: agentConfig.session_config?.voice?.name || 'en-US-AvaNeural',
            type: agentConfig.session_config?.voice?.type || 'azure-standard',
            temperature: agentConfig.session_config?.voice?.temperature || 0.8,
            rate: agentConfig.session_config?.voice?.rate || '1.0',
        },

        // Audio enhancements
        noiseReduction: agentConfig.noise_reduction !== false,
        echoCancellation: agentConfig.echo_cancellation !== false,

        // Input transcription
        inputTranscription: agentConfig.input_transcription ? {
            model: agentConfig.input_transcription_model || 'azure-speech',
            language: agentConfig.input_transcription_language || 'en'
        } : null,

        // Features
        audioTimestamps: agentConfig.audio_timestamps || false,
        visemeEnabled: agentConfig.viseme_enabled || false,

        // Tools - Ajouter les tools sélectionnés
        tools: buildToolsConfig(agentConfig),
    };

    return config;
}

/**
 * Construire la config VAD
 */
function buildVADConfig(agentConfig) {
    const vadConfig = {
        type: agentConfig.vad_type || 'server_vad',
        threshold: agentConfig.vad_threshold || 0.5,
        prefixPadding: agentConfig.vad_prefix_padding || 300,
        silenceDuration: agentConfig.vad_silence_duration || 500,
    };

    // Semantic VAD
    if (agentConfig.vad_type === 'semantic_vad') {
        vadConfig.eagerness = agentConfig.vad_eagerness || 'auto';
    }

    // Azure Semantic VAD
    if (agentConfig.vad_type === 'azure_semantic_vad' ||
        agentConfig.vad_type === 'azure_semantic_vad_multilingual') {

        vadConfig.removeFillerWords = agentConfig.vad_remove_filler_words || false;
        vadConfig.interruptResponse = agentConfig.vad_interrupt_response || false;
    }

    // Multilingual languages
    if (agentConfig.vad_type === 'azure_semantic_vad_multilingual') {
        vadConfig.languages = agentConfig.vad_languages || ['en'];
    }

    // End of Utterance Detection
    if (agentConfig.enable_end_of_utterance) {
        vadConfig.endOfUtterance = {
            model: agentConfig.end_of_utterance_model || 'semantic_detection_v1',
            thresholdLevel: agentConfig.threshold_level || 'default',
            timeout: agentConfig.timeout_ms || 1000
        };
    }

    return vadConfig;
}

/**
 * Construire la configuration des tools
 * Utilise les définitions chargées depuis le backend et filtre selon selected_tools
 */
function buildToolsConfig(agentConfig) {
    // Si pas de tools sélectionnés, retourner tableau vide
    if (!agentConfig.selected_tools || agentConfig.selected_tools.length === 0) {
        console.log('⚠️ Aucun tool sélectionné');
        return [];
    }

    // Si les définitions n'ont pas été chargées, retourner vide
    if (!allToolsDefinitions || allToolsDefinitions.length === 0) {
        console.error('❌ Les définitions de tools ne sont pas chargées');
        return [];
    }

    // Filtrer les tools : garder seulement ceux qui sont dans selected_tools
    const selectedTools = allToolsDefinitions.filter(toolDef => {
        // Vérifier si le nom du tool est dans la liste des selected_tools
        return agentConfig.selected_tools.includes(toolDef.name);
    });

    console.log(`✅ ${selectedTools.length} tools configurés sur ${agentConfig.selected_tools.length} sélectionnés:`);
    console.log('   Tools sélectionnés:', agentConfig.selected_tools);
    console.log('   Tools trouvés:', selectedTools.map(t => t.name));

    // Vérifier si certains tools n'ont pas été trouvés
    const notFound = agentConfig.selected_tools.filter(name =>
        !selectedTools.find(t => t.name === name)
    );
    if (notFound.length > 0) {
        console.warn(`⚠️ Tools non trouvés dans les définitions:`, notFound);
    }

    return selectedTools;
}

// =============================================================================
// CALLBACKS SESSION
// =============================================================================

function handleSessionConnected() {
    console.log('✅ Session Voice Live connectée');
    updateConnectionStatus('Connecté', 'connected');
    addSystemMessage('✅ Session Voice Live démarrée - Vous pouvez parler ou écrire');

    // Activer les boutons
    voiceBtn.disabled = false;
    sendBtn.disabled = false;
    textInput.disabled = false;
}

function handleSessionDisconnected(event) {
    console.log('🔌 Session déconnectée');
    updateConnectionStatus('Déconnecté', 'disconnected');
    addSystemMessage('⚠️ Session terminée');

    isSessionActive = false;

    // Désactiver les boutons
    voiceBtn.disabled = true;
    sendBtn.disabled = true;
    textInput.disabled = true;
}

function handleSessionError(error) {
    console.error('❌ Erreur session:', error);
    updateConnectionStatus('Erreur', 'error');
    addSystemMessage('❌ Erreur: ' + (error.message || JSON.stringify(error)));
}

function handleTranscript(transcript) {
    console.log('📝 Transcription:', transcript);

    // Afficher comme message utilisateur
    addMessage('user', transcript);
}

function handleAudioReceived(audioBuffer) {
    console.log('🔊 Audio reçu:', audioBuffer.duration, 'secondes');
    // L'audio est déjà joué par la session
}

function handleResponseStart(response) {
    console.log('🤖 Réponse démarrée:', response.id);

    // Afficher un indicateur
    showTypingIndicator();
}

function handleResponseEnd(response) {
    console.log('✅ Réponse terminée:', response.id);

    // Masquer l'indicateur
    hideTypingIndicator();

    // Extraire le texte de la réponse
    if (response.output && response.output.length > 0) {
        const output = response.output[0];

        if (output.content && output.content.length > 0) {
            const content = output.content[0];

            if (content.text) {
                addMessage('assistant', content.text);
            }
        }
    }
}

/**
 * Gérer les appels de fonction (tools)
 */
async function handleFunctionCall(functionName, functionArgs, callId) {
    console.log(`🔧 Function call: ${functionName}`, functionArgs);

    // Afficher dans l'interface qu'un tool est appelé
    addSystemMessage(`🔧 Exécution de: ${functionName}`);

    try {
        // Parser les arguments si c'est une string JSON
        let parsedArgs = functionArgs;
        if (typeof functionArgs === 'string') {
            try {
                parsedArgs = JSON.parse(functionArgs);
            } catch (e) {
                console.warn('Arguments déjà parsés ou invalides:', functionArgs);
            }
        }

        console.log(`📤 Envoi au backend - Tool: ${functionName}, Args:`, parsedArgs);

        // Appeler le backend pour exécuter le tool
        const response = await fetch('/agents/api/execute-tool', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tool_name: functionName,
                arguments: parsedArgs
            })
        });

        if (!response.ok) {
            throw new Error(`Erreur HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        console.log(`✅ Résultat reçu pour ${functionName}:`, result);

        // Soumettre le résultat au modèle via WebSocket
        // Cette méthode arrête automatiquement le monitoring de patience
        voiceLiveSession.submitToolResult(
            callId,
            functionName,
            JSON.stringify(result)
        );

        addSystemMessage(`✅ ${functionName} exécuté avec succès`);

    } catch (error) {
        console.error(`❌ Erreur exécution tool ${functionName}:`, error);

        // En cas d'erreur, soumettre un message d'erreur au modèle
        const errorResult = {
            error: true,
            message: error.message || 'Erreur inconnue',
            tool: functionName
        };

        voiceLiveSession.submitToolResult(
            callId,
            functionName,
            JSON.stringify(errorResult)
        );

        addSystemMessage(`❌ Erreur: ${error.message}`);
    }
}

// =============================================================================
// UI - MESSAGES
// =============================================================================

/**
 * Ajouter un message au chat
 */
function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    bubbleDiv.textContent = content;

    messageDiv.appendChild(bubbleDiv);
    chatContainer.appendChild(messageDiv);

    // Scroll vers le bas
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Ajouter un message système
 */
function addSystemMessage(content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    bubbleDiv.textContent = content;

    messageDiv.appendChild(bubbleDiv);
    chatContainer.appendChild(messageDiv);

    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Afficher l'indicateur de frappe
 */
function showTypingIndicator() {
    // Supprimer l'indicateur existant
    hideTypingIndicator();

    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'message assistant';
    indicatorDiv.id = 'typingIndicator';

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    bubbleDiv.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';

    indicatorDiv.appendChild(bubbleDiv);
    chatContainer.appendChild(indicatorDiv);

    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Masquer l'indicateur de frappe
 */
function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

/**
 * Mettre à jour le statut de connexion
 */
function updateConnectionStatus(text, status) {
    if (connectionStatus) {
        connectionStatus.textContent = text;
        connectionStatus.className = `connection-status ${status}`;
    }

    if (statusIndicator) {
        statusIndicator.className = `status-indicator ${status}`;
    }
}

// =============================================================================
// EVENT LISTENERS
// =============================================================================

function setupEventListeners() {
    // Bouton voix - Push-to-talk
    voiceBtn.addEventListener('mousedown', handleVoiceStart);
    voiceBtn.addEventListener('mouseup', handleVoiceEnd);
    voiceBtn.addEventListener('touchstart', handleVoiceStart);
    voiceBtn.addEventListener('touchend', handleVoiceEnd);

    // Bouton envoi texte
    sendBtn.addEventListener('click', sendTextMessage);

    // Enter pour envoyer
    textInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendTextMessage();
        }
    });
}

/**
 * Démarrer l'enregistrement vocal
 */
async function handleVoiceStart(e) {
    e.preventDefault();

    if (!isSessionActive || !voiceLiveSession) {
        addSystemMessage('⚠️ Session non active');
        return;
    }

    try {
        voiceBtn.classList.add('recording');
        addSystemMessage('🎤 Enregistrement...');

        await voiceLiveSession.startRecording();

    } catch (error) {
        console.error('❌ Erreur enregistrement:', error);
        addSystemMessage('❌ Impossible d\'accéder au microphone');
        voiceBtn.classList.remove('recording');
    }
}

/**
 * Arrêter l'enregistrement vocal
 */
function handleVoiceEnd(e) {
    e.preventDefault();

    if (!voiceLiveSession) return;

    voiceBtn.classList.remove('recording');
    voiceLiveSession.stopRecording();
}

/**
 * Envoyer un message texte
 */
function sendTextMessage() {
    const text = textInput.value.trim();

    if (!text) return;

    if (!isSessionActive || !voiceLiveSession) {
        addSystemMessage('⚠️ Session non active');
        return;
    }

    // Afficher le message
    addMessage('user', text);

    // Envoyer via Voice Live
    voiceLiveSession.sendTextMessage(text);

    // Vider l'input
    textInput.value = '';
}

// =============================================================================
// CLEANUP
// =============================================================================

// Fermer la session au déchargement
window.addEventListener('beforeunload', () => {
    if (voiceLiveSession) {
        voiceLiveSession.disconnect();
    }
});
