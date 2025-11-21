// ============================================
// PERSONAL VOICE - MAIN LOGIC
// Version: 2.1.0 - Scores 90%/80%
// ============================================

console.log('🎯 Personal Voice Script loaded v2.1.0');

// ============================================
// VARIABLES GLOBALES
// ============================================
let selectedProjectId = null;
let consentId = null;
let personalVoiceId = null;
let speakerProfileId = null;

// Audio blobs
let consentAudioBlob = null;
let voiceAudioBlobs = {
    1: null,
    2: null,
    3: null
};

// Validation status
let voiceValidationStatus = {
    1: false,
    2: false,
    3: false
};

// Recorders
let consentRecorder = null;
let voiceRecorders = {
    1: null,
    2: null,
    3: null
};

let consentRecordingInterval = null;
let voiceRecordingIntervals = {
    1: null,
    2: null,
    3: null
};

// Textes des échantillons vocaux
const VOICE_SAMPLE_TEXTS = {
    1: "Bienvenue dans ce module de formation sur l'intelligence artificielle. Aujourd'hui, nous allons découvrir les concepts fondamentaux du machine learning et leurs applications pratiques. N'hésitez pas à poser des questions si certains points nécessitent des éclaircissements. Ensemble, nous progresserons étape par étape vers la maîtrise de ces technologies.",

    2: "Bonjour et merci d'avoir contacté notre service client. Je suis là pour vous aider aujourd'hui. Pourriez-vous me donner plus de détails sur votre demande ? Je vais faire mon possible pour résoudre votre problème rapidement et efficacement. Votre satisfaction est notre priorité et nous sommes à votre écoute.",

    3: "Bienvenue dans cet épisode où nous explorons les dernières innovations technologiques. Aujourd'hui, nous allons discuter de l'impact de l'intelligence artificielle sur notre quotidien. Ces avancées transforment profondément notre façon de travailler et de communiquer. Restez avec nous pour découvrir comment ces technologies façonnent notre avenir."
};

// ============================================
// INITIALISATION
// ============================================
document.addEventListener('DOMContentLoaded', function () {
    console.log('✅ DOM loaded');
    loadProjects();
    updateConsentText();
    updateCreateVoiceButton();

    const firstName = document.getElementById('firstName');
    const lastName = document.getElementById('lastName');
    const companyName = document.getElementById('companyName');

    if (firstName) firstName.addEventListener('input', updateConsentText);
    if (lastName) lastName.addEventListener('input', updateConsentText);
    if (companyName) companyName.addEventListener('input', updateConsentText);
});

// ============================================
// NOTIFICATIONS
// ============================================
function showNotification(message, type) {
    type = type || 'success';

    const toastEl = document.getElementById('notificationToast');
    if (!toastEl) {
        console.error('Toast element not found');
        return;
    }

    const toastBody = toastEl.querySelector('.toast-body');
    const toastHeader = toastEl.querySelector('.toast-header');

    const icons = {
        'success': 'bi-check-circle-fill',
        'error': 'bi-exclamation-triangle-fill',
        'warning': 'bi-exclamation-circle-fill',
        'info': 'bi-info-circle-fill'
    };

    const colors = {
        'success': '#4CAF50',
        'error': '#f44336',
        'warning': '#FFC107',
        'info': '#2196F3'
    };

    const icon = toastHeader.querySelector('i');
    if (icon) {
        icon.className = 'bi ' + (icons[type] || icons.info) + ' me-2';
    }

    toastHeader.style.background = colors[type] || colors.info;
    toastBody.textContent = message;

    const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: 5000
    });
    toast.show();
}

