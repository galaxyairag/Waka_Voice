/**
 * Agent Configuration Step 2 - CORRIGÉ
 * JavaScript conforme documentation Azure
 * 
 * CORRECTIONS APPLIQUÉES :
 * 1. Semantic VAD uniquement F1
 * 2. Language conditionnel multilingual
 * 3. End of utterance = objet
 * 4. Eagerness conditionnel semantic_vad
 * 5. Voix OpenAI pour F1
 * 6. Lexicon/Temp/Rate cachés si OpenAI
 */

// =============================================================================
// CONSTANTES
// =============================================================================

// Modèles F1 (Realtime avec audio natif)
const F1_MODELS = ['gpt-realtime', 'gpt-realtime-mini', 'phi4-mm-realtime'];

// Langues supportées par multilingual
const MULTILINGUAL_LANGUAGES = [
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'it', name: 'Italian' },
    { code: 'de', name: 'German' },
    { code: 'ja', name: 'Japanese' },
    { code: 'pt', name: 'Portuguese' },
    { code: 'zh', name: 'Chinese' },
    { code: 'ko', name: 'Korean' },
    { code: 'hi', name: 'Hindi' }
];

// =============================================================================
// VARIABLES GLOBALES
// =============================================================================

let currentModelFamily = null;
let currentVoiceType = null; // 'openai' ou 'azure'
let selectedVoice = null;

// =============================================================================
// INITIALISATION
// =============================================================================

document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 Initialisation Step 2 - Configuration Voice Live');

    // Récupérer les infos du modèle
    initializeModelInfo();

    // Masquer Speech to Text pour les modèles Realtime (F1)
    hideInputTranscriptionForRealtime();

    // Setup event listeners
    setupEventListeners();

    // Initialiser l'UI selon la famille
    initializeUIForFamily();

    // Charger les lexiques depuis Azure Storage
    loadLexicons();

    console.log('✅ Step 2 initialisé');
});

/**
 * Initialiser les informations du modèle
 */
function initializeModelInfo() {
    // Récupérer depuis les champs cachés
    const modelId = document.getElementById('modelId').value;
    const modelName = document.getElementById('modelName').value;
    const modelFamily = document.getElementById('modelFamily').value;

    currentModelFamily = modelFamily;

    // Mettre à jour l'affichage
    document.getElementById('selectedModelName').textContent = modelName;
    document.getElementById('selectedModelFamily').textContent = modelFamily;

    // Icône selon famille
    const icon = document.querySelector('.model-info-icon');
    icon.className = 'model-info-icon ' + modelFamily.toLowerCase().replace('_', '-');

    console.log('📦 Modèle:', modelName, '| Famille:', modelFamily);
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // VAD Type change
    const vadTypeSelect = document.getElementById('vadType');
    if (vadTypeSelect) {
        vadTypeSelect.addEventListener('change', handleVADTypeChange);
    }

    // Voice Type buttons (F1)
    const voiceTypeButtons = document.querySelectorAll('[data-voice-type]');
    voiceTypeButtons.forEach(btn => {
        btn.addEventListener('click', handleVoiceTypeSelection);
    });

    // OpenAI voice cards
    const openaiVoiceCards = document.querySelectorAll('#openaiVoicesGrid .voice-card');
    openaiVoiceCards.forEach(card => {
        card.addEventListener('click', handleOpenAIVoiceSelection);
    });

    // Voice Type select (azure-standard vs azure-custom)
    const voiceTypeSelect = document.getElementById('voiceType');
    if (voiceTypeSelect) {
        voiceTypeSelect.addEventListener('change', handleAzureVoiceTypeChange);
    }

    // End of Utterance checkbox
    const eouCheckbox = document.getElementById('enableEndOfUtterance');
    if (eouCheckbox) {
        eouCheckbox.addEventListener('change', handleEndOfUtteranceToggle);
    }

    // Input Transcription Model
    const transcriptionModel = document.getElementById('inputTranscriptionModel');
    if (transcriptionModel) {
        transcriptionModel.addEventListener('change', handleTranscriptionModelChange);
    }

    // Phrase list counter
    const phraseList = document.getElementById('phraseList');
    if (phraseList) {
        phraseList.addEventListener('input', updatePhraseListCounter);
    }
}

/**
 * Initialiser l'UI selon la famille de modèles
 */
