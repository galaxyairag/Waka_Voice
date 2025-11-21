// ============================================
// VOICE SESSION CLIENT (v2.0 - Modular)
// Teams-inspired interface with full avatar support
// Last updated: 2025-01-19
// ============================================

console.log('🔧 Voice Session Script Version: 2.0');
console.log('📅 Loaded at:', new Date().toISOString());

// ============================================
// GLOBAL VARIABLES
// ============================================

let websocket = null;
let isRecording = false;
let mediaRecorder = null;
let audioContext = null;
let audioChunks = [];
window.callId = null;
let sessionTokens = null;

// Avatar variables
let avatarCombinedStream = null;
let avatarSynthesizer = null;
let peerConnection = null;
let sdpSent = false;
let serverIceServers = null;

// Audio playback variables
let playbackContext = null;
let nextPlaybackTime = 0;
const MAX_AUDIO_LAG = 0.5;
let activeSources = [];
let currentResponseId = null;

// Audio queue for sequential playback
let audioQueue = [];
let isProcessingQueue = false;

// Pending function calls
let pendingFunctionCalls = new Map();

// Agent configuration from window.AGENT_CONFIG (set by template)
const agentConfig = window.AGENT_CONFIG;

// ============================================
// INITIALIZATION
// ============================================

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Initialize or recover call ID
const existingCallId = sessionStorage.getItem('current_call_id');
if (existingCallId) {
    window.callId = existingCallId;
    console.log('📞 Call ID récupéré (conversation en cours):', window.callId);
} else {
    window.callId = generateUUID();
    sessionStorage.setItem('current_call_id', window.callId);
    console.log('📞 Call ID généré (nouvelle conversation):', window.callId);
}

console.log('🤖 Agent Configuration:', agentConfig);

// ============================================
// CONVERSATION PERSISTENCE (Cosmos DB)
// ============================================

async function saveMessageToCosmosDB(messageType, content, metadata = {}) {
    try {
        const payload = {
            call_id: window.callId,
            agent_id: agentConfig.agentId,
            message_type: messageType,
            content: content,
            metadata: metadata,
            model: agentConfig.modelId
        };

        console.log('💾 Sauvegarde message - model:', agentConfig.modelId);

        const response = await fetch('/agents/api/conversation/save-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            console.warn('⚠️ Failed to save message to Cosmos DB:', response.status);
        }
    } catch (error) {
        console.error('❌ Error saving message to Cosmos DB:', error);
    }
}

async function endConversationInCosmosDB(toolsUsed = []) {
    try {
        const requestBody = {
            call_id: window.callId,
            tools_used: toolsUsed
        };

        if (sessionTokens) {
            requestBody.tokens = sessionTokens;
            console.log('📊 Sending tokens for cost calculation:', sessionTokens);
        } else {
            console.warn('⚠️ No tokens captured - costs will be estimated');
        }

        const response = await fetch('/agents/api/conversation/end', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            console.warn('⚠️ Failed to end conversation in Cosmos DB:', response.status);
        } else {
            const result = await response.json();
            console.log('✅ Conversation ended in Cosmos DB');
            console.log('📊 Analysis results:', result.data);
        }
    } catch (error) {
        console.error('❌ Error ending conversation in Cosmos DB:', error);
    }
}

// ============================================
// CONVERSATION CONTROL
// ============================================

async function startConversation() {
    console.log('🎙️ Starting conversation...');

    try {
        // Reset audio playback timing
        nextPlaybackTime = 0;

        // Initialize audio context
        if (!playbackContext) {
            playbackContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
            console.log('🎵 AudioContext created on user click - state:', playbackContext.state);
        }

        // Resume if suspended
        if (playbackContext.state === 'suspended') {
            await playbackContext.resume();
            console.log('▶️ AudioContext resumed - state:', playbackContext.state);
        }

        // Update UI
        updateConnectionStatus('connecting', 'Connexion...');
        document.getElementById('startButton').style.display = 'none';
        document.getElementById('stopButton').style.display = 'block';

        // Connect to WebSocket
        await connectWebSocket();

        // Start audio recording
        await startAudioRecording();

        addMessage('system', 'Connexion établie. Parlez maintenant...');
        updateConnectionStatus('connected', 'Connecté');

    } catch (error) {
        console.error('❌ Error starting conversation:', error);
        addMessage('system', 'Erreur de connexion: ' + error.message);
        updateConnectionStatus('disconnected', 'Erreur');
        resetUI();
    }
}

