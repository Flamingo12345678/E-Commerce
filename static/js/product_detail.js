/**
 * Product Detail Page - JavaScript functionality
 * Gestion de la page de détail produit avec sélection de taille, quantité, wishlist, etc.
 */

let selectedSize = null;

// Configuration globale récupérée depuis le template
let productConfig = window.productConfig || {
    totalStock: 0,
    price: 0,
    hasVariants: false,
    productId: null,
    urls: {
        checkWishlistStatus: '',
        addToWishlist: '',
        removeFromWishlist: ''
    }
};

/**
 * Fonction globale pour gérer la sélection de taille
 */
function handleSizeSelection(button) {
    // Remove active class from all size options
    document.querySelectorAll('.size-option').forEach(btn => {
        btn.classList.remove('active');
        btn.style.backgroundColor = '';
        btn.style.color = '';
        btn.style.borderColor = '';
    });

    // Add active class to clicked option
    button.classList.add('active');
    button.style.backgroundColor = '#000000';
    button.style.color = '#ffffff';
    button.style.borderColor = '#000000';

    selectedSize = button.dataset.size;

    const selectedSizeInput = document.getElementById('selectedSize');
    const maxStock = parseInt(button.dataset.stock);

    // Update hidden form field
    if (selectedSizeInput) {
        selectedSizeInput.value = selectedSize;
    }

    // Enable add to cart button
    const addToCartBtn = document.querySelector('.add-to-cart');
    if (addToCartBtn) {
        addToCartBtn.disabled = false;
        addToCartBtn.style.opacity = '1';
        addToCartBtn.style.cursor = 'pointer';
    }

    // Update stock info
    const stockInfo = document.getElementById('sizeStockInfo');
    if (stockInfo) {
        if (maxStock > 10) {
            stockInfo.innerHTML = `<span class="stock-available">En stock (${maxStock} disponibles)</span>`;
        } else if (maxStock > 0) {
            stockInfo.innerHTML = `<span class="stock-low">Stock limité (${maxStock} restants)</span>`;
        }
    }

    // Update quantity max
    const quantityInput = document.querySelector('.quantity-input');
    if (quantityInput) {
        quantityInput.max = maxStock;
        if (parseInt(quantityInput.value) > maxStock) {
            quantityInput.value = maxStock;
        }

        const selectedQuantityInput = document.getElementById('selectedQuantity');
        if (selectedQuantityInput) {
            selectedQuantityInput.value = quantityInput.value;
        }
    }

    updateCartButton();
}

/**
 * Met à jour le bouton d'ajout au panier
 */
function updateCartButton() {
    const addToCartBtn = document.querySelector('.add-to-cart');
    const quantityInput = document.querySelector('.quantity-input');
    const sizeOptions = document.querySelectorAll('.size-option:not(.unavailable)');
    
    if (!addToCartBtn || !quantityInput) return;
    
    const quantity = parseInt(quantityInput.value);
    const price = productConfig.price;
    const total = (price * quantity).toFixed(2);
    
    // Si le produit n'a pas de variantes de taille, toujours afficher le bouton
    if (sizeOptions.length === 0) {
        addToCartBtn.innerHTML = `<i class="bi bi-cart-plus me-2"></i>ajouter au panier - €${total}`;
        addToCartBtn.disabled = false;
        addToCartBtn.style.opacity = '1';
        addToCartBtn.style.cursor = 'pointer';
        addToCartBtn.style.display = 'block';
        addToCartBtn.style.visibility = 'visible';
    } else if (selectedSize) {
        // Taille sélectionnée
        addToCartBtn.innerHTML = `<i class="bi bi-cart-plus me-2"></i>ajouter au panier - €${total}`;
        addToCartBtn.disabled = false;
        addToCartBtn.style.opacity = '1';
        addToCartBtn.style.cursor = 'pointer';
        addToCartBtn.style.display = 'block';
        addToCartBtn.style.visibility = 'visible';
    } else {
        // Variantes disponibles mais aucune taille sélectionnée
        addToCartBtn.innerHTML = '<i class="bi bi-cart-plus me-2"></i>sélectionnez une taille';
        addToCartBtn.disabled = true;
        addToCartBtn.style.opacity = '0.6';
        addToCartBtn.style.cursor = 'not-allowed';
        addToCartBtn.style.display = 'block';
        addToCartBtn.style.visibility = 'visible';
    }
}

