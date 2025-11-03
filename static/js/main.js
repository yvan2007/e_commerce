/**
 * E-Commerce CI - Main JavaScript
 * Gestion des animations, interactions et fonctionnalités
 */

// Configuration globale
const CONFIG = {
    animationDuration: 300,
    debounceDelay: 300,
    apiEndpoints: {
        addToCart: '/add-to-cart/',
        removeFromCart: '/remove-from-cart/',
        updateCart: '/update-cart-item/',
        searchSuggestions: '/api/search-suggestions/',
        checkUsername: '/accounts/api/check-username/',
        checkEmail: '/accounts/api/check-email/',
    }
};

// Gestion des menus déroulants
const DropdownManager = {
    init() {
        this.setupDropdowns();
        this.handleDropdownPositioning();
    },

    setupDropdowns() {
        // Laisser Bootstrap gérer nativement les dropdowns
        // Ne pas interférer avec les dropdowns standards
        return;
        
        // Améliorer les dropdowns Bootstrap
        document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const dropdown = e.target.closest('.dropdown');
                const menu = dropdown.querySelector('.dropdown-menu');
                
                // Fermer les autres dropdowns
                document.querySelectorAll('.dropdown-menu.show').forEach(openMenu => {
                    if (openMenu !== menu) {
                        openMenu.classList.remove('show');
                        openMenu.closest('.dropdown').classList.remove('show');
                    }
                });
                
                // Toggle le dropdown actuel
                const isOpen = menu.classList.contains('show');
                if (isOpen) {
                    menu.classList.remove('show');
                    dropdown.classList.remove('show');
                } else {
                    menu.classList.add('show');
                    dropdown.classList.add('show');
                }
                
                console.log('Dropdown toggled:', menu.classList.contains('show'));
            });
        });

        // Fermer les dropdowns en cliquant ailleurs
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.dropdown')) {
                document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                    menu.classList.remove('show');
                    menu.closest('.dropdown').classList.remove('show');
                });
            }
        });
    },

    handleDropdownPositioning() {
        // S'assurer que les dropdowns de la top bar s'affichent correctement
        document.querySelectorAll('.top-bar .dropdown-menu').forEach(menu => {
            const dropdown = menu.closest('.dropdown');
            const toggle = dropdown.querySelector('.dropdown-toggle');
            
            toggle.addEventListener('click', () => {
                // Calculer la position pour éviter le débordement
                const rect = toggle.getBoundingClientRect();
                const menuRect = menu.getBoundingClientRect();
                
                // Si le menu déborde à droite, l'aligner à droite
                if (rect.right + menuRect.width > window.innerWidth) {
                    menu.style.left = 'auto';
                    menu.style.right = '0';
                } else {
                    menu.style.left = '0';
                    menu.style.right = 'auto';
                }
                
                // Si le menu déborde en haut, l'afficher vers le bas
                if (rect.top - menuRect.height < 0) {
                    menu.style.top = '100%';
                    menu.style.bottom = 'auto';
                } else {
                    menu.style.top = 'auto';
                    menu.style.bottom = '100%';
                }
            });
        });
    }
};

// Utilitaires
const Utils = {
    // Debounce function
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Formatage des prix
    formatPrice(price) {
        return new Intl.NumberFormat('fr-CI', {
            style: 'currency',
            currency: 'XOF',
            minimumFractionDigits: 0
        }).format(price);
    },

    // Animation de notification
    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = `
            top: 100px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            animation: slideInRight 0.5s ease;
        `;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    },

    // Loading spinner
    showLoading(element) {
        const spinner = document.createElement('div');
        spinner.className = 'spinner-border text-primary';
        spinner.innerHTML = '<span class="visually-hidden">Chargement...</span>';
        element.innerHTML = '';
        element.appendChild(spinner);
    },

    // Validation email
    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    // Validation téléphone
    isValidPhone(phone) {
        const re = /^\+?[\d\s\-\(\)]+$/;
        return re.test(phone) && phone.replace(/\D/g, '').length >= 8;
    }
};