function stopConversation() {
    console.log('🛑 Stopping conversation...');

    // Stop avatar
    stopAvatar();

    // Close WebSocket
    if (websocket) {
        websocket.close();
        websocket = null;
    }

    // Stop audio recording
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }

    // Stop audio visualizer
    stopAudioVisualizer();

    // Stop audio playback
    stopAllAudio();
    currentResponseId = null;

    // End conversation in Cosmos DB
    endConversationInCosmosDB();

    // Clear call ID
    sessionStorage.removeItem('current_call_id');
    console.log('🗑️ Call ID cleared - prêt pour nouvelle conversation');

    addMessage('system', 'Conversation terminée.');
    updateConnectionStatus('disconnected', 'Déconnecté');
    resetUI();
}

function startNewConversation() {
    console.log('🆕 Starting NEW conversation...');

    window.callId = generateUUID();
    sessionStorage.setItem('current_call_id', window.callId);
    console.log('📞 New Call ID generated:', window.callId);

    document.getElementById('conversationDisplay').innerHTML = '';

    startConversation();
}

// ============================================
// WEBSOCKET CONNECTION
// ============================================

async function connectWebSocket() {
    return new Promise((resolve, reject) => {
        console.log('🔌 Connecting to:', agentConfig.websocketUrl);

        websocket = new WebSocket(agentConfig.websocketUrl);

        websocket.onopen = () => {
            console.log('✅ WebSocket connected');

            // Send session configuration
            const sessionConfig = {
                type: 'session.update',
                session: {
                    modalities: agentConfig.modalities || ["text", "audio"],
                    instructions: agentConfig.instructions,
                    voice: {
                        name: agentConfig.voice.name
                    },
                    max_response_output_tokens: agentConfig.maxTokens,
                    input_audio_transcription: {
                        model: 'whisper-1'
                    },
                    turn_detection: {
                        type: 'server_vad',
                        threshold: 0.5,
                        prefix_padding_ms: 300,
                        silence_duration_ms: 500
                    },
                    output_audio_timestamp_types: ['word'],
                    animation: {
                        outputs: ['viseme_id']
                    }
                }
            };

            // Add avatar configuration if enabled
            if (agentConfig.avatarEnabled && agentConfig.avatarConfig) {
                console.log('🎭 Adding avatar configuration to session...');
                console.log('🎭 Avatar character:', agentConfig.avatarConfig.character);
                console.log('🎭 Avatar style:', agentConfig.avatarConfig.style);

                const avatarCharacter = agentConfig.avatarConfig.character || 'lisa';
                const avatarStyle = agentConfig.avatarConfig.style || 'casual-sitting';

                sessionConfig.session.avatar = {
                    character: avatarCharacter,
                    style: avatarStyle,
                    customized: agentConfig.avatarConfig.customized || false,
                    video: {
                        codec: agentConfig.avatarConfig.video?.codec || 'h264',
                        bitrate: agentConfig.avatarConfig.video?.bitrate || 2000000,
                        resolution: agentConfig.avatarConfig.video?.resolution || {
                            width: 1920,
                            height: 1080
                        },
                        crop: agentConfig.avatarConfig.video?.crop || {
                            top_left: [560, 0],
                            bottom_right: [1360, 1080]
                        },
                        background: {}
                    }
                };

                if (agentConfig.avatarConfig.backgroundImage) {
                    sessionConfig.session.avatar.video.background.image_url = agentConfig.avatarConfig.backgroundImage;
                } else {
                    sessionConfig.session.avatar.video.background.color = agentConfig.avatarConfig.backgroundColor || '#00FF00FF';
                }

                console.log('🎭 Avatar config added (full format):', sessionConfig.session.avatar);
            }

            // Add custom lexicon URL if provided
            if (agentConfig.voice.custom_lexicon_url && agentConfig.voice.custom_lexicon_url.trim() !== '') {
                sessionConfig.session.voice.custom_lexicon_url = agentConfig.voice.custom_lexicon_url;
            }

            // Add tools
            if (agentConfig.tools && agentConfig.tools.length > 0) {
                sessionConfig.session.tools = agentConfig.tools;
                console.log(`🔧 Adding ${agentConfig.tools.length} tools to session`);
            }

            // Log config summary
            console.log('📤 Sending session config:');
            console.log('   - Modalities:', sessionConfig.session.modalities);
            console.log('   - Voice:', sessionConfig.session.voice.name);
            console.log('   - Max tokens:', sessionConfig.session.max_response_output_tokens);
            console.log('   - Tools:', agentConfig.tools ? agentConfig.tools.length : 0);
            console.log('   - Avatar enabled:', !!sessionConfig.session.avatar);
            if (sessionConfig.session.avatar) {
                console.log('   - Avatar character:', sessionConfig.session.avatar.character);
                console.log('   - Avatar style:', sessionConfig.session.avatar.style);
            }

            // Calculate payload size
            const payload = JSON.stringify(sessionConfig);
            console.log(`   - Payload size: ${payload.length} bytes (${(payload.length / 1024).toFixed(2)} KB)`);

            // Send configuration
            websocket.send(payload);
            console.log('📤 Session config sent');

            resolve();
        };

        websocket.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            console.error('❌ Error details:', {
                type: error.type,
                message: error.message,
                target: error.target ? {
                    url: error.target.url,
                    readyState: error.target.readyState,
                    protocol: error.target.protocol
                } : null
            });
            reject(new Error('WebSocket connection failed'));
        };

        websocket.onclose = (event) => {
            console.log('🔌 WebSocket disconnected');
            console.log('🔍 Close details:', {
                code: event.code,
                reason: event.reason || '(no reason provided)',
                wasClean: event.wasClean
            });

            if (event.code !== 1000) {
                console.error(`⚠️ Abnormal close code: ${event.code}`);
            }

            updateConnectionStatus('disconnected', 'Déconnecté');
        };

        websocket.onmessage = handleWebSocketMessage;

        // Timeout after 10 seconds
        setTimeout(() => {
            if (websocket && websocket.readyState !== WebSocket.OPEN) {
                reject(new Error('Connection timeout'));
            }
        }, 10000);
    });
}

