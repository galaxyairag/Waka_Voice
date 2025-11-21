// ============================================
// AGENT VOICE SESSION - JAVASCRIPT
// WebSocket, Audio Recording/Playback, UI
// ============================================

// Global variables
let websocket = null;
let audioContext = null;
let audioProcessor = null;
let playbackContext = null;
let nextPlaybackTime = 0;
const MAX_AUDIO_LAG = 0.5;
let activeSources = [];
let currentResponseId = null;
let audioQueue = [];
let isProcessingQueue = false;
let isResponseActive = false;
let isSpeaking = false;
let sessionTokens = null;
let pendingFunctionCalls = new Map();

// Generate or retrieve call ID
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

const existingCallId = sessionStorage.getItem('current_call_id');
if (existingCallId) {
    window.callId = existingCallId;
    console.log('📞 Resuming call:', window.callId);
} else {
    window.callId = generateUUID();
    sessionStorage.setItem('current_call_id', window.callId);
    console.log('🆕 New call created:', window.callId);
}

// Update call ID display
if (document.getElementById('callIdDisplay')) {
    document.getElementById('callIdDisplay').textContent = window.callId.substring(0, 8) + '...';
}

// ============================================
// STATUS BAR CLOCK
// ============================================

function updateStatusTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const timeElement = document.getElementById('statusTime');
    if (timeElement) {
        timeElement.textContent = `${hours}:${minutes}`;
    }
}
updateStatusTime();
setInterval(updateStatusTime, 60000);

// ============================================
// CONFIG PANEL TOGGLE
// ============================================

function toggleConfig() {
    const panel = document.getElementById('configPanel');
    if (panel) {
        panel.classList.toggle('show');
    }
}

// ============================================
// CONVERSATION MANAGEMENT
// ============================================

async function saveMessageToCosmosDB(role, content, metadata = {}) {
    try {
        const response = await fetch('/agents/api/conversation/save-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                call_id: window.callId,
                agent_id: window.agentConfig.agentId,
                message_type: role,
                content: content,
                model: window.agentConfig.modelId,
                metadata: metadata
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to save message: ${response.statusText}`);
        }

        console.log(`💾 Message saved: ${role}`);
    } catch (error) {
        console.error('❌ Error saving message:', error);
    }
}

async function endConversationInCosmosDB() {
    try {
        const response = await fetch('/agents/api/conversation/end', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                call_id: window.callId,
                agent_id: window.agentConfig.agentId,
                tokens: sessionTokens,
                timestamp: new Date().toISOString()
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to end conversation: ${response.statusText}`);
        }

        console.log('✅ Conversation ended in Cosmos DB');
    } catch (error) {
        console.error('❌ Error ending conversation:', error);
    }
}

function startNewConversation() {
    sessionStorage.removeItem('current_call_id');
    window.callId = generateUUID();
    sessionStorage.setItem('current_call_id', window.callId);

    if (document.getElementById('callIdDisplay')) {
        document.getElementById('callIdDisplay').textContent = window.callId.substring(0, 8) + '...';
    }

    document.getElementById('conversationDisplay').innerHTML = '';
    addMessage('system', '🆕 Nouvelle conversation démarrée');
    console.log('🆕 New conversation started:', window.callId);
}

// ============================================
// WEBSOCKET CONNECTION
// ============================================

async function startConversation() {
    console.log('🎙️ Starting conversation...');
    updateConnectionStatus('connecting', 'Connexion...');

    document.getElementById('startButton').style.display = 'none';
    document.getElementById('stopButton').style.display = 'block';
    document.getElementById('stopButton').classList.add('recording');

    try {
        await connectWebSocket();
        await startAudioRecording();
        startAudioVisualizer(null);
        addMessage('system', '✅ Conversation démarrée');
    } catch (error) {
        console.error('❌ Error starting conversation:', error);
        addMessage('system', '❌ Erreur: ' + error.message);
        resetUI();
    }
}

function stopConversation() {
    console.log('🛑 Stopping conversation...');

    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.close();
    }

    if (audioProcessor) {
        audioProcessor.disconnect();
        audioProcessor = null;
    }

    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }

    stopAudioVisualizer();
    stopAllAudio();
    resetUI();
    updateConnectionStatus('disconnected', 'Déconnecté');

    endConversationInCosmosDB();

    addMessage('system', '👋 Conversation terminée');
}