// ============================================
// STEPPER NAVIGATION
// ============================================
function goToStep(stepNumber) {
    document.querySelectorAll('.step-content').forEach(function (content) {
        content.classList.remove('active');
    });

    const stepContent = document.getElementById('step' + stepNumber);
    if (stepContent) {
        stepContent.classList.add('active');
    }

    document.querySelectorAll('.step').forEach(function (step, index) {
        step.classList.remove('active', 'completed');

        if (index + 1 < stepNumber) {
            step.classList.add('completed');
        } else if (index + 1 === stepNumber) {
            step.classList.add('active');
        }
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================
// ÉTAPE 1: GESTION DES PROJETS
// ============================================
async function loadProjects() {
    try {
        const response = await fetch('/creer-une-voix/api/projects');
        const data = await response.json();

        if (data.success) {
            const select = document.getElementById('existingProjects');
            if (!select) return;

            select.innerHTML = '<option value="">-- Sélectionner un projet --</option>';

            data.projects.forEach(function (project) {
                const option = document.createElement('option');
                option.value = project.id;
                option.textContent = project.project_name + ' (' + project.id + ')';
                select.appendChild(option);
            });

            console.log('✅ ' + data.projects.length + ' projets chargés');
        }
    } catch (error) {
        console.error('❌ Erreur chargement projets:', error);
        showNotification('Erreur de chargement des projets', 'error');
    }
}

function selectExistingProject() {
    const select = document.getElementById('existingProjects');
    if (!select) return;

    selectedProjectId = select.value;

    const nextBtn = document.getElementById('step1NextBtn');
    if (!nextBtn) return;

    if (selectedProjectId) {
        nextBtn.disabled = false;
        showNotification('Projet sélectionné !');
        console.log('📁 Projet sélectionné:', selectedProjectId);
    } else {
        nextBtn.disabled = true;
    }
}

async function createProject() {
    const projectName = document.getElementById('projectName').value;
    const projectDescription = document.getElementById('projectDescription').value;

    if (!projectName) {
        showNotification('Veuillez entrer un nom de projet', 'warning');
        return;
    }

    try {
        const response = await fetch('/creer-une-voix/api/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_name: projectName,
                description: projectDescription
            })
        });

        const data = await response.json();

        if (data.success) {
            selectedProjectId = data.project_id;
            showNotification('✅ Projet créé avec succès !');

            const nextBtn = document.getElementById('step1NextBtn');
            if (nextBtn) nextBtn.disabled = false;

            await loadProjects();

            const select = document.getElementById('existingProjects');
            if (select) select.value = selectedProjectId;

            console.log('✅ Projet créé:', selectedProjectId);
        } else {
            showNotification('Erreur: ' + data.error, 'error');
        }
    } catch (error) {
        showNotification('Erreur: ' + error.message, 'error');
        console.error('❌ Erreur:', error);
    }
}

// ============================================
// ÉTAPE 2: CONSENTEMENT (Score 90%)
// ============================================
function updateConsentText() {
    const firstName = document.getElementById('firstName');
    const lastName = document.getElementById('lastName');
    const companyName = document.getElementById('companyName');

    const firstNameValue = firstName ? firstName.value || '[prénom]' : '[prénom]';
    const lastNameValue = lastName ? lastName.value || '[nom]' : '[nom]';
    const companyNameValue = companyName ? companyName.value || '[nom de l\'entreprise]' : '[nom de l\'entreprise]';

    const fullNameDisplay = document.getElementById('fullNameDisplay');
    const companyNameDisplay = document.getElementById('companyNameDisplay');

    if (fullNameDisplay) {
        fullNameDisplay.textContent = firstNameValue + ' ' + lastNameValue;
    }
    if (companyNameDisplay) {
        companyNameDisplay.textContent = companyNameValue;
    }
}

function getConsentText() {
    const firstName = document.getElementById('firstName').value;
    const lastName = document.getElementById('lastName').value;
    const companyName = document.getElementById('companyName').value;
    const locale = document.getElementById('locale').value;

    const templates = {
        'fr-FR': 'Je ' + firstName + ' ' + lastName + ' suis conscient que les enregistrements de ma voix seront utilisés par ' + companyName + ' pour créer et utiliser une version synthétique de ma voix.',
        'en-US': 'I ' + firstName + ' ' + lastName + ' am aware that recordings of my voice will be used by ' + companyName + ' to create and use a synthetic version of my voice.',
        'en-GB': 'I ' + firstName + ' ' + lastName + ' am aware that recordings of my voice will be used by ' + companyName + ' to create and use a synthetic version of my voice.',
        'es-ES': 'Yo ' + firstName + ' ' + lastName + ' soy consciente de que las grabaciones de mi voz serán utilizadas por ' + companyName + ' para crear y usar una versión sintética de mi voz.',
        'de-DE': 'Ich ' + firstName + ' ' + lastName + ' bin mir bewusst, dass Aufnahmen meiner Stimme von ' + companyName + ' verwendet werden, um eine synthetische Version meiner Stimme zu erstellen und zu verwenden.',
        'pt-BR': 'Eu ' + firstName + ' ' + lastName + ' estou ciente de que as gravações da minha voz serão usadas por ' + companyName + ' para criar e usar uma versão sintética da minha voz.'
    };

    return templates[locale] || templates['fr-FR'];
}