// ============================================
// WEBSOCKET MESSAGE HANDLER
// ============================================

async function handleWebSocketMessage(event) {
    try {
        const message = JSON.parse(event.data);

        if (message.type.includes('function_call') || message.type.includes('output_item') || message.type === 'error') {
            console.log('📥 WebSocket message:', message.type, message);
        } else {
            console.log('📥 WebSocket message:', message.type);
        }

        switch (message.type) {
            case 'session.created':
                console.log('✅ Session created:', message.session);
                console.log('🔍 Session details:');
                console.log('   - Model:', message.session.model);
                console.log('   - Modalities:', message.session.modalities);
                console.log('   - Avatar in session?', 'avatar' in message.session);
                if (message.session.avatar) {
                    console.log('   - Avatar config:', message.session.avatar);
                }

                if (agentConfig.avatarEnabled) {
                    console.log('🎭 Avatar enabled, waiting for server SDP...');
                    console.log('⏳ Waiting for session.avatar.connecting event...');
                }
                break;

            case 'response.audio.delta':
                if (agentConfig.avatarEnabled && peerConnection) {
                    console.log('🎭 Avatar enabled - skipping audio.delta (using WebRTC audio)');
                    break;
                }

                if (message.response_id === currentResponseId) {
                    playAudioChunk(message.delta, message.response_id);
                } else {
                    console.log(`🚫 Ignoring audio from old response: ${message.response_id}`);
                }
                break;

            case 'response.audio_transcript.delta':
                console.log('📝 Transcript delta:', message.delta);
                if (message.delta && message.delta !== '<|audio_text|>') {
                    addOrUpdateMessage('agent', message.delta, message.response_id);
                }
                break;

            case 'response.audio_transcript.done':
                console.log('📝 Transcript done:', message.transcript);
                if (message.transcript && message.transcript !== '<|audio_text|>') {
                    saveMessageToCosmosDB('agent', message.transcript);
                }
                break;

            case 'response.text.delta':
                console.log('📝 Text delta:', message.delta);
                if (message.delta) {
                    let textToDisplay = message.delta;
                    try {
                        const parsed = JSON.parse(message.delta);
                        if (parsed.message) {
                            textToDisplay = parsed.message;
                        }
                    } catch (e) {
                        // Not JSON
                    }
                    addOrUpdateMessage('agent', textToDisplay, message.response_id);
                }
                break;

            case 'response.text.done':
                console.log('📝 Text done:', message.text);
                if (message.text) {
                    let textToSave = message.text;
                    try {
                        const parsed = JSON.parse(message.text);
                        if (parsed.message) {
                            textToSave = parsed.message;
                        }
                    } catch (e) {
                        // Not JSON
                    }
                    saveMessageToCosmosDB('agent', textToSave);
                }
                break;

            case 'conversation.item.input_audio_transcription.completed':
                console.log('📝 User transcript:', message.transcript);
                if (message.transcript && message.transcript !== '<|audio_text|>') {
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
                }
                break;

            case 'response.created':
                console.log('🆕 New response created');
                stopAllAudio();
                break;

            case 'input_audio_buffer.speech_started':
                console.log('🎤 User started speaking - stopping AI audio');
                stopAllAudio();
                break;

            case 'response.cancelled':
                console.log('🚫 Response cancelled - stopping audio');
                stopAllAudio();
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
                console.log('📊 Response.done complete:', JSON.stringify(message, null, 2));

                if (message.response && message.response.output) {
                    for (const item of message.response.output) {
                        if (item.type === 'message' && item.content) {
                            for (const content of item.content) {
                                if (content.type === 'audio' && content.transcript) {
                                    console.log('📝 Transcript from response.done:', content.transcript);
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
                    console.log('📊 Tokens updated from response.done:', sessionTokens);
                }
                break;

            case 'error':
                console.error('❌ Server error:', message.error);
                console.error('❌ Full error message:', JSON.stringify(message, null, 2));

                const errorDetails = {
                    type: message.error?.type || 'unknown',
                    code: message.error?.code || message.error?.status_code,
                    message: message.error?.message || message.error?.error,
                    param: message.error?.param,
                    event_id: message.error?.event_id
                };

                console.error('📋 Error details:', errorDetails);

                const errorMsg = message.error?.message || message.error?.error || JSON.stringify(message.error);
                addMessage('system', 'Erreur serveur: ' + errorMsg);

                if (errorMsg.includes('avatar') || errorMsg.includes('character') || errorMsg.includes('style')) {
                    console.error('💡 Hint: Avatar configuration error. Check:');
                    console.error('   - Character name is valid (e.g., "lisa", "harry")');
                    console.error('   - Style is valid for the character');
                    console.error('   - Model supports avatars (gpt-5 required)');
                }
                break;

            case 'session.avatar.connecting':
                console.log('🎭 Received session.avatar.connecting');
                console.log('🎉 Server is ready for avatar WebRTC connection!');

                if (message.server_sdp) {
                    console.log('📥 Received server SDP, initializing WebRTC...');

                    if (!peerConnection) {
                        await initializeAvatarWebRTC();
                    }

                    await handleAvatarConnecting(message.server_sdp);
                } else {
                    console.error('❌ session.avatar.connecting received but no server_sdp provided');
                }
                break;

            case 'session.updated':
                console.log('✅ Session updated');
                if (message.session && message.session.avatar && message.session.avatar.ice_servers) {
                    console.log('🧊 Server provided ICE servers:', message.session.avatar.ice_servers);
                    serverIceServers = message.session.avatar.ice_servers;

                    if (agentConfig.avatarEnabled && !peerConnection) {
                        console.log('🎭 Session updated received, initializing avatar with server ICE servers...');
                        await initializeAvatar();
                    }
                }
                break;

            case 'response.animation_viseme.delta':
                const visemeId = message.viseme_id;
                const audioOffset = message.audio_offset_ms;
                console.log(`👄 Viseme ${visemeId} at ${audioOffset}ms`);
                break;

            case 'response.animation_viseme.done':
                console.log('👄 All visemes received for response:', message.response_id);
                break;

            default:
                console.log('ℹ️ Unhandled message type:', message.type);
                break;
        }
    } catch (error) {
        console.error('❌ Error handling WebSocket message:', error);
        console.error('❌ Raw event data:', event.data);
    }
}

// ============================================
// AZURE AVATAR INTEGRATION
// ============================================

async function initializeAvatarWebRTC() {
    if (!agentConfig.avatarEnabled) {
        console.log('ℹ️ Avatar not enabled for this agent');
        return;
    }

    if (peerConnection) {
        console.log('ℹ️ WebRTC peer connection already exists');
        return;
    }

    try {
        console.log('🎭 Initializing WebRTC peer connection...');

        const avatarContainer = document.getElementById('avatarContainer');
        if (!avatarContainer) {
            console.error('❌ Avatar container not found');
            return;
        }

        // Préparer le container pour la vidéo avatar
        avatarContainer.innerHTML = `
            <video id="avatarVideo" autoplay playsinline style="width: 100%; height: 100%; object-fit: contain; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"></video>
        `;

        // Créer la connexion WebRTC avec les ICE servers
        const iceServers = serverIceServers && serverIceServers.length > 0
            ? serverIceServers
            : [{ urls: 'stun:stun.l.google.com:19302' }];

        console.log('🧊 Using ICE servers:', iceServers);

        peerConnection = new RTCPeerConnection({
            iceServers: iceServers
        });

        // Add transceivers to receive audio and video from avatar
        peerConnection.addTransceiver('audio', { direction: 'recvonly' });
        peerConnection.addTransceiver('video', { direction: 'recvonly' });
        console.log('✅ Added audio and video transceivers (recvonly)');

        // Gérer les événements
        peerConnection.ontrack = (event) => {
            console.log('🎬 Received track:', event.track.kind, 'streams:', event.streams.length);

            const videoElement = document.getElementById('avatarVideo');

            // Azure envoie audio et vidéo dans des streams SÉPARÉS
            // Il faut les combiner dans un seul MediaStream
            if (!avatarCombinedStream) {
                avatarCombinedStream = new MediaStream();
                console.log('🎭 Created combined MediaStream for avatar');
            }

            // Ajouter le track au stream combiné
            avatarCombinedStream.addTrack(event.track);
            console.log(`➕ Added ${event.track.kind} track to combined stream`);

            // Log l'état actuel du stream combiné
            const audioTracks = avatarCombinedStream.getAudioTracks();
            const videoTracks = avatarCombinedStream.getVideoTracks();
            console.log(`📊 Combined stream now has: ${audioTracks.length} audio, ${videoTracks.length} video`);

            // Attacher le stream combiné à l'élément vidéo
            if (videoElement) {
                videoElement.srcObject = avatarCombinedStream;
                videoElement.muted = false;
                videoElement.volume = 1.0;

                // Si on a reçu le track vidéo, démarrer la lecture
                if (event.track.kind === 'video') {
                    console.log('📹 Video track received - starting playback');
                    videoElement.play().then(() => {
                        console.log('✅ Avatar video playing with WebRTC audio (volume: 1.0)');
                        console.log(`🔊 Final audio tracks: ${audioTracks.length}`);
                        audioTracks.forEach((track, i) => {
                            console.log(`   Audio track ${i}: enabled=${track.enabled}, muted=${track.muted}, readyState=${track.readyState}`);
                        });
                        console.log(`📹 Final video tracks: ${videoTracks.length}`);
                        videoTracks.forEach((track, i) => {
                            console.log(`   Video track ${i}: enabled=${track.enabled}, muted=${track.muted}, readyState=${track.readyState}`);
                        });
                    }).catch(e => {
                        console.error('❌ Video autoplay blocked:', e.message);
                        const audioControlButton = document.getElementById('audioControlButton');
                        if (audioControlButton) {
                            audioControlButton.style.display = 'block';
                        }
                    });
                } else if (event.track.kind === 'audio') {
                    console.log('🔊 Audio track added to combined stream');
                }
            }
        };

        peerConnection.onicecandidate = (event) => {
            console.log('🧊 ICE candidate event:', event.candidate ? 'candidate' : 'gathering complete');
        };

        peerConnection.onicegatheringstatechange = () => {
            console.log('🧊 ICE gathering state:', peerConnection.iceGatheringState);
        };

        peerConnection.oniceconnectionstatechange = () => {
            console.log('🧊 ICE connection state:', peerConnection.iceConnectionState);
        };

        peerConnection.onconnectionstatechange = () => {
            console.log('🔗 Connection state:', peerConnection.connectionState);
        };

        console.log('✅ WebRTC peer connection initialized (waiting for server SDP)');

    } catch (error) {
        console.error('❌ Error initializing WebRTC:', error);
    }
}

async function initializeAvatar() {
    if (!agentConfig.avatarEnabled) {
        console.log('ℹ️ Avatar not enabled for this agent');
        return;
    }

    try {
        console.log('🎭 Initializing Azure Avatar...', agentConfig.avatarConfig);

        // Réinitialiser le flag SDP pour cette nouvelle connexion
        sdpSent = false;

        const avatarContainer = document.getElementById('avatarContainer');
        if (!avatarContainer) {
            console.error('❌ Avatar container not found');
            return;
        }

        // Préparer le container pour la vidéo avatar
        avatarContainer.innerHTML = `
            <video id="avatarVideo" autoplay playsinline style="width: 100%; height: 100%; object-fit: contain; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"></video>
        `;

        // Créer la connexion WebRTC avec les ICE servers du serveur Azure
        console.log('🎭 Creating WebRTC peer connection for avatar...');

        const iceServers = serverIceServers && serverIceServers.length > 0
            ? serverIceServers
            : [{ urls: 'stun:stun.l.google.com:19302' }];

        console.log('🧊 Using ICE servers:', iceServers);

        peerConnection = new RTCPeerConnection({
            iceServers: iceServers
        });

        // Add transceivers to receive audio and video from avatar
        peerConnection.addTransceiver('audio', { direction: 'recvonly' });
        peerConnection.addTransceiver('video', { direction: 'recvonly' });
        console.log('✅ Added audio and video transceivers (recvonly)');

        // Gérer les événements
        peerConnection.ontrack = (event) => {
            console.log('🎬 Received track:', event.track.kind, 'streams:', event.streams.length);

            const videoElement = document.getElementById('avatarVideo');

            if (!avatarCombinedStream) {
                avatarCombinedStream = new MediaStream();
                console.log('🎭 Created combined MediaStream for avatar');
            }

            avatarCombinedStream.addTrack(event.track);
            console.log(`➕ Added ${event.track.kind} track to combined stream`);

            const audioTracks = avatarCombinedStream.getAudioTracks();
            const videoTracks = avatarCombinedStream.getVideoTracks();
            console.log(`📊 Combined stream now has: ${audioTracks.length} audio, ${videoTracks.length} video`);

            if (videoElement) {
                videoElement.srcObject = avatarCombinedStream;
                videoElement.muted = false;
                videoElement.volume = 1.0;

                if (event.track.kind === 'video') {
                    console.log('📹 Video track received - starting playback');
                    videoElement.play().then(() => {
                        console.log('✅ Avatar video playing with WebRTC audio (volume: 1.0)');
                        console.log(`🔊 Final audio tracks: ${audioTracks.length}`);
                        audioTracks.forEach((track, i) => {
                            console.log(`   Audio track ${i}: enabled=${track.enabled}, muted=${track.muted}, readyState=${track.readyState}`);
                        });
                        console.log(`📹 Final video tracks: ${videoTracks.length}`);
                        videoTracks.forEach((track, i) => {
                            console.log(`   Video track ${i}: enabled=${track.enabled}, muted=${track.muted}, readyState=${track.readyState}`);
                        });
                    }).catch(e => {
                        console.error('❌ Video autoplay blocked:', e.message);
                        console.log('⚠️ Affichage du bouton pour activer l\'audio');

                        const audioControlButton = document.getElementById('audioControlButton');
                        if (audioControlButton) {
                            audioControlButton.style.display = 'block';
                        }

                        document.addEventListener('click', () => {
                            videoElement.play().then(() => {
                                console.log('✅ Video playing after user interaction');
                                if (audioControlButton) {
                                    audioControlButton.style.display = 'none';
                                }
                            });
                        }, { once: true });
                    });
                } else if (event.track.kind === 'audio') {
                    console.log('🔊 Audio track added to combined stream');
                }
            }
        };

        peerConnection.onicecandidate = (event) => {
            console.log('🧊 ICE candidate event:', event.candidate ? 'candidate' : 'gathering complete');
        };

        peerConnection.onicegatheringstatechange = () => {
            console.log('🧊 ICE gathering state:', peerConnection.iceGatheringState);

            if (peerConnection.iceGatheringState === 'complete' && !sdpSent) {
                sdpSent = true;
                sendAvatarConnect();
            }
        };

        // Timeout de sécurité : envoyer après 3 secondes même si ICE gathering pas terminé
        setTimeout(() => {
            if (peerConnection && peerConnection.iceGatheringState !== 'complete' && !sdpSent) {
                console.log('⏱️ ICE gathering timeout - sending SDP anyway with', peerConnection.iceGatheringState);
                sdpSent = true;
                sendAvatarConnect();
            }
        }, 3000);

        peerConnection.oniceconnectionstatechange = () => {
            console.log('🧊 ICE connection state:', peerConnection.iceConnectionState);
        };

        peerConnection.onconnectionstatechange = () => {
            console.log('🔗 Connection state:', peerConnection.connectionState);
        };

        // Créer une offre WebRTC
        console.log('🎭 Creating WebRTC offer...');
        const offer = await peerConnection.createOffer({
            offerToReceiveAudio: true,
            offerToReceiveVideo: true
        });
        await peerConnection.setLocalDescription(offer);
        console.log('✅ Local description set, waiting for ICE gathering...');

    } catch (error) {
        console.error('❌ Error initializing avatar:', error);
        const avatarContainer = document.getElementById('avatarContainer');
        if (avatarContainer) {
            avatarContainer.innerHTML = `
                <div style="text-align: center; color: white; padding: 20px;">
                    <i class="bi bi-exclamation-triangle" style="font-size: 60px; opacity: 0.8; margin-bottom: 20px; display: block;"></i>
                    <p style="font-size: 16px; opacity: 0.9;">Erreur d'initialisation de l'avatar</p>
                    <p style="font-size: 12px; opacity: 0.7;">${error.message}</p>
                </div>
            `;
        }
    }
}

async function sendAvatarConnect() {
    if (!peerConnection || !websocket || websocket.readyState !== WebSocket.OPEN) {
        console.error('❌ Cannot send avatar connect: connection not ready');
        return;
    }

    try {
        const localDescription = peerConnection.localDescription;
        if (!localDescription) {
            console.error('❌ No local description available');
            return;
        }

        const sdpPayload = {
            type: localDescription.type,
            sdp: localDescription.sdp
        };

        const jsonString = JSON.stringify(sdpPayload);
        const base64Encoded = btoa(jsonString);

        console.log('📤 Sending session.avatar.connect with client SDP...');
        console.log('🔍 SDP type:', localDescription.type);
        console.log('🔍 Original SDP length:', localDescription.sdp.length);
        console.log('🔍 JSON payload length:', jsonString.length);
        console.log('🔍 Base64 encoded length:', base64Encoded.length);
        console.log('🔍 First 100 chars of JSON:', jsonString.substring(0, 100));

        websocket.send(JSON.stringify({
            type: 'session.avatar.connect',
            client_sdp: base64Encoded
        }));
    } catch (error) {
        console.error('❌ Error sending avatar connect:', error);
    }
}

async function handleAvatarConnecting(serverSdp) {
    try {
        console.log('🎭 Received session.avatar.connecting with server SDP');
        console.log('🔍 Server SDP type:', typeof serverSdp);
        console.log('🔍 Server SDP length:', serverSdp ? serverSdp.length : 0);

        if (!peerConnection) {
            console.error('❌ No peer connection available');
            return;
        }

        if (!serverSdp) {
            console.error('❌ No server SDP received');
            return;
        }

        try {
            // Decode base64 to JSON string
            const jsonString = atob(serverSdp);
            console.log('✅ Base64 decoded, JSON length:', jsonString.length);
            console.log('🔍 First 100 chars of JSON:', jsonString.substring(0, 100));

            // Parse JSON to get type and sdp
            const sdpPayload = JSON.parse(jsonString);
            console.log('✅ JSON parsed, type:', sdpPayload.type, 'SDP length:', sdpPayload.sdp ? sdpPayload.sdp.length : 0);

            // Set remote description with the decoded SDP
            await peerConnection.setRemoteDescription(new RTCSessionDescription({
                type: sdpPayload.type || 'answer',
                sdp: sdpPayload.sdp
            }));

            console.log('✅ Avatar WebRTC connection established');

            // Debug: vérifier l'état de l'élément vidéo
            setTimeout(() => {
                const videoElement = document.getElementById('avatarVideo');
                if (videoElement) {
                    console.log('🔍 Video element state:');
                    console.log('  - srcObject:', videoElement.srcObject ? 'set' : 'NOT SET');
                    console.log('  - muted:', videoElement.muted);
                    console.log('  - volume:', videoElement.volume);
                    console.log('  - paused:', videoElement.paused);
                    console.log('  - readyState:', videoElement.readyState);
                    if (videoElement.srcObject) {
                        const tracks = videoElement.srcObject.getTracks();
                        console.log('  - tracks:', tracks.length);
                        tracks.forEach(track => {
                            console.log(`    - ${track.kind}: enabled=${track.enabled}, muted=${track.muted}, readyState=${track.readyState}`);
                        });
                    }
                }
            }, 1000);

        } catch (decodeError) {
            console.error('❌ Failed to decode server SDP:', decodeError);
            console.error('❌ Raw server SDP:', serverSdp.substring(0, 200));
        }

    } catch (error) {
        console.error('❌ Error handling avatar connecting:', error);
        console.error('❌ Error details:', error.message, error.stack);
    }
}

function stopAvatar() {
    if (avatarSynthesizer) {
        avatarSynthesizer.close();
        avatarSynthesizer = null;
    }
    if (peerConnection) {
        peerConnection.close();
        peerConnection = null;
    }
    if (avatarCombinedStream) {
        avatarCombinedStream.getTracks().forEach(track => track.stop());
        avatarCombinedStream = null;
    }
}

// Fonction pour activer manuellement l'audio de l'avatar
window.enableAvatarAudio = function () {
    const videoElement = document.getElementById('avatarVideo');
    const audioControlButton = document.getElementById('audioControlButton');

    if (videoElement) {
        videoElement.muted = false;
        videoElement.volume = 1.0;

        videoElement.play().then(() => {
            console.log('✅ Audio activé manuellement - volume:', videoElement.volume);
            if (audioControlButton) {
                audioControlButton.style.display = 'none';
            }
        }).catch(e => {
            console.error('❌ Erreur lors de l\'activation audio:', e);
        });
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

        // Use AudioContext to capture raw PCM audio
        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
        const source = audioContext.createMediaStreamSource(stream);
        const processor = audioContext.createScriptProcessor(4096, 1, 1);

        source.connect(processor);
        processor.connect(audioContext.destination);

        processor.onaudioprocess = (e) => {
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                const inputData = e.inputBuffer.getChannelData(0);

                // Convert Float32 to Int16 PCM
                const pcmData = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    const s = Math.max(-1, Math.min(1, inputData[i]));
                    pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }

                // Ensure even length for PCM16
                const evenLength = pcmData.length % 2 === 0 ? pcmData.length : pcmData.length - 1;
                const evenPcmData = pcmData.slice(0, evenLength);

                // Convert to base64
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
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = audioContext.createAnalyser();
    const microphone = audioContext.createMediaStreamSource(stream);

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
}

function stopAudioVisualizer() {
    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }

    const bars = document.querySelectorAll('.visualizer-bar');
    bars.forEach(bar => {
        bar.style.height = '20px';
        bar.classList.remove('active');
    });
}

// ============================================
// AUDIO PLAYBACK WITH QUEUE
// ============================================

function stopAllAudio() {
    activeSources.forEach(source => {
        try {
            source.stop();
        } catch (e) {
            // Ignore si déjà arrêté
        }
    });
    activeSources = [];

    audioQueue = [];
    isProcessingQueue = false;

    if (playbackContext) {
        try {
            playbackContext.close();
        } catch (e) {
            // Ignore si déjà fermé
        }
        playbackContext = null;
    }

    nextPlaybackTime = 0;

    console.log('🔇 All audio stopped and context reset');
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

async function playAudioChunkNow(base64Audio, responseId) {
    return new Promise(async (resolve) => {
        if (responseId !== currentResponseId) {
            console.log(`🚫 Skipping audio chunk from old response: ${responseId}`);
            resolve();
            return;
        }

        // Decode base64 to PCM16 audio
        const audioData = atob(base64Audio);
        const arrayBuffer = new ArrayBuffer(audioData.length);
        const view = new Uint8Array(arrayBuffer);

        for (let i = 0; i < audioData.length; i++) {
            view[i] = audioData.charCodeAt(i);
        }

        // Convert PCM16 to Float32 for Web Audio API
        const pcm16 = new Int16Array(arrayBuffer);
        const float32 = new Float32Array(pcm16.length);
        for (let i = 0; i < pcm16.length; i++) {
            float32[i] = pcm16[i] / 32768.0;
        }

        // Initialize audio context if needed
        if (!playbackContext) {
            playbackContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
            nextPlaybackTime = playbackContext.currentTime;
            console.log('🎵 AudioContext created - state:', playbackContext.state);
        }

        // Resume AudioContext if suspended
        if (playbackContext.state === 'suspended') {
            await playbackContext.resume();
            console.log('▶️ AudioContext resumed - state:', playbackContext.state);
        }

        // Create audio buffer
        const audioBuffer = playbackContext.createBuffer(1, float32.length, 24000);
        audioBuffer.getChannelData(0).set(float32);

        // Schedule playback sequentially
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
    console.log(`📋 Arguments JSON:`, argumentsJson);

    try {
        if (!toolName || toolName === 'unknown') {
            throw new Error('Tool name is missing or unknown');
        }

        const args = JSON.parse(argumentsJson);
        console.log(`📦 Parsed arguments:`, args);

        // Injecter automatiquement le call_id
        args.call_id = window.callId;
        console.log(`📞 Added call_id to arguments:`, window.callId);

        // Appeler le backend pour exécuter le tool
        const response = await fetch('/api/tools/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tool_name: toolName,
                arguments: args,
                agent_id: agentConfig.agentId
            })
        });

        if (!response.ok) {
            throw new Error(`Backend returned ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        console.log('✅ Tool result:', result);

        // Sauvegarder l'appel d'outil dans Cosmos DB
        saveMessageToCosmosDB('tool', `Tool ${toolName} executed`, {
            tool_name: toolName,
            arguments: args,
            result: result
        });

        // Détecter si c'est le tool end_conversation
        if (toolName === 'end_conversation' && result.action === 'end_conversation') {
            console.log('🛑 end_conversation tool detected - triggering automatic conversation end');
            console.log('📝 User farewell:', result.user_farewell);
            console.log('📝 Summary:', result.summary);

            setTimeout(() => {
                console.log('🛑 Auto-stopping conversation after end_conversation tool');
                stopConversation();
            }, 2000);
        }

        // Envoyer le résultat au modèle via WebSocket
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({
                type: 'conversation.item.create',
                item: {
                    type: 'function_call_output',
                    call_id: callId,
                    output: JSON.stringify(result)
                }
            }));

            // Demander une nouvelle réponse
            websocket.send(JSON.stringify({
                type: 'response.create'
            }));
        }

        addMessage('system', `✅ ${toolName} exécuté avec succès`);

    } catch (error) {
        console.error('❌ Tool execution error:', error);
        addMessage('system', `❌ Erreur lors de l'exécution de ${toolName}`);

        // Envoyer l'erreur au modèle
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
    const badge = document.getElementById('connectionStatus');
    badge.className = 'status-badge ' + status;
    badge.querySelector('span').textContent = text;
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

    try {
        const response = await fetch(`/agents/api/${agentConfig.agentId}/update_session_config`, {
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
            agentConfig.instructions = newInstructions;
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

    try {
        const response = await fetch(`/agents/api/${agentConfig.agentId}/update_session_config`, {
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
// GLOBAL FUNCTION EXPOSURE
// ============================================

// Expose functions to window for onclick handlers
window.startConversation = startConversation;
window.stopConversation = stopConversation;
window.startNewConversation = startNewConversation;
window.toggleInstructionsEditor = toggleInstructionsEditor;
window.cancelInstructionsEdit = cancelInstructionsEdit;
window.saveInstructions = saveInstructions;
window.toggleLexiconEditor = toggleLexiconEditor;
window.cancelLexiconEdit = cancelLexiconEdit;
window.saveLexiconUrl = saveLexiconUrl;

// ============================================
// INITIALIZATION COMPLETE
// ============================================

console.log('✅ Voice Session Client Ready');
console.log('🤖 Agent:', agentConfig.agentName);
console.log('🎯 Model:', agentConfig.modelId);
console.log('🔧 Tools:', agentConfig.tools ? agentConfig.tools.length : 0);
console.log('🎭 Avatar enabled:', agentConfig.avatarEnabled);