async function connectWebSocket() {
    return new Promise((resolve, reject) => {
        // Vérifier que agentConfig existe
        if (!window.agentConfig) {
            console.error('❌ window.agentConfig is not defined');
            reject(new Error('Configuration de l\'agent non disponible'));
            return;
        }

        const wsUrl = window.agentConfig.websocketUrl || 'wss://voice-live.openai.azure.com/openai/realtime';

        try {
            websocket = new WebSocket(wsUrl);
        } catch (error) {
            console.error('❌ Failed to create WebSocket:', error);
            reject(new Error('Impossible de créer la connexion WebSocket'));
            return;
        }

        websocket.onopen = () => {
            console.log('✅ WebSocket connected');
            updateConnectionStatus('connected', 'Connecté');

            const sessionConfig = {
                type: 'session.update',
                session: {
                    modalities: window.agentConfig.modalities || ['text', 'audio'],
                    instructions: window.agentConfig.instructions || '',
                    input_audio_format: 'pcm16',
                    output_audio_format: 'pcm16',
                    input_audio_transcription: {
                        model: 'whisper-1'
                    },
                    turn_detection: {
                        type: 'server_vad',
                        threshold: 0.5,
                        prefix_padding_ms: 300,
                        silence_duration_ms: 500
                    },
                    tools: window.agentConfig.tools || [],
                    tool_choice: 'auto',
                    temperature: window.agentConfig.temperature || 0.8,
                    max_response_output_tokens: window.agentConfig.maxTokens || 4096
                }
            };

            // Configure voice based on Voice Live API documentation
            // https://learn.microsoft.com/en-us/azure/ai-services/speech-service/voice-live-how-to-customize
            console.log('🎤 Voice config from agentConfig:', window.agentConfig.voice);

            if (window.agentConfig.voice) {
                const voiceName = window.agentConfig.voice.name || window.agentConfig.voice;
                const voiceType = window.agentConfig.voice.type || 'azure-standard';

                console.log('🎤 Voice name:', voiceName, 'Type:', voiceType);

                // Voice Live supports voice as object with type, name, temperature, custom_lexicon_url
                sessionConfig.session.voice = {
                    type: voiceType,
                    name: voiceName
                };

                // Add temperature if specified (optional, range 0.0-1.0, only for HD voices)
                if (window.agentConfig.voice.temperature !== null && window.agentConfig.voice.temperature !== undefined) {
                    sessionConfig.session.voice.temperature = window.agentConfig.voice.temperature;
                }

                // Add custom_lexicon_url if specified
                if (window.agentConfig.customLexiconUrl) {
                    sessionConfig.session.voice.custom_lexicon_url = window.agentConfig.customLexiconUrl;
                }
            } else {
                console.log('⚠️ No voice config found, using default');
                // Default voice for Azure Voice Live
                sessionConfig.session.voice = {
                    type: 'azure-standard',
                    name: 'en-US-AndrewMultilingualNeural'
                };
            }

            if (window.agentConfig.customLexiconUrl) {
                sessionConfig.session.pronunciation_lexicons = [{
                    url: window.agentConfig.customLexiconUrl
                }];
            }

            console.log('🔍 Voice in sessionConfig BEFORE stringify:', sessionConfig.session.voice);
            console.log('📤 Session config:', JSON.stringify(sessionConfig, null, 2));
            websocket.send(JSON.stringify(sessionConfig));
            console.log('📤 Session config sent');
            resolve();
        };

        websocket.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            updateConnectionStatus('disconnected', 'Erreur de connexion');
            reject(new Error('Erreur de connexion WebSocket'));
        }; websocket.onclose = () => {
            console.log('🔌 WebSocket disconnected');
            updateConnectionStatus('disconnected', 'Déconnecté');
        };

        websocket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                handleWebSocketMessage(message);
            } catch (error) {
                console.error('❌ Error parsing message:', error);
            }
        };
    });
}

// ============================================
// WEBSOCKET MESSAGE HANDLING
// ============================================

