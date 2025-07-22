
/**
 * Product Detail Page - JavaScript functionality
 * Gestion de la page de détail produit avec sélection de taille, quantité, wishlist, etc.
 */

let selectedSize = null;

let productConfig = {
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

function handleSizeSelection(button) {
    document.querySelectorAll('.size-option').forEach(btn => {
        btn.classList.remove('active');
        btn.style.backgroundColor = '';
        btn.style.color = '';
        btn.style.borderColor = '';
    });

    button.classList.add('active');
    button.style.backgroundColor = '#000000';
    button.style.color = '#ffffff';
    button.style.borderColor = '#000000';

    selectedSize = button.dataset.size;
    const selectedSizeInput = document.getElementById('selectedSize');
    const maxStock = parseInt(button.dataset.stock);

    if (selectedSizeInput) {
        selectedSizeInput.value = selectedSize;
    }

    const addToCartBtn = document.querySelector('.add-to-cart');
    if (addToCartBtn) {
        addToCartBtn.disabled = false;
        addToCartBtn.style.opacity = '1';
        addToCartBtn.style.cursor = 'pointer';
    }

    const stockInfo = document.getElementById('sizeStockInfo');
    if (stockInfo) {
        if (maxStock > 10) {
            stockInfo.innerHTML = `<span class="stock-available">En stock (${maxStock} disponibles)</span>`;
        } else if (maxStock > 0) {
            stockInfo.innerHTML = `<span class="stock-low">Stock limité (${maxStock} restants)</span>`;
        }
    }

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

function updateCartButton() {
    const addToCartBtn = document.querySelector('.add-to-cart');
    const quantityInput = document.querySelector('.quantity-input');
    const sizeOptions = document.querySelectorAll('.size-option:not(.unavailable)');

    if (!addToCartBtn || !quantityInput) return;

    const quantity = parseInt(quantityInput.value);
    const price = productConfig.price;
    const total = (price * quantity).toFixed(2);

    if (selectedSize || sizeOptions.length === 0) {
        addToCartBtn.disabled = false;
        addToCartBtn.style.opacity = '1';
        addToCartBtn.style.cursor = 'pointer';
        addToCartBtn.innerHTML = `<i class="bi bi-cart-plus me-2"></i>ajouter au panier - €${total}`;
    } else {
        addToCartBtn.disabled = true;
        addToCartBtn.style.opacity = '0.6';
        addToCartBtn.style.cursor = 'not-allowed';
        addToCartBtn.innerHTML = '<i class="bi bi-cart-plus me-2"></i>sélectionnez une taille';
    }
}

function initQuantityControls() {
    const quantityInput = document.querySelector('.quantity-input');
    const minusBtn = document.querySelector('.quantity-btn.minus');
    const plusBtn = document.querySelector('.quantity-btn.plus');

    if (minusBtn) {
        minusBtn.addEventListener('click', function () {
            const currentValue = parseInt(quantityInput.value);
            if (currentValue > 1) {
                quantityInput.value = currentValue - 1;
                const selectedQuantityInput = document.getElementById('selectedQuantity');
                if (selectedQuantityInput) {
                    selectedQuantityInput.value = quantityInput.value;
                }
                updateCartButton();
            }
        });
    }

    if (plusBtn) {
        plusBtn.addEventListener('click', function () {
            const currentValue = parseInt(quantityInput.value);
            const max = parseInt(quantityInput.max) || 99;
            if (currentValue < max) {
                quantityInput.value = currentValue + 1;
                const selectedQuantityInput = document.getElementById('selectedQuantity');
                if (selectedQuantityInput) {
                    selectedQuantityInput.value = quantityInput.value;
                }
                updateCartButton();
            }
        });
    }

    if (quantityInput) {
        quantityInput.addEventListener('change', function () {
            let value = parseInt(this.value);
            const max = parseInt(this.max) || 99;
            if (value < 1) value = 1;
            if (value > max) value = max;
            this.value = value;

            const selectedQuantityInput = document.getElementById('selectedQuantity');
            if (selectedQuantityInput) {
                selectedQuantityInput.value = value;
            }
            updateCartButton();
        });
    }
}

document.addEventListener('DOMContentLoaded', function () {
    initQuantityControls();
    updateCartButton(); // Ajout important
});