async function toggleConsentRecording() {
    const btn = document.getElementById('consentRecorderBtn');
    const container = document.getElementById('consentRecorder');

    if (!btn || !container) return;

    if (!consentRecorder || !consentRecorder.isCurrentlyRecording()) {
        try {
            consentRecorder = new AzureCompatibleRecorder();
            await consentRecorder.startRecording();

            btn.classList.remove('record');
            btn.classList.add('recording');
            btn.innerHTML = '<i class="bi bi-stop-fill"></i>';
            container.classList.add('recording');

            let seconds = 0;
            consentRecordingInterval = setInterval(function () {
                seconds++;
                const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
                const secs = (seconds % 60).toString().padStart(2, '0');
                const timeDisplay = document.getElementById('consentRecordingTime');
                if (timeDisplay) {
                    timeDisplay.textContent = mins + ':' + secs;
                }
            }, 1000);

            showNotification('🎙️ Lisez le texte de consentement', 'info');

        } catch (error) {
            showNotification('Erreur microphone: ' + error.message, 'error');
            console.error('❌ Erreur:', error);
        }
    } else {
        try {
            const result = await consentRecorder.stopRecording();

            if (consentRecordingInterval) {
                clearInterval(consentRecordingInterval);
            }

            btn.classList.remove('recording');
            btn.classList.add('record');
            btn.innerHTML = '<i class="bi bi-mic-fill"></i>';
            container.classList.remove('recording');

            if (result.duration < 8) {
                showNotification('⚠️ Enregistrement trop court (min 8 secondes)', 'warning');
                return;
            }

            if (result.duration > 20) {
                showNotification('⚠️ Enregistrement trop long. Lisez juste le texte.', 'warning');
            }

            consentAudioBlob = result.blob;

            const audioUrl = URL.createObjectURL(consentAudioBlob);
            const audioEl = document.getElementById('consentAudio');
            const previewEl = document.getElementById('consentAudioPreview');

            if (audioEl) audioEl.src = audioUrl;
            if (previewEl) previewEl.style.display = 'block';

            showNotification('✅ Enregistrement OK (' + result.duration.toFixed(1) + 's)');

        } catch (error) {
            showNotification('Erreur: ' + error.message, 'error');
            console.error('❌ Erreur:', error);
        }
    }
}

async function validateConsentTranscription() {
    if (!consentAudioBlob) {
        showNotification('Aucun enregistrement à valider', 'error');
        return;
    }

    const validationDiv = document.getElementById('consentValidation');
    if (!validationDiv) return;

    validationDiv.style.display = 'block';
    validationDiv.innerHTML = '<div style="text-align: center; padding: 20px;"><div class="spinner-border text-primary" role="status"></div><p style="margin-top: 10px; color: var(--waka-text-muted);">🎙️ Transcription et validation en cours...</p></div>';

    try {
        const formData = new FormData();
        formData.append('audio', consentAudioBlob, 'consent.wav');
        formData.append('type', 'consent');
        formData.append('project_id', selectedProjectId || 'temp');

        const uploadResponse = await fetch('/creer-une-voix/api/upload-audio', {
            method: 'POST',
            body: formData
        });

        const uploadData = await uploadResponse.json();

        if (!uploadData.success) {
            throw new Error(uploadData.error);
        }

        const expectedText = getConsentText();
        const locale = document.getElementById('locale').value;

        const transcribeResponse = await fetch('/creer-une-voix/api/transcribe-consent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                audio_url: uploadData.blob_url,
                expected_text: expectedText,
                locale: locale
            })
        });

        const transcribeData = await transcribeResponse.json();

        if (!transcribeData.success) {
            throw new Error(transcribeData.error || 'Erreur transcription');
        }

        console.log('✅ Transcription consentement:', transcribeData);

        displayValidationResults(
            transcribeData.comparison,
            transcribeData.transcribed_text,
            'consentValidation',
            90  // Score minimum 90%
        );

        const submitBtn = document.getElementById('submitConsentBtn');
        if (submitBtn) {
            if (transcribeData.comparison.similarity_percentage >= 90) {
                submitBtn.disabled = false;
                showNotification('✅ Validation réussie ! Vous pouvez continuer.', 'success');
            } else {
                submitBtn.disabled = true;
                showNotification('❌ Score insuffisant. Le consentement nécessite 90% minimum.', 'error');
            }
        }

    } catch (error) {
        console.error('❌ Erreur validation:', error);
        validationDiv.innerHTML = '<div class="alert alert-danger"><i class="bi bi-exclamation-triangle-fill"></i><strong>Erreur de validation</strong><br>' + error.message + '</div>';
        showNotification('Erreur validation: ' + error.message, 'error');
    }
}