function handleWebSocketMessage(message) {
    const messageType = message.type;

    switch (messageType) {
        case 'session.created':
        case 'session.updated':
            console.log('✅ Session ready:', messageType);
            break;

        case 'response.audio.delta':
            if (message.delta && message.response_id) {
                playAudioChunk(message.delta, message.response_id);
            }
            break;

        case 'response.audio_transcript.delta':
            if (message.delta) {
                addOrUpdateMessage('agent', message.delta, 'agent-transcript');
            }
            break;

        case 'response.audio_transcript.done':
            if (message.transcript && message.transcript !== '<|audio_text|>') {
                saveMessageToCosmosDB('agent', message.transcript);
            }
            break;

        case 'conversation.item.input_audio_transcription.completed':
            if (message.transcript) {
                addMessage('user', message.transcript);
                saveMessageToCosmosDB('user', message.transcript);
            }
            break;

        case 'response.output_item.added':
            if (message.response_id && message.response_id !== currentResponseId) {
                currentResponseId = message.response_id;
                console.log('🆕 New response starting:', currentResponseId);
            }

            if (message.item && message.item.type === 'function_call') {
                const callId = message.item.call_id;
                const toolName = message.item.name;

                if (!pendingFunctionCalls.has(callId)) {
                    pendingFunctionCalls.set(callId, {
                        name: toolName,
                        arguments: ''
                    });
                } else {
                    pendingFunctionCalls.get(callId).name = toolName;
                }

                console.log('🔧 Tool call detected:', toolName);
                addMessage('system', `🔧 Utilisation de l'outil: ${toolName}...`);
            }
            break;

        case 'response.created':
            console.log('🆕 New response created');
            stopAllAudio();
            isResponseActive = true;
            break;

        case 'input_audio_buffer.speech_started':
            console.log('🎤 User started speaking - INTERRUPTING AI audio');
            stopAllAudio();
            currentResponseId = null;
            isSpeaking = false;

            if (isResponseActive && websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({
                    type: 'response.cancel'
                }));
                console.log('📤 Sent response.cancel to server');
                isResponseActive = false;
            }

            addMessage('system', '🎤 Interruption détectée');
            break;

        case 'response.cancelled':
            console.log('🚫 Response cancelled - stopping audio');
            stopAllAudio();
            currentResponseId = null;
            isSpeaking = false;
            isResponseActive = false;
            break;

        case 'response.function_call_arguments.delta':
            if (!pendingFunctionCalls.has(message.call_id)) {
                pendingFunctionCalls.set(message.call_id, {
                    name: 'unknown',
                    arguments: ''
                });
            }
            pendingFunctionCalls.get(message.call_id).arguments += message.delta;
            break;

        case 'response.function_call_arguments.done':
            if (pendingFunctionCalls.has(message.call_id)) {
                const functionCall = pendingFunctionCalls.get(message.call_id);
                console.log('🔧 Tool call done:', functionCall.name, functionCall.arguments);
                executeToolCall(message.call_id, functionCall.name, functionCall.arguments);
                pendingFunctionCalls.delete(message.call_id);
            }
            break;

        case 'response.done':
            console.log('📊 Response.done complete');

            if (message.response && message.response.output) {
                for (const item of message.response.output) {
                    if (item.type === 'message' && item.content) {
                        for (const content of item.content) {
                            if (content.type === 'audio' && content.transcript) {
                                if (content.transcript !== '<|audio_text|>') {
                                    saveMessageToCosmosDB('agent', content.transcript);
                                }
                            }
                        }
                    }
                }
            }

            if (message.response && message.response.usage) {
                sessionTokens = {
                    inputs_text_tokens: message.response.usage.input_token_details?.text_tokens || 0,
                    inputs_cached_tokens: message.response.usage.input_token_details?.cached_tokens || 0,
                    inputs_audio_tokens: message.response.usage.input_token_details?.audio_tokens || 0,
                    outputs_text_tokens: message.response.usage.output_token_details?.text_tokens || 0,
                    outputs_audio_tokens: message.response.usage.output_token_details?.audio_tokens || 0
                };
                console.log('📊 Tokens updated:', sessionTokens);
            }

            isResponseActive = false;
            break;

        case 'error':
            console.error('❌ Server error:', message.error);
            addMessage('system', 'Erreur: ' + message.error.message);
            break;
    }
}

// ============================================
// AUDIO RECORDING
// ============================================