/**
 * Initialise les contrôles de quantité
 */
function initQuantityControls() {
    const quantityInput = document.querySelector('.quantity-input');
    const minusBtn = document.querySelector('.quantity-btn.minus');
    const plusBtn = document.querySelector('.quantity-btn.plus');

    if (minusBtn) {
        minusBtn.addEventListener('click', function() {
            const currentValue = parseInt(quantityInput.value);
            if (currentValue > 1) {
                quantityInput.value = currentValue - 1;
                
                // Update hidden quantity field
                const selectedQuantityInput = document.getElementById('selectedQuantity');
                if (selectedQuantityInput) {
                    selectedQuantityInput.value = quantityInput.value;
                }
                
                updateCartButton();
            }
        });
    }

    if (plusBtn) {
        plusBtn.addEventListener('click', function() {
            const currentValue = parseInt(quantityInput.value);
            const maxStock = getMaxStock();
            
            if (currentValue < maxStock) {
                quantityInput.value = currentValue + 1;
                
                // Update hidden quantity field
                const selectedQuantityInput = document.getElementById('selectedQuantity');
                if (selectedQuantityInput) {
                    selectedQuantityInput.value = quantityInput.value;
                }
                
                updateCartButton();
            }
        });
    }

    if (quantityInput) {
        quantityInput.addEventListener('change', function() {
            const value = parseInt(this.value);
            const maxStock = getMaxStock();
            
            if (value < 1) {
                this.value = 1;
            } else if (value > maxStock) {
                this.value = maxStock;
            }
            
            // Update hidden quantity field
            const selectedQuantityInput = document.getElementById('selectedQuantity');
            if (selectedQuantityInput) {
                selectedQuantityInput.value = this.value;
            }
            
            updateCartButton();
        });
    }
}

/**
 * Récupère le stock maximum selon la taille sélectionnée
 */
function getMaxStock() {
    const quantityInput = document.querySelector('.quantity-input');
    if (quantityInput && quantityInput.max) {
        return parseInt(quantityInput.max);
    }
    return productConfig.totalStock;
}

/**
 * Initialise la galerie d'images
 */
function initImageGallery() {
    const thumbnails = document.querySelectorAll('.thumbnail');
    const mainImage = document.querySelector('.main-product-image');
    
    thumbnails.forEach(thumb => {
        thumb.addEventListener('click', function() {
            thumbnails.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            const img = this.querySelector('img');
            if (img && mainImage) {
                mainImage.src = img.src;
            }
        });
    });
}

/**
 * Ajoute un produit à la wishlist
 */
function addToWishlist(productId) {
    const form = new FormData();
    form.append('product_id', productId);
    form.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
    
    fetch(productConfig.urls.addToWishlist, {
        method: 'POST',
        body: form,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateWishlistButton(true);
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showToast('Erreur lors de l\'ajout à la liste de souhaits', 'error');
    });
}

/**
 * Retire un produit de la wishlist
 */
function removeFromWishlist(productId) {
    const form = new FormData();
    form.append('product_id', productId);
    form.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
    
    fetch(productConfig.urls.removeFromWishlist, {
        method: 'POST',
        body: form,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateWishlistButton(false);
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        showToast('Erreur lors de la suppression de la liste de souhaits', 'error');
    });
}

/**
 * Met à jour l'état du bouton wishlist
 */
function updateWishlistButton(inWishlist) {
    const wishlistBtn = document.querySelector('.wishlist-btn');
    if (!wishlistBtn) return;
    
    const icon = wishlistBtn.querySelector('i');
    if (inWishlist) {
        icon.className = 'fas fa-heart';
        wishlistBtn.classList.remove('btn-outline-danger');
        wishlistBtn.classList.add('btn-danger');
        wishlistBtn.title = 'Retirer de la liste de souhaits';
    } else {
        icon.className = 'far fa-heart';
        wishlistBtn.classList.remove('btn-danger');
        wishlistBtn.classList.add('btn-outline-danger');
        wishlistBtn.title = 'Ajouter à la liste de souhaits';
    }
}