// Gestionnaire de panier
class CartManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateCartCount();
    }

    bindEvents() {
        // Ajouter au panier
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="add-to-cart"]')) {
                e.preventDefault();
                this.addToCart(e.target);
            }
            
            if (e.target.matches('[data-action="remove-from-cart"]')) {
                e.preventDefault();
                this.removeFromCart(e.target);
            }
            
            if (e.target.matches('[data-action="update-cart"]')) {
                e.preventDefault();
                this.updateCartItem(e.target);
            }
        });

        // Mise à jour quantité
        document.addEventListener('change', (e) => {
            if (e.target.matches('[data-cart-quantity]')) {
                this.updateCartQuantity(e.target);
            }
        });
    }

    async addToCart(button) {
        const productId = button.dataset.productId;
        const quantity = button.dataset.quantity || 1;
        const variantId = button.dataset.variantId || null;

        try {
            button.disabled = true;
            Utils.showLoading(button);

            const formData = new FormData();
            formData.append('product_id', productId);
            formData.append('quantity', quantity);
            if (variantId) formData.append('variant_id', variantId);
            formData.append('csrfmiddlewaretoken', this.getCSRFToken());

            const response = await fetch(CONFIG.apiEndpoints.addToCart + productId + '/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });

            // Vérifier si la réponse est OK
            if (!response.ok) {
                // Si ce n'est pas OK (404, 500, etc.), essayer de lire le texte pour voir l'erreur
                const text = await response.text();
                console.error('Erreur HTTP:', response.status, text);
                Utils.showNotification(`Erreur ${response.status}: URL non trouvée. Veuillez rafraîchir la page.`, 'danger');
                return;
            }

            // Vérifier si le contenu est JSON
            const contentType = response.headers.get("content-type");
            let data;
            if (contentType && contentType.includes("application/json")) {
                data = await response.json();
            } else {
                // Essayer quand même de parser comme JSON
                try {
                    const text = await response.text();
                    data = JSON.parse(text);
                } catch (e) {
                    console.error('La réponse n\'est pas du JSON:', e);
                    Utils.showNotification('Erreur: Réponse invalide du serveur', 'danger');
                    return;
                }
            }

            if (data.success) {
                Utils.showNotification(data.message || 'Produit ajouté au panier', 'success');
                this.updateCartCount(data.cart_count);
                this.animateCartIcon();
            } else {
                Utils.showNotification(data.message || 'Erreur lors de l\'ajout au panier', 'danger');
            }
        } catch (error) {
            console.error('Erreur:', error);
            Utils.showNotification('Erreur de connexion lors de l\'ajout au panier. Veuillez réessayer.', 'danger');
        } finally {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-shopping-cart me-2"></i>Ajouter au panier';
        }
    }

    async removeFromCart(button) {
        const itemId = button.dataset.itemId;

        try {
            button.disabled = true;
            Utils.showLoading(button);

            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', this.getCSRFToken());

            const response = await fetch(CONFIG.apiEndpoints.removeFromCart + itemId + '/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                const text = await response.text();
                console.error('Erreur HTTP:', response.status, text);
                Utils.showNotification(`Erreur ${response.status}: URL non trouvée.`, 'danger');
                return;
            }

            const contentType = response.headers.get("content-type");
            let data;
            if (contentType && contentType.includes("application/json")) {
                data = await response.json();
            } else {
                try {
                    const text = await response.text();
                    data = JSON.parse(text);
                } catch (e) {
                    console.error('La réponse n\'est pas du JSON:', e);
                    Utils.showNotification('Erreur: Réponse invalide du serveur', 'danger');
                    return;
                }
            }

            if (data.success) {
                Utils.showNotification(data.message || 'Produit retiré du panier', 'success');
                this.updateCartCount(data.cart_count);
                this.removeCartItem(itemId);
            } else {
                Utils.showNotification(data.message || 'Erreur lors de la suppression', 'danger');
            }
        } catch (error) {
            console.error('Erreur:', error);
            Utils.showNotification('Erreur de connexion', 'danger');
        } finally {
            button.disabled = false;
        }
    }

    async updateCartQuantity(input) {
        const itemId = input.dataset.cartQuantity;
        const quantity = input.value;

        try {
            const formData = new FormData();
            formData.append('quantity', quantity);
            formData.append('csrfmiddlewaretoken', this.getCSRFToken());

            const response = await fetch(CONFIG.apiEndpoints.updateCart + itemId + '/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                const text = await response.text();
                console.error('Erreur HTTP:', response.status, text);
                Utils.showNotification(`Erreur ${response.status}: URL non trouvée.`, 'danger');
                return;
            }

            const contentType = response.headers.get("content-type");
            let data;
            if (contentType && contentType.includes("application/json")) {
                data = await response.json();
            } else {
                try {
                    const text = await response.text();
                    data = JSON.parse(text);
                } catch (e) {
                    console.error('La réponse n\'est pas du JSON:', e);
                    Utils.showNotification('Erreur: Réponse invalide du serveur', 'danger');
                    return;
                }
            }

            if (data.success) {
                this.updateCartCount(data.cart_count);
                this.updateCartTotal(data.total_price);
            }
        } catch (error) {
            console.error('Erreur:', error);
        }
    }

    updateCartCount(count) {
        const cartCountElement = document.getElementById('cart-count');
        if (cartCountElement) {
            cartCountElement.textContent = count;
            cartCountElement.style.animation = 'none';
            setTimeout(() => {
                cartCountElement.style.animation = 'pulse 0.5s ease';
            }, 10);
        }
    }

    animateCartIcon() {
        const cartIcon = document.querySelector('.fa-shopping-cart');
        if (cartIcon) {
            cartIcon.style.animation = 'none';
            setTimeout(() => {
                cartIcon.style.animation = 'bounce 0.6s ease';
            }, 10);
        }
    }

    removeCartItem(itemId) {
        const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);
        if (itemElement) {
            const cartItem = itemElement.closest('.cart-item');
            if (cartItem) {
                cartItem.style.animation = 'slideOutLeft 0.3s ease';
                setTimeout(() => {
                    cartItem.remove();
                }, 300);
            }
        }
    }

    updateCartTotal(totalPrice) {
        const totalElement = document.querySelector('.cart-total');
        if (totalElement) {
            totalElement.textContent = Utils.formatPrice(totalPrice);
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
}

// Gestionnaire de recherche
class SearchManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', Utils.debounce((e) => {
                this.handleSearch(e.target.value);
            }, CONFIG.debounceDelay));

            searchInput.addEventListener('focus', () => {
                this.showSuggestions();
            });

            searchInput.addEventListener('blur', () => {
                setTimeout(() => this.hideSuggestions(), 200);
            });
        }
    }

    async handleSearch(query) {
        if (query.length < 2) {
            this.hideSuggestions();
            return;
        }

        try {
            const response = await fetch(`${CONFIG.apiEndpoints.searchSuggestions}?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.suggestions && data.suggestions.length > 0) {
                this.showSuggestions(data.suggestions);
            } else {
                this.hideSuggestions();
            }
        } catch (error) {
            console.error('Erreur de recherche:', error);
        }
    }

    showSuggestions(suggestions = []) {
        let suggestionsContainer = document.getElementById('search-suggestions');
        
        if (!suggestionsContainer) {
            suggestionsContainer = document.createElement('div');
            suggestionsContainer.id = 'search-suggestions';
            suggestionsContainer.className = 'search-suggestions position-absolute bg-white border rounded shadow-lg';
            suggestionsContainer.style.cssText = `
                top: 100%;
                left: 0;
                right: 0;
                z-index: 1000;
                max-height: 300px;
                overflow-y: auto;
            `;
            
            const searchContainer = document.querySelector('.input-group');
            if (searchContainer) {
                searchContainer.style.position = 'relative';
                searchContainer.appendChild(suggestionsContainer);
            }
    }
    
    if (suggestions.length > 0) {
            suggestionsContainer.innerHTML = suggestions.map(suggestion => `
                <div class="suggestion-item p-3 border-bottom cursor-pointer" 
                     onclick="window.location.href='${suggestion.url}'">
                <div class="d-flex align-items-center">
                        ${suggestion.image ? 
                            `<img src="${suggestion.image}" alt="${suggestion.name}" class="me-3" width="40" height="40" style="object-fit: cover;">` : 
                            '<div class="me-3 bg-light rounded" style="width: 40px; height: 40px;"></div>'
                        }
                    <div>
                            <div class="fw-semibold">${suggestion.name}</div>
                            <div class="text-muted small">${Utils.formatPrice(suggestion.price)}</div>
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            suggestionsContainer.innerHTML = '<div class="p-3 text-muted">Aucun résultat trouvé</div>';
        }
    }

    hideSuggestions() {
        const suggestionsContainer = document.getElementById('search-suggestions');
        if (suggestionsContainer) {
            suggestionsContainer.remove();
        }
    }
}

