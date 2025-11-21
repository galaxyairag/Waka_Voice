// ===================================================================
// Gestion de la sélection hiérarchique des voix Azure
// ===================================================================

class AzureVoiceSelector {
    constructor(apiBaseUrl = '/api/azure-voices', voiceType = 'azure') {
        this.apiBaseUrl = apiBaseUrl;
        this.voiceType = voiceType; // 'azure' ou 'personal'
        this.languages = [];
        this.voices = [];
        this.selectedLocale = null;
        this.selectedGender = null;
        this.selectedVoice = null;

        this.init();
    }

    /**
     * Initialisation
     */
    async init() {
        console.log(`🎤 Initialisation Voice Selector (Type: ${this.voiceType})`);
        this.setupEventListeners();

        if (this.voiceType === 'personal') {
            await this.loadPersonalVoices();
        } else {
            await this.loadLanguages();
        }
    }

    /**
     * Configuration des écouteurs d'événements
     */
    setupEventListeners() {
        const localeSelect = document.getElementById('voiceLocaleSelect');
        if (localeSelect) {
            localeSelect.addEventListener('change', (e) => this.onLocaleChange(e.target.value));
        }
    }

    /**
     * Charge les voix personnalisées
     */
    async loadPersonalVoices() {
        try {
            console.log('📥 Chargement des voix personnalisées...');
            const voicesContainer = document.getElementById('voicesContainer');

            if (voicesContainer) {
                voicesContainer.innerHTML = '<div class="loading-spinner">Chargement des voix personnalisées...</div>';
            }

            const response = await fetch('/creer-une-voix/api/personal-voices');
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Erreur lors du chargement des voix personnalisées');
            }

            this.voices = data.voices || [];
            console.log(`✅ ${this.voices.length} voix personnalisées chargées`);

            this.displayPersonalVoices();

        } catch (error) {
            console.error('❌ Erreur chargement voix personnalisées:', error);
            const voicesContainer = document.getElementById('voicesContainer');
            if (voicesContainer) {
                voicesContainer.innerHTML = `
                    <div class="error-message">
                        <i class="bi bi-exclamation-triangle"></i>
                        Erreur lors du chargement des voix personnalisées: ${error.message}
                    </div>
                `;
            }
        }
    }

    /**
     * Affiche les voix personnalisées
     */
    displayPersonalVoices() {
        const voicesContainer = document.getElementById('voicesContainer');
        if (!voicesContainer) return;

        if (this.voices.length === 0) {
            voicesContainer.innerHTML = `
                <div class="no-voices-message">
                    <i class="bi bi-info-circle"></i>
                    <p>Aucune voix personnalisée disponible.</p>
                    <p><a href="/personal-voice">Créer une voix personnalisée</a></p>
                </div>
            `;
            return;
        }

        voicesContainer.innerHTML = '';

        this.voices.forEach(voice => {
            const card = this.createPersonalVoiceCard(voice);
            voicesContainer.appendChild(card);
        });
    }

    /**
     * Crée une carte pour une voix personnalisée
     */
    createPersonalVoiceCard(voice) {
        const card = document.createElement('div');
        card.className = 'voice-card';
        card.dataset.voiceId = voice.voice_id;
        card.dataset.speakerProfileId = voice.speaker_profile_id;
        card.dataset.voiceName = voice.voice_name;

        const genderIcon = voice.gender === 'Female' ? '👩' :
            voice.gender === 'Male' ? '👨' : '🧑';

        const statusBadge = voice.status === 'Succeeded' ?
            '<span class="badge badge-success">✅ Prête</span>' :
            '<span class="badge badge-warning">⏳ En cours</span>';

        card.innerHTML = `
            <div class="voice-card-header">
                <div class="voice-icon">${genderIcon}</div>
                <div class="voice-info">
                    <h4 class="voice-name">${voice.voice_name}</h4>
                    <div class="voice-meta">
                        <span class="voice-locale">${voice.locale || 'fr-FR'}</span>
                        <span class="voice-gender">${voice.gender || 'Unknown'}</span>
                    </div>
                </div>
                ${statusBadge}
            </div>
            ${voice.description ? `<p class="voice-description">${voice.description}</p>` : ''}
            <div class="voice-card-footer">
                <small>Créée le ${new Date(voice.created_at).toLocaleDateString('fr-FR')}</small>
            </div>
        `;

        card.addEventListener('click', () => this.selectPersonalVoice(voice));

        return card;
    }

    /**
     * Sélectionne une voix personnalisée
     */
    selectPersonalVoice(voice) {
        // Retirer la sélection précédente
        document.querySelectorAll('.voice-card').forEach(c => c.classList.remove('selected'));

        // Sélectionner la nouvelle carte
        const card = document.querySelector(`[data-voice-id="${voice.voice_id}"]`);
        if (card) {
            card.classList.add('selected');
        }

        this.selectedVoice = voice;

        // Mettre à jour les champs du formulaire
        const voiceIdField = document.getElementById('voiceId');
        const voiceNameField = document.getElementById('voiceName');
        const voiceLocaleField = document.getElementById('voiceLocale');
        const voiceGenderField = document.getElementById('voiceGender');
        const speakerProfileField = document.getElementById('speakerProfileId');

        if (voiceIdField) voiceIdField.value = voice.voice_id;
        if (voiceNameField) voiceNameField.value = voice.voice_name;
        if (voiceLocaleField) voiceLocaleField.value = voice.locale || 'fr-FR';
        if (voiceGenderField) voiceGenderField.value = voice.gender || '';
        if (speakerProfileField) speakerProfileField.value = voice.speaker_profile_id;

        console.log(`✅ Voix personnalisée sélectionnée: ${voice.voice_name}`);
    }

    /**
     * Charge la liste des langues
     */
    async loadLanguages() {
        try {
            console.log('📥 Chargement des langues...');
            const localeSelect = document.getElementById('voiceLocaleSelect');
            localeSelect.innerHTML = '<option value="">Chargement...</option>';

            const response = await fetch(`${this.apiBaseUrl}/languages`);
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Erreur lors du chargement des langues');
            }

            this.languages = data.languages;
            this.populateLanguageSelect();

            console.log(`✅ ${data.total} langues chargées`);
        } catch (error) {
            console.error('❌ Erreur chargement langues:', error);
            document.getElementById('voiceLocaleSelect').innerHTML =
                '<option value="">Erreur de chargement</option>';
            alert('Erreur lors du chargement des langues. Vérifiez votre configuration Azure.');
        }
    }

    /**
     * Remplit le sélecteur de langues
     */
    populateLanguageSelect() {
        const select = document.getElementById('voiceLocaleSelect');
        select.innerHTML = '<option value="">-- Sélectionnez une langue --</option>';

        // Grouper par région
        const regions = {
            'Français': [],
            'Anglais': [],
            'Espagnol': [],
            'Autres': []
        };

        this.languages.forEach(lang => {
            const locale = lang.locale;
            if (locale.startsWith('fr-')) {
                regions['Français'].push(lang);
            } else if (locale.startsWith('en-')) {
                regions['Anglais'].push(lang);
            } else if (locale.startsWith('es-')) {
                regions['Espagnol'].push(lang);
            } else {
                regions['Autres'].push(lang);
            }
        });

        // Ajouter les options par groupe
        Object.keys(regions).forEach(regionName => {
            if (regions[regionName].length > 0) {
                const optgroup = document.createElement('optgroup');
                optgroup.label = regionName;

                regions[regionName].forEach(lang => {
                    const option = document.createElement('option');
                    option.value = lang.locale;
                    option.textContent = `${this.getFlag(lang.locale)} ${lang.locale_name} (${lang.voice_count} voix)`;
                    optgroup.appendChild(option);
                });

                select.appendChild(optgroup);
            }
        });
    }

    /**
     * Gestion du changement de langue
     */
    async onLocaleChange(locale) {
        if (!locale) {
            this.hideStep('genderStep');
            this.hideStep('voiceStep');
            return;
        }

        this.selectedLocale = locale;
        this.selectedGender = null;
        this.selectedVoice = null;

        // Afficher les infos de la langue
        const langInfo = this.languages.find(l => l.locale === locale);
        if (langInfo) {
            document.getElementById('localeInfo').innerHTML = `
                <i class="bi bi-info-circle"></i>
                ${langInfo.voice_count} voix disponibles 
                (👩 ${langInfo.female_count} • 👨 ${langInfo.male_count})
            `;
        }

        // Charger les genres
        await this.loadGenders(locale);
    }

    /**
     * Charge les genres disponibles pour une langue
     */
    async loadGenders(locale) {
        try {
            console.log(`📥 Chargement des genres pour ${locale}...`);

            const response = await fetch(`${this.apiBaseUrl}/genders-by-locale?locale=${locale}`);
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Erreur lors du chargement des genres');
            }

            this.populateGenderButtons(data.genders);
            this.showStep('genderStep');
            this.hideStep('voiceStep');

            console.log(`✅ ${data.genders.length} genres disponibles`);
        } catch (error) {
            console.error('❌ Erreur chargement genres:', error);
            alert('Erreur lors du chargement des genres.');
        }
    }

    /**
     * Remplit les boutons de genre
     */
    populateGenderButtons(genders) {
        const container = document.getElementById('genderButtons');
        container.innerHTML = '';

        genders.forEach(gender => {
            const button = document.createElement('div');
            button.className = 'gender-button';
            button.dataset.gender = gender.gender;

            button.innerHTML = `
                <div class="gender-button-emoji">${gender.emoji}</div>
                <div class="gender-button-text">${this.translateGender(gender.gender)}</div>
                <div class="gender-button-count">${gender.count} voix</div>
            `;

            button.addEventListener('click', () => this.onGenderSelect(gender.gender));
            container.appendChild(button);
        });
    }

    /**
     * Gestion de la sélection de genre
     */
    async onGenderSelect(gender) {
        // Désélectionner les autres boutons
        document.querySelectorAll('.gender-button').forEach(btn => {
            btn.classList.remove('selected');
        });

        // Sélectionner ce bouton
        event.currentTarget.classList.add('selected');

        this.selectedGender = gender;

        // Charger les voix
        await this.loadVoices(this.selectedLocale, gender);
    }

    /**
     * Charge les voix par langue et genre
     */
    async loadVoices(locale, gender) {
        try {
            console.log(`📥 Chargement des voix ${gender} pour ${locale}...`);

            const container = document.getElementById('voicesGrid');
            container.innerHTML = `
                <div class="loading-spinner">
                    <i class="bi bi-arrow-repeat"></i>
                    Chargement des voix...
                </div>
            `;
            this.showStep('voiceStep');

            const response = await fetch(`${this.apiBaseUrl}/voices-by-locale?locale=${locale}&gender=${gender}`);
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Erreur lors du chargement des voix');
            }

            this.voices = data.voices;
            this.populateVoicesGrid(data.voices);

            console.log(`✅ ${data.total} voix chargées`);
        } catch (error) {
            console.error('❌ Erreur chargement voix:', error);
            document.getElementById('voicesGrid').innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-exclamation-circle"></i>
                    <p>Erreur lors du chargement des voix</p>
                </div>
            `;
        }
    }

    /**
     * Remplit la grille de voix
     */
    populateVoicesGrid(voices) {
        const grid = document.getElementById('voicesGrid');

        if (voices.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-mic-mute"></i>
                    <p>Aucune voix trouvée</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = '';

        voices.forEach(voice => {
            const card = this.createVoiceCard(voice);
            grid.appendChild(card);
        });
    }

    /**
     * Crée une carte de voix
     */
    createVoiceCard(voice) {
        const card = document.createElement('div');
        card.className = 'voice-card';
        card.dataset.voiceName = voice.name;

        // Badge type (HD, Standard, etc.)
        const isHD = voice.name.includes('HD') || voice.name.includes('Dragon');
        const badgeText = isHD ? 'HD' : (voice.voice_type || 'Standard');

        // Styles disponibles
        const stylesHTML = voice.styles && voice.styles.length > 0 ? `
            <div class="voice-card-styles">
                <div class="voice-card-styles-title">
                    <i class="bi bi-palette"></i> Styles disponibles
                </div>
                <div class="voice-styles-tags">
                    ${voice.styles.map(style => `
                        <span class="voice-style-tag">${style}</span>
                    `).join('')}
                </div>
            </div>
        ` : '';

        card.innerHTML = `
            <div class="voice-card-header">
                <div class="voice-card-icon">
                    ${voice.gender === 'Female' ? '👩' : (voice.gender === 'Male' ? '👨' : '⚪')}
                </div>
                <div class="voice-card-title">
                    <div class="voice-card-name">${voice.display_name || voice.short_name}</div>
                    <div class="voice-card-local">${voice.local_name}</div>
                </div>
                <span class="voice-card-badge">${badgeText}</span>
            </div>
            
            <div class="voice-card-details">
                <div class="voice-card-detail">
                    <i class="bi bi-soundwave"></i>
                    <span>${voice.sample_rate_hertz / 1000}kHz</span>
                </div>
                <div class="voice-card-detail">
                    <i class="bi bi-code"></i>
                    <span>${voice.short_name}</span>
                </div>
            </div>
            
            ${stylesHTML}
        `;

        card.addEventListener('click', () => this.onVoiceSelect(voice, card));

        return card;
    }

    /**
     * Gestion de la sélection de voix
     */
    onVoiceSelect(voice, cardElement) {
        // Désélectionner les autres cartes
        document.querySelectorAll('.voice-card').forEach(card => {
            card.classList.remove('selected');
        });

        // Sélectionner cette carte
        cardElement.classList.add('selected');

        this.selectedVoice = voice;

        // Mettre à jour les champs cachés
        document.getElementById('voiceName').value = voice.name;
        document.getElementById('voiceLocale').value = voice.locale;
        document.getElementById('voiceGender').value = voice.gender;

        console.log('✅ Voix sélectionnée:', voice.name);

        // Scroll vers le bas pour voir la suite
        setTimeout(() => {
            document.getElementById('voiceStep').scrollIntoView({ behavior: 'smooth', block: 'end' });
        }, 300);
    }

    /**
     * Affiche une étape
     */
    showStep(stepId) {
        const step = document.getElementById(stepId);
        if (step) {
            step.style.display = 'block';
            setTimeout(() => step.classList.add('active'), 100);
        }
    }

    /**
     * Masque une étape
     */
    hideStep(stepId) {
        const step = document.getElementById(stepId);
        if (step) {
            step.classList.remove('active');
            step.style.display = 'none';
        }
    }

    /**
     * Obtient le drapeau emoji pour un locale
     */
    getFlag(locale) {
        const flags = {
            'fr': '🇫🇷', 'en': '🇺🇸', 'es': '🇪🇸', 'de': '🇩🇪',
            'it': '🇮🇹', 'pt': '🇵🇹', 'ja': '🇯🇵', 'zh': '🇨🇳',
            'ko': '🇰🇷', 'ar': '🇸🇦', 'ru': '🇷🇺', 'hi': '🇮🇳',
            'nl': '🇳🇱', 'sv': '🇸🇪', 'pl': '🇵🇱', 'tr': '🇹🇷'
        };

        const langCode = locale.split('-')[0];
        return flags[langCode] || '🌍';
    }

    /**
     * Traduit le genre en français
     */
    translateGender(gender) {
        const translations = {
            'Female': 'Féminin',
            'Male': 'Masculin',
            'Neutral': 'Neutre',
            'Unknown': 'Autre'
        };
        return translations[gender] || gender;
    }
}

// Initialisation globale
let azureVoiceSelector;

document.addEventListener('DOMContentLoaded', function () {
    // Vérifier si nous sommes sur la page de configuration de voix
    if (document.getElementById('voiceLocaleSelect')) {
        azureVoiceSelector = new AzureVoiceSelector();
    }
});

// Export pour usage externe
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AzureVoiceSelector;
}