function displayValidationResults(comparison, transcribedText, containerId, minScore) {
    const validationDiv = document.getElementById(containerId);
    if (!validationDiv) return;

    const scoreColor = comparison.similarity_percentage >= minScore ? '#4CAF50' :
        comparison.similarity_percentage >= (minScore - 10) ? '#FFC107' : '#f44336';

    const iconClass = comparison.similarity_percentage >= minScore ? 'bi-check-circle-fill' : 'bi-x-circle-fill';

    let missingWordsHtml = '';
    if (comparison.missing_words && comparison.missing_words.length > 0) {
        const badges = comparison.missing_words.map(function (word) {
            return '<span class="missing-word-badge">' + word + '</span>';
        }).join('');

        missingWordsHtml = '<div style="margin-top: 16px; padding: 12px; background: #ffebee; border-radius: 8px;"><strong style="color: #c62828;">⚠️ Mots manquants:</strong><div style="margin-top: 8px;">' + badges + '</div></div>';
    }

    const retryButton = comparison.similarity_percentage < minScore ?
        '<div style="text-align: center; margin-top: 20px;"><button class="btn-accent" onclick="' + (containerId === 'consentValidation' ? 'retryConsentRecording()' : 'retryVoiceRecording()') + '"><i class="bi bi-arrow-clockwise"></i> Réenregistrer</button></div>' : '';

    validationDiv.innerHTML = '<div style="background: var(--waka-white); border-radius: 12px; padding: 24px; border: 2px solid ' + scoreColor + ';"><div style="text-align: center; margin-bottom: 20px;" class="validation-score-container"><i class="bi ' + iconClass + '" style="font-size: 3rem; color: ' + scoreColor + ';"></i><h4 style="margin-top: 10px; color: var(--waka-primary);">Score : ' + comparison.similarity_percentage + '% / ' + minScore + '%</h4></div><div style="background: var(--waka-border); height: 12px; border-radius: 999px; overflow: hidden; margin-bottom: 20px;"><div style="background: ' + scoreColor + '; height: 100%; width: ' + comparison.similarity_percentage + '%; transition: width 0.5s ease;"></div></div><div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 20px;"><div class="stat-card"><div style="font-size: 24px; font-weight: 700; color: var(--waka-primary);">' + comparison.word_accuracy + '%</div><div style="font-size: 12px; color: var(--waka-text-muted);">Précision mots</div></div><div class="stat-card"><div style="font-size: 24px; font-weight: 700; color: var(--waka-primary);">' + comparison.common_words_count + '/' + comparison.total_expected_words + '</div><div style="font-size: 12px; color: var(--waka-text-muted);">Mots corrects</div></div></div><div style="background: ' + (comparison.similarity_percentage >= minScore ? '#e8f5e9' : '#fff3e0') + '; padding: 12px 16px; border-radius: 8px; border-left: 4px solid ' + scoreColor + ';"><strong>' + comparison.recommendation + '</strong></div>' + missingWordsHtml + '<div style="margin-top: 20px;"><button class="btn btn-sm btn-secondary-custom" onclick="toggleTranscript(\'' + containerId + '\')" style="width: 100%;"><i class="bi bi-file-text"></i> Voir la transcription</button><div id="' + containerId + 'Transcript" style="display: none; margin-top: 12px; padding: 12px; background: var(--waka-off-white); border-radius: 8px; font-size: 13px;"><strong>Transcription :</strong><br><em style="color: var(--waka-text-muted);">"' + transcribedText + '"</em></div></div>' + retryButton + '</div>';
}

function toggleTranscript(containerId) {
    const transcriptDiv = document.getElementById(containerId + 'Transcript');
    if (transcriptDiv) {
        transcriptDiv.style.display = transcriptDiv.style.display === 'none' ? 'block' : 'none';
    }
}