/**
 * Affiche un toast de notification
 */
function showToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
}

/**
 * Initialise la fonctionnalité wishlist
 */
function initWishlistFunctionality() {
    const wishlistBtn = document.querySelector('.action-button.secondary[data-product-id]');

    if (!wishlistBtn) return;

    const productId = wishlistBtn.getAttribute('data-product-id');

    // Vérifier le statut initial de la wishlist
    checkWishlistStatus(productId);

    // Ajouter l'événement de clic
    wishlistBtn.addEventListener('click', function(e) {
        e.preventDefault();
        toggleWishlist(productId, this);
    });
}

/**
 * Vérifie si le produit est dans la wishlist
 */
function checkWishlistStatus(productId) {
    if (!productConfig.urls.checkWishlistStatus || !productId) return;

    fetch(`${productConfig.urls.checkWishlistStatus}?product_id=${productId}`)
        .then(response => response.json())
        .then(data => {
            updateWishlistButton(data.in_wishlist);
        })
        .catch(error => {
            console.log('Erreur lors de la vérification de la wishlist:', error);
        });
}

/**
 * Ajoute ou retire le produit de la wishlist
 */
function toggleWishlist(productId, button) {
    const isInWishlist = button.classList.contains('in-wishlist');
    const url = isInWishlist ? productConfig.urls.removeFromWishlist : productConfig.urls.addToWishlist;

    if (!url || !productId) return;

    // Désactiver le bouton pendant la requête
    button.disabled = true;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>En cours...';

    // Préparer les données du formulaire
    const formData = new FormData();
    formData.append('product_id', productId);

    // Récupérer le token CSRF
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateWishlistButton(data.in_wishlist);

            // Afficher un message de succès
            showWishlistMessage(data.message, 'success');
        } else {
            // Afficher un message d'erreur
            showWishlistMessage(data.message || 'Une erreur est survenue', 'error');
        }
    })
    .catch(error => {
        console.error('Erreur wishlist:', error);
        showWishlistMessage('Erreur de connexion', 'error');
    })
    .finally(() => {
        // Réactiver le bouton
        button.disabled = false;
        if (!button.classList.contains('in-wishlist') && !button.classList.contains('not-in-wishlist')) {
            button.innerHTML = originalText;
        }
    });
}

/**
 * Met à jour l'apparence du bouton wishlist
 */
function updateWishlistButton(inWishlist) {
    const wishlistBtn = document.querySelector('.action-button.secondary[data-product-id]');
    if (!wishlistBtn) return;

    wishlistBtn.classList.remove('in-wishlist', 'not-in-wishlist');

    if (inWishlist) {
        wishlistBtn.classList.add('in-wishlist');
        wishlistBtn.innerHTML = '<i class="bi bi-heart-fill me-2" style="color: #dc3545;"></i>dans la wishlist';
        wishlistBtn.style.background = '#fff5f5';
        wishlistBtn.style.borderColor = '#dc3545';
        wishlistBtn.style.color = '#dc3545';
    } else {
        wishlistBtn.classList.add('not-in-wishlist');
        wishlistBtn.innerHTML = '<i class="bi bi-heart me-2"></i>ajouter à la wishlist';
        wishlistBtn.style.background = '#fff';
        wishlistBtn.style.borderColor = '#000';
        wishlistBtn.style.color = '#000';
    }
}

/**
 * Affiche un message temporaire pour les actions wishlist
 */
function showWishlistMessage(message, type) {
    // Créer l'élément de message
    const messageEl = document.createElement('div');
    messageEl.className = `wishlist-message ${type}`;
    messageEl.textContent = message;

    // Styles du message
    Object.assign(messageEl.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '12px 20px',
        borderRadius: '8px',
        color: '#fff',
        fontSize: '14px',
        fontWeight: '500',
        zIndex: '10000',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        transform: 'translateX(100%)',
        transition: 'transform 0.3s ease',
        maxWidth: '300px'
    });

    if (type === 'success') {
        messageEl.style.background = '#22c55e';
    } else {
        messageEl.style.background = '#ef4444';
    }

    // Ajouter au DOM
    document.body.appendChild(messageEl);

    // Animer l'entrée
    setTimeout(() => {
        messageEl.style.transform = 'translateX(0)';
    }, 100);

    // Supprimer après 3 secondes
    setTimeout(() => {
        messageEl.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.parentNode.removeChild(messageEl);
            }
        }, 300);
    }, 3000);
}

