// Configuration des familles de modèles avec descriptions ET pricing
const modelFamilies = {
    'realtime': [
        {
            id: 'gpt-realtime',
            name: 'GPT Realtime',
            description: 'GPT real-time + option to use Azure text to speech voices including custom voice for audio.',
            color: 'danger',
            family: 'F1_Realtime',
            pricing: 'pro'
        },
        {
            id: 'gpt-realtime-mini',
            name: 'GPT Realtime Mini',
            description: 'GPT mini real-time + option to use Azure text to speech voices including custom voice for audio.',
            color: 'danger',
            family: 'F1_Realtime',
            pricing: 'basic'
        },
        {
            id: 'gpt-4o-mini-realtime',
            name: 'GPT-4o Mini Realtime',
            description: 'GPT-4o mini real-time + option to use Azure text to speech voices including custom voice for audio.',
            color: 'danger',
            family: 'F1_Realtime',
            pricing: 'basic'
        },
        {
            id: 'phi4-mm-realtime',
            name: 'Phi4-MM Realtime',
            description: 'Phi4-mm + audio output through Azure text to speech voices including custom voice.',
            color: 'danger',
            family: 'F1_Realtime',
            pricing: 'lite'
        }
    ],
    'gpt4o-family': [
        {
            id: 'gpt-4o',
            name: 'GPT-4o',
            description: 'GPT-4o + audio input through Azure speech to text + audio output through Azure text to speech voices including custom voice.',
            color: 'warning',
            family: 'F2_GPT4o',
            pricing: 'pro'
        },
        {
            id: 'gpt-4o-mini',
            name: 'GPT-4o Mini',
            description: 'GPT-4o mini + audio input through Azure speech to text + audio output through Azure text to speech voices including custom voice.',
            color: 'warning',
            family: 'F2_GPT4o',
            pricing: 'basic'
        },
        {
            id: 'gpt-4.1',
            name: 'GPT-4.1',
            description: 'GPT-4.1 + audio input through Azure speech to text + audio output through Azure text to speech voices including custom voice.',
            color: 'warning',
            family: 'F2_GPT4o',
            pricing: 'pro'
        },
        {
            id: 'gpt-4.1-mini',
            name: 'GPT-4.1 Mini',
            description: 'GPT-4.1 mini + audio input through Azure speech to text + audio output through Azure text to speech voices including custom voice.',
            color: 'warning',
            family: 'F2_GPT4o',
            pricing: 'basic'
        },
        {
            id: 'phi4-mini',
            name: 'Phi4 Mini',
            description: 'Phi4-mm + audio input through Azure speech to text + audio output through Azure text to speech voices including custom voice.',
            color: 'warning',
            family: 'F2_GPT4o',
            pricing: 'lite'
        }
    ],
    'gpt5-family': [
        {
            id: 'gpt-5',
            name: 'GPT-5',
            description: 'GPT-5 + audio input through Azure speech to text + audio output through Azure text to speech voices including custom voice.',
            color: 'success',
            family: 'F3_GPT5',
            pricing: 'pro'
        },
        {
            id: 'gpt-5-mini',
            name: 'GPT-5 Mini',
            description: 'GPT-5 mini + audio input through Azure speech to text + audio output through Azure text to speech voices including custom voice.',
            color: 'success',
            family: 'F3_GPT5',
            pricing: 'basic'
        },
        {
            id: 'gpt-5-nano',
            name: 'GPT-5 Nano',
            description: 'GPT-5 nano + audio input through Azure speech to text + audio output through Azure text to speech voices including custom voice.',
            color: 'success',
            family: 'F3_GPT5',
            pricing: 'lite'
        },
        {
            id: 'gpt-5-chat',
            name: 'GPT-5 Chat',
            description: 'GPT-5 chat + audio input through Azure speech to text + audio output through Azure text to speech voices including custom voice.',
            color: 'success',
            family: 'F3_GPT5',
            pricing: 'pro'
        }
    ]
};

// Configuration des catégories de pricing
const pricingConfig = {
    'pro': {
        label: 'Voice Live Pro',
        color: '#7B1FA2',
        bgColor: '#F3E5F5',
        icon: '💎'
    },
    'basic': {
        label: 'Voice Live Basic',
        color: '#1976D2',
        bgColor: '#E3F2FD',
        icon: '⭐'
    },
    'lite': {
        label: 'Voice Live Lite',
        color: '#388E3C',
        bgColor: '#E8F5E9',
        icon: '🌟'
    }
};

// Variable globale pour stocker la famille sélectionnée
let currentFamily = null;

/**
 * Affiche la liste des modèles pour une famille donnée
 */