function retryConsentRecording() {
    consentAudioBlob = null;

    const previewEl = document.getElementById('consentAudioPreview');
    const validationEl = document.getElementById('consentValidation');
    const submitBtn = document.getElementById('submitConsentBtn');
    const timeEl = document.getElementById('consentRecordingTime');

    if (previewEl) previewEl.style.display = 'none';
    if (validationEl) validationEl.style.display = 'none';
    if (submitBtn) submitBtn.disabled = true;
    if (timeEl) timeEl.textContent = '00:00';

    showNotification('Prêt pour un nouvel enregistrement', 'info');
}

async function submitConsent() {
    if (!consentAudioBlob) {
        showNotification('Veuillez enregistrer et valider votre consentement', 'error');
        return;
    }

    const firstName = document.getElementById('firstName').value;
    const lastName = document.getElementById('lastName').value;
    const companyName = document.getElementById('companyName').value;
    const locale = document.getElementById('locale').value;

    if (!firstName || !lastName || !companyName) {
        showNotification('Veuillez remplir tous les champs', 'warning');
        return;
    }

    try {
        showNotification('📤 Soumission du consentement...', 'info');

        const formData = new FormData();
        formData.append('audio', consentAudioBlob, 'consent.wav');
        formData.append('type', 'consent');
        formData.append('project_id', selectedProjectId);

        const uploadResponse = await fetch('/creer-une-voix/api/upload-audio', {
            method: 'POST',
            body: formData
        });

        const uploadData = await uploadResponse.json();

        if (!uploadData.success) {
            showNotification('Erreur upload: ' + uploadData.error, 'error');
            return;
        }

        const consentResponse = await fetch('/creer-une-voix/api/consents', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_id: selectedProjectId,
                audio_url: uploadData.blob_url,
                locale: locale,
                voice_talent_name: firstName + ' ' + lastName,
                company_name: companyName
            })
        });

        const consentData = await consentResponse.json();

        if (consentData.success) {
            consentId = consentData.consent_id;
            showNotification('✅ Consentement enregistré avec succès !');
            goToStep(3);
            console.log('✅ Consent ID:', consentId);
        } else {
            showNotification('Erreur: ' + consentData.error, 'error');
        }

    } catch (error) {
        showNotification('Erreur: ' + error.message, 'error');
        console.error('❌ Erreur:', error);
    }
}

// ============================================
// ÉTAPE 3: 3 ÉCHANTILLONS VOCAUX (Score 80%)
// ============================================
async function toggleVoiceRecording(sampleNumber) {
    const btn = document.getElementById('voiceRecorderBtn' + sampleNumber);
    const container = document.getElementById('voiceRecorder' + sampleNumber);

    if (!btn || !container) return;

    if (!voiceRecorders[sampleNumber] || !voiceRecorders[sampleNumber].isCurrentlyRecording()) {
        try {
            voiceRecorders[sampleNumber] = new AzureCompatibleRecorder();
            await voiceRecorders[sampleNumber].startRecording();

            btn.classList.remove('record');
            btn.classList.add('recording');
            btn.innerHTML = '<i class="bi bi-stop-fill"></i>';
            container.classList.add('recording');

            let seconds = 0;
            voiceRecordingIntervals[sampleNumber] = setInterval(function () {
                seconds++;
                const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
                const secs = (seconds % 60).toString().padStart(2, '0');
                const timeDisplay = document.getElementById('voiceRecordingTime' + sampleNumber);
                if (timeDisplay) {
                    timeDisplay.textContent = mins + ':' + secs;
                }
            }, 1000);

            showNotification('🎙️ Lisez le texte de l\'échantillon ' + sampleNumber, 'info');

        } catch (error) {
            showNotification('Erreur microphone: ' + error.message, 'error');
            console.error('❌ Erreur:', error);
        }
    } else {
        try {
            const result = await voiceRecorders[sampleNumber].stopRecording();

            if (voiceRecordingIntervals[sampleNumber]) {
                clearInterval(voiceRecordingIntervals[sampleNumber]);
            }

            btn.classList.remove('recording');
            btn.classList.add('record');
            btn.innerHTML = '<i class="bi bi-mic-fill"></i>';
            container.classList.remove('recording');

            if (result.duration < 5) {
                showNotification('⚠️ Enregistrement trop court (min 5 secondes)', 'warning');
                return;
            }

            if (result.duration > 90) {
                showNotification('⚠️ Enregistrement trop long (max 90 secondes)', 'warning');
                return;
            }

            voiceAudioBlobs[sampleNumber] = result.blob;

            const audioUrl = URL.createObjectURL(voiceAudioBlobs[sampleNumber]);
            const audioEl = document.getElementById('voiceAudio' + sampleNumber);
            const previewEl = document.getElementById('voiceAudioPreview' + sampleNumber);

            if (audioEl) audioEl.src = audioUrl;
            if (previewEl) previewEl.style.display = 'block';

            showNotification('✅ Échantillon ' + sampleNumber + ' enregistré (' + result.duration.toFixed(1) + 's)');

        } catch (error) {
            showNotification('Erreur: ' + error.message, 'error');
            console.error('❌ Erreur:', error);
        }
    }
}

