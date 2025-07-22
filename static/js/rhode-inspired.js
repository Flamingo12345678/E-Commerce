/*
=================================================
RHODE SKIN INSPIRED INTERACTIONS
=================================================
*/

document.addEventListener('DOMContentLoaded', function() {
    
    // Smooth scroll for navigation links
    const navLinks = document.querySelectorAll('.nav-link-rhode[href^="#"]');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Product card hover effects
    const productCards = document.querySelectorAll('.product-card-rhode');
    productCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Category card hover effects
    const categoryCards = document.querySelectorAll('.category-card-rhode');
    categoryCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Newsletter form enhancement
    const newsletterForm = document.querySelector('.newsletter-form-rhode');
    if (newsletterForm) {
        const emailInput = newsletterForm.querySelector('.newsletter-input-rhode');
        const submitBtn = newsletterForm.querySelector('.newsletter-btn-rhode');
        
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (emailInput.value && isValidEmail(emailInput.value)) {
                // Simulate success
                submitBtn.textContent = 'subscribed!';
                submitBtn.style.background = 'var(--rhode-sage)';
                emailInput.value = '';
                
                setTimeout(() => {
                    submitBtn.textContent = 'subscribe';
                    submitBtn.style.background = 'var(--rhode-black)';
                }, 2000);
            } else {
                // Show error
                emailInput.style.borderColor = '#e74c3c';
                emailInput.placeholder = 'please enter a valid email';
                
                setTimeout(() => {
                    emailInput.style.borderColor = 'var(--rhode-gray-light)';
                    emailInput.placeholder = 'your email address';
                }, 3000);
            }
        });
    }
    
    // Mobile menu toggle
    const mobileToggle = document.querySelector('.navbar-toggler');
    if (mobileToggle) {
        mobileToggle.addEventListener('click', function() {
            const navCollapse = document.querySelector('#navbarNav');
            const spans = this.querySelectorAll('span');
            
            if (navCollapse.classList.contains('show')) {
                // Close animation
                spans[0].style.transform = 'rotate(0deg)';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'rotate(0deg)';
            } else {
                // Open animation
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(7px, -6px)';
            }
        });
    }
    
    // Add to cart button enhancement
    const addToCartBtns = document.querySelectorAll('.product-add-to-cart-rhode');
    addToCartBtns.forEach(btn => {
        if (!btn.disabled) {
            btn.addEventListener('click', function(e) {
                // Add loading state
                const originalText = this.textContent;
                this.textContent = 'adding...';
                this.style.opacity = '0.7';
                this.disabled = true;
                
                // Simulate loading (remove this in production)
                setTimeout(() => {
                    this.textContent = 'added!';
                    this.style.background = 'var(--rhode-sage)';
                    
                    setTimeout(() => {
                        this.textContent = originalText;
                        this.style.background = 'var(--rhode-black)';
                        this.style.opacity = '1';
                        this.disabled = false;
                    }, 1500);
                }, 800);
            });
        }
    });
    
    // Wishlist button functionality
    const wishlistBtns = document.querySelectorAll('.action-btn-rhode');
    wishlistBtns.forEach(btn => {
        const heartIcon = btn.querySelector('.bi-heart');
        if (heartIcon) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                
                if (heartIcon.classList.contains('bi-heart')) {
                    heartIcon.classList.remove('bi-heart');
                    heartIcon.classList.add('bi-heart-fill');
                    this.style.color = 'var(--rhode-peach)';
                    this.style.background = 'var(--rhode-white)';
                } else {
                    heartIcon.classList.remove('bi-heart-fill');
                    heartIcon.classList.add('bi-heart');
                    this.style.color = 'var(--rhode-black)';
                    this.style.background = 'var(--rhode-white)';
                }
            });
        }
    });
    
    // Intersection Observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    const animatedElements = document.querySelectorAll('.product-card-rhode, .category-card-rhode, .hero-content-rhode');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
    
    // Header scroll effect
    const header = document.querySelector('.navbar-rhode');
    if (header) {
        let lastScrollY = window.scrollY;
        
        window.addEventListener('scroll', () => {
            const currentScrollY = window.scrollY;
            
            if (currentScrollY > 100) {
                header.style.background = 'rgba(248, 246, 243, 0.95)';
                header.style.backdropFilter = 'blur(10px)';
                header.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
            } else {
                header.style.background = 'var(--rhode-white)';
                header.style.backdropFilter = 'none';
                header.style.boxShadow = 'none';
            }
            
            lastScrollY = currentScrollY;
        });
    }
    
    // Search functionality enhancement
    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length > 2) {
                searchTimeout = setTimeout(() => {
                    // Add search suggestions here if needed
                    console.log('Searching for:', query);
                }, 300);
            }
        });
    }
});

// Utility functions
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Lazy loading for images
function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('loading');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Call lazy loading
lazyLoadImages();

// Add loading shimmer effect
function addShimmerEffect() {
    const style = document.createElement('style');
    style.textContent = `
        .loading-shimmer {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
        }
        
        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
    `;
    document.head.appendChild(style);
}

addShimmerEffect();
