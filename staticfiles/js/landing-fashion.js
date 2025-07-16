/*
=================================================
LANDING FASHION - JAVASCRIPT SHOWCASE/VITRINE
Style Zara/Bershka pour présentation de collections
=================================================
*/

document.addEventListener('DOMContentLoaded', function() {
    
    // ===========================================
    // 1. NAVIGATION COLLECTIONS INTERACTIVE
    // ===========================================
    
    const categoryLinks = document.querySelectorAll('.category-nav-link');
    
    categoryLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            // Animation d'hover améliorée
            this.style.transform = 'translateY(-5px) scale(1.02)';
            this.style.boxShadow = '0 10px 25px rgba(0,0,0,0.1)';
        });
        
        link.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
            this.style.boxShadow = 'none';
        });
        
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Effet de clic avec feedback
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
            
            // Analytics tracking
            trackCollectionClick(this.textContent.trim());
            
            // Navigation vers la catégorie
            const href = this.getAttribute('href');
            if (href && href !== '#') {
                setTimeout(() => {
                    window.location.href = href;
                }, 200);
            }
        });
    });
    
    // ===========================================
    // 2. COLLECTIONS SHOWCASE INTERACTIONS
    // ===========================================
    
    const collectionCards = document.querySelectorAll('.collection-card');
    
    collectionCards.forEach(card => {
        const overlay = card.querySelector('.collection-overlay');
        const content = card.querySelector('.collection-content');
        
        card.addEventListener('mouseenter', function() {
            // Animation d'entrée sophistiquée
            if (overlay) overlay.style.opacity = '1';
            if (content) {
                content.style.transform = 'translateY(0)';
                content.style.opacity = '1';
            }
        });
        
        card.addEventListener('mouseleave', function() {
            // Animation de sortie
            if (overlay) overlay.style.opacity = '0';
            if (content) {
                content.style.transform = 'translateY(20px)';
                content.style.opacity = '0.8';
            }
        });
        
        card.addEventListener('click', function() {
            const collectionName = this.querySelector('.collection-name')?.textContent;
            const collectionBtn = this.querySelector('.btn-collection');
            
            // Effet de loading
            if (collectionBtn) {
                const originalText = collectionBtn.textContent;
                collectionBtn.textContent = 'LOADING...';
                collectionBtn.style.pointerEvents = 'none';
                
                // Redirection avec délai pour l'animation
                setTimeout(() => {
                    const href = collectionBtn.getAttribute('href');
                    if (href && href !== '#') {
                        window.location.href = href;
                    } else {
                        // Fallback vers page shop général
                        window.location.href = '/shop/';
                    }
                }, 800);
            }
            
            // Analytics
            trackCollectionClick(collectionName || 'Unknown Collection');
        });
    });
    
    // ===========================================
    // 3. GESTION DES LIENS DE NAVIGATION
    // ===========================================
    
    const collectionButtons = document.querySelectorAll('.btn-collection');
    
    collectionButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Animation de chargement
            const originalText = this.textContent;
            this.textContent = 'EXPLORING...';
            this.style.transform = 'scale(0.95)';
            this.style.pointerEvents = 'none';
            
            // Navigation vers les catégories
            setTimeout(() => {
                const href = this.getAttribute('href');
                if (href && href !== '#') {
                    window.location.href = href;
                } else {
                    // Fallback vers page shop général
                    window.location.href = '/shop/';
                }
            }, 1000);
        });
    });
    
    // ===========================================
    // 4. EFFETS DE SCROLL ET ANIMATIONS
    // ===========================================
    
    // Animation d'apparition des collections au scroll
    const showcaseObserverOptions = {
        threshold: 0.2,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const showcaseObserver = new IntersectionObserver(function(entries) {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.animation = 'fadeInUp 0.8s ease forwards';
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, index * 150);
                
                showcaseObserver.unobserve(entry.target);
            }
        });
    }, showcaseObserverOptions);
    
    // Observer toutes les collections
    collectionCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(50px)';
        showcaseObserver.observe(card);
    });
    
    // ===========================================
    // 5. RESPONSIVE ET LAYOUT DYNAMIQUE
    // ===========================================
    
    function adjustGridLayout() {
        const grid = document.querySelector('.collections-grid');
        if (!grid) return;
        
        const windowWidth = window.innerWidth;
        
        if (windowWidth < 768) {
            // Mobile: une seule colonne
            grid.style.gridTemplateColumns = '1fr';
            grid.style.gridTemplateRows = 'repeat(4, 250px)';
            
            // Réajuster les spans
            collectionCards.forEach(card => {
                card.style.gridColumn = 'span 1';
                card.style.gridRow = 'span 1';
            });
        } else if (windowWidth < 1024) {
            // Tablet: adaptatif
            grid.style.gridTemplateColumns = 'repeat(6, 1fr)';
            grid.style.gridTemplateRows = 'repeat(3, 280px)';
        } else {
            // Desktop: layout normal
            grid.style.gridTemplateColumns = 'repeat(12, 1fr)';
            grid.style.gridTemplateRows = 'repeat(3, 300px)';
        }
    }
    
    // Fonction throttle pour optimiser les performances
    function throttle(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Ajuster au chargement et au redimensionnement
    adjustGridLayout();
    window.addEventListener('resize', throttle(adjustGridLayout, 250));
    
    // ===========================================
    // 6. ANALYTICS ET TRACKING
    // ===========================================
    
    function trackCollectionClick(collectionName) {
        console.log(`Fashion Showcase Analytics: Collection clicked - ${collectionName}`);
        
        // Ici intégration analytics réels
        // gtag('event', 'collection_view', {
        //     'event_category': 'Navigation',
        //     'event_label': collectionName
        // });
    }
    
    function trackPageEngagement() {
        const startTime = Date.now();
        
        window.addEventListener('beforeunload', function() {
            const timeSpent = Math.floor((Date.now() - startTime) / 1000);
            console.log(`Fashion Showcase Analytics: Time spent - ${timeSpent}s`);
        });
    }
    
    trackPageEngagement();
    
    // ===========================================
    // 7. LAZY LOADING ET OPTIMISATIONS
    // ===========================================
    
    // Lazy loading pour les images de fond
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                
                if (element.dataset.bgImage) {
                    element.style.backgroundImage = `url(${element.dataset.bgImage})`;
                    element.classList.add('loaded');
                    observer.unobserve(element);
                }
            }
        });
    });
    
    document.querySelectorAll('[data-bg-image]').forEach(el => {
        imageObserver.observe(el);
    });
    
    // ===========================================
    // 8. GESTION DES ERREURS ET FALLBACKS
    // ===========================================
    
    // Fallback pour les navigateurs sans support IntersectionObserver
    if (!window.IntersectionObserver) {
        // Afficher tous les éléments immédiatement
        collectionCards.forEach(card => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        });
        
        console.warn('IntersectionObserver not supported, using fallback');
    }
    
    window.addEventListener('error', function(e) {
        console.error('Fashion Showcase Error:', e.error);
        
        // Fallback pour les liens cassés
        document.querySelectorAll('a[href]').forEach(link => {
            link.addEventListener('click', function(e) {
                if (!this.href || this.href === '#') {
                    e.preventDefault();
                    console.warn('Navigation link not configured:', this);
                }
            });
        });
    });
    
    // ===========================================
    // 9. ANIMATIONS CSS DYNAMIQUES
    // ===========================================
    
    // Injection des keyframes d'animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .collection-card {
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .category-nav-link {
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-collection {
            transition: all 0.3s ease;
        }
    `;
    
    document.head.appendChild(style);
    
    console.log('🏪 Fashion Showcase JavaScript loaded successfully!');
});