async function startAudioRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                sampleRate: 24000,
                echoCancellation: true,
                noiseSuppression: true
            }
        });

        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
        const source = audioContext.createMediaStreamSource(stream);
        audioProcessor = audioContext.createScriptProcessor(4096, 1, 1);

        source.connect(audioProcessor);
        audioProcessor.connect(audioContext.destination);

        audioProcessor.onaudioprocess = (e) => {
            const inputData = e.inputBuffer.getChannelData(0);

            let sum = 0;
            for (let i = 0; i < inputData.length; i++) {
                sum += inputData[i] * inputData[i];
            }
            const rms = Math.sqrt(sum / inputData.length);
            const isSpeakingNow = rms > 0.01;

            if (isSpeakingNow && isSpeaking) {
                console.log('🎤 LOCAL INTERRUPT: User speaking detected while AI is talking');
                stopAllAudio();
                currentResponseId = null;
                isSpeaking = false;

                if (isResponseActive && websocket && websocket.readyState === WebSocket.OPEN) {
                    websocket.send(JSON.stringify({
                        type: 'response.cancel'
                    }));
                    isResponseActive = false;
                }
            }

            if (isSpeaking) {
                return;
            }

            if (websocket && websocket.readyState === WebSocket.OPEN) {
                const pcmData = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    const s = Math.max(-1, Math.min(1, inputData[i]));
                    pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }

                const evenLength = pcmData.length % 2 === 0 ? pcmData.length : pcmData.length - 1;
                const evenPcmData = pcmData.slice(0, evenLength);
                const base64Audio = arrayBufferToBase64(evenPcmData.buffer);

                websocket.send(JSON.stringify({
                    type: 'input_audio_buffer.append',
                    audio: base64Audio
                }));
            }
        };

        startAudioVisualizer(stream);
        console.log('🎤 Audio recording started');
    } catch (error) {
        console.error('❌ Error accessing microphone:', error);
        throw new Error('Impossible d\'accéder au microphone');
    }
}

function arrayBufferToBase64(buffer) {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
}

// ============================================
// AUDIO VISUALIZER
// ============================================

function startAudioVisualizer(stream) {
    if (stream) {
        const analyserContext = new (window.AudioContext || window.webkitAudioContext)();
        const analyser = analyserContext.createAnalyser();
        const microphone = analyserContext.createMediaStreamSource(stream);

        microphone.connect(analyser);
        analyser.fftSize = 64;

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        const bars = document.querySelectorAll('.visualizer-bar');

        function animate() {
            if (!audioContext) return;

            requestAnimationFrame(animate);
            analyser.getByteFrequencyData(dataArray);

            bars.forEach((bar, index) => {
                const value = dataArray[index] || 0;
                const height = (value / 255) * 40 + 10;
                bar.style.height = height + 'px';
                bar.classList.add('active');
            });
        }

        animate();
    } else {
        const bars = document.querySelectorAll('.visualizer-bar');
        bars.forEach(bar => bar.classList.add('active'));
    }
}

function stopAudioVisualizer() {
    const bars = document.querySelectorAll('.visualizer-bar');
    bars.forEach(bar => {
        bar.style.height = '15px';
        bar.classList.remove('active');
    });
}

// ============================================
// AUDIO PLAYBACK
// ============================================

function stopAllAudio() {
    console.log('🔇 Stopping ALL audio - sources:', activeSources.length, 'queued:', audioQueue.length);

    activeSources.forEach(source => {
        try {
            source.stop(0);
            source.disconnect();
        } catch (e) {
            // Ignore
        }
    });
    activeSources = [];

    audioQueue = [];
    isProcessingQueue = false;

    if (playbackContext) {
        try {
            playbackContext.suspend().then(() => {
                playbackContext.close();
            }).catch(e => {
                // Ignore
            });
        } catch (e) {
            // Ignore
        }
        playbackContext = null;
    }

    nextPlaybackTime = 0;
    console.log('🔇 ✅ All audio stopped and context reset');
}

async function processAudioQueue() {
    if (isProcessingQueue || audioQueue.length === 0) {
        return;
    }

    isProcessingQueue = true;

    while (audioQueue.length > 0) {
        const { base64Audio, responseId } = audioQueue.shift();

        if (responseId !== currentResponseId) {
            console.log(`🚫 Skipping queued audio from old response: ${responseId}`);
            continue;
        }

        try {
            await playAudioChunkNow(base64Audio, responseId);
        } catch (error) {
            console.error('❌ Error playing audio chunk:', error);
        }
    }

    isProcessingQueue = false;
}

function playAudioChunk(base64Audio, responseId) {
    audioQueue.push({ base64Audio, responseId });
    processAudioQueue();
}