function initializeUIForFamily() {
    console.log(`🎨 Configuration UI pour ${currentModelFamily}`);

    const isF1 = currentModelFamily === 'F1_Realtime';

    // 1. Configurer les options VAD disponibles
    configureVADOptions(isF1);

    // 2. Configurer la sélection de voix
    configureVoiceSelection(isF1);

    // 3. Configurer End of Utterance availability
    configureEndOfUtterance(isF1);

    // 4. Configurer les langues multilingual
    initializeLanguageGrid();

    // 5. Configurer max_tokens label dynamically
    updateMaxTokensUI();
}

/**
 * Update max_tokens UI based on model family
 */
function updateMaxTokensUI() {
    const modelName = document.getElementById('modelName').value.toLowerCase();
    const maxTokensLabel = document.getElementById('maxTokensLabel');
    const maxTokensHelp = document.getElementById('maxTokensHelp');
    const maxTokensTooltipTitle = document.getElementById('maxTokensTooltipTitle');
    const maxTokensTooltipContent = document.getElementById('maxTokensTooltipContent');
    const maxCompletionTokensTooltipContent = document.getElementById('maxCompletionTokensTooltipContent');

    // Check if model is GPT-5 or o1 family
    const isGPT5OrO1 = modelName.includes('gpt-5') ||
        modelName.includes('o1') ||
        modelName.includes('gpt5');

    if (isGPT5OrO1) {
        // Use max_completion_tokens
        maxTokensLabel.textContent = 'Tokens de complétion maximum (Max Completion Tokens)';
        maxTokensHelp.textContent = 'Nombre maximum de tokens de complétion (1-16000 pour GPT-5/o1)';
        maxTokensTooltipTitle.textContent = 'Max Completion Tokens :';
        maxTokensTooltipContent.style.display = 'none';
        maxCompletionTokensTooltipContent.style.display = 'block';
        console.log('✅ Max Tokens UI: max_completion_tokens (GPT-5/o1)');
    } else {
        // Use max_tokens
        maxTokensLabel.textContent = 'Tokens maximum (Max Tokens)';
        maxTokensHelp.textContent = 'Nombre maximum de tokens dans la réponse (1-4096 pour GPT-4, 1-16000 pour GPT-5/o1)';
        maxTokensTooltipTitle.textContent = 'Max Tokens :';
        maxTokensTooltipContent.style.display = 'block';
        maxCompletionTokensTooltipContent.style.display = 'none';
        console.log('✅ Max Tokens UI: max_tokens (GPT-4)');
    }
}

/**
 * CORRECTION 1 : Configurer les options VAD disponibles
 * Semantic VAD UNIQUEMENT pour F1
 */
function configureVADOptions(isF1) {
    const vadTypeSelect = document.getElementById('vadType');
    const semanticOption = vadTypeSelect.querySelector('[value="semantic_vad"]');
    const azureSemanticOption = vadTypeSelect.querySelector('[value="azure_semantic_vad"]');
    const azureSemanticMulti = vadTypeSelect.querySelector('[value="azure_semantic_vad_multilingual"]');

    if (!isF1) {
        // F2/F3 : Cacher semantic_vad
        if (semanticOption) semanticOption.style.display = 'none';
        if (azureSemanticOption) azureSemanticOption.style.display = 'none';
        if (azureSemanticMulti) azureSemanticMulti.style.display = 'none';

        // Sélectionner server_vad par défaut
        vadTypeSelect.value = 'server_vad';

        console.log('✅ VAD: Server VAD uniquement (F2/F3)');
    } else {
        // F1 : Tous les VAD disponibles
        if (semanticOption) semanticOption.style.display = 'block';
        if (azureSemanticOption) azureSemanticOption.style.display = 'block';
        if (azureSemanticMulti) azureSemanticMulti.style.display = 'block';

        console.log('✅ VAD: Tous types disponibles (F1)');
    }
}

/**
 * CORRECTION 5 : Configurer la sélection de voix
 * OpenAI disponible UNIQUEMENT pour F1
 */