function showModels(familyType) {
    currentFamily = familyType;
    const models = modelFamilies[familyType];
    
    if (!models || models.length === 0) {
        console.error('Aucun modèle trouvé pour la famille:', familyType);
        return;
    }

    const modelsList = document.getElementById('modelsList');
    const modelsSection = document.getElementById('modelsSection');
    
    // Effacer la liste actuelle
    modelsList.innerHTML = '';
    
    // Créer les éléments de liste pour chaque modèle
    models.forEach((model, index) => {
        const modelItem = createModelItem(model, index);
        modelsList.appendChild(modelItem);
    });
    
    // Afficher la section avec animation
    modelsSection.style.display = 'block';
    
    // Smooth scroll vers la section
    setTimeout(() => {
        modelsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

/**
 * Crée un élément HTML pour un modèle
 */
function createModelItem(model, index) {
    const div = document.createElement('div');
    div.className = 'agent-model-item';
    div.style.opacity = '0';
    div.style.transform = 'translateY(20px)';
    
    // Animation d'apparition décalée
    setTimeout(() => {
        div.style.transition = 'all 0.4s ease';
        div.style.opacity = '1';
        div.style.transform = 'translateY(0)';
    }, index * 100);
    
    // Icône selon la couleur du modèle
    const iconMap = {
        'danger': 'bi-lightning-charge-fill',
        'warning': 'bi-cpu-fill',
        'success': 'bi-stars'
    };
    
    const icon = iconMap[model.color] || 'bi-robot';
    
    // Configuration du pricing
    const pricing = pricingConfig[model.pricing] || pricingConfig['basic'];
    
    div.innerHTML = `
        <div class="agent-model-header">
            <div class="d-flex align-items-center gap-3">
                <div style="
                    width: 48px;
                    height: 48px;
                    border-radius: 12px;
                    background: ${getGradientForColor(model.color)};
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 4px 12px ${getBoxShadowForColor(model.color)};
                ">
                    <i class="bi ${icon} text-white" style="font-size: 24px;"></i>
                </div>
                <div style="flex: 1;">
                    <div class="agent-model-name">${model.name}</div>
                    <div class="d-flex gap-2 mt-1">
                        <span class="badge bg-${model.color} text-${model.color === 'warning' ? 'dark' : 'white'}">
                            ${model.id}
                        </span>
                        <span class="badge" style="
                            background-color: ${pricing.bgColor};
                            color: ${pricing.color};
                            font-weight: 600;
                            border: 1px solid ${pricing.color}40;
                        ">
                            ${pricing.icon} ${pricing.label}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        <div class="agent-model-description">
            ${model.description}
        </div>
    `;
    
    // Gestion du clic
    div.addEventListener('click', () => selectModel(model));
    
    return div;
}

/**
 * Retourne le gradient approprié selon la couleur
 */
function getGradientForColor(color) {
    const gradients = {
        'danger': 'linear-gradient(135deg, #dc3545, #c82333)',
        'warning': 'linear-gradient(135deg, #FF6F00, #FFC107)',
        'success': 'linear-gradient(135deg, #28a745, #20c997)'
    };
    return gradients[color] || 'linear-gradient(135deg, #4A148C, #7B1FA2)';
}

/**
 * Retourne l'ombre appropriée selon la couleur
 */
function getBoxShadowForColor(color) {
    const shadows = {
        'danger': 'rgba(220, 53, 69, 0.3)',
        'warning': 'rgba(255, 111, 0, 0.3)',
        'success': 'rgba(40, 167, 69, 0.3)'
    };
    return shadows[color] || 'rgba(74, 20, 140, 0.3)';
}

/**
 * Sélectionne un modèle et redirige vers Step 2
 */
function selectModel(model) {
    console.log('🎯 Modèle sélectionné:', model);
    
    // Remplir les champs cachés du formulaire
    document.getElementById('configType').value = currentFamily;
    document.getElementById('modelId').value = model.id;
    document.getElementById('modelName').value = model.name;
    document.getElementById('modelDescription').value = model.description;
    document.getElementById('modelFamily').value = model.family;
    
    // Animation de confirmation avec bordure accentuée
    const modelItem = event.currentTarget;
    modelItem.style.transform = 'scale(1.02)';
    modelItem.style.borderLeftWidth = '8px';
    modelItem.style.borderLeftColor = getBorderColorForFamily(model.color);
    modelItem.style.boxShadow = `0 12px 32px ${getBoxShadowForColor(model.color)}`;
    
    // Afficher un feedback visuel
    const pricing = pricingConfig[model.pricing] || pricingConfig['basic'];
    console.log(`✅ Configuration: ${pricing.label} (${model.family})`);
    
    setTimeout(() => {
        // Soumettre le formulaire vers Step 2
        document.getElementById('configForm').submit();
    }, 400);
}

/**
 * Retourne la couleur de bordure appropriée selon la famille
 */
function getBorderColorForFamily(color) {
    const borderColors = {
        'danger': '#dc3545',
        'warning': '#FF6F00',
        'success': '#28a745'
    };
    return borderColors[color] || '#4A148C';
}

/**
 * Cache la section des modèles et retourne à la sélection des familles
 */
function hideModels() {
    const modelsSection = document.getElementById('modelsSection');
    
    // Animation de sortie
    modelsSection.style.opacity = '1';
    modelsSection.style.transition = 'opacity 0.3s ease';
    modelsSection.style.opacity = '0';
    
    setTimeout(() => {
        modelsSection.style.display = 'none';
        modelsSection.style.opacity = '1';
        
        // Smooth scroll vers le haut
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }, 300);
    
    currentFamily = null;
}

/**
 * Initialisation au chargement de la page
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Agent Config Step 1 - JavaScript chargé');
    console.log('Familles de modèles disponibles:', Object.keys(modelFamilies));
    
    // Gestion du clic sur les cartes de famille (en plus de l'attribut onclick)
    document.querySelectorAll('.agent-family-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.cursor = 'pointer';
        });
    });
    
    // Gestion du bouton retour avec la touche ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && currentFamily) {
            hideModels();
        }
    });
});
