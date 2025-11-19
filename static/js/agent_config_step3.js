/**
 * Agent Configuration Step 3 - Tools Selection
 * JavaScript pour la gestion de la sélection des tools
 */

// Toggle tool selection
function toggleTool(card, toolValue) {
    const checkbox = card.querySelector('input[type="checkbox"]');
    checkbox.checked = !checkbox.checked;

    if (checkbox.checked) {
        card.classList.add('selected');
    } else {
        card.classList.remove('selected');
    }

    updateCounter();
}

// Update selection counter
function updateCounter() {
    const checkedBoxes = document.querySelectorAll('input[name="tools"]:checked');
    const count = checkedBoxes.length;
    document.getElementById('selectedCount').textContent = count;
}

// Select all tools
function selectAll() {
    const allCards = document.querySelectorAll('.tool-card');
    allCards.forEach(card => {
        const checkbox = card.querySelector('input[type="checkbox"]');
        checkbox.checked = true;
        card.classList.add('selected');
    });
    updateCounter();
}

// Deselect all tools
function deselectAll() {
    const allCards = document.querySelectorAll('.tool-card');
    allCards.forEach(card => {
        const checkbox = card.querySelector('input[type="checkbox"]');
        checkbox.checked = false;
        card.classList.remove('selected');
    });
    updateCounter();
}

// Select recommended tools
function selectRecommended() {
    deselectAll();
    const recommendedTools = [
        'search_web',
        'weather',
        'flight_search',
        'hotel_search',
        'email',
        'knowledge_base'
    ];

    recommendedTools.forEach(toolValue => {
        const checkbox = document.querySelector(`input[value="${toolValue}"]`);
        if (checkbox) {
            checkbox.checked = true;
            checkbox.closest('.tool-card').classList.add('selected');
        }
    });

    updateCounter();
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function () {

    // Prevent checkbox click from triggering card click
    document.querySelectorAll('.tool-checkbox').forEach(checkbox => {
        checkbox.addEventListener('click', function (e) {
            e.stopPropagation();
            const card = this.closest('.tool-card');
            if (this.checked) {
                card.classList.add('selected');
            } else {
                card.classList.remove('selected');
            }
            updateCounter();
        });
    });

    // Form submission handler
    document.getElementById('toolsForm').addEventListener('submit', function (e) {
        const checkedBoxes = document.querySelectorAll('input[name="tools"]:checked');

        // Validation: au moins un tool doit être sélectionné
        if (checkedBoxes.length === 0) {
            e.preventDefault();
            alert('⚠️ Veuillez sélectionner au moins un tool pour continuer.');
            return;
        }

        // Collecter les tools sélectionnés
        const selectedTools = Array.from(checkedBoxes).map(cb => cb.value);

        // Log pour debug
        console.log('🛠️ Tools sélectionnés:', selectedTools);
        console.log('📊 Nombre total:', selectedTools.length);

        // Stocker dans sessionStorage (optionnel)
        sessionStorage.setItem('selectedTools', JSON.stringify(selectedTools));

        // Laisser le formulaire se soumettre normalement vers /agents/config/step4
        // Le backend redirigera automatiquement vers Step 5
    });

    // Initialiser le compteur au chargement
    updateCounter();

    // Log de chargement
    console.log('✅ Agent Config Step 3 - JavaScript chargé');
});