function playAudioChunkNow(base64Audio, responseId) {
    return new Promise((resolve) => {
        if (!currentResponseId || responseId !== currentResponseId) {
            console.log(`🚫 Skipping audio chunk from cancelled/old response: ${responseId}`);
            resolve();
            return;
        }

        isSpeaking = true;

        const audioData = atob(base64Audio);
        const arrayBuffer = new ArrayBuffer(audioData.length);
        const view = new Uint8Array(arrayBuffer);

        for (let i = 0; i < audioData.length; i++) {
            view[i] = audioData.charCodeAt(i);
        }

        const pcm16 = new Int16Array(arrayBuffer);
        const float32 = new Float32Array(pcm16.length);
        for (let i = 0; i < pcm16.length; i++) {
            float32[i] = pcm16[i] / 32768.0;
        }

        if (!playbackContext) {
            playbackContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
            nextPlaybackTime = playbackContext.currentTime;
        }

        const audioBuffer = playbackContext.createBuffer(1, float32.length, 24000);
        audioBuffer.getChannelData(0).set(float32);

        const source = playbackContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(playbackContext.destination);

        const now = playbackContext.currentTime;
        const startTime = Math.max(now, Math.min(nextPlaybackTime, now + MAX_AUDIO_LAG));
        source.start(startTime);

        activeSources.push(source);

        source.onended = () => {
            const index = activeSources.indexOf(source);
            if (index > -1) {
                activeSources.splice(index, 1);
            }

            if (activeSources.length === 0 && audioQueue.length === 0) {
                isSpeaking = false;
                console.log('🎤 Assistant terminé - Micro réactivé');
            }

            resolve();
        };

        nextPlaybackTime = startTime + audioBuffer.duration;
        console.log(`🔊 Audio chunk playing (lag: ${Math.round((startTime - now) * 1000)}ms, queue: ${audioQueue.length})`);
    });
}

// ============================================
// TOOL EXECUTION
// ============================================

async function executeToolCall(callId, toolName, argumentsJson) {
    console.log(`🔧 Executing tool: ${toolName}`);

    try {
        if (!toolName || toolName === 'unknown') {
            throw new Error('Tool name is missing or unknown');
        }

        if (!window.agentConfig || !window.agentConfig.agentId) {
            throw new Error('Agent configuration not available');
        }

        const args = JSON.parse(argumentsJson);
        args.call_id = window.callId;

        const response = await fetch('/api/tools/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tool_name: toolName,
                arguments: args,
                agent_id: window.agentConfig.agentId
            })
        }); if (!response.ok) {
            throw new Error(`Backend returned ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        console.log('✅ Tool result:', result);

        saveMessageToCosmosDB('tool', `Tool ${toolName} executed`, {
            tool_name: toolName,
            arguments: args,
            result: result
        });

        if (toolName === 'end_conversation' && result.action === 'end_conversation') {
            console.log('🛑 end_conversation tool detected - triggering automatic conversation end');
            setTimeout(() => {
                stopConversation();
            }, 2000);
        }

        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({
                type: 'conversation.item.create',
                item: {
                    type: 'function_call_output',
                    call_id: callId,
                    output: JSON.stringify(result)
                }
            }));

            websocket.send(JSON.stringify({
                type: 'response.create'
            }));
        }

        addMessage('system', `✅ ${toolName} exécuté avec succès`);

    } catch (error) {
        console.error('❌ Tool execution error:', error);
        addMessage('system', `❌ Erreur lors de l'exécution de ${toolName}`);

        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({
                type: 'conversation.item.create',
                item: {
                    type: 'function_call_output',
                    call_id: callId,
                    output: JSON.stringify({ error: error.message })
                }
            }));
        }
    }
}

// ============================================
// UI HELPERS
// ============================================

function updateConnectionStatus(status, text) {
    const statusElement = document.getElementById('connectionStatus');
    if (statusElement) {
        statusElement.className = 'status-indicator ' + status;
        const textSpan = statusElement.querySelector('.status-text');
        if (textSpan) {
            textSpan.textContent = text;
        }
    }
}

function addMessage(type, content, id = null) {
    const display = document.getElementById('conversationDisplay');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ' + type;
    if (id) messageDiv.dataset.messageId = id;

    const time = new Date().toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit'
    });

    messageDiv.innerHTML = `
        <div>${content}</div>
        <div class="message-meta">${time}</div>
    `;

    display.appendChild(messageDiv);
    display.scrollTop = display.scrollHeight;
}