function configureVoiceSelection(isF1) {
    const voiceTypeStep = document.getElementById('voiceTypeStep');
    const localeStep = document.querySelector('.voice-selection-step:has(#voiceLocaleSelect)');

    if (isF1) {
        // F1 : Afficher l'étape 0 (Type de voix)
        voiceTypeStep.style.display = 'block';
        console.log('✅ F1: Sélection OpenAI/Azure disponible');
    } else {
        // F2/F3 : Cacher étape 0, afficher directement Azure
        voiceTypeStep.style.display = 'none';
        document.getElementById('openaiVoicesStep').style.display = 'none';

        // Forcer Azure
        currentVoiceType = 'azure';

        console.log('✅ F2/F3: Azure uniquement');
    }
}

/**
 * Configurer la disponibilité End of Utterance
 */
function configureEndOfUtterance(isF1) {
    const eouSection = document.getElementById('endOfUtteranceSection');
    const eouAvailability = document.getElementById('endOfUtteranceAvailability');

    if (isF1) {
        // F1 : MASQUER complètement la section (gpt-realtime, gpt-realtime-mini, phi4-mm-realtime)
        console.log('🚫 Masquage section End of Utterance pour modèle Realtime (F1)');
        eouSection.style.display = 'none';

        // Désactiver le checkbox au cas où il serait activé
        document.getElementById('enableEndOfUtterance').disabled = true;
        document.getElementById('enableEndOfUtterance').checked = false;
    } else {
        // F2/F3 : AFFICHER la section
        console.log('✅ Affichage section End of Utterance pour modèle F2/F3');
        eouSection.style.display = 'block';

        eouAvailability.textContent = '✅ Cette fonctionnalité est disponible pour votre modèle';
        eouAvailability.style.color = '#0D47A1';
        eouAvailability.style.background = '#E3F2FD';

        document.getElementById('enableEndOfUtterance').disabled = false;
    }
}

/**
 * Initialiser la grille de langues
 */
function initializeLanguageGrid() {
    const languageGrid = document.getElementById('languageGrid');
    if (!languageGrid) return;

    languageGrid.innerHTML = '';

    MULTILINGUAL_LANGUAGES.forEach(lang => {
        const div = document.createElement('div');
        div.className = 'language-checkbox';
        div.innerHTML = `
            <input class="form-check-input" type="checkbox" 
                   id="lang_${lang.code}" 
                   name="vad_languages" 
                   value="${lang.code}">
            <label class="form-check-label" for="lang_${lang.code}">
                ${lang.name}
            </label>
        `;
        languageGrid.appendChild(div);
    });
}

/**
 * CORRECTION 2 & 4 : Gérer le changement de type VAD
 * - Language UNIQUEMENT si multilingual
 * - Eagerness UNIQUEMENT si semantic_vad
 */
function handleVADTypeChange(e) {
    const vadType = e.target.value;

    // Gestion de Eagerness (Rapidité d'interruption)
    // Uniquement si Semantic VAD (pas Azure Semantic)
    const eagernessGroup = document.getElementById('eagernessGroup');
    if (vadType === 'semantic_vad') {
        eagernessGroup.style.display = 'block';
        console.log('✅ Eagerness affiché (semantic VAD)');
    } else {
        eagernessGroup.style.display = 'none';
        console.log('❌ Eagerness caché (non semantic VAD)');
    }

    // Gestion de Languages
    const languagesGroup = document.getElementById('languagesGroup');
    if (vadType === 'azure_semantic_vad_multilingual') {
        languagesGroup.style.display = 'block';
        console.log('✅ Languages affiché (multilingual)');
    } else {
        languagesGroup.style.display = 'none';
        console.log('❌ Languages caché (non multilingual)');
    }

    // Gestion de Interrupt Response (Activer l'interruption pendant l'appel)
    // Uniquement si Azure Semantic VAD ou Azure Semantic VAD Multilingual
    const interruptGroup = document.getElementById('interruptResponseGroup');
    if (vadType === 'azure_semantic_vad' || vadType === 'azure_semantic_vad_multilingual') {
        interruptGroup.style.display = 'block';
        console.log('✅ Interrupt Response affiché (Azure Semantic VAD)');
    } else {
        interruptGroup.style.display = 'none';
        console.log('❌ Interrupt Response caché (non Azure Semantic VAD)');
    }
}

/**
 * CORRECTION 6 : Gérer la sélection du type de voix (OpenAI vs Azure)
 * Si OpenAI → Cacher Lexicon, Temperature, Rate
 * Si Azure → Afficher Lexicon, Temperature, Rate
 */