async function validateVoiceSample(sampleNumber) {
    if (!voiceAudioBlobs[sampleNumber]) {
        showNotification('Aucun enregistrement à valider', 'error');
        return;
    }

    const validationDiv = document.getElementById('voiceValidation' + sampleNumber);
    if (!validationDiv) return;

    validationDiv.style.display = 'block';
    validationDiv.innerHTML = '<div style="text-align: center; padding: 20px;"><div class="spinner-border text-primary" role="status"></div><p style="margin-top: 10px;">🎙️ Validation échantillon ' + sampleNumber + '...</p></div>';

    try {
        const formData = new FormData();
        formData.append('audio', voiceAudioBlobs[sampleNumber], 'voice_sample_' + sampleNumber + '.wav');
        formData.append('type', 'voice');
        formData.append('project_id', selectedProjectId || 'temp');

        const uploadResponse = await fetch('/creer-une-voix/api/upload-audio', {
            method: 'POST',
            body: formData
        });

        const uploadData = await uploadResponse.json();

        if (!uploadData.success) {
            throw new Error(uploadData.error);
        }

        const expectedText = VOICE_SAMPLE_TEXTS[sampleNumber];
        const locale = document.getElementById('locale').value;

        const transcribeResponse = await fetch('/creer-une-voix/api/transcribe-consent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                audio_url: uploadData.blob_url,
                expected_text: expectedText,
                locale: locale
            })
        });

        const transcribeData = await transcribeResponse.json();

        if (!transcribeData.success) {
            throw new Error(transcribeData.error || 'Erreur transcription');
        }

        console.log('✅ Transcription échantillon ' + sampleNumber + ':', transcribeData);

        displayValidationResults(
            transcribeData.comparison,
            transcribeData.transcribed_text,
            'voiceValidation' + sampleNumber,
            80  // Score minimum 80%
        );

        if (transcribeData.comparison.similarity_percentage >= 80) {
            voiceValidationStatus[sampleNumber] = true;
            updateValidationBadge(sampleNumber, true);
            updateValidationSummary();
            updateCreateVoiceButton();
            showNotification('✅ Échantillon ' + sampleNumber + ' validé !', 'success');
        } else {
            voiceValidationStatus[sampleNumber] = false;
            updateValidationBadge(sampleNumber, false);
            updateCreateVoiceButton();
            showNotification('❌ Échantillon ' + sampleNumber + ' : score insuffisant (min 80%)', 'error');
        }

    } catch (error) {
        console.error('❌ Erreur validation:', error);
        validationDiv.innerHTML = '<div class="alert alert-danger"><i class="bi bi-exclamation-triangle-fill"></i><strong>Erreur de validation</strong><br>' + error.message + '</div>';
        showNotification('Erreur validation: ' + error.message, 'error');
    }
}

function updateValidationBadge(sampleNumber, isValid) {
    const badge = document.getElementById('sample' + sampleNumber + 'Badge');
    const card = document.getElementById('voiceSample' + sampleNumber + 'Card');

    if (!badge || !card) return;

    if (isValid) {
        badge.className = 'validation-badge validated';
        badge.innerHTML = '<i class="bi bi-check-circle-fill"></i> Validé';
        card.classList.add('validated');
    } else {
        badge.className = 'validation-badge not-validated';
        badge.innerHTML = '<i class="bi bi-x-circle"></i> Non validé';
        card.classList.remove('validated');
    }
}

function updateValidationSummary() {
    for (let i = 1; i <= 3; i++) {
        const item = document.getElementById('validationItem' + i);
        if (!item) continue;

        if (voiceValidationStatus[i]) {
            item.classList.add('validated');
            const icon = item.querySelector('i');
            if (icon) icon.className = 'bi bi-check-circle-fill';
        } else {
            item.classList.remove('validated');
            const icon = item.querySelector('i');
            if (icon) icon.className = 'bi bi-circle';
        }
    }
}

