// Landing Page Professional JavaScript

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Smooth scrolling pour les ancres
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // 2. Animation d'apparition au scroll (Intersection Observer)
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in-up');
                observer.unobserve(entry.target); // Animer une seule fois
            }
        });
    }, observerOptions);

    // Observer les sections principales
    document.querySelectorAll('.features-section, .testimonials-section, .categories-section, .new-arrivals-section, .faq-section').forEach(section => {
        observer.observe(section);
    });

    // 3. Effet parallax subtil sur la hero section
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const rate = scrolled * -0.5;
        const heroImage = document.querySelector('.hero-section img');
        if (heroImage) {
            heroImage.style.transform = `translateY(${rate}px)`;
        }
    });

    // 4. Compteur animé pour les statistiques
    function animateCounter(element, target, duration = 2000) {
        const start = 0;
        const increment = target / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            
            // Formatage des nombres
            if (target >= 1000) {
                element.textContent = Math.floor(current / 1000) + 'K+';
            } else if (element.textContent.includes('★')) {
                element.textContent = current.toFixed(1) + '★';
            } else {
                element.textContent = Math.floor(current) + '+';
            }
        }, 16);
    }

    // Observer pour les statistiques
    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const statElement = entry.target;
                const text = statElement.textContent;
                
                // Extraire le nombre du texte
                if (text.includes('50K')) {
                    animateCounter(statElement, 50000);
                } else if (text.includes('1000')) {
                    animateCounter(statElement, 1000);
                } else if (text.includes('4.9')) {
                    animateCounter(statElement, 4.9);
                }
                
                statsObserver.unobserve(statElement);
            }
        });
    }, { threshold: 0.5 });

    // Observer les éléments statistiques
    document.querySelectorAll('.hero-section .h3').forEach(stat => {
        statsObserver.observe(stat);
    });

    // 5. Loading lazy pour les images
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                
                // Ajouter une classe de chargement
                img.classList.add('loading');
                
                // Simuler le chargement
                setTimeout(() => {
                    img.classList.remove('loading');
                    img.setAttribute('data-loaded', 'true');
                }, 300);
                
                imageObserver.unobserve(img);
            }
        });
    });

    document.querySelectorAll('.product-image img').forEach(img => {
        img.setAttribute('data-loaded', 'false');
        imageObserver.observe(img);
    });

    // 6. Effet de typing pour le titre principal
    function typeWriter(element, text, speed = 100) {
        let i = 0;
        element.textContent = '';
        
        function type() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(type, speed);
            }
        }
        
        type();
    }

    // 7. Newsletter avec validation
    const newsletterForms = document.querySelectorAll('form[action="#"]');
    newsletterForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const emailInput = this.querySelector('input[type="email"]');
            const email = emailInput.value;
            
            // Validation simple
            if (email && isValidEmail(email)) {
                // Animation de succès
                const button = this.querySelector('button');
                const originalText = button.textContent;
                
                button.textContent = '✓ Subscribed!';
                button.classList.add('bg-success');
                
                // Reset après 3 secondes
                setTimeout(() => {
                    button.textContent = originalText;
                    button.classList.remove('bg-success');
                    emailInput.value = '';
                }, 3000);
                
                // Ici vous pourriez ajouter un appel AJAX pour enregistrer l'email
                console.log('Newsletter subscription:', email);
            } else {
                // Animation d'erreur
                emailInput.classList.add('border-danger');
                emailInput.placeholder = 'Please enter a valid email';
                
                setTimeout(() => {
                    emailInput.classList.remove('border-danger');
                    emailInput.placeholder = 'Enter your email';
                }, 3000);
            }
        });
    });

    // 8. Fonction utilitaire pour valider l'email
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // 9. Effet hover avancé pour les cartes produits
    document.querySelectorAll('.product-card-premium, .product-card-modern').forEach(card => {
        card.addEventListener('mouseenter', function() {
            // Ajouter un effet de brillance
            this.style.background = 'linear-gradient(145deg, #ffffff 0%, #f8fafc 100%)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.background = 'white';
        });
    });

    // 10. Gestion du scroll pour la navbar (si nécessaire)
    let lastScrollTop = 0;
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const navbar = document.querySelector('.navbar');
        
        if (scrollTop > 100) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }
        
        lastScrollTop = scrollTop;
    });

    // 11. Préchargement des images importantes
    function preloadImages() {
        const imageUrls = [
            // Ajouter ici les URLs des images importantes à précharger
        ];
        
        imageUrls.forEach(url => {
            const img = new Image();
            img.src = url;
        });
    }

    // 12. Gestion des favoris (pour plus tard)
    document.querySelectorAll('.btn-outline-primary').forEach(button => {
        if (button.textContent.includes('View')) {
            button.addEventListener('click', function(e) {
                // Ajouter des analytics ou autres actions
                console.log('Product viewed:', this.closest('.card').querySelector('.card-title').textContent);
            });
        }
    });

    // 13. Animation du scroll indicator
    const scrollIndicator = document.querySelector('.scroll-indicator');
    if (scrollIndicator) {
        scrollIndicator.addEventListener('click', function() {
            window.scrollTo({
                top: window.innerHeight,
                behavior: 'smooth'
            });
        });
    }

    // 14. Performance: Debounce pour le scroll
    function debounce(func, wait) {
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

    // Appliquer le debounce aux événements de scroll intensifs
    window.addEventListener('scroll', debounce(() => {
        // Logique de scroll optimisée ici
    }, 10));

    // 15. Initialisation finale
    console.log('YEE Store Professional Landing Page Loaded! 🚀');
    
    // Précharger les images importantes
    preloadImages();
    
    // Ajouter une classe pour indiquer que JS est chargé
    document.body.classList.add('js-loaded');
});

// 16. Service Worker pour le cache (optionnel)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