function handleVoiceTypeSelection(e) {
    const button = e.currentTarget;
    const voiceType = button.dataset.voiceType;

    // Désélectionner tous les boutons
    document.querySelectorAll('[data-voice-type]').forEach(btn => {
        btn.classList.remove('selected');
    });

    // Sélectionner le bouton cliqué
    button.classList.add('selected');

    currentVoiceType = voiceType;

    if (voiceType === 'openai') {
        // Afficher grille OpenAI
        document.getElementById('openaiVoicesStep').style.display = 'block';

        // Cacher sélection Azure
        document.querySelector('.voice-selection-step:has(#voiceLocaleSelect)').style.display = 'none';
        document.getElementById('genderStep').style.display = 'none';
        document.getElementById('voiceStep').style.display = 'none';

        // Retirer required des champs Azure cachés
        const voiceLocaleSelect = document.getElementById('voiceLocaleSelect');
        if (voiceLocaleSelect) voiceLocaleSelect.removeAttribute('required');

        // CACHER Lexicon, Temperature, Rate
        document.getElementById('customLexiconUrl').closest('.form-group').style.display = 'none';
        document.getElementById('voiceTemperatureGroup').style.display = 'none';
        document.getElementById('speakingRate').closest('.form-group').style.display = 'none';

        // CACHER les 5 nouveaux paramètres Azure (locale, prefer_locales, style, pitch, volume)
        const azureOnlyFields = ['voiceLocaleGroup', 'voicePreferLocalesGroup', 'voiceStyleGroup', 'voicePitchGroup', 'voiceVolumeGroup'];
        azureOnlyFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) field.style.display = 'none';
        });

        console.log('✅ OpenAI sélectionné → Tous paramètres Azure cachés');

    } else {
        // Afficher sélection Azure
        document.querySelector('.voice-selection-step:has(#voiceLocaleSelect)').style.display = 'block';

        // Rétablir required sur les champs Azure
        const voiceLocaleSelect = document.getElementById('voiceLocaleSelect');
        if (voiceLocaleSelect) voiceLocaleSelect.setAttribute('required', 'required');

        // Cacher grille OpenAI
        document.getElementById('openaiVoicesStep').style.display = 'none';

        // AFFICHER Lexicon, Temperature, Rate
        document.getElementById('customLexiconUrl').closest('.form-group').style.display = 'block';
        document.getElementById('voiceTemperatureGroup').style.display = 'block';
        document.getElementById('speakingRate').closest('.form-group').style.display = 'block';

        // AFFICHER les 5 nouveaux paramètres Azure (locale, prefer_locales, style, pitch, volume)
        const azureOnlyFields = ['voiceLocaleGroup', 'voicePreferLocalesGroup', 'voiceStyleGroup', 'voicePitchGroup', 'voiceVolumeGroup'];
        azureOnlyFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) field.style.display = 'block';
        });

        console.log('✅ Azure sélectionné → Tous paramètres Azure affichés (y compris locale, style, pitch, volume)');
    }
}

/**
 * Gérer la sélection d'une voix OpenAI
 */
function handleOpenAIVoiceSelection(e) {
    const card = e.currentTarget;
    const voice = card.dataset.voice;

    // Désélectionner toutes les cartes
    document.querySelectorAll('#openaiVoicesGrid .voice-card').forEach(c => {
        c.classList.remove('selected');
    });

    // Sélectionner la carte cliquée
    card.classList.add('selected');

    // Stocker la sélection
    selectedVoice = voice;
    document.getElementById('voiceName').value = voice;

    // currentVoiceType est déjà défini à 'openai' par handleVoiceTypeSelection
    // Pas besoin de modifier le select

    console.log('✅ Voix OpenAI sélectionnée:', voice, '(type:', currentVoiceType, ')');
}

/**
 * Gérer le changement de type de voix Azure
 */
function handleAzureVoiceTypeChange(e) {
    const voiceType = e.target.value;
    const customEndpointGroup = document.getElementById('customVoiceEndpointGroup');

    if (voiceType === 'azure-custom') {
        customEndpointGroup.style.display = 'block';
        document.getElementById('customVoiceEndpoint').required = true;
    } else {
        customEndpointGroup.style.display = 'none';
        document.getElementById('customVoiceEndpoint').required = false;
    }
}

/**
 * CORRECTION 3 : Gérer le toggle End of Utterance
 * Active/désactive les champs de configuration (OBJET)
 */
