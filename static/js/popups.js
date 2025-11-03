/**
 * Système de gestion des popups, captcha et confidentialité
 */

class PopupManager {
    constructor() {
        this.popups = [];
        this.currentPopup = null;
        this.isPopupVisible = false;
        this.init();
    }

    init() {
        // Vérifier si les popups sont désactivés sur cette page
        if (window.disablePopups) {
            console.log('Popups désactivés sur cette page');
            return;
        }


        this.loadPopups();
        this.setupEventListeners();
        this.showCookieConsent();
    }

    async loadPopups() {
        try {
            const response = await fetch('/popups/api/popups/');
            const data = await response.json();

            if (data.status === 'success') {
                this.popups = data.popups;
                this.schedulePopups();
            }
        } catch (error) {
            console.error('Erreur lors du chargement des popups:', error);
        }
    }

    schedulePopups() {
        this.popups.forEach(popup => {
            if (this.shouldShowPopup(popup)) {
                this.schedulePopup(popup);
            }
        });
    }

    shouldShowPopup(popup) {
        // Vérifier si le popup doit être affiché selon les conditions
        const userType = this.getUserType();
        const currentPage = window.location.pathname;

        // Vérifier le type d'utilisateur
        if (userType === 'authenticated' && !popup.show_to_authenticated) return false;
        if (userType === 'anonymous' && !popup.show_to_anonymous) return false;

        // Vérifier les pages
        if (popup.pages && popup.pages.length > 0) {
            if (!popup.pages.includes(currentPage)) return false;
        }

        return true;
    }

    schedulePopup(popup) {
        let delay = 0;

        switch (popup.trigger_type) {
            case 'immediate':
                delay = 0;
                break;
            case 'delay':
                delay = popup.trigger_delay * 1000;
                break;
            case 'scroll':
                this.setupScrollTrigger(popup);
                return;
            case 'exit_intent':
                this.setupExitIntentTrigger(popup);
                return;
            case 'time_on_page':
                delay = popup.trigger_time * 1000;
                break;
        }

        if (delay > 0) {
            setTimeout(() => this.showPopup(popup), delay);
        } else {
            this.showPopup(popup);
        }
    }

    setupScrollTrigger(popup) {
        let hasTriggered = false;

        window.addEventListener('scroll', () => {
            if (hasTriggered) return;

            const scrollPercent = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100;

            if (scrollPercent >= popup.trigger_scroll) {
                hasTriggered = true;
                this.showPopup(popup);
            }
        });
    }

    setupExitIntentTrigger(popup) {
        let hasTriggered = false;

        document.addEventListener('mouseleave', (e) => {
            if (hasTriggered || e.clientY > 0) return;

            hasTriggered = true;
            this.showPopup(popup);
        });
    }

    showPopup(popup) {
        if (this.isPopupVisible) return;

        this.currentPopup = popup;
        this.isPopupVisible = true;

        // Créer le popup
        const popupElement = this.createPopupElement(popup);
        document.body.appendChild(popupElement);

        // Animer l'apparition
        setTimeout(() => {
            popupElement.classList.add('show');
        }, 10);

        // Tracker l'affichage
        this.trackPopupInteraction(popup.id, 'shown');
    }

