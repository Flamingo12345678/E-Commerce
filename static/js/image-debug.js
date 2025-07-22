/**
 * Script de debug pour les images sur mobile
 * Aide à diagnostiquer les problèmes d'affichage des images
 */

// Fonction de debug des images
function debugImages() {
    console.log('=== DEBUG IMAGES ===');
    
    const productImages = document.querySelectorAll('.product-image img');
    console.log(`Nombre d'images trouvées: ${productImages.length}`);
    
    productImages.forEach((img, index) => {
        console.log(`Image ${index + 1}:`, {
            src: img.src,
            naturalWidth: img.naturalWidth,
            naturalHeight: img.naturalHeight,
            displayWidth: img.offsetWidth,
            displayHeight: img.offsetHeight,
            complete: img.complete,
            loading: img.loading,
            style: {
                display: getComputedStyle(img).display,
                visibility: getComputedStyle(img).visibility,
                opacity: getComputedStyle(img).opacity
            }
        });
        
        // Test de chargement
        if (!img.complete) {
            console.warn(`Image ${index + 1} n'est pas complètement chargée`);
        }
        
        if (img.naturalWidth === 0) {
            console.error(`Image ${index + 1} a échoué à charger`);
        }
    });
    
    // Vérifier les placeholders
    const placeholders = document.querySelectorAll('.image-placeholder');
    console.log(`Nombre de placeholders: ${placeholders.length}`);
    
    placeholders.forEach((placeholder, index) => {
        const isVisible = getComputedStyle(placeholder).display !== 'none';
        console.log(`Placeholder ${index + 1} visible:`, isVisible);
    });
}

// Fonction pour forcer l'affichage des images
function forceImageDisplay() {
    const productImages = document.querySelectorAll('.product-image img');
    
    productImages.forEach(img => {
        img.style.display = 'block';
        img.style.width = '100%';
        img.style.height = '100%';
        img.style.objectFit = 'cover';
        img.style.visibility = 'visible';
        img.style.opacity = '1';
    });
    
    console.log('Images forcées à s\'afficher');
}

// Fonction pour recharger les images défaillantes
function reloadFailedImages() {
    const productImages = document.querySelectorAll('.product-image img');
    
    productImages.forEach(img => {
        if (img.naturalWidth === 0 && img.src) {
            console.log('Rechargement de l\'image:', img.src);
            const newSrc = img.src;
            img.src = '';
            setTimeout(() => {
                img.src = newSrc;
            }, 100);
        }
    });
}

// Fonction pour optimiser le lazy loading sur mobile
function optimizeLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src && !img.src) {
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    console.log('=== INITIALISATION DEBUG IMAGES ===');
    
    // Debug initial
    setTimeout(debugImages, 1000);
    
    // Optimisation du lazy loading
    optimizeLazyLoading();
    
    // Force l'affichage des images après un délai
    setTimeout(forceImageDisplay, 2000);
    
    // Expose les fonctions globalement pour debug manuel
    window.debugImages = debugImages;
    window.forceImageDisplay = forceImageDisplay;
    window.reloadFailedImages = reloadFailedImages;
    
    console.log('Fonctions disponibles: debugImages(), forceImageDisplay(), reloadFailedImages()');
});

// Écouter les erreurs de chargement d'images
document.addEventListener('error', function(e) {
    if (e.target.tagName === 'IMG') {
        console.error('Erreur de chargement d\'image:', e.target.src);
        
        // Essayer de recharger l'image une fois
        if (!e.target.dataset.retried) {
            e.target.dataset.retried = 'true';
            setTimeout(() => {
                const newSrc = e.target.src;
                e.target.src = '';
                e.target.src = newSrc;
            }, 1000);
        }
    }
}, true);