// Gestionnaire de formulaires
class FormManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initValidation();
    }

    bindEvents() {
        // Validation en temps réel
        document.addEventListener('input', (e) => {
            if (e.target.matches('[data-validate]')) {
                this.validateField(e.target);
            }
        });

        // Soumission de formulaires
        document.addEventListener('submit', (e) => {
            if (e.target.matches('[data-ajax-form]')) {
                e.preventDefault();
                this.handleAjaxSubmit(e.target);
            }
        });
    }

    initValidation() {
        // Validation email
        const emailInputs = document.querySelectorAll('input[type="email"]');
        emailInputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateEmail(input);
            });
        });

        // Validation téléphone (sauf checkout)
        const phoneInputs = document.querySelectorAll('input[type="tel"], input[name*="phone"]');
        phoneInputs.forEach(input => {
            // Ignorer la validation pour le champ checkout
            if (input.closest('#checkout-form')) {
                return;
            }
            input.addEventListener('blur', () => {
                this.validatePhone(input);
            });
        });

        // Vérification disponibilité username/email
        const usernameInput = document.querySelector('input[name="username"]');
        if (usernameInput) {
            usernameInput.addEventListener('blur', Utils.debounce(() => {
                this.checkAvailability(usernameInput, 'username');
            }, CONFIG.debounceDelay));
        }

        const emailInput = document.querySelector('input[name="email"]');
        if (emailInput) {
            emailInput.addEventListener('blur', Utils.debounce(() => {
                this.checkAvailability(emailInput, 'email');
            }, CONFIG.debounceDelay));
        }
    }

    validateField(field) {
        const value = field.value.trim();
        const type = field.dataset.validate;

        switch (type) {
            case 'required':
                return this.setFieldValidity(field, value.length > 0, 'Ce champ est requis');
            case 'email':
                return this.validateEmail(field);
            case 'phone':
                return this.validatePhone(field);
            case 'password':
                return this.validatePassword(field);
            default:
                return true;
        }
    }

    validateEmail(field) {
        const isValid = Utils.isValidEmail(field.value);
        this.setFieldValidity(field, isValid, 'Adresse email invalide');
        return isValid;
    }

    validatePhone(field) {
        const isValid = Utils.isValidPhone(field.value);
        this.setFieldValidity(field, isValid, 'Numéro de téléphone invalide');
        return isValid;
    }

    validatePassword(field) {
        const password = field.value;
        const isValid = password.length >= 8;
        this.setFieldValidity(field, isValid, 'Le mot de passe doit contenir au moins 8 caractères');
        return isValid;
    }

    async checkAvailability(field, type) {
        const value = field.value.trim();
        if (!value) return;

        try {
            const formData = new FormData();
            formData.append(type, value);
            formData.append('csrfmiddlewaretoken', this.getCSRFToken());

            const response = await fetch(CONFIG.apiEndpoints[`check${type.charAt(0).toUpperCase() + type.slice(1)}`], {
            method: 'POST',
                body: formData,
            headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();
            this.setFieldValidity(field, data.available, data.available ? '' : `${type} déjà utilisé`);
        } catch (error) {
            console.error('Erreur de vérification:', error);
        }
    }

    setFieldValidity(field, isValid, message) {
        const feedback = field.parentNode.querySelector('.invalid-feedback') || 
                        field.parentNode.querySelector('.valid-feedback');
        
        if (feedback) {
            feedback.remove();
        }

        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = isValid ? 'valid-feedback' : 'invalid-feedback';
        feedbackDiv.textContent = message;
        
        field.parentNode.appendChild(feedbackDiv);
        field.classList.toggle('is-valid', isValid);
        field.classList.toggle('is-invalid', !isValid);

        return isValid;
    }

    async handleAjaxSubmit(form) {
        const submitButton = form.querySelector('[type="submit"]');
        const originalText = submitButton.innerHTML;

        try {
            submitButton.disabled = true;
            Utils.showLoading(submitButton);

            const formData = new FormData(form);
            const response = await fetch(form.action, {
        method: 'POST',
                body: formData,
        headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

        if (data.success) {
                Utils.showNotification(data.message || 'Action réussie', 'success');
                if (data.redirect) {
                    setTimeout(() => {
                        window.location.href = data.redirect;
                    }, 1000);
            }
        } else {
                Utils.showNotification(data.message || 'Erreur', 'danger');
            }
        } catch (error) {
            console.error('Erreur:', error);
            Utils.showNotification('Erreur de connexion', 'danger');
        } finally {
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
}

// Gestionnaire d'animations
class AnimationManager {
    constructor() {
        this.init();
    }

    init() {
        this.initAOS();
        this.initScrollAnimations();
        this.initHoverEffects();
    }

    initAOS() {
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-in-out',
            once: true,
            offset: 100
        });
    }
    }

    initScrollAnimations() {
        // Back to top button
        const backToTopButton = document.getElementById('backToTop');
        if (backToTopButton) {
            window.addEventListener('scroll', Utils.debounce(() => {
                if (window.pageYOffset > 300) {
                    backToTopButton.style.display = 'block';
                    backToTopButton.style.animation = 'fadeIn 0.3s ease';
                } else {
                    backToTopButton.style.display = 'none';
                }
            }, 100));

            backToTopButton.addEventListener('click', () => {
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
        });
    });
}

        // Parallax effect for hero sections
        const heroElements = document.querySelectorAll('.hero-section');
        heroElements.forEach(element => {
            window.addEventListener('scroll', () => {
                const scrolled = window.pageYOffset;
                const rate = scrolled * -0.5;
                element.style.transform = `translateY(${rate}px)`;
            });
        });
    }

    initHoverEffects() {
        // Card hover effects
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-5px)';
                card.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.15)';
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
                card.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
            });
        });

        // Button hover effects
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(button => {
            button.addEventListener('mouseenter', () => {
                button.style.transform = 'translateY(-2px)';
            });

            button.addEventListener('mouseleave', () => {
                button.style.transform = 'translateY(0)';
            });
        });
    }
}