    createPopupElement(popup) {
        const overlay = document.createElement('div');
        overlay.className = 'popup-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, ${popup.overlay_opacity});
            z-index: 9999;
            display: flex;
            justify-content: center;
            align-items: center;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;

        const container = document.createElement('div');
        container.className = 'popup-container';
        container.style.cssText = `
            background-color: ${popup.background_color};
            color: ${popup.text_color};
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            max-width: 500px;
            width: 90%;
            text-align: center;
            transform: translateY(-50px) scale(0.9);
            transition: transform 0.3s ease;
        `;

        container.innerHTML = `
            <button class="popup-close" style="position: absolute; top: 10px; right: 15px; background: none; border: none; font-size: 1.5rem; cursor: pointer; color: ${popup.text_color};">&times;</button>
            <h2 style="font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">${popup.title}</h2>
            <div style="font-size: 1rem; line-height: 1.6; margin-bottom: 2rem;">${popup.content}</div>
            <button class="popup-button" style="background-color: ${popup.button_color}; color: white; border: none; padding: 12px 30px; border-radius: 5px; font-size: 1rem; cursor: pointer; transition: all 0.3s ease;">
                ${popup.button_text}
            </button>
        `;

        overlay.appendChild(container);

        // Événements
        const closeBtn = container.querySelector('.popup-close');
        const actionBtn = container.querySelector('.popup-button');

        closeBtn.addEventListener('click', () => this.closePopup('closed'));
        actionBtn.addEventListener('click', () => {
            if (popup.button_url) {
                window.location.href = popup.button_url;
            } else {
                this.closePopup('clicked');
            }
        });

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                this.closePopup('closed');
            }
        });

        return overlay;
    }

    closePopup(action) {
        if (!this.currentPopup) return;

        this.trackPopupInteraction(this.currentPopup.id, action);

        const popupElement = document.querySelector('.popup-overlay');
        if (popupElement) {
            popupElement.classList.remove('show');
            setTimeout(() => {
                popupElement.remove();
            }, 300);
        }

        this.currentPopup = null;
        this.isPopupVisible = false;
    }

    async trackPopupInteraction(popupId, action) {
        try {
            await fetch('/popups/api/popup-interaction/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    popup_id: popupId,
                    action: action
                })
            });
        } catch (error) {
            console.error('Erreur lors du tracking:', error);
        }
    }


    async showCookieConsent() {
        try {
            const response = await fetch('/popups/api/cookie-consent/get/');
            const data = await response.json();

            if (data.status === 'success' && !data.consent) {
                this.displayCookieConsent();
            }
        } catch (error) {
            console.error('Erreur lors de la vérification du consentement:', error);
        }
    }

    displayCookieConsent() {
        // Créer la bannière de cookies
        const banner = document.createElement('div');
        banner.id = 'cookieConsentBanner';
        banner.style.cssText = `
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            box-shadow: 0 -5px 20px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            transform: translateY(100%);
            transition: transform 0.3s ease;
        `;

        banner.innerHTML = `
            <div style="max-width: 1200px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;">
                <div style="flex: 1; min-width: 300px;">
                    <h3 style="margin: 0 0 0.5rem 0; font-size: 1.2rem;">🍪 Gestion des Cookies</h3>
                    <p style="margin: 0; font-size: 0.9rem; opacity: 0.9;">Nous utilisons des cookies pour améliorer votre expérience. En continuant, vous acceptez notre utilisation des cookies.</p>
                </div>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                    <button onclick="popupManager.acceptAllCookies()" style="padding: 0.5rem 1rem; border: none; border-radius: 5px; cursor: pointer; font-size: 0.9rem; background-color: #28a745; color: white;">Accepter tout</button>
                    <button onclick="popupManager.declineAllCookies()" style="padding: 0.5rem 1rem; border: none; border-radius: 5px; cursor: pointer; font-size: 0.9rem; background-color: #6c757d; color: white;">Refuser tout</button>
                    <button onclick="popupManager.showCookieSettings()" style="padding: 0.5rem 1rem; border: 1px solid white; border-radius: 5px; cursor: pointer; font-size: 0.9rem; background-color: transparent; color: white;">Paramètres</button>
                </div>
            </div>
        `;

        document.body.appendChild(banner);

        // Afficher la bannière
        setTimeout(() => {
            banner.style.transform = 'translateY(0)';
        }, 1000);
    }

    async acceptAllCookies() {
        await this.saveCookieConsent({
            necessary: true,
            analytics: true,
            marketing: true,
            preferences: true,
            social: true
        });
        this.hideCookieConsent();
    }

    async declineAllCookies() {
        await this.saveCookieConsent({
            necessary: true,
            analytics: false,
            marketing: false,
            preferences: false,
            social: false
        });
        this.hideCookieConsent();
    }

    showCookieSettings() {
        // Rediriger vers la page de paramètres de cookies
        window.location.href = '/popups/cookie-settings/';
    }

    async saveCookieConsent(consent) {
        try {
            await fetch('/popups/api/cookie-consent/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(consent)
            });
        } catch (error) {
            console.error('Erreur lors de la sauvegarde du consentement:', error);
        }
    }

    hideCookieConsent() {
        const banner = document.getElementById('cookieConsentBanner');
        if (banner) {
            banner.style.transform = 'translateY(100%)';
            setTimeout(() => {
                banner.remove();
            }, 300);
        }
    }

    setupEventListeners() {
        // Fermer les popups avec Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isPopupVisible) {
                this.closePopup('closed');
            }
        });
    }

    getUserType() {
        // Déterminer le type d'utilisateur
        const userElement = document.querySelector('[data-user-type]');
        if (userElement) {
            return userElement.dataset.userType;
        }
        return 'anonymous';
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
}

// Captcha Manager
class CaptchaManager {
    constructor() {
        this.currentSession = null;
        this.attempts = 0;
        this.maxAttempts = 3;
    }

    async generateCaptcha() {
        try {
            const response = await fetch('/popups/api/captcha/generate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const data = await response.json();

            if (data.status === 'success') {
                this.currentSession = data.data.session_id;
                return data.data;
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Erreur lors de la génération du captcha:', error);
            throw error;
        }
    }

    async verifyCaptcha(answer) {
        try {
            const response = await fetch('/popups/api/captcha/verify/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    session_id: this.currentSession,
                    answer: answer
                })
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Erreur lors de la vérification du captcha:', error);
            return { status: 'error', message: 'Erreur de connexion' };
        }
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
}

// Initialiser les gestionnaires
const popupManager = new PopupManager();
const captchaManager = new CaptchaManager();

// Exposer les gestionnaires globalement
window.popupManager = popupManager;
window.captchaManager = captchaManager;
