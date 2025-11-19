/**
 * Background Upload & Gallery Manager
 * Gère l'upload et la sélection d'images de fond pour avatars
 */

class BackgroundManager {
    constructor() {
        this.galleryVisible = false;
        this.backgrounds = [];
        this.init();
    }

    init() {
        // Toggle gallery button
        const toggleBtn = document.getElementById('toggleBackgroundGallery');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleGallery());
        }

        // Upload button
        const uploadBtn = document.getElementById('uploadBackgroundBtn');
        if (uploadBtn) {
            uploadBtn.addEventListener('click', () => this.triggerUpload());
        }

        // File input
        const fileInput = document.getElementById('backgroundFileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }

        // Background image input change
        const bgInput = document.getElementById('avatarBackgroundImage');
        if (bgInput) {
            bgInput.addEventListener('change', () => this.updatePreview());
        }
    }

    async toggleGallery() {
        this.galleryVisible = !this.galleryVisible;
        const gallery = document.getElementById('backgroundGallery');

        if (this.galleryVisible) {
            gallery.style.display = 'block';
            await this.loadBackgrounds();
        } else {
            gallery.style.display = 'none';
        }
    }

    async loadBackgrounds() {
        const loading = document.getElementById('backgroundGalleryLoading');
        const grid = document.getElementById('backgroundGalleryGrid');
        const empty = document.getElementById('backgroundGalleryEmpty');

        loading.style.display = 'block';
        grid.style.display = 'none';
        empty.style.display = 'none';

        try {
            const response = await fetch('/background/api/list');
            const data = await response.json();

            loading.style.display = 'none';

            if (data.success && data.backgrounds && data.backgrounds.length > 0) {
                this.backgrounds = data.backgrounds;
                this.renderGallery();
                grid.style.display = 'flex';
            } else {
                empty.style.display = 'block';
            }
        } catch (error) {
            console.error('❌ Erreur chargement galerie:', error);
            loading.style.display = 'none';
            empty.style.display = 'block';
            empty.className = 'alert alert-danger';
            empty.innerHTML = '<i class="bi bi-exclamation-triangle"></i> Erreur de chargement';
        }
    }

    renderGallery() {
        const grid = document.getElementById('backgroundGalleryGrid');
        grid.innerHTML = '';

        this.backgrounds.forEach(bg => {
            const col = document.createElement('div');
            col.className = 'col-6 col-md-4 col-lg-3';

            const card = document.createElement('div');
            card.className = 'background-gallery-item';
            card.style.cssText = `
                cursor: pointer;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 8px;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            `;

            const img = document.createElement('img');
            img.src = bg.url;
            img.alt = bg.filename;
            img.style.cssText = `
                width: 100%;
                height: 120px;
                object-fit: cover;
                border-radius: 6px;
            `;

            const filename = document.createElement('p');
            filename.className = 'text-muted small mt-2 mb-0 text-truncate';
            filename.textContent = bg.filename;

            card.appendChild(img);
            card.appendChild(filename);

            // Click to select
            card.addEventListener('click', () => this.selectBackground(bg.url));

            // Hover effect
            card.addEventListener('mouseenter', () => {
                card.style.borderColor = '#4a148c';
                card.style.transform = 'scale(1.05)';
            });

            card.addEventListener('mouseleave', () => {
                card.style.borderColor = '#dee2e6';
                card.style.transform = 'scale(1)';
            });

            col.appendChild(card);
            grid.appendChild(col);
        });
    }

    selectBackground(url) {
        const input = document.getElementById('avatarBackgroundImage');
        if (input) {
            input.value = url;
            this.updatePreview();

            // Fermer la galerie
            this.galleryVisible = false;
            document.getElementById('backgroundGallery').style.display = 'none';

            console.log('✅ Image de fond sélectionnée:', url);
        }
    }

    updatePreview() {
        const input = document.getElementById('avatarBackgroundImage');
        const preview = document.getElementById('backgroundPreview');
        const previewImg = document.getElementById('backgroundPreviewImg');

        if (input && input.value) {
            previewImg.src = input.value;
            preview.style.display = 'block';
        } else {
            preview.style.display = 'none';
        }
    }

    triggerUpload() {
        const fileInput = document.getElementById('backgroundFileInput');
        if (fileInput) {
            fileInput.click();
        }
    }

    async handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Vérifier le type de fichier
        const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            alert('❌ Type de fichier non autorisé. Utilisez PNG, JPEG, GIF ou WebP.');
            return;
        }

        // Vérifier la taille (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            alert('❌ Fichier trop volumineux. Taille maximale: 10 MB');
            return;
        }

        // Afficher un loader
        const uploadBtn = document.getElementById('uploadBackgroundBtn');
        const originalText = uploadBtn.innerHTML;
        uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Upload...';
        uploadBtn.disabled = true;

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/background/api/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                console.log('✅ Image uploadée:', data.url);

                // Sélectionner automatiquement l'image uploadée
                this.selectBackground(data.url);

                // Recharger la galerie si visible
                if (this.galleryVisible) {
                    await this.loadBackgrounds();
                }

                alert('✅ Image uploadée avec succès !');
            } else {
                throw new Error(data.error || 'Erreur inconnue');
            }
        } catch (error) {
            console.error('❌ Erreur upload:', error);
            alert('❌ Erreur lors de l\'upload: ' + error.message);
        } finally {
            uploadBtn.innerHTML = originalText;
            uploadBtn.disabled = false;
            event.target.value = ''; // Reset file input
        }
    }
}

// Initialiser au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    window.backgroundManager = new BackgroundManager();
});