// Gestionnaire de modales
class ModalManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // Ouverture de modales
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-modal-target]')) {
                e.preventDefault();
                this.openModal(e.target.dataset.modalTarget);
            }
        });

        // Fermeture de modales
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-modal-close]') || 
                e.target.matches('.modal-backdrop')) {
                this.closeModal();
            }
        });

        // Fermeture avec Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'block';
            modal.classList.add('show');
            document.body.classList.add('modal-open');
            
            // Animation d'entrée
            setTimeout(() => {
                modal.querySelector('.modal-dialog').style.transform = 'scale(1)';
                modal.querySelector('.modal-dialog').style.opacity = '1';
            }, 10);
        }
    }

    closeModal() {
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            const dialog = openModal.querySelector('.modal-dialog');
            dialog.style.transform = 'scale(0.8)';
            dialog.style.opacity = '0';
            
            setTimeout(() => {
                openModal.classList.remove('show');
                openModal.style.display = 'none';
                document.body.classList.remove('modal-open');
            }, 300);
        }
    }
}

// Initialisation de l'application
document.addEventListener('DOMContentLoaded', () => {
    // Initialiser les gestionnaires
    new CartManager();
    new SearchManager();
    new FormManager();
    new AnimationManager();
    new ModalManager();
    DropdownManager.init(); // Initialiser le gestionnaire de dropdowns

    // Animation de chargement de page
    document.body.classList.add('fade-in');

    // Gestion des messages flash
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.animation = 'slideOutRight 0.5s ease';
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });

    // Gestion des tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Gestion des popovers Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    console.log('E-Commerce CI - Application initialisée avec succès');
});

// Styles CSS pour les animations
const style = document.createElement('style');
style.textContent = `
    @keyframes bounce {
        0%, 20%, 53%, 80%, 100% { transform: translate3d(0,0,0); }
        40%, 43% { transform: translate3d(0,-8px,0); }
        70% { transform: translate3d(0,-4px,0); }
        90% { transform: translate3d(0,-2px,0); }
    }

    @keyframes slideOutLeft {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(-100%); opacity: 0; }
    }

    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }

    .search-suggestions .suggestion-item:hover {
        background-color: rgba(0, 123, 255, 0.1);
    }

    .modal-dialog {
        transition: all 0.3s ease;
        transform: scale(0.8);
        opacity: 0;
    }

    .modal.show .modal-dialog {
        transform: scale(1);
        opacity: 1;
    }

    .cursor-pointer {
        cursor: pointer;
    }
`;
document.head.appendChild(style);