function updateCreateVoiceButton() {
    const btn = document.getElementById('createVoiceBtn');
    if (!btn) return;

    const validCount = Object.values(voiceValidationStatus).filter(function (v) { return v; }).length;

    btn.innerHTML = '<i class="bi bi-check-circle"></i> Créer la voix (' + validCount + '/3 validés)';
    btn.disabled = validCount !== 3;
}

async function createPersonalVoice() {
    const validCount = Object.values(voiceValidationStatus).filter(function (v) { return v; }).length;

    if (validCount !== 3) {
        showNotification('Les 3 échantillons doivent être validés', 'error');
        return;
    }

    const voiceName = document.getElementById('voiceName').value;
    const description = document.getElementById('voiceDescription').value;

    if (!voiceName) {
        showNotification('Veuillez nommer votre voix', 'warning');
        return;
    }

    const statusEl = document.getElementById('voiceCreationStatus');
    const createBtn = document.getElementById('createVoiceBtn');

    if (statusEl) statusEl.style.display = 'block';
    if (createBtn) createBtn.disabled = true;

    try {
        showNotification('📤 Upload des 3 échantillons vocaux...', 'info');

        const audioUrls = [];
        for (let i = 1; i <= 3; i++) {
            const formData = new FormData();
            formData.append('audio', voiceAudioBlobs[i], 'voice_sample_' + i + '.wav');
            formData.append('type', 'voice');
            formData.append('project_id', selectedProjectId);

            const uploadResponse = await fetch('/creer-une-voix/api/upload-audio', {
                method: 'POST',
                body: formData
            });

            const uploadData = await uploadResponse.json();

            if (!uploadData.success) {
                throw new Error('Erreur upload échantillon ' + i + ': ' + uploadData.error);
            }

            audioUrls.push(uploadData.blob_url);
            console.log('✅ Échantillon ' + i + ' uploadé');
        }

        showNotification('⏳ Création de la voix personnelle...', 'info');

        const voiceResponse = await fetch('/creer-une-voix/api/personal-voices', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_id: selectedProjectId,
                consent_id: consentId,
                audio_urls: audioUrls,
                voice_name: voiceName,
                description: description
            })
        });

        const voiceData = await voiceResponse.json();

        if (voiceData.success) {
            personalVoiceId = voiceData.personal_voice_id;
            showNotification('⏳ Traitement en cours... Veuillez patienter.', 'info');

            await pollVoiceStatus(personalVoiceId);
        } else {
            showNotification('Erreur: ' + voiceData.error, 'error');
            if (statusEl) statusEl.style.display = 'none';
            if (createBtn) createBtn.disabled = false;
        }

    } catch (error) {
        showNotification('Erreur: ' + error.message, 'error');
        if (statusEl) statusEl.style.display = 'none';
        if (createBtn) createBtn.disabled = false;
        console.error('❌ Erreur:', error);
    }
}

async function pollVoiceStatus(voiceId) {
    const maxAttempts = 60;
    let attempts = 0;

    const checkStatus = async function () {
        try {
            const response = await fetch('/creer-une-voix/api/personal-voices/' + voiceId + '?project_id=' + selectedProjectId);
            const data = await response.json();

            if (data.success) {
                const status = data.voice.status;

                if (status === 'Succeeded' && data.voice.speakerProfileId) {
                    speakerProfileId = data.voice.speakerProfileId;

                    const profileInput = document.getElementById('speakerProfileId');
                    if (profileInput) profileInput.value = speakerProfileId;

                    const statusEl = document.getElementById('voiceCreationStatus');
                    if (statusEl) statusEl.style.display = 'none';

                    showNotification('✅ Voix personnelle créée avec succès !', 'success');
                    goToStep(4);
                    return;
                } else if (status === 'Failed') {
                    showNotification('❌ Échec de la création de la voix', 'error');

                    const statusEl = document.getElementById('voiceCreationStatus');
                    const createBtn = document.getElementById('createVoiceBtn');

                    if (statusEl) statusEl.style.display = 'none';
                    if (createBtn) createBtn.disabled = false;
                    return;
                }
            }

            attempts++;
            if (attempts < maxAttempts) {
                setTimeout(checkStatus, 5000);
            } else {
                showNotification('⏱️ Délai d\'attente dépassé', 'error');

                const statusEl = document.getElementById('voiceCreationStatus');
                const createBtn = document.getElementById('createVoiceBtn');

                if (statusEl) statusEl.style.display = 'none';
                if (createBtn) createBtn.disabled = false;
            }

        } catch (error) {
            console.error('❌ Erreur polling:', error);
            setTimeout(checkStatus, 5000);
        }
    };

    checkStatus();
}