/**
 * Initialise la validation du formulaire
 */
function initFormValidation() {
    const addToCartForm = document.querySelector('form[action*="add-to-cart"]');
    const sizeOptions = document.querySelectorAll('.size-option:not(.unavailable)');
    const quantityInput = document.querySelector('.quantity-input');
    
    if (addToCartForm) {
        addToCartForm.addEventListener('submit', function(e) {
            // Si il y a des variantes et qu'aucune taille n'est sélectionnée
            if (sizeOptions.length > 0 && !selectedSize) {
                e.preventDefault();
                alert('Veuillez sélectionner une taille avant d\'ajouter au panier.');
                return false;
            }
            
            if (quantityInput) {
                const quantityFormInput = document.createElement('input');
                quantityFormInput.type = 'hidden';
                quantityFormInput.name = 'quantity';
                quantityFormInput.value = quantityInput.value;
                this.appendChild(quantityFormInput);
            }
        });
    }
}

/**
 * Initialisation principale
 */
function initProductDetail() {
    console.log('🔍 Initialisation du détail produit...');
    
    const sizeOptions = document.querySelectorAll('.size-option:not(.unavailable)');
    console.log('📏 Options de taille disponibles:', sizeOptions.length);
    
    const addToCartBtn = document.querySelector('.add-to-cart');
    console.log('🛒 Bouton ajout panier trouvé:', addToCartBtn ? 'OUI' : 'NON');
    if (addToCartBtn) {
        console.log('Style actuel du bouton:', {
            display: getComputedStyle(addToCartBtn).display,
            visibility: getComputedStyle(addToCartBtn).visibility,
            opacity: getComputedStyle(addToCartBtn).opacity,
            position: getComputedStyle(addToCartBtn).position,
            zIndex: getComputedStyle(addToCartBtn).zIndex
        });
    }
    
    // Forcer la visibilité du bouton si trouvé avec tous les styles possibles
    if (addToCartBtn) {
        const styles = {
            display: 'block !important',
            visibility: 'visible !important',
            opacity: '1 !important',
            position: 'relative !important',
            zIndex: '999999 !important',
            width: '100% !important',
            margin: '20px 0 !important',
            padding: '15px !important',
            backgroundColor: '#000000 !important',
            color: '#ffffff !important',
            border: 'none !important',
            cursor: 'pointer !important',
            borderRadius: '0 !important',
            fontSize: '1rem !important',
            fontWeight: '500 !important',
            textTransform: 'lowercase !important'
        };
        
        Object.assign(addToCartBtn.style, styles);
        
        // Force l'application des styles avec setAttribute
        let styleString = Object.entries(styles)
            .map(([key, value]) => `${key.replace(/([A-Z])/g, '-$1').toLowerCase()}: ${value}`)
            .join('; ');
        addToCartBtn.setAttribute('style', styleString);
        
        console.log('💅 Styles appliqués au bouton');
    }

    // Initialiser les différents modules
    initQuantityControls();
    initImageGallery();
    initWishlistFunctionality();
    initFormValidation();

    // Initialize first size if only one available
    if (sizeOptions.length === 1) {
        sizeOptions[0].click();
    } else if (sizeOptions.length === 0) {
        // Si pas de variantes, afficher directement le bouton
        updateCartButton();
    } else {
        // Si plusieurs tailles disponibles, désactiver le bouton jusqu'à sélection
        if (addToCartBtn) {
            addToCartBtn.disabled = true;
            addToCartBtn.style.opacity = '0.6';
            addToCartBtn.style.cursor = 'not-allowed';
            addToCartBtn.innerHTML = '<i class="bi bi-cart-plus me-2"></i>sélectionnez une taille';
            addToCartBtn.style.display = 'block';
            addToCartBtn.style.visibility = 'visible';
        }
    }
}

// Initialisation quand le DOM est prêt
document.addEventListener('DOMContentLoaded', function() {
    initProductDetail();
});