function handleEndOfUtteranceToggle(e) {
    const enabled = e.target.checked;
    const configDiv = document.getElementById('endOfUtteranceConfig');

    if (enabled) {
        configDiv.style.display = 'block';
        console.log('✅ End of Utterance activé (objet avec 3 propriétés)');
    } else {
        configDiv.style.display = 'none';
        console.log('❌ End of Utterance désactivé');
    }
}

/**
 * Gérer le changement de modèle de transcription
 */
function handleTranscriptionModelChange(e) {
    const model = e.target.value;
    const languagesGroup = document.getElementById('transcriptionLanguagesGroup');

    if (model === 'azure-speech') {
        languagesGroup.style.display = 'block';
    } else {
        languagesGroup.style.display = 'none';
    }
}

/**
 * Mettre à jour le compteur de phrases
 */
function updatePhraseListCounter() {
    const phraseList = document.getElementById('phraseList');
    if (!phraseList) return;

    const text = phraseList.value;
    const lines = text.split('\n').filter(line => line.trim() !== '');
    const count = lines.length;

    // Afficher le compteur quelque part (à ajouter dans le HTML si besoin)
    console.log(`📋 Phrase list: ${count} phrases`);

    // Warning si > 500
    if (count > 500) {
        alert('⚠️ Maximum 500 phrases autorisées');
    }
}

/**
 * Collecter les données du formulaire
 */
function collectFormData() {
    const vadType = document.getElementById('vadType').value;
    const eouEnabled = document.getElementById('enableEndOfUtterance').checked;

    const data = {
        // Model info
        config_type: document.getElementById('configType').value,
        model_id: document.getElementById('modelId').value,
        model_name: document.getElementById('modelName').value,
        model_family: document.getElementById('modelFamily').value,

        // Input Audio
        input_audio_sampling_rate: parseInt(document.getElementById('inputAudioSamplingRate').value),
        enable_echo_cancellation: document.getElementById('enableEchoCancellation').checked,
        enable_noise_reduction: document.getElementById('enableNoiseReduction').checked,

        // Transcription
        input_transcription_model: document.getElementById('inputTranscriptionModel').value,
        transcription_languages: document.getElementById('transcriptionLanguages').value,
        phrase_list: document.getElementById('phraseList').value.split('\n').filter(p => p.trim() !== ''),

        // VAD
        vad_type: vadType,
        vad_threshold: document.getElementById('vadThreshold').value,
        prefix_padding_ms: document.getElementById('prefixPadding').value,
        speech_duration_ms: document.getElementById('speechDuration').value,
        silence_duration_ms: document.getElementById('silenceDuration').value,
        remove_filler_words: document.getElementById('removeFillerWords').checked,
        create_response: document.getElementById('createResponse').checked,
        auto_truncate: document.getElementById('autoTruncate').checked,
    };

    // Eagerness (SEULEMENT si semantic_vad)
    if (vadType.includes('semantic_vad')) {
        data.eagerness = document.getElementById('eagerness').value;
    }

    // Languages (SEULEMENT si multilingual)
    if (vadType === 'azure_semantic_vad_multilingual') {
        const selectedLangs = Array.from(document.querySelectorAll('[name="vad_languages"]:checked'))
            .map(cb => cb.value);
        data.vad_languages = selectedLangs;
    }

    // Interrupt Response (SEULEMENT si azure semantic)
    if (vadType === 'azure_semantic_vad' || vadType === 'azure_semantic_vad_multilingual') {
        data.interrupt_response = document.getElementById('interruptResponse').checked;
    }

    // End of Utterance (OBJET)
    if (eouEnabled && currentModelFamily !== 'F1_Realtime') {
        data.end_of_utterance_detection = {
            model: document.getElementById('endOfUtteranceModel').value,
            threshold_level: document.getElementById('thresholdLevel').value,
            timeout_ms: parseInt(document.getElementById('timeoutMs').value)
        };
    }

    // Model configuration
    const modelFamily = document.getElementById('modelFamily').value;
    const maxTokensValue = document.getElementById('maxTokens').value;

    // Conditionally set max_tokens or max_completion_tokens based on model family
    if (maxTokensValue) {
        if (modelFamily.includes('gpt-5') || modelFamily.includes('o1') || modelFamily.includes('GPT5') || modelFamily.includes('O1')) {
            data.max_completion_tokens = parseInt(maxTokensValue);
        } else {
            data.max_tokens = parseInt(maxTokensValue);
        }
    }

    // Voice - FIX: Ensure realtime + azure uses 'azure-standard'
    if (modelFamily === 'F1_Realtime' && currentVoiceType === 'azure') {
        data.voice_type = 'azure-standard';
    } else {
        data.voice_type = currentVoiceType || 'azure-standard';
    }
    data.voice_name = document.getElementById('voiceName').value;

    // Si Azure voice → Collecter tous les paramètres Azure
    if (currentVoiceType !== 'openai') {
        data.custom_lexicon_url = document.getElementById('customLexiconUrl').value;
        data.voice_temperature = document.getElementById('voiceTemperature').value;
        data.speaking_rate = parseFloat(document.getElementById('speakingRate').value);

        // Nouveaux paramètres de voix (Azure uniquement)
        const voiceLocale = document.getElementById('voiceLocale').value;
        if (voiceLocale) data.voice_locale = voiceLocale;

        const voicePreferLocales = document.getElementById('voicePreferLocales').value;
        if (voicePreferLocales) {
            data.voice_prefer_locales = voicePreferLocales.split(',').map(l => l.trim()).filter(l => l);
        }

        const voiceStyle = document.getElementById('voiceStyle').value;
        if (voiceStyle) data.voice_style = voiceStyle;

        const voicePitch = document.getElementById('voicePitch').value;
        if (voicePitch) data.voice_pitch = voicePitch;

        const voiceVolume = document.getElementById('voiceVolume').value;
        if (voiceVolume) data.voice_volume = voiceVolume;
    }

    // Custom voice endpoint
    if (data.voice_type === 'azure-custom') {
        data.custom_voice_endpoint = document.getElementById('customVoiceEndpoint').value;
    }

    // Output timestamps
    data.enable_output_timestamps = document.getElementById('enableOutputTimestamps').checked;

    return data;
}