// ============================================
// ÉTAPE 4: SYNTHÈSE
// ============================================
async function synthesizeSpeech() {
    const text = document.getElementById('synthesisText').value;
    const baseVoice = document.getElementById('baseVoice').value;

    if (!text) {
        showNotification('Veuillez entrer un texte à synthétiser', 'error');
        return;
    }

    if (!speakerProfileId) {
        showNotification('Speaker Profile ID manquant', 'error');
        return;
    }

    try {
        showNotification('🎵 Synthèse en cours...', 'info');

        const response = await fetch('/creer-une-voix/api/synthesize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                speaker_profile_id: speakerProfileId,
                voice_name: baseVoice
            })
        });

        const data = await response.json();

        if (data.success) {
            const audioEl = document.getElementById('synthesizedAudio');
            const resultEl = document.getElementById('synthesisResult');

            if (audioEl) audioEl.src = data.audio_url;
            if (resultEl) resultEl.style.display = 'block';

            showNotification('✅ Synthèse réussie !', 'success');
        } else {
            showNotification('Erreur: ' + data.error, 'error');
        }

    } catch (error) {
        showNotification('Erreur: ' + error.message, 'error');
    }
}

function copySpeakerProfileId() {
    const input = document.getElementById('speakerProfileId');
    if (!input) return;

    input.select();
    document.execCommand('copy');
    showNotification('📋 Speaker Profile ID copié !', 'success');
}

function downloadSynthesizedAudio() {
    const audio = document.getElementById('synthesizedAudio');
    if (!audio || !audio.src) return;

    const a = document.createElement('a');
    a.href = audio.src;
    a.download = 'synthesized_voice.mp3';
    a.click();
    showNotification('📥 Téléchargement démarré', 'success');
}

// ============================================
// RESET WIZARD
// ============================================
function resetWizard() {
    if (!confirm('Êtes-vous sûr de vouloir recommencer ? Toutes les données seront perdues.')) {
        return;
    }

    selectedProjectId = null;
    consentId = null;
    personalVoiceId = null;
    speakerProfileId = null;
    consentAudioBlob = null;
    voiceAudioBlobs = { 1: null, 2: null, 3: null };
    voiceValidationStatus = { 1: false, 2: false, 3: false };

    const elements = {
        'existingProjects': '',
        'projectName': '',
        'projectDescription': '',
        'firstName': '',
        'lastName': '',
        'companyName': '',
        'voiceName': '',
        'voiceDescription': '',
        'synthesisText': ''
    };

    for (const id in elements) {
        const el = document.getElementById(id);
        if (el) el.value = elements[id];
    }

    const displays = {
        'fullNameDisplay': '[prénom et nom]',
        'companyNameDisplay': '[nom de l\'entreprise]'
    };

    for (const id in displays) {
        const el = document.getElementById(id);
        if (el) el.textContent = displays[id];
    }

    const hideElements = ['consentAudioPreview', 'consentValidation', 'synthesisResult'];
    hideElements.forEach(function (id) {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });

    for (let i = 1; i <= 3; i++) {
        const preview = document.getElementById('voiceAudioPreview' + i);
        const validation = document.getElementById('voiceValidation' + i);

        if (preview) preview.style.display = 'none';
        if (validation) validation.style.display = 'none';

        updateValidationBadge(i, false);
    }

    const buttons = {
        'step1NextBtn': true,
        'submitConsentBtn': true
    };

    for (const id in buttons) {
        const btn = document.getElementById(id);
        if (btn) btn.disabled = buttons[id];
    }

    updateCreateVoiceButton();

    const timers = ['consentRecordingTime', 'voiceRecordingTime1', 'voiceRecordingTime2', 'voiceRecordingTime3'];
    timers.forEach(function (id) {
        const el = document.getElementById(id);
        if (el) el.textContent = '00:00';
    });

    updateValidationSummary();
    goToStep(1);
    loadProjects();

    showNotification('🔄 Wizard réinitialisé', 'info');
}

console.log('✅ Personal Voice Script initialized v2.1.0 - Scores: Consentement 90%, Audios 80%');