
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
 * Vérifie le statut de la wishlist
 */
function checkWishlistStatus() {
    const wishlistBtn = document.querySelector('.wishlist-btn');
    if (!wishlistBtn || !productConfig.urls.checkWishlistStatus) return;
    
    const productId = wishlistBtn.dataset.productId;
    
    fetch(`${productConfig.urls.checkWishlistStatus}?product_id=${productId}`)
        .then(response => response.json())
        .then(data => {
            updateWishlistButton(data.in_wishlist);
        })
        .catch(error => console.error('Erreur:', error));
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
function initWishlist() {
    const wishlistBtn = document.querySelector('.wishlist-btn');
    if (wishlistBtn) {
        // Vérifier le statut initial de la wishlist
        checkWishlistStatus();
        
        wishlistBtn.addEventListener('click', function() {
            const productId = this.dataset.productId;
            const icon = this.querySelector('i');
            const isInWishlist = icon.classList.contains('fa-heart') && !icon.classList.contains('far');
            
            if (isInWishlist) {
                // Retirer de la wishlist
                removeFromWishlist(productId);
            } else {
                // Ajouter à la wishlist
                addToWishlist(productId);
            }
        });
    }
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
    const sizeOptions = document.querySelectorAll('.size-option:not(.unavailable)');
    const addToCartBtn = document.querySelector('.add-to-cart');
    const quantityInput = document.querySelector('.quantity-input');

    // Forcer la visibilité du bouton si trouvé
    if (addToCartBtn) {
        addToCartBtn.style.display = 'block';
        addToCartBtn.style.visibility = 'visible';
        addToCartBtn.style.opacity = '1';
        addToCartBtn.style.position = 'relative';
        addToCartBtn.style.zIndex = '999999';
    }

    // Initialiser les différents modules
    initQuantityControls();
    initImageGallery();
    initWishlist();
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
