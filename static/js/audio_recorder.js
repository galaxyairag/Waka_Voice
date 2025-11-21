// ============================================
// AUDIO RECORDER - Compatible Azure Personal Voice
// WAV PCM 16-bit 16kHz Mono
// Version: 1.0.0
// ============================================

class AzureCompatibleRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioContext = null;
        this.stream = null;
        this.audioChunks = [];
        this.startTime = null;
        this.isRecording = false;
        this.scriptProcessor = null;
        this.source = null;
    }

    async startRecording() {
        try {
            // Demander accès micro avec contraintes spécifiques
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,        // Mono
                    sampleRate: 16000,      // 16 kHz
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // Créer AudioContext à 16kHz
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 16000
            });

            this.source = this.audioContext.createMediaStreamSource(this.stream);

            // Utiliser ScriptProcessor pour capturer PCM brut
            const bufferSize = 4096;
            this.scriptProcessor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);

            this.audioChunks = [];
            this.startTime = Date.now();
            this.isRecording = true;

            this.scriptProcessor.onaudioprocess = (e) => {
                if (!this.isRecording) return;

                const inputData = e.inputBuffer.getChannelData(0);
                // Convertir Float32 en Int16 (PCM 16-bit)
                const pcm16 = this.float32ToInt16(inputData);
                this.audioChunks.push(pcm16);
            };

            this.source.connect(this.scriptProcessor);
            this.scriptProcessor.connect(this.audioContext.destination);

            console.log('🎙️ Enregistrement démarré - Format: WAV PCM 16-bit 16kHz Mono');
            return true;

        } catch (error) {
            console.error('❌ Erreur démarrage enregistrement:', error);
            throw new Error(`Impossible d'accéder au microphone: ${error.message}`);
        }
    }

    stopRecording() {
        return new Promise((resolve, reject) => {
            if (!this.isRecording) {
                reject(new Error('Aucun enregistrement en cours'));
                return;
            }

            this.isRecording = false;

            // Arrêter le stream
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
            }

            // Déconnecter et nettoyer
            if (this.scriptProcessor) {
                this.scriptProcessor.disconnect();
                this.scriptProcessor = null;
            }
            if (this.source) {
                this.source.disconnect();
                this.source = null;
            }
            if (this.audioContext) {
                this.audioContext.close();
                this.audioContext = null;
            }

            const duration = (Date.now() - this.startTime) / 1000;
            console.log(`🎙️ Enregistrement arrêté - Durée: ${duration.toFixed(1)}s`);

            // Créer WAV file
            try {
                const wavBlob = this.createWavBlob();
                resolve({
                    blob: wavBlob,
                    duration: duration
                });
            } catch (error) {
                reject(new Error(`Erreur création WAV: ${error.message}`));
            }
        });
    }

    float32ToInt16(float32Array) {
        const int16Array = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            const s = Math.max(-1, Math.min(1, float32Array[i]));
            int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return int16Array;
    }

    createWavBlob() {
        // Combiner tous les chunks PCM
        const totalLength = this.audioChunks.reduce((acc, chunk) => acc + chunk.length, 0);
        const combinedPCM = new Int16Array(totalLength);
        let offset = 0;
        for (const chunk of this.audioChunks) {
            combinedPCM.set(chunk, offset);
            offset += chunk.length;
        }

        // Créer header WAV
        const sampleRate = 16000;
        const numChannels = 1;
        const bitsPerSample = 16;
        const byteRate = sampleRate * numChannels * (bitsPerSample / 8);
        const blockAlign = numChannels * (bitsPerSample / 8);
        const dataSize = combinedPCM.length * 2; // 2 bytes per sample (16-bit)

        const buffer = new ArrayBuffer(44 + dataSize);
        const view = new DataView(buffer);

        // Header WAV (44 bytes)
        this.writeString(view, 0, 'RIFF');
        view.setUint32(4, 36 + dataSize, true);
        this.writeString(view, 8, 'WAVE');
        this.writeString(view, 12, 'fmt ');
        view.setUint32(16, 16, true); // Subchunk1Size (16 for PCM)
        view.setUint16(20, 1, true);  // AudioFormat (1 for PCM)
        view.setUint16(22, numChannels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, byteRate, true);
        view.setUint16(32, blockAlign, true);
        view.setUint16(34, bitsPerSample, true);
        this.writeString(view, 36, 'data');
        view.setUint32(40, dataSize, true);

        // Données audio PCM
        const dataView = new Int16Array(buffer, 44);
        dataView.set(combinedPCM);

        return new Blob([buffer], { type: 'audio/wav' });
    }

    writeString(view, offset, string) {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    }

    getDuration() {
        if (!this.startTime) return 0;
        return (Date.now() - this.startTime) / 1000;
    }

    isCurrentlyRecording() {
        return this.isRecording;
    }
}

// Export pour utilisation globale
window.AzureCompatibleRecorder = AzureCompatibleRecorder;

console.log('✅ AzureCompatibleRecorder loaded successfully');