/**
 * Masque la section Speech to Text pour les modèles Realtime
 * Les modèles F1 (Realtime) sont audio-to-audio natifs, pas besoin de transcription séparée
 */
function hideInputTranscriptionForRealtime() {
    const modelFamilyInput = document.getElementById('modelFamily');
    const inputTranscriptionGroup = document.getElementById('inputTranscriptionGroup');

    if (!modelFamilyInput || !inputTranscriptionGroup) {
        console.warn('⚠️ Éléments introuvables pour masquer la transcription');
        return;
    }

    const modelFamily = modelFamilyInput.value;

    // Si c'est un modèle Realtime (F1), masquer la transcription
    if (modelFamily === 'F1_Realtime' || modelFamily === 'Realtime') {
        inputTranscriptionGroup.style.display = 'none';
        console.log('✅ Section "Speech to Text" masquée pour modèle Realtime (audio-to-audio natif)');
    } else {
        inputTranscriptionGroup.style.display = 'block';
        console.log('📝 Section "Speech to Text" affichée pour modèle non-Realtime');
    }
}

/**
 * Charger les lexiques depuis Azure Storage
 */
async function loadLexicons() {
    const selectElement = document.getElementById('customLexiconSelect');
    if (!selectElement) return;

    console.log('📚 Chargement des lexiques depuis Azure Storage...');

    try {
        const response = await fetch('/agents/api/lexicons');
        const data = await response.json();

        if (data.success && data.lexicons) {
            // Vider le select
            selectElement.innerHTML = '<option value="">-- Aucun lexique --</option>';

            // Ajouter chaque lexique
            data.lexicons.forEach(lexicon => {
                const option = document.createElement('option');
                option.value = lexicon.url;
                option.textContent = lexicon.name;
                option.setAttribute('data-size', lexicon.size);
                option.setAttribute('data-modified', lexicon.last_modified);
                selectElement.appendChild(option);
            });

            console.log(`✅ ${data.count} lexiques chargés`);
        } else {
            console.error('❌ Erreur lors du chargement des lexiques:', data.error);
            selectElement.innerHTML = '<option value="">Erreur de chargement</option>';
        }
    } catch (error) {
        console.error('❌ Erreur réseau:', error);
        selectElement.innerHTML = '<option value="">Erreur de chargement</option>';
    }
}

// Exposer pour utilisation externe si besoin
window.Step2 = {
    collectFormData
};