function addOrUpdateMessage(type, content, id) {
    const display = document.getElementById('conversationDisplay');
    let messageDiv = display.querySelector(`[data-message-id="${id}"]`);

    if (messageDiv) {
        messageDiv.querySelector('div:first-child').textContent += content;
    } else {
        addMessage(type, content, id);
    }

    display.scrollTop = display.scrollHeight;
}

function resetUI() {
    document.getElementById('startButton').style.display = 'block';
    document.getElementById('stopButton').style.display = 'none';
    document.getElementById('stopButton').classList.remove('recording');
}

// ============================================
// INSTRUCTIONS & LEXICON EDITORS
// ============================================

function toggleInstructionsEditor() {
    const display = document.getElementById('instructionsDisplay');
    const editor = document.getElementById('instructionsEditor');

    if (editor.style.display === 'none') {
        display.style.display = 'none';
        editor.style.display = 'block';
    } else {
        display.style.display = 'block';
        editor.style.display = 'none';
    }
}

function cancelInstructionsEdit() {
    document.getElementById('instructionsDisplay').style.display = 'block';
    document.getElementById('instructionsEditor').style.display = 'none';
}

async function saveInstructions() {
    const newInstructions = document.getElementById('instructionsTextarea').value;

    if (!window.agentConfig || !window.agentConfig.agentId) {
        addMessage('system', '❌ Configuration de l\'agent non disponible');
        return;
    }

    try {
        const response = await fetch(`/agents/api/${window.agentConfig.agentId}/update_session_config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                instructions: newInstructions
            })
        });

        const result = await response.json();

        if (result.success) {
            document.getElementById('instructionsDisplay').innerHTML = newInstructions.substring(0, 200) + (newInstructions.length > 200 ? '...' : '');
            window.agentConfig.instructions = newInstructions;
            cancelInstructionsEdit();
            addMessage('system', '✅ Instructions mises à jour avec succès');
            console.log('✅ Instructions saved successfully');
        } else {
            throw new Error(result.error || 'Erreur lors de la sauvegarde');
        }
    } catch (error) {
        console.error('❌ Error saving instructions:', error);
        addMessage('system', `❌ Erreur: ${error.message}`);
    }
}

function toggleLexiconEditor() {
    const display = document.getElementById('lexiconDisplay');
    const editor = document.getElementById('lexiconEditor');

    if (editor.style.display === 'none') {
        display.style.display = 'none';
        editor.style.display = 'block';
    } else {
        display.style.display = 'block';
        editor.style.display = 'none';
    }
}

function cancelLexiconEdit() {
    document.getElementById('lexiconDisplay').style.display = 'block';
    document.getElementById('lexiconEditor').style.display = 'none';
}

async function saveLexiconUrl() {
    const newLexiconUrl = document.getElementById('lexiconUrlInput').value;

    if (!window.agentConfig || !window.agentConfig.agentId) {
        addMessage('system', '❌ Configuration de l\'agent non disponible');
        return;
    }

    try {
        const response = await fetch(`/agents/api/${window.agentConfig.agentId}/update_session_config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                custom_lexicon_url: newLexiconUrl
            })
        });

        const result = await response.json();

        if (result.success) {
            document.getElementById('lexiconUrlText').textContent = newLexiconUrl || 'Aucun lexique configuré';
            cancelLexiconEdit();
            addMessage('system', '✅ URL du lexique mise à jour avec succès');
            console.log('✅ Lexicon URL saved successfully');
        } else {
            throw new Error(result.error || 'Erreur lors de la sauvegarde');
        }
    } catch (error) {
        console.error('❌ Error saving lexicon URL:', error);
        addMessage('system', `❌ Erreur: ${error.message}`);
    }
}

// ============================================
// INITIALIZATION
// ============================================

console.log('✅ Voice Session Client Ready');
if (window.agentConfig) {
    console.log('🤖 Agent:', window.agentConfig.agentName || 'Non défini');
    console.log('🎯 Model:', window.agentConfig.modelId || 'Non défini');
    console.log('🔧 Tools:', (window.agentConfig.tools && window.agentConfig.tools.length) || 0);
} else {
    console.warn('⚠️ window.agentConfig not yet initialized. Will be set by template.');
}
